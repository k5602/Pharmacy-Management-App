"""
Models Package
Database models for the Pharmacy Management System v2.0

This package contains all data models and repository classes for:
- Client management
- Diet and nutrition tracking
- Notes and documentation
- User authentication
- System configuration

The models use SQLAlchemy ORM for database operations and provide
a clean abstraction layer for data access.
"""

from .base import (
    BaseModel,
    BaseRepository,
    DatabaseManager,
    get_database_manager,
    init_database
)

from .client import (
    Client,
    ClientNote,
    ClientRepository,
    ClientNoteRepository
)

from .diet import (
    DietRecord,
    MealPlan,
    WeightCategory,
    WeightCondition,
    BMICategory,
    ActivityLevel,
    DietRepository,
    MealPlanRepository
)

# Version information
__version__ = "2.0.0"
__author__ = "Khaled Alam"

# Supported model types
SUPPORTED_MODELS = [
    "Client",
    "ClientNote",
    "DietRecord",
    "MealPlan"
]

# Repository mapping
REPOSITORIES = {
    "client": ClientRepository,
    "client_note": ClientNoteRepository,
    "diet": DietRepository,
    "meal_plan": MealPlanRepository
}

def get_repository(model_name: str):
    """
    Get repository instance for a model

    Args:
        model_name: Name of the model

    Returns:
        Repository instance or None if not found
    """
    repo_class = REPOSITORIES.get(model_name.lower())
    if repo_class:
        return repo_class()
    return None

def get_all_models():
    """Get list of all available model classes"""
    return [
        BaseModel,
        Client,
        ClientNote,
        DietRecord,
        MealPlan
    ]

def get_model_info():
    """Get information about available models"""
    return {
        "version": __version__,
        "supported_models": SUPPORTED_MODELS,
        "repositories": list(REPOSITORIES.keys())
    }

# Auto-initialize database on import (optional)
def initialize_models():
    """Initialize all models and create database tables if needed"""
    try:
        init_database()
        return True
    except Exception as e:
        import warnings
        warnings.warn(f"Failed to initialize models: {e}")
        return False

# Export commonly used items
__all__ = [
    # Base classes
    "BaseModel",
    "BaseRepository",
    "DatabaseManager",
    "get_database_manager",
    "init_database",

    # Client models
    "Client",
    "ClientNote",
    "ClientRepository",
    "ClientNoteRepository",

    # Diet models
    "DietRecord",
    "MealPlan",
    "WeightCategory",
    "WeightCondition",
    "BMICategory",
    "ActivityLevel",
    "DietRepository",
    "MealPlanRepository",

    # Utility functions
    "get_repository",
    "get_all_models",
    "get_model_info",
    "initialize_models"
]
