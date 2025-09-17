"""
Main Window Module

This module provides the MainWindow class which serves as the primary interface
for the Pharmacy Management Application. It integrates all widgets, handles
navigation, and manages the overall application state.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QMenuBar, QToolBar, QStatusBar,
    QLabel, QPushButton, QLineEdit, QComboBox,
    QSplitter, QStackedWidget, QMessageBox,
    QProgressBar, QSystemTrayIcon, QMenu,
    QApplication, QFileDialog, QDialog
)
from PyQt6.QtCore import (
    pyqtSignal, Qt, QTimer, QSettings,
    QSize, QPoint, QThread, QObject
)
from PyQt6.QtGui import (
    QAction, QIcon, QKeySequence, QFont,
    QCloseEvent, QPalette, QColor
)

from views.widgets.dashboard_widget import DashboardWidget
from views.widgets.client_widget import ClientWidget
from views.widgets.diet_widget import DietWidget
from views.widgets.base_widget import BaseWidget
from views.dialogs.login_dialog import LoginDialog
from controllers.auth import AuthController
from controllers.client import ClientController
from controllers.diet import DietController
from controllers.report import ReportController
from config.settings import AppSettings
from utils.resource_manager import ResourceManager


class MainWindow(QMainWindow):
    """
    Main application window providing the primary user interface.

    Features:
    - Tabbed interface for different modules
    - Menu bar with comprehensive actions
    - Tool bar with quick actions
    - Status bar with system information
    - User authentication integration
    - Theme and language support
    - Auto-save functionality
    - System tray integration
    """

    # Signals
    user_logged_in = pyqtSignal(dict)     # user_data
    user_logged_out = pyqtSignal()
    theme_changed = pyqtSignal(str)       # theme_name
    language_changed = pyqtSignal(str)    # language_code
    client_selected = pyqtSignal(int)     # client_id
    backup_completed = pyqtSignal(bool)   # success

    def __init__(self):
        super().__init__()

        # Core components
        self.settings = AppSettings()
        self.resource_manager = ResourceManager()

        # Controllers
        self.auth_controller = AuthController()
        self.client_controller = ClientController()
        self.diet_controller = DietController()
        self.report_controller = ReportController()

        # Application state
        self.current_user = None
        self.current_client_id = None
        self.current_language = self.settings.get('ui.language', 'ar')
        self.current_theme = self.settings.get('ui.theme', 'light')
        self.is_rtl = self.current_language == 'ar'

        # UI components
        self.central_stack = None
        self.tab_widget = None
        self.dashboard_widget = None
        self.client_widget = None
        self.diet_widget = None
        self.menu_bar = None
        self.tool_bar = None
        self.status_bar = None
        self.search_widget = None
        self.quick_actions_widget = None

        # Timers
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save)

        self.status_update_timer = QTimer()
        self.status_update_timer.timeout.connect(self._update_status_info)

        # System tray
        self.tray_icon = None

        # Initialize UI
        self._setup_window()
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_central_widget()
        self._create_status_bar()
        self._apply_theme()
        self._setup_shortcuts()
        self._setup_auto_save()
        self._setup_system_tray()
        self._connect_signals()

        # Show login dialog
        self._show_login_dialog()

    def _setup_window(self):
        """Initialize basic window properties."""
        self.setWindowTitle("نظام إدارة الصيدلية" if self.is_rtl else "Pharmacy Management System")
        self.setMinimumSize(1200, 800)

        # Restore window geometry
        self.restoreGeometry(self.settings.get('window.geometry', b''))
        self.restoreState(self.settings.get('window.state', b''))

        # If no saved geometry, center window
        if not self.settings.get('window.geometry'):
            screen = QApplication.primaryScreen()
            if screen:
                screen_geometry = screen.geometry()
                size = screen_geometry.size() * 0.8
                self.resize(size)

                # Center window
                x = (screen_geometry.width() - self.width()) // 2
                y = (screen_geometry.height() - self.height()) // 2
                self.move(x, y)

        # Set layout direction
        if self.is_rtl:
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        # Set window icon
        self.setWindowIcon(QIcon(":/icons/pharmacy.png"))

    def _create_menu_bar(self):
        """Create the application menu bar."""
        self.menu_bar = self.menuBar()

        # File Menu
        file_menu = self.menu_bar.addMenu("ملف" if self.is_rtl else "File")

        # New Client
        new_client_action = QAction("عميل جديد" if self.is_rtl else "New Client", self)
        new_client_action.setShortcut(QKeySequence.StandardKey.New)
        new_client_action.setIcon(QIcon(":/icons/user_add.png"))
        new_client_action.triggered.connect(self._new_client)
        file_menu.addAction(new_client_action)

        # Open Client
        open_client_action = QAction("فتح عميل" if self.is_rtl else "Open Client", self)
        open_client_action.setShortcut(QKeySequence.StandardKey.Open)
        open_client_action.setIcon(QIcon(":/icons/user_open.png"))
        open_client_action.triggered.connect(self._open_client)
        file_menu.addAction(open_client_action)

        file_menu.addSeparator()

        # Import Data
        import_action = QAction("استيراد البيانات" if self.is_rtl else "Import Data", self)
        import_action.setIcon(QIcon(":/icons/import.png"))
        import_action.triggered.connect(self._import_data)
        file_menu.addAction(import_action)

        # Export Data
        export_action = QAction("تصدير البيانات" if self.is_rtl else "Export Data", self)
        export_action.setIcon(QIcon(":/icons/export.png"))
        export_action.triggered.connect(self._export_data)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        # Backup
        backup_action = QAction("نسخ احتياطي" if self.is_rtl else "Backup", self)
        backup_action.setIcon(QIcon(":/icons/backup.png"))
        backup_action.triggered.connect(self._create_backup)
        file_menu.addAction(backup_action)

        # Restore
        restore_action = QAction("استعادة" if self.is_rtl else "Restore", self)
        restore_action.setIcon(QIcon(":/icons/restore.png"))
        restore_action.triggered.connect(self._restore_backup)
        file_menu.addAction(restore_action)

        file_menu.addSeparator()

        # Exit
        exit_action = QAction("خروج" if self.is_rtl else "Exit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setIcon(QIcon(":/icons/exit.png"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = self.menu_bar.addMenu("تحرير" if self.is_rtl else "Edit")

        # Undo
        undo_action = QAction("تراجع" if self.is_rtl else "Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.setIcon(QIcon(":/icons/undo.png"))
        edit_menu.addAction(undo_action)

        # Redo
        redo_action = QAction("إعادة" if self.is_rtl else "Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.setIcon(QIcon(":/icons/redo.png"))
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        # Find
        find_action = QAction("بحث" if self.is_rtl else "Find", self)
        find_action.setShortcut(QKeySequence.StandardKey.Find)
        find_action.setIcon(QIcon(":/icons/search.png"))
        find_action.triggered.connect(self._focus_search)
        edit_menu.addAction(find_action)

        edit_menu.addSeparator()

        # Preferences
        preferences_action = QAction("تفضيلات" if self.is_rtl else "Preferences", self)
        preferences_action.setShortcut(QKeySequence.StandardKey.Preferences)
        preferences_action.setIcon(QIcon(":/icons/settings.png"))
        preferences_action.triggered.connect(self._show_settings)
        edit_menu.addAction(preferences_action)

        # View Menu
        view_menu = self.menu_bar.addMenu("عرض" if self.is_rtl else "View")

        # Dashboard
        dashboard_action = QAction("لوحة المعلومات" if self.is_rtl else "Dashboard", self)
        dashboard_action.setShortcut(QKeySequence("Ctrl+1"))
        dashboard_action.triggered.connect(lambda: self._switch_to_tab(0))
        view_menu.addAction(dashboard_action)

        # Clients
        clients_action = QAction("العملاء" if self.is_rtl else "Clients", self)
        clients_action.setShortcut(QKeySequence("Ctrl+2"))
        clients_action.triggered.connect(lambda: self._switch_to_tab(1))
        view_menu.addAction(clients_action)

        # Diet & Nutrition
        diet_action = QAction("التغذية والحمية" if self.is_rtl else "Diet & Nutrition", self)
        diet_action.setShortcut(QKeySequence("Ctrl+3"))
        diet_action.triggered.connect(lambda: self._switch_to_tab(2))
        view_menu.addAction(diet_action)

        view_menu.addSeparator()

        # Toggle Theme
        theme_action = QAction("تبديل المظهر" if self.is_rtl else "Toggle Theme", self)
        theme_action.setShortcut(QKeySequence("Ctrl+T"))
        theme_action.triggered.connect(self._toggle_theme)
        view_menu.addAction(theme_action)

        # Toggle Language
        language_action = QAction("تبديل اللغة" if self.is_rtl else "Toggle Language", self)
        language_action.setShortcut(QKeySequence("Ctrl+L"))
        language_action.triggered.connect(self._toggle_language)
        view_menu.addAction(language_action)

        view_menu.addSeparator()

        # Fullscreen
        fullscreen_action = QAction("ملء الشاشة" if self.is_rtl else "Fullscreen", self)
        fullscreen_action.setShortcut(QKeySequence.StandardKey.FullScreen)
        fullscreen_action.triggered.connect(self._toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        # Reports Menu
        reports_menu = self.menu_bar.addMenu("التقارير" if self.is_rtl else "Reports")

        # Client Report
        client_report_action = QAction("تقرير العميل" if self.is_rtl else "Client Report", self)
        client_report_action.setIcon(QIcon(":/icons/report_client.png"))
        client_report_action.triggered.connect(self._generate_client_report)
        reports_menu.addAction(client_report_action)

        # Nutrition Report
        nutrition_report_action = QAction("تقرير التغذية" if self.is_rtl else "Nutrition Report", self)
        nutrition_report_action.setIcon(QIcon(":/icons/report_nutrition.png"))
        nutrition_report_action.triggered.connect(self._generate_nutrition_report)
        reports_menu.addAction(nutrition_report_action)

        # Statistics Report
        stats_report_action = QAction("تقرير الإحصائيات" if self.is_rtl else "Statistics Report", self)
        stats_report_action.setIcon(QIcon(":/icons/report_stats.png"))
        stats_report_action.triggered.connect(self._generate_statistics_report)
        reports_menu.addAction(stats_report_action)

        # Tools Menu
        tools_menu = self.menu_bar.addMenu("أدوات" if self.is_rtl else "Tools")

        # BMI Calculator
        bmi_action = QAction("حاسبة مؤشر كتلة الجسم" if self.is_rtl else "BMI Calculator", self)
        bmi_action.setIcon(QIcon(":/icons/calculator.png"))
        bmi_action.triggered.connect(self._show_bmi_calculator)
        tools_menu.addAction(bmi_action)

        # Calorie Calculator
        calorie_action = QAction("حاسبة السعرات" if self.is_rtl else "Calorie Calculator", self)
        calorie_action.setIcon(QIcon(":/icons/calories.png"))
        calorie_action.triggered.connect(self._show_calorie_calculator)
        tools_menu.addAction(calorie_action)

        tools_menu.addSeparator()

        # User Management
        user_mgmt_action = QAction("إدارة المستخدمين" if self.is_rtl else "User Management", self)
        user_mgmt_action.setIcon(QIcon(":/icons/users.png"))
        user_mgmt_action.triggered.connect(self._show_user_management)
        tools_menu.addAction(user_mgmt_action)

        # Database Maintenance
        db_maintenance_action = QAction("صيانة قاعدة البيانات" if self.is_rtl else "Database Maintenance", self)
        db_maintenance_action.setIcon(QIcon(":/icons/database.png"))
        db_maintenance_action.triggered.connect(self._show_db_maintenance)
        tools_menu.addAction(db_maintenance_action)

        # Help Menu
        help_menu = self.menu_bar.addMenu("مساعدة" if self.is_rtl else "Help")

        # User Manual
        manual_action = QAction("دليل المستخدم" if self.is_rtl else "User Manual", self)
        manual_action.setShortcut(QKeySequence.StandardKey.HelpContents)
        manual_action.setIcon(QIcon(":/icons/help.png"))
        manual_action.triggered.connect(self._show_help)
        help_menu.addAction(manual_action)

        # Keyboard Shortcuts
        shortcuts_action = QAction("اختصارات لوحة المفاتيح" if self.is_rtl else "Keyboard Shortcuts", self)
        shortcuts_action.triggered.connect(self._show_shortcuts)
        help_menu.addAction(shortcuts_action)

        help_menu.addSeparator()

        # Check for Updates
        update_action = QAction("التحقق من التحديثات" if self.is_rtl else "Check for Updates", self)
        update_action.setIcon(QIcon(":/icons/update.png"))
        update_action.triggered.connect(self._check_updates)
        help_menu.addAction(update_action)

        # About
        about_action = QAction("حول البرنامج" if self.is_rtl else "About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _create_tool_bar(self):
        """Create the application tool bar."""
        self.tool_bar = self.addToolBar("أدوات سريعة" if self.is_rtl else "Quick Tools")
        self.tool_bar.setMovable(False)
        self.tool_bar.setIconSize(QSize(24, 24))

        # Search widget
        search_label = QLabel("بحث:" if self.is_rtl else "Search:")
        self.tool_bar.addWidget(search_label)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(
            "بحث عن عميل..." if self.is_rtl else "Search for client..."
        )
        self.search_edit.setMaximumWidth(200)
        self.search_edit.textChanged.connect(self._on_search_changed)
        self.tool_bar.addWidget(self.search_edit)

        self.tool_bar.addSeparator()

        # Quick actions
        new_client_btn = QPushButton("عميل جديد" if self.is_rtl else "New Client")
        new_client_btn.setIcon(QIcon(":/icons/user_add.png"))
        new_client_btn.clicked.connect(self._new_client)
        self.tool_bar.addWidget(new_client_btn)

        new_diet_btn = QPushButton("خطة غذائية" if self.is_rtl else "Diet Plan")
        new_diet_btn.setIcon(QIcon(":/icons/diet.png"))
        new_diet_btn.clicked.connect(self._new_diet_plan)
        self.tool_bar.addWidget(new_diet_btn)

        generate_report_btn = QPushButton("تقرير" if self.is_rtl else "Report")
        generate_report_btn.setIcon(QIcon(":/icons/report.png"))
        generate_report_btn.clicked.connect(self._quick_report)
        self.tool_bar.addWidget(generate_report_btn)

        self.tool_bar.addSeparator()

        # User info
        self.user_label = QLabel("غير مسجل الدخول" if self.is_rtl else "Not logged in")
        self.tool_bar.addWidget(self.user_label)

        # Logout button
        self.logout_btn = QPushButton("تسجيل الخروج" if self.is_rtl else "Logout")
        self.logout_btn.setIcon(QIcon(":/icons/logout.png"))
        self.logout_btn.clicked.connect(self._logout)
        self.logout_btn.setVisible(False)
        self.tool_bar.addWidget(self.logout_btn)

    def _create_central_widget(self):
        """Create the central widget with tab interface."""
        # Create central stack for login/main interface switching
        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)

        # Main interface widget
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Tab widget for different modules
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setMovable(True)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        # Dashboard Tab
        self.dashboard_widget = DashboardWidget()
        self.tab_widget.addTab(
            self.dashboard_widget,
            "لوحة المعلومات" if self.is_rtl else "Dashboard"
        )

        # Client Management Tab
        self.client_widget = ClientWidget()
        self.tab_widget.addTab(
            self.client_widget,
            "إدارة العملاء" if self.is_rtl else "Client Management"
        )

        # Diet & Nutrition Tab
        self.diet_widget = DietWidget()
        self.tab_widget.addTab(
            self.diet_widget,
            "التغذية والحمية" if self.is_rtl else "Diet & Nutrition"
        )

        main_layout.addWidget(self.tab_widget)

        # Add main widget to stack
        self.central_stack.addWidget(main_widget)

        # Initially show main interface (will be hidden until login)
        self.central_stack.setCurrentWidget(main_widget)

    def _create_status_bar(self):
        """Create the application status bar."""
        self.status_bar = self.statusBar()

        # Status message
        self.status_label = QLabel("جاهز" if self.is_rtl else "Ready")
        self.status_bar.addWidget(self.status_label)

        # Progress bar for operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.status_bar.addPermanentWidget(self.progress_bar)

        # Connection status
        self.connection_label = QLabel("متصل" if self.is_rtl else "Connected")
        self.connection_label.setStyleSheet("color: green; font-weight: bold;")
        self.status_bar.addPermanentWidget(self.connection_label)

        # Current date/time
        self.datetime_label = QLabel()
        self._update_datetime()
        self.status_bar.addPermanentWidget(self.datetime_label)

        # Update datetime every minute
        datetime_timer = QTimer(self)
        datetime_timer.timeout.connect(self._update_datetime)
        datetime_timer.start(60000)

    def _apply_theme(self):
        """Apply the current theme to the application."""
        if self.current_theme == 'dark':
            self._apply_dark_theme()
        else:
            self._apply_light_theme()

    def _apply_light_theme(self):
        """Apply light theme styling."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
                color: #333333;
            }

            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: white;
            }

            QTabBar::tab {
                background-color: #e0e0e0;
                border: 1px solid #cccccc;
                border-bottom: none;
                padding: 8px 16px;
                margin-right: 2px;
            }

            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }

            QTabBar::tab:hover {
                background-color: #f0f0f0;
            }

            QToolBar {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                spacing: 8px;
                padding: 4px;
            }

            QStatusBar {
                background-color: #f8f8f8;
                border-top: 1px solid #e0e0e0;
            }

            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: 500;
            }

            QPushButton:hover {
                background-color: #1976D2;
            }

            QPushButton:pressed {
                background-color: #0D47A1;
            }

            QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: white;
            }

            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)

    def _apply_dark_theme(self):
        """Apply dark theme styling."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }

            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #3c3c3c;
            }

            QTabBar::tab {
                background-color: #404040;
                border: 1px solid #555555;
                border-bottom: none;
                padding: 8px 16px;
                margin-right: 2px;
                color: #ffffff;
            }

            QTabBar::tab:selected {
                background-color: #3c3c3c;
                border-bottom: 1px solid #3c3c3c;
            }

            QTabBar::tab:hover {
                background-color: #4a4a4a;
            }

            QToolBar {
                background-color: #333333;
                border: 1px solid #555555;
                color: #ffffff;
            }

            QStatusBar {
                background-color: #2a2a2a;
                border-top: 1px solid #555555;
                color: #ffffff;
            }

            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: 500;
            }

            QPushButton:hover {
                background-color: #1976D2;
            }

            QLineEdit {
                border: 1px solid #666666;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: #404040;
                color: #ffffff;
            }

            QLineEdit:focus {
                border: 2px solid #2196F3;
            }

            QLabel {
                color: #ffffff;
            }
        """)

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Tab switching shortcuts
        for i in range(1, 10):
            shortcut = QKeySequence(f"Ctrl+{i}")
            action = QAction(self)
            action.setShortcut(shortcut)
            action.triggered.connect(lambda checked, index=i-1: self._switch_to_tab(index))
            self.addAction(action)

    def _setup_auto_save(self):
        """Setup auto-save functionality."""
        auto_save_interval = self.settings.get('app.auto_save_interval', 300)  # 5 minutes
        if auto_save_interval > 0:
            self.auto_save_timer.start(auto_save_interval * 1000)

    def _setup_system_tray(self):
        """Setup system tray icon and menu."""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)

            # Try to set icon with fallback
            icon = QIcon(":/icons/pharmacy.png")
            if icon.isNull():
                # Create a simple fallback icon
                from PyQt6.QtGui import QPixmap, QPainter, QBrush
                pixmap = QPixmap(16, 16)
                pixmap.fill(Qt.GlobalColor.blue)
                painter = QPainter(pixmap)
                painter.setBrush(QBrush(Qt.GlobalColor.white))
                painter.drawEllipse(2, 2, 12, 12)
                painter.end()
                icon = QIcon(pixmap)

            self.tray_icon.setIcon(icon)

            # Tray menu
            tray_menu = QMenu()

            show_action = tray_menu.addAction("إظهار" if self.is_rtl else "Show")
            show_action.triggered.connect(self.show)

            hide_action = tray_menu.addAction("إخفاء" if self.is_rtl else "Hide")
            hide_action.triggered.connect(self.hide)

            tray_menu.addSeparator()

            quit_action = tray_menu.addAction("خروج" if self.is_rtl else "Quit")
            quit_action.triggered.connect(QApplication.instance().quit)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self._on_tray_activated)
            self.tray_icon.show()

    def _connect_signals(self):
        """Connect widget signals to handlers."""
        # Dashboard signals
        if self.dashboard_widget:
            self.dashboard_widget.quick_action_triggered.connect(self._handle_quick_action)
            self.dashboard_widget.client_selected.connect(self._select_client)

        # Client widget signals
        if self.client_widget:
            self.client_widget.client_selected.connect(self._select_client)
            self.client_widget.client_saved.connect(self._on_client_saved)
            self.client_widget.client_deleted.connect(self._on_client_deleted)

        # Diet widget signals
        if self.diet_widget:
            self.diet_widget.diet_record_saved.connect(self._on_diet_record_saved)
            self.diet_widget.nutrition_calculated.connect(self._on_nutrition_calculated)

    def _show_login_dialog(self):
        """Show the login dialog."""
        if not self.current_user:
            login_dialog = LoginDialog(self)
            login_dialog.login_successful.connect(self._on_login_successful)
            login_dialog.language_changed.connect(self._on_language_changed)
            login_dialog.theme_changed.connect(self._on_theme_changed)

            if login_dialog.exec() != QDialog.DialogCode.Accepted:
                # User cancelled login, exit application
                QApplication.instance().quit()

    def _on_login_successful(self, user_data: Dict[str, Any]):
        """Handle successful login."""
        self.current_user = user_data
        self.user_logged_in.emit(user_data)

        # Update UI
        self._update_user_interface()

        # Set user in widgets
        if self.dashboard_widget:
            self.dashboard_widget.set_current_user(user_data)

        # Show welcome message
        username = user_data.get('username', 'User')
        self.show_message(
            f"مرحباً {username}!" if self.is_rtl else f"Welcome {username}!",
            3000
        )

    def _update_user_interface(self):
        """Update UI based on current user."""
        if self.current_user:
            # Update user label in toolbar
            username = self.current_user.get('username', 'User')
            self.user_label.setText(f"مرحباً {username}" if self.is_rtl else f"Hello {username}")
            self.logout_btn.setVisible(True)

            # Enable/disable menu items based on user role
            self._update_menu_permissions()
        else:
            self.user_label.setText("غير مسجل الدخول" if self.is_rtl else "Not logged in")
            self.logout_btn.setVisible(False)

    def _update_menu_permissions(self):
        """Update menu item permissions based on user role."""
        if not self.current_user:
            return

        user_role = self.current_user.get('role', 'viewer')

        # Enable/disable menu items based on role
        # TODO: Implement role-based permissions
        pass

    def _logout(self):
        """Handle user logout."""
        reply = QMessageBox.question(
            self,
            "تأكيد تسجيل الخروج" if self.is_rtl else "Confirm Logout",
            "هل أنت متأكد من تسجيل الخروج؟" if self.is_rtl else "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Save any pending data
            self._auto_save()

            # Clear current user
            self.current_user = None
            self.user_logged_out.emit()

            # Update UI
            self._update_user_interface()

            # Show login dialog again
            self._show_login_dialog()

    def _auto_save(self):
        """Perform auto-save of current data."""
        try:
            # Save current tab data
            current_widget = self.tab_widget.currentWidget()
            if hasattr(current_widget, 'save_data'):
                current_widget.save_data()

            # Save window state
            self._save_window_state()

        except Exception as e:
            print(f"Auto-save error: {e}")

    def _save_window_state(self):
        """Save window geometry and state."""
        self.settings.set('window.geometry', self.saveGeometry())
        self.settings.set('window.state', self.saveState())

    def _focus_search(self):
        """Focus the search field."""
        if self.search_edit:
            self.search_edit.setFocus()
            self.search_edit.selectAll()

    def _switch_to_tab(self, index: int):
        """Switch to a specific tab."""
        if 0 <= index < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(index)

    def _toggle_theme(self):
        """Toggle between light and dark themes."""
        new_theme = 'dark' if self.current_theme == 'light' else 'light'
        self.current_theme = new_theme
        self.settings.set('ui.theme', new_theme)
        self._apply_theme()
        self.theme_changed.emit(new_theme)

    def _toggle_language(self):
        """Toggle between Arabic and English."""
        new_language = 'en' if self.current_language == 'ar' else 'ar'
        self._change_language(new_language)

    def _change_language(self, language_code: str):
        """Change the application language."""
        self.current_language = language_code
        self.is_rtl = language_code == 'ar'
        self.settings.set('ui.language', language_code)

        # Update layout direction
        if self.is_rtl:
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        self.language_changed.emit(language_code)

        # Note: Full language change would require recreating UI elements
        # For now, just emit signal for other components to handle
        self.show_message(
            "يرجى إعادة تشغيل البرنامج لتطبيق تغيير اللغة" if self.is_rtl
            else "Please restart the application to apply language change"
        )

    def _toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _show_settings(self):
        """Show application settings dialog."""
        # TODO: Implement settings dialog
        self.show_message("قريباً - نافذة الإعدادات" if self.is_rtl else "Coming Soon - Settings Dialog")

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "حول البرنامج" if self.is_rtl else "About",
            """
            <h3>نظام إدارة الصيدلية</h3>
            <p>نسخة 2.0</p>
            <p>نظام شامل لإدارة التغذية والصحة في الصيدليات</p>
            """ if self.is_rtl else """
            <h3>Pharmacy Management System</h3>
            <p>Version 2.0</p>
            <p>Comprehensive nutrition and health management system for pharmacies</p>
            """
        )

    # Event handlers for main operations
    def _new_client(self):
        """Create a new client."""
        self._switch_to_tab(1)  # Switch to client tab
        if self.client_widget:
            self.client_widget._new_client()

    def _open_client(self):
        """Open client selection dialog."""
        # TODO: Implement client selection dialog
        self.show_message("قريباً - نافذة اختيار العميل" if self.is_rtl else "Coming Soon - Client Selection Dialog")

    def _select_client(self, client_id: int):
        """Select a client and update all widgets."""
        self.current_client_id = client_id
        self.client_selected.emit(client_id)

        # Update diet widget with selected client
        if self.diet_widget:
            self.diet_widget.set_client(client_id)

    def _new_diet_plan(self):
        """Create a new diet plan."""
        if not self.current_client_id:
            self.show_warning("يرجى تحديد عميل أولاً" if self.is_rtl else "Please select a client first")
            return

        self._switch_to_tab(2)  # Switch to diet tab

    def _quick_report(self):
        """Generate a quick report."""
        if not self.current_client_id:
            self.show_warning("يرجى تحديد عميل أولاً" if self.is_rtl else "Please select a client first")
            return

        # TODO: Implement quick report generation
        self.show_message("قريباً - إنشاء التقارير السريعة" if self.is_rtl else "Coming Soon - Quick Report Generation")

    def _on_search_changed(self, text: str):
        """Handle search text changes."""
        # TODO: Implement real-time search
        pass

    def _on_tab_changed(self, index: int):
        """Handle tab change."""
        # Refresh data in the new tab
        current_widget = self.tab_widget.currentWidget()
        if hasattr(current_widget, 'refresh_data'):
            current_widget.refresh_data()

    def _handle_quick_action(self, action_name: str, action_data: Dict[str, Any]):
        """Handle quick actions from dashboard."""
        if action_name == "new_client":
            self._new_client()
        elif action_name == "new_appointment":
            self.show_message("قريباً - نظام المواعيد" if self.is_rtl else "Coming Soon - Appointment System")
        elif action_name == "diet_plan":
            self._new_diet_plan()
        elif action_name == "generate_report":
            self._quick_report()
        elif action_name == "backup_data":
            self._create_backup()
        elif action_name == "user_management":
            self._show_user_management()

    def _on_client_saved(self, client_data: Dict[str, Any]):
        """Handle client saved event."""
        # Refresh dashboard
        if self.dashboard_widget:
            self.dashboard_widget.refresh_data()

    def _on_client_deleted(self, client_id: int):
        """Handle client deleted event."""
        if self.current_client_id == client_id:
            self.current_client_id = None

        # Refresh dashboard
        if self.dashboard_widget:
            self.dashboard_widget.refresh_data()

    def _on_diet_record_saved(self, diet_data: Dict[str, Any]):
        """Handle diet record saved event."""
        # Refresh dashboard
        if self.dashboard_widget:
            self.dashboard_widget.refresh_data()

    def _on_nutrition_calculated(self, nutrition_data: Dict[str, Any]):
        """Handle nutrition calculation event."""
        # Update status bar with nutrition info
        calories = nutrition_data.get('calories', 0)
        self.show_message(f"السعرات: {calories:.0f}" if self.is_rtl else f"Calories: {calories:.0f}")

    def _on_language_changed(self, language_code: str):
        """Handle language change from login dialog."""
        self._change_language(language_code)

    def _on_theme_changed(self, theme_name: str):
        """Handle theme change from login dialog."""
        self.current_theme = theme_name
        self.settings.set('ui.theme', theme_name)
        self._apply_theme()
        self.theme_changed.emit(theme_name)

    def _update_datetime(self):
        """Update the date/time display in status bar."""
        now = datetime.now()
        if self.is_rtl:
            date_str = now.strftime("%d/%m/%Y %H:%M")
        else:
            date_str = now.strftime("%m/%d/%Y %H:%M")
        self.datetime_label.setText(date_str)

    def _update_status_info(self):
        """Update status bar information."""
        # Update connection status
        try:
            if self.client_controller.test_connection():
                self.connection_label.setText("متصل" if self.is_rtl else "Connected")
                self.connection_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.connection_label.setText("غير متصل" if self.is_rtl else "Disconnected")
                self.connection_label.setStyleSheet("color: red; font-weight: bold;")
        except:
            self.connection_label.setText("خطأ" if self.is_rtl else "Error")
            self.connection_label.setStyleSheet("color: orange; font-weight: bold;")

    def _on_tray_activated(self, reason):
        """Handle system tray activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()
                self.raise_()

    # Utility methods
    def show_message(self, message: str, timeout: int = 2000):
        """Show a message in the status bar."""
        self.status_bar.showMessage(message, timeout)

    def show_progress(self, text: str = ""):
        """Show progress bar with optional text."""
        if text:
            self.status_label.setText(text)
        self.progress_bar.setVisible(True)

    def hide_progress(self):
        """Hide progress bar."""
        self.progress_bar.setVisible(False)
        self.status_label.setText("جاهز" if self.is_rtl else "Ready")

    def show_error(self, message: str):
        """Show error message dialog."""
        QMessageBox.critical(
            self,
            "خطأ" if self.is_rtl else "Error",
            message
        )

    def show_warning(self, message: str):
        """Show warning message dialog."""
        QMessageBox.warning(
            self,
            "تحذير" if self.is_rtl else "Warning",
            message
        )

    def show_information(self, message: str):
        """Show information message dialog."""
        QMessageBox.information(
            self,
            "معلومات" if self.is_rtl else "Information",
            message
        )

    def ask_question(self, title: str, message: str) -> QMessageBox.StandardButton:
        """Show question dialog and return user response."""
        return QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

    # Placeholder methods for future implementation
    def _import_data(self):
        """Import data from file."""
        self.show_message("قريباً - استيراد البيانات" if self.is_rtl else "Coming Soon - Data Import")

    def _export_data(self):
        """Export data to file."""
        self.show_message("قريباً - تصدير البيانات" if self.is_rtl else "Coming Soon - Data Export")

    def _create_backup(self):
        """Create data backup."""
        self.show_message("قريباً - النسخ الاحتياطي" if self.is_rtl else "Coming Soon - Backup Creation")

    def _restore_backup(self):
        """Restore from backup."""
        self.show_message("قريباً - استعادة النسخ الاحتياطية" if self.is_rtl else "Coming Soon - Backup Restoration")

    def _generate_client_report(self):
        """Generate client report."""
        self.show_message("قريباً - تقرير العميل" if self.is_rtl else "Coming Soon - Client Report")

    def _generate_nutrition_report(self):
        """Generate nutrition report."""
        self.show_message("قريباً - تقرير التغذية" if self.is_rtl else "Coming Soon - Nutrition Report")

    def _generate_statistics_report(self):
        """Generate statistics report."""
        self.show_message("قريباً - تقرير الإحصائيات" if self.is_rtl else "Coming Soon - Statistics Report")

    def _show_bmi_calculator(self):
        """Show BMI calculator."""
        self.show_message("قريباً - حاسبة مؤشر كتلة الجسم" if self.is_rtl else "Coming Soon - BMI Calculator")

    def _show_calorie_calculator(self):
        """Show calorie calculator."""
        self.show_message("قريباً - حاسبة السعرات" if self.is_rtl else "Coming Soon - Calorie Calculator")

    def _show_user_management(self):
        """Show user management dialog."""
        self.show_message("قريباً - إدارة المستخدمين" if self.is_rtl else "Coming Soon - User Management")

    def _show_db_maintenance(self):
        """Show database maintenance dialog."""
        self.show_message("قريباً - صيانة قاعدة البيانات" if self.is_rtl else "Coming Soon - Database Maintenance")

    def _show_help(self):
        """Show help documentation."""
        self.show_message("قريباً - دليل المستخدم" if self.is_rtl else "Coming Soon - User Manual")

    def _show_shortcuts(self):
        """Show keyboard shortcuts dialog."""
        self.show_message("قريباً - اختصارات لوحة المفاتيح" if self.is_rtl else "Coming Soon - Keyboard Shortcuts")

    def _check_updates(self):
        """Check for application updates."""
        self.show_message("قريباً - التحقق من التحديثات" if self.is_rtl else "Coming Soon - Update Check")

    def closeEvent(self, event: QCloseEvent):
        """Handle application close event."""
        # Save current data
        self._auto_save()

        # Ask for confirmation if there are unsaved changes
        reply = QMessageBox.question(
            self,
            "إغلاق البرنامج" if self.is_rtl else "Close Application",
            "هل أنت متأكد من إغلاق البرنامج؟" if self.is_rtl else "Are you sure you want to close the application?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Hide to system tray if available
            if self.tray_icon and self.tray_icon.isVisible():
                self.hide()
                event.ignore()
                if not self.settings.get('app.tray_notification_shown', False):
                    self.tray_icon.showMessage(
                        "نظام إدارة الصيدلية" if self.is_rtl else "Pharmacy Management System",
                        "تم تصغير البرنامج إلى علبة النظام" if self.is_rtl else "Application minimized to system tray"
                    )
                    self.settings.set('app.tray_notification_shown', True)
            else:
                event.accept()
        else:
            event.ignore()
