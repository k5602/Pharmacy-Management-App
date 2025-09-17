#!/usr/bin/env python3
"""
Pharmacy Management System v2.0 - Main Entry Point

This is the main entry point for the Pharmacy Management Application Phase 3.
It initializes the application, sets up logging, handles exceptions, and
manages the overall application lifecycle.

Features:
- PyQt6 application initialization
- Exception handling and logging
- Resource management
- Database initialization
- Application settings management
- Graceful shutdown handling
"""

import sys
import os
import traceback
import logging
from pathlib import Path
from typing import Optional

# Add the src directory to Python path for imports
current_dir = Path(__file__).parent
src_dir = current_dir
sys.path.insert(0, str(src_dir))

# PyQt6 imports
from PyQt6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt6.QtCore import Qt, QTimer, QThread, QObject, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont, QIcon

# Application imports
from views.main_window import MainWindow
from config.settings import AppSettings
from utils.resource_manager import ResourceManager
from controllers.auth import AuthController
from models.base import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pharmacy_management.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class ApplicationInitializer(QObject):
    """
    Background application initializer to handle heavy startup tasks.
    """

    initialization_complete = pyqtSignal(bool, str)  # success, message
    progress_updated = pyqtSignal(str, int)  # message, percentage

    def __init__(self):
        super().__init__()
        self.settings = AppSettings()
        self.resource_manager = ResourceManager()
        self.db_manager = DatabaseManager()

    def initialize(self):
        """Perform application initialization tasks."""
        try:
            # Step 1: Initialize settings
            self.progress_updated.emit("تحميل الإعدادات..." if self._is_rtl() else "Loading settings...", 10)
            self.settings.load()

            # Step 2: Initialize resource manager
            self.progress_updated.emit("تحميل الموارد..." if self._is_rtl() else "Loading resources...", 30)
            # ResourceManager initializes in constructor, no separate initialize method needed

            # Step 3: Initialize database
            self.progress_updated.emit("تهيئة قاعدة البيانات..." if self._is_rtl() else "Initializing database...", 50)
            # DatabaseManager initializes in constructor, no separate initialize method needed

            # Step 4: Check database connection
            self.progress_updated.emit("فحص الاتصال..." if self._is_rtl() else "Testing connection...", 70)
            if not self.db_manager.test_connection():
                raise Exception("Database connection failed")

            # Step 5: Create default admin user if needed
            self.progress_updated.emit("إعداد المستخدم الافتراضي..." if self._is_rtl() else "Setting up default user...", 85)
            auth_controller = AuthController()

            # Step 6: Final setup
            self.progress_updated.emit("إنهاء التحضير..." if self._is_rtl() else "Finalizing setup...", 100)

            self.initialization_complete.emit(True, "Initialization successful")

        except Exception as e:
            error_msg = f"Initialization failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.initialization_complete.emit(False, error_msg)

    def _is_rtl(self) -> bool:
        """Check if current language is RTL."""
        return self.settings.get('ui.language', 'ar') == 'ar'


class PharmacyManagementApp(QApplication):
    """
    Main application class extending QApplication.

    Handles application-wide events, settings, and lifecycle management.
    """

    def __init__(self, argv):
        super().__init__(argv)

        # Application metadata
        self.setApplicationName("Pharmacy Management System")
        self.setApplicationVersion("2.0.0")
        self.setOrganizationName("Pharmacy Solutions")
        self.setOrganizationDomain("pharmacy-solutions.com")

        # Application settings
        self.settings = AppSettings()
        self.resource_manager = ResourceManager()

        # UI components
        self.main_window: Optional[MainWindow] = None
        self.splash_screen: Optional[QSplashScreen] = None
        self.initializer: Optional[ApplicationInitializer] = None
        self.init_thread: Optional[QThread] = None

        # Setup application
        self._setup_application()
        self._setup_error_handling()
        self._show_splash_screen()
        self._initialize_application()

    def _setup_application(self):
        """Setup basic application properties."""
        # Set application icon
        app_icon = QIcon(":/icons/pharmacy.png")
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)

        # Set application font
        language = self.settings.get('ui.language', 'ar')
        if language == 'ar':
            font_family = self.settings.get('ui.arabic_font', 'Tahoma')
        else:
            font_family = self.settings.get('ui.english_font', 'Segoe UI')

        font = QFont(font_family, 10)
        self.setFont(font)

        # Set style
        self.setStyle('Fusion')  # Use Fusion style for better cross-platform appearance

        # Enable high DPI scaling (PyQt6 compatible)
        try:
            self.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
            self.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        except AttributeError:
            # These attributes may not exist in all PyQt6 versions
            pass

        logger.info("Application setup completed")

    def _setup_error_handling(self):
        """Setup global error handling."""
        # Install custom exception handler
        sys.excepthook = self._handle_exception

        # Handle Qt warnings and errors
        def qt_message_handler(mode, context, message):
            if mode == Qt.QtMsgType.QtCriticalMsg or mode == Qt.QtMsgType.QtFatalMsg:
                logger.error(f"Qt Error: {message}")
            elif mode == Qt.QtMsgType.QtWarningMsg:
                logger.warning(f"Qt Warning: {message}")
            else:
                logger.debug(f"Qt Message: {message}")

        # Note: qInstallMessageHandler would be used in a real implementation
        # but it's not available in all PyQt6 versions

    def _handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Handle Ctrl+C gracefully
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # Log the exception
        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.critical(f"Uncaught exception: {error_msg}")

        # Show error dialog
        language = self.settings.get('ui.language', 'ar')
        is_rtl = language == 'ar'

        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Icon.Critical)
        error_dialog.setWindowTitle("خطأ خطير" if is_rtl else "Critical Error")
        error_dialog.setText(
            "حدث خطأ غير متوقع في البرنامج" if is_rtl
            else "An unexpected error occurred in the application"
        )
        error_dialog.setDetailedText(str(exc_value))
        error_dialog.setStandardButtons(
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Close
        )

        result = error_dialog.exec()

        # Close application if user chooses to
        if result == QMessageBox.StandardButton.Close:
            self.quit()

    def _show_splash_screen(self):
        """Show application splash screen during initialization."""
        # Create splash screen
        splash_pixmap = QPixmap(400, 300)
        splash_pixmap.fill(Qt.GlobalColor.white)

        self.splash_screen = QSplashScreen(splash_pixmap)
        self.splash_screen.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint
        )

        # Show splash with initial message
        language = self.settings.get('ui.language', 'ar')
        is_rtl = language == 'ar'

        initial_message = "تحميل نظام إدارة الصيدلية..." if is_rtl else "Loading Pharmacy Management System..."
        self.splash_screen.showMessage(
            initial_message,
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
            Qt.GlobalColor.black
        )

        self.splash_screen.show()
        self.processEvents()  # Ensure splash screen is shown

        logger.info("Splash screen displayed")

    def _initialize_application(self):
        """Initialize application in background thread."""
        # Create initializer
        self.initializer = ApplicationInitializer()
        self.init_thread = QThread()

        # Move initializer to thread
        self.initializer.moveToThread(self.init_thread)

        # Connect signals
        self.init_thread.started.connect(self.initializer.initialize)
        self.initializer.progress_updated.connect(self._update_splash_progress)
        self.initializer.initialization_complete.connect(self._on_initialization_complete)
        self.initializer.initialization_complete.connect(self.init_thread.quit)
        self.init_thread.finished.connect(self.init_thread.deleteLater)

        # Start initialization
        self.init_thread.start()

        logger.info("Background initialization started")

    def _update_splash_progress(self, message: str, percentage: int):
        """Update splash screen with progress information."""
        if self.splash_screen:
            self.splash_screen.showMessage(
                f"{message} ({percentage}%)",
                Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
                Qt.GlobalColor.black
            )
            self.processEvents()

    def _on_initialization_complete(self, success: bool, message: str):
        """Handle completion of background initialization."""
        if success:
            logger.info("Application initialization completed successfully")
            self._show_main_window()
        else:
            logger.error(f"Application initialization failed: {message}")
            self._show_initialization_error(message)

    def _show_main_window(self):
        """Show the main application window."""
        try:
            # Create main window
            self.main_window = MainWindow()

            # Connect application signals
            self.main_window.user_logged_out.connect(self._handle_logout)

            # Show main window
            self.main_window.show()

            # Hide splash screen
            if self.splash_screen:
                self.splash_screen.finish(self.main_window)
                self.splash_screen = None

            logger.info("Main window displayed")

        except Exception as e:
            logger.error(f"Failed to show main window: {e}", exc_info=True)
            self._show_initialization_error(str(e))

    def _show_initialization_error(self, error_message: str):
        """Show initialization error dialog."""
        language = self.settings.get('ui.language', 'ar')
        is_rtl = language == 'ar'

        # Hide splash screen
        if self.splash_screen:
            self.splash_screen.hide()

        # Show error dialog
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Icon.Critical)
        error_dialog.setWindowTitle("خطأ في التهيئة" if is_rtl else "Initialization Error")
        error_dialog.setText(
            "فشل في تهيئة التطبيق" if is_rtl
            else "Failed to initialize application"
        )
        error_dialog.setDetailedText(error_message)
        error_dialog.setStandardButtons(QMessageBox.StandardButton.Ok)

        error_dialog.exec()

        # Exit application
        self.quit()

    def _handle_logout(self):
        """Handle user logout event."""
        logger.info("User logged out")
        # Could implement additional logout logic here

    def closeAllWindows(self):
        """Override to ensure clean shutdown."""
        logger.info("Closing all windows")

        # Save any pending data
        if self.main_window:
            # Trigger auto-save
            self.main_window._auto_save()

        # Call parent implementation
        super().closeAllWindows()

    def quit(self):
        """Override to ensure clean shutdown."""
        logger.info("Application quit requested")

        # Clean up threads
        try:
            if self.init_thread and self.init_thread.isRunning():
                self.init_thread.quit()
                self.init_thread.wait(3000)  # Wait up to 3 seconds
        except RuntimeError:
            # Thread may have been deleted already
            pass

        # Save settings
        try:
            self.settings.save()
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

        # Call parent implementation
        super().quit()


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)


def check_dependencies():
    """Check if required dependencies are available."""
    required_modules = ['PyQt6', 'sqlalchemy']
    missing_modules = []

    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)

    if missing_modules:
        print(f"Error: Missing required modules: {', '.join(missing_modules)}")
        print("Please install them using: pip install -r requirements.txt")
        sys.exit(1)


def setup_environment():
    """Setup application environment."""
    # Set environment variables for PyQt6
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '0'
    os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'
    os.environ['QT_SCALE_FACTOR_ROUNDING_POLICY'] = 'PassThrough'

    # Create necessary directories
    app_dirs = [
        'logs',
        'data',
        'reports',
        'backups',
        'temp'
    ]

    for dir_name in app_dirs:
        dir_path = Path(dir_name)
        dir_path.mkdir(exist_ok=True)


def main():
    """Main application entry point."""
    try:
        # Pre-flight checks
        check_python_version()
        check_dependencies()

        # Setup environment before creating QApplication
        setup_environment()

        # Create application
        app = PharmacyManagementApp(sys.argv)

        # Set up signal handlers for graceful shutdown
        import signal

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down gracefully")
            app.quit()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Start application event loop
        logger.info("Starting application event loop")
        exit_code = app.exec()

        logger.info(f"Application exited with code {exit_code}")
        return exit_code

    except Exception as e:
        logger.critical(f"Failed to start application: {e}", exc_info=True)

        # Show basic error dialog if possible
        try:
            error_app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
            QMessageBox.critical(
                None,
                "Startup Error",
                f"Failed to start Pharmacy Management System:\n\n{str(e)}"
            )
        except:
            print(f"CRITICAL ERROR: {e}")

        return 1


if __name__ == "__main__":
    sys.exit(main())
