import logging
import threading
import time
import numpy as np
import sounddevice as sd
from noise_suppression import NoiseSuppressionModel
from accent_conversion import AccentConversionPipeline
from audio_routing import AudioRouter

logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self, noise_suppression=True, accent_conversion=False, 
                 target_accent='american', identity_preservation=True,
                 sample_rate=16000, buffer_size=1024):
        """
        Initialize the audio processing pipeline.
        
        Args:
            noise_suppression (bool): Whether to enable noise suppression
            accent_conversion (bool): Whether to enable accent conversion
            target_accent (str): Target accent for conversion ('american', 'british', etc.)
            identity_preservation (bool): Whether to preserve speaker identity
            sample_rate (int): Audio sample rate
            buffer_size (int): Processing buffer size
        """
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.running = False
        self.thread = None
        
        # Initialize processing components
        self.noise_suppressor = NoiseSuppressionModel()
        self.accent_converter = AccentConversionPipeline(
            target_accent=target_accent,
            preserve_identity=identity_preservation
        )
        self.audio_router = AudioRouter()
        
        # Configure settings
        self.update_settings(
            noise_suppression=noise_suppression,
            accent_conversion=accent_conversion,
            target_accent=target_accent,
            identity_preservation=identity_preservation
        )
        
        logger.info("Audio processor initialized")
    
    def update_settings(self, noise_suppression=None, accent_conversion=None, 
                       target_accent=None, identity_preservation=None):
        """Update the audio processing settings."""
        if noise_suppression is not None:
            self.noise_suppression_enabled = noise_suppression
        
        if accent_conversion is not None:
            self.accent_conversion_enabled = accent_conversion
        
        if target_accent is not None:
            self.target_accent = target_accent
            if hasattr(self.accent_converter, 'set_target_accent'):
                self.accent_converter.set_target_accent(target_accent)
        
        if identity_preservation is not None:
            self.identity_preservation_enabled = identity_preservation
            if hasattr(self.accent_converter, 'set_identity_preservation'):
                self.accent_converter.set_identity_preservation(identity_preservation)
        
        logger.info(f"Settings updated: NS={self.noise_suppression_enabled}, "
                  f"AC={self.accent_conversion_enabled}, Accent={self.target_accent}, "
                  f"Identity={self.identity_preservation_enabled}")
    
    def process_audio(self, audio_data):
        """
        Process audio data through the active components of the pipeline.
        
        Args:
            audio_data (numpy.ndarray): Raw audio data to process
            
        Returns:
            numpy.ndarray: Processed audio data
        """
        processed_data = audio_data.copy()
        
        # Apply noise suppression if enabled
        if self.noise_suppression_enabled:
            processed_data = self.noise_suppressor.process(processed_data)
        
        # Apply accent conversion if enabled
        if self.accent_conversion_enabled:
            # Accent conversion is more complex and has higher latency
            # Only process chunks with voice activity
            if self.noise_suppressor.voice_activity_detected:
                processed_data = self.accent_converter.process(
                    processed_data, 
                    preserve_identity=self.identity_preservation_enabled
                )
        
        return processed_data
    
    def audio_callback(self, indata, outdata, frames, time, status):
        """Callback for real-time audio processing."""
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        # Process the input audio
        processed = self.process_audio(indata.copy())
        
        # Send to output
        outdata[:] = processed
    
    def start(self):
        """Start the audio processing."""
        if self.running:
            logger.warning("Audio processor is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._processing_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info("Audio processor started")
    
    def stop(self):
        """Stop the audio processing."""
        if not self.running:
            logger.warning("Audio processor is not running")
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
            self.thread = None
        
        logger.info("Audio processor stopped")
    
    def is_running(self):
        """Check if the audio processor is running."""
        return self.running
    
    def _processing_loop(self):
        """Main processing loop running in a separate thread."""
        try:
            # Setup virtual audio routing
            self.audio_router.setup()
            
            # Get device information
            input_device = self.audio_router.get_input_device()
            output_device = self.audio_router.get_output_device()
            
            if not input_device or not output_device:
                logger.error("No audio devices available - using mock devices for testing")
                self._run_mock_processing_loop()
                return
                
            logger.info(f"Starting audio stream with input={input_device}, output={output_device}")
            
            # Use robust error handling for stream initialization
            try:
                # Start streaming with callback
                with sd.Stream(
                    channels=1,
                    dtype='float32',
                    samplerate=self.sample_rate,
                    blocksize=self.buffer_size,
                    callback=self.audio_callback,
                    device=(input_device, output_device),
                    latency='high'  # More stable but higher latency
                ):
                    logger.info(f"Audio stream started: sample_rate={self.sample_rate}, buffer_size={self.buffer_size}")
                    
                    # Keep the stream running until stop() is called
                    while self.running:
                        time.sleep(0.1)
            except ValueError as ve:
                logger.error(f"Invalid parameters for audio stream: {str(ve)}")
                logger.info("Falling back to default devices")
                
                # Fall back to defaults with fewer parameters
                with sd.Stream(
                    samplerate=self.sample_rate,
                    callback=self.audio_callback,
                    latency='high'  # More stable but higher latency
                ):
                    logger.info("Audio stream started with default parameters")
                    
                    # Keep the stream running until stop() is called
                    while self.running:
                        time.sleep(0.1)
                        
        except Exception as e:
            logger.error(f"Error in audio processing loop: {str(e)}")
            self.running = False
            # Try to run in mock mode as a fallback
            self._run_mock_processing_loop()
        finally:
            # Clean up audio routing
            self.audio_router.cleanup()
            logger.info("Audio processing loop ended")
            
    def _run_mock_processing_loop(self):
        """Run a mock processing loop that simulates audio processing."""
        logger.info("Starting mock audio processing (simulation mode)")
        
        try:
            # Create a mock test signal (sine wave)
            sample_rate = self.sample_rate
            duration = 3.0  # 3 seconds of audio
            frequency = 440.0  # A4 note
            
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            test_signal = 0.3 * np.sin(2 * np.pi * frequency * t)  # Sine wave
            
            # Add noise to make it more realistic
            noise = 0.05 * np.random.normal(0, 1, len(test_signal))
            test_signal = test_signal + noise
            
            # Convert to float32 format
            mock_audio = test_signal.astype(np.float32)
            
            # Process in chunks to simulate real-time processing
            chunk_size = self.buffer_size
            chunks = [mock_audio[i:i+chunk_size] for i in range(0, len(mock_audio), chunk_size)]
            
            logger.info(f"Mock audio processing ready with {len(chunks)} chunks")
            
            # Simulate processing until stopped
            chunk_index = 0
            while self.running:
                # Process current chunk
                current_chunk = chunks[chunk_index % len(chunks)]
                processed_chunk = self.process_audio(current_chunk)
                
                # Log every 10 chunks
                if chunk_index % 10 == 0:
                    logger.info(f"Processed mock audio chunk {chunk_index}")
                
                # Move to next chunk
                chunk_index += 1
                time.sleep(chunk_size / sample_rate)  # Sleep to simulate real-time processing
                
            logger.info("Mock audio processing stopped")
            
        except Exception as e:
            logger.error(f"Error in mock processing loop: {str(e)}")
            self.running = False
