import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # General
    APP_ENV = os.getenv('APP_ENV', 'development')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///shiptrack.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Uploads
    MAX_UPLOAD_SIZE_MB = int(os.getenv('MAX_UPLOAD_SIZE_MB', '16'))
    MAX_CONTENT_LENGTH = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), os.getenv('UPLOAD_FOLDER', 'uploads'))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Tracking
    TRACKING_PROVIDER = os.getenv('TRACKING_PROVIDER', 'mock')
    TRACKING_DEMO_MODE = os.getenv('TRACKING_DEMO_MODE', 'true').lower() == 'true'
    
    # OCR
    OCR_ENGINE = os.getenv('OCR_ENGINE', 'easyocr')
    OCR_DEMO_MODE = os.getenv('OCR_DEMO_MODE', 'true').lower() == 'true'
    
    # AI
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'mock')
    AI_API_KEY = os.getenv('AI_API_KEY', '')
    AI_MODEL = os.getenv('AI_MODEL', 'gpt-3.5-turbo')
    AI_BASE_URL = os.getenv('AI_BASE_URL', '')
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    # WhatsApp
    WHATSAPP_ENABLED = os.getenv('WHATSAPP_ENABLED', 'false').lower() == 'true'
    WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN', '')
    WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '')
    WHATSAPP_BUSINESS_ACCOUNT_ID = os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID', '')
    WHATSAPP_RECIPIENT_NUMBER = os.getenv('WHATSAPP_RECIPIENT_NUMBER', '')
    
    # Email
    EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
    SMTP_HOST = os.getenv('SMTP_HOST', '')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    EMAIL_FROM = os.getenv('EMAIL_FROM', '')
    
    # Scheduler
    SCHEDULER_ENABLED = os.getenv('SCHEDULER_ENABLED', 'false').lower() == 'true'
    REFRESH_INTERVAL_MINUTES = int(os.getenv('REFRESH_INTERVAL_MINUTES', '60'))

class DevelopmentConfig(Config):
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = 'production'

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    TRACKING_DEMO_MODE = True
    WTF_CSRF_ENABLED = False

config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
