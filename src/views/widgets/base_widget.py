"""
Base Widget Module

This module provides the foundational BaseWidget class that all custom widgets
in the Pharmacy Management App inherit from. It includes common functionality
like theming, localization, validation, and signal handling.
"""

from typing import Optional, Dict, Any, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit,
    QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QRadioButton, QGroupBox,
    QFrame, QSplitter, QScrollArea
)
from PyQt6.QtCore import (
    QObject, pyqtSignal, QTimer, QSettings,
    Qt, QPropertyAnimation, QEasingCurve,
    QRect, QSize
)
from PyQt6.QtGui import (
    QFont, QPalette, QColor, QIcon,
    QPainter, QPen, QBrush
)

from config.settings import AppSettings
from utils.resource_manager import ResourceManager
from utils.validation import ValidationMixin


class BaseWidget(QWidget, ValidationMixin):
    """
    Base widget class providing common functionality for all custom widgets.

    Features:
    - Theme management and styling
    - RTL/LTR layout support
    - Validation integration
    - Common UI patterns
    - Resource management
    - Animation support
    - Signal handling
    """

    # Common signals that widgets can emit
    data_changed = pyqtSignal(str, object)  # field_name, new_value
    validation_error = pyqtSignal(str, str)  # field_name, error_message
    action_requested = pyqtSignal(str, dict)  # action_name, parameters
    focus_next_requested = pyqtSignal()
    focus_previous_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        # Initialize core components
        self.settings = AppSettings()
        self.resource_manager = ResourceManager()

        # Widget state
        self._is_rtl = self.settings.get('ui.language', 'ar') == 'ar'
        self._current_theme = self.settings.get('ui.theme', 'light')
        self._validation_enabled = True
        self._auto_save_enabled = False
        self._animations_enabled = self.settings.get('ui.animations', True)

        # UI components
        self._main_layout = None
        self._error_labels: Dict[str, QLabel] = {}
        self._field_widgets: Dict[str, QWidget] = {}

        # Timers
        self._auto_save_timer = QTimer()
        self._auto_save_timer.timeout.connect(self._auto_save)
        self._validation_timer = QTimer()
        self._validation_timer.setSingleShot(True)
        self._validation_timer.timeout.connect(self._delayed_validation)

        # Initialize the widget
        self._setup_widget()
        self._setup_layout()
        self._apply_theme()
        self._setup_shortcuts()

    def _setup_widget(self):
        """Initialize basic widget properties."""
        self.setObjectName(self.__class__.__name__)

        # Set layout direction based on language
        if self._is_rtl:
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

    def _setup_layout(self):
        """Setup the main layout. Override in subclasses."""
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(10, 10, 10, 10)
        self._main_layout.setSpacing(8)

    def _apply_theme(self):
        """Apply the current theme to the widget."""
        theme_colors = self._get_theme_colors()

        # Base styling
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {theme_colors['background']};
                color: {theme_colors['text']};
                font-family: {self._get_font_family()};
                font-size: 10pt;
            }}

            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
                background-color: {theme_colors['input_background']};
                border: 1px solid {theme_colors['border']};
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 20px;
            }}

            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
                border: 2px solid {theme_colors['primary']};
            }}

            QPushButton {{
                background-color: {theme_colors['button_background']};
                border: 1px solid {theme_colors['border']};
                border-radius: 4px;
                padding: 6px 12px;
                min-height: 24px;
                font-weight: 500;
            }}

            QPushButton:hover {{
                background-color: {theme_colors['button_hover']};
            }}

            QPushButton:pressed {{
                background-color: {theme_colors['button_pressed']};
            }}

            QPushButton:disabled {{
                background-color: {theme_colors['disabled']};
                color: {theme_colors['disabled_text']};
            }}

            QLabel.error {{
                color: {theme_colors['error']};
                font-size: 9pt;
                font-style: italic;
            }}

            QLabel.warning {{
                color: {theme_colors['warning']};
                font-size: 9pt;
                font-style: italic;
            }}

            QLabel.success {{
                color: {theme_colors['success']};
                font-size: 9pt;
                font-style: italic;
            }}

            QGroupBox {{
                font-weight: bold;
                border: 2px solid {theme_colors['border']};
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px 0 4px;
            }}
        """)

    def _get_theme_colors(self) -> Dict[str, str]:
        """Get color scheme for current theme."""
        if self._current_theme == 'dark':
            return {
                'background': '#2b2b2b',
                'text': '#ffffff',
                'input_background': '#3c3c3c',
                'button_background': '#404040',
                'button_hover': '#4a4a4a',
                'button_pressed': '#363636',
                'border': '#555555',
                'primary': '#0078d4',
                'error': '#ff6b6b',
                'warning': '#ffa726',
                'success': '#4caf50',
                'disabled': '#666666',
                'disabled_text': '#999999'
            }
        else:  # light theme
            return {
                'background': '#ffffff',
                'text': '#000000',
                'input_background': '#ffffff',
                'button_background': '#f0f0f0',
                'button_hover': '#e6e6e6',
                'button_pressed': '#d9d9d9',
                'border': '#cccccc',
                'primary': '#0078d4',
                'error': '#d32f2f',
                'warning': '#f57c00',
                'success': '#388e3c',
                'disabled': '#e0e0e0',
                'disabled_text': '#999999'
            }

    def _get_font_family(self) -> str:
        """Get appropriate font family for current language."""
        if self._is_rtl:
            return self.settings.get('ui.arabic_font', 'Tahoma')
        else:
            return self.settings.get('ui.english_font', 'Segoe UI')

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts. Override in subclasses."""
        pass

    def _auto_save(self):
        """Auto-save functionality. Override in subclasses."""
        if self._auto_save_enabled:
            self.save_data()

    def _delayed_validation(self):
        """Perform delayed validation to avoid excessive validation calls."""
        if self._validation_enabled:
            self.validate_all_fields()

    # Public API methods

    def set_validation_enabled(self, enabled: bool):
        """Enable or disable field validation."""
        self._validation_enabled = enabled

    def set_auto_save_enabled(self, enabled: bool, interval: int = 5000):
        """Enable or disable auto-save with specified interval in milliseconds."""
        self._auto_save_enabled = enabled
        if enabled:
            self._auto_save_timer.start(interval)
        else:
            self._auto_save_timer.stop()

    def set_rtl_mode(self, rtl: bool):
        """Set right-to-left layout mode."""
        self._is_rtl = rtl
        if rtl:
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

    def set_theme(self, theme: str):
        """Change the widget theme."""
        self._current_theme = theme
        self._apply_theme()

    def add_field_widget(self, name: str, widget: QWidget):
        """Register a field widget for validation and data handling."""
        self._field_widgets[name] = widget

        # Connect appropriate signals based on widget type
        if isinstance(widget, (QLineEdit, QTextEdit)):
            widget.textChanged.connect(
                lambda: self.data_changed.emit(name, widget.text())
            )
            widget.textChanged.connect(self._schedule_validation)
        elif isinstance(widget, QComboBox):
            widget.currentTextChanged.connect(
                lambda text: self.data_changed.emit(name, text)
            )
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            widget.valueChanged.connect(
                lambda value: self.data_changed.emit(name, value)
            )
        elif isinstance(widget, QCheckBox):
            widget.toggled.connect(
                lambda checked: self.data_changed.emit(name, checked)
            )

    def add_error_label(self, field_name: str, label: QLabel):
        """Register an error label for a field."""
        label.setObjectName(f"error_label_{field_name}")
        label.setProperty("class", "error")
        label.hide()
        self._error_labels[field_name] = label

    def show_field_error(self, field_name: str, message: str):
        """Show an error message for a specific field."""
        if field_name in self._error_labels:
            label = self._error_labels[field_name]
            label.setText(message)
            label.show()

            # Animate the error label if animations are enabled
            if self._animations_enabled:
                self._animate_widget(label, "color")

    def clear_field_error(self, field_name: str):
        """Clear the error message for a specific field."""
        if field_name in self._error_labels:
            self._error_labels[field_name].hide()

    def clear_all_errors(self):
        """Clear all error messages."""
        for label in self._error_labels.values():
            label.hide()

    def validate_field(self, field_name: str) -> bool:
        """Validate a specific field. Override in subclasses."""
        return True

    def validate_all_fields(self) -> bool:
        """Validate all registered fields."""
        is_valid = True
        for field_name in self._field_widgets.keys():
            if not self.validate_field(field_name):
                is_valid = False
        return is_valid

    def get_field_value(self, field_name: str) -> Any:
        """Get the current value of a field widget."""
        if field_name not in self._field_widgets:
            return None

        widget = self._field_widgets[field_name]

        if isinstance(widget, (QLineEdit, QTextEdit)):
            return widget.text()
        elif isinstance(widget, QComboBox):
            return widget.currentText()
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            return widget.value()
        elif isinstance(widget, QCheckBox):
            return widget.isChecked()
        else:
            return None

    def set_field_value(self, field_name: str, value: Any):
        """Set the value of a field widget."""
        if field_name not in self._field_widgets:
            return

        widget = self._field_widgets[field_name]

        if isinstance(widget, (QLineEdit, QTextEdit)):
            widget.setText(str(value) if value is not None else "")
        elif isinstance(widget, QComboBox):
            index = widget.findText(str(value))
            if index >= 0:
                widget.setCurrentIndex(index)
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            widget.setValue(value if value is not None else 0)
        elif isinstance(widget, QCheckBox):
            widget.setChecked(bool(value))

    def get_all_field_values(self) -> Dict[str, Any]:
        """Get all field values as a dictionary."""
        values = {}
        for field_name in self._field_widgets.keys():
            values[field_name] = self.get_field_value(field_name)
        return values

    def set_all_field_values(self, values: Dict[str, Any]):
        """Set multiple field values from a dictionary."""
        for field_name, value in values.items():
            self.set_field_value(field_name, value)

    def clear_all_fields(self):
        """Clear all field values."""
        for field_name in self._field_widgets.keys():
            widget = self._field_widgets[field_name]
            if isinstance(widget, (QLineEdit, QTextEdit)):
                widget.clear()
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(-1)
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.setValue(0)
            elif isinstance(widget, QCheckBox):
                widget.setChecked(False)

    def _schedule_validation(self):
        """Schedule validation to occur after a brief delay."""
        if self._validation_enabled:
            self._validation_timer.start(500)  # 500ms delay

    def _animate_widget(self, widget: QWidget, property_name: str):
        """Animate a widget property if animations are enabled."""
        if not self._animations_enabled:
            return

        # Simple fade-in animation for error labels
        if property_name == "color" and isinstance(widget, QLabel):
            widget.setStyleSheet("color: rgba(211, 47, 47, 0);")
            animation = QPropertyAnimation(widget, b"color")
            animation.setDuration(300)
            animation.setStartValue(QColor(211, 47, 47, 0))
            animation.setEndValue(QColor(211, 47, 47, 255))
            animation.start()

    def create_form_layout(self) -> QGridLayout:
        """Create a standard form layout with proper spacing."""
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(8)
        layout.setColumnStretch(1, 1)  # Make input column expandable
        return layout

    def create_button_layout(self, buttons: List[QPushButton]) -> QHBoxLayout:
        """Create a horizontal layout for buttons with proper spacing."""
        layout = QHBoxLayout()
        layout.addStretch()  # Push buttons to the right (or left in RTL)

        for button in buttons:
            layout.addWidget(button)

        return layout

    def create_group_box(self, title: str, layout: QVBoxLayout = None) -> QGroupBox:
        """Create a styled group box with optional layout."""
        group = QGroupBox(title)
        if layout:
            group.setLayout(layout)
        return group

    def create_separator(self) -> QFrame:
        """Create a horizontal separator line."""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        return separator

    # Virtual methods for subclasses to override

    def load_data(self) -> bool:
        """Load data into the widget. Override in subclasses."""
        return True

    def save_data(self) -> bool:
        """Save data from the widget. Override in subclasses."""
        return True

    def reset_data(self):
        """Reset the widget to its default state. Override in subclasses."""
        self.clear_all_fields()
        self.clear_all_errors()

    def refresh_data(self):
        """Refresh the widget data. Override in subclasses."""
        self.load_data()

    def show_error(self, message: str):
        """Show error message. Override in subclasses for custom implementation."""
        print(f"Error: {message}")

    def show_warning(self, message: str):
        """Show warning message. Override in subclasses for custom implementation."""
        print(f"Warning: {message}")

    def show_information(self, message: str):
        """Show information message. Override in subclasses for custom implementation."""
        print(f"Info: {message}")
