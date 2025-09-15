"""
Configuration Management System
Handles configuration saving, loading, and import/export
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class AppConfig:
    """Application configuration data class"""
    # API Configuration
    deepseek_api_key: str = ""
    deepseek_api_base: str = "https://api.deepseek.com/v1"

    # Processing Configuration
    batch_size: int = 500
    translate_keywords: bool = True
    target_language: str = "Chinese"

    # Interface Configuration
    theme: str = "light"  # light, dark, auto
    auto_scroll_logs: bool = True
    show_notifications: bool = True
    log_level: str = "info"

    # File Processing
    supported_extensions: list = None
    output_filename_pattern: str = "processed_{original_name}"

    # Performance
    max_concurrent_jobs: int = 3
    memory_limit_mb: int = 512

    # Advanced
    enable_debug_mode: bool = False
    log_retention_days: int = 30
    auto_backup: bool = True

    def __post_init__(self):
        if self.supported_extensions is None:
            self.supported_extensions = ['.xlsx', '.xls', '.csv']

class ConfigManager:
    """Configuration management system"""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "app_config.json"
        self.backup_dir = self.config_dir / "backups"
        self.current_config = AppConfig()

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Create directories
        self.config_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)

        # Load existing configuration
        self.load_config()

    def load_config(self) -> bool:
        """
        Load configuration from file

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                # Update configuration
                for key, value in config_data.items():
                    if hasattr(self.current_config, key):
                        setattr(self.current_config, key, value)

                self.logger.info("Configuration loaded successfully")
                return True
            else:
                self.logger.info("No existing configuration found, using defaults")
                return False

        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return False

    def save_config(self) -> bool:
        """
        Save current configuration to file

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Create backup if enabled
            if self.current_config.auto_backup and self.config_file.exists():
                self.create_backup()

            # Save configuration
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.current_config), f, indent=2, ensure_ascii=False)

            self.logger.info("Configuration saved successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False

    def get_config(self) -> AppConfig:
        """
        Get current configuration

        Returns:
            Current configuration object
        """
        return self.current_config

    def update_config(self, **kwargs) -> bool:
        """
        Update configuration with new values

        Args:
            **kwargs: Configuration key-value pairs

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            for key, value in kwargs.items():
                if hasattr(self.current_config, key):
                    setattr(self.current_config, key, value)
                    self.logger.debug(f"Updated config: {key} = {value}")
                else:
                    self.logger.warning(f"Unknown configuration key: {key}")

            return self.save_config()

        except Exception as e:
            self.logger.error(f"Failed to update configuration: {e}")
            return False

    def reset_config(self) -> bool:
        """
        Reset configuration to defaults

        Returns:
            True if reset successfully, False otherwise
        """
        try:
            self.current_config = AppConfig()
            return self.save_config()

        except Exception as e:
            self.logger.error(f"Failed to reset configuration: {e}")
            return False

    def create_backup(self) -> bool:
        """
        Create backup of current configuration

        Returns:
            True if backup created successfully, False otherwise
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"config_backup_{timestamp}.json"

            # Copy current config to backup
            with open(self.config_file, 'r', encoding='utf-8') as src:
                with open(backup_file, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())

            self.logger.info(f"Configuration backup created: {backup_file}")

            # Clean old backups
            self.clean_old_backups()

            return True

        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return False

    def clean_old_backups(self, retention_days: int = 30):
        """
        Clean old backup files

        Args:
            retention_days: Number of days to keep backups
        """
        try:
            import time

            cutoff_time = time.time() - (retention_days * 24 * 60 * 60)

            for backup_file in self.backup_dir.glob("config_backup_*.json"):
                if backup_file.stat().st_mtime < cutoff_time:
                    backup_file.unlink()
                    self.logger.info(f"Deleted old backup: {backup_file}")

        except Exception as e:
            self.logger.error(f"Failed to clean old backups: {e}")

    def export_config(self, filename: str, format: str = 'json') -> bool:
        """
        Export configuration to file

        Args:
            filename: Export filename
            format: Export format ('json', 'env')

        Returns:
            True if exported successfully, False otherwise
        """
        try:
            export_path = Path(filename)

            if format.lower() == 'json':
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(asdict(self.current_config), f, indent=2, ensure_ascii=False)

            elif format.lower() == 'env':
                with open(export_path, 'w', encoding='utf-8') as f:
                    f.write("# Keyword Batch Processing Configuration\n")
                    f.write(f"# Generated on {datetime.now().isoformat()}\n\n")

                    for key, value in asdict(self.current_config).items():
                        if isinstance(value, str):
                            f.write(f"{key.upper()}=\"{value}\"\n")
                        elif isinstance(value, bool):
                            f.write(f"{key.upper()}={str(value).lower()}\n")
                        elif isinstance(value, (int, float)):
                            f.write(f"{key.upper()}={value}\n")
                        elif isinstance(value, list):
                            f.write(f"{key.upper()}={','.join(map(str, value))}\n")

            else:
                raise ValueError(f"Unsupported export format: {format}")

            self.logger.info(f"Configuration exported to: {export_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export configuration: {e}")
            return False

    def import_config(self, filename: str) -> bool:
        """
        Import configuration from file

        Args:
            filename: Import filename

        Returns:
            True if imported successfully, False otherwise
        """
        try:
            import_path = Path(filename)

            if not import_path.exists():
                self.logger.error(f"Import file not found: {import_path}")
                return False

            with open(import_path, 'r', encoding='utf-8') as f:
                if import_path.suffix.lower() == '.json':
                    config_data = json.load(f)
                elif import_path.suffix.lower() == '.env':
                    config_data = self.parse_env_file(f.read())
                else:
                    raise ValueError(f"Unsupported import format: {import_path.suffix}")

            # Update configuration
            for key, value in config_data.items():
                if hasattr(self.current_config, key):
                    setattr(self.current_config, key, value)

            # Save imported configuration
            if self.save_config():
                self.logger.info(f"Configuration imported from: {import_path}")
                return True
            else:
                return False

        except Exception as e:
            self.logger.error(f"Failed to import configuration: {e}")
            return False

    def parse_env_file(self, content: str) -> Dict[str, Any]:
        """
        Parse .env file content

        Args:
            content: .env file content

        Returns:
            Configuration dictionary
        """
        config = {}

        for line in content.split('\n'):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Parse key-value pairs
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip().lower()
                value = value.strip().strip('"\'')

                # Convert value types
                if value.lower() in ('true', 'false'):
                    config[key] = value.lower() == 'true'
                elif value.isdigit():
                    config[key] = int(value)
                elif value.replace('.', '').isdigit():
                    config[key] = float(value)
                elif ',' in value:
                    config[key] = [item.strip() for item in value.split(',')]
                else:
                    config[key] = value

        return config

    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get configuration summary for display

        Returns:
            Configuration summary
        """
        config_dict = asdict(self.current_config)

        # Mask sensitive information
        if config_dict.get('deepseek_api_key'):
            config_dict['deepseek_api_key'] = '***masked***'

        return {
            'config': config_dict,
            'config_file': str(self.config_file),
            'config_exists': self.config_file.exists(),
            'backup_count': len(list(self.backup_dir.glob("config_backup_*.json"))),
            'last_modified': datetime.fromtimestamp(self.config_file.stat().st_mtime).isoformat() if self.config_file.exists() else None
        }

    def validate_config(self) -> Dict[str, Any]:
        """
        Validate current configuration

        Returns:
            Validation result
        """
        errors = []
        warnings = []

        # Validate API configuration
        if not self.current_config.deepseek_api_key:
            warnings.append("DeepSeek API key not configured")

        # Validate processing configuration
        if self.current_config.batch_size < 1 or self.current_config.batch_size > 10000:
            errors.append("Batch size must be between 1 and 10000")

        if self.current_config.max_concurrent_jobs < 1 or self.current_config.max_concurrent_jobs > 10:
            errors.append("Max concurrent jobs must be between 1 and 10")

        # Validate file extensions
        if not self.current_config.supported_extensions:
            errors.append("At least one file extension must be supported")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

# Global configuration manager instance
config_manager = ConfigManager()