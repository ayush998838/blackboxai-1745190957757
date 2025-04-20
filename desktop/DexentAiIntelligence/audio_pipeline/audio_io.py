"""
Audio I/O module for handling audio input/output streams.
"""
import logging
import threading
import numpy as np
import queue
import time
import pyaudio
from config import SAMPLE_RATE, CHANNELS, FRAMES_PER_BUFFER, FORMAT

logger = logging.getLogger(__name__)

class AudioIO:
    """
    Handles audio input/output streams using PyAudio.
    """
    def __init__(self):
        self.pa = pyaudio.PyAudio()
        self.input_stream = None
        self.output_stream = None
        self.input_queue = queue.Queue(maxsize=100)
        self.output_queue = queue.Queue(maxsize=100)
        self.is_running = False
        self.processing_thread = None
        
        # Audio processing callbacks
        self.processors = []
        
        logger.info("AudioIO initialized")
    
    def start(self, input_device_index=None, output_device_index=None):
        """
        Start audio I/O streams.
        
        Args:
            input_device_index (int, optional): Input device index
            output_device_index (int, optional): Output device index
        """
        if self.is_running:
            logger.warning("AudioIO already running")
            return
        
        # Start input stream
        self.input_stream = self.pa.open(
            format=self._get_pyaudio_format(FORMAT),
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            input_device_index=input_device_index,
            frames_per_buffer=FRAMES_PER_BUFFER,
            stream_callback=self._input_callback
        )
        
        # Start output stream
        self.output_stream = self.pa.open(
            format=self._get_pyaudio_format(FORMAT),
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            output=True,
            output_device_index=output_device_index,
            frames_per_buffer=FRAMES_PER_BUFFER,
            stream_callback=self._output_callback
        )
        
        self.is_running = True
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self._process_audio, daemon=True)
        self.processing_thread.start()
        
        logger.info("AudioIO started")
    
    def stop(self):
        """Stop audio I/O streams."""
        if not self.is_running:
            logger.warning("AudioIO not running")
            return
        
        self.is_running = False
        
        # Stop streams
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
        
        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
        
        # Clear queues
        self._clear_queue(self.input_queue)
        self._clear_queue(self.output_queue)
        
        # Wait for processing thread to finish
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=1.0)
        
        logger.info("AudioIO stopped")
    
    def add_processor(self, processor_func):
        """
        Add an audio processor function.
        
        Args:
            processor_func (callable): Function that takes a numpy array of audio data
                                      and returns processed audio data
        """
        self.processors.append(processor_func)
        logger.info(f"Added audio processor: {processor_func.__name__}")
    
    def remove_processor(self, processor_func):
        """
        Remove an audio processor function.
        
        Args:
            processor_func (callable): Function to remove
        """
        if processor_func in self.processors:
            self.processors.remove(processor_func)
            logger.info(f"Removed audio processor: {processor_func.__name__}")
    
    def _input_callback(self, in_data, frame_count, time_info, status):
        """Callback for input stream."""
        try:
            self.input_queue.put(in_data, block=False)
        except queue.Full:
            logger.warning("Input queue full, dropping frame")
        
        return (None, pyaudio.paContinue)
    
    def _output_callback(self, in_data, frame_count, time_info, status):
        """Callback for output stream."""
        try:
            data = self.output_queue.get(block=False)
            return (data, pyaudio.paContinue)
        except queue.Empty:
            # Return silence if queue is empty
            return (bytes(frame_count * CHANNELS * 2), pyaudio.paContinue)
    
    def _process_audio(self):
        """Process audio data in a separate thread."""
        while self.is_running:
            try:
                # Get input data
                in_data = self.input_queue.get(block=True, timeout=0.1)
                
                # Convert to numpy array for processing
                audio_data = np.frombuffer(in_data, dtype=np.int16)
                
                # Apply processors
                for processor in self.processors:
                    audio_data = processor(audio_data)
                
                # Convert back to bytes
                out_data = audio_data.astype(np.int16).tobytes()
                
                # Put in output queue
                try:
                    self.output_queue.put(out_data, block=False)
                except queue.Full:
                    logger.warning("Output queue full, dropping frame")
                
            except queue.Empty:
                # Input queue is empty, wait a bit
                time.sleep(0.001)
            except Exception as e:
                logger.error(f"Error processing audio: {e}")
    
    def _clear_queue(self, q):
        """Clear a queue."""
        while not q.empty():
            try:
                q.get(block=False)
            except queue.Empty:
                break
    
    def _get_pyaudio_format(self, format_str):
        """Convert string format to PyAudio format."""
        formats = {
            "int16": pyaudio.paInt16,
            "int24": pyaudio.paInt24,
            "int32": pyaudio.paInt32,
            "float32": pyaudio.paFloat32
        }
        return formats.get(format_str.lower(), pyaudio.paInt16)
    
    def list_devices(self):
        """List available audio devices."""
        devices = []
        for i in range(self.pa.get_device_count()):
            device_info = self.pa.get_device_info_by_index(i)
            devices.append({
                "index": i,
                "name": device_info["name"],
                "max_input_channels": device_info["maxInputChannels"],
                "max_output_channels": device_info["maxOutputChannels"],
                "default_sample_rate": device_info["defaultSampleRate"]
            })
        return devices
    
    def __del__(self):
        """Clean up PyAudio on deletion."""
        self.stop()
        if hasattr(self, 'pa') and self.pa:
            self.pa.terminate()
