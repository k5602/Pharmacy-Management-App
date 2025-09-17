"""
Login Dialog Module

This module provides the LoginDialog class for user authentication
with modern UI design and comprehensive validation.
"""

from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QCheckBox,
    QFrame, QGroupBox, QProgressBar, QComboBox
)
from PyQt6.QtCore import (
    pyqtSignal, Qt, QTimer, QPropertyAnimation,
    QEasingCurve, QRect
)
from PyQt6.QtGui import (
    QFont, QPixmap, QIcon, QPalette,
    QColor, QPainter, QLinearGradient
)

from controllers.auth import AuthController
from utils.validation import AuthValidation
from config.settings import AppSettings


class LoginDialog(QDialog):
    """
    Modern login dialog with authentication and validation.

    Features:
    - Username/password authentication
    - Remember me functionality
    - Language selection
    - Theme selection
    - Password visibility toggle
    - Loading animations
    - Error handling with visual feedback
    """

    # Signals
    login_successful = pyqtSignal(dict)  # user_data
    login_failed = pyqtSignal(str)       # error_message
    language_changed = pyqtSignal(str)   # language_code
    theme_changed = pyqtSignal(str)      # theme_name

    def __init__(self, parent: Optional[QDialog] = None):
        super().__init__(parent)

        # Controllers and validation
        self.auth_controller = AuthController()
        self.auth_validation = AuthValidation
        self.settings = AppSettings()

        # Dialog state
        self._is_logging_in = False
        self._current_language = self.settings.get('ui.language', 'ar')
        self._current_theme = self.settings.get('ui.theme', 'light')

        # UI components
        self.username_edit = None
        self.password_edit = None
        self.remember_checkbox = None
        self.login_button = None
        self.progress_bar = None
        self.error_label = None

        # Animations
        self.shake_animation = None
        self.fade_animation = None

        self._setup_dialog()
        self._setup_ui()
        self._connect_signals()
        self._apply_theme()

    def _setup_dialog(self):
        """Setup basic dialog properties."""
        self.setWindowTitle("تسجيل الدخول - إدارة الصيدلية" if self._current_language == 'ar' else "Login - Pharmacy Management")
        self.setModal(True)
        self.setFixedSize(400, 500)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)

        # Center on screen
        screen = self.screen()
        if screen:
            screen_geometry = screen.geometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)

    def _setup_ui(self):
        """Setup the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header section
        header_frame = self._create_header()
        main_layout.addWidget(header_frame)

        # Login form section
        form_frame = self._create_login_form()
        main_layout.addWidget(form_frame)

        # Footer section
        footer_frame = self._create_footer()
        main_layout.addWidget(footer_frame)

    def _create_header(self) -> QFrame:
        """Create the header section with logo and title."""
        frame = QFrame()
        frame.setFixedHeight(120)
        frame.setObjectName("headerFrame")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 10)
        layout.setSpacing(10)

        # Logo placeholder
        logo_label = QLabel("🏥")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = logo_label.font()
        font.setPointSize(32)
        logo_label.setFont(font)

        # Title
        title_label = QLabel("إدارة الصيدلية" if self._current_language == 'ar' else "Pharmacy Management")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setObjectName("titleLabel")
        font = title_label.font()
        font.setPointSize(18)
        font.setBold(True)
        title_label.setFont(font)

        # Subtitle
        subtitle_label = QLabel("نظام إدارة التغذية والصحة" if self._current_language == 'ar' else "Nutrition & Health Management System")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setObjectName("subtitleLabel")
        font = subtitle_label.font()
        font.setPointSize(10)
        subtitle_label.setFont(font)

        layout.addWidget(logo_label)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)

        return frame

    def _create_login_form(self) -> QFrame:
        """Create the login form section."""
        frame = QFrame()
        frame.setObjectName("formFrame")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(15)

        # Form title
        form_title = QLabel("تسجيل الدخول" if self._current_language == 'ar' else "Sign In")
        form_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_title.setObjectName("formTitle")
        font = form_title.font()
        font.setPointSize(16)
        font.setBold(True)
        form_title.setFont(font)
        layout.addWidget(form_title)

        # Error message label
        self.error_label = QLabel()
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setObjectName("errorLabel")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        # Username field
        username_group = self._create_input_group(
            "اسم المستخدم" if self._current_language == 'ar' else "Username",
            "admin"
        )
        self.username_edit = username_group.findChild(QLineEdit)
        layout.addWidget(username_group)

        # Password field
        password_group = self._create_input_group(
            "كلمة المرور" if self._current_language == 'ar' else "Password",
            "",
            is_password=True
        )
        self.password_edit = password_group.findChild(QLineEdit)
        layout.addWidget(password_group)

        # Remember me checkbox
        self.remember_checkbox = QCheckBox("تذكرني" if self._current_language == 'ar' else "Remember me")
        self.remember_checkbox.setChecked(self.settings.get('auth.remember_me', False))
        layout.addWidget(self.remember_checkbox)

        # Login button
        self.login_button = QPushButton("تسجيل الدخول" if self._current_language == 'ar' else "Sign In")
        self.login_button.setObjectName("loginButton")
        self.login_button.setMinimumHeight(45)
        self.login_button.clicked.connect(self._handle_login)
        layout.addWidget(self.login_button)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Forgot password link (placeholder)
        forgot_label = QLabel("<a href='#'>نسيت كلمة المرور؟</a>" if self._current_language == 'ar' else "<a href='#'>Forgot Password?</a>")
        forgot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        forgot_label.setOpenExternalLinks(False)
        forgot_label.linkActivated.connect(self._handle_forgot_password)
        layout.addWidget(forgot_label)

        return frame

    def _create_footer(self) -> QFrame:
        """Create the footer section with settings."""
        frame = QFrame()
        frame.setFixedHeight(80)
        frame.setObjectName("footerFrame")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(10)

        # Settings row
        settings_layout = QHBoxLayout()

        # Language selection
        language_label = QLabel("اللغة:" if self._current_language == 'ar' else "Language:")
        self.language_combo = QComboBox()
        self.language_combo.addItems(["العربية", "English"])
        self.language_combo.setCurrentIndex(0 if self._current_language == 'ar' else 1)
        self.language_combo.currentTextChanged.connect(self._handle_language_change)

        # Theme selection
        theme_label = QLabel("المظهر:" if self._current_language == 'ar' else "Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["فاتح" if self._current_language == 'ar' else "Light",
                                  "داكن" if self._current_language == 'ar' else "Dark"])
        self.theme_combo.setCurrentIndex(0 if self._current_theme == 'light' else 1)
        self.theme_combo.currentTextChanged.connect(self._handle_theme_change)

        settings_layout.addWidget(language_label)
        settings_layout.addWidget(self.language_combo)
        settings_layout.addStretch()
        settings_layout.addWidget(theme_label)
        settings_layout.addWidget(self.theme_combo)

        layout.addLayout(settings_layout)

        # Close button
        close_button = QPushButton("إغلاق" if self._current_language == 'ar' else "Close")
        close_button.setObjectName("closeButton")
        close_button.clicked.connect(self.reject)
        layout.addWidget(close_button)

        return frame

    def _create_input_group(self, label_text: str, placeholder: str, is_password: bool = False) -> QFrame:
        """Create an input group with label and field."""
        group = QFrame()
        layout = QVBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Label
        label = QLabel(label_text)
        label.setObjectName("inputLabel")
        layout.addWidget(label)

        # Input container
        input_container = QFrame()
        input_container.setObjectName("inputContainer")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(10, 8, 10, 8)
        input_layout.setSpacing(8)

        # Input field
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        input_field.setObjectName("inputField")

        if is_password:
            input_field.setEchoMode(QLineEdit.EchoMode.Password)

            # Password visibility toggle
            toggle_button = QPushButton("👁")
            toggle_button.setObjectName("toggleButton")
            toggle_button.setFixedSize(24, 24)
            toggle_button.setCheckable(True)
            toggle_button.clicked.connect(
                lambda checked: input_field.setEchoMode(
                    QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
                )
            )
            input_layout.addWidget(toggle_button)

        input_layout.addWidget(input_field)
        layout.addWidget(input_container)

        # Connect Enter key to login
        input_field.returnPressed.connect(self._handle_login)

        return group

    def _connect_signals(self):
        """Connect signals to handlers."""
        # Enable login button when both fields have text
        if self.username_edit and self.password_edit:
            self.username_edit.textChanged.connect(self._update_login_button_state)
            self.password_edit.textChanged.connect(self._update_login_button_state)

    def _apply_theme(self):
        """Apply the current theme styling."""
        if self._current_theme == 'dark':
            self._apply_dark_theme()
        else:
            self._apply_light_theme()

    def _apply_light_theme(self):
        """Apply light theme styling."""
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }

            #headerFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2196F3, stop:1 #1976D2);
                border-radius: 0px;
            }

            #titleLabel {
                color: white;
            }

            #subtitleLabel {
                color: rgba(255, 255, 255, 0.8);
            }

            #formFrame {
                background-color: white;
                border-radius: 0px;
            }

            #formTitle {
                color: #333333;
                margin-bottom: 10px;
            }

            #inputLabel {
                color: #666666;
                font-weight: 500;
            }

            #inputContainer {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
            }

            #inputContainer:focus-within {
                border-color: #2196F3;
            }

            #inputField {
                border: none;
                background: transparent;
                font-size: 14px;
                color: #333333;
            }

            #inputField:focus {
                outline: none;
            }

            #toggleButton {
                border: none;
                background: transparent;
                font-size: 12px;
                border-radius: 4px;
            }

            #toggleButton:hover {
                background-color: #f0f0f0;
            }

            #loginButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 12px;
            }

            #loginButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #45a049, stop:1 #3d8b40);
            }

            #loginButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3d8b40, stop:1 #2e7d32);
            }

            #loginButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }

            #errorLabel {
                color: #f44336;
                font-weight: 500;
                padding: 8px;
                background-color: #ffebee;
                border: 1px solid #ffcdd2;
                border-radius: 4px;
            }

            #footerFrame {
                background-color: #fafafa;
                border-top: 1px solid #e0e0e0;
            }

            #closeButton {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 6px;
                padding: 8px 16px;
                color: #666666;
            }

            #closeButton:hover {
                background-color: #e0e0e0;
            }

            QCheckBox {
                color: #666666;
                font-size: 14px;
            }

            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #cccccc;
                border-radius: 3px;
                background-color: white;
            }

            QCheckBox::indicator:checked {
                background-color: #2196F3;
                border-color: #2196F3;
                image: url(:/icons/checkmark.png);
            }

            QComboBox {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: white;
                min-width: 80px;
            }

            QComboBox:hover {
                border-color: #2196F3;
            }

            QComboBox::drop-down {
                border: none;
                width: 20px;
            }

            QComboBox::down-arrow {
                image: url(:/icons/arrow_down.png);
                width: 12px;
                height: 12px;
            }

            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #e0e0e0;
                height: 6px;
            }

            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2196F3, stop:1 #1976D2);
                border-radius: 4px;
            }

            QLabel[href] {
                color: #2196F3;
                text-decoration: none;
            }

            QLabel[href]:hover {
                text-decoration: underline;
            }
        """)

    def _apply_dark_theme(self):
        """Apply dark theme styling."""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }

            #headerFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1976D2, stop:1 #0d47a1);
            }

            #titleLabel, #subtitleLabel {
                color: white;
            }

            #formFrame {
                background-color: #3c3c3c;
            }

            #formTitle {
                color: #ffffff;
            }

            #inputLabel {
                color: #cccccc;
            }

            #inputContainer {
                border: 2px solid #555555;
                background-color: #404040;
            }

            #inputContainer:focus-within {
                border-color: #2196F3;
            }

            #inputField {
                color: #ffffff;
                background: transparent;
                border: none;
            }

            #toggleButton {
                background: transparent;
                border: none;
                color: #cccccc;
            }

            #toggleButton:hover {
                background-color: #555555;
            }

            #loginButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                border: none;
                color: white;
            }

            #errorLabel {
                color: #ff6b6b;
                background-color: rgba(255, 107, 107, 0.1);
                border: 1px solid rgba(255, 107, 107, 0.3);
            }

            #footerFrame {
                background-color: #333333;
                border-top: 1px solid #555555;
            }

            #closeButton {
                background-color: #555555;
                border: 1px solid #666666;
                color: #ffffff;
            }

            #closeButton:hover {
                background-color: #666666;
            }

            QCheckBox {
                color: #cccccc;
            }

            QCheckBox::indicator {
                border: 2px solid #666666;
                background-color: #404040;
            }

            QCheckBox::indicator:checked {
                background-color: #2196F3;
                border-color: #2196F3;
            }

            QComboBox {
                border: 1px solid #666666;
                background-color: #404040;
                color: #ffffff;
            }

            QComboBox:hover {
                border-color: #2196F3;
            }

            QComboBox QAbstractItemView {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #666666;
            }

            QProgressBar {
                background-color: #555555;
            }

            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2196F3, stop:1 #1976D2);
            }
        """)

    def _update_login_button_state(self):
        """Update login button enabled state based on input validation."""
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()

        # Enable button only if both fields have content
        self.login_button.setEnabled(bool(username and password and not self._is_logging_in))

    def _handle_login(self):
        """Handle login button click."""
        if self._is_logging_in:
            return

        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()

        # Validate inputs
        if not username:
            self._show_error("يرجى إدخال اسم المستخدم" if self._current_language == 'ar' else "Please enter username")
            self._animate_error()
            return

        if not password:
            self._show_error("يرجى إدخال كلمة المرور" if self._current_language == 'ar' else "Please enter password")
            self._animate_error()
            return

        # Start login process
        self._start_login()

        try:
            # Authenticate user
            auth_result = self.auth_controller.authenticate(username, password)

            if auth_result.success:
                # Save remember me setting
                if self.remember_checkbox.isChecked():
                    self.settings.set('auth.remember_me', True)
                    self.settings.set('auth.last_username', username)
                else:
                    self.settings.set('auth.remember_me', False)
                    self.settings.remove('auth.last_username')

                # Save language and theme preferences
                self.settings.set('ui.language', self._current_language)
                self.settings.set('ui.theme', self._current_theme)

                self._finish_login()
                self.login_successful.emit(auth_result.user_data)
                self.accept()
            else:
                self._finish_login()
                self._show_error(auth_result.error_message)
                self._animate_error()
                self.login_failed.emit(auth_result.error_message)

        except Exception as e:
            self._finish_login()
            error_msg = f"خطأ في تسجيل الدخول: {str(e)}" if self._current_language == 'ar' else f"Login error: {str(e)}"
            self._show_error(error_msg)
            self._animate_error()
            self.login_failed.emit(error_msg)

    def _start_login(self):
        """Start login process with visual feedback."""
        self._is_logging_in = True
        self.login_button.setEnabled(False)
        self.login_button.setText("جاري تسجيل الدخول..." if self._current_language == 'ar' else "Signing in...")
        self.progress_bar.show()
        self._hide_error()

    def _finish_login(self):
        """Finish login process and reset UI."""
        self._is_logging_in = False
        self.login_button.setText("تسجيل الدخول" if self._current_language == 'ar' else "Sign In")
        self.progress_bar.hide()
        self._update_login_button_state()

    def _show_error(self, message: str):
        """Show error message with styling."""
        self.error_label.setText(message)
        self.error_label.show()

    def _hide_error(self):
        """Hide error message."""
        self.error_label.hide()

    def _animate_error(self):
        """Animate error display with shake effect."""
        if not self.shake_animation:
            self.shake_animation = QPropertyAnimation(self, b"geometry")
            self.shake_animation.setDuration(500)
            self.shake_animation.setEasingCurve(QEasingCurve.Type.OutBounce)

        # Shake the dialog
        original_geometry = self.geometry()
        self.shake_animation.setStartValue(original_geometry)
        self.shake_animation.setEndValue(original_geometry)

        # Add intermediate shake positions
        self.shake_animation.setKeyValueAt(0.1, QRect(original_geometry.x() - 10, original_geometry.y(),
                                                      original_geometry.width(), original_geometry.height()))
        self.shake_animation.setKeyValueAt(0.3, QRect(original_geometry.x() + 10, original_geometry.y(),
                                                      original_geometry.width(), original_geometry.height()))
        self.shake_animation.setKeyValueAt(0.5, QRect(original_geometry.x() - 5, original_geometry.y(),
                                                      original_geometry.width(), original_geometry.height()))
        self.shake_animation.setKeyValueAt(0.7, QRect(original_geometry.x() + 5, original_geometry.y(),
                                                      original_geometry.width(), original_geometry.height()))

        self.shake_animation.start()

    def _handle_language_change(self, language_text: str):
        """Handle language selection change."""
        new_language = 'ar' if language_text == 'العربية' else 'en'
        if new_language != self._current_language:
            self._current_language = new_language
            self.language_changed.emit(new_language)
            self._update_ui_language()

    def _handle_theme_change(self, theme_text: str):
        """Handle theme selection change."""
        if self._current_language == 'ar':
            new_theme = 'light' if theme_text == 'فاتح' else 'dark'
        else:
            new_theme = 'light' if theme_text == 'Light' else 'dark'

        if new_theme != self._current_theme:
            self._current_theme = new_theme
            self.theme_changed.emit(new_theme)
            self._apply_theme()

    def _handle_forgot_password(self):
        """Handle forgot password link click."""
        # TODO: Implement forgot password functionality
        message = "ميزة استعادة كلمة المرور قيد التطوير" if self._current_language == 'ar' else "Password recovery feature coming soon"
        self._show_error(message)

    def _update_ui_language(self):
        """Update UI text based on selected language."""
        # This would typically require recreating the dialog or using a translation system
        # For now, just update the window title
        self.setWindowTitle("تسجيل الدخول - إدارة الصيدلية" if self._current_language == 'ar' else "Login - Pharmacy Management")

    def load_saved_credentials(self):
        """Load saved credentials if remember me was enabled."""
        if self.settings.get('auth.remember_me', False):
            saved_username = self.settings.get('auth.last_username', '')
            if saved_username and self.username_edit:
                self.username_edit.setText(saved_username)
                if self.password_edit:
                    self.password_edit.setFocus()

    def showEvent(self, event):
        """Handle dialog show event."""
        super().showEvent(event)
        self.load_saved_credentials()
        self._update_login_button_state()

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
