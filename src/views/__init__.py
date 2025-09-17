"""
Views Package
User interface components for the Pharmacy Management System v2.0

This package contains all UI-related classes and components following the MVC pattern:

- MainWindow: Primary application window
- Dialogs: Modal dialogs for user interactions
- Components: Reusable UI components and widgets
- Widgets: Custom widgets for specific functionality
- Themes: Theme and styling management

The views are responsible for displaying data and capturing user input,
but do not contain business logic (which belongs in controllers).
"""

from typing import Optional, Dict, Any

# Import main window when available
try:
    from .main_window import MainWindow
except ImportError:
    MainWindow = None

# Import dialogs when available
try:
    from .dialogs.login_dialog import LoginDialog
except ImportError:
    LoginDialog = None

try:
    from .dialogs.about_dialog import AboutDialog
except ImportError:
    AboutDialog = None

try:
    from .dialogs.settings_dialog import SettingsDialog
except ImportError:
    SettingsDialog = None

# Import components when available
try:
    from .components.search_widget import SearchWidget
except ImportError:
    SearchWidget = None

try:
    from .components.client_dashboard import ClientDashboard
except ImportError:
    ClientDashboard = None

try:
    from .components.quick_actions import QuickActionsWidget
except ImportError:
    QuickActionsWidget = None

# Version information
__version__ = "2.0.0"
__author__ = "Khaled Alam"

# Available view types
VIEW_TYPES = [
    "main_window",
    "login_dialog",
    "about_dialog",
    "settings_dialog",
    "search_widget",
    "client_dashboard",
    "quick_actions"
]

# View class mapping
VIEW_CLASSES = {
    "main_window": MainWindow,
    "login_dialog": LoginDialog,
    "about_dialog": AboutDialog,
    "settings_dialog": SettingsDialog,
    "search_widget": SearchWidget,
    "client_dashboard": ClientDashboard,
    "quick_actions": QuickActionsWidget
}

def get_view_class(view_type: str):
    """
    Get view class by type

    Args:
        view_type: Type of view to get

    Returns:
        View class or None if not found
    """
    return VIEW_CLASSES.get(view_type.lower())

def create_view(view_type: str, *args, **kwargs):
    """
    Create a view instance by type

    Args:
        view_type: Type of view to create
        *args: View constructor arguments
        **kwargs: View constructor keyword arguments

    Returns:
        View instance or None if type not found
    """
    view_class = get_view_class(view_type)
    if view_class:
        return view_class(*args, **kwargs)
    return None

def get_available_views():
    """Get list of available view types"""
    return [
        view_type for view_type, view_class in VIEW_CLASSES.items()
        if view_class is not None
    ]

def get_view_info():
    """Get information about available views"""
    return {
        "version": __version__,
        "view_types": VIEW_TYPES,
        "available_views": get_available_views()
    }

# UI utilities
def apply_rtl_layout(widget):
    """
    Apply Right-to-Left layout to a widget for Arabic support

    Args:
        widget: Qt widget to apply RTL layout to
    """
    try:
        from PyQt6.QtCore import Qt
        widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    except Exception:
        pass

def set_arabic_font(widget, font_size: int = 12):
    """
    Set Arabic font for a widget

    Args:
        widget: Qt widget to set font for
        font_size: Font size
    """
    try:
        from PyQt6.QtGui import QFont
        from ..utils.resource_manager import get_resource_manager

        resource_manager = get_resource_manager()
        arabic_font = resource_manager.load_font("NotoSansArabic-Regular.ttf", font_size)

        if arabic_font:
            widget.setFont(arabic_font)
        else:
            # Fallback to system font
            fallback_font = QFont("Arial", font_size)
            widget.setFont(fallback_font)

    except Exception:
        pass

# Theme management
def apply_theme(widget, theme_name: str = "light"):
    """
    Apply theme to a widget

    Args:
        widget: Qt widget to apply theme to
        theme_name: Name of theme (light/dark)
    """
    try:
        from ..utils.resource_manager import get_resource_manager

        resource_manager = get_resource_manager()
        if theme_name == "dark":
            stylesheet = resource_manager.load_stylesheet("dark_theme.qss")
        else:
            stylesheet = resource_manager.load_stylesheet("light_theme.qss")

        if stylesheet:
            widget.setStyleSheet(stylesheet)

    except Exception:
        pass

# Export commonly used items
__all__ = [
    # Main components
    "MainWindow",
    "LoginDialog",
    "AboutDialog",
    "SettingsDialog",
    "SearchWidget",
    "ClientDashboard",
    "QuickActionsWidget",

    # Utility functions
    "get_view_class",
    "create_view",
    "get_available_views",
    "get_view_info",
    "apply_rtl_layout",
    "set_arabic_font",
    "apply_theme",

    # Constants
    "VIEW_TYPES",
    "VIEW_CLASSES"
]
