"""
Audio processing pipeline for dexent.ai.

This module contains the core audio processing functionality including:
1. Noise suppression
2. Accent conversion with speaker identity preservation
3. Audio I/O handling
4. Virtual microphone integration
"""

import logging
logger = logging.getLogger(__name__)
logger.info("Initializing audio pipeline")
