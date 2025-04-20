"""
Configuration settings for the Dexent.ai application.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Application settings
SETTINGS = {
    # Database settings
    "DATABASE_URL": os.environ.get("DATABASE_URL", "sqlite:///dexent.db"),
    
    # Audio processing settings
    "SAMPLE_RATE": 16000,
    "BUFFER_SIZE": 1024,
    "DEFAULT_NOISE_SUPPRESSION_LEVEL": 50,
    "DEFAULT_TARGET_ACCENT": "american",
    
    # API settings
    "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
    
    # Firebase settings
    "FIREBASE_API_KEY": os.environ.get("FIREBASE_API_KEY"),
    "FIREBASE_PROJECT_ID": os.environ.get("FIREBASE_PROJECT_ID"),
    "FIREBASE_APP_ID": os.environ.get("FIREBASE_APP_ID"),
    
    # File upload settings
    "UPLOAD_FOLDER": "uploads",
    "PROCESSED_FOLDER": "processed",
    "ALLOWED_EXTENSIONS": {"wav", "mp3", "ogg", "flac"},
    "MAX_CONTENT_LENGTH": 16 * 1024 * 1024,  # 16 MB
    
    # Session settings
    "SESSION_SECRET": os.environ.get("SESSION_SECRET", "dexent-ai-secret-key"),
}

# Model paths
MODEL_PATHS = {
    "WHISPER_MODEL": "models/whisper-small",
    "TTS_MODEL": "models/styletts2",
    "RNNOISE_MODEL": "models/rnnoise",
}

# Audio device settings
AUDIO_SETTINGS = {
    "DEFAULT_INPUT_DEVICE": None,  # Auto-select
    "DEFAULT_OUTPUT_DEVICE": None,  # Auto-select
    "SAMPLE_FORMAT": "float32",
    "CHANNELS": 1,
}

# Accent options
ACCENT_OPTIONS = [
    "american",
    "british",
    "australian",
    "indian",
    "spanish",
    "french",
    "german",
    "chinese",
    "japanese",
    "russian",
]

# Create required directories
os.makedirs(SETTINGS["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(SETTINGS["PROCESSED_FOLDER"], exist_ok=True)
os.makedirs("models", exist_ok=True)