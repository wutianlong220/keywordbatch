"""
Configuration settings for Keyword Batch Processing Application
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration class"""
    
    # Project paths
    PROJECT_ROOT = Path(__file__).parent
    TEMPLATES_DIR = PROJECT_ROOT / "templates"
    STATIC_DIR = PROJECT_ROOT / "static"
    SERVICES_DIR = PROJECT_ROOT / "services"
    UTILS_DIR = PROJECT_ROOT / "utils"
    TESTS_DIR = PROJECT_ROOT / "tests"
    
    # Application settings
    DEBUG = True  # Enable debug mode for development
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5001"))
    
    # File upload settings
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {'.xlsx', '.xls', '.csv'}
    
    # API Configuration
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
    
    # Processing settings
    BATCH_SIZE = 500  # Fixed batch size for processing
    MAX_CONCURRENT_REQUESTS = 1  # Simple sequential processing
    
    @classmethod
    def init(cls):
        """Initialize configuration and create necessary directories"""
        cls._ensure_directories()
        cls._validate_config()
    
    @classmethod
    def _ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        directories = [
            cls.TEMPLATES_DIR,
            cls.STATIC_DIR,
            cls.SERVICES_DIR,
            cls.UTILS_DIR,
            cls.TESTS_DIR,
            cls.STATIC_DIR / "css",
            cls.STATIC_DIR / "js",
            cls.STATIC_DIR / "images"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Directory ensured: {directory}")
    
    @classmethod
    def _validate_config(cls):
        """Validate configuration settings"""
        if not cls.DEEPSEEK_API_KEY:
            print("Warning: DEEPSEEK_API_KEY not set in environment variables")
        
        print(f"Configuration validated (DEBUG={cls.DEBUG})")