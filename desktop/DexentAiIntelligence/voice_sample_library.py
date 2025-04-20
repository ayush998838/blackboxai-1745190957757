"""
Voice sample library module for Dexent.ai.
Implements a library of diverse accent samples for reference and learning.
"""

import os
import json
import logging
from datetime import datetime
from flask_login import current_user
from config import SETTINGS, ACCENT_OPTIONS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
SAMPLE_LIBRARY_DATA_FILE = "data/voice_sample_library.json"
SAMPLE_AUDIO_FOLDER = "static/voice_samples"

# Ensure directories exist
os.makedirs(os.path.dirname(SAMPLE_LIBRARY_DATA_FILE), exist_ok=True)
os.makedirs(SAMPLE_AUDIO_FOLDER, exist_ok=True)

class VoiceSampleLibrary:
    """Manages a library of voice samples with various accents."""
    
    def __init__(self):
        """Initialize the voice sample library."""
        self.samples = {}
        self.categories = []
        self.load_library()
    
    def load_library(self):
        """Load voice sample library data from file."""
        try:
            if os.path.exists(SAMPLE_LIBRARY_DATA_FILE):
                with open(SAMPLE_LIBRARY_DATA_FILE, 'r') as f:
                    library_data = json.load(f)
                    self.samples = library_data.get("samples", {})
                    self.categories = library_data.get("categories", [])
            else:
                # Create default categories
                self.create_default_categories()
                # Initialize with empty samples
                self.samples = {}
                self.save_library()
        except Exception as e:
            logger.error(f"Error loading voice sample library: {str(e)}")
            self.create_default_categories()
            self.samples = {}
    
    def save_library(self):
        """Save voice sample library data to file."""
        try:
            library_data = {
                "samples": self.samples,
                "categories": self.categories
            }
            
            with open(SAMPLE_LIBRARY_DATA_FILE, 'w') as f:
                json.dump(library_data, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving voice sample library: {str(e)}")
    
    def create_default_categories(self):
        """Create default categories for voice samples."""
        self.categories = [
            {
                "id": "accents",
                "name": "Accents",
                "description": "Voice samples demonstrating different accents",
                "subcategories": [accent.capitalize() for accent in ACCENT_OPTIONS]
            },
            {
                "id": "genders",
                "name": "Genders",
                "description": "Voice samples categorized by gender",
                "subcategories": ["Male", "Female", "Other"]
            },
            {
                "id": "age_groups",
                "name": "Age Groups",
                "description": "Voice samples from different age groups",
                "subcategories": ["Child", "Young Adult", "Adult", "Senior"]
            },
            {
                "id": "contexts",
                "name": "Speaking Contexts",
                "description": "Voice samples in different speaking contexts",
                "subcategories": ["Conversation", "Presentation", "Narration", "Reading", "Interview"]
            },
            {
                "id": "emotions",
                "name": "Emotional Tones",
                "description": "Voice samples with different emotional tones",
                "subcategories": ["Neutral", "Happy", "Sad", "Excited", "Angry", "Calm"]
            }
        ]
    
    def add_sample(self, title, description, audio_file, accent, gender=None, 
                  age_group=None, context=None, emotion=None, metadata=None, 
                  tags=None, contributor_id=None, is_public=True):
        """
        Add a voice sample to the library.
        
        Args:
            title (str): Title of the sample
            description (str): Description of the sample
            audio_file (str): Path to the audio file
            accent (str): Accent of the speaker
            gender (str, optional): Gender of the speaker
            age_group (str, optional): Age group of the speaker
            context (str, optional): Speaking context
            emotion (str, optional): Emotional tone
            metadata (dict, optional): Additional metadata
            tags (list, optional): List of tags
            contributor_id (int, optional): ID of the user who contributed the sample
            is_public (bool): Whether the sample is publicly accessible
            
        Returns:
            str: Sample ID if successful, None otherwise
        """
        try:
            # Check if the audio file exists
            if not os.path.exists(audio_file):
                logger.error(f"Audio file not found: {audio_file}")
                return None
            
            # Generate a unique sample ID
            sample_id = f"sample_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            
            # Create a copy of the audio file in the samples folder
            file_ext = os.path.splitext(audio_file)[1]
            sample_filename = f"{sample_id}{file_ext}"
            sample_path = os.path.join(SAMPLE_AUDIO_FOLDER, sample_filename)
            
            # Copy the file
            with open(audio_file, 'rb') as src, open(sample_path, 'wb') as dst:
                dst.write(src.read())
            
            # Create the sample record
            timestamp = datetime.now().isoformat()
            sample = {
                "id": sample_id,
                "title": title,
                "description": description,
                "file_path": sample_path,
                "file_url": f"/static/voice_samples/{sample_filename}",
                "created_at": timestamp,
                "categories": {
                    "accent": accent.lower() if accent else None,
                    "gender": gender,
                    "age_group": age_group,
                    "context": context,
                    "emotion": emotion
                },
                "metadata": metadata or {},
                "tags": tags or [],
                "contributor_id": contributor_id,
                "is_public": is_public,
                "play_count": 0,
                "like_count": 0,
                "download_count": 0,
                "ratings": [],
                "average_rating": 0
            }
            
            # Add to samples
            self.samples[sample_id] = sample
            
            # Save library
            self.save_library()
            
            return sample_id
        except Exception as e:
            logger.error(f"Error adding voice sample: {str(e)}")
            return None
    
    def get_sample(self, sample_id):
        """
        Get a voice sample by ID.
        
        Args:
            sample_id (str): Sample ID
            
        Returns:
            dict: Sample information, or None if not found
        """
        return self.samples.get(sample_id, None)
    
    def get_samples_by_category(self, category, value, limit=20):
        """
        Get samples by category.
        
        Args:
            category (str): Category name (accent, gender, age_group, context, emotion)
            value (str): Category value
            limit (int): Maximum number of samples to return
            
        Returns:
            list: List of matching samples
        """
        matches = []
        count = 0
        
        for sample in self.samples.values():
            if sample.get("is_public", True) and sample.get("categories", {}).get(category) == value:
                matches.append(sample)
                count += 1
                if count >= limit:
                    break
        
        return matches
    
    def search_samples(self, query, categories=None, tags=None, limit=20):
        """
        Search for voice samples.
        
        Args:
            query (str): Search query
            categories (dict, optional): Category filters
            tags (list, optional): Tag filters
            limit (int): Maximum number of samples to return
            
        Returns:
            list: List of matching samples
        """
        query = query.lower() if query else ""
        matches = []
        count = 0
        
        for sample in self.samples.values():
            if not sample.get("is_public", True):
                continue
                
            # Check if query matches title or description
            title = sample.get("title", "").lower()
            description = sample.get("description", "").lower()
            
            if query and not (query in title or query in description):
                continue
            
            # Check categories if specified
            if categories:
                match_categories = True
                for cat, val in categories.items():
                    if val and sample.get("categories", {}).get(cat) != val:
                        match_categories = False
                        break
                
                if not match_categories:
                    continue
            
            # Check tags if specified
            if tags:
                sample_tags = sample.get("tags", [])
                if not all(tag in sample_tags for tag in tags):
                    continue
            
            matches.append(sample)
            count += 1
            if count >= limit:
                break
        
        return matches
    
    def get_random_samples(self, count=5, category=None, value=None):
        """
        Get random voice samples, optionally filtered by category.
        
        Args:
            count (int): Number of samples to return
            category (str, optional): Category name
            value (str, optional): Category value
            
        Returns:
            list: List of random samples
        """
        import random
        
        # Get all public samples
        all_samples = [
            sample for sample in self.samples.values()
            if sample.get("is_public", True)
        ]
        
        # Filter by category if specified
        if category and value:
            all_samples = [
                sample for sample in all_samples
                if sample.get("categories", {}).get(category) == value
            ]
        
        # Shuffle and limit
        random.shuffle(all_samples)
        return all_samples[:count]
    
    def update_sample_stats(self, sample_id, action="play"):
        """
        Update statistics for a voice sample.
        
        Args:
            sample_id (str): Sample ID
            action (str): Action to record ("play", "like", "download")
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        try:
            if sample_id not in self.samples:
                return False
            
            if action == "play":
                self.samples[sample_id]["play_count"] += 1
            elif action == "like":
                self.samples[sample_id]["like_count"] += 1
            elif action == "download":
                self.samples[sample_id]["download_count"] += 1
            
            # Save library
            self.save_library()
            
            return True
        except Exception as e:
            logger.error(f"Error updating sample stats: {str(e)}")
            return False
    
    def rate_sample(self, sample_id, user_id, rating):
        """
        Rate a voice sample.
        
        Args:
            sample_id (str): Sample ID
            user_id (int): User ID
            rating (int): Rating value (1-5)
            
        Returns:
            bool: True if rated successfully, False otherwise
        """
        try:
            if sample_id not in self.samples:
                return False
            
            # Ensure rating is valid
            rating = max(1, min(5, rating))
            
            # Check if user has already rated this sample
            ratings = self.samples[sample_id]["ratings"]
            user_rating = next((r for r in ratings if r["user_id"] == user_id), None)
            
            if user_rating:
                # Update existing rating
                user_rating["rating"] = rating
                user_rating["updated_at"] = datetime.now().isoformat()
            else:
                # Add new rating
                ratings.append({
                    "user_id": user_id,
                    "rating": rating,
                    "created_at": datetime.now().isoformat()
                })
            
            # Update average rating
            total_ratings = len(ratings)
            average_rating = sum(r["rating"] for r in ratings) / total_ratings if total_ratings > 0 else 0
            self.samples[sample_id]["average_rating"] = average_rating
            
            # Save library
            self.save_library()
            
            return True
        except Exception as e:
            logger.error(f"Error rating sample: {str(e)}")
            return False
    
    def get_popular_samples(self, category=None, limit=10):
        """
        Get popular voice samples based on play count.
        
        Args:
            category (str, optional): Category name
            limit (int): Maximum number of samples to return
            
        Returns:
            list: List of popular samples
        """
        # Get all public samples
        public_samples = [
            sample for sample in self.samples.values()
            if sample.get("is_public", True)
        ]
        
        # Filter by category if specified
        if category:
            category_name, category_value = category.split(":")
            public_samples = [
                sample for sample in public_samples
                if sample.get("categories", {}).get(category_name) == category_value
            ]
        
        # Sort by play count (highest first)
        public_samples.sort(key=lambda s: s.get("play_count", 0), reverse=True)
        
        return public_samples[:limit]
    
    def get_top_rated_samples(self, category=None, limit=10):
        """
        Get top-rated voice samples.
        
        Args:
            category (str, optional): Category name
            limit (int): Maximum number of samples to return
            
        Returns:
            list: List of top-rated samples
        """
        # Get all public samples
        public_samples = [
            sample for sample in self.samples.values()
            if sample.get("is_public", True)
        ]
        
        # Filter by category if specified
        if category:
            category_name, category_value = category.split(":")
            public_samples = [
                sample for sample in public_samples
                if sample.get("categories", {}).get(category_name) == category_value
            ]
        
        # Sort by average rating (highest first)
        public_samples.sort(key=lambda s: s.get("average_rating", 0), reverse=True)
        
        return public_samples[:limit]
    
    def get_user_contributed_samples(self, user_id, limit=20):
        """
        Get samples contributed by a specific user.
        
        Args:
            user_id (int): User ID
            limit (int): Maximum number of samples to return
            
        Returns:
            list: List of user-contributed samples
        """
        user_samples = [
            sample for sample in self.samples.values()
            if sample.get("contributor_id") == user_id
        ]
        
        # Sort by creation time (newest first)
        user_samples.sort(key=lambda s: s.get("created_at", ""), reverse=True)
        
        return user_samples[:limit]
    
    def delete_sample(self, sample_id, user_id=None):
        """
        Delete a voice sample.
        
        Args:
            sample_id (str): Sample ID
            user_id (int, optional): User ID (for authorization check)
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            if sample_id not in self.samples:
                return False
            
            # Check if the user is authorized to delete
            if user_id is not None and self.samples[sample_id].get("contributor_id") != user_id:
                return False
            
            # Get the file path
            file_path = self.samples[sample_id].get("file_path")
            
            # Delete the file if it exists
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            
            # Remove the sample record
            del self.samples[sample_id]
            
            # Save library
            self.save_library()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting voice sample: {str(e)}")
            return False
    
    def get_all_categories(self):
        """
        Get all categories with their subcategories.
        
        Returns:
            list: List of category information
        """
        return self.categories
    
    def get_category_values(self, category_id):
        """
        Get values for a specific category.
        
        Args:
            category_id (str): Category ID
            
        Returns:
            list: List of subcategory values
        """
        for category in self.categories:
            if category["id"] == category_id:
                return category.get("subcategories", [])
        
        return []
    
    def add_category(self, category_id, name, description, subcategories=None):
        """
        Add a new category.
        
        Args:
            category_id (str): Category ID
            name (str): Category name
            description (str): Category description
            subcategories (list, optional): List of subcategory values
            
        Returns:
            bool: True if added successfully, False otherwise
        """
        try:
            # Check if category already exists
            for category in self.categories:
                if category["id"] == category_id:
                    return False
            
            # Create new category
            new_category = {
                "id": category_id,
                "name": name,
                "description": description,
                "subcategories": subcategories or []
            }
            
            # Add to categories
            self.categories.append(new_category)
            
            # Save library
            self.save_library()
            
            return True
        except Exception as e:
            logger.error(f"Error adding category: {str(e)}")
            return False
    
    def update_category(self, category_id, name=None, description=None, subcategories=None):
        """
        Update a category.
        
        Args:
            category_id (str): Category ID
            name (str, optional): New category name
            description (str, optional): New category description
            subcategories (list, optional): New list of subcategory values
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        try:
            # Find the category
            for category in self.categories:
                if category["id"] == category_id:
                    # Update fields
                    if name is not None:
                        category["name"] = name
                    if description is not None:
                        category["description"] = description
                    if subcategories is not None:
                        category["subcategories"] = subcategories
                    
                    # Save library
                    self.save_library()
                    
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error updating category: {str(e)}")
            return False
    
    def delete_category(self, category_id):
        """
        Delete a category.
        
        Args:
            category_id (str): Category ID
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            # Find the category
            for i, category in enumerate(self.categories):
                if category["id"] == category_id:
                    # Remove the category
                    del self.categories[i]
                    
                    # Save library
                    self.save_library()
                    
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error deleting category: {str(e)}")
            return False

# Create a singleton instance
voice_sample_library = VoiceSampleLibrary()

# Function to get the voice sample library instance
def get_voice_sample_library():
    """Get the voice sample library instance."""
    return voice_sample_library