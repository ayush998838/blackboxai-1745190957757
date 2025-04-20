"""
Replit-specific entry point for Dexent.ai application.
This file is optimized for Replit's environment and preview feature.
"""

import os
from app import app

# Make sure any web server reference uses 0.0.0.0 for the host
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)