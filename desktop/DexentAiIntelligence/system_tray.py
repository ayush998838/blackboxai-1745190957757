import sys
import os
import logging
import threading
import requests
import webbrowser
from pathlib import Path
import signal
from PyQt5.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QAction, 
    QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, 
    QLabel, QComboBox, QCheckBox, QPushButton
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

logger = logging.getLogger(__name__)

# Flask server management
class ServerManager(QObject):
    status_changed = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.process = None
        self.server_url = "http://localhost:5000"
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_server_status)
        self.timer.start(5000)  # Check every 5 seconds
        self.running = False
    
    def start_server(self):
        """Start the Flask server in a subprocess."""
        if self.is_server_running():
            logger.info("Server is already running")
            return
        
        try:
            # Start the Flask app in a separate Python process
            # Using the Python executable that's running this script
            from subprocess import Popen
            import sys
            
            python_exec = sys.executable
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
            
            # Start the process
            self.process = Popen([python_exec, script_path])
            
            logger.info(f"Started Flask server (PID: {self.process.pid})")
            self.running = True
            self.status_changed.emit(True)
            
        except Exception as e:
            logger.error(f"Error starting Flask server: {str(e)}")
            self.running = False
            self.status_changed.emit(False)
    
    def stop_server(self):
        """Stop the Flask server."""
        if self.process:
            try:
                # Try to terminate gracefully
                self.process.terminate()
                self.process.wait(timeout=5)
                logger.info("Flask server stopped")
            except Exception as e:
                logger.error(f"Error stopping Flask server: {str(e)}")
                # If it didn't terminate, force kill
                try:
                    self.process.kill()
                except:
                    pass
            
            self.process = None
            self.running = False
            self.status_changed.emit(False)
    
    def is_server_running(self):
        """Check if the Flask server is running."""
        if self.process and self.process.poll() is None:
            # Process exists and has not terminated
            return True
        
        # Try to connect to the server
        try:
            response = requests.get(f"{self.server_url}/api/status", timeout=1)
            if response.status_code == 200:
                return True
        except:
            pass
            
        return False
    
    def check_server_status(self):
        """Periodically check server status and emit signal if changed."""
        running = self.is_server_running()
        if running != self.running:
            self.running = running
            self.status_changed.emit(running)
    
    def open_dashboard(self):
        """Open the web dashboard in the default browser."""
        webbrowser.open(self.server_url)

# Settings Dialog
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dexent.ai Settings")
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Accent settings
        accent_layout = QHBoxLayout()
        accent_layout.addWidget(QLabel("Target Accent:"))
        self.accent_combo = QComboBox()
        self.accent_combo.addItems(["American", "British", "Australian", "Indian"])
        accent_layout.addWidget(self.accent_combo)
        layout.addLayout(accent_layout)
        
        # Feature toggles
        self.noise_suppression_cb = QCheckBox("Enable Noise Suppression")
        self.noise_suppression_cb.setChecked(True)
        layout.addWidget(self.noise_suppression_cb)
        
        self.accent_conversion_cb = QCheckBox("Enable Accent Conversion")
        layout.addWidget(self.accent_conversion_cb)
        
        self.identity_preservation_cb = QCheckBox("Preserve Speaker Identity")
        self.identity_preservation_cb.setChecked(True)
        layout.addWidget(self.identity_preservation_cb)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def get_settings(self):
        """Get the current settings from the dialog."""
        return {
            "target_accent": self.accent_combo.currentText().lower(),
            "noise_suppression": self.noise_suppression_cb.isChecked(),
            "accent_conversion": self.accent_conversion_cb.isChecked(),
            "identity_preservation": self.identity_preservation_cb.isChecked()
        }
    
    def set_settings(self, settings):
        """Update the dialog with the given settings."""
        if "target_accent" in settings:
            index = self.accent_combo.findText(settings["target_accent"].capitalize())
            if index >= 0:
                self.accent_combo.setCurrentIndex(index)
        
        if "noise_suppression" in settings:
            self.noise_suppression_cb.setChecked(settings["noise_suppression"])
        
        if "accent_conversion" in settings:
            self.accent_conversion_cb.setChecked(settings["accent_conversion"])
        
        if "identity_preservation" in settings:
            self.identity_preservation_cb.setChecked(settings["identity_preservation"])

# System Tray Application
class DexentSystemTray:
    def __init__(self):
        self.app = QApplication(sys.argv)
        
        # Set application name and organization
        self.app.setApplicationName("Dexent.ai")
        self.app.setApplicationVersion("1.0.0")
        
        # Check if system tray is available
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(None, "Dexent.ai", "System tray is not available on this system")
            sys.exit(1)
        
        # Create the system tray icon
        self.create_tray_icon()
        
        # Initialize the server manager
        self.server_manager = ServerManager()
        self.server_manager.status_changed.connect(self.update_status)
        
        # Start the Flask server
        self.server_manager.start_server()
        
        # Default settings
        self.settings = {
            "target_accent": "american",
            "noise_suppression": True,
            "accent_conversion": False,
            "identity_preservation": True
        }
        
        # Audio processing state
        self.audio_processing = False
        
        # Start application
        logger.info("Dexent.ai system tray application started")
    
    def create_tray_icon(self):
        """Create the system tray icon and menu."""
        # Create the system tray icon
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setToolTip("Dexent.ai")
        
        # Use a default icon or load an SVG icon
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static/assets/logo.svg")
            if os.path.exists(icon_path):
                self.tray_icon.setIcon(QIcon(icon_path))
            else:
                # Use a fallback icon
                self.tray_icon.setIcon(QIcon.fromTheme("audio-input-microphone"))
        except Exception as e:
            logger.error(f"Error setting tray icon: {str(e)}")
            # Fallback to a system icon
            self.tray_icon.setIcon(QIcon.fromTheme("audio-input-microphone"))
        
        # Create the menu
        self.menu = QMenu()
        
        # Status indicator (not clickable)
        self.status_action = QAction("Status: Not Running")
        self.status_action.setEnabled(False)
        self.menu.addAction(self.status_action)
        
        self.menu.addSeparator()
        
        # Start/Stop audio processing
        self.toggle_action = QAction("Start Audio Processing")
        self.toggle_action.triggered.connect(self.toggle_audio_processing)
        self.menu.addAction(self.toggle_action)
        
        # Open dashboard
        self.dashboard_action = QAction("Open Dashboard")
        self.dashboard_action.triggered.connect(self.open_dashboard)
        self.menu.addAction(self.dashboard_action)
        
        # Settings
        self.settings_action = QAction("Settings")
        self.settings_action.triggered.connect(self.open_settings)
        self.menu.addAction(self.settings_action)
        
        self.menu.addSeparator()
        
        # Exit action
        self.exit_action = QAction("Exit")
        self.exit_action.triggered.connect(self.exit_app)
        self.menu.addAction(self.exit_action)
        
        # Set the context menu
        self.tray_icon.setContextMenu(self.menu)
        
        # Show the tray icon
        self.tray_icon.show()
    
    def update_status(self, is_running):
        """Update the status indicator based on server status."""
        if is_running:
            self.status_action.setText("Status: Server Running")
            self.dashboard_action.setEnabled(True)
        else:
            self.status_action.setText("Status: Server Not Running")
            self.dashboard_action.setEnabled(False)
    
    def toggle_audio_processing(self):
        """Toggle audio processing on/off."""
        if not self.server_manager.is_server_running():
            QMessageBox.warning(None, "Dexent.ai", "Server is not running. Cannot start audio processing.")
            return
        
        try:
            if self.audio_processing:
                # Stop audio processing
                response = requests.post("http://localhost:5000/api/stop_processing")
                if response.status_code == 200:
                    self.audio_processing = False
                    self.toggle_action.setText("Start Audio Processing")
                    logger.info("Audio processing stopped")
                else:
                    QMessageBox.warning(None, "Dexent.ai", "Failed to stop audio processing")
            else:
                # Start audio processing
                response = requests.post("http://localhost:5000/api/start_processing")
                if response.status_code == 200:
                    self.audio_processing = True
                    self.toggle_action.setText("Stop Audio Processing")
                    logger.info("Audio processing started")
                else:
                    QMessageBox.warning(None, "Dexent.ai", "Failed to start audio processing")
        except Exception as e:
            logger.error(f"Error toggling audio processing: {str(e)}")
            QMessageBox.warning(None, "Dexent.ai", f"Error: {str(e)}")
    
    def open_dashboard(self):
        """Open the web dashboard."""
        self.server_manager.open_dashboard()
    
    def open_settings(self):
        """Open the settings dialog."""
        dialog = SettingsDialog()
        dialog.set_settings(self.settings)
        
        if dialog.exec_():
            # User clicked Save
            new_settings = dialog.get_settings()
            self.settings = new_settings
            
            # Update settings on the server if it's running
            if self.server_manager.is_server_running():
                try:
                    # In a real implementation, this would send the settings to the server
                    # For now, just log the settings
                    logger.info(f"Settings updated: {new_settings}")
                except Exception as e:
                    logger.error(f"Error updating settings: {str(e)}")
    
    def exit_app(self):
        """Exit the application."""
        # Stop audio processing if running
        if self.audio_processing:
            try:
                requests.post("http://localhost:5000/api/stop_processing")
            except:
                pass
        
        # Stop the server
        self.server_manager.stop_server()
        
        # Exit the application
        self.tray_icon.hide()
        self.app.quit()
    
    def run(self):
        """Run the application event loop."""
        # Handle Ctrl+C gracefully
        signal.signal(signal.SIGINT, self.handle_signal)
        
        sys.exit(self.app.exec_())
    
    def handle_signal(self, signum, frame):
        """Handle interrupt signals."""
        logger.info(f"Received signal {signum}, exiting")
        self.exit_app()

def main():
    """Main entry point for the system tray application."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run the system tray application
    app = DexentSystemTray()
    app.run()

if __name__ == "__main__":
    main()
