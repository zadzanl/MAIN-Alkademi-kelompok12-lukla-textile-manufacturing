"""
API Routes Package untuk SAMPLING & SPEC R&D Module

Import semua blueprints di sini agar mudah di-register di main app
"""

from .time_study_routes import time_study_bp
from .spec_version_routes import spec_bp

__all__ = ['time_study_bp', 'spec_bp']


def register_blueprints(app):
    """
    Register semua API blueprints ke Flask app
    
    Usage:
        from flask import Flask
        from backend.api import register_blueprints
        
        app = Flask(__name__)
        register_blueprints(app)
    """
    app.register_blueprint(time_study_bp)
    app.register_blueprint(spec_bp)
