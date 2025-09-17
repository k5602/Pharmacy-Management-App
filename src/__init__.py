"""
Pharmacy Management System v2.0
A comprehensive pharmacy management application with nutrition tracking capabilities.

This package provides:
- Client management with comprehensive health tracking
- Diet and nutrition planning with BMI calculations
- Rich text notes and documentation
- PDF report generation with Arabic support
- Modern PyQt6 interface with MVC architecture
- SQLAlchemy-based database management
- User authentication and security features
"""

__version__ = "2.0.0"
__author__ = "Khaled Alam"
__email__ = "khaled.alam5602@gmail.com"
__description__ = "Modern pharmacy management system with nutrition tracking"

# Package information
PACKAGE_NAME = "pharmacy_management"
DATABASE_VERSION = "2.0"
CONFIG_VERSION = "1.0"

# Supported features
FEATURES = [
    "client_management",
    "diet_tracking",
    "bmi_calculation",
    "meal_planning",
    "rich_text_notes",
    "pdf_reports",
    "arabic_support",
    "user_authentication",
    "data_backup",
    "analytics_dashboard"
]

# API version for future compatibility
API_VERSION = "2.0"

# Minimum requirements
MIN_PYTHON_VERSION = (3, 8)
MIN_PYQT_VERSION = "6.5.0"
MIN_SQLALCHEMY_VERSION = "2.0.0"

def get_version():
    """Get the current version string"""
    return __version__

def get_package_info():
    """Get comprehensive package information"""
    return {
        "name": PACKAGE_NAME,
        "version": __version__,
        "author": __author__,
        "description": __description__,
        "features": FEATURES,
        "api_version": API_VERSION,
        "database_version": DATABASE_VERSION,
        "config_version": CONFIG_VERSION
    }

def check_dependencies():
    """Check if all required dependencies are available"""
    import sys

    # Check Python version
    if sys.version_info < MIN_PYTHON_VERSION:
        raise RuntimeError(f"Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+ required")

    # Check PyQt6
    try:
        import PyQt6
        # Additional version check could be added here
    except ImportError:
        raise RuntimeError("PyQt6 is required but not installed")

    # Check SQLAlchemy
    try:
        import sqlalchemy
        # Additional version check could be added here
    except ImportError:
        raise RuntimeError("SQLAlchemy is required but not installed")

    return True

# Initialize logging for the package
def setup_package_logging():
    """Setup basic package logging"""
    try:
        from loguru import logger
        logger.info(f"Pharmacy Management System v{__version__} package loaded")
    except ImportError:
        # Fallback to standard logging if loguru not available
        import logging
        logging.basicConfig()
        logger = logging.getLogger(__name__)
        logger.info(f"Pharmacy Management System v{__version__} package loaded")

# Auto-setup when package is imported
try:
    check_dependencies()
    setup_package_logging()
except Exception as e:
    import warnings
    warnings.warn(f"Package initialization warning: {e}")
