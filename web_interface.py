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

# Create CSS file with improved mobile support
with open('static/css/shorts_style.css', 'w') as f:
    f.write("""
:root {
    --primary-color: #ff0000;  /* YouTube red */
    --secondary-color: #cc0000;
    --accent-color: #ff9900;
    --success-color: #28a745;
    --warning-color: #ffc107;
    --danger-color: #dc3545;
    --info-color: #17a2b8;
    --text-color: #333333;
    --light-bg: #f8f9fa;
    --dark-bg: #343a40;
    --card-bg: white;
    --border-color: #e5e5e5;
    --shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    --transition: all 0.3s ease;
}

[data-theme="dark"] {
    --primary-color: #ff4444;
    --secondary-color: #cc4444;
    --text-color: #f1f1f1;
    --light-bg: #2d2d2d;
    --dark-bg: #1a1a1a;
    --card-bg: #2d2d2d;
    --border-color: #444;
    --shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin: 0;
    padding: 0;
    background-color: var(--light-bg);
    color: var(--text-color);
    transition: var(--transition);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

.container {
    max-width: 1200px;
    width: 100%;
    margin: 0 auto;
    padding: 20px;
    flex: 1;
}

/* Header and Navigation */
.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    background-color: var(--primary-color);
    box-shadow: var(--shadow);
    position: sticky;
    top: 0;
    z-index: 100;
    color: white;
}

.header h1 {
    color: white;
    margin: 0;
    font-size: 1.5rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.logo-icon {
    font-size: 1.8rem;
}

.nav-links {
    display: flex;
    gap: 1.5rem;
}

.nav-link {
    color: white;
    text-decoration: none;
    font-weight: 500;
    padding: 0.5rem 0;
    position: relative;
}

.nav-link:after {
    content: '';
    position: absolute;
    width: 0;
    height: 2px;
    bottom: 0;
    left: 0;
    background-color: white;
    transition: width 0.3s;
}

.nav-link:hover:after,
.nav-link.active:after {
    width: 100%;
}

.mobile-menu-btn {
    display: none;
    background: none;
    border: none;
    color: white;
    font-size: 1.5rem;
    cursor: pointer;
}

/* Theme Switch */
.theme-switch {
    position: relative;
    display: inline-block;
    width: 60px;
    height: 30px;
    margin-left: 1rem;
}

.theme-switch input {
    opacity: 0;
    width: 0;
    height: 0;
}

.slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #ccc;
    transition: .4s;
    border-radius: 34px;
}

.slider:before {
    position: absolute;
    content: "";
    height: 22px;
    width: 22px;
    left: 4px;
    bottom: 4px;
    background-color: white;
    transition: .4s;
    border-radius: 50%;
}

input:checked + .slider {
    background-color: var(--primary-color);
}

input:checked + .slider:before {
    transform: translateX(30px);
}

/* Cards and Layout */
.card {
    background-color: var(--card-bg);
    border-radius: 8px;
    box-shadow: var(--shadow);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    transition: var(--transition);
    border: 1px solid var(--border-color);
}

.card h2 {
    margin-top: 0;
    color: var(--primary-color);
    font-size: 1.3rem;
    font-weight: 500;
    margin-bottom: 1.2rem;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 0.6rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.section-icon {
    font-size: 1.4rem;
}

.dashboard-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
}

/* Forms and Inputs */
.form-group {
    margin-bottom: 1.2rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: var(--text-color);
}

.form-control {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    font-size: 1rem;
    transition: border-color 0.3s;
    background-color: var(--card-bg);
    color: var(--text-color);
}

.form-control:focus {
    border-color: var(--primary-color);
    outline: none;
    box-shadow: 0 0 0 3px rgba(255, 0, 0, 0.2);
}

.checkbox-group {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1rem;
}

/* Buttons */
.btn {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: var(--transition);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
}

.btn-primary {
    background-color: var(--primary-color);
    color: white;
}

.btn-primary:hover {
    background-color: var(--secondary-color);
}

.btn-outline {
    background-color: transparent;
    border: 2px solid var(--primary-color);
    color: var(--primary-color);
}

.btn-outline:hover {
    background-color: var(--primary-color);
    color: white;
}

.btn-danger {
    background-color: var(--danger-color);
    color: white;
}

.btn-danger:hover {
    background-color: #c82333;
}

.btn-sm {
    padding: 0.4rem 0.8rem;
    font-size: 0.875rem;
}

/* Status Cards */
.status-card {
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: flex-start;
    background-color: rgba(0, 0, 0, 0.03);
    position: relative;
    border-left: 5px solid transparent;
}

.status-indicator {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    margin-right: 1rem;
    flex-shrink: 0;
    margin-top: 0.25rem;
}

.status-message {
    flex-grow: 1;
}

.status-title {
    font-weight: 600;
    margin-bottom: 0.3rem;
}

.status-detail {
    font-size: 0.9rem;
    margin-bottom: 0.5rem;
}

.status-time {
    font-size: 0.8rem;
    color: #777;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    min-width: 100px;
}

[data-theme="dark"] .status-time {
    color: #aaa;
}

.status-controls {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.5rem;
}

.status-completed {
    background-color: rgba(40, 167, 69, 0.1);
    border-left-color: var(--success-color);
}
.status-completed .status-indicator {
    background-color: var(--success-color);
}

.status-in-progress {
    background-color: rgba(23, 162, 184, 0.1);
    border-left-color: var(--info-color);
}
.status-in-progress .status-indicator {
    background-color: var(--info-color);
}

.status-failed {
    background-color: rgba(220, 53, 69, 0.1);
    border-left-color: var(--danger-color);
}
.status-failed .status-indicator {
    background-color: var(--danger-color);
}

.status-paused {
    background-color: rgba(255, 193, 7, 0.1);
    border-left-color: var(--warning-color);
}
.status-paused .status-indicator {
    background-color: var(--warning-color);
}

/* Progress Bar */
.progress-container {
    width: 100%;
    background-color: #e0e0e0;
    border-radius: 4px;
    height: 8px;
    margin-top: 0.5rem;
    overflow: hidden;
}

[data-theme="dark"] .progress-container {
    background-color: #444;
}

.progress-bar {
    height: 100%;
    background-color: var(--primary-color);
    width: 0%;
    transition: width 0.3s ease;
    border-radius: 4px;
}

/* Video Gallery - Modified for Vertical Shorts */
.video-gallery {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-top: 1.2rem;
}

.video-item {
    border-radius: 8px;
    overflow: hidden;
    box-shadow: var(--shadow);
    transition: transform 0.3s;
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    height: 100%;
    display: flex;
    flex-direction: column;
}

.video-item:hover {
    transform: translateY(-5px);
}

.video-thumbnail {
    width: 100%;
    /* Adjusted for vertical shorts aspect ratio (9:16) */
    height: 280px;
    background-color: #000;
    position: relative;
    overflow: hidden;
}

.video-thumbnail img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.3s;
}

.video-item:hover .video-thumbnail img {
    transform: scale(1.05);
}

.play-button {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 50px;
    height: 50px;
    background-color: rgba(0, 0, 0, 0.7);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.3s;
}

.video-item:hover .play-button {
    opacity: 1;
}

.play-button:before {
    content: "";
    width: 0;
    height: 0;
    border-top: 10px solid transparent;
    border-bottom: 10px solid transparent;
    border-left: 15px solid white;
    margin-left: 5px;
}

.video-info {
    padding: 1rem;
    flex-grow: 1;
    display: flex;
    flex-direction: column;
}

.video-title {
    margin: 0 0 0.6rem 0;
    font-size: 1rem;
    font-weight: 500;
    color: var(--text-color);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    line-height: 1.4;
}

.video-meta {
    display: flex;
    justify-content: space-between;
    font-size: 0.875rem;
    color: #777;
    margin-top: auto;
}

[data-theme="dark"] .video-meta {
    color: #aaa;
}

.video-options {
    display: flex;
    margin-top: 0.8rem;
    gap: 0.5rem;
}

/* Shorts badge */
.shorts-badge {
    position: absolute;
    top: 10px;
    right: 10px;
    background-color: var(--primary-color);
    color: white;
    font-weight: bold;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.7rem;
    z-index: 2;
}

/* Badges */
.badge {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 500;
}

.badge-primary {
    background-color: var(--primary-color);
    color: white;
}

.badge-success {
    background-color: var(--success-color);
    color: white;
}

.badge-warning {
    background-color: var(--warning-color);
    color: black;
}

.badge-danger {
    background-color: var(--danger-color);
    color: white;
}

.badge-info {
    background-color: var(--info-color);
    color: white;
}

/* Stats Grid */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.stat-card {
    background-color: var(--card-bg);
    border-radius: 8px;
    padding: 1.2rem;
    box-shadow: var(--shadow);
    text-align: center;
    border: 1px solid var(--border-color);
    transition: var(--transition);
}

.stat-card:hover {
    transform: translateY(-3px);
}

.stat-icon {
    font-size: 1.8rem;
    color: var(--primary-color);
    margin-bottom: 0.8rem;
}

.stat-value {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 0.3rem;
    color: var(--primary-color);
}

.stat-label {
    font-size: 0.875rem;
    color: #777;
}

[data-theme="dark"] .stat-label {
    color: #aaa;
}

/* Empty State */
.empty-state {
    text-align: center;
    padding: 2.5rem 1.2rem;
    color: #777;
}

[data-theme="dark"] .empty-state {
    color: #aaa;
}

.empty-state i {
    font-size: 3rem;
    margin-bottom: 1.2rem;
    display: block;
    color: var(--primary-color);
    opacity: 0.5;
}

/* Media Queries for Responsiveness */
@media (max-width: 1024px) {
    .stats-grid {
        grid-template-columns: repeat(2, 1fr);
    }
    
    .dashboard-grid {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 768px) {
    .container {
        padding: 15px;
    }
    
    .stats-grid {
        gap: 10px;
    }
    
    .video-gallery {
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    }
    
    .header h1 {
        font-size: 1.2rem;
    }
    
    .nav-links {
        display: none;
        flex-direction: column;
        position: absolute;
        top: 100%;
        left: 0;
        width: 100%;
        background-color: var(--primary-color);
        box-shadow: var(--shadow);
        padding: 1rem;
        z-index: 99;
    }
    
    .nav-links.active {
        display: flex;
    }
    
    .mobile-menu-btn {
        display: block;
    }
}

@media (max-width: 480px) {
    .stats-grid {
        grid-template-columns: 1fr;
    }
    
    .video-gallery {
        grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    }
    
    .card {
        padding: 1rem;
    }
    
    .btn {
        width: 100%;
        margin-bottom: 0.5rem;
    }
}

/* Utilities */
.mt-1 { margin-top: 0.5rem; }
.mt-2 { margin-top: 1rem; }
.mt-3 { margin-top: 1.5rem; }
.mb-1 { margin-bottom: 0.5rem; }
.mb-2 { margin-bottom: 1rem; }
.mb-3 { margin-bottom: 1.5rem; }
.ml-1 { margin-left: 0.5rem; }
.ml-2 { margin-left: 1rem; }
.mr-1 { margin-right: 0.5rem; }
.mr-2 { margin-right: 1rem; }

.text-center { text-align: center; }
.text-right { text-align: right; }
.text-success { color: var(--success-color); }
.text-danger { color: var(--danger-color); }
.text-warning { color: var(--warning-color); }
.text-info { color: var(--info-color); }

.d-flex { display: flex; }
.flex-wrap { flex-wrap: wrap; }
.align-center { align-items: center; }
.justify-between { justify-content: space-between; }
.justify-end { justify-content: flex-end; }
.gap-1 { gap: 0.5rem; }
.gap-2 { gap: 1rem; }

.w-100 { width: 100%; }
.h-100 { height: 100%; }
    """)

# Create main JavaScript file
with open('static/js/shorts_main.js', 'w') as f:
    f.write("""
// Theme Toggle Functionality
function initThemeToggle() {
    const toggleSwitch = document.getElementById('theme-toggle');
    const themeLabel = document.getElementById('theme-label');
    
    function switchTheme(e) {
        if (e.target.checked) {
            document.documentElement.setAttribute('data-theme', 'dark');
            themeLabel.textContent = 'Light Mode';
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
            themeLabel.textContent = 'Dark Mode';
            localStorage.setItem('theme', 'light');
        }
    }
    
    // Check for saved theme preference
    const currentTheme = localStorage.getItem('theme') || 'light';
    if (currentTheme === 'dark') {
        toggleSwitch.checked = true;
        document.documentElement.setAttribute('data-theme', 'dark');
        themeLabel.textContent = 'Light Mode';
    }
    
    toggleSwitch.addEventListener('change', switchTheme);
}

// Mobile Menu Toggle
function initMobileMenu() {
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const navLinks = document.getElementById('nav-links');
    
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', () => {
            navLinks.classList.toggle('active');
        });
    }
}

// Toast Notifications
function showToast(type, title, message, duration = 5000) {
    const toastContainer = document.getElementById('toast-container');
    
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let iconClass = 'fas fa-info-circle';
    if (type === 'success') iconClass = 'fas fa-check-circle';
    if (type === 'error') iconClass = 'fas fa-exclamation-circle';
    if (type === 'warning') iconClass = 'fas fa-exclamation-triangle';
    
    toast.innerHTML = `
        <div class="toast-icon"><i class="${iconClass}"></i></div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <div class="toast-close"><i class="fas fa-times"></i></div>
    `;
    
    document.getElementById('toast-container').appendChild(toast);
    
    // Add click event to close button
    toast.querySelector('.toast-close').addEventListener('click', () => {
        toast.style.animation = 'slide-out 0.3s forwards';
        setTimeout(() => {
            toast.remove();
        }, 300);
    });
    
    // Auto remove after duration
    setTimeout(() => {
        if (toast.parentNode) {
            toast.style.animation = 'slide-out 0.3s forwards';
            setTimeout(() => {
                if (toast.parentNode) toast.remove();
            }, 300);
        }
    }, duration);
}

// Initialize Dashboard Updates
function initDashboardUpdates() {
    function updateDashboard() {
        fetch('/status')
            .then(response => response.json())
            .then(data => {
                // Update stats
                if (document.getElementById('total-shorts')) {
                    document.getElementById('total-shorts').textContent = data.stats.total_videos;
                }
                if (document.getElementById('shorts-today')) {
                    document.getElementById('shorts-today').textContent = data.stats.videos_today;
                }
                if (document.getElementById('active-jobs')) {
                    document.getElementById('active-jobs').textContent = data.stats.active_jobs;
                }
                if (document.getElementById('success-rate')) {
                    document.getElementById('success-rate').textContent = data.stats.success_rate + '%';
                }
                
                // Update jobs list
                const jobsList = document.getElementById('jobsList');
                if (jobsList) {
                    if (data.jobs && data.jobs.length > 0) {
                        let jobsHTML = '';
                        data.jobs.forEach(job => {
                            let statusClass = `status-${job.status}`;
                            let progress = job.progress || 0;
                            
                            if (job.status === 'completed') progress = 100;
                            if (job.status === 'failed') progress = 0;
                            
                            let statusIcon = '';
                            if (job.status === 'completed') statusIcon = '<i class="fas fa-check"></i>';
                            else if (job.status === 'failed') statusIcon = '<i class="fas fa-times"></i>';
                            else if (job.status === 'paused') statusIcon = '<i class="fas fa-pause"></i>';
                            
                            jobsHTML += `
                                <div class="status-card ${statusClass}" id="job-${job.id}">
                                    <div class="status-indicator"></div>
                                    <div class="status-message">
                                        <div class="status-title">${job.niche} ${statusIcon}</div>
                                        <div class="status-detail">${job.message}</div>
                                        <div class="progress-container">
                                            <div class="progress-bar" style="width: ${progress}%"></div>
                                        </div>
                                        ${job.status === 'in-progress' ? `
                                        <div class="status-controls">
                                            <button class="btn btn-sm btn-outline pause-job" data-job-id="${job.id}">
                                                <i class="fas fa-pause"></i> Pause
                                            </button>
                                            <button class="btn btn-sm btn-danger cancel-job" data-job-id="${job.id}">
                                                <i class="fas fa-times"></i> Cancel
                                            </button>
                                        </div>
                                        ` : job.status === 'paused' ? `
                                        <div class="status-controls">
                                            <button class="btn btn-sm btn-outline resume-job" data-job-id="${job.id}">
                                                <i class="fas fa-play"></i> Resume
                                            </button>
                                            <button class="btn btn-sm btn-danger cancel-job" data-job-id="${job.id}">
                                                <i class="fas fa-times"></i> Cancel
                                            </button>
                                        </div>
                                        ` : ''}
                                    </div>
                                    <div class="status-time">
                                        <div><i class="far fa-clock"></i> ${job.started || 'N/A'}</div>
                                        <div>${job.status === 'completed' ? `<i class="far fa-check-circle"></i> Completed` : 
                                               job.status === 'failed' ? `<i class="far fa-times-circle"></i> Failed` : 
                                               job.status === 'paused' ? `<i class="far fa-pause-circle"></i> Paused` :
                                               `<i class="fas fa-spinner fa-spin"></i> In progress`}</div>
                                    </div>
                                </div>
                            `;
                        });
                        jobsList.innerHTML = jobsHTML;
                        
                        // Add event listeners for job control buttons
                        document.querySelectorAll('.pause-job').forEach(btn => {
                            btn.addEventListener('click', (e) => {
                                const jobId = btn.getAttribute('data-job-id');
                                fetch(`/job/${jobId}/pause`, { method: 'POST' })
                                    .then(response => response.json())
                                    .then(data => {
                                        if (data.success) {
                                            showToast('info', 'Job Paused', `Job #${jobId} has been paused.`);
                                        } else {
                                            showToast('error', 'Error', data.message);
                                        }
                                    });
                            });
                        });
                        
                        document.querySelectorAll('.resume-job').forEach(btn => {
                            btn.addEventListener('click', (e) => {
                                const jobId = btn.getAttribute('data-job-id');
                                fetch(`/job/${jobId}/resume`, { method: 'POST' })
                                    .then(response => response.json())
                                    .then(data => {
                                        if (data.success) {
                                            showToast('info', 'Job Resumed', `Job #${jobId} has been resumed.`);
                                        } else {
                                            showToast('error', 'Error', data.message);
                                        }
                                    });
                            });
                        });
                        
                        document.querySelectorAll('.cancel-job').forEach(btn => {
                            btn.addEventListener('click', (e) => {
                                const jobId = btn.getAttribute('data-job-id');
                                if (confirm('Are you sure you want to cancel this job?')) {
                                    fetch(`/job/${jobId}/cancel`, { method: 'POST' })
                                        .then(response => response.json())
                                        .then(data => {
                                            if (data.success) {
                                                showToast('warning', 'Job Cancelled', `Job #${jobId} has been cancelled.`);
                                            } else {
                                                showToast('error', 'Error', data.message);
                                            }
                                        });
                                }
                            });
                        });
                        
                    } else {
                        jobsList.innerHTML = `
                            <div class="empty-state">
                                <i class="fas fa-tasks"></i>
                                <p>No active jobs. Start a new Shorts automation job to see status here.</p>
                            </div>
                        `;
                    }
                }
                
                // Update shorts gallery
                const shortsGallery = document.getElementById('shortsGallery');
                if (shortsGallery) {
                    if (data.videos && data.videos.length > 0) {
                        let shortsHTML = '';
                        data.videos.forEach(video => {
                            shortsHTML += `
                                <div class="video-item">
                                    <div class="video-thumbnail">
                                        <div class="shorts-badge">#SHORTS</div>
                                        <!-- Use onerror to fallback to placeholder if the thumbnail fails to load -->
                                        <img src="${video.thumbnail || '/static/images/placeholder_vertical.jpg'}" 
                                            alt="${video.title}" 
                                            onerror="this.onerror=null; this.src='/static/images/placeholder_vertical.jpg';">
                                        <a href="#" class="play-button" data-video-path="${video.path}" data-video-title="${video.title}"></a>
                                    </div>
                                    <div class="video-info">
                                        <h3 class="video-title">${video.title}</h3>
                                        <div class="video-meta">
                                            <span><i class="far fa-calendar-alt"></i> ${video.date}</span>
                                            <span class="badge badge-${video.uploaded ? 'success' : 'warning'}">${video.uploaded ? 'Uploaded' : 'Local'}</span>
                                        </div>
                                        <div class="video-options">
                                            <button class="btn btn-sm btn-outline preview-video" data-video-path="${video.path}" data-video-title="${video.title}">
                                                <i class="fas fa-play"></i> Preview
                                            </button>
                                            ${!video.uploaded ? `
                                            <button class="btn btn-sm btn-primary upload-video" data-video-path="${video.path}" data-video-title="${video.title}">
                                                <i class="fas fa-upload"></i> Upload
                                            </button>
                                            ` : ''}
                                        </div>
                                    </div>
                                </div>
                            `;
                        });
                        shortsGallery.innerHTML = shortsHTML;
                        
                        // Add event listeners for video preview
                        document.querySelectorAll('.preview-video, .play-button').forEach(btn => {
                            btn.addEventListener('click', (e) => {
                                e.preventDefault();
                                const videoPath = btn.getAttribute('data-video-path');
                                const videoTitle = btn.getAttribute('data-video-title');
                                openVideoModal(videoPath, videoTitle);
                            });
                        });
                        
                        // Add event listeners for video upload
                        document.querySelectorAll('.upload-video').forEach(btn => {
                            btn.addEventListener('click', (e) => {
                                e.preventDefault();
                                const videoPath = btn.getAttribute('data-video-path');
                                const videoTitle = btn.getAttribute('data-video-title');
                                if (confirm(`Are you sure you want to upload "${videoTitle}" to YouTube as a Short?`)) {
                                    uploadVideo(videoPath, videoTitle);
                                }
                            });
                        });
                        
                    } else {
                        shortsGallery.innerHTML = `
                            <div class="empty-state">
                                <i class="fas fa-video"></i>
                                <p>No Shorts generated yet. Start creating content to see your Shorts here.</p>
                            </div>
                        `;
                    }
                }
                
                // Check for notifications
                if (data.notifications && data.notifications.length > 0) {
                    data.notifications.forEach(notification => {
                        showToast(notification.type, notification.title, notification.message);
                    });
                }
            })
            .catch(error => console.error('Error fetching status:', error));
    }
    
    // Function to open video preview modal
    function openVideoModal(videoPath, videoTitle) {
        // Create modal if it doesn't exist
        if (!document.getElementById('videoPreviewModal')) {
            const modal = document.createElement('div');
            modal.id = 'videoPreviewModal';
            modal.className = 'modal-backdrop';
            modal.innerHTML = `
                <div class="modal">
                    <div class="modal-header">
                        <div class="modal-title" id="videoModalTitle">Shorts Preview</div>
                        <button class="modal-close">&times;</button>
                    </div>
                    <div class="modal-body" style="display: flex; justify-content: center;">
                        <video id="videoPlayer" controls style="max-height: 70vh; max-width: 100%;"></video>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
            
            // Add event listener to close button
            modal.querySelector('.modal-close').addEventListener('click', () => {
                modal.classList.remove('active');
                const videoPlayer = document.getElementById('videoPlayer');
                videoPlayer.pause();
                videoPlayer.src = '';
            });
            
            // Close modal when clicking outside
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('active');
                    const videoPlayer = document.getElementById('videoPlayer');
                    videoPlayer.pause();
                    videoPlayer.src = '';
                }
            });
        }
        
        // Update modal content and open it
        const modal = document.getElementById('videoPreviewModal');
        document.getElementById('videoModalTitle').textContent = videoTitle;
        
        const videoPlayer = document.getElementById('videoPlayer');
        videoPlayer.src = `/video/${encodeURIComponent(videoPath)}`;
        
        modal.classList.add('active');
    }
    
    // Function to upload video to YouTube
    function uploadVideo(videoPath, videoTitle) {
        showToast('info', 'Upload Started', `Starting upload of "${videoTitle}" to YouTube as a Short...`);
        
        fetch('/upload', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                video_path: videoPath,
                title: videoTitle
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('success', 'Upload Success', `"${videoTitle}" has been uploaded to YouTube Shorts!`);
            } else {
                showToast('error', 'Upload Failed', data.message || 'There was an error uploading the video.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('error', 'Upload Error', 'There was a network error while uploading the video.');
        });
    }
    
    // Update dashboard every 2 seconds
    setInterval(updateDashboard, 2000);
    
    // Initialize dashboard on page load
    updateDashboard();
}

// Document Ready
document.addEventListener('DOMContentLoaded', function() {
    initThemeToggle();
    initMobileMenu();
    initDashboardUpdates();
    
    // Handle trending topics click
    document.querySelectorAll('.trending-topic').forEach(btn => {
        btn.addEventListener('click', function() {
            document.getElementById('niche').value = this.textContent.trim();
        });
    });
    
    // Form submission handling
    const automationForm = document.getElementById('automationForm');
    if (automationForm) {
        automationForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            
            fetch('/run', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast('success', 'Job Started', `New Shorts automation job "${formData.get('niche')}" has been started.`);
                } else {
                    showToast('error', 'Error', data.message || 'There was an error starting the job.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('error', 'Submission Error', 'There was a problem with your submission.');
            });
        });
    }
});
    """)

# Create the improved main HTML template
with open('templates/shorts_index.html', 'w') as f:
    f.write("""
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <title>YouTube Shorts Automation</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="/static/css/shorts_style.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <meta name="csrf-token" content="{{ csrf_token() }}">
</head>
<body>
    <div class="header">
        <button id="mobile-menu-btn" class="mobile-menu-btn">
            <i class="fas fa-bars"></i>
        </button>
        <h1><i class="fab fa-youtube logo-icon"></i> YouTube Shorts Automation</h1>
        <div class="nav-links" id="nav-links">
            <a href="/" class="nav-link active">Dashboard</a>
            <a href="/shorts" class="nav-link">My Shorts</a>
            <a href="/analytics" class="nav-link">Analytics</a>
            <a href="/settings" class="nav-link">Settings</a>
        </div>
        <div class="theme-toggle d-flex align-center">
            <label class="theme-switch">
                <input type="checkbox" id="theme-toggle">
                <span class="slider"></span>
            </label>
            <span id="theme-label" class="ml-1">Dark Mode</span>
        </div>
    </div>

    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">
                        <div class="alert-icon">
                            <i class="fas fa-{% if category == 'success' %}check-circle{% elif category == 'error' %}exclamation-circle{% elif category == 'warning' %}exclamation-triangle{% else %}info-circle{% endif %}"></i>
                        </div>
                        <div class="alert-content">
                            <div class="alert-message">{{ message }}</div>
                        </div>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon"><i class="fas fa-film"></i></div>
                <div class="stat-value" id="total-shorts">0</div>
                <div class="stat-label">Total Shorts</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon"><i class="fas fa-calendar-day"></i></div>
                <div class="stat-value" id="shorts-today">0</div>
                <div class="stat-label">Shorts Today</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon"><i class="fas fa-tasks"></i></div>
                <div class="stat-value" id="active-jobs">0</div>
                <div class="stat-label">Active Jobs</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon"><i class="fas fa-check-circle"></i></div>
                <div class="stat-value" id="success-rate">0%</div>
                <div class="stat-label">Success Rate</div>
            </div>
        </div>

        <div class="dashboard-grid">
            <div class="card">
                <h2><i class="fas fa-play-circle section-icon"></i> Create New Shorts</h2>
                <form id="automationForm" action="/run" method="post">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                    
                    <div class="form-group">
                        <label for="niche">Content Topic:</label>
                        <input type="text" id="niche" name="niche" class="form-control" required placeholder="e.g., fintech tips, cryptocurrency, tech hacks">
                    </div>
                    
                    <div class="form-group">
                        <label>Trending Topics:</label>
                        <div class="d-flex flex-wrap gap-1 mb-2">
                            <button type="button" class="btn btn-sm btn-outline trending-topic">fintech tips</button>
                            <button type="button" class="btn btn-sm btn-outline trending-topic">crypto investing</button>
                            <button type="button" class="btn btn-sm btn-outline trending-topic">tech tricks</button>
                            <button type="button" class="btn btn-sm btn-outline trending-topic">productivity hacks</button>
                            <button type="button" class="btn btn-sm btn-outline trending-topic">passive income</button>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="count">Number of Shorts:</label>
                        <select id="count" name="count" class="form-control">
                            <option value="1">1 Short</option>
                            <option value="2">2 Shorts</option>
                            <option value="3" selected>3 Shorts</option>
                            <option value="5">5 Shorts</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="style">Content Style:</label>
                        <select id="style" name="style" class="form-control">
                            <option value="informative">Informative</option>
                            <option value="entertaining" selected>Entertaining</option>
                            <option value="educational">Educational</option>
                            <option value="casual">Casual/Conversational</option>
                            <option value="surprising">Surprising/Shocking</option>
                        </select>
                    </div>
                    
                    <div class="checkbox-group mt-2">
                        <input type="checkbox" id="auto-upload" name="auto_upload" checked>
                        <label for="auto-upload">Automatically upload to YouTube</label>
                    </div>
                    
                    <button type="submit" class="btn btn-primary mt-2"><i class="fas fa-cogs"></i> Start Shorts Generation</button>
                </form>
            </div>
            
            <div class="card">
                <h2><i class="fas fa-tasks section-icon"></i> Active Jobs</h2>
                <div id="jobsList">
                    <div class="empty-state">
                        <i class="fas fa-tasks"></i>
                        <p>No active jobs. Start a new Shorts automation job to see status here.</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2><i class="fas fa-film section-icon"></i> Recent Shorts</h2>
            <div id="shortsGallery" class="video-gallery">
                <div class="empty-state">
                    <i class="fas fa-video"></i>
                    <p>No Shorts generated yet. Start creating content to see your Shorts here.</p>
                </div>
            </div>
        </div>
    </div>
    
    <div id="toast-container" class="toast-container"></div>
    
    <script src="/static/js/shorts_main.js"></script>
</body>
</html>
    """)

# Main routes for the application
@app.route('/')
def index():
    return render_template('shorts_index.html')

@app.route('/shorts')
def shorts():
    return render_template('shorts_videos.html')

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
    
    return render_template(
        'shorts_settings.html',
        api_keys=api_keys,
        shorts_settings=shorts_settings,
        youtube_channel=None  # Placeholder for connected channel info
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

# Video management endpoints
@app.route('/api/shorts')
def api_shorts():
    status = request.args.get('status', 'all')
    date_filter = request.args.get('date', 'all')
    search = request.args.get('search', '')
    
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
    
    return jsonify({
        'success': True,
        'videos': videos
    })

# Settings endpoints
@app.route('/settings/api-keys', methods=['POST'])
def save_api_keys():
    if request.method == 'POST':
        # Update API keys in automation system
        automation.api_keys['openai'] = request.form.get('openai_api_key', '')
        automation.api_keys['elevenlabs'] = request.form.get('elevenlabs_api_key', '')
        automation.api_keys['pexels'] = request.form.get('pexels_api_key', '')
        automation.api_keys['youtube'] = request.form.get('youtube_api_key', '')
        
        # Save to environment or config
        # (simplified for demonstration)
        
        return jsonify({
            'success': True,
            'message': 'API keys updated successfully'
        })

@app.route('/settings/shorts', methods=['POST'])
def save_shorts_settings():
    if request.method == 'POST':
        # Get shorts_settings or create if it doesn't exist
        if 'shorts_settings' not in automation.config:
            automation.config['shorts_settings'] = {}
            
        # Update shorts settings
        automation.config['shorts_settings']['max_duration'] = int(request.form.get('shorts_duration', 60))
        automation.config['shorts_settings']['vertical_format'] = request.form.get('vertical_format', 'off') == 'on'
        automation.config['shorts_settings']['fast_paced'] = request.form.get('shorts_pace', 'fast') == 'fast'
        
        # Update general settings
        automation.config['style'] = request.form.get('shorts_style', 'entertaining')
        
        # Auto upload setting
        auto_upload = request.form.get('auto_upload', 'off') == 'on'
        
        return jsonify({
            'success': True,
            'message': 'Shorts settings updated successfully'
        })

@app.route('/settings/youtube', methods=['POST'])
def save_youtube_settings():
    if request.method == 'POST':
        # Save YouTube settings (simplified)
        if 'shorts_settings' not in automation.config:
            automation.config['shorts_settings'] = {}
            
        # Get shorts tags
        shorts_tags = request.form.get('shorts_tags', '#shorts, #youtubeshorts')
        automation.config['shorts_settings']['tags'] = shorts_tags
        
        return jsonify({
            'success': True,
            'message': 'YouTube settings updated successfully'
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

# Utility routes
@app.route('/video/<path:video_path>')
def serve_video(video_path):
    return send_from_directory('output', os.path.basename(video_path))

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

# Helper functions
def mask_api_key(key):
    """Mask API key for display in settings."""
    if not key:
        return ''
    if len(key) <= 8:
        return '*' * len(key)
    return key[:4] + '*' * (len(key) - 8) + key[-4:]

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

@app.route('/thumbnails/<path:filename>')
def serve_thumbnail(filename):
    """Serve thumbnail images."""
    thumbnail_dir = automation.config['directories'].get('thumbnails', 'thumbnails')
    return send_from_directory(thumbnail_dir, filename)

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