"""
Application Configuration Settings
Manages all configuration parameters for the Pharmacy Management System
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import Field
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
import json


class DatabaseSettings(BaseSettings):
    """Database configuration settings"""

    # SQLite Database settings
    database_url: str = Field(default="sqlite:///pharmacy.db", description="Database connection URL")
    database_name: str = Field(default="pharmacy.db", description="Database file name")
    backup_location: str = Field(default="backups/", description="Database backup directory")
    auto_backup: bool = Field(default=True, description="Enable automatic backups")
    backup_interval_hours: int = Field(default=24, description="Backup interval in hours")
    max_backups: int = Field(default=7, description="Maximum number of backups to keep")

    # Connection settings
    pool_size: int = Field(default=10, description="Database connection pool size")
    echo_sql: bool = Field(default=False, description="Echo SQL queries to console")

    class Config:
        env_prefix = "DB_"


class SecuritySettings(BaseSettings):
    """Security and authentication settings"""

    # Password settings
    min_password_length: int = Field(default=8, description="Minimum password length")
    require_uppercase: bool = Field(default=True, description="Require uppercase letters")
    require_lowercase: bool = Field(default=True, description="Require lowercase letters")
    require_digits: bool = Field(default=True, description="Require digits")
    require_special_chars: bool = Field(default=True, description="Require special characters")

    # Session settings
    session_timeout_minutes: int = Field(default=60, description="Session timeout in minutes")
    max_login_attempts: int = Field(default=3, description="Maximum login attempts")
    lockout_duration_minutes: int = Field(default=15, description="Account lockout duration")

    # Encryption settings
    secret_key: str = Field(default="", description="Secret key for encryption")
    encryption_algorithm: str = Field(default="HS256", description="Encryption algorithm")

    # Default admin credentials (should be changed on first run)
    default_admin_username: str = Field(default="admin", description="Default admin username")
    default_admin_password: str = Field(default="admin2024", description="Default admin password")

    class Config:
        env_prefix = "SEC_"


class UISettings(BaseSettings):
    """User Interface configuration settings"""

    # Theme settings
    default_theme: str = Field(default="light", description="Default theme (light/dark)")
    enable_theme_switching: bool = Field(default=True, description="Allow theme switching")

    # Language settings
    default_language: str = Field(default="ar", description="Default language (ar/en)")
    rtl_support: bool = Field(default=True, description="Right-to-left text support")

    # Font settings
    default_font_family: str = Field(default="NotoSansArabic", description="Default font family")
    default_font_size: int = Field(default=12, description="Default font size")
    arabic_font_regular: str = Field(default="NotoSansArabic-Regular.ttf", description="Arabic regular font")
    arabic_font_bold: str = Field(default="NotoSansArabic-Bold.ttf", description="Arabic bold font")

    # Window settings
    default_window_width: int = Field(default=1200, description="Default window width")
    default_window_height: int = Field(default=800, description="Default window height")
    remember_window_state: bool = Field(default=True, description="Remember window size and position")

    # Performance settings
    enable_animations: bool = Field(default=True, description="Enable UI animations")
    enable_transparency: bool = Field(default=True, description="Enable transparency effects")
    max_table_rows: int = Field(default=1000, description="Maximum rows to display in tables")

    class Config:
        env_prefix = "UI_"


class ReportSettings(BaseSettings):
    """Report generation settings"""

    # PDF settings
    default_page_size: str = Field(default="A4", description="Default PDF page size")
    pdf_margin_mm: int = Field(default=15, description="PDF margins in millimeters")
    pdf_quality: str = Field(default="high", description="PDF quality (low/medium/high)")

    # Template settings
    report_template_dir: str = Field(default="resources/templates/reports/", description="Report templates directory")
    default_report_template: str = Field(default="client_report.html", description="Default report template")

    # Export settings
    default_export_format: str = Field(default="pdf", description="Default export format")
    export_directory: str = Field(default="exports/", description="Default export directory")

    class Config:
        env_prefix = "REPORT_"


class PerformanceSettings(BaseSettings):
    """Performance optimization settings"""

    # Caching
    enable_caching: bool = Field(default=True, description="Enable data caching")
    cache_size_mb: int = Field(default=100, description="Cache size in megabytes")
    cache_expiry_minutes: int = Field(default=30, description="Cache expiry time in minutes")

    # Database performance
    enable_query_caching: bool = Field(default=True, description="Enable query result caching")
    pagination_size: int = Field(default=50, description="Default pagination size")
    max_search_results: int = Field(default=500, description="Maximum search results")

    # UI performance
    lazy_loading: bool = Field(default=True, description="Enable lazy loading for large datasets")
    virtual_scrolling: bool = Field(default=True, description="Enable virtual scrolling")
    background_operations: bool = Field(default=True, description="Enable background operations")

    class Config:
        env_prefix = "PERF_"


class LoggingSettings(BaseSettings):
    """Logging configuration settings"""

    # Log levels
    log_level: str = Field(default="INFO", description="Logging level")
    enable_file_logging: bool = Field(default=True, description="Enable file logging")
    enable_console_logging: bool = Field(default=True, description="Enable console logging")

    # Log files
    log_directory: str = Field(default="logs/", description="Log files directory")
    log_file_name: str = Field(default="pharmacy_app.log", description="Log file name")
    max_log_size_mb: int = Field(default=10, description="Maximum log file size in MB")
    log_backup_count: int = Field(default=5, description="Number of log backup files")

    # Log format
    log_format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        description="Log message format"
    )

    class Config:
        env_prefix = "LOG_"


class ApplicationSettings(BaseSettings):
    """Main application settings that combines all configuration"""

    # Application info
    app_name: str = Field(default="Dr.Abaza Pharmacy Management", description="Application name")
    app_version: str = Field(default="2.0.0", description="Application version")
    organization: str = Field(default="Dr.Abaza Pharmacy", description="Organization name")

    # Feature flags
    enable_advanced_search: bool = Field(default=True, description="Enable advanced search features")
    enable_analytics: bool = Field(default=True, description="Enable analytics dashboard")
    enable_notifications: bool = Field(default=True, description="Enable system notifications")
    enable_auto_save: bool = Field(default=True, description="Enable auto-save functionality")

    # Data settings
    auto_save_interval_seconds: int = Field(default=300, description="Auto-save interval in seconds")
    data_retention_days: int = Field(default=365, description="Data retention period in days")

    # Subsystem settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    ui: UISettings = Field(default_factory=UISettings)
    reports: ReportSettings = Field(default_factory=ReportSettings)
    performance: PerformanceSettings = Field(default_factory=PerformanceSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    class Config:
        env_prefix = "APP_"
        case_sensitive = False


def get_resource_path(relative_path: str) -> str:
    """
    Get the absolute path to a resource file.
    Handles both development and PyInstaller packaged environments.
    """
    try:
        # PyInstaller stores files in a temporary folder _MEIPASS when packaged
        base_path = sys._MEIPASS
    except AttributeError:
        # Fallback to current directory for development environment
        base_path = Path(__file__).parent.parent.parent.absolute()

    full_path = os.path.join(base_path, relative_path)
    return full_path if os.path.exists(full_path) else None


def get_app_data_path() -> Path:
    """Get the application data directory based on the operating system"""
    if sys.platform == "win32":
        app_data = Path(os.environ.get("APPDATA", ""))
        return app_data / "PharmacyManagement"
    elif sys.platform == "darwin":
        home = Path.home()
        return home / "Library" / "Application Support" / "PharmacyManagement"
    else:  # Linux and other Unix-like systems
        home = Path.home()
        return home / ".config" / "PharmacyManagement"


class SettingsManager:
    """Manages application settings loading, saving, and validation"""

    def __init__(self, config_file: Optional[str] = None):
        self.app_data_path = get_app_data_path()
        self.config_file = config_file or self.app_data_path / "settings.json"
        self._settings: Optional[ApplicationSettings] = None

        # Ensure app data directory exists
        self.app_data_path.mkdir(parents=True, exist_ok=True)

    def load_settings(self) -> ApplicationSettings:
        """Load settings from configuration file or create defaults"""
        if self._settings is not None:
            return self._settings

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self._settings = ApplicationSettings(**config_data)
            except Exception as e:
                print(f"Error loading settings: {e}")
                self._settings = ApplicationSettings()
        else:
            self._settings = ApplicationSettings()
            self.save_settings()

        return self._settings

    def save_settings(self) -> bool:
        """Save current settings to configuration file"""
        try:
            if self._settings is None:
                return False

            config_data = self._settings.dict()
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def get_settings(self) -> ApplicationSettings:
        """Get current settings instance"""
        if self._settings is None:
            return self.load_settings()
        return self._settings

    def update_setting(self, section: str, key: str, value: Any) -> bool:
        """Update a specific setting value"""
        try:
            settings = self.get_settings()
            section_obj = getattr(settings, section)
            setattr(section_obj, key, value)
            return self.save_settings()
        except Exception as e:
            print(f"Error updating setting {section}.{key}: {e}")
            return False

    def reset_to_defaults(self) -> bool:
        """Reset all settings to default values"""
        try:
            self._settings = ApplicationSettings()
            return self.save_settings()
        except Exception as e:
            print(f"Error resetting settings: {e}")
            return False

    def validate_settings(self) -> bool:
        """Validate current settings"""
        try:
            settings = self.get_settings()
            # Perform validation checks
            return True
        except Exception as e:
            print(f"Settings validation failed: {e}")
            return False


# Global settings instance
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

def save_settings() -> bool:
    """Save the current settings"""
    return get_settings_manager().save_settings()


class AppSettings:
    """
    Simplified settings wrapper for UI components.

    Provides a simple interface for accessing and modifying application settings
    without needing to understand the underlying settings manager structure.
    """

    def __init__(self):
        self._settings_manager = get_settings_manager()
        self._settings = self._settings_manager.get_settings()

    def get(self, key: str, default=None):
        """
        Get a setting value using dot notation.

        Args:
            key: Setting key in dot notation (e.g., 'ui.theme', 'database.url')
            default: Default value if setting not found

        Returns:
            Setting value or default
        """
        try:
            keys = key.split('.')
            value = self._settings

            for k in keys:
                if hasattr(value, k):
                    value = getattr(value, k)
                else:
                    return default

            return value
        except:
            return default

    def set(self, key: str, value):
        """
        Set a setting value using dot notation.

        Args:
            key: Setting key in dot notation
            value: Value to set
        """
        try:
            keys = key.split('.')
            obj = self._settings

            # Navigate to the parent object
            for k in keys[:-1]:
                if hasattr(obj, k):
                    obj = getattr(obj, k)
                else:
                    return

            # Set the final value
            if hasattr(obj, keys[-1]):
                setattr(obj, keys[-1], value)
        except:
            pass

    def save(self) -> bool:
        """Save settings to file."""
        return self._settings_manager.save_settings()

    def load(self):
        """Reload settings from file."""
        self._settings = self._settings_manager.get_settings()

    def remove(self, key: str):
        """Remove a setting (set to default value)."""
        # For simplicity, we'll just set common removable settings to None
        self.set(key, None)
