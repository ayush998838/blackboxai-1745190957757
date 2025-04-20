"""
Emotion control module for Dexent.ai.
Implements emotion control for voice output.
"""

import os
import logging
import numpy as np
import torch
from tts import TextToSpeech
from config import SETTINGS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmotionControlManager:
    """Manages emotion control for voice output."""
    
    def __init__(self):
        """Initialize the emotion control manager."""
        self.tts_engine = TextToSpeech()
        self.sample_rate = SETTINGS["SAMPLE_RATE"]
        
        # Available emotions and their parameters
        self.emotions = {
            "neutral": {
                "description": "Neutral, balanced tone",
                "pitch_shift": 0.0,
                "speed_factor": 1.0,
                "energy_factor": 1.0,
                "voice_model": "neutral"
            },
            "happy": {
                "description": "Happy, upbeat tone",
                "pitch_shift": 0.5,  # Higher pitch
                "speed_factor": 1.15,  # Slightly faster
                "energy_factor": 1.2,  # More energy
                "voice_model": "happy"
            },
            "sad": {
                "description": "Sad, melancholic tone",
                "pitch_shift": -0.3,  # Lower pitch
                "speed_factor": 0.9,  # Slower
                "energy_factor": 0.8,  # Less energy
                "voice_model": "sad"
            },
            "angry": {
                "description": "Angry, intense tone",
                "pitch_shift": 0.2,  # Slightly higher pitch
                "speed_factor": 1.1,  # Slightly faster
                "energy_factor": 1.5,  # Much more energy
                "voice_model": "angry"
            },
            "calm": {
                "description": "Calm, soothing tone",
                "pitch_shift": -0.1,  # Slightly lower pitch
                "speed_factor": 0.95,  # Slightly slower
                "energy_factor": 0.9,  # Less energy
                "voice_model": "calm"
            },
            "excited": {
                "description": "Excited, enthusiastic tone",
                "pitch_shift": 0.4,  # Higher pitch
                "speed_factor": 1.2,  # Faster
                "energy_factor": 1.4,  # More energy
                "voice_model": "excited"
            },
            "serious": {
                "description": "Serious, authoritative tone",
                "pitch_shift": -0.2,  # Lower pitch
                "speed_factor": 0.97,  # Slightly slower
                "energy_factor": 1.05,  # Slightly more energy
                "voice_model": "serious"
            },
            "friendly": {
                "description": "Friendly, warm tone",
                "pitch_shift": 0.1,  # Slightly higher pitch
                "speed_factor": 1.05,  # Slightly faster
                "energy_factor": 1.1,  # More energy
                "voice_model": "friendly"
            }
        }
    
    def get_available_emotions(self):
        """
        Get available emotions.
        
        Returns:
            dict: Available emotions with descriptions
        """
        return {emotion: info["description"] for emotion, info in self.emotions.items()}
    
    def apply_emotion(self, audio_data, emotion="neutral", intensity=1.0):
        """
        Apply emotion to audio data.
        
        Args:
            audio_data (numpy.ndarray): Audio data to process
            emotion (str): Emotion to apply
            intensity (float): Intensity of the emotion (0.0 to 1.0)
            
        Returns:
            numpy.ndarray: Processed audio data
        """
        try:
            # Check if emotion is valid
            if emotion not in self.emotions:
                logger.warning(f"Invalid emotion: {emotion}. Using 'neutral' instead.")
                emotion = "neutral"
            
            # Get emotion parameters
            emotion_params = self.emotions[emotion]
            
            # Adjust intensity
            intensity = max(0.0, min(1.0, intensity))
            
            if intensity == 0.0:
                # No emotion, return original audio
                return audio_data
            
            # Apply emotion transformation
            processed_audio = self._apply_emotion_transformation(
                audio_data, 
                emotion_params["pitch_shift"] * intensity,
                emotion_params["speed_factor"] ** intensity,
                emotion_params["energy_factor"] ** intensity
            )
            
            return processed_audio
        except Exception as e:
            logger.error(f"Error applying emotion: {str(e)}")
            return audio_data
    
    def _apply_emotion_transformation(self, audio_data, pitch_shift, speed_factor, energy_factor):
        """
        Apply emotion transformation to audio data.
        
        Args:
            audio_data (numpy.ndarray): Audio data to process
            pitch_shift (float): Pitch shift factor
            speed_factor (float): Speed factor
            energy_factor (float): Energy factor
            
        Returns:
            numpy.ndarray: Processed audio data
        """
        try:
            # Convert to mono if needed
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            # Apply energy factor (amplitude scaling)
            audio_data = audio_data * energy_factor
            
            # For actual implementation, we'd use a library like librosa or scipy
            # to handle pitch shifting and time stretching
            
            # This is a simplified implementation that doesn't actually
            # perform the pitch shifting and time stretching, which require
            # more complex processing (e.g., phase vocoder, resampling)
            
            # For pitch shifting: librosa.effects.pitch_shift
            # For time stretching: librosa.effects.time_stretch
            
            # Placeholder for actual implementation
            processed_audio = audio_data
            
            return processed_audio
        except Exception as e:
            logger.error(f"Error applying emotion transformation: {str(e)}")
            return audio_data
    
    def synthesize_with_emotion(self, text, voice="default", emotion="neutral", intensity=1.0):
        """
        Synthesize text to speech with emotion.
        
        Args:
            text (str): Text to synthesize
            voice (str): Voice to use
            emotion (str): Emotion to apply
            intensity (float): Intensity of the emotion (0.0 to 1.0)
            
        Returns:
            numpy.ndarray: Synthesized audio data
        """
        try:
            # Check if emotion is valid
            if emotion not in self.emotions:
                logger.warning(f"Invalid emotion: {emotion}. Using 'neutral' instead.")
                emotion = "neutral"
            
            # Get emotion parameters
            emotion_params = self.emotions[emotion]
            
            # Choose the appropriate voice model if available
            voice_model = emotion_params.get("voice_model", voice)
            
            # Synthesize speech
            audio_data = self.tts_engine.synthesize(text, voice=voice_model)
            
            # Apply emotion transformation
            processed_audio = self.apply_emotion(audio_data, emotion, intensity)
            
            return processed_audio
        except Exception as e:
            logger.error(f"Error synthesizing with emotion: {str(e)}")
            return None
    
    def detect_emotion(self, audio_data):
        """
        Detect emotion in audio data.
        
        Args:
            audio_data (numpy.ndarray): Audio data to analyze
            
        Returns:
            dict: Detected emotions with confidence scores
        """
        try:
            # This would require a trained emotion recognition model
            # For now, return a placeholder result
            
            # In a real implementation, this would use a model like:
            # - SER (Speech Emotion Recognition) models
            # - Fine-tuned transformer models (e.g., Wav2Vec2, HuBERT)
            # - Acoustic feature extraction + classifier
            
            # Placeholder for actual implementation
            detected_emotions = {
                "neutral": 0.6,
                "happy": 0.2,
                "sad": 0.1,
                "angry": 0.05,
                "calm": 0.05
            }
            
            return detected_emotions
        except Exception as e:
            logger.error(f"Error detecting emotion: {str(e)}")
            return {"neutral": 1.0}
    
    def interpolate_emotions(self, audio_data, emotion1, emotion2, ratio=0.5):
        """
        Interpolate between two emotions.
        
        Args:
            audio_data (numpy.ndarray): Audio data to process
            emotion1 (str): First emotion
            emotion2 (str): Second emotion
            ratio (float): Interpolation ratio (0.0 for emotion1, 1.0 for emotion2)
            
        Returns:
            numpy.ndarray: Processed audio data
        """
        try:
            # Check if emotions are valid
            if emotion1 not in self.emotions:
                logger.warning(f"Invalid emotion1: {emotion1}. Using 'neutral' instead.")
                emotion1 = "neutral"
            
            if emotion2 not in self.emotions:
                logger.warning(f"Invalid emotion2: {emotion2}. Using 'neutral' instead.")
                emotion2 = "neutral"
            
            # Get emotion parameters
            params1 = self.emotions[emotion1]
            params2 = self.emotions[emotion2]
            
            # Adjust ratio
            ratio = max(0.0, min(1.0, ratio))
            
            # Interpolate parameters
            pitch_shift = params1["pitch_shift"] * (1 - ratio) + params2["pitch_shift"] * ratio
            speed_factor = params1["speed_factor"] * (1 - ratio) + params2["speed_factor"] * ratio
            energy_factor = params1["speed_factor"] * (1 - ratio) + params2["energy_factor"] * ratio
            
            # Apply transformation
            processed_audio = self._apply_emotion_transformation(
                audio_data, 
                pitch_shift,
                speed_factor,
                energy_factor
            )
            
            return processed_audio
        except Exception as e:
            logger.error(f"Error interpolating emotions: {str(e)}")
            return audio_data
    
    def adjust_emotion_parameters(self, emotion_name, params):
        """
        Adjust parameters for an emotion.
        
        Args:
            emotion_name (str): Emotion name
            params (dict): Parameters to adjust
            
        Returns:
            bool: True if adjusted successfully, False otherwise
        """
        try:
            if emotion_name not in self.emotions:
                return False
            
            # Update specified parameters
            for param, value in params.items():
                if param in self.emotions[emotion_name]:
                    self.emotions[emotion_name][param] = value
            
            return True
        except Exception as e:
            logger.error(f"Error adjusting emotion parameters: {str(e)}")
            return False
    
    def create_custom_emotion(self, emotion_name, description, pitch_shift=0.0, 
                            speed_factor=1.0, energy_factor=1.0, voice_model="neutral"):
        """
        Create a custom emotion.
        
        Args:
            emotion_name (str): Name of the emotion
            description (str): Description of the emotion
            pitch_shift (float): Pitch shift factor
            speed_factor (float): Speed factor
            energy_factor (float): Energy factor
            voice_model (str): Voice model to use
            
        Returns:
            bool: True if created successfully, False otherwise
        """
        try:
            # Check if emotion already exists
            if emotion_name in self.emotions:
                return False
            
            # Create new emotion
            self.emotions[emotion_name] = {
                "description": description,
                "pitch_shift": pitch_shift,
                "speed_factor": speed_factor,
                "energy_factor": energy_factor,
                "voice_model": voice_model
            }
            
            return True
        except Exception as e:
            logger.error(f"Error creating custom emotion: {str(e)}")
            return False
    
    def delete_custom_emotion(self, emotion_name):
        """
        Delete a custom emotion.
        
        Args:
            emotion_name (str): Name of the emotion
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            # Check if emotion exists and is not a built-in emotion
            if emotion_name not in self.emotions:
                return False
            
            # Check if it's a built-in emotion
            builtin_emotions = ["neutral", "happy", "sad", "angry", "calm", "excited", "serious", "friendly"]
            if emotion_name in builtin_emotions:
                return False
            
            # Delete emotion
            del self.emotions[emotion_name]
            
            return True
        except Exception as e:
            logger.error(f"Error deleting custom emotion: {str(e)}")
            return False
    
    def get_emotion_parameters(self, emotion_name):
        """
        Get parameters for an emotion.
        
        Args:
            emotion_name (str): Emotion name
            
        Returns:
            dict: Emotion parameters
        """
        if emotion_name in self.emotions:
            return self.emotions[emotion_name]
        else:
            return None

# Create a singleton instance
emotion_control_manager = EmotionControlManager()

# Function to get the emotion control manager instance
def get_emotion_control_manager():
    """Get the emotion control manager instance."""
    return emotion_control_manager