"""
Language translation module for Dexent.ai.
Implements real-time language translation with identity preservation.
"""

import os
import logging
import numpy as np
import torch
import whisper
import tempfile
from tts import TextToSpeech
from config import SETTINGS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LanguageTranslationManager:
    """Manages real-time language translation with identity preservation."""
    
    def __init__(self):
        """Initialize the language translation manager."""
        self.sample_rate = SETTINGS["SAMPLE_RATE"]
        
        # Load whisper model for transcription and translation
        self.model_size = "medium"  # Can be 'tiny', 'base', 'small', 'medium', 'large'
        try:
            self.whisper_model = whisper.load_model(self.model_size)
            logger.info(f"Loaded Whisper {self.model_size} model for translation")
        except Exception as e:
            logger.error(f"Error loading Whisper model: {str(e)}")
            self.whisper_model = None
        
        # Initialize TTS engine
        self.tts_engine = TextToSpeech()
        
        # Available languages
        self.languages = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "nl": "Dutch",
            "ru": "Russian",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "ar": "Arabic",
            "hi": "Hindi",
            "tr": "Turkish",
            "pl": "Polish",
            "uk": "Ukrainian",
            "el": "Greek",
            "he": "Hebrew",
            "th": "Thai",
            "sv": "Swedish",
            "cs": "Czech",
            "da": "Danish",
            "fi": "Finnish",
            "bg": "Bulgarian",
            "hr": "Croatian",
            "hu": "Hungarian"
        }
        
        # Voice models for each language
        self.language_voice_models = {
            "en": ["en_US_1", "en_US_2", "en_UK_1"],
            "es": ["es_ES_1", "es_MX_1"],
            "fr": ["fr_FR_1", "fr_CA_1"],
            "de": ["de_DE_1"],
            "it": ["it_IT_1"],
            "pt": ["pt_BR_1", "pt_PT_1"],
            "nl": ["nl_NL_1"],
            "ru": ["ru_RU_1"],
            "zh": ["zh_CN_1", "zh_TW_1"],
            "ja": ["ja_JP_1"],
            "ko": ["ko_KR_1"]
            # Other languages would use the default voice model
        }
    
    def get_available_languages(self):
        """
        Get available languages.
        
        Returns:
            dict: Available languages with language codes and names
        """
        return self.languages
    
    def detect_language(self, audio_data):
        """
        Detect language in audio data.
        
        Args:
            audio_data (numpy.ndarray): Audio data to analyze
            
        Returns:
            dict: Detected language information
        """
        try:
            if self.whisper_model is None:
                return {"error": "Whisper model not loaded"}
            
            # Convert to float32 if needed
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Normalize audio data
            if np.max(np.abs(audio_data)) > 0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            # Detect language using Whisper
            audio_features = self.whisper_model.embed_audio(audio_data)
            _, language_probs = self.whisper_model.detect_language(audio_features)
            
            # Get top predicted language
            language_code = max(language_probs, key=language_probs.get)
            confidence = language_probs[language_code]
            
            # Get language name
            language_name = self.languages.get(language_code, "Unknown")
            
            return {
                "language_code": language_code,
                "language_name": language_name,
                "confidence": float(confidence),
                "probabilities": {code: float(prob) for code, prob in language_probs.items() if prob > 0.01}
            }
        except Exception as e:
            logger.error(f"Error detecting language: {str(e)}")
            return {"error": str(e)}
    
    def transcribe(self, audio_data, source_language=None):
        """
        Transcribe audio data in the source language.
        
        Args:
            audio_data (numpy.ndarray): Audio data to transcribe
            source_language (str, optional): Source language code
            
        Returns:
            dict: Transcription result
        """
        try:
            if self.whisper_model is None:
                return {"error": "Whisper model not loaded"}
            
            # Convert to float32 if needed
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Normalize audio data
            if np.max(np.abs(audio_data)) > 0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            # Transcribe using Whisper
            options = {}
            if source_language:
                options["language"] = source_language
            
            result = self.whisper_model.transcribe(audio_data, **options)
            
            return {
                "text": result["text"],
                "language": result["language"],
                "segments": result["segments"]
            }
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return {"error": str(e)}
    
    def translate(self, audio_data, target_language="en", source_language=None):
        """
        Translate audio data to target language.
        
        Args:
            audio_data (numpy.ndarray): Audio data to translate
            target_language (str): Target language code
            source_language (str, optional): Source language code
            
        Returns:
            dict: Translation result
        """
        try:
            if self.whisper_model is None:
                return {"error": "Whisper model not loaded"}
            
            # Check if target language is supported
            if target_language not in self.languages:
                return {"error": f"Unsupported target language: {target_language}"}
            
            # Convert to float32 if needed
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Normalize audio data
            if np.max(np.abs(audio_data)) > 0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            # Transcribe and translate using Whisper
            options = {
                "task": "translate",
                "language": source_language,
            }
            
            # For most language models, Whisper translates to English by default
            # So we need to handle non-English target languages separately
            if target_language == "en":
                result = self.whisper_model.transcribe(audio_data, **options)
                translated_text = result["text"]
            else:
                # First transcribe and translate to English
                result = self.whisper_model.transcribe(audio_data, **options)
                english_text = result["text"]
                
                # Then use an external translation API or model to translate from English to target language
                # This is a simplified implementation; in practice, you'd use a translation API or model
                translated_text = self._translate_text(english_text, "en", target_language)
            
            return {
                "source_text": result.get("text", ""),
                "source_language": result.get("language", source_language),
                "translated_text": translated_text,
                "target_language": target_language
            }
        except Exception as e:
            logger.error(f"Error translating audio: {str(e)}")
            return {"error": str(e)}
    
    def _translate_text(self, text, source_language, target_language):
        """
        Translate text from source language to target language.
        
        Args:
            text (str): Text to translate
            source_language (str): Source language code
            target_language (str): Target language code
            
        Returns:
            str: Translated text
        """
        # This is a placeholder for actual translation implementation
        # In a real implementation, this would use a translation API or model
        # such as Google Translate API, Microsoft Translator API, or a custom model
        
        logger.info(f"Translating text from {source_language} to {target_language}")
        
        # Return original text for now
        return f"[Translated to {self.languages.get(target_language, target_language)}]: {text}"
    
    def synthesize_translation(self, translated_text, target_language, voice_model=None):
        """
        Synthesize translated text to speech.
        
        Args:
            translated_text (str): Translated text
            target_language (str): Target language code
            voice_model (str, optional): Voice model to use
            
        Returns:
            numpy.ndarray: Synthesized audio data
        """
        try:
            # If no voice model specified, use the first available for the language
            if not voice_model:
                available_voices = self.language_voice_models.get(target_language, ["default"])
                voice_model = available_voices[0]
            
            # Synthesize speech
            audio_data = self.tts_engine.synthesize(translated_text, voice=voice_model)
            
            return audio_data
        except Exception as e:
            logger.error(f"Error synthesizing translation: {str(e)}")
            return None
    
    def translate_and_preserve_identity(self, audio_data, target_language="en", source_language=None, 
                                      identity_preservation=True, voice_model=None):
        """
        Translate audio and preserve speaker identity.
        
        Args:
            audio_data (numpy.ndarray): Audio data to translate
            target_language (str): Target language code
            source_language (str, optional): Source language code
            identity_preservation (bool): Whether to preserve speaker identity
            voice_model (str, optional): Voice model to use
            
        Returns:
            dict: Translation result with audio
        """
        try:
            # Translate the audio
            translation_result = self.translate(audio_data, target_language, source_language)
            
            if "error" in translation_result:
                return translation_result
            
            # Synthesize the translation
            translated_audio = self.synthesize_translation(
                translation_result["translated_text"],
                target_language,
                voice_model
            )
            
            if translated_audio is None:
                return {"error": "Failed to synthesize translation"}
            
            # If identity preservation is enabled, apply voice conversion
            if identity_preservation:
                # Extract voice characteristics from original audio
                voice_characteristics = self._extract_voice_characteristics(audio_data)
                
                # Apply voice characteristics to translated audio
                if voice_characteristics:
                    translated_audio = self._apply_voice_characteristics(
                        translated_audio, 
                        voice_characteristics
                    )
            
            # Add audio to the result
            translation_result["audio"] = translated_audio
            
            return translation_result
        except Exception as e:
            logger.error(f"Error translating with identity preservation: {str(e)}")
            return {"error": str(e)}
    
    def _extract_voice_characteristics(self, audio_data):
        """
        Extract voice characteristics from audio data.
        
        Args:
            audio_data (numpy.ndarray): Audio data to analyze
            
        Returns:
            dict: Voice characteristics
        """
        # This is a placeholder for actual voice characteristic extraction
        # In a real implementation, this would extract features like:
        # - Pitch statistics (mean, range, variation)
        # - Speaking rate
        # - Voice quality parameters
        # - Speaker embeddings
        
        # Simplified placeholder implementation
        return {
            "pitch_mean": 0.0,
            "pitch_range": 0.0,
            "speaking_rate": 1.0,
            "voice_quality": "neutral"
        }
    
    def _apply_voice_characteristics(self, audio_data, voice_characteristics):
        """
        Apply voice characteristics to audio data.
        
        Args:
            audio_data (numpy.ndarray): Audio data to modify
            voice_characteristics (dict): Voice characteristics to apply
            
        Returns:
            numpy.ndarray: Modified audio data
        """
        # This is a placeholder for actual voice characteristic application
        # In a real implementation, this would apply transformations like:
        # - Pitch shifting to match statistics
        # - Time stretching to match speaking rate
        # - Spectral modifications for voice quality
        # - Voice conversion using speaker embeddings
        
        # Return unmodified audio for now
        return audio_data
    
    def get_voice_models_for_language(self, language_code):
        """
        Get available voice models for a language.
        
        Args:
            language_code (str): Language code
            
        Returns:
            list: Available voice models
        """
        return self.language_voice_models.get(language_code, ["default"])
    
    def real_time_translate(self, audio_chunk, context, target_language="en", source_language=None,
                          identity_preservation=True, voice_model=None):
        """
        Process a chunk of audio for real-time translation.
        
        Args:
            audio_chunk (numpy.ndarray): Audio chunk to process
            context (dict): Translation context for maintaining state
            target_language (str): Target language code
            source_language (str, optional): Source language code
            identity_preservation (bool): Whether to preserve speaker identity
            voice_model (str, optional): Voice model to use
            
        Returns:
            dict: Processing result with translated audio chunk and updated context
        """
        try:
            # Initialize context if needed
            if not context:
                context = {
                    "buffer": np.array([], dtype=np.float32),
                    "last_translation": None,
                    "silence_frames": 0,
                    "is_speaking": False,
                    "current_utterance": np.array([], dtype=np.float32),
                    "translations": []
                }
            
            # Add chunk to buffer
            context["buffer"] = np.concatenate([context["buffer"], audio_chunk])
            
            # Check for speech activity
            is_speech = self._detect_speech(audio_chunk)
            
            if is_speech:
                context["silence_frames"] = 0
                context["is_speaking"] = True
                
                # Add to current utterance
                context["current_utterance"] = np.concatenate([context["current_utterance"], audio_chunk])
            else:
                context["silence_frames"] += 1
                
                # If we've detected enough silence after speech, process the utterance
                if context["is_speaking"] and context["silence_frames"] >= 10:  # Adjust threshold as needed
                    context["is_speaking"] = False
                    
                    # Process the complete utterance
                    if len(context["current_utterance"]) > 0:
                        # Translate the utterance
                        translation_result = self.translate_and_preserve_identity(
                            context["current_utterance"],
                            target_language,
                            source_language,
                            identity_preservation,
                            voice_model
                        )
                        
                        # Store the translation
                        context["last_translation"] = translation_result
                        context["translations"].append(translation_result)
                        
                        # Reset current utterance
                        context["current_utterance"] = np.array([], dtype=np.float32)
                        
                        # Return the translated audio
                        return {
                            "context": context,
                            "has_translation": True,
                            "translation": translation_result
                        }
            
            # If no translation yet, return empty result
            return {
                "context": context,
                "has_translation": False
            }
        except Exception as e:
            logger.error(f"Error in real-time translation: {str(e)}")
            return {
                "context": context,
                "has_translation": False,
                "error": str(e)
            }
    
    def _detect_speech(self, audio_chunk, threshold=0.01):
        """
        Detect speech in an audio chunk.
        
        Args:
            audio_chunk (numpy.ndarray): Audio chunk to analyze
            threshold (float): Energy threshold for speech detection
            
        Returns:
            bool: True if speech detected, False otherwise
        """
        # Simple energy-based speech detection
        energy = np.mean(np.square(audio_chunk))
        return energy > threshold

# Create a singleton instance
language_translation_manager = LanguageTranslationManager()

# Function to get the language translation manager instance
def get_language_translation_manager():
    """Get the language translation manager instance."""
    return language_translation_manager