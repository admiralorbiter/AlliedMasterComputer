# app/routes/__init__.py
"""
Application routes package
"""

from .main import register_main_routes
from .auth import register_auth_routes
from .admin import register_admin_routes
from .research import register_research_routes
from .todo import register_todo_routes

def init_routes(app):
    """Initialize all application routes"""
    register_main_routes(app)
    register_auth_routes(app)
    register_admin_routes(app)
    register_research_routes(app)
    register_todo_routes(app)