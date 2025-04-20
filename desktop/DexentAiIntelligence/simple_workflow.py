import subprocess
import sys
import os
import time
import signal

def run_simple_app():
    print("Starting simple Flask app...")
    try:
        # Run the simple Flask app with gunicorn
        process = subprocess.Popen(
            ["gunicorn", "--bind", "0.0.0.0:5001", "simple_app:app"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment for the server to start
        time.sleep(2)
        
        # Test local connectivity
        test_process = subprocess.run(
            ["curl", "http://0.0.0.0:5001/api/ping"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print("Local ping test result:")
        print(test_process.stdout)
        
        # Keep the server running until interrupted
        try:
            while True:
                # Print server output
                stdout_line = process.stdout.readline()
                if stdout_line:
                    print(stdout_line, end='')
                stderr_line = process.stderr.readline()
                if stderr_line:
                    print(stderr_line, end='', file=sys.stderr)
                
                # Check if process is still running
                if process.poll() is not None:
                    break
                
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Stopping simple Flask app...")
            process.terminate()
            process.wait()
    except Exception as e:
        print(f"Error running simple Flask app: {e}")

if __name__ == "__main__":
    run_simple_app()