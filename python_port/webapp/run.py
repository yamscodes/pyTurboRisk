#!/usr/bin/env python3
"""
TurboRisk Web Application - Run Script
Starts the Flask development server for the TurboRisk web app.
"""

import os
import sys

# Add the parent directory to the path to import turborisk modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webapp import app

if __name__ == '__main__':
    # Set the app path for the game
    from turborisk.globals import G
    G.s_g_app_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
