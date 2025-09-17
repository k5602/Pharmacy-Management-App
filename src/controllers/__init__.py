"""
Controllers Package
Exports all controller classes for the Pharmacy Management System
"""

from .base import BaseController, ControllerManager, get_controller_manager, get_controller
from .client import ClientController
from .diet import DietController
from .report import ReportController
from .auth import AuthController, User, Session, UserRole, Permission, SessionStatus

__all__ = [
    # Base controller infrastructure
    'BaseController',
    'ControllerManager',
    'get_controller_manager',
    'get_controller',

    # Main controllers
    'ClientController',
    'DietController',
    'ReportController',
    'AuthController',

    # Auth models and enums
    'User',
    'Session',
    'UserRole',
    'Permission',
    'SessionStatus'
]



def initialize_all_controllers(app_instance=None) -> bool:
    """
    Initialize all controllers in the correct dependency order

    Args:
        app_instance: Optional PyQt application instance

    Returns:
        bool: True if all controllers initialized successfully
    """
    try:
        # Get controller manager
        manager = get_controller_manager()

        # Register controllers in dependency order
        # AuthController has no dependencies
        auth_controller = AuthController(app_instance)
        manager.register_controller('auth', auth_controller)

        # ClientController depends on auth for user permissions
        client_controller = ClientController(app_instance)
        manager.register_controller('client', client_controller, dependencies=['auth'])

        # DietController depends on client and auth
        diet_controller = DietController(app_instance)
        manager.register_controller('diet', diet_controller, dependencies=['auth', 'client'])

        # ReportController depends on all other controllers
        report_controller = ReportController(app_instance)
        manager.register_controller('report', report_controller, dependencies=['auth', 'client', 'diet'])

        # Initialize all controllers
        success = manager.initialize_all()

        if success:
            from loguru import logger
            logger.info("All controllers initialized successfully")
        else:
            from loguru import logger
            logger.error("Failed to initialize some controllers")

        return success

    except Exception as e:
        from loguru import logger
        logger.error(f"Error initializing controllers: {e}")
        return False


def cleanup_all_controllers() -> None:
    """
    Cleanup all controllers and resources
    """
    try:
        manager = get_controller_manager()
        manager.cleanup_all()

        from loguru import logger
        logger.info("All controllers cleaned up successfully")

    except Exception as e:
        from loguru import logger
        logger.error(f"Error cleaning up controllers: {e}")


# Convenience functions for getting specific controllers
def get_auth_controller() -> AuthController:
    """Get the authentication controller"""
    return get_controller('auth')


def get_client_controller() -> ClientController:
    """Get the client management controller"""
    return get_controller('client')


def get_diet_controller() -> DietController:
    """Get the diet management controller"""
    return get_controller('diet')


def get_report_controller() -> ReportController:
    """Get the report generation controller"""
    return get_controller('report')
