
"""
Routes package initialization
Contains all Flask blueprint routes for the FeelSync application
"""

from flask import Blueprint

# Import all blueprints
from .auth import auth_bp
from .games import games_bp  
from .analysis import analysis_bp
from .dashboard import dashboard_bp

# List of all blueprints to be registered
BLUEPRINTS = [
    auth_bp,
    games_bp,
    analysis_bp, 
    dashboard_bp
]

def register_blueprints(app):
    """
    Register all blueprints with the Flask application
    
    Args:
        app: Flask application instance
    """
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)
    
    # Log registered blueprints
    app.logger.info(f"Registered {len(BLUEPRINTS)} blueprints: {[bp.name for bp in BLUEPRINTS]}")

__all__ = ['BLUEPRINTS', 'register_blueprints', 'auth_bp', 'games_bp', 'analysis_bp', 'dashboard_bp']
