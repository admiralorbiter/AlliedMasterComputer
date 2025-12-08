# config.py
import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_secret_key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=31)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CSRF protection
    WTF_CSRF_ENABLED = True
    
    # OpenAI configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4-turbo')
    
    # File upload configuration
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')  # Optional, for temporary storage if needed

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///your_database.db'
    SQLALCHEMY_ECHO = True  # Enable SQL query logging in development

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # In-memory database for testing
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_ECHO = False

class ProductionConfig(Config):
    DEBUG = False
    uri = os.environ.get('DATABASE_URL')  # Get the Heroku DATABASE_URL
    if uri and uri.startswith('postgres://'):
        uri = uri.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = uri
    SQLALCHEMY_ECHO = False
    SESSION_COOKIE_SECURE = True  # Secure cookies in production
