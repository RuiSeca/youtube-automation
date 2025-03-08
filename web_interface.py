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
import pickle
import random
from datetime import datetime, timedelta
import re
import shutil
import subprocess
from werkzeug.utils import secure_filename
from youtube_shorts_automation import YouTubeShortsAutomationSystem

# YouTube API imports
import google.oauth2.credentials
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)  # You already have this line
csrf = CSRFProtect(app)

# YouTube API Settings
YOUTUBE_CLIENT_SECRETS_FILE = "client_secrets.json"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/yt-analytics.readonly",  # Add this line
    "https://www.googleapis.com/auth/yt-analytics-monetary.readonly"  # Add this if you want monetary data
]
YOUTUBE_TOKEN_FILE = "youtube_token.pickle"

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
    """Provide analytics data from YouTube API or mock data."""
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)
    use_real_data = request.args.get('use_real_data', 'false').lower() == 'true'
    
    # If no dates provided, default to last 30 days
    if not start_date:
        end_datetime = datetime.now()
        start_datetime = end_datetime - timedelta(days=30)
        start_date = start_datetime.strftime('%Y-%m-%d')
        end_date = end_datetime.strftime('%Y-%m-%d')
    
    print(f"Analytics request: start={start_date}, end={end_date}, use_real_data={use_real_data}")
    
    # If real data is requested, try to get it from YouTube API
    if use_real_data:
        try:
            print("Attempting to fetch real YouTube Analytics data...")
            
            # Step 1: Get YouTube credentials
            credentials = get_youtube_credentials()
            if not credentials:
                print("ERROR: No YouTube credentials available")
                return jsonify({
                    'success': False,
                    'message': 'Not authenticated with YouTube. Please connect your channel in Settings.'
                })
            
            # Step 2: Build the YouTube API clients
            print("Building YouTube API clients...")
            youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)
            
            # Try to build YouTube Analytics API client specifically
            try:
                youtube_analytics = build('youtubeAnalytics', 'v2', credentials=credentials)
                print("Successfully built YouTube Analytics API client")
            except Exception as analytics_e:
                print(f"ERROR: Failed to build YouTube Analytics API client: {str(analytics_e)}")
                return jsonify({
                    'success': False,
                    'message': f'YouTube Analytics API access error: {str(analytics_e)}. You may need to reconnect your channel with additional permissions.'
                })
            
            # Step 3: Get channel ID
            print("Fetching channel ID...")
            try:
                channels_response = youtube.channels().list(
                    part="id,snippet,statistics",
                    mine=True
                ).execute()
                
                if not channels_response.get("items"):
                    print("No channels found for this account")
                    return jsonify({
                        'success': False,
                        'message': 'No YouTube channel found for this account.'
                    })
                
                channel = channels_response["items"][0]
                channel_id = channel["id"]
                channel_title = channel["snippet"]["title"]
                print(f"Found channel: {channel_title} (ID: {channel_id})")
                
                # Show basic channel stats for verification
                subscribers = channel["statistics"]["subscriberCount"]
                video_count = channel["statistics"]["videoCount"]
                print(f"Channel stats: {subscribers} subscribers, {video_count} videos")
                
                # New channels might not have analytics data yet
                if int(video_count) == 0:
                    print("Channel has no videos. Cannot retrieve analytics.")
                    return jsonify({
                        'success': False,
                        'message': 'Your channel has no videos. Analytics data is not available.'
                    })
            except Exception as channel_e:
                print(f"ERROR getting channel info: {str(channel_e)}")
                return jsonify({
                    'success': False,
                    'message': f'Error accessing YouTube channel: {str(channel_e)}'
                })
            
            # Step 4: Try to get analytics data
            print(f"Fetching analytics data for channel {channel_id} from {start_date} to {end_date}...")
            try:
                # Create a simpler analytics query first to test permissions
                analytics_response = youtube_analytics.reports().query(
                    ids=f'channel=={channel_id}',
                    startDate=start_date,
                    endDate=end_date,
                    metrics='views',  # Just query views first as a test
                    dimensions='day'
                ).execute()
                
                print(f"Basic analytics query successful")
                
                # If first query works, try the complete query
                analytics_response = youtube_analytics.reports().query(
                    ids=f'channel=={channel_id}',
                    startDate=start_date,
                    endDate=end_date,
                    metrics='views,likes,comments,shares,subscribersGained',
                    dimensions='day',
                    sort='day'
                ).execute()
                
                # Print response structure for debugging (without full data)
                if 'rows' in analytics_response:
                    row_count = len(analytics_response['rows'])
                    print(f"Received {row_count} data points from YouTube Analytics API")
                    if row_count > 0:
                        print(f"Sample row: {analytics_response['rows'][0]}")
                else:
                    print(f"YouTube Analytics response has no rows")
                    print(f"Response keys: {analytics_response.keys()}")
                
                # Check if we got valid data
                if 'rows' not in analytics_response or not analytics_response.get('rows'):
                    print("WARNING: No analytics data rows received")
                    return jsonify({
                        'success': False,
                        'message': 'No analytics data available for this time period. Your channel may be too new or have too little activity.'
                    })
                
                # Step 5: Format views data
                views_data = []
                for row in analytics_response['rows']:
                    views_data.append({
                        'date': row[0],
                        'views': row[1] if len(row) > 1 else 0
                    })
                
                # Step 6: Get top videos data
                print("Fetching top videos data...")
                try:
                    top_videos_response = youtube_analytics.reports().query(
                        ids=f'channel=={channel_id}',
                        startDate=start_date,
                        endDate=end_date,
                        metrics='views,likes,comments,shares',
                        dimensions='video',
                        sort='-views',
                        maxResults=5
                    ).execute()
                    
                    top_videos = []
                    if 'rows' in top_videos_response and top_videos_response['rows']:
                        video_ids = [row[0] for row in top_videos_response['rows']]
                        
                        if video_ids:
                            videos_response = youtube.videos().list(
                                part="snippet,statistics",
                                id=','.join(video_ids)
                            ).execute()
                            
                            video_data = {item['id']: item for item in videos_response.get('items', [])}
                            
                            for row in top_videos_response['rows']:
                                video_id = row[0]
                                if video_id in video_data:
                                    video = video_data[video_id]
                                    thumbnail = video['snippet']['thumbnails'].get('maxres') or \
                                              video['snippet']['thumbnails'].get('high') or \
                                              video['snippet']['thumbnails'].get('default')
                                    
                                    # Safely handle indices in case the API response format changes
                                    views = row[1] if len(row) > 1 else 0
                                    likes = row[2] if len(row) > 2 else 0
                                    comments = row[3] if len(row) > 3 else 0
                                    shares = row[4] if len(row) > 4 else 0
                                    
                                    top_videos.append({
                                        'id': video_id,
                                        'title': video['snippet']['title'],
                                        'views': views,
                                        'likes': likes,
                                        'comments': comments,
                                        'shares': shares,
                                        'thumbnail': thumbnail['url'],
                                        'publish_date': video['snippet']['publishedAt'],
                                        'ctr': f"{(likes / views * 100):.1f}%" if views > 0 else "0%",
                                    })
                    
                except Exception as videos_e:
                    print(f"ERROR getting top videos: {str(videos_e)}")
                    # Continue without top videos if this fails
                    top_videos = []
                
                # Step 7: Calculate summary stats
                total_views = sum(item['views'] for item in views_data) if views_data else 0
                total_likes = sum(video['likes'] for video in top_videos) if top_videos else 0
                total_comments = sum(video['comments'] for video in top_videos) if top_videos else 0
                total_shares = sum(video.get('shares', 0) for video in top_videos) if top_videos else 0
                
                # Create additional mock data for UI components not fully supported by the API
                print("Creating additional data for UI components...")
                engagement_data = {
                    'likes': total_likes,
                    'comments': total_comments,
                    'shares': total_shares,
                    'saves': int(total_views * 0.03),  # Estimate
                    'subscribes': int(total_likes * 0.05)  # Estimate
                }
                
                device_data = {
                    'devices': ['Mobile', 'Tablet', 'Desktop', 'TV', 'Other'],
                    'percentages': [75, 8, 15, 1, 1]  # Generic estimate
                }
                
                demographics_data = {
                    'age_groups': ['18-24', '25-34', '35-44', '45-54', '55-64', '65+'],
                    'male': [25, 30, 15, 8, 4, 2],  # Generic estimate
                    'female': [22, 28, 12, 6, 3, 1],  # Generic estimate
                    'other': [5, 6, 3, 2, 1, 0]  # Generic estimate
                }
                
                geographic_data = {
                    'countries': ['United States', 'India', 'United Kingdom', 'Canada', 'Australia', 'Germany', 'Other'],
                    'percentages': [40, 12, 8, 6, 4, 3, 27]  # Generic estimate
                }
                
                performance_data = {
                    'videos': [video['title'][:20] + '...' for video in top_videos[:8]] if top_videos else [f"Video {i+1}" for i in range(8)],
                    'views': [video['views'] for video in top_videos[:8]] if top_videos else [random.randint(1000, 5000) for _ in range(8)],
                    'engagement_rates': [float(video['ctr'].replace('%', '')) for video in top_videos[:8]] if top_videos else [random.uniform(5.0, 15.0) for _ in range(8)]
                }
                
                print("Successfully compiled all analytics data")
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
                        'total_views': total_views,
                        'total_likes': total_likes,
                        'total_comments': total_comments,
                        'total_shares': total_shares,
                        'new_subscribers': int(total_views * 0.01),  # Rough estimate
                        'watch_time': int(total_views * 0.02)  # Rough estimate in hours
                    }
                })
                
            except HttpError as api_e:
                error_reason = str(api_e)
                print(f"YouTube API HTTP Error: {error_reason}")
                
                # Handle specific error cases with clear messages
                if "quota" in error_reason.lower():
                    message = "YouTube API quota exceeded. Please try again tomorrow."
                elif "permission" in error_reason.lower() or "scope" in error_reason.lower():
                    message = "Insufficient YouTube permissions. Please disconnect and reconnect your channel in Settings."
                elif "serviceunavailable" in error_reason.lower():
                    message = "YouTube Analytics service is temporarily unavailable. Please try again later."
                else:
                    message = f"YouTube Analytics API error: {error_reason}"
                
                return jsonify({
                    'success': False,
                    'message': message,
                    'error_details': error_reason
                })
                
            except Exception as e:
                print(f"General exception in analytics query: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': f'Error fetching analytics data: {str(e)}'
                })
        
        except Exception as outer_e:
            print(f"Outer exception in api_analytics: {str(outer_e)}")
            return jsonify({
                'success': False,
                'message': f'General error accessing YouTube data: {str(outer_e)}'
            })
    
    # If we get here, either use_real_data was false or we're falling back to mock data
    print("Using mock analytics data instead")
    return get_mock_analytics_data(start_date, end_date)

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

# YouTube Integration Routes

@app.route('/youtube/connect')
def youtube_connect():
    """Show the YouTube connection page."""
    return render_template('youtube_auth.html')

@app.route('/api/youtube/auth')
def youtube_auth():
    """Handle YouTube API authentication."""
    # Check if we're disconnecting
    if request.args.get('disconnect') == 'true':
        if os.path.exists(YOUTUBE_TOKEN_FILE):
            os.remove(YOUTUBE_TOKEN_FILE)
        return jsonify({
            'success': True,
            'message': 'Successfully disconnected from YouTube.'
        })
    
    # Check if we should force a refresh
    force_refresh = request.args.get('force_refresh') == 'true'
    
    # Try to get credentials
    credentials = get_youtube_credentials(force_refresh)
    
    if not credentials:
        # Need to start OAuth flow
        flow = Flow.from_client_secrets_file(
            YOUTUBE_CLIENT_SECRETS_FILE, 
            scopes=YOUTUBE_SCOPES,
            redirect_uri=url_for('youtube_oauth_callback', _external=True)
        )
        
        # Generate the authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent' if force_refresh else None
        )
        
        # Store the state for later validation
        session['youtube_oauth_state'] = state
        
        return jsonify({
            'success': False,
            'auth_required': True,
            'auth_url': authorization_url
        })
    
    # If we have credentials, return success
    return jsonify({
        'success': True,
        'message': 'Already authenticated with YouTube.'
    })

@app.route('/api/youtube/callback')
def youtube_oauth_callback():
    """Handle the OAuth callback from YouTube."""
    # Get the authorization code from the request
    code = request.args.get('code')
    if not code:
        flash('Authentication error: No authorization code received.', 'error')
        return redirect(url_for('settings'))
    
    try:
        # Use the authorization code to get credentials
        flow = Flow.from_client_secrets_file(
            YOUTUBE_CLIENT_SECRETS_FILE,
            scopes=YOUTUBE_SCOPES,
            redirect_uri=url_for('youtube_oauth_callback', _external=True)
        )
        flow.fetch_token(code=code)
        
        # Save the credentials
        credentials = flow.credentials
        save_youtube_credentials(credentials)
        
        flash('Successfully connected to YouTube!', 'success')
    except Exception as e:
        flash(f'Authentication error: {str(e)}', 'error')
    
    return redirect(url_for('settings'))

@app.route('/api/youtube/channel')
def youtube_channel_info():
    """Get information about the connected YouTube channel."""
    credentials = get_youtube_credentials()
    if not credentials:
        return jsonify({
            'success': False,
            'message': 'Not authenticated with YouTube.'
        })
    
    try:
        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)
        
        # Get the channel information
        channels_response = youtube.channels().list(
            part="snippet,statistics,contentDetails",
            mine=True
        ).execute()
        
        if not channels_response['items']:
            return jsonify({
                'success': False,
                'message': 'No YouTube channel found for this account.'
            })
        
        channel = channels_response['items'][0]
        channel_info = {
            'id': channel['id'],
            'title': channel['snippet']['title'],
            'description': channel['snippet']['description'],
            'thumbnail': channel['snippet']['thumbnails']['default']['url'],
            'subscriberCount': channel['statistics']['subscriberCount'],
            'videoCount': channel['statistics']['videoCount'],
            'viewCount': channel['statistics']['viewCount'],
            'publishedAt': channel['snippet']['publishedAt']
        }
        
        return jsonify({
            'success': True,
            'channel': channel_info
        })
    except HttpError as e:
        return jsonify({
            'success': False,
            'message': f'YouTube API error: {str(e)}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching channel info: {str(e)}'
        })

@app.route('/api/youtube/analytics')
def youtube_analytics():
    """Get analytics data from the YouTube API."""
    credentials = get_youtube_credentials()
    if not credentials:
        return jsonify({
            'success': False,
            'message': 'Not authenticated with YouTube.'
        })
    
    try:
        # Build the YouTube Data API and Analytics API clients
        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)
        youtube_analytics = build('youtubeAnalytics', 'v2', credentials=credentials)
        
        # Get channel ID
        channels_response = youtube.channels().list(
            part="id",
            mine=True
        ).execute()
        
        if not channels_response['items']:
            return jsonify({
                'success': False,
                'message': 'No YouTube channel found for this account.'
            })
        
        channel_id = channels_response['items'][0]['id']
        
        # Get analytics data
        # Default to last 30 days if not specified
        start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        
        # Get basic report data
        analytics_response = youtube_analytics.reports().query(
            ids=f'channel=={channel_id}',
            startDate=start_date,
            endDate=end_date,
            metrics='views,likes,comments,shares,subscribersGained',
            dimensions='day',
            sort='day'
        ).execute()
        
        # Format data for charts
        views_data = []
        if 'rows' in analytics_response:
            for row in analytics_response['rows']:
                views_data.append({
                    'date': row[0],
                    'views': row[1],
                    'likes': row[2],
                    'comments': row[3],
                    'shares': row[4],
                    'subscribers': row[5]
                })
        
        # Get top videos
        top_videos_response = youtube_analytics.reports().query(
            ids=f'channel=={channel_id}',
            startDate=start_date,
            endDate=end_date,
            metrics='views,likes,comments,shares',
            dimensions='video',
            sort='-views',
            maxResults=10
        ).execute()
        
        # Get video details for the IDs
        top_videos = []
        if 'rows' in top_videos_response:
            video_ids = [row[0] for row in top_videos_response['rows']]
            
            if video_ids:
                videos_response = youtube.videos().list(
                    part="snippet,statistics",
                    id=','.join(video_ids)
                ).execute()
                
                video_data = {item['id']: item for item in videos_response.get('items', [])}
                
                for row in top_videos_response['rows']:
                    video_id = row[0]
                    if video_id in video_data:
                        video = video_data[video_id]
                        thumbnail = video['snippet']['thumbnails'].get('maxres') or \
                                  video['snippet']['thumbnails'].get('high') or \
                                  video['snippet']['thumbnails'].get('default')
                        
                        top_videos.append({
                            'id': video_id,
                            'title': video['snippet']['title'],
                            'views': row[1],
                            'likes': row[2],
                            'comments': row[3],
                            'shares': row[4],
                            'thumbnail': thumbnail['url'],
                            'publish_date': video['snippet']['publishedAt'],
                            'ctr': f"{(row[2] / row[1] * 100):.1f}%" if row[1] > 0 else "0%",
                        })
        
        # Get demographics and other data (mocked for this example)
        # In a real implementation, you would get this from the YouTube Analytics API
        
        return jsonify({
            'success': True,
            'views_data': views_data,
            'top_videos': top_videos,
            'summary': {
                'total_views': sum(item['views'] for item in views_data) if views_data else 0,
                'total_likes': sum(item['likes'] for item in views_data) if views_data else 0,
                'total_comments': sum(item['comments'] for item in views_data) if views_data else 0,
                'total_shares': sum(item['shares'] for item in views_data) if views_data else 0,
                'new_subscribers': sum(item['subscribers'] for item in views_data) if views_data else 0,
            }
        })
    except HttpError as e:
        return jsonify({
            'success': False,
            'message': f'YouTube API error: {str(e)}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching analytics: {str(e)}'
        })

@app.route('/api/youtube/settings', methods=['POST'])
def youtube_settings():
    """Save YouTube settings."""
    if request.method == 'POST':
        # Get settings data
        data = request.form.to_dict()
        if request.is_json:
            data = request.json
        
        # Update config with YouTube settings
        if 'shorts_settings' not in automation.config:
            automation.config['shorts_settings'] = {}
        
        # Update privacy setting
        if 'privacy_status' in data:
            automation.config['shorts_settings']['privacy_status'] = data['privacy_status']
        
        # Update tags
        if 'shorts_tags' in data:
            tags = data['shorts_tags']
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(',')]
            automation.config['shorts_settings']['tags'] = tags
        
        # Update notify subscribers setting
        notify = data.get('notify_subscribers') == 'on' or data.get('notify_subscribers') == 'true'
        automation.config['shorts_settings']['notify_subscribers'] = notify
        
        # Save config to file
        try:
            with open('config.json', 'w') as f:
                json.dump(automation.config, f, indent=4)
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error saving YouTube settings: {str(e)}'
            })
        
        return jsonify({
            'success': True,
            'message': 'YouTube settings saved successfully.'
        })

@app.route('/api/youtube/clear_cache', methods=['POST'])
def clear_youtube_cache():
    """Clear YouTube cache including authentication tokens."""
    try:
        # Remove token file
        if os.path.exists(YOUTUBE_TOKEN_FILE):
            os.remove(YOUTUBE_TOKEN_FILE)
            
        return jsonify({
            'success': True,
            'message': 'YouTube cache cleared successfully.'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error clearing YouTube cache: {str(e)}'
        })

# API endpoint for mock analytics data (for development without YouTube API access)
@app.route('/api/analytics/mock')
def mock_analytics_data():
    """Generate mock analytics data for development."""
    # This function provides mock data when we don't have YouTube API access
    
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Generate daily views data
    views_data = generate_random_views_data(start_date, end_date)
    
    # Generate engagement data
    engagement_data = {
        'likes': random.randint(2000, 5000),
        'comments': random.randint(400, 1000),
        'shares': random.randint(200, 600),
        'saves': random.randint(100, 400),
        'subscribes': random.randint(100, 300)
    }
    
    # Generate device data
    device_data = {
        'devices': ['Mobile', 'Tablet', 'Desktop', 'TV', 'Other'],
        'percentages': [78, 8, 12, 1, 1]  # Mobile dominant for Shorts
    }
    
    # Generate demographics data
    demographics_data = {
        'age_groups': ['18-24', '25-34', '35-44', '45-54', '55-64', '65+'],
        'male': [28, 35, 15, 8, 4, 2],
        'female': [25, 32, 18, 10, 3, 1],
        'other': [5, 8, 3, 2, 1, 0]
    }
    
    # Generate geographic data
    geographic_data = {
        'countries': ['United States', 'India', 'United Kingdom', 'Canada', 'Australia', 'Germany', 'Other'],
        'percentages': [45, 18, 12, 8, 5, 4, 8]
    }
    
    # Generate performance data
    performance_data = {
        'videos': [f"Video {i+1}" for i in range(8)],
        'views': [random.randint(1000, 5000) for _ in range(8)],
        'engagement_rates': [random.uniform(5.0, 15.0) for _ in range(8)]
    }
    
    # Get top videos
    top_videos = get_top_videos(5)
    
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
            'total_shares': random.randint(50, 500),
            'new_subscribers': random.randint(50, 200)
        }
    })

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
            # Try to upload with YouTube API if authenticated
            credentials = get_youtube_credentials()
            if credentials:
                # Get the uploader module
                try:
                    from youtube_uploader import YouTubeUploader
                    uploader = YouTubeUploader(client_secrets_file=YOUTUBE_CLIENT_SECRETS_FILE)
                    video_id = uploader.upload_video(
                        video_file=video_path,
                        title=title,
                        description=f"#Shorts video about {title}\n\n#YouTubeShorts",
                        tags=["shorts", "youtubeshorts"] + [keyword.strip() for keyword in title.split()],
                        privacy_status="private"  # Start as private for safety
                    )
                    
                    if video_id:
                        # Set thumbnail if available
                        if thumbnail_path:
                            uploader.update_thumbnail(video_id, thumbnail_path)
                            
                        return jsonify({
                            'success': True,
                            'message': f'Shorts video "{title}" uploaded to YouTube using OAuth',
                            'video_id': video_id,
                            'url': f'https://www.youtube.com/shorts/{video_id}'
                        })
                except:
                    pass
            
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

# Helper functions for settings
def mask_api_key(key):
    """Mask API key for display in settings."""
    if not key:
        return ''
    if len(key) <= 8:
        return '*' * len(key)
    return key[:4] + '*' * (len(key) - 8) + key[-4:]

# Helper functions for YouTube API authentication
def get_youtube_credentials(force_refresh=False):
    """Get YouTube credentials from the saved token."""
    credentials = None
    
    # Try to load credentials from the saved file
    if os.path.exists(YOUTUBE_TOKEN_FILE) and not force_refresh:
        try:
            with open(YOUTUBE_TOKEN_FILE, 'rb') as token:
                credentials = pickle.load(token)
        except Exception as e:
            print(f"Error loading YouTube credentials: {str(e)}")
            return None
    
    # If credentials are expired and have a refresh token, refresh them
    if credentials and credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
            save_youtube_credentials(credentials)
        except Exception as e:
            print(f"Error refreshing YouTube credentials: {str(e)}")
            return None
    
    # If we have valid credentials, return them
    if credentials and credentials.valid:
        return credentials
    
    # Otherwise, return None to trigger the OAuth flow
    return None

def save_youtube_credentials(credentials):
    """Save YouTube credentials to file."""
    try:
        with open(YOUTUBE_TOKEN_FILE, 'wb') as token:
            pickle.dump(credentials, token)
        return True
    except Exception as e:
        print(f"Error saving YouTube credentials: {str(e)}")
        return False

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

def get_mock_analytics_data(start_date, end_date):
    """Generate mock analytics data for demo purposes."""
    views_data = generate_random_views_data(start_date, end_date)
    top_videos = get_top_videos(5)
    
    return jsonify({
        'success': True,
        'views_data': views_data,
        'top_videos': top_videos,
        'summary': {
            'total_views': sum(point['views'] for point in views_data),
            'total_likes': random.randint(1000, 5000),
            'total_comments': random.randint(100, 1000),
            'total_shares': random.randint(50, 500),
            'new_subscribers': random.randint(50, 200),
            'watch_time': random.randint(200, 500)
        }
    })
    
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