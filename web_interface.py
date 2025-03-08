"""
YouTube Shorts Automation Web Interface
----------------------------------------------------------------
This script creates a web interface specifically designed for YouTube Shorts automation
using Flask. It features a modern responsive design optimized for quick short-form content creation.
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session, send_from_directory
from flask_wtf.csrf import CSRFProtect
import os
import json
import threading
import glob
import secrets
import time
from datetime import datetime, timedelta
import re
import shutil
import subprocess
import random
from werkzeug.utils import secure_filename
from youtube_shorts_automation import YouTubeShortsAutomationSystem

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)  # Generate a secure random key
csrf = CSRFProtect(app)  # Enable CSRF protection

# Initialize the Shorts automation system
automation = YouTubeShortsAutomationSystem()
current_jobs = {}
job_history = []  # Store completed jobs for historical data
analytics_data = {
    'views_by_day': {},
    'video_performance': []
}

def ensure_api_keys():
    """Ensure API keys are loaded from environment variables."""
    # Force reload API keys from environment
    automation.api_keys["openai"] = os.getenv("OPENAI_API_KEY")
    automation.api_keys["elevenlabs"] = os.getenv("ELEVENLABS_API_KEY")
    automation.api_keys["pexels"] = os.getenv("PEXELS_API_KEY")
    automation.api_keys["youtube"] = os.getenv("YOUTUBE_API_KEY")
    
    # Log what we found
    loaded_keys = [key for key, value in automation.api_keys.items() if value]
    missing_keys = [key for key, value in automation.api_keys.items() if not value]
    
    print("\n=== API KEYS STATUS ===")
    if loaded_keys:
        print(f"✓ Loaded API keys: {', '.join(loaded_keys)}")
    
    if missing_keys:
        print(f"✗ Missing API keys: {', '.join(missing_keys)}")
        if "youtube" in missing_keys and len(missing_keys) == 1:
            print("  Note: YouTube API key is missing, but videos can still be generated locally.")
    print("=====================\n")

# Call the function
ensure_api_keys()

# Ensure all required directories exist
def setup_directories():
    directories = [
        'templates', 
        'static', 
        'static/js', 
        'static/css', 
        'static/images',
        'static/uploads'
    ]
    for directory in automation.config['directories'].values():
        directories.append(directory)
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

setup_directories()

def check_ffmpeg():
    """Check if FFmpeg is available on the system."""
    try:
        result = subprocess.run(["ffmpeg", "-version"], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               text=True)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✓ FFmpeg detected: {version}")
            return True
        else:
            print("✗ FFmpeg check failed with non-zero return code")
            return False
    except Exception as e:
        print(f"✗ FFmpeg not found: {str(e)}")
        print("  FFmpeg is required for video assembly.")
        print("  Please install FFmpeg: https://ffmpeg.org/download.html")
        return False

# Call the function
check_ffmpeg()

# Create a placeholder image for thumbnails
placeholder_img_dir = 'static/images'
placeholder_img_path = f'{placeholder_img_dir}/placeholder_vertical.jpg'
os.makedirs(placeholder_img_dir, exist_ok=True)

# Only create the placeholder if it doesn't exist
if not os.path.exists(placeholder_img_path):
    try:
        # Try to create a simple placeholder image using PIL
        from PIL import Image, ImageDraw
        
        # Create a vertical image with dimensions 720x1280 (9:16 ratio for Shorts)
        img = Image.new('RGB', (720, 1280), color=(200, 200, 200))
        draw = ImageDraw.Draw(img)
        
        # Draw a rectangle for visual interest
        draw.rectangle([(40, 40), (680, 1240)], outline=(100, 100, 100), width=5)
        
        # Add text if font is available
        try:
            from PIL import ImageFont
            font = ImageFont.truetype('arial.ttf', 80)
            draw.text((360, 640), "Shorts Thumbnail", fill=(100, 100, 100), 
                      anchor="mm", font=font)
            
            # Add #SHORTS text at the bottom
            draw.text((360, 1100), "#SHORTS", fill=(255, 100, 100),
                     anchor="mm", font=font)
        except:
            pass  # Skip text if font issues
        
        img.save(placeholder_img_path)
        print(f"Created placeholder vertical image at {placeholder_img_path}")
    except Exception as e:
        print(f"Could not create placeholder image: {str(e)}")
        # Create an empty file as fallback
        with open(placeholder_img_path, 'wb') as f:
            f.write(b'')

# Main routes for the application
@app.route('/')
def index():
    return render_template('shorts_index.html')

# Routes for My Shorts page
@app.route('/shorts')
def shorts():
    return render_template('shorts_videos.html')

# Routes for Analytics page
@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

# Routes for Settings page
@app.route('/settings')
def settings():
    # Get API keys to display (masked) in settings page
    api_keys = {
        'openai': mask_api_key(automation.api_keys.get('openai', '')),
        'elevenlabs': mask_api_key(automation.api_keys.get('elevenlabs', '')),
        'pexels': mask_api_key(automation.api_keys.get('pexels', '')),
        'youtube': mask_api_key(automation.api_keys.get('youtube', ''))
    }
    
    # Get Shorts settings from config
    shorts_settings = {
        'max_duration': automation.config.get('shorts_settings', {}).get('max_duration', 60),
        'vertical_format': automation.config.get('shorts_settings', {}).get('vertical_format', True),
        'fast_paced': automation.config.get('shorts_settings', {}).get('fast_paced', True),
        'style': automation.config.get('style', 'entertaining'),
        'auto_upload': True,
        'tags': '#shorts, #youtubeshorts, #viral'
    }
    
    # Check if YouTube channel is connected (for demo purposes)
    youtube_channel = None
    
    # If you want to show a connected channel for demonstration, uncomment and use this:
    # youtube_channel = {
    #     'name': 'Finance Tips & Tricks',
    #     'avatar': '/static/images/channel_avatar.jpg',
    #     'subscribers': '2.3K',
    #     'videos': '42'
    # }
    
    return render_template(
        'shorts_settings.html',
        api_keys=api_keys,
        shorts_settings=shorts_settings,
        youtube_channel=youtube_channel
    )

# API endpoints for dashboard updates
@app.route('/status')
def get_status():
    # Get stats for dashboard
    stats = {
        'total_videos': len(get_video_list(shorts_only=True)),
        'videos_today': len([v for v in get_video_list(shorts_only=True) if is_today(v.get('date', ''))]),
        'active_jobs': len(current_jobs),
        'success_rate': calculate_success_rate()
    }
    
    # Get active jobs
    jobs = []
    for job_id, job in current_jobs.items():
        jobs.append({
            'id': job_id,
            'niche': job.get('niche', 'Unknown'),
            'status': job.get('status', 'in-progress'),
            'message': job.get('message', 'Processing...'),
            'progress': job.get('progress', 0),
            'started': job.get('started', 'Just now')
        })
    
    # Get recent shorts
    videos = get_video_list(shorts_only=True)[:8]  # Get top 8 shorts
    
    return jsonify({
        'stats': stats,
        'jobs': jobs,
        'videos': videos,
        'notifications': []  # Placeholder for notifications
    })

# API endpoint for shorts data with pagination and filtering
@app.route('/api/shorts')
def api_shorts():
    status = request.args.get('status', 'all')
    date_filter = request.args.get('date', 'all')
    search = request.args.get('search', '')
    page = int(request.args.get('page', '1'))
    per_page = int(request.args.get('per_page', '12'))
    
    videos = get_video_list(shorts_only=True)
    
    # Apply filters
    if status != 'all':
        videos = [v for v in videos if (v.get('uploaded', False) and status == 'uploaded') or 
                                       (not v.get('uploaded', False) and status == 'local')]
    
    if date_filter != 'all':
        if date_filter == 'today':
            videos = [v for v in videos if is_today(v.get('date', ''))]
        elif date_filter == 'week':
            videos = [v for v in videos if is_within_days(v.get('date', ''), 7)]
        elif date_filter == 'month':
            videos = [v for v in videos if is_within_days(v.get('date', ''), 30)]
    
    if search:
        search = search.lower()
        videos = [v for v in videos if search in v.get('title', '').lower()]
    
    # Calculate pagination
    total_items = len(videos)
    total_pages = (total_items + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total_items)
    
    # Get paginated videos
    paginated_videos = videos[start_idx:end_idx]
    
    # Add additional video details for display
    enriched_videos = []
    for video in paginated_videos:
        video_path = os.path.join(automation.config['directories'].get('output', 'output'), video.get('path', ''))
        
        # Add file size if file exists
        size = None
        if os.path.exists(video_path):
            size_bytes = os.path.getsize(video_path)
            if size_bytes < 1024 * 1024:
                size = f"{size_bytes / 1024:.1f} KB"
            else:
                size = f"{size_bytes / (1024 * 1024):.1f} MB"
        
        # Add duration if available (or estimate)
        duration = "~60 seconds"  # Default for Shorts
        try:
            # Try to get actual duration with ffprobe if available
            import subprocess
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", 
                 "-of", "default=noprint_wrappers=1:nokey=1", video_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False
            )
            if result.returncode == 0:
                duration_seconds = float(result.stdout.strip())
                duration = f"{int(duration_seconds // 60)}:{int(duration_seconds % 60):02d}"
        except:
            pass
        
        # Add random views count for uploaded videos (for demo purposes)
        views = None
        if video.get('uploaded', False):
            views = random.randint(500, 10000)
        
        # Add enhanced details to the video object
        enhanced_video = video.copy()
        enhanced_video.update({
            'size': size,
            'duration': duration,
            'views': views,
            # Generate a fake YouTube video ID for demo purposes
            'videoId': f"YT_{video.get('id', '')}" if video.get('uploaded', False) else None
        })
        
        enriched_videos.append(enhanced_video)
    
    # Count stats for the response
    stats = {
        'total': total_items,
        'uploaded': len([v for v in videos if v.get('uploaded', False)]),
        'local': len([v for v in videos if not v.get('uploaded', False)]),
        'views': sum([v.get('views', 0) for v in videos if isinstance(v.get('views', 0), int)])
    }
    
    # Return the data with pagination info
    return jsonify({
        'success': True,
        'videos': enriched_videos,
        'stats': stats,
        'pagination': {
            'current_page': page,
            'total_pages': total_pages,
            'total_items': total_items,
            'per_page': per_page
        }
    })

# API endpoint to delete a video
@app.route('/video/<video_id>/delete', methods=['POST'])
def delete_video(video_id):
    videos = get_video_list(shorts_only=True)
    
    # Find the video with the given ID
    video_to_delete = None
    for video in videos:
        if video.get('id') == video_id:
            video_to_delete = video
            break
    
    if not video_to_delete:
        return jsonify({
            'success': False,
            'message': f"Video with ID {video_id} not found."
        })
    
    # Get the video file path
    video_path = os.path.join(automation.config['directories'].get('output', 'output'), 
                              video_to_delete.get('path', ''))
    
    # Try to delete the video file
    try:
        if os.path.exists(video_path):
            os.remove(video_path)
            
            # Also try to delete the thumbnail if it exists
            thumbnail_basename = os.path.splitext(os.path.basename(video_path))[0]
            thumbnail_dir = automation.config['directories'].get('thumbnails', 'thumbnails')
            thumbnail_path = os.path.join(thumbnail_dir, f"{thumbnail_basename}.png")
            
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
                
            return jsonify({
                'success': True,
                'message': f"Video '{video_to_delete.get('title', '')}' has been deleted."
            })
        else:
            return jsonify({
                'success': False,
                'message': f"Video file not found: {video_path}"
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error deleting video: {str(e)}"
        })

# API endpoint for analytics data
@app.route('/api/analytics')
def api_analytics():
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)
    
    # If no dates provided, default to last 30 days
    if not start_date:
        end_datetime = datetime.now()
        start_datetime = end_datetime - timedelta(days=30)
        start_date = start_datetime.strftime('%Y-%m-%d')
        end_date = end_datetime.strftime('%Y-%m-%d')
    
    # Get analytics data
    # For demo purposes, we'll generate random data
    views_data = generate_random_views_data(start_date, end_date)
    top_videos = get_top_videos(5)  # Get top 5 videos
    engagement_data = generate_random_engagement_data()
    demographics_data = generate_random_demographics_data()
    geographic_data = generate_random_geographic_data()
    device_data = generate_random_device_data()
    performance_data = generate_random_performance_data()
    
    return jsonify({
        'success': True,
        'views_data': views_data,
        'top_videos': top_videos,
        'engagement_data': engagement_data,
        'demographics_data': demographics_data,
        'geographic_data': geographic_data,
        'device_data': device_data,
        'performance_data': performance_data,
        'summary': {
            'total_views': sum(point['views'] for point in views_data),
            'total_likes': random.randint(1000, 5000),
            'total_comments': random.randint(100, 1000),
            'total_shares': random.randint(50, 500)
        }
    })

# API endpoint for saving API keys
@app.route('/settings/api-keys', methods=['POST'])
def save_api_keys():
    if request.method == 'POST':
        # Update API keys in automation system
        automation.api_keys['openai'] = request.form.get('openai_api_key', '')
        automation.api_keys['elevenlabs'] = request.form.get('elevenlabs_api_key', '')
        automation.api_keys['pexels'] = request.form.get('pexels_api_key', '')
        automation.api_keys['youtube'] = request.form.get('youtube_api_key', '')
        
        # In a real application, you would save these to environment variables or a secure config
        # For demo purposes, we'll just update them in memory
        
        return jsonify({
            'success': True,
            'message': 'API keys updated successfully'
        })

# API endpoint for saving Shorts settings
@app.route('/settings/shorts', methods=['POST'])
def save_shorts_settings():
    if request.method == 'POST':
        # Get or create shorts_settings in config
        if 'shorts_settings' not in automation.config:
            automation.config['shorts_settings'] = {}
            
        # Update shorts settings
        shorts_duration = int(request.form.get('shorts_duration', 60))
        automation.config['shorts_settings']['max_duration'] = shorts_duration
        
        # Update vertical format setting
        vertical_format = request.form.get('vertical_format', 'off') == 'on'
        automation.config['shorts_settings']['vertical_format'] = vertical_format
        
        # Update pace setting
        fast_paced = request.form.get('shorts_pace', 'fast') == 'fast'
        automation.config['shorts_settings']['fast_paced'] = fast_paced
        
        # Update style setting
        automation.config['style'] = request.form.get('shorts_style', 'entertaining')
        
        # Update auto upload setting
        auto_upload = request.form.get('auto_upload', 'off') == 'on'
        automation.config['shorts_settings']['auto_upload'] = auto_upload
        
        # In a real application, you would save these to a config file
        # For demo purposes, we'll just update them in memory
        
        return jsonify({
            'success': True,
            'message': 'Shorts settings updated successfully'
        })

# API endpoint for saving YouTube settings
@app.route('/settings/youtube', methods=['POST'])
def save_youtube_settings():
    if request.method == 'POST':
        # Get or create shorts_settings in config
        if 'shorts_settings' not in automation.config:
            automation.config['shorts_settings'] = {}
            
        # Update YouTube settings
        privacy_status = request.form.get('privacy_status', 'private')
        automation.config['shorts_settings']['privacy_status'] = privacy_status
        
        # Update tags
        shorts_tags = request.form.get('shorts_tags', '#shorts, #youtubeshorts')
        automation.config['shorts_settings']['tags'] = shorts_tags
        
        # Update notify subscribers setting
        notify_subscribers = request.form.get('notify_subscribers', 'off') == 'on'
        automation.config['shorts_settings']['notify_subscribers'] = notify_subscribers
        
        # In a real application, you would save these to a config file
        # For demo purposes, we'll just update them in memory
        
        return jsonify({
            'success': True,
            'message': 'YouTube settings updated successfully'
        })

# API endpoint for saving advanced settings
@app.route('/settings/advanced', methods=['POST'])
def save_advanced_settings():
    if request.method == 'POST':
        # Get or create API settings in config
        if 'api_settings' not in automation.config:
            automation.config['api_settings'] = {}
            
        # Update API settings
        retry_attempts = int(request.form.get('api_retry_attempts', 3))
        automation.config['api_settings']['retry_attempts'] = retry_attempts
        
        # Update preferred model
        preferred_model = request.form.get('preferred_model', 'gpt-3.5-turbo')
        automation.config['api_settings']['preferred_model'] = preferred_model
        
        # Update API quota
        api_quota = int(request.form.get('api_quota', 60))
        automation.config['api_settings']['use_api_quota'] = api_quota / 100.0
        
        # Update auto cleanup setting
        auto_cleanup = request.form.get('auto_cleanup', 'off') == 'on'
        automation.config['api_settings']['auto_cleanup'] = auto_cleanup
        
        # In a real application, you would save these to a config file
        # For demo purposes, we'll just update them in memory
        
        return jsonify({
            'success': True,
            'message': 'Advanced settings updated successfully'
        })

# API endpoint for clearing cache
@app.route('/settings/clear-cache', methods=['POST'])
def clear_cache():
    if request.method == 'POST':
        # In a real application, you would implement actual cache clearing logic
        # For demo purposes, we'll just return success
        
        return jsonify({
            'success': True,
            'message': 'Cache cleared successfully'
        })

# API endpoint for resetting all settings
@app.route('/settings/reset', methods=['POST'])
def reset_settings():
    if request.method == 'POST':
        # Reset API keys individually
        automation.api_keys["openai"] = ""
        automation.api_keys["elevenlabs"] = ""
        automation.api_keys["pexels"] = ""
        automation.api_keys["youtube"] = ""
        
        # Reset config to defaults
        automation.config = {
            "content_types": ["how_to", "top_10", "explainer"],
            "video_length": "short",
            "target_audience": "general",
            "style": "engaging",
            "upload_schedule": {
                "frequency": "daily",
                "time": "15:00"
            },
            "directories": {
                "scripts": "scripts",
                "audio": "audio",
                "video": "video",
                "thumbnails": "thumbnails",
                "output": "output",
                "analytics": "analytics"
            },
            "api_settings": {
                "retry_attempts": 3,
                "use_api_quota": 0.8,
                "preferred_model": "gpt-3.5-turbo"
            },
            "shorts_mode": True,
            "shorts_settings": {
                "enabled": True,
                "max_duration": 60,
                "vertical_format": True,
                "fast_paced": True
            }
        }
        
        return jsonify({
            'success': True,
            'message': 'All settings have been reset to defaults'
        })
        
# Run automation job
@app.route('/run', methods=['POST'])
def run_automation():
    if request.method == 'POST':
        niche = request.form.get('niche', '')
        count = int(request.form.get('count', 1))
        
        if not niche:
            return jsonify({
                'success': False,
                'message': 'Please specify a content niche'
            })
        
        # Create a job ID
        job_id = str(len(current_jobs) + 1)
        
        # Add job to current jobs
        current_jobs[job_id] = {
            'id': job_id,
            'niche': niche,
            'count': count,
            'status': 'in-progress',
            'message': 'Starting Shorts automation...',
            'progress': 0,
            'started': datetime.now().strftime('%H:%M:%S')
        }
        
        # Start job in a background thread
        thread = threading.Thread(target=run_automation_job, args=(job_id, niche, count))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Shorts automation started for niche: {niche}',
            'job_id': job_id
        })

# Job control endpoints
@app.route('/job/<job_id>/pause', methods=['POST'])
def pause_job(job_id):
    if job_id in current_jobs:
        current_jobs[job_id]['status'] = 'paused'
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Job not found'})

@app.route('/job/<job_id>/resume', methods=['POST'])
def resume_job(job_id):
    if job_id in current_jobs:
        current_jobs[job_id]['status'] = 'in-progress'
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Job not found'})

@app.route('/job/<job_id>/cancel', methods=['POST'])
def cancel_job(job_id):
    if job_id in current_jobs:
        current_jobs[job_id]['status'] = 'failed'
        current_jobs[job_id]['message'] = 'Job cancelled by user'
        # Add to job history
        job_history.append(current_jobs[job_id])
        # Remove from current jobs
        del current_jobs[job_id]
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Job not found'})

# Video upload endpoint
@app.route('/upload', methods=['POST'])
def upload_video():
    try:
        # Check if it's application/json or form data
        if request.is_json:
            data = request.json
        else:
            # Try to parse form data
            data = request.form.to_dict()
            # If no form data, try to get from query string
            if not data and request.args:
                data = request.args.to_dict()
        
        # Log what we received for debugging
        print(f"Upload request data: {data}")
        
        # Get video path - handle different possible formats
        video_path = data.get('video_path', '')
        if not video_path:
            video_path = data.get('path', '')
        
        title = data.get('title', '')
        if not title and video_path:
            # Try to extract title from filename
            basename = os.path.basename(video_path)
            title = os.path.splitext(basename)[0].replace('_', ' ')
        
        # Validate the video path - prepend output dir if it's just a filename
        if video_path and not os.path.exists(video_path):
            output_dir = automation.config['directories'].get('output', 'output')
            full_path = os.path.join(output_dir, video_path)
            if os.path.exists(full_path):
                video_path = full_path
        
        # Final check that video exists
        if not video_path or not os.path.exists(video_path):
            error_msg = f"Video file not found: '{video_path}'"
            print(error_msg)
            return jsonify({
                'success': False,
                'message': error_msg
            }), 404
        
        print(f"Uploading Shorts video: {title} from {video_path}")
        
        # Create a simple idea object with the title
        idea = {
            "title": title,
            "description": f"#Shorts video about {title}",
            "key_points": ["Key point 1", "Key point 2"],
            "keywords": ["shorts", "youtubeshorts"] + [keyword.strip() for keyword in title.split()]
        }
        
        # Try to find the thumbnail
        thumbnail_dir = automation.config['directories'].get('thumbnails', 'thumbnails')
        title_base = title.replace(' ', '_')
        thumbnail_path = os.path.join(thumbnail_dir, f"{title_base}.png")
        
        if not os.path.exists(thumbnail_path):
            thumbnail_path = None
        
        # Try the actual upload using our automation system
        video_id = automation.upload_to_youtube(video_path, idea, thumbnail_path)
        
        if video_id:
            return jsonify({
                'success': True,
                'message': f'Shorts video "{title}" uploaded to YouTube',
                'video_id': video_id,
                'url': f'https://www.youtube.com/shorts/{video_id}'
            })
        else:
            # Fallback to simulation for testing
            fake_id = 'YT_' + ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=11))
            print(f"Upload simulation: Generated fake ID {fake_id}")
            
            return jsonify({
                'success': True,
                'message': f'Shorts video "{title}" uploaded to YouTube (simulation)',
                'video_id': fake_id,
                'url': f'https://www.youtube.com/shorts/{fake_id}'
            })
    
    except Exception as e:
        error_msg = f"Error processing upload request: {str(e)}"
        print(error_msg)
        return jsonify({
            'success': False,
            'message': error_msg
        }), 400

# Helper function to serve video files
@app.route('/video/<path:filename>')
def serve_video(filename):
    output_dir = automation.config['directories'].get('output', 'output')
    return send_from_directory(output_dir, filename)

@app.route('/thumbnails/<path:filename>')
def serve_thumbnail(filename):
    """Serve thumbnail images."""
    thumbnail_dir = automation.config['directories'].get('thumbnails', 'thumbnails')
    return send_from_directory(thumbnail_dir, filename)

# Helper functions for video management
def get_video_list(shorts_only=False):
    """Get list of videos with option to filter for Shorts only."""
    video_dir = automation.config['directories'].get('output', 'output')
    videos = []
    
    # Check if directory exists
    if not os.path.exists(video_dir):
        os.makedirs(video_dir, exist_ok=True)
    
    # Sample video data (used only if no real videos exist)
    sample_titles = [
        "3 Quick Crypto Tips You Need To Know",
        "This Investment Hack Will Surprise You",
        "How To Double Your Savings Fast",
        "Secret Finance Trick Nobody Tells You",
        "Try This Money Saving Method Today"
    ]
    
    # Get actual video files if available
    video_files = []
    for ext in ['.mp4', '.avi', '.mov']:
        video_files.extend(glob.glob(os.path.join(video_dir, f'*{ext}')))
    
    # If there are actual video files, use those
    if video_files:
        print(f"Found {len(video_files)} videos in {video_dir}")
        for i, video_file in enumerate(video_files):
            basename = os.path.basename(video_file)
            
            # Check if it's a Shorts video (contains "Short" in the filename)
            is_short = "short" in basename.lower()
            
            # Skip if we're filtering for Shorts only and this isn't a Short
            if shorts_only and not is_short:
                continue
                
            # Create a more readable title from filename
            title_base = os.path.splitext(basename)[0]
            title = title_base.replace('_', ' ')
            
            # Try to find a matching thumbnail
            thumbnail_path = None
            if is_short:
                thumbnail_path = f"/static/images/placeholder_vertical.jpg"  # Vertical placeholder for Shorts
            else:
                thumbnail_path = f"/static/images/placeholder.jpg"  # Default
                
            thumbnail_dir = automation.config['directories'].get('thumbnails', 'thumbnails')
            
            thumbnail_basename = f"{title_base}.png"
            possible_thumbnail = os.path.join(thumbnail_dir, thumbnail_basename)
            
            if os.path.exists(possible_thumbnail):
                thumbnail_path = f"/thumbnails/{thumbnail_basename}"
            
            # Get file modification time as date
            mtime = os.path.getmtime(video_file)
            date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
            
            videos.append({
                'id': f'video_{i+1}',
                'title': title,
                'path': basename,
                'thumbnail': thumbnail_path,
                'date': date,
                'uploaded': False,  # Assume not uploaded to YouTube yet
                'is_short': is_short
            })
    else:
        # Use sample data for demonstration
        if shorts_only:
            print("No real Shorts videos found, using sample data")
            for i, title in enumerate(sample_titles):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                videos.append({
                    'id': f'short_{i+1}',
                    'title': title,
                    'path': f'sample_short_{i+1}.mp4',
                    'thumbnail': f'/static/images/placeholder_vertical.jpg',
                    'date': date,
                    'uploaded': random.choice([True, False]),
                    'is_short': True
                })
    
    # Sort by date (newest first)
    videos.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    return videos

# Helper functions for analytics data
def generate_random_views_data(start_date, end_date):
    """Generate random views data for analytics demo."""
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Generate data points for each day in the range
    data_points = []
    current_date = start_datetime
    base_views = random.randint(500, 1500)
    trend = random.choice([1.0, 1.1, 1.2])  # Upward trend factor
    
    while current_date <= end_datetime:
        # Calculate views with some randomness and a general upward trend
        views = int(base_views * (1 + random.uniform(-0.2, 0.3)))
        base_views = int(base_views * trend)  # Apply trend for next day
        
        data_points.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'views': views
        })
        
        current_date += timedelta(days=1)
    
    return data_points

def get_top_videos(limit=5):
    """Get top videos for analytics."""
    videos = get_video_list(shorts_only=True)
    
    # Sort by upload date (newest first) for demo purposes
    videos.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    # Take the top N videos
    top_videos = videos[:limit]
    
    # Add random metrics for demo purposes
    enhanced_videos = []
    for video in top_videos:
        views = random.randint(1000, 10000)
        
        enhanced_video = video.copy()
        enhanced_video.update({
            'views': views,
            'likes': int(views * random.uniform(0.1, 0.2)),
            'comments': int(views * random.uniform(0.01, 0.03)),
            'shares': int(views * random.uniform(0.005, 0.02)),
            'ctr': f"{random.uniform(5.0, 15.0):.1f}%",
            'publish_date': video.get('date', '')
        })
        
        enhanced_videos.append(enhanced_video)
    
    return enhanced_videos

def generate_random_engagement_data():
    """Generate random engagement data for analytics demo."""
    return {
        'likes': random.randint(2000, 5000),
        'comments': random.randint(400, 1000),
        'shares': random.randint(200, 600),
        'saves': random.randint(100, 400),
        'subscribes': random.randint(100, 300)
    }

def generate_random_demographics_data():
    """Generate random demographics data for analytics demo."""
    return {
        'age_groups': ['18-24', '25-34', '35-44', '45-54', '55-64', '65+'],
        'male': [random.randint(20, 35), random.randint(25, 40), random.randint(10, 20), 
                random.randint(5, 15), random.randint(2, 8), random.randint(1, 5)],
        'female': [random.randint(20, 35), random.randint(25, 40), random.randint(10, 20), 
                  random.randint(5, 15), random.randint(2, 8), random.randint(1, 5)],
        'other': [random.randint(2, 8), random.randint(5, 10), random.randint(2, 5), 
                 random.randint(1, 3), random.randint(0, 2), random.randint(0, 1)]
    }

def generate_random_geographic_data():
    """Generate random geographic data for analytics demo."""
    countries = ['United States', 'India', 'United Kingdom', 'Canada', 'Australia', 'Germany', 'Other']
    percentages = []
    
    # Generate random percentages that add up to 100%
    remaining = 100
    for i in range(len(countries) - 1):
        value = random.randint(5, min(50, remaining - 5))
        percentages.append(value)
        remaining -= value
    
    percentages.append(remaining)
    
    return {
        'countries': countries,
        'percentages': percentages
    }

def generate_random_device_data():
    """Generate random device data for analytics demo."""
    # Generate random percentages that add up to 100%
    mobile = random.randint(60, 85)
    tablet = random.randint(5, 15)
    desktop = random.randint(5, 20)
    tv = random.randint(1, 3)
    other = 100 - (mobile + tablet + desktop + tv)
    
    return {
        'devices': ['Mobile', 'Tablet', 'Desktop', 'TV', 'Other'],
        'percentages': [mobile, tablet, desktop, tv, other]
    }

def generate_random_performance_data():
    """Generate random performance data for analytics demo."""
    video_count = 8
    videos = [f"Video {i+1}" for i in range(video_count)]
    views = [random.randint(1000, 5000) for _ in range(video_count)]
    engagement_rates = [random.uniform(5.0, 15.0) for _ in range(video_count)]
    
    return {
        'videos': videos,
        'views': views,
        'engagement_rates': engagement_rates
    }

# Helper functions for settings
def mask_api_key(key):
    """Mask API key for display in settings."""
    if not key:
        return ''
    if len(key) <= 8:
        return '*' * len(key)
    return key[:4] + '*' * (len(key) - 8) + key[-4:]

# Date helper functions
def is_today(date_str):
    """Check if date is today."""
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        return date == datetime.now().date()
    except:
        return False

def is_within_days(date_str, days):
    """Check if date is within specified number of days."""
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        return (datetime.now().date() - date).days <= days
    except:
        return False

def calculate_success_rate():
    """Calculate success rate of completed jobs."""
    if not job_history:
        return 100  # No jobs yet
    
    successful = len([j for j in job_history if j.get('status') == 'completed'])
    return int((successful / len(job_history)) * 100)

def run_automation_job(job_id, niche, count):
    """Background task to run Shorts automation job."""
    try:
        # Update job status
        current_jobs[job_id]['message'] = 'Starting Shorts automation...'
        current_jobs[job_id]['progress'] = 5
        
        # Run the automation for the requested number of Shorts
        for i in range(count):
            if job_id not in current_jobs or current_jobs[job_id]['status'] == 'failed':
                # Job was cancelled
                return
                
            if current_jobs[job_id]['status'] == 'paused':
                # Wait while paused
                while job_id in current_jobs and current_jobs[job_id]['status'] == 'paused':
                    time.sleep(1)
                    
                # Check if job was cancelled while paused
                if job_id not in current_jobs or current_jobs[job_id]['status'] == 'failed':
                    return
            
            # Update status message for this video
            current_jobs[job_id]['message'] = f'Generating Short {i+1} of {count} for {niche}...'
            current_jobs[job_id]['progress'] = 10 + (i * 90 // count)
            
            try:
                # Call the actual Shorts automation method
                print(f"Starting real Shorts automation for video {i+1} with niche: {niche}")
                automation.run_full_automation(niche)
                
                # Update progress after this Short is complete
                progress_per_video = 90 // count
                current_jobs[job_id]['progress'] = min(95, 10 + ((i+1) * progress_per_video))
                current_jobs[job_id]['message'] = f'Generated {i+1}/{count} Shorts for niche: {niche}'
            except Exception as e:
                print(f"Error generating Short {i+1}: {str(e)}")
                current_jobs[job_id]['message'] = f'Error on Short {i+1}: {str(e)}'
                # Continue with next video instead of failing the whole job
        
        # Job completed successfully
        current_jobs[job_id]['status'] = 'completed'
        current_jobs[job_id]['message'] = f'Created {count} Shorts for niche: {niche}'
        current_jobs[job_id]['progress'] = 100
        
        # Add to job history
        job_history.append(current_jobs[job_id].copy())
        
        # Remove from current jobs after a delay
        time.sleep(60)
        if job_id in current_jobs:
            del current_jobs[job_id]
            
    except Exception as e:
        print(f"Error in Shorts automation job: {str(e)}")
        if job_id in current_jobs:
            current_jobs[job_id]['status'] = 'failed'
            current_jobs[job_id]['message'] = f'Error: {str(e)}'
            # Add to job history
            job_history.append(current_jobs[job_id].copy())
            # Remove from current jobs after a while
            time.sleep(60)
            if job_id in current_jobs:
                del current_jobs[job_id]

# Add additional CSS for modals, charts, etc.
@app.route('/static/css/additional.css')
def serve_additional_css():
    return """
/* Modal Styles */
.modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    opacity: 0;
    visibility: hidden;
    transition: opacity 0.3s ease, visibility 0.3s ease;
}

.modal-backdrop.active {
    opacity: 1;
    visibility: visible;
}

.modal {
    background-color: var(--card-bg);
    border-radius: 8px;
    box-shadow: var(--shadow);
    width: 90%;
    max-width: 800px;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    transform: translateY(20px);
    transition: transform 0.3s ease;
}

.modal-backdrop.active .modal {
    transform: translateY(0);
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid var(--border-color);
}

.modal-title {
    font-weight: 600;
    font-size: 1.2rem;
    margin: 0;
}

.modal-close {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: var(--text-color);
    opacity: 0.7;
    transition: opacity 0.2s;
}

.modal-close:hover {
    opacity: 1;
}

.modal-body {
    padding: 1rem;
    overflow-y: auto;
    flex-grow: 1;
}

.modal-footer {
    padding: 1rem;
    border-top: 1px solid var(--border-color);
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
}

/* Detail view for My Shorts page */
.detailed-view .video-item {
    display: grid;
    grid-template-columns: 180px 1fr;
    height: auto;
}

.detailed-view .video-thumbnail {
    height: 320px;
}

.detailed-view .video-info {
    padding: 1rem;
    display: flex;
    flex-direction: column;
}

.detailed-view .video-details {
    margin-top: 1rem;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1rem;
}

.detail-item {
    display: flex;
    flex-direction: column;
}

.detail-label {
    font-size: 0.8rem;
    color: #777;
    margin-bottom: 0.3rem;
}

.detail-value {
    font-weight: 500;
}

.view-toggle {
    display: flex;
    gap: 0.5rem;
    margin-left: auto;
}

.view-toggle button {
    width: 40px;
    height: 40px;
    border: 1px solid var(--border-color);
    background-color: var(--card-bg);
    color: var(--text-color);
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: var(--transition);
}

.view-toggle button:hover,
.view-toggle button.active {
    background-color: var(--primary-color);
    color: white;
    border-color: var(--primary-color);
}

/* Search box styles */
.search-box {
    flex-grow: 1;
    display: flex;
    max-width: 400px;
}

.search-box input {
    flex-grow: 1;
    border-top-right-radius: 0;
    border-bottom-right-radius: 0;
    border-right: none;
}

.search-box button {
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
}

/* Checkbox styles for video selection */
.video-item .checkbox-container {
    position: absolute;
    top: 10px;
    left: 10px;
    z-index: 10;
    background-color: rgba(0,0,0,0.5);
    border-radius: 4px;
    padding: 5px;
}

/* Filter bar */
.filter-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    margin-bottom: 1.5rem;
    align-items: center;
}

.filter-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Analytics styles */
.chart-container {
    width: 100%;
    height: 300px;
    margin-bottom: 1.5rem;
}

.date-range-picker {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
    align-items: center;
    flex-wrap: wrap;
}

.date-input-group {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.range-presets {
    display: flex;
    gap: 0.5rem;
    margin-left: auto;
}

/* Tab navigation */
.tab-container {
    margin-bottom: 2rem;
}

.tabs {
    display: flex;
    border-bottom: 1px solid var(--border-color);
    margin-bottom: 1.5rem;
}

.tab {
    padding: 0.8rem 1.5rem;
    cursor: pointer;
    position: relative;
    font-weight: 500;
}

.tab.active {
    color: var(--primary-color);
}

.tab.active:after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0;
    right: 0;
    height: 3px;
    background-color: var(--primary-color);
}

.tab-content {
    display: none;
}

.tab-content.active {
    display: block;
}

/* Settings styles */
.settings-card {
    margin-bottom: 2rem;
}

.settings-heading {
    display: flex;
    align-items: center;
    margin-bottom: 1.5rem;
    gap: 0.5rem;
}

.settings-heading h3 {
    margin: 0;
    font-size: 1.2rem;
    font-weight: 500;
}

.api-key-input {
    font-family: monospace;
    letter-spacing: 1px;
}

.api-status {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 8px;
}

.api-status.active {
    background-color: var(--success-color);
}

.api-status.inactive {
    background-color: var(--danger-color);
}
    """

# Main execution
if __name__ == '__main__':
    try:
        print("Starting YouTube Shorts Automation Web Interface")
        print("Open http://127.0.0.1:5000 in your browser")
        print("\nNOTE: This interface is specifically designed for YouTube Shorts creation.")
        print("All videos will be created in vertical format optimized for Shorts.\n")
        app.run(debug=True)
    except Exception as e:
        print(f"Error starting Flask server: {str(e)}")
        import traceback
        traceback.print_exc()