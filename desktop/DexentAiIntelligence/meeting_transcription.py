"""
Meeting transcription module for Dexent.ai.
Implements real-time meeting transcription and summarization.
"""

import os
import json
import time
import uuid
import logging
import threading
from queue import Queue
from datetime import datetime
import numpy as np
import torch
import whisper
from flask_login import current_user
from config import SETTINGS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
TRANSCRIPTION_DATA_FOLDER = "data/transcriptions"
SUMMARY_MODEL_PATH = "models/meeting_summarization"

# Ensure directories exist
os.makedirs(TRANSCRIPTION_DATA_FOLDER, exist_ok=True)

class MeetingTranscriptionManager:
    """Manages real-time meeting transcription and summarization."""
    
    def __init__(self):
        """Initialize the meeting transcription manager."""
        self.transcription_queue = Queue(maxsize=100)
        self.running = False
        self.thread = None
        self.active_sessions = {}
        self.sample_rate = SETTINGS["SAMPLE_RATE"]
        
        # Load whisper model for transcription
        self.model_size = "base"  # Can be 'tiny', 'base', 'small', 'medium', 'large'
        try:
            self.transcription_model = whisper.load_model(self.model_size)
            logger.info(f"Loaded Whisper {self.model_size} model for transcription")
        except Exception as e:
            logger.error(f"Error loading Whisper model: {str(e)}")
            self.transcription_model = None
    
    def start(self):
        """Start the transcription processing thread."""
        if not self.running and self.transcription_model is not None:
            self.running = True
            self.thread = threading.Thread(target=self._process_loop)
            self.thread.daemon = True
            self.thread.start()
            logger.info("Meeting transcription processor started")
            return True
        return False
    
    def stop(self):
        """Stop the transcription processing thread."""
        if self.running:
            self.running = False
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5)
            logger.info("Meeting transcription processor stopped")
    
    def _process_loop(self):
        """Main processing loop for transcription requests."""
        while self.running:
            try:
                # Get a transcription request from the queue
                request = self.transcription_queue.get(timeout=1)
                
                # Process the request
                self._process_transcription_request(request)
                
                # Mark the task as done
                self.transcription_queue.task_done()
            except:
                # Queue.get timeout or other error, just continue
                pass
    
    def _process_transcription_request(self, request):
        """
        Process a transcription request.
        
        Args:
            request (dict): Transcription request containing audio data and metadata
        """
        try:
            # Extract request data
            session_id = request.get("session_id")
            audio_data = request.get("audio_data")
            metadata = request.get("metadata", {})
            timestamp = request.get("timestamp", datetime.now().isoformat())
            
            # Check if session exists
            if session_id not in self.active_sessions:
                logger.warning(f"Session {session_id} not found")
                return
            
            # Transcribe audio
            transcription = self._transcribe_audio(audio_data)
            
            if transcription:
                # Add transcription to session
                self._add_transcription_to_session(session_id, transcription, timestamp, metadata)
        except Exception as e:
            logger.error(f"Error processing transcription request: {str(e)}")
    
    def _transcribe_audio(self, audio_data):
        """
        Transcribe audio data using Whisper.
        
        Args:
            audio_data (numpy.ndarray): Audio data to transcribe
            
        Returns:
            dict: Transcription result with text, segments, and language
        """
        try:
            if self.transcription_model is None:
                return None
            
            # Convert to float32 if needed
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Normalize audio data
            if np.max(np.abs(audio_data)) > 0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            # Transcribe using Whisper
            result = self.transcription_model.transcribe(audio_data, temperature=0)
            
            # Extract relevant information
            transcription = {
                "text": result["text"],
                "segments": result["segments"],
                "language": result["language"]
            }
            
            return transcription
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return None
    
    def _add_transcription_to_session(self, session_id, transcription, timestamp, metadata):
        """
        Add a transcription to a session.
        
        Args:
            session_id (str): Session ID
            transcription (dict): Transcription data
            timestamp (str): Timestamp of the transcription
            metadata (dict): Additional metadata
        """
        try:
            session = self.active_sessions[session_id]
            
            # Add transcription with metadata
            transcription_entry = {
                "id": str(uuid.uuid4()),
                "timestamp": timestamp,
                "text": transcription["text"],
                "segments": transcription["segments"],
                "language": transcription["language"],
                "metadata": metadata
            }
            
            session["transcriptions"].append(transcription_entry)
            
            # Update full transcript
            session["full_transcript"] += " " + transcription["text"]
            
            # Save session
            self._save_session(session_id)
            
            # Notify listeners if configured
            if "callback_url" in session:
                self._notify_transcription_update(session["callback_url"], session_id, transcription_entry)
        except Exception as e:
            logger.error(f"Error adding transcription to session: {str(e)}")
    
    def _save_session(self, session_id):
        """
        Save a session to file.
        
        Args:
            session_id (str): Session ID
        """
        try:
            session = self.active_sessions[session_id]
            
            # Create session file path
            file_path = os.path.join(TRANSCRIPTION_DATA_FOLDER, f"{session_id}.json")
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(session, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving session: {str(e)}")
    
    def _notify_transcription_update(self, callback_url, session_id, transcription):
        """
        Notify listeners of transcription updates.
        
        Args:
            callback_url (str): URL to notify
            session_id (str): Session ID
            transcription (dict): Transcription data
        """
        # This would typically make an HTTP request or emit a socket event
        logger.info(f"Transcription update for session {session_id}")
        # Example: requests.post(callback_url, json={"session_id": session_id, "transcription": transcription})
    
    def create_session(self, name, user_id=None, metadata=None, callback_url=None):
        """
        Create a new transcription session.
        
        Args:
            name (str): Session name
            user_id (int, optional): User ID of the session creator
            metadata (dict, optional): Additional metadata
            callback_url (str, optional): URL to notify of transcription updates
            
        Returns:
            dict: Session information
        """
        try:
            # Generate a unique session ID
            session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}_{str(uuid.uuid4())[:8]}"
            
            # Create session record
            session = {
                "id": session_id,
                "name": name,
                "user_id": user_id,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "status": "active",
                "transcriptions": [],
                "full_transcript": "",
                "summary": None,
                "metadata": metadata or {},
                "callback_url": callback_url
            }
            
            # Store session
            self.active_sessions[session_id] = session
            
            # Save session
            self._save_session(session_id)
            
            # Start processor if not already running
            if not self.running:
                self.start()
            
            return {
                "session_id": session_id,
                "name": name,
                "created_at": session["created_at"],
                "status": "active"
            }
        except Exception as e:
            logger.error(f"Error creating transcription session: {str(e)}")
            return {"error": str(e)}
    
    def end_session(self, session_id):
        """
        End a transcription session.
        
        Args:
            session_id (str): Session ID
            
        Returns:
            dict: Session information
        """
        try:
            if session_id not in self.active_sessions:
                return {"error": "Session not found"}
            
            # Update session status
            self.active_sessions[session_id]["status"] = "completed"
            self.active_sessions[session_id]["updated_at"] = datetime.now().isoformat()
            
            # Save session
            self._save_session(session_id)
            
            # Generate summary
            summary = self.generate_summary(session_id)
            
            return {
                "session_id": session_id,
                "status": "completed",
                "summary": summary
            }
        except Exception as e:
            logger.error(f"Error ending transcription session: {str(e)}")
            return {"error": str(e)}
    
    def add_audio_data(self, session_id, audio_data, metadata=None):
        """
        Add audio data to a session for transcription.
        
        Args:
            session_id (str): Session ID
            audio_data (numpy.ndarray): Audio data to transcribe
            metadata (dict, optional): Additional metadata
            
        Returns:
            dict: Status information
        """
        try:
            if session_id not in self.active_sessions:
                return {"error": "Session not found"}
            
            if self.active_sessions[session_id]["status"] != "active":
                return {"error": "Session is not active"}
            
            # Create transcription request
            request = {
                "session_id": session_id,
                "audio_data": audio_data,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            # Add to queue
            self.transcription_queue.put(request)
            
            return {"status": "queued"}
        except Exception as e:
            logger.error(f"Error adding audio data to session: {str(e)}")
            return {"error": str(e)}
    
    def get_session(self, session_id):
        """
        Get information about a transcription session.
        
        Args:
            session_id (str): Session ID
            
        Returns:
            dict: Session information
        """
        try:
            if session_id in self.active_sessions:
                return self.active_sessions[session_id]
            else:
                # Try to load from file
                file_path = os.path.join(TRANSCRIPTION_DATA_FOLDER, f"{session_id}.json")
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        return json.load(f)
                else:
                    return {"error": "Session not found"}
        except Exception as e:
            logger.error(f"Error getting session: {str(e)}")
            return {"error": str(e)}
    
    def get_user_sessions(self, user_id, limit=10):
        """
        Get sessions for a specific user.
        
        Args:
            user_id (int): User ID
            limit (int): Maximum number of sessions to return
            
        Returns:
            list: List of session information
        """
        try:
            # Get all sessions for the user
            sessions = []
            
            # Check active sessions
            for session in self.active_sessions.values():
                if session.get("user_id") == user_id:
                    sessions.append({
                        "id": session["id"],
                        "name": session["name"],
                        "created_at": session["created_at"],
                        "updated_at": session["updated_at"],
                        "status": session["status"],
                        "transcription_count": len(session["transcriptions"]),
                        "has_summary": session["summary"] is not None
                    })
            
            # Check saved sessions
            for filename in os.listdir(TRANSCRIPTION_DATA_FOLDER):
                if filename.endswith(".json"):
                    file_path = os.path.join(TRANSCRIPTION_DATA_FOLDER, filename)
                    try:
                        with open(file_path, 'r') as f:
                            session = json.load(f)
                            if session.get("user_id") == user_id and session["id"] not in [s["id"] for s in sessions]:
                                sessions.append({
                                    "id": session["id"],
                                    "name": session["name"],
                                    "created_at": session["created_at"],
                                    "updated_at": session["updated_at"],
                                    "status": session["status"],
                                    "transcription_count": len(session["transcriptions"]),
                                    "has_summary": session["summary"] is not None
                                })
                    except:
                        # Skip invalid files
                        continue
            
            # Sort by creation time (newest first)
            sessions.sort(key=lambda s: s["created_at"], reverse=True)
            
            return sessions[:limit]
        except Exception as e:
            logger.error(f"Error getting user sessions: {str(e)}")
            return []
    
    def delete_session(self, session_id, user_id=None):
        """
        Delete a transcription session.
        
        Args:
            session_id (str): Session ID
            user_id (int, optional): User ID (for authorization check)
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            # Check if session exists
            session = self.get_session(session_id)
            if "error" in session:
                return False
            
            # Check if user is authorized to delete
            if user_id is not None and session.get("user_id") != user_id:
                return False
            
            # Remove from active sessions if present
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            # Delete file
            file_path = os.path.join(TRANSCRIPTION_DATA_FOLDER, f"{session_id}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return True
        except Exception as e:
            logger.error(f"Error deleting session: {str(e)}")
            return False
    
    def generate_summary(self, session_id):
        """
        Generate a summary for a transcription session.
        
        Args:
            session_id (str): Session ID
            
        Returns:
            dict: Summary information
        """
        try:
            session = self.get_session(session_id)
            if "error" in session:
                return {"error": "Session not found"}
            
            # Get full transcript
            transcript = session["full_transcript"]
            
            if not transcript:
                return {"error": "No transcript available"}
            
            # Generate summary (simplified implementation)
            # In a real implementation, this would use a more sophisticated model
            # such as BART, T5, or a custom summarization model
            
            # Simple extractive summarization for now
            summary = self._simple_extractive_summary(transcript)
            
            # Store summary in session
            session["summary"] = {
                "text": summary,
                "generated_at": datetime.now().isoformat(),
                "method": "extractive"
            }
            
            # Save session
            if session_id in self.active_sessions:
                self._save_session(session_id)
            else:
                file_path = os.path.join(TRANSCRIPTION_DATA_FOLDER, f"{session_id}.json")
                with open(file_path, 'w') as f:
                    json.dump(session, f, indent=4)
            
            return session["summary"]
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return {"error": str(e)}
    
    def _simple_extractive_summary(self, text, num_sentences=5):
        """
        Generate a simple extractive summary.
        
        Args:
            text (str): Text to summarize
            num_sentences (int): Number of sentences to include in summary
            
        Returns:
            str: Extractive summary
        """
        import re
        from collections import Counter
        
        # Split into sentences
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
        
        if len(sentences) <= num_sentences:
            return text
        
        # Calculate word frequencies
        words = re.findall(r'\w+', text.lower())
        word_freq = Counter(words)
        
        # Assign scores to sentences based on word frequency
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            score = 0
            for word in re.findall(r'\w+', sentence.lower()):
                if word in word_freq:
                    score += word_freq[word]
            sentence_scores[i] = score
        
        # Get top sentences
        top_indices = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:num_sentences]
        top_indices.sort()  # Preserve original order
        
        # Combine sentences for summary
        summary = ' '.join([sentences[i] for i in top_indices])
        
        return summary
    
    def identify_speakers(self, session_id):
        """
        Identify speakers in a transcription session.
        
        Args:
            session_id (str): Session ID
            
        Returns:
            dict: Speaker identification results
        """
        # This would be implemented using speaker diarization technologies
        # such as speaker embeddings and clustering
        # For now, return a placeholder
        return {
            "error": "Speaker identification not implemented yet"
        }
    
    def export_transcript(self, session_id, format="txt"):
        """
        Export a transcript in various formats.
        
        Args:
            session_id (str): Session ID
            format (str): Export format (txt, json, srt, vtt)
            
        Returns:
            dict: Export result with path to exported file
        """
        try:
            session = self.get_session(session_id)
            if "error" in session:
                return {"error": "Session not found"}
            
            # Create export filename
            export_filename = f"{session_id}_transcript.{format}"
            export_path = os.path.join(TRANSCRIPTION_DATA_FOLDER, export_filename)
            
            if format == "txt":
                # Export as plain text
                with open(export_path, 'w') as f:
                    f.write(session["full_transcript"])
            
            elif format == "json":
                # Export as JSON
                with open(export_path, 'w') as f:
                    json.dump({
                        "session_id": session["id"],
                        "name": session["name"],
                        "created_at": session["created_at"],
                        "transcriptions": session["transcriptions"],
                        "summary": session["summary"]
                    }, f, indent=4)
            
            elif format == "srt" or format == "vtt":
                # Export as subtitle format
                with open(export_path, 'w') as f:
                    for i, segment in enumerate(session["transcriptions"]):
                        if format == "srt":
                            # SRT format
                            f.write(f"{i+1}\n")
                            start_time = self._format_time_srt(segment.get("timestamp"))
                            end_time = self._format_time_srt(segment.get("timestamp", 0) + 5)  # Estimate 5 seconds duration
                            f.write(f"{start_time} --> {end_time}\n")
                            f.write(f"{segment['text']}\n\n")
                        else:
                            # VTT format
                            if i == 0:
                                f.write("WEBVTT\n\n")
                            start_time = self._format_time_vtt(segment.get("timestamp"))
                            end_time = self._format_time_vtt(segment.get("timestamp", 0) + 5)  # Estimate 5 seconds duration
                            f.write(f"{start_time} --> {end_time}\n")
                            f.write(f"{segment['text']}\n\n")
            
            else:
                return {"error": f"Unsupported export format: {format}"}
            
            return {
                "success": True,
                "export_path": export_path,
                "export_format": format
            }
        except Exception as e:
            logger.error(f"Error exporting transcript: {str(e)}")
            return {"error": str(e)}
    
    def _format_time_srt(self, seconds):
        """Format time for SRT subtitle format."""
        if isinstance(seconds, str):
            try:
                timestamp = datetime.fromisoformat(seconds)
                hours = timestamp.hour
                minutes = timestamp.minute
                seconds = timestamp.second
                milliseconds = timestamp.microsecond // 1000
            except:
                hours, minutes, seconds, milliseconds = 0, 0, 0, 0
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            seconds = int(seconds % 60)
            milliseconds = int((seconds - int(seconds)) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    
    def _format_time_vtt(self, seconds):
        """Format time for VTT subtitle format."""
        if isinstance(seconds, str):
            try:
                timestamp = datetime.fromisoformat(seconds)
                hours = timestamp.hour
                minutes = timestamp.minute
                seconds = timestamp.second
                milliseconds = timestamp.microsecond // 1000
            except:
                hours, minutes, seconds, milliseconds = 0, 0, 0, 0
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            seconds = int(seconds % 60)
            milliseconds = int((seconds - int(seconds)) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

# Create a singleton instance
meeting_transcription_manager = MeetingTranscriptionManager()

# Function to get the meeting transcription manager instance
def get_meeting_transcription_manager():
    """Get the meeting transcription manager instance."""
    return meeting_transcription_manager