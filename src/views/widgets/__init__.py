"""
Widgets Module

This module contains all custom widget classes for the Pharmacy Management App.
These widgets provide the main user interface components including forms,
dashboards, and specialized input widgets.
"""

from .base_widget import BaseWidget
from .client_widget import ClientWidget
from .diet_widget import DietWidget
from .dashboard_widget import DashboardWidget

__all__ = [
    'BaseWidget',
    'ClientWidget',
    'DietWidget',
    'DashboardWidget'
]
