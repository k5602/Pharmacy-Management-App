"""
Simple Application Configuration Settings
Manages all configuration parameters for the Pharmacy Management System without pydantic dependency
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List


class DatabaseSettings:
    """Database configuration settings"""

    def __init__(self):
        self.database_url = "sqlite:///pharmacy.db"
        self.database_name = "pharmacy.db"
        self.backup_location = "backups/"
        self.auto_backup = True
        self.backup_interval_hours = 24
        self.max_backups = 7
        self.pool_size = 10
        self.echo_sql = False


class SecuritySettings:
    """Security and authentication settings"""

    def __init__(self):
        self.min_password_length = 8
        self.require_uppercase = True
        self.require_lowercase = True
        self.require_digits = True
        self.require_special_chars = True
        self.session_timeout_minutes = 60
        self.max_login_attempts = 3
        self.lockout_duration_minutes = 15
        self.jwt_secret = "your-secret-key-change-in-production"
        self.session_timeout_hours = 8
        self.lockout_duration_minutes = 30


class UISettings:
    """User interface settings"""

    def __init__(self):
        self.theme = "default"
        self.language = "ar"
        self.default_font_family = "Arial"
        self.default_font_size = 12
        self.enable_animations = True
        self.show_splash_screen = True
        self.remember_window_state = True
        self.auto_save_interval = 300
        self.enable_tooltips = True


class LoggingSettings:
    """Logging configuration settings"""

    def __init__(self):
        self.log_level = "INFO"
        self.log_format = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
        self.enable_console_logging = True
        self.enable_file_logging = True
        self.log_directory = "logs"
        self.log_file_name = "pharmacy_management.log"
        self.max_log_size_mb = 10
        self.log_backup_count = 5


class ReportSettings:
    """Report generation settings"""

    def __init__(self):
        self.default_format = "PDF"
        self.output_directory = "reports"
        self.template_directory = "templates"
        self.include_logo = True
        self.auto_open_reports = True
        self.compression_level = 6
        self.page_size = "A4"
        self.page_orientation = "portrait"


class ApplicationSettings:
    """Main application settings container"""

    def __init__(self):
        self.app_name = "Pharmacy Management System"
        self.app_version = "2.0.0"
        self.organization = "Dr.Abaza Pharmacy"

        # Initialize sub-settings
        self.database = DatabaseSettings()
        self.security = SecuritySettings()
        self.ui = UISettings()
        self.logging = LoggingSettings()
        self.reports = ReportSettings()

        # Development settings
        self.debug_mode = False
        self.development_mode = False
        self.enable_profiling = False

        # Load settings from file if it exists
        self._load_from_file()

    def _load_from_file(self):
        """Load settings from configuration file"""
        try:
            config_file = Path("config/settings.json")
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self._update_from_dict(config_data)
        except Exception as e:
            print(f"Warning: Could not load settings from file: {e}")

    def _update_from_dict(self, config_data: Dict[str, Any]):
        """Update settings from dictionary"""
        for section_name, section_data in config_data.items():
            if hasattr(self, section_name):
                section = getattr(self, section_name)
                for key, value in section_data.items():
                    if hasattr(section, key):
                        setattr(section, key, value)

    def save_to_file(self, file_path: Optional[str] = None):
        """Save current settings to file"""
        try:
            if file_path is None:
                config_dir = Path("config")
                config_dir.mkdir(exist_ok=True)
                file_path = config_dir / "settings.json"

            settings_dict = self.to_dict()

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(settings_dict, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Error saving settings: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary"""
        return {
            "database": self._section_to_dict(self.database),
            "security": self._section_to_dict(self.security),
            "ui": self._section_to_dict(self.ui),
            "logging": self._section_to_dict(self.logging),
            "reports": self._section_to_dict(self.reports),
            "app_name": self.app_name,
            "app_version": self.app_version,
            "organization": self.organization,
            "debug_mode": self.debug_mode,
            "development_mode": self.development_mode,
            "enable_profiling": self.enable_profiling
        }

    def _section_to_dict(self, section) -> Dict[str, Any]:
        """Convert settings section to dictionary"""
        return {
            key: value for key, value in section.__dict__.items()
            if not key.startswith('_')
        }


class SettingsManager:
    """Manager for application settings"""

    def __init__(self):
        self.settings = ApplicationSettings()
        self._callbacks = {}

    def get_settings(self) -> ApplicationSettings:
        """Get current application settings"""
        return self.settings

    def load_settings(self, file_path: Optional[str] = None) -> ApplicationSettings:
        """Load settings from file"""
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self.settings._update_from_dict(config_data)
            except Exception as e:
                print(f"Error loading settings from {file_path}: {e}")

        return self.settings

    def save_settings(self, file_path: Optional[str] = None):
        """Save current settings to file"""
        self.settings.save_to_file(file_path)

    def update_setting(self, section: str, key: str, value: Any) -> bool:
        """Update a specific setting"""
        try:
            if hasattr(self.settings, section):
                section_obj = getattr(self.settings, section)
                if hasattr(section_obj, key):
                    setattr(section_obj, key, value)

                    # Trigger callbacks
                    callback_key = f"{section}.{key}"
                    if callback_key in self._callbacks:
                        for callback in self._callbacks[callback_key]:
                            try:
                                callback(value)
                            except Exception as e:
                                print(f"Error in settings callback: {e}")

                    return True

            return False

        except Exception as e:
            print(f"Error updating setting {section}.{key}: {e}")
            return False

    def get_setting(self, section: str, key: str, default: Any = None) -> Any:
        """Get a specific setting value"""
        try:
            if hasattr(self.settings, section):
                section_obj = getattr(self.settings, section)
                if hasattr(section_obj, key):
                    return getattr(section_obj, key)

            return default

        except Exception as e:
            print(f"Error getting setting {section}.{key}: {e}")
            return default

    def register_callback(self, section: str, key: str, callback):
        """Register callback for setting changes"""
        callback_key = f"{section}.{key}"
        if callback_key not in self._callbacks:
            self._callbacks[callback_key] = []
        self._callbacks[callback_key].append(callback)

    def validate_settings(self) -> Dict[str, List[str]]:
        """Validate current settings and return any errors"""
        errors = {}

        # Validate database settings
        db_errors = []
        if not self.settings.database.database_url:
            db_errors.append("Database URL is required")
        if self.settings.database.pool_size < 1:
            db_errors.append("Pool size must be at least 1")
        if self.settings.database.backup_interval_hours < 1:
            db_errors.append("Backup interval must be at least 1 hour")

        if db_errors:
            errors["database"] = db_errors

        # Validate security settings
        security_errors = []
        if self.settings.security.min_password_length < 4:
            security_errors.append("Minimum password length must be at least 4")
        if self.settings.security.session_timeout_minutes < 1:
            security_errors.append("Session timeout must be at least 1 minute")
        if self.settings.security.max_login_attempts < 1:
            security_errors.append("Max login attempts must be at least 1")

        if security_errors:
            errors["security"] = security_errors

        # Validate logging settings
        logging_errors = []
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.settings.logging.log_level not in valid_log_levels:
            logging_errors.append(f"Log level must be one of: {', '.join(valid_log_levels)}")
        if self.settings.logging.max_log_size_mb < 1:
            logging_errors.append("Max log size must be at least 1 MB")

        if logging_errors:
            errors["logging"] = logging_errors

        return errors


# Global settings manager instance
_settings_manager = None

def get_settings_manager() -> SettingsManager:
    """Get the global settings manager instance"""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager

def get_settings() -> ApplicationSettings:
    """Get the current application settings"""
    return get_settings_manager().get_settings()

def update_setting(section: str, key: str, value: Any) -> bool:
    """Update a specific setting"""
    return get_settings_manager().update_setting(section, key, value)

def get_setting(section: str, key: str, default: Any = None) -> Any:
    """Get a specific setting value"""
    return get_settings_manager().get_setting(section, key, default)
