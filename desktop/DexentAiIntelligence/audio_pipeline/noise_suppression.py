"""
Noise suppression module using RNNoise or DeepFilterNet.
"""
import os
import logging
import numpy as np
import soundfile as sf
from config import NOISE_SUPPRESSION_MODEL, PROCESSED_AUDIO_DIR

logger = logging.getLogger(__name__)

try:
    # Try to import RNNoise
    import rnnoise
    RNNOISE_AVAILABLE = True
except ImportError:
    logger.warning("RNNoise not available. Install with pip install rnnoise-python")
    RNNOISE_AVAILABLE = False

try:
    # Try to import DeepFilterNet
    import deepfilternet
    DEEPFILTERNET_AVAILABLE = True
except ImportError:
    logger.warning("DeepFilterNet not available. Install with pip install deepfilternet")
    DEEPFILTERNET_AVAILABLE = False

def process_noise_suppression(input_file, job_id):
    """
    Apply noise suppression to an audio file.
    
    Args:
        input_file (str): Path to input audio file
        job_id (int): ID of the processing job
        
    Returns:
        str: Path to output audio file
    """
    logger.info(f"Processing noise suppression for {input_file}")
    
    # Load audio file
    audio, sample_rate = sf.read(input_file)
    
    # Ensure audio is mono
    if len(audio.shape) > 1:
        audio = audio.mean(axis=1)
    
    # Process with selected model
    if NOISE_SUPPRESSION_MODEL == "rnnoise" and RNNOISE_AVAILABLE:
        processed_audio = _apply_rnnoise(audio, sample_rate)
    elif NOISE_SUPPRESSION_MODEL == "deepfilternet" and DEEPFILTERNET_AVAILABLE:
        processed_audio = _apply_deepfilternet(audio, sample_rate)
    else:
        logger.warning(f"Selected noise suppression model {NOISE_SUPPRESSION_MODEL} not available. Using dummy processor.")
        processed_audio = audio  # Fallback to no processing
    
    # Save output
    output_dir = os.path.join(PROCESSED_AUDIO_DIR, f"job_{job_id}")
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, "noise_suppressed.wav")
    sf.write(output_file, processed_audio, sample_rate)
    
    logger.info(f"Noise suppression completed. Output saved to {output_file}")
    return output_file

def _apply_rnnoise(audio, sample_rate):
    """
    Apply RNNoise noise suppression.
    
    Args:
        audio (numpy.ndarray): Audio data
        sample_rate (int): Sample rate
        
    Returns:
        numpy.ndarray: Processed audio data
    """
    if not RNNOISE_AVAILABLE:
        logger.error("RNNoise not available")
        return audio
    
    # RNNoise expects 16kHz sample rate
    if sample_rate != 16000:
        # In a real implementation, we would resample here
        logger.warning(f"Sample rate {sample_rate} is not 16kHz. Resampling would be required.")
    
    # Apply RNNoise
    # This is a simplified version - in reality, we'd process in frames
    denoiser = rnnoise.RNNoise()
    
    # Process in 10ms frames (160 samples at 16kHz)
    frame_size = 160
    output = np.zeros_like(audio)
    
    for i in range(0, len(audio), frame_size):
        frame = audio[i:i+frame_size]
        if len(frame) < frame_size:
            # Pad the last frame if needed
            frame = np.pad(frame, (0, frame_size - len(frame)))
        
        # Apply denoising
        denoised_frame = denoiser.process_frame(frame)
        
        # Copy to output
        output[i:i+len(denoised_frame)] = denoised_frame
    
    return output

def _apply_deepfilternet(audio, sample_rate):
    """
    Apply DeepFilterNet noise suppression.
    
    Args:
        audio (numpy.ndarray): Audio data
        sample_rate (int): Sample rate
        
    Returns:
        numpy.ndarray: Processed audio data
    """
    if not DEEPFILTERNET_AVAILABLE:
        logger.error("DeepFilterNet not available")
        return audio
    
    # This is a placeholder for DeepFilterNet integration
    # In a real implementation, we would use the DeepFilterNet API
    logger.info("Applying DeepFilterNet noise suppression (placeholder)")
    
    # Simulate processing
    return audio  # Return unmodified audio as placeholder
