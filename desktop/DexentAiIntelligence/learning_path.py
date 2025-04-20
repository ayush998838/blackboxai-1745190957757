"""
Learning path module for Dexent.ai.
Implements gamified learning path for accent improvement.
"""

import os
import json
import logging
import random
from datetime import datetime
from flask_login import current_user
from models import db, User, UserProfile
from config import SETTINGS, ACCENT_OPTIONS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
LEARNING_PATH_DATA_FILE = "data/learning_paths.json"
USER_PROGRESS_FOLDER = "data/user_progress"

# Ensure directories exist
os.makedirs(os.path.dirname(LEARNING_PATH_DATA_FILE), exist_ok=True)
os.makedirs(USER_PROGRESS_FOLDER, exist_ok=True)

class LearningPathManager:
    """Manages gamified learning paths for accent improvement."""
    
    def __init__(self):
        """Initialize the learning path manager."""
        self.learning_paths = {}
        self.load_learning_paths()
    
    def load_learning_paths(self):
        """Load learning path data from file."""
        try:
            if os.path.exists(LEARNING_PATH_DATA_FILE):
                with open(LEARNING_PATH_DATA_FILE, 'r') as f:
                    self.learning_paths = json.load(f)
            else:
                # Create default learning paths
                self.create_default_learning_paths()
                self.save_learning_paths()
        except Exception as e:
            logger.error(f"Error loading learning paths: {str(e)}")
            self.create_default_learning_paths()
    
    def save_learning_paths(self):
        """Save learning path data to file."""
        try:
            with open(LEARNING_PATH_DATA_FILE, 'w') as f:
                json.dump(self.learning_paths, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving learning paths: {str(e)}")
    
    def create_default_learning_paths(self):
        """Create default learning paths for each accent."""
        self.learning_paths = {}
        
        for accent in ACCENT_OPTIONS:
            path_data = {
                "accent": accent,
                "name": f"{accent.capitalize()} Accent Mastery",
                "description": f"Master the {accent.capitalize()} accent through progressive exercises.",
                "levels": [
                    {
                        "level": 1,
                        "name": "Beginner",
                        "description": "Learn the basics of the accent",
                        "xp_required": 0,
                        "exercises": [
                            {
                                "id": f"{accent}_1_1",
                                "name": "Vowel Sounds",
                                "description": "Practice the core vowel sounds",
                                "difficulty": "easy",
                                "xp_reward": 10,
                                "completion_criteria": "3 successful attempts",
                                "sample_sentences": self._get_sample_sentences(accent, "vowels", 5)
                            },
                            {
                                "id": f"{accent}_1_2",
                                "name": "Basic Phrases",
                                "description": "Practice common phrases",
                                "difficulty": "easy",
                                "xp_reward": 15,
                                "completion_criteria": "5 successful attempts",
                                "sample_sentences": self._get_sample_sentences(accent, "basic_phrases", 5)
                            }
                        ]
                    },
                    {
                        "level": 2,
                        "name": "Intermediate",
                        "description": "Refine your accent with more complex sounds",
                        "xp_required": 100,
                        "exercises": [
                            {
                                "id": f"{accent}_2_1",
                                "name": "Consonant Clusters",
                                "description": "Master difficult consonant combinations",
                                "difficulty": "medium",
                                "xp_reward": 20,
                                "completion_criteria": "7 successful attempts",
                                "sample_sentences": self._get_sample_sentences(accent, "consonant_clusters", 5)
                            },
                            {
                                "id": f"{accent}_2_2",
                                "name": "Intonation Patterns",
                                "description": "Learn the rhythm and melody of the accent",
                                "difficulty": "medium",
                                "xp_reward": 25,
                                "completion_criteria": "5 successful attempts with 70% accuracy",
                                "sample_sentences": self._get_sample_sentences(accent, "intonation", 5)
                            }
                        ]
                    },
                    {
                        "level": 3,
                        "name": "Advanced",
                        "description": "Perfect your accent with advanced techniques",
                        "xp_required": 300,
                        "exercises": [
                            {
                                "id": f"{accent}_3_1",
                                "name": "Regional Variations",
                                "description": "Explore different regional variations of the accent",
                                "difficulty": "hard",
                                "xp_reward": 30,
                                "completion_criteria": "10 successful attempts with 80% accuracy",
                                "sample_sentences": self._get_sample_sentences(accent, "regional", 5)
                            },
                            {
                                "id": f"{accent}_3_2",
                                "name": "Fluent Conversation",
                                "description": "Maintain the accent in natural conversation",
                                "difficulty": "hard",
                                "xp_reward": 40,
                                "completion_criteria": "3 minute continuous speech with consistent accent",
                                "sample_sentences": self._get_sample_sentences(accent, "conversation", 5)
                            }
                        ]
                    }
                ],
                "badges": [
                    {
                        "id": f"{accent}_novice",
                        "name": f"{accent.capitalize()} Novice",
                        "description": "Complete all beginner exercises",
                        "icon": "badge_novice.svg",
                        "criteria": "Complete Level 1"
                    },
                    {
                        "id": f"{accent}_adept",
                        "name": f"{accent.capitalize()} Adept",
                        "description": "Complete all intermediate exercises",
                        "icon": "badge_adept.svg",
                        "criteria": "Complete Level 2"
                    },
                    {
                        "id": f"{accent}_master",
                        "name": f"{accent.capitalize()} Master",
                        "description": "Complete all advanced exercises",
                        "icon": "badge_master.svg",
                        "criteria": "Complete Level 3"
                    },
                    {
                        "id": f"{accent}_perfect",
                        "name": f"Perfect {accent.capitalize()}",
                        "description": "Achieve 95% accuracy across all exercises",
                        "icon": "badge_perfect.svg",
                        "criteria": "95% accuracy overall"
                    }
                ]
            }
            
            self.learning_paths[accent] = path_data
    
    def _get_sample_sentences(self, accent, category, count):
        """Get sample sentences for a specific accent and category."""
        # These would ideally come from a larger database of accent-specific examples
        sample_sentences = {
            "american": {
                "vowels": [
                    "The cat sat on the mat.",
                    "I can't park my car in the yard.",
                    "The dog caught the ball.",
                    "Would you like some coffee?",
                    "Turn right at the next light.",
                    "I need to buy some groceries at the store.",
                    "Let's go to the mall today."
                ],
                "basic_phrases": [
                    "How are you doing today?",
                    "Nice to meet you.",
                    "What time is it?",
                    "Could you help me with this?",
                    "I'm looking for the nearest gas station.",
                    "Have a nice day!",
                    "Thanks for your help."
                ],
                "consonant_clusters": [
                    "Please place the plates on the table.",
                    "The streets are slippery when wet.",
                    "Three thrushes thrashed through the thicket.",
                    "Strength and strategy are key to success.",
                    "The scripts were sprawled across the screen.",
                    "The twelfth knight grabbed his sword swiftly.",
                    "Splash the water around the swimming pool."
                ],
                "intonation": [
                    "Are you coming to the party tonight?",
                    "I didn't say she stole the money.",
                    "When will you be arriving?",
                    "Would you like coffee, tea, or water?",
                    "I love this restaurant!",
                    "Can you believe what happened yesterday?",
                    "Tell me more about your new job."
                ],
                "regional": [
                    "Y'all come back now, ya hear?",
                    "I'm heading down to the shore this weekend.",
                    "That was wicked awesome!",
                    "We're fixin' to have dinner soon.",
                    "Put the groceries in a sack, please.",
                    "Park the car in Harvard Yard.",
                    "It's hotter than blue blazes out there."
                ],
                "conversation": [
                    "I've been thinking about changing careers lately. The tech industry seems promising, but I'm not sure if I have the right skills yet.",
                    "Have you tried that new restaurant downtown? Everyone's talking about their amazing seafood dishes and craft cocktails.",
                    "The weather forecast says we might get some thunderstorms this weekend, so we might need to reschedule our hiking trip.",
                    "I just finished reading this fascinating book about artificial intelligence and how it might reshape our society in the coming decades.",
                    "My family is planning a reunion next summer, and we're trying to find the perfect location that's convenient for everyone."
                ]
            },
            "british": {
                "vowels": [
                    "The bath is half full.",
                    "Pass me the glass, please.",
                    "The castle stands on the grassy hill.",
                    "I can't dance at the party.",
                    "Look at that lovely garden.",
                    "The car is parked far away.",
                    "Mind the gap when boarding the train."
                ],
                # Similar categories for British accent...
                "basic_phrases": [
                    "How do you do?",
                    "I'm terribly sorry about that.",
                    "Would you fancy a cup of tea?",
                    "That's absolutely brilliant!",
                    "I'll be with you in a moment.",
                    "Mind the gap, please.",
                    "Cheers, mate!"
                ],
                "consonant_clusters": [
                    "The Thames flows through London.",
                    "I thought the theatre was splendid.",
                    "Worcester sauce is quite distinctive.",
                    "Leicester Square is always crowded on weekends.",
                    "The knights of the realm gathered at the castle.",
                    "The proper pronunciation is crucial.",
                    "That's a rather splendid achievement."
                ],
                "intonation": [
                    "Shall we go to the cinema this evening?",
                    "Would you like milk in your tea?",
                    "I suppose you'll be wanting dinner soon?",
                    "Have you seen the Queen's speech?",
                    "Rather disappointing weather we're having, isn't it?",
                    "Could you possibly lend me your umbrella?",
                    "Haven't you finished your work yet?"
                ],
                "regional": [
                    "Ee by gum, that's a right bargain!",
                    "Aye, pet, I'll be there in a minute.",
                    "It's absolutely bucketing down outside.",
                    "That's proper mint, that is.",
                    "I'm chuffed to bits about the news.",
                    "That's well posh, innit?",
                    "He's gone down to the West Country for holiday."
                ],
                "conversation": [
                    "I've been thinking about taking a holiday in the Lake District this summer. The countryside there is absolutely gorgeous, especially when the weather is decent.",
                    "Have you tried that new gastropub that's opened on the high street? Their Sunday roast is supposed to be rather exceptional.",
                    "The weather forecast suggests we might have quite a bit of rain at the weekend, so perhaps we should postpone our cricket match.",
                    "I've just finished reading this fascinating book about the history of the British Empire and its complex legacy in modern geopolitics.",
                    "My family is planning a gathering for the Queen's Jubilee, and we're trying to find a suitable venue that's convenient for everyone."
                ]
            },
            # Additional accent categories would be defined similarly...
        }
        
        # Default sentences if accent or category not found
        default_sentences = [
            "The quick brown fox jumps over the lazy dog.",
            "She sells seashells by the seashore.",
            "How much wood would a woodchuck chuck if a woodchuck could chuck wood?",
            "Peter Piper picked a peck of pickled peppers.",
            "All good things must come to an end.",
            "Practice makes perfect.",
            "Actions speak louder than words."
        ]
        
        # Get sentences for the specified accent and category, or use defaults
        accent_data = sample_sentences.get(accent, {})
        category_sentences = accent_data.get(category, default_sentences)
        
        # Return the requested number of sentences (or all if count is greater than available)
        return random.sample(category_sentences, min(count, len(category_sentences)))
    
    def get_learning_path(self, accent):
        """Get the learning path for a specific accent."""
        return self.learning_paths.get(accent, None)
    
    def get_all_learning_paths(self):
        """Get all available learning paths."""
        return self.learning_paths
    
    def get_user_progress(self, user_id):
        """Get a user's progress in the learning paths."""
        try:
            progress_file = os.path.join(USER_PROGRESS_FOLDER, f"{user_id}.json")
            
            if os.path.exists(progress_file):
                with open(progress_file, 'r') as f:
                    return json.load(f)
            else:
                # Initialize empty progress for all learning paths
                progress = {}
                for accent in self.learning_paths:
                    progress[accent] = {
                        "current_level": 1,
                        "total_xp": 0,
                        "completed_exercises": [],
                        "earned_badges": [],
                        "last_activity": None
                    }
                
                # Save and return the new progress
                self.save_user_progress(user_id, progress)
                return progress
        except Exception as e:
            logger.error(f"Error getting user progress: {str(e)}")
            return {}
    
    def save_user_progress(self, user_id, progress):
        """Save a user's progress to file."""
        try:
            progress_file = os.path.join(USER_PROGRESS_FOLDER, f"{user_id}.json")
            
            with open(progress_file, 'w') as f:
                json.dump(progress, f, indent=4)
                
            return True
        except Exception as e:
            logger.error(f"Error saving user progress: {str(e)}")
            return False
    
    def complete_exercise(self, user_id, accent, exercise_id, accuracy=100):
        """Mark an exercise as completed and award XP."""
        try:
            # Get user progress
            progress = self.get_user_progress(user_id)
            if not progress or accent not in progress:
                return False
            
            # Get learning path
            learning_path = self.get_learning_path(accent)
            if not learning_path:
                return False
            
            # Find the exercise
            exercise = None
            for level in learning_path["levels"]:
                for ex in level["exercises"]:
                    if ex["id"] == exercise_id:
                        exercise = ex
                        break
                if exercise:
                    break
            
            if not exercise:
                return False
            
            # Calculate XP based on accuracy
            xp_earned = int(exercise["xp_reward"] * (accuracy / 100))
            
            # Update user progress
            if exercise_id not in progress[accent]["completed_exercises"]:
                progress[accent]["completed_exercises"].append(exercise_id)
            
            progress[accent]["total_xp"] += xp_earned
            progress[accent]["last_activity"] = datetime.now().isoformat()
            
            # Check if user leveled up
            current_level = progress[accent]["current_level"]
            for level in learning_path["levels"]:
                if level["level"] > current_level and progress[accent]["total_xp"] >= level["xp_required"]:
                    progress[accent]["current_level"] = level["level"]
            
            # Check for new badges
            self._check_for_badges(progress, accent, learning_path)
            
            # Save progress
            self.save_user_progress(user_id, progress)
            
            return {
                "success": True,
                "xp_earned": xp_earned,
                "total_xp": progress[accent]["total_xp"],
                "current_level": progress[accent]["current_level"]
            }
        except Exception as e:
            logger.error(f"Error completing exercise: {str(e)}")
            return False
    
    def _check_for_badges(self, progress, accent, learning_path):
        """Check if user has earned any new badges."""
        if not progress or accent not in progress:
            return
        
        for badge in learning_path["badges"]:
            # Skip if already earned
            if badge["id"] in progress[accent]["earned_badges"]:
                continue
            
            # Check criteria
            if badge["criteria"] == "Complete Level 1":
                if self._is_level_complete(progress, accent, learning_path, 1):
                    progress[accent]["earned_badges"].append(badge["id"])
            
            elif badge["criteria"] == "Complete Level 2":
                if self._is_level_complete(progress, accent, learning_path, 2):
                    progress[accent]["earned_badges"].append(badge["id"])
            
            elif badge["criteria"] == "Complete Level 3":
                if self._is_level_complete(progress, accent, learning_path, 3):
                    progress[accent]["earned_badges"].append(badge["id"])
            
            elif badge["criteria"] == "95% accuracy overall":
                # This would require tracking accuracy per exercise, simplified here
                if progress[accent]["current_level"] >= 3 and len(progress[accent]["completed_exercises"]) >= 6:
                    progress[accent]["earned_badges"].append(badge["id"])
    
    def _is_level_complete(self, progress, accent, learning_path, level_number):
        """Check if all exercises in a level are completed."""
        if not progress or accent not in progress:
            return False
        
        # Find the level
        level = None
        for lvl in learning_path["levels"]:
            if lvl["level"] == level_number:
                level = lvl
                break
        
        if not level:
            return False
        
        # Check if all exercises are completed
        for exercise in level["exercises"]:
            if exercise["id"] not in progress[accent]["completed_exercises"]:
                return False
        
        return True
    
    def get_recommended_exercises(self, user_id, accent):
        """Get recommended exercises for a user based on their progress."""
        try:
            # Get user progress
            progress = self.get_user_progress(user_id)
            if not progress or accent not in progress:
                return []
            
            # Get learning path
            learning_path = self.get_learning_path(accent)
            if not learning_path:
                return []
            
            recommended = []
            current_level = progress[accent]["current_level"]
            
            # Find exercises in the current level that aren't completed
            for level in learning_path["levels"]:
                if level["level"] == current_level:
                    for exercise in level["exercises"]:
                        if exercise["id"] not in progress[accent]["completed_exercises"]:
                            recommended.append(exercise)
            
            # If all exercises in current level are completed, suggest the next level
            if not recommended and current_level < len(learning_path["levels"]):
                next_level = current_level + 1
                for level in learning_path["levels"]:
                    if level["level"] == next_level:
                        # Check if user has enough XP for this level
                        if progress[accent]["total_xp"] >= level["xp_required"]:
                            for exercise in level["exercises"]:
                                if exercise["id"] not in progress[accent]["completed_exercises"]:
                                    recommended.append(exercise)
            
            return recommended
        except Exception as e:
            logger.error(f"Error getting recommended exercises: {str(e)}")
            return []
    
    def get_user_statistics(self, user_id):
        """Get statistics about a user's learning path progress."""
        try:
            # Get user progress
            progress = self.get_user_progress(user_id)
            if not progress:
                return {}
            
            stats = {
                "total_xp": 0,
                "completed_exercises": 0,
                "earned_badges": 0,
                "accent_progress": {},
                "last_activity": None
            }
            
            for accent, accent_progress in progress.items():
                # Update totals
                stats["total_xp"] += accent_progress["total_xp"]
                stats["completed_exercises"] += len(accent_progress["completed_exercises"])
                stats["earned_badges"] += len(accent_progress["earned_badges"])
                
                # Calculate percent complete for this accent
                learning_path = self.get_learning_path(accent)
                if learning_path:
                    total_exercises = sum(len(level["exercises"]) for level in learning_path["levels"])
                    completed = len(accent_progress["completed_exercises"])
                    percent_complete = (completed / total_exercises) * 100 if total_exercises > 0 else 0
                    
                    stats["accent_progress"][accent] = {
                        "level": accent_progress["current_level"],
                        "xp": accent_progress["total_xp"],
                        "completed_exercises": completed,
                        "total_exercises": total_exercises,
                        "percent_complete": percent_complete,
                        "badges": len(accent_progress["earned_badges"]),
                        "last_activity": accent_progress["last_activity"]
                    }
                    
                    # Update last activity overall
                    if accent_progress["last_activity"] and (not stats["last_activity"] or accent_progress["last_activity"] > stats["last_activity"]):
                        stats["last_activity"] = accent_progress["last_activity"]
            
            return stats
        except Exception as e:
            logger.error(f"Error getting user statistics: {str(e)}")
            return {}

# Create a singleton instance
learning_path_manager = LearningPathManager()

# Function to get the learning path manager instance
def get_learning_path_manager():
    """Get the learning path manager instance."""
    return learning_path_manager