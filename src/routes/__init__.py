from flask import Blueprint

# Create a blueprint for the routes
routes = Blueprint('routes', __name__)

# Import all route modules
from .auth import auth_bp
from .research import research_bp
from .user import user_bp

# Export the blueprints
__all__ = ['auth_bp', 'research_bp', 'user_bp']
