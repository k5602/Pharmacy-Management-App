"""
Base Database Models
Provides base classes and database setup for the Pharmacy Management System
"""

import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any, Type, TypeVar
from pathlib import Path

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from loguru import logger

# Type variable for generic model operations
ModelType = TypeVar("ModelType", bound="BaseModel")

# Create the declarative base
Base = declarative_base()


class BaseModel(Base):
    """
    Base model class that provides common fields and methods for all models
    """
    __abstract__ = True

    # Common fields for all tables
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update model instance from dictionary"""
        for key, value in data.items():
            if hasattr(self, key) and key not in ['id', 'created_at']:
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"


class DatabaseManager:
    """
    Manages database connections, sessions, and operations
    """

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or self._get_default_database_url()
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()

    def _get_default_database_url(self) -> str:
        """Get the default database URL"""
        # Get the application data directory
        app_data_path = self._get_app_data_path()
        app_data_path.mkdir(parents=True, exist_ok=True)

        db_path = app_data_path / "pharmacy.db"
        return f"sqlite:///{db_path}"

    def _get_app_data_path(self) -> Path:
        """Get the application data directory based on the operating system"""
        if sys.platform == "win32":
            app_data = Path(os.environ.get("APPDATA", ""))
            return app_data / "PharmacyManagement"
        elif sys.platform == "darwin":
            home = Path.home()
            return home / "Library" / "Application Support" / "PharmacyManagement"
        else:  # Linux and other Unix-like systems
            home = Path.home()
            return home / ".config" / "PharmacyManagement"

    def _initialize_database(self) -> None:
        """Initialize database engine and session factory"""
        try:
            # Create engine with appropriate settings for SQLite
            if self.database_url.startswith("sqlite"):
                self.engine = create_engine(
                    self.database_url,
                    poolclass=StaticPool,
                    connect_args={
                        "check_same_thread": False,
                        "timeout": 20
                    },
                    echo=False  # Set to True for SQL query debugging
                )
            else:
                self.engine = create_engine(self.database_url)

            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )

            logger.info(f"Database initialized: {self.database_url}")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def create_tables(self) -> None:
        """Create all tables in the database"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise

    def drop_tables(self) -> None:
        """Drop all tables in the database (use with caution!)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("All database tables dropped")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise

    def get_session(self) -> Session:
        """Get a new database session"""
        if self.SessionLocal is None:
            raise RuntimeError("Database not initialized")
        return self.SessionLocal()

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            from sqlalchemy import text
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    def backup_database(self, backup_path: Optional[str] = None) -> bool:
        """Create a backup of the database"""
        if not self.database_url.startswith("sqlite"):
            logger.warning("Backup is only supported for SQLite databases")
            return False

        try:
            import shutil

            # Extract database file path from URL
            db_file_path = self.database_url.replace("sqlite:///", "")

            if not os.path.exists(db_file_path):
                logger.error(f"Database file not found: {db_file_path}")
                return False

            # Generate backup filename if not provided
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = Path(db_file_path).parent / "backups"
                backup_dir.mkdir(exist_ok=True)
                backup_path = backup_dir / f"pharmacy_backup_{timestamp}.db"

            # Create backup
            shutil.copy2(db_file_path, backup_path)
            logger.info(f"Database backup created: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False

    def restore_database(self, backup_path: str) -> bool:
        """Restore database from backup"""
        if not self.database_url.startswith("sqlite"):
            logger.warning("Restore is only supported for SQLite databases")
            return False

        try:
            import shutil

            if not os.path.exists(backup_path):
                logger.error(f"Backup file not found: {backup_path}")
                return False

            # Extract database file path from URL
            db_file_path = self.database_url.replace("sqlite:///", "")

            # Close all connections
            self.engine.dispose()

            # Restore backup
            shutil.copy2(backup_path, db_file_path)

            # Reinitialize database
            self._initialize_database()

            logger.info(f"Database restored from: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return False

    def get_database_info(self) -> Dict[str, Any]:
        """Get database information"""
        info = {
            "url": self.database_url,
            "connected": self.test_connection(),
            "tables": []
        }

        if info["connected"]:
            try:
                info["tables"] = list(Base.metadata.tables.keys())

                # Get additional SQLite info if applicable
                if self.database_url.startswith("sqlite"):
                    db_file_path = self.database_url.replace("sqlite:///", "")
                    if os.path.exists(db_file_path):
                        stat = os.stat(db_file_path)
                        info["file_size"] = stat.st_size
                        info["last_modified"] = datetime.fromtimestamp(stat.st_mtime)

            except Exception as e:
                logger.error(f"Failed to get database info: {e}")

        return info

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.engine:
            self.engine.dispose()


class BaseRepository:
    """
    Base repository class providing common database operations
    """

    def __init__(self, db_manager: DatabaseManager, model_class: Type[ModelType]):
        self.db_manager = db_manager
        self.model_class = model_class

    def create(self, **kwargs) -> ModelType:
        """Create a new record"""
        with self.db_manager.get_session() as session:
            try:
                instance = self.model_class(**kwargs)
                session.add(instance)
                session.commit()
                session.refresh(instance)
                return instance
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to create {self.model_class.__name__}: {e}")
                raise

    def get_by_id(self, record_id: int) -> Optional[ModelType]:
        """Get a record by ID"""
        with self.db_manager.get_session() as session:
            try:
                return session.query(self.model_class).filter(
                    self.model_class.id == record_id,
                    self.model_class.is_active == True
                ).first()
            except Exception as e:
                logger.error(f"Failed to get {self.model_class.__name__} by ID {record_id}: {e}")
                return None

    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> list[ModelType]:
        """Get all active records"""
        with self.db_manager.get_session() as session:
            try:
                query = session.query(self.model_class).filter(
                    self.model_class.is_active == True
                ).offset(offset)

                if limit:
                    query = query.limit(limit)

                return query.all()
            except Exception as e:
                logger.error(f"Failed to get all {self.model_class.__name__}: {e}")
                return []

    def update(self, record_id: int, **kwargs) -> Optional[ModelType]:
        """Update a record"""
        with self.db_manager.get_session() as session:
            try:
                instance = session.query(self.model_class).filter(
                    self.model_class.id == record_id
                ).first()

                if not instance:
                    return None

                for key, value in kwargs.items():
                    if hasattr(instance, key) and key not in ['id', 'created_at']:
                        setattr(instance, key, value)

                instance.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(instance)
                return instance

            except Exception as e:
                session.rollback()
                logger.error(f"Failed to update {self.model_class.__name__} {record_id}: {e}")
                raise

    def delete(self, record_id: int, soft_delete: bool = True) -> bool:
        """Delete a record (soft delete by default)"""
        with self.db_manager.get_session() as session:
            try:
                instance = session.query(self.model_class).filter(
                    self.model_class.id == record_id
                ).first()

                if not instance:
                    return False

                if soft_delete:
                    instance.is_active = False
                    instance.updated_at = datetime.utcnow()
                else:
                    session.delete(instance)

                session.commit()
                return True

            except Exception as e:
                session.rollback()
                logger.error(f"Failed to delete {self.model_class.__name__} {record_id}: {e}")
                return False

    def count(self) -> int:
        """Count active records"""
        with self.db_manager.get_session() as session:
            try:
                return session.query(self.model_class).filter(
                    self.model_class.is_active == True
                ).count()
            except Exception as e:
                logger.error(f"Failed to count {self.model_class.__name__}: {e}")
                return 0

    def exists(self, record_id: int) -> bool:
        """Check if a record exists"""
        return self.get_by_id(record_id) is not None


# Global database manager instance
_db_manager = None

def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager

def init_database() -> None:
    """Initialize the database and create tables"""
    db_manager = get_database_manager()
    db_manager.create_tables()
