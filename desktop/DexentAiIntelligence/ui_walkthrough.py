"""
UI walkthrough module for Dexent.ai.
Implements interactive UI walkthrough for first-time users.
"""

import os
import json
import logging
from datetime import datetime
from flask_login import current_user
from config import SETTINGS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
WALKTHROUGH_DATA_FILE = "data/walkthrough_data.json"
USER_PROGRESS_FOLDER = "data/user_walkthrough"

# Ensure directories exist
os.makedirs(os.path.dirname(WALKTHROUGH_DATA_FILE), exist_ok=True)
os.makedirs(USER_PROGRESS_FOLDER, exist_ok=True)

class UIWalkthroughManager:
    """Manages interactive UI walkthroughs for first-time users."""
    
    def __init__(self):
        """Initialize the UI walkthrough manager."""
        self.walkthroughs = {}
        self.load_walkthroughs()
    
    def load_walkthroughs(self):
        """Load walkthrough data from file."""
        try:
            if os.path.exists(WALKTHROUGH_DATA_FILE):
                with open(WALKTHROUGH_DATA_FILE, 'r') as f:
                    self.walkthroughs = json.load(f)
            else:
                # Create default walkthroughs
                self.create_default_walkthroughs()
                self.save_walkthroughs()
        except Exception as e:
            logger.error(f"Error loading walkthroughs: {str(e)}")
            self.create_default_walkthroughs()
    
    def save_walkthroughs(self):
        """Save walkthrough data to file."""
        try:
            with open(WALKTHROUGH_DATA_FILE, 'w') as f:
                json.dump(self.walkthroughs, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving walkthroughs: {str(e)}")
    
    def create_default_walkthroughs(self):
        """Create default walkthroughs for new users."""
        self.walkthroughs = {
            "main": {
                "id": "main",
                "name": "Main Walkthrough",
                "description": "Learn how to use Dexent.ai's main features",
                "version": "1.0",
                "steps": [
                    {
                        "id": "welcome",
                        "title": "Welcome to Dexent.ai",
                        "content": "Welcome to Dexent.ai, your advanced voice enhancement platform. This quick tour will help you get started.",
                        "target": "body",
                        "position": "center",
                        "button_text": "Next",
                        "dismissible": False
                    },
                    {
                        "id": "dashboard",
                        "title": "Dashboard",
                        "content": "This is your Dashboard, where you can monitor your audio processing status and access all features.",
                        "target": ".navbar-brand",
                        "position": "bottom",
                        "button_text": "Next",
                        "dismissible": False
                    },
                    {
                        "id": "audio_processing",
                        "title": "Audio Processing",
                        "content": "Toggle this switch to start or stop audio processing. When active, your voice will be enhanced in real-time.",
                        "target": "#processingToggle",
                        "position": "right",
                        "button_text": "Next",
                        "dismissible": False
                    },
                    {
                        "id": "noise_suppression",
                        "title": "Noise Suppression",
                        "content": "Enable noise suppression to remove background noise from your audio.",
                        "target": "#noiseSuppressionToggle",
                        "position": "right",
                        "button_text": "Next",
                        "dismissible": False
                    },
                    {
                        "id": "accent_conversion",
                        "title": "Accent Conversion",
                        "content": "Convert your accent to a different one while preserving your voice identity.",
                        "target": "#accentConversionToggle",
                        "position": "right",
                        "button_text": "Next",
                        "dismissible": False
                    },
                    {
                        "id": "target_accent",
                        "title": "Target Accent",
                        "content": "Choose your desired target accent from the dropdown menu.",
                        "target": "#targetAccent",
                        "position": "bottom",
                        "button_text": "Next",
                        "dismissible": False
                    },
                    {
                        "id": "identity_preservation",
                        "title": "Identity Preservation",
                        "content": "Keep this enabled to maintain your unique voice characteristics during accent conversion.",
                        "target": "#identityPreservationToggle",
                        "position": "right",
                        "button_text": "Next",
                        "dismissible": False
                    },
                    {
                        "id": "settings",
                        "title": "Settings",
                        "content": "Access more advanced settings and configurations here.",
                        "target": "a[href*='settings']",
                        "position": "left",
                        "button_text": "Next",
                        "dismissible": False
                    },
                    {
                        "id": "help",
                        "title": "Help & Setup",
                        "content": "Find guides for setting up virtual audio devices on your platform.",
                        "target": "#setupAccordion",
                        "position": "top",
                        "button_text": "Next",
                        "dismissible": False
                    },
                    {
                        "id": "completion",
                        "title": "You're All Set!",
                        "content": "You've completed the tour. Explore Dexent.ai and enhance your voice communication!",
                        "target": "body",
                        "position": "center",
                        "button_text": "Finish",
                        "dismissible": True
                    }
                ]
            },
            "accent_learning": {
                "id": "accent_learning",
                "name": "Accent Learning Path",
                "description": "Learn how to use the accent improvement features",
                "version": "1.0",
                "steps": [
                    {
                        "id": "learning_welcome",
                        "title": "Welcome to Accent Learning",
                        "content": "This walkthrough will show you how to use our gamified learning features to improve your accent.",
                        "target": "body",
                        "position": "center",
                        "button_text": "Get Started",
                        "dismissible": False
                    },
                    {
                        "id": "learning_paths",
                        "title": "Learning Paths",
                        "content": "Browse available accent learning paths and choose one that interests you.",
                        "target": "#learningPathsSection",
                        "position": "top",
                        "button_text": "Next",
                        "dismissible": False
                    },
                    {
                        "id": "practice_exercises",
                        "title": "Practice Exercises",
                        "content": "Complete exercises to gain experience points (XP) and level up your accent skills.",
                        "target": "#exercisesSection",
                        "position": "top",
                        "button_text": "Next",
                        "dismissible": False
                    },
                    {
                        "id": "voice_samples",
                        "title": "Voice Samples",
                        "content": "Listen to authentic voice samples to understand the accent better.",
                        "target": "#sampleLibrarySection",
                        "position": "right",
                        "button_text": "Next",
                        "dismissible": False
                    },
                    {
                        "id": "progress_tracking",
                        "title": "Progress Tracking",
                        "content": "Track your progress and earn badges as you improve.",
                        "target": "#progressTrackingSection",
                        "position": "left",
                        "button_text": "Next",
                        "dismissible": False
                    },
                    {
                        "id": "learning_completion",
                        "title": "Ready to Learn!",
                        "content": "You're ready to start improving your accent. Good luck!",
                        "target": "body",
                        "position": "center",
                        "button_text": "Start Learning",
                        "dismissible": True
                    }
                ]
            },
            "social_sharing": {
                "id": "social_sharing",
                "name": "Social Sharing Tutorial",
                "description": "Learn how to share your enhanced voice clips",
                "version": "1.0",
                "steps": [
                    {
                        "id": "sharing_welcome",
                        "title": "Share Your Voice",
                        "content": "Learn how to share your enhanced voice clips on social media.",
                        "target": "body",
                        "position": "center",
                        "button_text": "Let's Go",
                        "dismissible": False
                    },
                    {
                        "id": "create_clip",
                        "title": "Create a Clip",
                        "content": "Record or upload audio to create a shareable clip.",
                        "target": "#createClipSection",
                        "position": "top",
                        "button_text": "Next",
                        "dismissible": False
                    },
                    {
                        "id": "enhance_audio",
                        "title": "Enhance Audio",
                        "content": "Apply noise suppression and accent conversion to your clip.",
                        "target": "#enhanceAudioSection",
                        "position": "right",
                        "button_text": "Next",
                        "dismissible": False
                    },
                    {
                        "id": "preview_clip",
                        "title": "Preview Your Clip",
                        "content": "Listen to your enhanced clip before sharing.",
                        "target": "#previewClipSection",
                        "position": "bottom",
                        "button_text": "Next",
                        "dismissible": False
                    },
                    {
                        "id": "share_options",
                        "title": "Share Options",
                        "content": "Choose where and how to share your enhanced clip.",
                        "target": "#shareOptionsSection",
                        "position": "left",
                        "button_text": "Next",
                        "dismissible": False
                    },
                    {
                        "id": "embed_options",
                        "title": "Embed Options",
                        "content": "You can also embed your clip on websites or blogs.",
                        "target": "#embedCodeSection",
                        "position": "top",
                        "button_text": "Next",
                        "dismissible": False
                    },
                    {
                        "id": "sharing_completion",
                        "title": "Ready to Share!",
                        "content": "You're now ready to share your enhanced voice with the world!",
                        "target": "body",
                        "position": "center",
                        "button_text": "Finish",
                        "dismissible": True
                    }
                ]
            }
        }
    
    def get_walkthrough(self, walkthrough_id):
        """
        Get a walkthrough by ID.
        
        Args:
            walkthrough_id (str): Walkthrough ID
            
        Returns:
            dict: Walkthrough data, or None if not found
        """
        return self.walkthroughs.get(walkthrough_id, None)
    
    def get_all_walkthroughs(self):
        """
        Get all available walkthroughs.
        
        Returns:
            dict: All walkthroughs
        """
        return self.walkthroughs
    
    def get_user_progress(self, user_id):
        """
        Get a user's progress through walkthroughs.
        
        Args:
            user_id (int): User ID
            
        Returns:
            dict: User's walkthrough progress
        """
        try:
            progress_file = os.path.join(USER_PROGRESS_FOLDER, f"{user_id}.json")
            
            if os.path.exists(progress_file):
                with open(progress_file, 'r') as f:
                    return json.load(f)
            else:
                # Initialize empty progress for all walkthroughs
                progress = {}
                for walkthrough_id in self.walkthroughs:
                    progress[walkthrough_id] = {
                        "started": False,
                        "completed": False,
                        "current_step": 0,
                        "completed_steps": [],
                        "last_activity": None
                    }
                
                # Save and return the new progress
                self.save_user_progress(user_id, progress)
                return progress
        except Exception as e:
            logger.error(f"Error getting user walkthrough progress: {str(e)}")
            return {}
    
    def save_user_progress(self, user_id, progress):
        """
        Save a user's walkthrough progress.
        
        Args:
            user_id (int): User ID
            progress (dict): User's progress data
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            progress_file = os.path.join(USER_PROGRESS_FOLDER, f"{user_id}.json")
            
            with open(progress_file, 'w') as f:
                json.dump(progress, f, indent=4)
                
            return True
        except Exception as e:
            logger.error(f"Error saving user walkthrough progress: {str(e)}")
            return False
    
    def start_walkthrough(self, user_id, walkthrough_id):
        """
        Start a walkthrough for a user.
        
        Args:
            user_id (int): User ID
            walkthrough_id (str): Walkthrough ID
            
        Returns:
            dict: Initial step data, or None if walkthrough not found
        """
        try:
            # Get walkthrough
            walkthrough = self.get_walkthrough(walkthrough_id)
            if not walkthrough:
                return None
            
            # Get user progress
            progress = self.get_user_progress(user_id)
            
            # Update progress
            if walkthrough_id not in progress:
                progress[walkthrough_id] = {
                    "started": False,
                    "completed": False,
                    "current_step": 0,
                    "completed_steps": [],
                    "last_activity": None
                }
            
            progress[walkthrough_id]["started"] = True
            progress[walkthrough_id]["current_step"] = 0
            progress[walkthrough_id]["last_activity"] = datetime.now().isoformat()
            
            # Save progress
            self.save_user_progress(user_id, progress)
            
            # Return first step
            if walkthrough["steps"]:
                return walkthrough["steps"][0]
            else:
                return None
        except Exception as e:
            logger.error(f"Error starting walkthrough: {str(e)}")
            return None
    
    def next_step(self, user_id, walkthrough_id, current_step_id):
        """
        Move to the next step in a walkthrough.
        
        Args:
            user_id (int): User ID
            walkthrough_id (str): Walkthrough ID
            current_step_id (str): Current step ID
            
        Returns:
            dict: Next step data, or None if no more steps
        """
        try:
            # Get walkthrough
            walkthrough = self.get_walkthrough(walkthrough_id)
            if not walkthrough:
                return None
            
            # Get user progress
            progress = self.get_user_progress(user_id)
            if walkthrough_id not in progress:
                return self.start_walkthrough(user_id, walkthrough_id)
            
            # Find current step index
            current_index = -1
            for i, step in enumerate(walkthrough["steps"]):
                if step["id"] == current_step_id:
                    current_index = i
                    break
            
            if current_index == -1:
                # Step not found, restart walkthrough
                return self.start_walkthrough(user_id, walkthrough_id)
            
            # Mark current step as completed
            if current_step_id not in progress[walkthrough_id]["completed_steps"]:
                progress[walkthrough_id]["completed_steps"].append(current_step_id)
            
            # Move to next step
            next_index = current_index + 1
            if next_index < len(walkthrough["steps"]):
                progress[walkthrough_id]["current_step"] = next_index
                progress[walkthrough_id]["last_activity"] = datetime.now().isoformat()
                
                # Save progress
                self.save_user_progress(user_id, progress)
                
                return walkthrough["steps"][next_index]
            else:
                # Walkthrough completed
                progress[walkthrough_id]["completed"] = True
                progress[walkthrough_id]["last_activity"] = datetime.now().isoformat()
                
                # Save progress
                self.save_user_progress(user_id, progress)
                
                return {
                    "id": "completion_confirmation",
                    "title": "Walkthrough Completed",
                    "content": f"You've completed the {walkthrough['name']} walkthrough!",
                    "target": "body",
                    "position": "center",
                    "button_text": "Done",
                    "dismissible": True,
                    "is_completion": True
                }
        except Exception as e:
            logger.error(f"Error getting next walkthrough step: {str(e)}")
            return None
    
    def skip_walkthrough(self, user_id, walkthrough_id):
        """
        Skip a walkthrough for a user.
        
        Args:
            user_id (int): User ID
            walkthrough_id (str): Walkthrough ID
            
        Returns:
            bool: True if skipped successfully, False otherwise
        """
        try:
            # Get user progress
            progress = self.get_user_progress(user_id)
            
            # Update progress
            if walkthrough_id not in progress:
                progress[walkthrough_id] = {
                    "started": True,
                    "completed": True,
                    "current_step": 0,
                    "completed_steps": [],
                    "last_activity": datetime.now().isoformat()
                }
            else:
                progress[walkthrough_id]["started"] = True
                progress[walkthrough_id]["completed"] = True
                progress[walkthrough_id]["last_activity"] = datetime.now().isoformat()
            
            # Save progress
            self.save_user_progress(user_id, progress)
            
            return True
        except Exception as e:
            logger.error(f"Error skipping walkthrough: {str(e)}")
            return False
    
    def reset_walkthrough(self, user_id, walkthrough_id):
        """
        Reset a walkthrough for a user.
        
        Args:
            user_id (int): User ID
            walkthrough_id (str): Walkthrough ID
            
        Returns:
            bool: True if reset successfully, False otherwise
        """
        try:
            # Get user progress
            progress = self.get_user_progress(user_id)
            
            # Update progress
            if walkthrough_id in progress:
                progress[walkthrough_id] = {
                    "started": False,
                    "completed": False,
                    "current_step": 0,
                    "completed_steps": [],
                    "last_activity": datetime.now().isoformat()
                }
            
            # Save progress
            self.save_user_progress(user_id, progress)
            
            return True
        except Exception as e:
            logger.error(f"Error resetting walkthrough: {str(e)}")
            return False
    
    def should_show_walkthrough(self, user_id, walkthrough_id, show_completed=False):
        """
        Check if a walkthrough should be shown to a user.
        
        Args:
            user_id (int): User ID
            walkthrough_id (str): Walkthrough ID
            show_completed (bool): Whether to show completed walkthroughs
            
        Returns:
            bool: True if the walkthrough should be shown, False otherwise
        """
        try:
            # Get user progress
            progress = self.get_user_progress(user_id)
            
            # Check if walkthrough exists
            if walkthrough_id not in progress:
                return True
            
            # Check if walkthrough is completed
            if progress[walkthrough_id]["completed"] and not show_completed:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error checking if walkthrough should be shown: {str(e)}")
            return False
    
    def get_recommended_walkthroughs(self, user_id):
        """
        Get recommended walkthroughs for a user.
        
        Args:
            user_id (int): User ID
            
        Returns:
            list: List of recommended walkthroughs
        """
        try:
            # Get user progress
            progress = self.get_user_progress(user_id)
            
            # Get all walkthroughs
            all_walkthroughs = self.get_all_walkthroughs()
            
            recommended = []
            
            # First, add any started but not completed walkthroughs
            for walkthrough_id, walkthrough in all_walkthroughs.items():
                if walkthrough_id in progress and progress[walkthrough_id]["started"] and not progress[walkthrough_id]["completed"]:
                    recommended.append({
                        "id": walkthrough_id,
                        "name": walkthrough["name"],
                        "description": walkthrough["description"],
                        "status": "in_progress",
                        "progress_percent": (len(progress[walkthrough_id]["completed_steps"]) / len(walkthrough["steps"])) * 100 if walkthrough["steps"] else 0
                    })
            
            # Then, add not started walkthroughs
            for walkthrough_id, walkthrough in all_walkthroughs.items():
                if walkthrough_id not in progress or not progress[walkthrough_id]["started"]:
                    recommended.append({
                        "id": walkthrough_id,
                        "name": walkthrough["name"],
                        "description": walkthrough["description"],
                        "status": "not_started",
                        "progress_percent": 0
                    })
            
            return recommended
        except Exception as e:
            logger.error(f"Error getting recommended walkthroughs: {str(e)}")
            return []

# Create a singleton instance
ui_walkthrough_manager = UIWalkthroughManager()

# Function to get the UI walkthrough manager instance
def get_ui_walkthrough_manager():
    """Get the UI walkthrough manager instance."""
    return ui_walkthrough_manager