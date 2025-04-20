"""
Social sharing module for Dexent.ai.
Implements one-click social media sharing of enhanced voice clips.
"""

import os
import json
import uuid
import base64
import logging
import requests
from urllib.parse import quote
from datetime import datetime
from flask import url_for
from config import SETTINGS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
SHARE_DATA_FILE = "data/shared_clips.json"
SHARED_CLIPS_FOLDER = "static/shared_clips"

# Ensure directories exist
os.makedirs(os.path.dirname(SHARE_DATA_FILE), exist_ok=True)
os.makedirs(SHARED_CLIPS_FOLDER, exist_ok=True)

class SocialSharingManager:
    """Manages social media sharing of enhanced voice clips."""
    
    def __init__(self):
        """Initialize the social sharing manager."""
        self.shared_clips = {}
        self.load_shared_clips()
        
        # Social media platform configuration
        self.platforms = {
            "twitter": {
                "name": "Twitter",
                "icon": "fab fa-twitter",
                "share_url": "https://twitter.com/intent/tweet",
                "params": {
                    "text": "text",
                    "url": "url",
                    "hashtags": "hashtags"
                }
            },
            "facebook": {
                "name": "Facebook",
                "icon": "fab fa-facebook",
                "share_url": "https://www.facebook.com/sharer/sharer.php",
                "params": {
                    "u": "url",
                    "quote": "text"
                }
            },
            "linkedin": {
                "name": "LinkedIn",
                "icon": "fab fa-linkedin",
                "share_url": "https://www.linkedin.com/shareArticle",
                "params": {
                    "mini": "true",
                    "url": "url",
                    "title": "title",
                    "summary": "summary"
                }
            },
            "whatsapp": {
                "name": "WhatsApp",
                "icon": "fab fa-whatsapp",
                "share_url": "https://api.whatsapp.com/send",
                "params": {
                    "text": "text"
                }
            },
            "telegram": {
                "name": "Telegram",
                "icon": "fab fa-telegram",
                "share_url": "https://t.me/share/url",
                "params": {
                    "url": "url",
                    "text": "text"
                }
            },
            "reddit": {
                "name": "Reddit",
                "icon": "fab fa-reddit",
                "share_url": "https://www.reddit.com/submit",
                "params": {
                    "url": "url",
                    "title": "title"
                }
            },
            "email": {
                "name": "Email",
                "icon": "fas fa-envelope",
                "share_url": "mailto:",
                "params": {
                    "subject": "subject",
                    "body": "body"
                }
            }
        }
    
    def load_shared_clips(self):
        """Load shared clips data from file."""
        try:
            if os.path.exists(SHARE_DATA_FILE):
                with open(SHARE_DATA_FILE, 'r') as f:
                    self.shared_clips = json.load(f)
        except Exception as e:
            logger.error(f"Error loading shared clips: {str(e)}")
            self.shared_clips = {}
    
    def save_shared_clips(self):
        """Save shared clips data to file."""
        try:
            with open(SHARE_DATA_FILE, 'w') as f:
                json.dump(self.shared_clips, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving shared clips: {str(e)}")
    
    def create_shareable_clip(self, user_id, audio_file, title, description, 
                             accent="", metadata=None, is_public=True):
        """
        Create a shareable audio clip.
        
        Args:
            user_id (int): ID of the user who created the clip
            audio_file (str): Path to the audio file
            title (str): Title of the clip
            description (str): Description of the clip
            accent (str, optional): Accent used for the clip
            metadata (dict, optional): Additional metadata
            is_public (bool): Whether the clip is publicly accessible
            
        Returns:
            dict: Shareable clip information with unique share ID
        """
        try:
            # Check if the audio file exists
            if not os.path.exists(audio_file):
                return {"error": "Audio file not found"}
            
            # Generate a unique share ID
            share_id = str(uuid.uuid4())
            
            # Create a copy of the audio file in the shared clips folder
            file_ext = os.path.splitext(audio_file)[1]
            shared_filename = f"{share_id}{file_ext}"
            shared_path = os.path.join(SHARED_CLIPS_FOLDER, shared_filename)
            
            # Copy the file
            with open(audio_file, 'rb') as src, open(shared_path, 'wb') as dst:
                dst.write(src.read())
            
            # Create the shareable clip record
            timestamp = datetime.now().isoformat()
            clip = {
                "share_id": share_id,
                "user_id": user_id,
                "title": title,
                "description": description,
                "accent": accent,
                "file_path": shared_path,
                "file_url": f"/static/shared_clips/{shared_filename}",
                "created_at": timestamp,
                "is_public": is_public,
                "share_count": 0,
                "play_count": 0,
                "likes": 0,
                "metadata": metadata or {}
            }
            
            # Store the clip
            self.shared_clips[share_id] = clip
            
            # Save to file
            self.save_shared_clips()
            
            return clip
        except Exception as e:
            logger.error(f"Error creating shareable clip: {str(e)}")
            return {"error": str(e)}
    
    def get_shareable_clip(self, share_id):
        """
        Get a shareable clip by ID.
        
        Args:
            share_id (str): Unique share ID
            
        Returns:
            dict: Shareable clip information
        """
        return self.shared_clips.get(share_id, {"error": "Clip not found"})
    
    def get_user_clips(self, user_id, limit=10):
        """
        Get clips shared by a specific user.
        
        Args:
            user_id (int): User ID
            limit (int): Maximum number of clips to return
            
        Returns:
            list: List of shareable clip information
        """
        user_clips = [
            clip for clip in self.shared_clips.values()
            if clip.get("user_id") == user_id
        ]
        
        # Sort by creation time (newest first)
        user_clips.sort(key=lambda clip: clip.get("created_at", ""), reverse=True)
        
        return user_clips[:limit]
    
    def get_public_clips(self, limit=10):
        """
        Get publicly shared clips.
        
        Args:
            limit (int): Maximum number of clips to return
            
        Returns:
            list: List of public shareable clip information
        """
        public_clips = [
            clip for clip in self.shared_clips.values()
            if clip.get("is_public", False)
        ]
        
        # Sort by creation time (newest first)
        public_clips.sort(key=lambda clip: clip.get("created_at", ""), reverse=True)
        
        return public_clips[:limit]
    
    def delete_shareable_clip(self, share_id, user_id=None):
        """
        Delete a shareable clip.
        
        Args:
            share_id (str): Unique share ID
            user_id (int, optional): User ID (for authorization check)
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            if share_id not in self.shared_clips:
                return False
            
            # Check if the user is authorized to delete
            if user_id is not None and self.shared_clips[share_id].get("user_id") != user_id:
                return False
            
            # Get the file path
            file_path = self.shared_clips[share_id].get("file_path")
            
            # Delete the file if it exists
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            
            # Remove the clip record
            del self.shared_clips[share_id]
            
            # Save changes
            self.save_shared_clips()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting shareable clip: {str(e)}")
            return False
    
    def update_clip_stats(self, share_id, action="play"):
        """
        Update statistics for a shareable clip.
        
        Args:
            share_id (str): Unique share ID
            action (str): Action to record ("play", "share", "like")
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        try:
            if share_id not in self.shared_clips:
                return False
            
            if action == "play":
                self.shared_clips[share_id]["play_count"] += 1
            elif action == "share":
                self.shared_clips[share_id]["share_count"] += 1
            elif action == "like":
                self.shared_clips[share_id]["likes"] += 1
            
            # Save changes
            self.save_shared_clips()
            
            return True
        except Exception as e:
            logger.error(f"Error updating clip stats: {str(e)}")
            return False
    
    def get_share_url(self, share_id, base_url=None):
        """
        Get the URL for sharing a clip.
        
        Args:
            share_id (str): Unique share ID
            base_url (str, optional): Base URL for the share link
            
        Returns:
            str: URL for sharing the clip
        """
        if not base_url:
            # Use a default base URL (this should be configured properly in production)
            base_url = "https://dexent.ai"
        
        return f"{base_url}/share/{share_id}"
    
    def get_social_share_links(self, share_id, base_url=None):
        """
        Get share links for various social media platforms.
        
        Args:
            share_id (str): Unique share ID
            base_url (str, optional): Base URL for the share link
            
        Returns:
            dict: Dictionary of social media platform share links
        """
        clip = self.get_shareable_clip(share_id)
        if "error" in clip:
            return {}
        
        # Get the share URL
        share_url = self.get_share_url(share_id, base_url)
        
        # Prepare share text
        title = clip.get("title", "Check out my enhanced voice clip")
        description = clip.get("description", "I created this with Dexent.ai")
        accent = clip.get("accent", "")
        
        share_text = f"{title}"
        if accent:
            share_text += f" ({accent} accent)"
        
        full_text = f"{share_text}\n\n{description}\n\nCreated with Dexent.ai"
        
        # Create share links for each platform
        share_links = {}
        
        for platform_id, platform in self.platforms.items():
            params = {}
            
            for param_name, param_key in platform["params"].items():
                if param_key == "url":
                    params[param_name] = share_url
                elif param_key == "text":
                    params[param_name] = full_text
                elif param_key == "title":
                    params[param_name] = share_text
                elif param_key == "summary":
                    params[param_name] = description
                elif param_key == "hashtags":
                    params[param_name] = "DexentAI,VoiceEnhancement"
                elif param_key == "subject":
                    params[param_name] = share_text
                elif param_key == "body":
                    params[param_name] = f"{full_text}\n\n{share_url}"
            
            # Build the share link
            share_link = platform["share_url"]
            
            if platform_id == "email":
                # Email links have a different format
                recipient = ""
                subject = quote(params.get("subject", ""))
                body = quote(params.get("body", ""))
                share_link = f"mailto:{recipient}?subject={subject}&body={body}"
            else:
                # Build query string for other platforms
                query_params = "&".join([f"{k}={quote(str(v))}" for k, v in params.items()])
                if query_params:
                    share_link += f"?{query_params}"
            
            # Add to share links
            share_links[platform_id] = {
                "name": platform["name"],
                "icon": platform["icon"],
                "url": share_link
            }
        
        return share_links
    
    def generate_embed_code(self, share_id, width=400, height=150):
        """
        Generate HTML embed code for a shareable clip.
        
        Args:
            share_id (str): Unique share ID
            width (int): Width of the embedded player
            height (int): Height of the embedded player
            
        Returns:
            str: HTML embed code
        """
        clip = self.get_shareable_clip(share_id)
        if "error" in clip:
            return ""
        
        file_url = clip.get("file_url", "")
        title = clip.get("title", "Dexent.ai Audio Clip")
        
        # Create an iframe embed code
        embed_code = f'''<iframe 
            src="https://dexent.ai/embed/{share_id}" 
            width="{width}" 
            height="{height}" 
            frameborder="0" 
            allow="autoplay" 
            title="{title}">
        </iframe>'''
        
        return embed_code

# Create a singleton instance
social_sharing_manager = SocialSharingManager()

# Function to get the social sharing manager instance
def get_social_sharing_manager():
    """Get the social sharing manager instance."""
    return social_sharing_manager