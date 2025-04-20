"""
Realtime accent preview module for Dexent.ai.
Implements preview functionality for accent conversion before final processing.
"""

import os
import logging
import tempfile
import threading
import numpy as np
import soundfile as sf
from queue import Queue
from datetime import datetime
from accent_conversion import AccentConversionPipeline
from noise_suppression import NoiseSuppressionModel
from tts import TextToSpeech
from config import SETTINGS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealtimePreviewProcessor:
    """Processes audio for realtime preview of accent conversion."""
    
    def __init__(self, preview_duration=5):
        """
        Initialize the realtime preview processor.
        
        Args:
            preview_duration (int): Maximum duration of preview in seconds
        """
        self.preview_duration = preview_duration
        self.preview_queue = Queue(maxsize=10)  # Queue for preview requests
        self.running = False
        self.thread = None
        self.sample_rate = SETTINGS["SAMPLE_RATE"]
        self.preview_dir = "previews"
        self.temp_dir = tempfile.gettempdir()
        self.current_jobs = {}
        
        # Create preview directory if it doesn't exist
        os.makedirs(self.preview_dir, exist_ok=True)
        
        # Initialize audio processing components
        self.noise_suppressor = NoiseSuppressionModel()
        # These will be created on demand based on target accent
        self.accent_converters = {}
        self.tts_engines = {}
    
    def start(self):
        """Start the preview processing thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._process_loop)
            self.thread.daemon = True
            self.thread.start()
            logger.info("Realtime preview processor started")
    
    def stop(self):
        """Stop the preview processing thread."""
        if self.running:
            self.running = False
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5)
            logger.info("Realtime preview processor stopped")
    
    def _process_loop(self):
        """Main processing loop for preview requests."""
        while self.running:
            try:
                # Get a preview request from the queue
                request = self.preview_queue.get(timeout=1)
                
                # Process the request
                self._process_preview_request(request)
                
                # Mark the task as done
                self.preview_queue.task_done()
            except:
                # Queue.get timeout or other error, just continue
                pass
    
    def _process_preview_request(self, request):
        """
        Process a preview request.
        
        Args:
            request (dict): Preview request containing audio data and processing parameters
        """
        try:
            # Extract request data
            job_id = request.get("job_id")
            audio_data = request.get("audio_data")
            target_accent = request.get("target_accent", "american")
            noise_suppression = request.get("noise_suppression", True)
            identity_preservation = request.get("identity_preservation", True)
            callback_url = request.get("callback_url")
            
            # Update job status
            self._update_job_status(job_id, "processing")
            
            # Process audio data
            processed_audio = self._process_audio(
                audio_data, 
                target_accent, 
                noise_suppression, 
                identity_preservation
            )
            
            if processed_audio is not None:
                # Save processed audio to a temporary file
                preview_file = self._save_preview(job_id, processed_audio)
                
                # Update job status
                self._update_job_status(job_id, "completed", preview_file)
                
                # If callback URL provided, notify completion
                if callback_url:
                    self._notify_completion(callback_url, job_id, preview_file)
            else:
                # Update job status with error
                self._update_job_status(job_id, "error", "Processing failed")
        except Exception as e:
            logger.error(f"Error processing preview request: {str(e)}")
            self._update_job_status(job_id, "error", str(e))
    
    def _process_audio(self, audio_data, target_accent, noise_suppression, identity_preservation):
        """
        Process audio data with specified parameters.
        
        Args:
            audio_data (numpy.ndarray): Audio data to process
            target_accent (str): Target accent for conversion
            noise_suppression (bool): Whether to apply noise suppression
            identity_preservation (bool): Whether to preserve speaker identity
            
        Returns:
            numpy.ndarray: Processed audio data, or None if processing failed
        """
        try:
            # Apply noise suppression if enabled
            if noise_suppression:
                audio_data = self.noise_suppressor.process(audio_data)
            
            # Apply accent conversion if target accent is specified
            if target_accent:
                # Get or create accent converter for this target accent
                if target_accent not in self.accent_converters:
                    self.accent_converters[target_accent] = AccentConversionPipeline(
                        target_accent=target_accent,
                        preserve_identity=identity_preservation
                    )
                
                # Convert accent
                audio_data = self.accent_converters[target_accent].process(
                    audio_data, 
                    preserve_identity=identity_preservation
                )
            
            return audio_data
        except Exception as e:
            logger.error(f"Error processing audio for preview: {str(e)}")
            return None
    
    def _save_preview(self, job_id, audio_data):
        """
        Save processed audio to a preview file.
        
        Args:
            job_id (str): Job ID
            audio_data (numpy.ndarray): Processed audio data
            
        Returns:
            str: Path to preview file
        """
        try:
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"preview_{job_id}_{timestamp}.wav"
            filepath = os.path.join(self.preview_dir, filename)
            
            # Save audio data
            sf.write(filepath, audio_data, self.sample_rate)
            
            return filepath
        except Exception as e:
            logger.error(f"Error saving preview file: {str(e)}")
            return None
    
    def _update_job_status(self, job_id, status, result=None):
        """
        Update the status of a preview job.
        
        Args:
            job_id (str): Job ID
            status (str): Job status (queued, processing, completed, error)
            result (str, optional): Job result (e.g., path to preview file or error message)
        """
        if job_id in self.current_jobs:
            self.current_jobs[job_id].update({
                "status": status,
                "updated_at": datetime.now().isoformat()
            })
            
            if result is not None:
                self.current_jobs[job_id]["result"] = result
    
    def _notify_completion(self, callback_url, job_id, preview_file):
        """
        Notify completion of a preview job.
        This would typically send a request to a webhook or socket connection.
        
        Args:
            callback_url (str): URL to notify
            job_id (str): Job ID
            preview_file (str): Path to preview file
        """
        # In a real implementation, this would make an HTTP request or emit a socket event
        logger.info(f"Job {job_id} completed. Preview file: {preview_file}")
        # Example: requests.post(callback_url, json={"job_id": job_id, "preview_file": preview_file})
    
    def submit_preview_request(self, audio_data, target_accent="american", 
                             noise_suppression=True, identity_preservation=True, 
                             callback_url=None):
        """
        Submit a request for realtime preview processing.
        
        Args:
            audio_data (numpy.ndarray): Audio data to process
            target_accent (str): Target accent for conversion
            noise_suppression (bool): Whether to apply noise suppression
            identity_preservation (bool): Whether to preserve speaker identity
            callback_url (str, optional): URL to notify on completion
            
        Returns:
            dict: Job information with job_id and status
        """
        try:
            # Check if audio data is valid
            if audio_data is None or len(audio_data) == 0:
                return {"error": "Invalid audio data"}
            
            # Trim audio data to maximum preview duration
            max_samples = self.preview_duration * self.sample_rate
            if len(audio_data) > max_samples:
                audio_data = audio_data[:max_samples]
            
            # Generate job ID
            job_id = f"preview_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            
            # Create job record
            job = {
                "job_id": job_id,
                "status": "queued",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "parameters": {
                    "target_accent": target_accent,
                    "noise_suppression": noise_suppression,
                    "identity_preservation": identity_preservation
                }
            }
            
            # Store job record
            self.current_jobs[job_id] = job
            
            # Create request
            request = {
                "job_id": job_id,
                "audio_data": audio_data,
                "target_accent": target_accent,
                "noise_suppression": noise_suppression,
                "identity_preservation": identity_preservation,
                "callback_url": callback_url
            }
            
            # Start processor if not already running
            if not self.running:
                self.start()
            
            # Add request to queue
            self.preview_queue.put(request)
            
            # Return job information
            return {
                "job_id": job_id,
                "status": "queued",
                "message": "Preview request submitted successfully"
            }
        except Exception as e:
            logger.error(f"Error submitting preview request: {str(e)}")
            return {"error": str(e)}
    
    def get_job_status(self, job_id):
        """
        Get the status of a preview job.
        
        Args:
            job_id (str): Job ID
            
        Returns:
            dict: Job information with status and result (if available)
        """
        if job_id in self.current_jobs:
            return self.current_jobs[job_id]
        else:
            return {"error": "Job not found"}
    
    def list_jobs(self, limit=10):
        """
        List recent preview jobs.
        
        Args:
            limit (int): Maximum number of jobs to return
            
        Returns:
            list: List of job information dictionaries
        """
        # Sort jobs by creation time (newest first)
        sorted_jobs = sorted(
            self.current_jobs.values(),
            key=lambda job: job.get("created_at", ""),
            reverse=True
        )
        
        # Return limited number of jobs
        return sorted_jobs[:limit]
    
    def compare_previews(self, original_audio, processed_audio):
        """
        Generate comparison data for original and processed audio.
        
        Args:
            original_audio (numpy.ndarray): Original audio data
            processed_audio (numpy.ndarray): Processed audio data
            
        Returns:
            dict: Comparison data
        """
        try:
            # Ensure both arrays are the same length
            min_length = min(len(original_audio), len(processed_audio))
            original = original_audio[:min_length]
            processed = processed_audio[:min_length]
            
            # Calculate basic metrics
            original_rms = np.sqrt(np.mean(np.square(original)))
            processed_rms = np.sqrt(np.mean(np.square(processed)))
            
            # Calculate difference signal
            difference = processed - original
            difference_rms = np.sqrt(np.mean(np.square(difference)))
            
            # Calculate signal-to-noise ratio (SNR)
            if difference_rms > 0:
                snr = 20 * np.log10(processed_rms / difference_rms)
            else:
                snr = float('inf')
            
            # Return comparison data
            return {
                "original_rms": float(original_rms),
                "processed_rms": float(processed_rms),
                "difference_rms": float(difference_rms),
                "snr_db": float(snr) if not np.isinf(snr) else None,
                "length_seconds": min_length / self.sample_rate
            }
        except Exception as e:
            logger.error(f"Error comparing previews: {str(e)}")
            return {"error": str(e)}

# Create a singleton instance
realtime_preview_processor = RealtimePreviewProcessor()

# Function to get the realtime preview processor instance
def get_realtime_preview_processor():
    """Get the realtime preview processor instance."""
    return realtime_preview_processor