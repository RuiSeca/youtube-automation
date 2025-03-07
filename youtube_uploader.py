"""
Enhanced YouTube Upload Module with OAuth Authentication
------------------------------------------------------
This module handles OAuth authentication and video uploads to YouTube.
It's designed to be integrated with the YouTube automation system with
advanced error handling and retry logic.
"""

import os
import pickle
import time
import json
import random
from datetime import datetime
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

class YouTubeUploader:
    def __init__(self, client_secrets_file="client_secrets.json", token_pickle_file="token.pickle"):
        """
        Initialize the YouTube uploader with OAuth credentials.
        
        Args:
            client_secrets_file: Path to the OAuth client secrets JSON file
            token_pickle_file: Path to save/load the OAuth token
        """
        self.client_secrets_file = client_secrets_file
        self.token_pickle_file = token_pickle_file
        self.api_service_name = "youtube"
        self.api_version = "v3"
        self.scopes = ["https://www.googleapis.com/auth/youtube.upload", 
                       "https://www.googleapis.com/auth/youtube.readonly"]
        self.youtube = None
        
    def authenticate(self):
        """Handle OAuth authentication flow with improved error handling."""
        credentials = None
        
        # Try to load credentials from token pickle file
        if os.path.exists(self.token_pickle_file):
            try:
                print("Loading credentials from file...")
                with open(self.token_pickle_file, "rb") as token:
                    credentials = pickle.load(token)
            except Exception as e:
                print(f"Error loading credentials: {str(e)}")
                # Continue with credentials = None
        
        # If there are no valid credentials, authenticate
        if not credentials or not credentials.valid:
            try:
                if credentials and credentials.expired and credentials.refresh_token:
                    print("Refreshing access token...")
                    credentials.refresh(Request())
                else:
                    print("Fetching new tokens...")
                    if not os.path.exists(self.client_secrets_file):
                        raise FileNotFoundError(f"OAuth client secrets file '{self.client_secrets_file}' not found.")
                    
                    # Read the client secrets file to check its format
                    with open(self.client_secrets_file, 'r') as f:
                        client_secrets = json.load(f)
                    
                    # Check if it has a 'web' key (Google Cloud Console format)
                    if 'web' in client_secrets:
                        print("Using web application credentials format")
                        # Use the web flow for authentication
                        flow = InstalledAppFlow.from_client_config(
                            client_secrets, self.scopes
                        )
                    else:
                        print("Using standard client secrets format")
                        # Use the standard client secrets file format
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.client_secrets_file, self.scopes
                        )
                    
                    # This will open a browser window for authentication
                    credentials = flow.run_local_server(port=8080)
                
                # Save the credentials for the next run
                with open(self.token_pickle_file, "wb") as token:
                    pickle.dump(credentials, token)
            except Exception as e:
                print(f"Authentication error: {str(e)}")
                return False
        
        # Build the YouTube API client
        try:
            self.youtube = build(
                self.api_service_name, self.api_version, credentials=credentials
            )
            print("YouTube API client created successfully.")
            return True
        except Exception as e:
            print(f"Error building YouTube API client: {str(e)}")
            return False
    
    def upload_video(self, video_file, title, description, tags, category="22", privacy_status="private", notify_subscribers=False):
        """
        Upload a video to YouTube with enhanced error handling.
        
        Args:
            video_file: Path to the video file to upload
            title: Video title
            description: Video description
            tags: List of tags
            category: YouTube category ID (default is 22 for People & Blogs)
            privacy_status: private, public, or unlisted (default is private)
            notify_subscribers: Whether to notify subscribers (only works if privacy_status is "public")
            
        Returns:
            YouTube video ID if successful, None otherwise
        """
        if not os.path.exists(video_file):
            print(f"Error: Video file '{video_file}' not found.")
            return None
            
        if not self.youtube:
            success = self.authenticate()
            if not success:
                print("Failed to authenticate with YouTube.")
                return None
        
        try:
            # Make sure tags is a list
            if tags and not isinstance(tags, list):
                if isinstance(tags, str):
                    tags = [tag.strip() for tag in tags.split(',')]
                else:
                    tags = list(tags)
            
            # Ensure title isn't too long (YouTube limit is 100 characters)
            if len(title) > 100:
                title = title[:97] + "..."
            
            # Define video metadata
            body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags,
                    "categoryId": category
                },
                "status": {
                    "privacyStatus": privacy_status,
                    "selfDeclaredMadeForKids": False,
                    "publishAt": None  # Set a date to schedule, or None for immediate
                }
            }
            
            # If public and notify_subscribers is False, add notifySubscribers property
            if privacy_status == "public" and not notify_subscribers:
                body["status"]["notifySubscribers"] = False
            
            # Create upload request
            print(f"Preparing to upload video: {title}")
            print(f"File path: {video_file}")
            file_size = os.path.getsize(video_file)
            print(f"File size: {file_size / (1024 * 1024):.2f} MB")
            
            # Validate video file
            if file_size == 0:
                print("Error: Video file is empty")
                return None
                
            # Create a media upload object
            media = MediaFileUpload(
                video_file, 
                mimetype="video/*",
                chunksize=1024 * 1024 * 5,  # 5MB chunks
                resumable=True
            )
            
            # Create the API request
            insert_request = self.youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media
            )
            
            # Execute upload with progress tracking and exponential backoff
            print(f"Starting upload for '{title}'...")
            video_id = self._resumable_upload(insert_request)
            return video_id
            
        except HttpError as e:
            print(f"An HTTP error occurred: {e.resp.status} {e.content}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during upload: {str(e)}")
            return None
        
    def _resumable_upload(self, request):
        """
        Implement resumable upload with progress tracking and exponential backoff.
        
        Args:
            request: The YouTube API request object
            
        Returns:
            YouTube video ID if successful, None otherwise
        """
        response = None
        error = None
        retry = 0
        max_retries = 10
        
        # Exponential backoff parameters
        sleep_seconds = 1
        sleep_multiplier = 2
        max_sleep = 60  # Maximum sleep time between retries (1 minute)
        
        while response is None and retry <= max_retries:
            try:
                print("Uploading video...")
                status, response = request.next_chunk()
                if status:
                    percent = int(status.progress() * 100)
                    print(f"Upload progress: {percent}%")
                    
                    # Add occasional delay to avoid rate limits
                    if random.random() < 0.2:  # 20% chance
                        delay = random.uniform(0.5, 2.0)
                        time.sleep(delay)
                        
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504, 429]:  # Server errors or rate limits
                    retry += 1
                    if retry > max_retries:
                        print(f"Too many retries ({retry-1}). Upload failed.")
                        error = e
                        break
                        
                    # Calculate sleep time with exponential backoff and jitter
                    sleep_time = min(sleep_seconds * (sleep_multiplier ** (retry - 1)), max_sleep)
                    # Add jitter (±30%)
                    sleep_time = sleep_time * random.uniform(0.7, 1.3)
                    
                    print(f"Retrying upload in {sleep_time:.1f} seconds... (Attempt {retry}/{max_retries})")
                    time.sleep(sleep_time)
                else:
                    print(f"Upload failed with error: {e}")
                    error = e
                    break
            except Exception as e:
                print(f"Unexpected error during upload: {str(e)}")
                error = e
                retry += 1
                if retry > max_retries:
                    break
                time.sleep(sleep_seconds * (sleep_multiplier ** (retry - 1)))
        
        if error:
            print(f"Upload failed: {error}")
            return None
            
        if not response:
            print("Upload failed: No response received after retries")
            return None
            
        print("Upload successful!")
        
        # Check if response has the expected format
        if isinstance(response, dict) and "id" in response:
            video_id = response["id"]
            print(f"Video ID: {video_id}")
            return video_id
        else:
            print(f"Warning: Unexpected response format. Full response: {response}")
            # Try to extract ID if possible
            try:
                if hasattr(response, "get"):
                    return response.get("id")
                elif hasattr(response, "id"):
                    return response["id"]
                else:
                    return str(response)  # Last resort
            except:
                return None
    
    def update_thumbnail(self, video_id, thumbnail_file):
        """
        Set a custom thumbnail for a video with retry logic.
        
        Args:
            video_id: YouTube video ID
            thumbnail_file: Path to the thumbnail image file
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(thumbnail_file):
            print(f"Error: Thumbnail file '{thumbnail_file}' not found.")
            return False
            
        if not self.youtube:
            success = self.authenticate()
            if not success:
                print("Failed to authenticate with YouTube.")
                return False
        
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                print(f"Setting thumbnail for video {video_id} using file {thumbnail_file}")
                
                # Verify the file can be read
                with open(thumbnail_file, 'rb') as f:
                    first_bytes = f.read(10)
                    if not first_bytes:
                        print("Warning: Thumbnail file appears to be empty")
                
                # Create the media upload object
                media = MediaFileUpload(
                    thumbnail_file,
                    mimetype='image/png' if thumbnail_file.endswith('.png') else 'image/jpeg',
                    resumable=True
                )
                
                # Execute the request
                self.youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=media
                ).execute()
                
                print(f"Thumbnail set for video {video_id}")
                return True
                
            except HttpError as e:
                print(f"An error occurred while setting thumbnail (attempt {attempt+1}/{max_attempts}): {e}")
                if attempt < max_attempts - 1:
                    # Wait before retrying
                    time.sleep(5)
                    continue
                return False
            except Exception as e:
                print(f"Unexpected error setting thumbnail (attempt {attempt+1}/{max_attempts}): {str(e)}")
                if attempt < max_attempts - 1:
                    time.sleep(5)
                    continue
                return False
    
    def get_channel_info(self):
        """
        Get information about the authenticated user's YouTube channel.
        
        Returns:
            Dictionary with channel information
        """
        if not self.youtube:
            success = self.authenticate()
            if not success:
                print("Failed to authenticate with YouTube.")
                return None
        
        try:
            # Get channel information for the authenticated user
            response = self.youtube.channels().list(
                part="snippet,statistics,contentDetails",
                mine=True
            ).execute()
            
            if response and "items" in response and response["items"]:
                channel = response["items"][0]
                
                # Safely access nested properties
                snippet = channel.get("snippet", {})
                statistics = channel.get("statistics", {})
                content_details = channel.get("contentDetails", {})
                
                info = {
                    "id": channel.get("id", ""),
                    "title": snippet.get("title", ""),
                    "description": snippet.get("description", ""),
                    "customUrl": snippet.get("customUrl", ""),
                    "publishedAt": snippet.get("publishedAt", ""),
                    "country": snippet.get("country", ""),
                    "subscribers": statistics.get("subscriberCount", "0"),
                    "videos": statistics.get("videoCount", "0"),
                    "views": statistics.get("viewCount", "0"),
                    "playlists": content_details.get("relatedPlaylists", {})
                }
                return info
            else:
                print("No channel found for authenticated user or response format unexpected.")
                return None
                
        except HttpError as e:
            print(f"An error occurred while getting channel info: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error while getting channel info: {str(e)}")
            return None
    
    def get_video_statistics(self, video_id):
        """
        Get statistics for a specific video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Dictionary with video statistics
        """
        if not self.youtube:
            success = self.authenticate()
            if not success:
                print("Failed to authenticate with YouTube.")
                return None
        
        try:
            # Get video information
            response = self.youtube.videos().list(
                part="statistics,snippet",
                id=video_id
            ).execute()
            
            if response and "items" in response and response["items"]:
                video = response["items"][0]
                
                # Safely access nested properties
                snippet = video.get("snippet", {})
                statistics = video.get("statistics", {})
                
                info = {
                    "title": snippet.get("title", ""),
                    "publishedAt": snippet.get("publishedAt", ""),
                    "views": statistics.get("viewCount", "0"),
                    "likes": statistics.get("likeCount", "0"),
                    "comments": statistics.get("commentCount", "0"),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                return info
            else:
                print(f"No video found with ID {video_id}.")
                return None
                
        except HttpError as e:
            print(f"An error occurred while getting video statistics: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error while getting video statistics: {str(e)}")
            return None
    
    def update_video(self, video_id, title=None, description=None, tags=None, category=None, privacy=None):
        """
        Update video metadata.
        
        Args:
            video_id: YouTube video ID
            title: New title (optional)
            description: New description (optional)
            tags: New tags (optional)
            category: New category ID (optional)
            privacy: New privacy status (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.youtube:
            success = self.authenticate()
            if not success:
                print("Failed to authenticate with YouTube.")
                return False
        
        try:
            # First get the existing video details
            response = self.youtube.videos().list(
                part="snippet,status",
                id=video_id
            ).execute()
            
            if not response or "items" not in response or not response["items"]:
                print(f"No video found with ID {video_id}.")
                return False
            
            video = response["items"][0]
            snippet = video["snippet"]
            status = video["status"]
            
            # Update fields if provided
            if title:
                snippet["title"] = title
            if description:
                snippet["description"] = description
            if tags:
                snippet["tags"] = tags
            if category:
                snippet["categoryId"] = category
            if privacy:
                status["privacyStatus"] = privacy
            
            # Update the video
            update_response = self.youtube.videos().update(
                part="snippet,status",
                body={
                    "id": video_id,
                    "snippet": snippet,
                    "status": status
                }
            ).execute()
            
            print(f"Video {video_id} updated successfully.")
            return True
                
        except HttpError as e:
            print(f"An error occurred while updating video: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error while updating video: {str(e)}")
            return False
            
# Simple testing functionality
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='YouTube Uploader Tool')
    parser.add_argument('--upload', help='Upload a video file to YouTube', metavar='VIDEO_FILE')
    parser.add_argument('--title', help='Video title', default="Test Video")
    parser.add_argument('--description', help='Video description', default="This is a test video uploaded by YouTubeUploader")
    parser.add_argument('--tags', help='Comma-separated tags', default="test,upload,api")
    parser.add_argument('--thumbnail', help='Path to thumbnail image', metavar='THUMBNAIL_FILE')
    parser.add_argument('--privacy', help='Privacy status', choices=['private', 'public', 'unlisted'], default='private')
    parser.add_argument('--info', help='Get channel info', action='store_true')
    
    args = parser.parse_args()
    
    uploader = YouTubeUploader()
    
    if args.info:
        # Get channel info
        print("Getting channel info...")
        channel_info = uploader.get_channel_info()
        if channel_info:
            print("\nChannel Information:")
            print(f"Title: {channel_info['title']}")
            print(f"ID: {channel_info['id']}")
            print(f"URL: https://youtube.com/channel/{channel_info['id']}")
            print(f"Subscribers: {channel_info['subscribers']}")
            print(f"Total Videos: {channel_info['videos']}")
            print(f"Total Views: {channel_info['views']}")
    
    if args.upload:
        # Upload video
        print(f"Uploading {args.upload}...")
        video_id = uploader.upload_video(
            args.upload,
            args.title,
            args.description,
            args.tags.split(','),
            privacy_status=args.privacy
        )
        
        if video_id:
            print(f"Upload successful! Video ID: {video_id}")
            print(f"Video URL: https://youtu.be/{video_id}")
            
            if args.thumbnail:
                print(f"Setting thumbnail {args.thumbnail}...")
                if uploader.update_thumbnail(video_id, args.thumbnail):
                    print("Thumbnail set successfully!")
                else:
                    print("Failed to set thumbnail.")
        else:
            print("Upload failed.")
    
    if not args.upload and not args.info:
        print("No action specified. Use --upload or --info.")
        parser.print_help()