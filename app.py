"""
Keyword Batch Processing Application
Main application entry point
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import Config


def main():
    """Main application entry point"""
    print("Starting Keyword Batch Processing Application...")
    print(f"Project root: {project_root}")
    print(f"Config loaded: {Config.DEBUG}")
    
    # TODO: Implement application logic
    print("Application initialized successfully!")


if __name__ == "__main__":
    main()