#!/usr/bin/env python3
"""
TurboRisk Web Application - Run Script
Starts the Flask development server for the TurboRisk web app.

Usage:
    python run.py                    # Run on default port 5000
    python run.py --port 5001        # Run on port 5001
    python run.py -p 5001           # Run on port 5001 (short form)
"""

import argparse
import os
import sys

# Add the parent directory to the path to import turborisk modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webapp import app

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run TurboRisk Web Application')
    parser.add_argument('--port', '-p', type=int, default=5000,
                        help='Port to run the server on (default: 5000)')
    parser.add_argument('--host', '-H', type=str, default='0.0.0.0',
                        help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Enable debug mode')
    args = parser.parse_args()
    
    # Set the app path for the game
    from turborisk.globals import G
    G.s_g_app_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Run the Flask app
    print(f"Starting TurboRisk Web App on http://{args.host}:{args.port}")
    app.run(debug=args.debug, host=args.host, port=args.port)
