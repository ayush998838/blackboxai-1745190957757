#!/usr/bin/env python
"""
Command-line interface for Dexent.ai.
This script provides command-line utilities for managing the Dexent.ai application.
"""

import os
import sys
import argparse
import subprocess
import time
import webbrowser
import logging
import signal
import requests
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants
DEFAULT_PORT = 5000
SERVER_URL = f"http://localhost:{DEFAULT_PORT}"
SERVER_PROCESS = None

def start_server(debug=False):
    """Start the Flask server."""
    global SERVER_PROCESS
    
    if SERVER_PROCESS:
        logger.warning("Server is already running.")
        return
    
    try:
        # Determine the path to main.py
        main_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
        
        if debug:
            # Start with Flask's built-in development server in debug mode
            cmd = [sys.executable, main_path]
            env = os.environ.copy()
            env["FLASK_ENV"] = "development"
            env["FLASK_DEBUG"] = "1"
        else:
            # Start with Gunicorn for production
            cmd = ["gunicorn", "--bind", f"0.0.0.0:{DEFAULT_PORT}", "--reuse-port", "main:app"]
        
        logger.info(f"Starting server with command: {' '.join(cmd)}")
        
        # Start the server process
        SERVER_PROCESS = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ.copy()
        )
        
        # Wait for server to start
        time.sleep(2)
        logger.info(f"Server started with PID: {SERVER_PROCESS.pid}")
        
        # Check if server is running
        try:
            response = requests.get(f"{SERVER_URL}/")
            if response.status_code == 200:
                logger.info(f"Server is running at {SERVER_URL}")
            else:
                logger.warning(f"Server returned status code: {response.status_code}")
        except requests.ConnectionError:
            logger.warning("Could not connect to server, but process is running.")
        
        return True
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        return False

def stop_server():
    """Stop the Flask server."""
    global SERVER_PROCESS
    
    if not SERVER_PROCESS:
        logger.warning("No server is running.")
        return
    
    try:
        # Try to terminate gracefully
        SERVER_PROCESS.terminate()
        
        # Wait for process to terminate
        try:
            SERVER_PROCESS.wait(timeout=5)
            logger.info("Server stopped gracefully.")
        except subprocess.TimeoutExpired:
            # Force kill if it doesn't terminate
            SERVER_PROCESS.kill()
            logger.info("Server forcefully terminated.")
        
        SERVER_PROCESS = None
        return True
    except Exception as e:
        logger.error(f"Error stopping server: {str(e)}")
        return False

def is_server_running():
    """Check if the server is running."""
    global SERVER_PROCESS
    
    if SERVER_PROCESS:
        # Check if process is still running
        if SERVER_PROCESS.poll() is None:
            try:
                # Try to connect to the server
                response = requests.get(f"{SERVER_URL}/")
                return response.status_code == 200
            except requests.ConnectionError:
                return False
    
    # Check if any server is running on the port
    try:
        response = requests.get(f"{SERVER_URL}/")
        return response.status_code == 200
    except requests.ConnectionError:
        return False

def open_dashboard():
    """Open the web dashboard in the default browser."""
    if not is_server_running():
        logger.warning("Server is not running. Starting server...")
        start_server()
    
    webbrowser.open(f"{SERVER_URL}/")
    logger.info(f"Opening dashboard at {SERVER_URL}")

def setup_environment():
    """Set up the environment for the Dexent.ai application."""
    try:
        # Create required directories
        os.makedirs("uploads", exist_ok=True)
        os.makedirs("processed", exist_ok=True)
        os.makedirs("models", exist_ok=True)
        os.makedirs("instance", exist_ok=True)
        
        logger.info("Environment setup complete.")
        return True
    except Exception as e:
        logger.error(f"Error setting up environment: {str(e)}")
        return False

def handle_shutdown(signum, frame):
    """Handle shutdown signals."""
    logger.info("Shutdown signal received")
    stop_server()
    sys.exit(0)

def main():
    """Main entry point for the CLI."""
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    # Create the parser
    parser = argparse.ArgumentParser(description="Dexent.ai command-line interface")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Start server command
    start_parser = subparsers.add_parser("start", help="Start the Dexent.ai server")
    start_parser.add_argument("--debug", action="store_true", help="Start in debug mode")
    
    # Stop server command
    subparsers.add_parser("stop", help="Stop the Dexent.ai server")
    
    # Status command
    subparsers.add_parser("status", help="Check if the server is running")
    
    # Open dashboard command
    subparsers.add_parser("dashboard", help="Open the web dashboard in the default browser")
    
    # Setup command
    subparsers.add_parser("setup", help="Set up the environment for the Dexent.ai application")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    if args.command == "start":
        start_server(args.debug)
    elif args.command == "stop":
        stop_server()
    elif args.command == "status":
        if is_server_running():
            logger.info("Server is running.")
        else:
            logger.info("Server is not running.")
    elif args.command == "dashboard":
        open_dashboard()
    elif args.command == "setup":
        setup_environment()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()