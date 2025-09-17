"""
Base Controller
Provides base controller class and common functionality for the Pharmacy Management System
"""

from typing import Any, Dict, Optional, List, Callable
from PyQt6.QtCore import QObject, pyqtSignal
from loguru import logger

from models.base import DatabaseManager, get_database_manager
from config.simple_settings import get_settings


class BaseController(QObject):
    """
    Base controller class that provides common functionality for all controllers
    """

    # Common signals for UI updates
    data_changed = pyqtSignal(str, dict)  # (operation, data)
    error_occurred = pyqtSignal(str, str)  # (title, message)
    success_occurred = pyqtSignal(str, str)  # (title, message)
    progress_updated = pyqtSignal(int)  # progress percentage
    status_changed = pyqtSignal(str)  # status message

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.db_manager = get_database_manager()
        self.settings = get_settings()
        self._initialized = False
        self._event_handlers: Dict[str, List[Callable]] = {}

    def initialize(self) -> bool:
        """
        Initialize the controller. Should be called after construction.

        Returns:
            bool: True if initialization successful
        """
        try:
            if self._initialized:
                return True

            success = self._do_initialize()
            if success:
                self._initialized = True
                logger.info(f"{self.__class__.__name__} initialized successfully")
            else:
                logger.error(f"Failed to initialize {self.__class__.__name__}")

            return success

        except Exception as e:
            logger.error(f"Error initializing {self.__class__.__name__}: {e}")
            self.emit_error("Initialization Error", f"Failed to initialize controller: {str(e)}")
            return False

    def _do_initialize(self) -> bool:
        """
        Perform controller-specific initialization.
        Must be implemented by subclasses.

        Returns:
            bool: True if initialization successful
        """
        return True

    def is_initialized(self) -> bool:
        """Check if controller is initialized"""
        return self._initialized

    def emit_error(self, title: str, message: str) -> None:
        """Emit error signal"""
        logger.error(f"{title}: {message}")
        self.error_occurred.emit(title, message)

    def emit_success(self, title: str, message: str) -> None:
        """Emit success signal"""
        logger.info(f"{title}: {message}")
        self.success_occurred.emit(title, message)

    def emit_data_changed(self, operation: str, data: Dict[str, Any]) -> None:
        """Emit data changed signal"""
        logger.debug(f"Data changed: {operation}")
        self.data_changed.emit(operation, data)

    def emit_progress(self, percentage: int) -> None:
        """Emit progress update signal"""
        self.progress_updated.emit(percentage)

    def emit_status(self, status: str) -> None:
        """Emit status change signal"""
        self.status_changed.emit(status)

    def register_event_handler(self, event: str, handler: Callable) -> None:
        """
        Register an event handler for custom events

        Args:
            event: Event name
            handler: Handler function
        """
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)

    def unregister_event_handler(self, event: str, handler: Callable) -> None:
        """
        Unregister an event handler

        Args:
            event: Event name
            handler: Handler function to remove
        """
        if event in self._event_handlers:
            try:
                self._event_handlers[event].remove(handler)
            except ValueError:
                pass

    def emit_custom_event(self, event: str, *args, **kwargs) -> None:
        """
        Emit a custom event to registered handlers

        Args:
            event: Event name
            *args: Event arguments
            **kwargs: Event keyword arguments
        """
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                try:
                    handler(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in event handler for {event}: {e}")

    def validate_input(self, data: Dict[str, Any], validation_rules: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate input data against rules

        Args:
            data: Data to validate
            validation_rules: Validation rules

        Returns:
            dict: Validation result with errors and warnings
        """
        errors = []
        warnings = []

        for field, rules in validation_rules.items():
            value = data.get(field)

            # Check required fields
            if rules.get('required', False) and not value:
                errors.append(f"Field '{field}' is required")
                continue

            if value is not None:
                # Check data type
                expected_type = rules.get('type')
                if expected_type and not isinstance(value, expected_type):
                    try:
                        # Try to convert
                        data[field] = expected_type(value)
                    except (ValueError, TypeError):
                        errors.append(f"Field '{field}' must be of type {expected_type.__name__}")
                        continue

                # Check length constraints
                if isinstance(value, str):
                    min_length = rules.get('min_length')
                    max_length = rules.get('max_length')

                    if min_length and len(value) < min_length:
                        errors.append(f"Field '{field}' must be at least {min_length} characters")

                    if max_length and len(value) > max_length:
                        errors.append(f"Field '{field}' must not exceed {max_length} characters")

                # Check numeric constraints
                if isinstance(value, (int, float)):
                    min_value = rules.get('min_value')
                    max_value = rules.get('max_value')

                    if min_value is not None and value < min_value:
                        errors.append(f"Field '{field}' must be at least {min_value}")

                    if max_value is not None and value > max_value:
                        errors.append(f"Field '{field}' must not exceed {max_value}")

                # Check custom validation function
                validator = rules.get('validator')
                if validator and callable(validator):
                    if not validator(value):
                        errors.append(f"Field '{field}' failed validation")

        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'data': data
        }

    def handle_database_error(self, error: Exception, operation: str) -> None:
        """
        Handle database errors consistently

        Args:
            error: The exception that occurred
            operation: Description of the operation that failed
        """
        error_msg = str(error)
        logger.error(f"Database error during {operation}: {error_msg}")

        # Emit user-friendly error message
        if "UNIQUE constraint failed" in error_msg:
            self.emit_error("Duplicate Data", "This record already exists in the database.")
        elif "FOREIGN KEY constraint failed" in error_msg:
            self.emit_error("Data Relationship Error", "Cannot perform this operation due to data relationships.")
        elif "database is locked" in error_msg:
            self.emit_error("Database Busy", "Database is currently busy. Please try again.")
        else:
            self.emit_error("Database Error", f"An error occurred while {operation}: {error_msg}")

    def execute_with_progress(self, operation: Callable, *args, **kwargs) -> Any:
        """
        Execute an operation with progress feedback

        Args:
            operation: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Any: Operation result
        """
        try:
            self.emit_progress(0)
            self.emit_status("Starting operation...")

            result = operation(*args, **kwargs)

            self.emit_progress(100)
            self.emit_status("Operation completed")

            return result

        except Exception as e:
            self.emit_progress(0)
            self.emit_status("Operation failed")
            raise e

    def batch_operation(self, items: List[Any], operation: Callable,
                       batch_size: int = 50, progress_callback: Optional[Callable] = None) -> List[Any]:
        """
        Execute batch operations with progress tracking

        Args:
            items: List of items to process
            operation: Operation to perform on each item
            batch_size: Number of items to process in each batch
            progress_callback: Optional progress callback function

        Returns:
            List[Any]: Results of operations
        """
        results = []
        total_items = len(items)

        try:
            for i in range(0, total_items, batch_size):
                batch = items[i:i + batch_size]
                batch_results = []

                for j, item in enumerate(batch):
                    try:
                        result = operation(item)
                        batch_results.append(result)

                        # Update progress
                        progress = int(((i + j + 1) / total_items) * 100)
                        self.emit_progress(progress)

                        if progress_callback:
                            progress_callback(progress, i + j + 1, total_items)

                    except Exception as e:
                        logger.error(f"Error processing item {i + j}: {e}")
                        batch_results.append(None)

                results.extend(batch_results)

                # Allow GUI to update between batches
                if hasattr(self, 'app') and self.app:
                    self.app.processEvents()

            return results

        except Exception as e:
            logger.error(f"Batch operation failed: {e}")
            raise e

    def get_setting(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a setting value

        Args:
            section: Settings section
            key: Setting key
            default: Default value if not found

        Returns:
            Any: Setting value
        """
        try:
            section_obj = getattr(self.settings, section, None)
            if section_obj:
                return getattr(section_obj, key, default)
            return default
        except Exception:
            return default

    def update_setting(self, section: str, key: str, value: Any) -> bool:
        """
        Update a setting value

        Args:
            section: Settings section
            key: Setting key
            value: New value

        Returns:
            bool: True if successful
        """
        try:
            from config.simple_settings import get_settings_manager
            return get_settings_manager().update_setting(section, key, value)
        except Exception as e:
            logger.error(f"Failed to update setting {section}.{key}: {e}")
            return False

    def cleanup(self) -> None:
        """
        Cleanup resources when controller is destroyed
        """
        try:
            self._event_handlers.clear()
            logger.info(f"{self.__class__.__name__} cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup of {self.__class__.__name__}: {e}")

    def __del__(self):
        """Destructor"""
        self.cleanup()


class ControllerManager:
    """
    Manages controller instances and provides centralized access
    """

    def __init__(self):
        self._controllers: Dict[str, BaseController] = {}
        self._initialization_order: List[str] = []

    def register_controller(self, name: str, controller: BaseController,
                          dependencies: List[str] = None) -> None:
        """
        Register a controller

        Args:
            name: Controller name
            controller: Controller instance
            dependencies: List of controller names this depends on
        """
        self._controllers[name] = controller

        # Handle initialization order based on dependencies
        if dependencies:
            for dep in dependencies:
                if dep not in self._initialization_order:
                    self._initialization_order.append(dep)

        if name not in self._initialization_order:
            self._initialization_order.append(name)

    def get_controller(self, name: str) -> Optional[BaseController]:
        """
        Get a controller by name

        Args:
            name: Controller name

        Returns:
            BaseController: Controller instance or None
        """
        return self._controllers.get(name)

    def initialize_all(self) -> bool:
        """
        Initialize all controllers in dependency order

        Returns:
            bool: True if all controllers initialized successfully
        """
        success = True

        for name in self._initialization_order:
            controller = self._controllers.get(name)
            if controller and not controller.is_initialized():
                if not controller.initialize():
                    logger.error(f"Failed to initialize controller: {name}")
                    success = False

        return success

    def cleanup_all(self) -> None:
        """Cleanup all controllers"""
        for controller in self._controllers.values():
            controller.cleanup()

        self._controllers.clear()
        self._initialization_order.clear()


# Global controller manager instance
_controller_manager = None

def get_controller_manager() -> ControllerManager:
    """Get the global controller manager instance"""
    global _controller_manager
    if _controller_manager is None:
        _controller_manager = ControllerManager()
    return _controller_manager

def get_controller(name: str) -> Optional[BaseController]:
    """Get a controller by name from the global manager"""
    return get_controller_manager().get_controller(name)
