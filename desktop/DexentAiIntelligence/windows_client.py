#!/usr/bin/env python
"""
Windows desktop client for Dexent.ai.
This script provides a system tray application for controlling Dexent.ai on Windows.
"""

import os
import sys
import time
import webbrowser
import logging
import signal
import subprocess
import requests
from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QAction,
                           QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                           QComboBox, QCheckBox, QSlider, QPushButton)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
DEFAULT_PORT = 5000
SERVER_URL = f"http://localhost:{DEFAULT_PORT}"

class ServerManager(QThread):
    """Manage the Flask server process."""
    status_changed = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.server_process = None
        self.running = False
        self.check_interval = 5  # seconds
    
    def start_server(self):
        """Start the Flask server."""
        if self.server_process:
            logger.warning("Server is already running.")
            return
        
        try:
            # Determine the path to main.py
            main_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
            
            # Start with Gunicorn for production
            cmd = ["gunicorn", "--bind", f"0.0.0.0:{DEFAULT_PORT}", "--reuse-port", "main:app"]
            
            logger.info(f"Starting server with command: {' '.join(cmd)}")
            
            # Start the server process
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=os.environ.copy()
            )
            
            # Wait for server to start
            time.sleep(2)
            logger.info(f"Server started with PID: {self.server_process.pid}")
            
            # Check if server is running
            if self.is_server_running():
                self.running = True
                self.status_changed.emit(True)
                logger.info(f"Server is running at {SERVER_URL}")
            else:
                logger.warning("Server failed to start.")
        except Exception as e:
            logger.error(f"Error starting server: {str(e)}")
    
    def stop_server(self):
        """Stop the Flask server."""
        if not self.server_process:
            logger.warning("No server is running.")
            return
        
        try:
            # Try to terminate gracefully
            self.server_process.terminate()
            
            # Wait for process to terminate
            try:
                self.server_process.wait(timeout=5)
                logger.info("Server stopped gracefully.")
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate
                self.server_process.kill()
                logger.info("Server forcefully terminated.")
            
            self.server_process = None
            self.running = False
            self.status_changed.emit(False)
        except Exception as e:
            logger.error(f"Error stopping server: {str(e)}")
    
    def is_server_running(self):
        """Check if the server is running."""
        if self.server_process:
            # Check if process is still running
            if self.server_process.poll() is None:
                try:
                    # Try to connect to the server
                    response = requests.get(f"{SERVER_URL}/")
                    return response.status_code == 200
                except requests.ConnectionError:
                    return False
            else:
                # Process has terminated
                self.server_process = None
                return False
        
        # Check if any server is running on the port
        try:
            response = requests.get(f"{SERVER_URL}/")
            return response.status_code == 200
        except requests.ConnectionError:
            return False
    
    def run(self):
        """Thread main loop to periodically check server status."""
        while True:
            is_running = self.is_server_running()
            if is_running != self.running:
                self.running = is_running
                self.status_changed.emit(is_running)
            
            time.sleep(self.check_interval)
    
    def open_dashboard(self):
        """Open the web dashboard in the default browser."""
        if not self.is_server_running():
            logger.warning("Server is not running. Starting server...")
            self.start_server()
        
        webbrowser.open(f"{SERVER_URL}/")
        logger.info(f"Opening dashboard at {SERVER_URL}")


class SettingsDialog(QDialog):
    """Settings dialog for the Dexent.ai application."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dexent.ai Settings")
        self.resize(400, 300)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        # Audio Processing Section
        layout.addWidget(QLabel("<b>Audio Processing</b>"))
        
        # Noise Suppression
        noise_layout = QHBoxLayout()
        self.noise_checkbox = QCheckBox("Noise Suppression")
        self.noise_checkbox.setChecked(True)
        noise_layout.addWidget(self.noise_checkbox)
        
        noise_level_layout = QHBoxLayout()
        noise_level_layout.addWidget(QLabel("Suppression Level:"))
        self.noise_slider = QSlider(Qt.Horizontal)
        self.noise_slider.setRange(0, 100)
        self.noise_slider.setValue(50)
        noise_level_layout.addWidget(self.noise_slider)
        self.noise_level_label = QLabel("50")
        noise_level_layout.addWidget(self.noise_level_label)
        
        layout.addLayout(noise_layout)
        layout.addLayout(noise_level_layout)
        
        # Accent Conversion
        accent_layout = QHBoxLayout()
        self.accent_checkbox = QCheckBox("Accent Conversion")
        accent_layout.addWidget(self.accent_checkbox)
        layout.addLayout(accent_layout)
        
        accent_target_layout = QHBoxLayout()
        accent_target_layout.addWidget(QLabel("Target Accent:"))
        self.accent_combo = QComboBox()
        self.accent_combo.addItems([
            "American", "British", "Australian", "Indian", 
            "Spanish", "French", "German", "Chinese", "Japanese", "Russian"
        ])
        accent_target_layout.addWidget(self.accent_combo)
        layout.addLayout(accent_target_layout)
        
        # Identity Preservation
        identity_layout = QHBoxLayout()
        self.identity_checkbox = QCheckBox("Preserve Identity")
        self.identity_checkbox.setChecked(True)
        identity_layout.addWidget(self.identity_checkbox)
        layout.addLayout(identity_layout)
        
        # Audio Devices Section
        layout.addWidget(QLabel("<b>Audio Devices</b>"))
        
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Input Device:"))
        self.input_combo = QComboBox()
        self.input_combo.addItems(["Default Input Device", "VB-Audio Virtual Cable"])
        input_layout.addWidget(self.input_combo)
        layout.addLayout(input_layout)
        
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output Device:"))
        self.output_combo = QComboBox()
        self.output_combo.addItems(["Default Output Device", "VB-Audio Virtual Cable"])
        output_layout.addWidget(self.output_combo)
        layout.addLayout(output_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connect signals
        self.noise_slider.valueChanged.connect(self.update_noise_level)
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
    
    def update_noise_level(self, value):
        """Update the noise level label."""
        self.noise_level_label.setText(str(value))
    
    def get_settings(self):
        """Get the current settings from the dialog."""
        return {
            "noise_suppression_enabled": self.noise_checkbox.isChecked(),
            "noise_suppression_level": self.noise_slider.value(),
            "accent_conversion_enabled": self.accent_checkbox.isChecked(),
            "target_accent": self.accent_combo.currentText().lower(),
            "identity_preservation_enabled": self.identity_checkbox.isChecked(),
            "input_device": self.input_combo.currentText(),
            "output_device": self.output_combo.currentText()
        }
    
    def set_settings(self, settings):
        """Update the dialog with the given settings."""
        if "noise_suppression_enabled" in settings:
            self.noise_checkbox.setChecked(settings["noise_suppression_enabled"])
        
        if "noise_suppression_level" in settings:
            self.noise_slider.setValue(settings["noise_suppression_level"])
        
        if "accent_conversion_enabled" in settings:
            self.accent_checkbox.setChecked(settings["accent_conversion_enabled"])
        
        if "target_accent" in settings:
            index = self.accent_combo.findText(settings["target_accent"].capitalize())
            if index >= 0:
                self.accent_combo.setCurrentIndex(index)
        
        if "identity_preservation_enabled" in settings:
            self.identity_checkbox.setChecked(settings["identity_preservation_enabled"])
        
        if "input_device" in settings:
            index = self.input_combo.findText(settings["input_device"])
            if index >= 0:
                self.input_combo.setCurrentIndex(index)
        
        if "output_device" in settings:
            index = self.output_combo.findText(settings["output_device"])
            if index >= 0:
                self.output_combo.setCurrentIndex(index)


class DexentSystemTray:
    """System tray application for Dexent.ai."""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # Create server manager
        self.server_manager = ServerManager()
        self.server_manager.status_changed.connect(self.update_status)
        self.server_manager.start()
        
        # Create tray icon
        self.create_tray_icon()
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
    
    def create_tray_icon(self):
        """Create the system tray icon and menu."""
        # Create icon (should use actual icon file in production)
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setToolTip("Dexent.ai")
        
        # Create tray menu
        tray_menu = QMenu()
        
        # Status indicator (not clickable)
        self.status_action = QAction("Status: Checking...")
        self.status_action.setEnabled(False)
        tray_menu.addAction(self.status_action)
        
        tray_menu.addSeparator()
        
        # Audio Processing toggle
        self.toggle_action = QAction("Start Audio Processing")
        self.toggle_action.triggered.connect(self.toggle_audio_processing)
        tray_menu.addAction(self.toggle_action)
        
        # Open dashboard
        dashboard_action = QAction("Open Dashboard")
        dashboard_action.triggered.connect(self.open_dashboard)
        tray_menu.addAction(dashboard_action)
        
        # Settings
        settings_action = QAction("Settings")
        settings_action.triggered.connect(self.open_settings)
        tray_menu.addAction(settings_action)
        
        tray_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit")
        exit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(exit_action)
        
        # Set the menu
        self.tray_icon.setContextMenu(tray_menu)
        
        # Set initial icon and show
        self.update_status(False)
        self.tray_icon.show()
    
    from PyQt5.QtWidgets import QStyle
from PyQt5.QtWidgets import QStyle

    def update_status(self, is_running):
        """Update the status indicator based on server status."""
        if is_running:
            self.status_action.setText("Status: Server Running")
            # Set green icon (should use actual icon files in production)
            self.tray_icon.setIcon(self.app.style().standardIcon(QStyle.SP_MessageBoxInformation))
            self.toggle_action.setText("Stop Audio Processing")
        else:
            self.status_action.setText("Status: Server Stopped")
            # Set red icon (should use actual icon files in production)
            self.tray_icon.setIcon(self.app.style().standardIcon(QStyle.SP_MessageBoxCritical))
            self.toggle_action.setText("Start Audio Processing")

    def toggle_audio_processing(self):
        """Toggle audio processing on/off."""
        if self.server_manager.is_server_running():
            # Stop audio processing via API call
            try:
                requests.post(f"{SERVER_URL}/api/stop_processing")
                self.toggle_action.setText("Start Audio Processing")
            except requests.ConnectionError:
                logger.error("Could not connect to server to stop audio processing.")
        else:
            # Start server if not running
            if not self.server_manager.running:
                self.server_manager.start_server()
                # Wait for server to start
                time.sleep(2)
            
            # Start audio processing via API call
            try:
                requests.post(f"{SERVER_URL}/api/start_processing")
                self.toggle_action.setText("Stop Audio Processing")
            except requests.ConnectionError:
                logger.error("Could not connect to server to start audio processing.")
    
    def open_dashboard(self):
        """Open the web dashboard."""
        self.server_manager.open_dashboard()
    
    def open_settings(self):
        """Open the settings dialog."""
        # Get current settings from server if available
        settings = {}
        if self.server_manager.is_server_running():
            try:
                response = requests.get(f"{SERVER_URL}/api/settings")
                if response.status_code == 200:
                    settings = response.json()
            except requests.ConnectionError:
                logger.error("Could not connect to server to get settings.")
        
        # Create and show settings dialog
        dialog = SettingsDialog()
        dialog.set_settings(settings)
        
        if dialog.exec_() == QDialog.Accepted:
            # Save settings to server if running
            new_settings = dialog.get_settings()
            if self.server_manager.is_server_running():
                try:
                    requests.post(f"{SERVER_URL}/api/update_settings", json=new_settings)
                except requests.ConnectionError:
                    logger.error("Could not connect to server to update settings.")
    
    def exit_app(self):
        """Exit the application."""
        # Stop server if running
        self.server_manager.stop_server()
        
        # Quit application
        self.app.quit()
    
    def handle_signal(self, signum, frame):
        """Handle interrupt signals."""
        self.exit_app()
    
    def run(self):
        """Run the application event loop."""
        return self.app.exec_()


def main():
    """Main entry point for the system tray application."""
    tray_app = DexentSystemTray()
    sys.exit(tray_app.run())


if __name__ == "__main__":
    main()