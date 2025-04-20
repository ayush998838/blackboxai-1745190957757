import os
import logging
import platform
import subprocess
import tempfile
import sounddevice as sd
import numpy as np

logger = logging.getLogger(__name__)

class AudioRouter:
    """
    Handles audio routing through virtual audio devices.
    For Windows, helps set up VB-Audio Virtual Cable or similar solutions.
    """
    
    def __init__(self):
        """Initialize the audio router."""
        self.platform = platform.system()
        self.virtual_mic_setup = False
        logger.info(f"Audio router initialized on platform: {self.platform}")
    
    def setup(self):
        """Set up virtual audio routing based on the platform."""
        if self.platform == "Windows":
            return self._setup_windows()
        elif self.platform == "Darwin":  # macOS
            return self._setup_macos()
        elif self.platform == "Linux":
            return self._setup_linux()
        else:
            logger.warning(f"Unsupported platform for audio routing: {self.platform}")
            return False
    
    def _setup_windows(self):
        """Set up virtual audio routing on Windows."""
        try:
            # Check if VB-Audio Virtual Cable is installed
            # This is a simple check that doesn't actually verify if it's installed
            virtual_outputs = [d for d in sd.query_devices() if "VB-Audio" in d["name"]]
            
            if not virtual_outputs:
                logger.warning("VB-Audio Virtual Cable not detected on Windows")
                self._show_installation_instructions("windows")
                return False
            
            logger.info("Virtual audio devices detected on Windows")
            
            # Display available devices to the user
            self._show_available_devices()
            
            # In a real application, you would set up audio routing here
            # For now, we'll just assume it's set up correctly
            self.virtual_mic_setup = True
            return True
            
        except Exception as e:
            logger.error(f"Error setting up Windows audio routing: {str(e)}")
            return False
    
    def _setup_macos(self):
        """Set up virtual audio routing on macOS."""
        try:
            # Check for BlackHole or similar virtual audio device
            virtual_outputs = [d for d in sd.query_devices() if "BlackHole" in d["name"]]
            
            if not virtual_outputs:
                logger.warning("BlackHole virtual audio device not detected on macOS")
                self._show_installation_instructions("macos")
                return False
            
            logger.info("Virtual audio devices detected on macOS")
            
            # Display available devices to the user
            self._show_available_devices()
            
            # In a real application, you would set up audio routing here
            # For now, we'll just assume it's set up correctly
            self.virtual_mic_setup = True
            return True
            
        except Exception as e:
            logger.error(f"Error setting up macOS audio routing: {str(e)}")
            return False
    
    def _setup_linux(self):
        """Set up virtual audio routing on Linux."""
        try:
            # Check for PulseAudio or JACK
            # This is a very basic check that doesn't verify configuration
            
            # Display available devices to the user
            self._show_available_devices()
            
            # In a real application, you would set up audio routing here
            # For now, we'll just assume it's set up correctly
            logger.info("Assuming PulseAudio/JACK loopback is configured on Linux")
            self.virtual_mic_setup = True
            return True
            
        except Exception as e:
            logger.error(f"Error setting up Linux audio routing: {str(e)}")
            return False
    
    def _show_available_devices(self):
        """Log available audio devices."""
        try:
            devices = sd.query_devices()
            if devices is None or len(devices) == 0:
                logger.warning("No audio devices detected")
                return
                
            logger.info("Available audio devices:")
            
            input_devices = [d for d in devices if d.get("max_input_channels", 0) > 0]
            output_devices = [d for d in devices if d.get("max_output_channels", 0) > 0]
            
            logger.info("Input devices:")
            for i, device in enumerate(input_devices):
                logger.info(f"  {i}: {device.get('name', 'Unknown device')}")
            
            logger.info("Output devices:")
            for i, device in enumerate(output_devices):
                logger.info(f"  {i}: {device.get('name', 'Unknown device')}")
                
        except Exception as e:
            logger.error(f"Error listing audio devices: {str(e)}")
    
    def _show_installation_instructions(self, platform):
        """Show instructions for installing virtual audio devices."""
        if platform == "windows":
            logger.info("VB-Audio Virtual Cable installation instructions:")
            logger.info("1. Download VB-Audio Virtual Cable from https://vb-audio.com/Cable/")
            logger.info("2. Install the software")
            logger.info("3. Restart your computer")
            logger.info("4. Restart Dexent.ai")
        elif platform == "macos":
            logger.info("BlackHole installation instructions:")
            logger.info("1. Install BlackHole using Homebrew: brew install blackhole-2ch")
            logger.info("2. Configure the virtual device in Audio MIDI Setup")
            logger.info("3. Restart Dexent.ai")
        elif platform == "linux":
            logger.info("PulseAudio loopback module instructions:")
            logger.info("1. Install PulseAudio: sudo apt-get install pulseaudio")
            logger.info("2. Load the module: pactl load-module module-loopback")
            logger.info("3. Restart Dexent.ai")
    
    def get_input_device(self):
        """Get the recommended input device for capturing audio."""
        try:
            # Safe way to get default input device
            try:
                default_device_id = sd.default.device[0]  # Get default input device ID
                if default_device_id is not None and default_device_id >= 0:
                    default_input = sd.query_devices(device=default_device_id)
                    if default_input:
                        logger.info(f"Default input device: {default_input.get('name', 'Unknown')}")
                        return default_input.get("name")
                else:
                    logger.warning("Default input device ID is invalid, falling back to device list")
            except Exception as inner_e:
                logger.warning(f"Error getting default input device: {str(inner_e)}")
            
            # Fallback: Look through all devices if default fails
            devices = sd.query_devices()
            if devices:
                # Find first device with input channels
                for device in devices:
                    if device.get("max_input_channels", 0) > 0:
                        logger.info(f"Using input device: {device.get('name', 'Unknown')}")
                        return device.get("name")
            
            # If we reach here, no suitable device was found
            logger.warning("No suitable input device found")
            # Return a fake device name for testing - can be used with mocked audio data
            return "Dexent Virtual Input"
            
        except Exception as e:
            logger.error(f"Error getting input device: {str(e)}")
            return "Dexent Virtual Input"  # Return a fallback device name
    
    def get_output_device(self):
        """Get the recommended output device for playback."""
        try:
            # Safe way to get default output device
            try:
                default_device_id = sd.default.device[1]  # Get default output device ID
                if default_device_id is not None and default_device_id >= 0:
                    default_output = sd.query_devices(device=default_device_id)
                    if default_output:
                        logger.info(f"Default output device: {default_output.get('name', 'Unknown')}")
                        return default_output.get("name")
                else:
                    logger.warning("Default output device ID is invalid, falling back to device list")
            except Exception as inner_e:
                logger.warning(f"Error getting default output device: {str(inner_e)}")
            
            # Try to get all devices as fallback
            devices = sd.query_devices()
            if not devices:
                logger.warning("No audio devices found")
                return "Dexent Virtual Output"
                
            # Look for virtual audio device first
            virtual_devices = []
            try:
                if self.platform == "Windows":
                    virtual_devices = [d for d in devices if "VB-Audio" in d.get("name", "") 
                                      and d.get("max_output_channels", 0) > 0]
                elif self.platform == "Darwin":  # macOS
                    virtual_devices = [d for d in devices if "BlackHole" in d.get("name", "") 
                                      and d.get("max_output_channels", 0) > 0]
            except Exception as inner_e:
                logger.warning(f"Error checking for virtual devices: {str(inner_e)}")
                virtual_devices = []
            
            if virtual_devices:
                logger.info(f"Found virtual output device: {virtual_devices[0].get('name', 'Unknown')}")
                return virtual_devices[0].get("name")
            
            # Fallback: Look for any output device
            for device in devices:
                if device.get("max_output_channels", 0) > 0:
                    logger.info(f"Using output device: {device.get('name', 'Unknown')}")
                    return device.get("name")
            
            # If we reach here, no suitable device was found
            logger.warning("No suitable output device found")
            return "Dexent Virtual Output"  # Return a fallback device name
            
        except Exception as e:
            logger.error(f"Error getting output device: {str(e)}")
            return "Dexent Virtual Output"  # Return a fallback device name
    
    def cleanup(self):
        """Clean up any audio routing configuration."""
        logger.info("Cleaning up audio routing")
        self.virtual_mic_setup = False
