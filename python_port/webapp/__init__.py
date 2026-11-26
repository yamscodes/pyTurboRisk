"""
TurboRisk Web Application
A Flask-based web interface for the TurboRisk game.
"""

from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = 'turborisk-secret-key-change-in-production'

# Import routes after app is created to avoid circular imports
from . import routes
