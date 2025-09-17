"""
Auth Controller
Handles user authentication, authorization, session management and security
for the Pharmacy Management System
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import hashlib
import secrets
import jwt
from enum import Enum
from PyQt6.QtCore import pyqtSignal, QTimer
from loguru import logger

from .base import BaseController
from utils.validation import AuthValidator
from config.simple_settings import get_settings


class UserRole(Enum):
    """User roles for authorization"""
    ADMIN = "admin"
    PHARMACIST = "pharmacist"
    NUTRITIONIST = "nutritionist"
    ASSISTANT = "assistant"
    VIEWER = "viewer"


class Permission(Enum):
    """System permissions"""
    # Client permissions
    CLIENT_CREATE = "client:create"
    CLIENT_READ = "client:read"
    CLIENT_UPDATE = "client:update"
    CLIENT_DELETE = "client:delete"

    # Diet permissions
    DIET_CREATE = "diet:create"
    DIET_READ = "diet:read"
    DIET_UPDATE = "diet:update"
    DIET_DELETE = "diet:delete"

    # Report permissions
    REPORT_GENERATE = "report:generate"
    REPORT_VIEW = "report:view"
    REPORT_DELETE = "report:delete"

    # System permissions
    USER_MANAGE = "user:manage"
    SETTINGS_MANAGE = "settings:manage"
    BACKUP_RESTORE = "backup:restore"
    AUDIT_VIEW = "audit:view"


class SessionStatus(Enum):
    """Session status types"""
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    LOCKED = "locked"


class User:
    """User model class"""

    def __init__(self, user_id: str, username: str, email: str, role: UserRole,
                 password_hash: str = None, salt: str = None, is_active: bool = True,
                 created_at: datetime = None, last_login: datetime = None,
                 failed_login_attempts: int = 0, locked_until: datetime = None):
        self.id = user_id
        self.username = username
        self.email = email
        self.role = role
        self.password_hash = password_hash
        self.salt = salt
        self.is_active = is_active
        self.created_at = created_at or datetime.now()
        self.last_login = last_login
        self.failed_login_attempts = failed_login_attempts
        self.locked_until = locked_until

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role.value,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'failed_login_attempts': self.failed_login_attempts,
            'is_locked': self.is_locked()
        }

        if include_sensitive:
            data.update({
                'password_hash': self.password_hash,
                'salt': self.salt,
                'locked_until': self.locked_until.isoformat() if self.locked_until else None
            })

        return data

    def is_locked(self) -> bool:
        """Check if user account is locked"""
        if self.locked_until:
            return datetime.now() < self.locked_until
        return False

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission"""
        return permission in self.get_permissions()

    def get_permissions(self) -> List[Permission]:
        """Get all permissions for user's role"""
        role_permissions = {
            UserRole.ADMIN: [
                # All permissions
                Permission.CLIENT_CREATE, Permission.CLIENT_READ, Permission.CLIENT_UPDATE, Permission.CLIENT_DELETE,
                Permission.DIET_CREATE, Permission.DIET_READ, Permission.DIET_UPDATE, Permission.DIET_DELETE,
                Permission.REPORT_GENERATE, Permission.REPORT_VIEW, Permission.REPORT_DELETE,
                Permission.USER_MANAGE, Permission.SETTINGS_MANAGE, Permission.BACKUP_RESTORE, Permission.AUDIT_VIEW
            ],
            UserRole.PHARMACIST: [
                # Full client and diet management, reports
                Permission.CLIENT_CREATE, Permission.CLIENT_READ, Permission.CLIENT_UPDATE,
                Permission.DIET_CREATE, Permission.DIET_READ, Permission.DIET_UPDATE,
                Permission.REPORT_GENERATE, Permission.REPORT_VIEW
            ],
            UserRole.NUTRITIONIST: [
                # Client and diet management, reports
                Permission.CLIENT_CREATE, Permission.CLIENT_READ, Permission.CLIENT_UPDATE,
                Permission.DIET_CREATE, Permission.DIET_READ, Permission.DIET_UPDATE,
                Permission.REPORT_GENERATE, Permission.REPORT_VIEW
            ],
            UserRole.ASSISTANT: [
                # Limited client management, read-only diet, basic reports
                Permission.CLIENT_CREATE, Permission.CLIENT_READ, Permission.CLIENT_UPDATE,
                Permission.DIET_READ, Permission.REPORT_VIEW
            ],
            UserRole.VIEWER: [
                # Read-only access
                Permission.CLIENT_READ, Permission.DIET_READ, Permission.REPORT_VIEW
            ]
        }

        return role_permissions.get(self.role, [])


class Session:
    """User session model"""

    def __init__(self, session_id: str, user_id: str, username: str, role: UserRole,
                 created_at: datetime = None, expires_at: datetime = None,
                 last_activity: datetime = None, ip_address: str = None,
                 user_agent: str = None):
        self.session_id = session_id
        self.user_id = user_id
        self.username = username
        self.role = role
        self.created_at = created_at or datetime.now()
        self.expires_at = expires_at or (datetime.now() + timedelta(hours=8))
        self.last_activity = last_activity or datetime.now()
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.status = SessionStatus.ACTIVE

    def is_valid(self) -> bool:
        """Check if session is valid"""
        return (
            self.status == SessionStatus.ACTIVE and
            datetime.now() < self.expires_at
        )

    def extend_session(self, hours: int = 8) -> None:
        """Extend session expiration"""
        self.expires_at = datetime.now() + timedelta(hours=hours)
        self.last_activity = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'username': self.username,
            'role': self.role.value,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'status': self.status.value,
            'is_valid': self.is_valid()
        }


class AuthController(BaseController):
    """Controller for authentication and authorization"""

    # Specific signals for authentication events
    user_logged_in = pyqtSignal(dict)  # user data
    user_logged_out = pyqtSignal(str)  # username
    user_created = pyqtSignal(dict)    # user data
    user_updated = pyqtSignal(dict)    # user data
    user_deleted = pyqtSignal(str)     # user_id
    session_expired = pyqtSignal(str)  # session_id
    login_failed = pyqtSignal(str, str)  # username, reason
    account_locked = pyqtSignal(str)   # username
    password_changed = pyqtSignal(str) # username

    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth_validator = AuthValidator()
        self.current_user = None
        self.current_session = None
        self._users = {}  # In-memory user storage (replace with database in production)
        self._sessions = {}  # Active sessions
        self._session_timer = None
        self.jwt_secret = None
        self.max_login_attempts = 5
        self.lockout_duration_minutes = 30
        self.session_timeout_hours = 8
        self.password_min_length = 8

    def _do_initialize(self) -> bool:
        """Initialize the auth controller"""
        try:
            # Load settings
            settings = get_settings()

            # Initialize JWT secret
            self.jwt_secret = getattr(settings.security, 'jwt_secret', self._generate_jwt_secret())

            # Load security settings
            security_settings = getattr(settings, 'security', None)
            if security_settings:
                self.max_login_attempts = getattr(security_settings, 'max_login_attempts', 5)
                self.lockout_duration_minutes = getattr(security_settings, 'lockout_duration_minutes', 30)
                self.session_timeout_hours = getattr(security_settings, 'session_timeout_hours', 8)
                self.password_min_length = getattr(security_settings, 'password_min_length', 8)

            # Load existing users (in production, this would load from database)
            self._load_users()

            # Start session monitoring
            self._start_session_monitoring()

            logger.info("AuthController initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize AuthController: {e}")
            return False

    def _generate_jwt_secret(self) -> str:
        """Generate a secure JWT secret"""
        return secrets.token_urlsafe(32)

    def _load_users(self) -> None:
        """Load users from storage (placeholder - implement database loading)"""
        try:
            # Create default admin user if no users exist
            if not self._users:
                admin_user = self._create_default_admin()
                self._users[admin_user.id] = admin_user
                logger.info("Created default admin user")

        except Exception as e:
            logger.error(f"Error loading users: {e}")

    def _create_default_admin(self) -> User:
        """Create default admin user"""
        user_id = "admin_001"
        username = "admin"
        email = "admin@pharmacy.local"
        password = "admin123"  # Default password - should be changed on first login

        salt = self._generate_salt()
        password_hash = self._hash_password(password, salt)

        return User(
            user_id=user_id,
            username=username,
            email=email,
            role=UserRole.ADMIN,
            password_hash=password_hash,
            salt=salt,
            is_active=True
        )

    def _start_session_monitoring(self) -> None:
        """Start session monitoring timer"""
        try:
            self._session_timer = QTimer()
            self._session_timer.timeout.connect(self._check_session_expiry)
            self._session_timer.start(60000)  # Check every minute
        except Exception as e:
            logger.error(f"Error starting session monitoring: {e}")

    def _check_session_expiry(self) -> None:
        """Check for expired sessions"""
        try:
            expired_sessions = []
            for session_id, session in self._sessions.items():
                if not session.is_valid():
                    expired_sessions.append(session_id)

            for session_id in expired_sessions:
                session = self._sessions.pop(session_id, None)
                if session:
                    session.status = SessionStatus.EXPIRED
                    self.session_expired.emit(session_id)
                    if self.current_session and self.current_session.session_id == session_id:
                        self._handle_session_expiry()

        except Exception as e:
            logger.error(f"Error checking session expiry: {e}")

    def _handle_session_expiry(self) -> None:
        """Handle current session expiry"""
        try:
            if self.current_user:
                username = self.current_user.username
                self.current_user = None
                self.current_session = None
                self.emit_error("Session Expired", "Your session has expired. Please log in again.")
                self.user_logged_out.emit(username)

        except Exception as e:
            logger.error(f"Error handling session expiry: {e}")

    # ==================== Authentication Methods ====================

    def login(self, username: str, password: str, remember_me: bool = False) -> bool:
        """
        Authenticate user and create session

        Args:
            username: Username or email
            password: User password
            remember_me: Whether to extend session duration

        Returns:
            bool: True if login successful
        """
        try:
            # Validate input
            validation_result = self.auth_validator.validate_login_data({
                'username': username,
                'password': password
            })

            if not validation_result['is_valid']:
                error_msg = "; ".join(validation_result['errors'])
                self.emit_error("Login Error", f"Invalid login data: {error_msg}")
                return False

            # Find user
            user = self._find_user_by_username_or_email(username)
            if not user:
                self.login_failed.emit(username, "User not found")
                self.emit_error("Login Failed", "Invalid username or password")
                return False

            # Check if user is active
            if not user.is_active:
                self.login_failed.emit(username, "Account inactive")
                self.emit_error("Login Failed", "Account is inactive")
                return False

            # Check if account is locked
            if user.is_locked():
                self.account_locked.emit(username)
                self.emit_error("Account Locked", f"Account is locked until {user.locked_until}")
                return False

            # Verify password
            if not self._verify_password(password, user.password_hash, user.salt):
                # Increment failed login attempts
                user.failed_login_attempts += 1

                # Lock account if max attempts reached
                if user.failed_login_attempts >= self.max_login_attempts:
                    user.locked_until = datetime.now() + timedelta(minutes=self.lockout_duration_minutes)
                    self.account_locked.emit(username)
                    self.emit_error("Account Locked",
                                  f"Account locked due to too many failed attempts. "
                                  f"Try again in {self.lockout_duration_minutes} minutes.")
                else:
                    attempts_left = self.max_login_attempts - user.failed_login_attempts
                    self.emit_error("Login Failed",
                                  f"Invalid password. {attempts_left} attempts remaining.")

                self.login_failed.emit(username, "Invalid password")
                return False

            # Reset failed login attempts on successful login
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login = datetime.now()

            # Create session
            session_duration = 24 if remember_me else self.session_timeout_hours
            session = self._create_session(user, session_duration)

            # Set current user and session
            self.current_user = user
            self.current_session = session

            # Emit success signals
            self.emit_success("Login Successful", f"Welcome back, {user.username}!")
            self.user_logged_in.emit(user.to_dict())
            self.emit_data_changed("user_logged_in", {
                "user_id": user.id,
                "username": user.username,
                "role": user.role.value
            })

            logger.info(f"User {username} logged in successfully")
            return True

        except Exception as e:
            logger.error(f"Error during login: {e}")
            self.emit_error("Login Error", f"Login failed: {str(e)}")
            return False

    def logout(self) -> bool:
        """
        Logout current user and terminate session

        Returns:
            bool: True if logout successful
        """
        try:
            if not self.current_user or not self.current_session:
                self.emit_error("Logout Error", "No active session to logout")
                return False

            username = self.current_user.username
            session_id = self.current_session.session_id

            # Terminate session
            if session_id in self._sessions:
                self._sessions[session_id].status = SessionStatus.TERMINATED
                del self._sessions[session_id]

            # Clear current user and session
            self.current_user = None
            self.current_session = None

            # Emit signals
            self.emit_success("Logout Successful", "You have been logged out successfully")
            self.user_logged_out.emit(username)
            self.emit_data_changed("user_logged_out", {"username": username})

            logger.info(f"User {username} logged out successfully")
            return True

        except Exception as e:
            logger.error(f"Error during logout: {e}")
            self.emit_error("Logout Error", f"Logout failed: {str(e)}")
            return False

    def change_password(self, current_password: str, new_password: str) -> bool:
        """
        Change password for current user

        Args:
            current_password: Current password
            new_password: New password

        Returns:
            bool: True if password changed successfully
        """
        try:
            if not self.current_user:
                self.emit_error("Authorization Error", "No active session")
                return False

            # Validate current password
            if not self._verify_password(current_password, self.current_user.password_hash, self.current_user.salt):
                self.emit_error("Password Change Failed", "Current password is incorrect")
                return False

            # Validate new password
            validation_result = self.auth_validator.validate_password(new_password)
            if not validation_result['is_valid']:
                error_msg = "; ".join(validation_result['errors'])
                self.emit_error("Password Validation Error", f"New password is invalid: {error_msg}")
                return False

            # Generate new salt and hash
            new_salt = self._generate_salt()
            new_password_hash = self._hash_password(new_password, new_salt)

            # Update user password
            self.current_user.salt = new_salt
            self.current_user.password_hash = new_password_hash

            # Emit signals
            self.emit_success("Password Changed", "Password changed successfully")
            self.password_changed.emit(self.current_user.username)

            logger.info(f"Password changed for user {self.current_user.username}")
            return True

        except Exception as e:
            logger.error(f"Error changing password: {e}")
            self.emit_error("Password Change Error", f"Failed to change password: {str(e)}")
            return False

    # ==================== User Management ====================

    def create_user(self, user_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new user

        Args:
            user_data: User information dictionary

        Returns:
            str: User ID if successful, None if failed
        """
        try:
            # Check permission
            if not self.has_permission(Permission.USER_MANAGE):
                self.emit_error("Permission Denied", "You don't have permission to create users")
                return None

            # Validate user data
            validation_result = self.auth_validator.validate_user_data(user_data)
            if not validation_result['is_valid']:
                error_msg = "; ".join(validation_result['errors'])
                self.emit_error("Validation Error", f"User data validation failed: {error_msg}")
                return None

            validated_data = validation_result['data']

            # Check if username or email already exists
            if self._find_user_by_username_or_email(validated_data['username']):
                self.emit_error("User Creation Error", "Username already exists")
                return None

            if self._find_user_by_username_or_email(validated_data['email']):
                self.emit_error("User Creation Error", "Email already exists")
                return None

            # Generate user ID
            user_id = f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(4)}"

            # Hash password
            salt = self._generate_salt()
            password_hash = self._hash_password(validated_data['password'], salt)

            # Create user
            user = User(
                user_id=user_id,
                username=validated_data['username'],
                email=validated_data['email'],
                role=UserRole(validated_data['role']),
                password_hash=password_hash,
                salt=salt,
                is_active=validated_data.get('is_active', True)
            )

            # Store user
            self._users[user_id] = user

            # Emit signals
            self.emit_success("User Created", f"User {user.username} created successfully")
            self.user_created.emit(user.to_dict())
            self.emit_data_changed("user_created", {"user_id": user_id})

            logger.info(f"User {user.username} created by {self.current_user.username if self.current_user else 'system'}")
            return user_id

        except Exception as e:
            logger.error(f"Error creating user: {e}")
            self.emit_error("User Creation Error", f"Failed to create user: {str(e)}")
            return None

    def update_user(self, user_id: str, updated_data: Dict[str, Any]) -> bool:
        """
        Update an existing user

        Args:
            user_id: User ID to update
            updated_data: Updated user data

        Returns:
            bool: True if successful
        """
        try:
            # Check permission
            if not self.has_permission(Permission.USER_MANAGE):
                self.emit_error("Permission Denied", "You don't have permission to update users")
                return False

            # Get user
            user = self._users.get(user_id)
            if not user:
                self.emit_error("User Not Found", f"User with ID {user_id} not found")
                return False

            # Validate updated data
            validation_result = self.auth_validator.validate_user_data(updated_data, is_update=True)
            if not validation_result['is_valid']:
                error_msg = "; ".join(validation_result['errors'])
                self.emit_error("Validation Error", f"Update data validation failed: {error_msg}")
                return False

            validated_data = validation_result['data']

            # Update user properties
            if 'username' in validated_data:
                # Check if new username already exists (for other users)
                existing_user = self._find_user_by_username_or_email(validated_data['username'])
                if existing_user and existing_user.id != user_id:
                    self.emit_error("Update Error", "Username already exists")
                    return False
                user.username = validated_data['username']

            if 'email' in validated_data:
                # Check if new email already exists (for other users)
                existing_user = self._find_user_by_username_or_email(validated_data['email'])
                if existing_user and existing_user.id != user_id:
                    self.emit_error("Update Error", "Email already exists")
                    return False
                user.email = validated_data['email']

            if 'role' in validated_data:
                user.role = UserRole(validated_data['role'])

            if 'is_active' in validated_data:
                user.is_active = validated_data['is_active']

            # Emit signals
            self.emit_success("User Updated", f"User {user.username} updated successfully")
            self.user_updated.emit(user.to_dict())
            self.emit_data_changed("user_updated", {"user_id": user_id})

            logger.info(f"User {user.username} updated by {self.current_user.username if self.current_user else 'system'}")
            return True

        except Exception as e:
            logger.error(f"Error updating user: {e}")
            self.emit_error("User Update Error", f"Failed to update user: {str(e)}")
            return False

    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user (soft delete - deactivate)

        Args:
            user_id: User ID to delete

        Returns:
            bool: True if successful
        """
        try:
            # Check permission
            if not self.has_permission(Permission.USER_MANAGE):
                self.emit_error("Permission Denied", "You don't have permission to delete users")
                return False

            # Get user
            user = self._users.get(user_id)
            if not user:
                self.emit_error("User Not Found", f"User with ID {user_id} not found")
                return False

            # Prevent self-deletion
            if self.current_user and user_id == self.current_user.id:
                self.emit_error("Delete Error", "Cannot delete your own account")
                return False

            # Deactivate user instead of hard delete
            user.is_active = False

            # Terminate any active sessions for this user
            sessions_to_remove = []
            for session_id, session in self._sessions.items():
                if session.user_id == user_id:
                    sessions_to_remove.append(session_id)

            for session_id in sessions_to_remove:
                del self._sessions[session_id]

            # Emit signals
            self.emit_success("User Deleted", f"User {user.username} deactivated successfully")
            self.user_deleted.emit(user_id)
            self.emit_data_changed("user_deleted", {"user_id": user_id})

            logger.info(f"User {user.username} deleted by {self.current_user.username if self.current_user else 'system'}")
            return True

        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            self.emit_error("User Delete Error", f"Failed to delete user: {str(e)}")
            return False

    def get_all_users(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """
        Get all users

        Args:
            include_inactive: Whether to include inactive users

        Returns:
            List[dict]: List of users
        """
        try:
            # Check permission
            if not self.has_permission(Permission.USER_MANAGE):
                return []

            users = []
            for user in self._users.values():
                if include_inactive or user.is_active:
                    users.append(user.to_dict())

            return users

        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []

    # ==================== Authorization Methods ====================

    def has_permission(self, permission: Permission) -> bool:
        """
        Check if current user has specific permission

        Args:
            permission: Permission to check

        Returns:
            bool: True if user has permission
        """
        try:
            if not self.current_user or not self.current_session:
                return False

            if not self.current_session.is_valid():
                return False

            return self.current_user.has_permission(permission)

        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            return False

    def require_permission(self, permission: Permission) -> bool:
        """
        Check permission and emit error if not authorized

        Args:
            permission: Required permission

        Returns:
            bool: True if authorized
        """
        if not self.has_permission(permission):
            self.emit_error("Permission Denied", f"You don't have permission: {permission.value}")
            return False
        return True

    def is_authenticated(self) -> bool:
        """Check if user is authenticated with valid session"""
        return (
            self.current_user is not None and
            self.current_session is not None and
            self.current_session.is_valid()
        )

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user"""
        if self.current_user:
            return self.current_user.to_dict()
        return None

    def get_current_session(self) -> Optional[Dict[str, Any]]:
        """Get current session info"""
        if self.current_session:
            return self.current_session.to_dict()
        return None

    # ==================== Session Management ====================

    def _create_session(self, user: User, duration_hours: int = 8) -> Session:
        """Create a new session for user"""
        session_id = self._generate_session_id()
        expires_at = datetime.now() + timedelta(hours=duration_hours)

        session = Session(
            session_id=session_id,
            user_id=user.id,
            username=user.username,
            role=user.role,
            expires_at=expires_at
        )

        self._sessions[session_id] = session
        return session

    def _generate_session_id(self) -> str:
        """Generate a secure session ID"""
        return secrets.token_urlsafe(32)

    def extend_current_session(self, hours: int = 8) -> bool:
        """
        Extend current session duration

        Args:
            hours: Number of hours to extend

        Returns:
            bool: True if successful
        """
        try:
            if not self.current_session:
                return False

            self.current_session.extend_session(hours)
            return True

        except Exception as e:
            logger.error(f"Error extending session: {e}")
            return False

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active sessions (admin only)"""
        try:
            if not self.has_permission(Permission.AUDIT_VIEW):
                return []

            sessions = []
            for session in self._sessions.values():
                if session.is_valid():
                    sessions.append(session.to_dict())

            return sessions

        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return []

    def terminate_session(self, session_id: str) -> bool:
        """
        Terminate a specific session (admin only)

        Args:
            session_id: Session ID to terminate

        Returns:
            bool: True if successful
        """
        try:
            if not self.has_permission(Permission.USER_MANAGE):
                self.emit_error("Permission Denied", "You don't have permission to terminate sessions")
                return False

            if session_id in self._sessions:
                session = self._sessions[session_id]
                session.status = SessionStatus.TERMINATED
                del self._sessions[session_id]

                self.emit_success("Session Terminated", f"Session {session_id} terminated")
                return True
            else:
                self.emit_error("Session Not Found", f"Session {session_id} not found")
                return False

        except Exception as e:
            logger.error(f"Error terminating session: {e}")
            return False

    # ==================== Utility Methods ====================

    def _find_user_by_username_or_email(self, identifier: str) -> Optional[User]:
        """Find user by username or email"""
        for user in self._users.values():
            if user.username == identifier or user.email == identifier:
                return user
        return None

    def _generate_salt(self) -> str:
        """Generate a random salt for password hashing"""
        return secrets.token_hex(16)

    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password with salt"""
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()

    def _verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash"""
        return self._hash_password(password, salt) == password_hash

    def reset_failed_login_attempts(self, username: str) -> bool:
        """
        Reset failed login attempts for a user (admin only)

        Args:
            username: Username to reset

        Returns:
            bool: True if successful
        """
        try:
            if not self.has_permission(Permission.USER_MANAGE):
                self.emit_error("Permission Denied", "You don't have permission to reset login attempts")
                return False

            user = self._find_user_by_username_or_email(username)
            if not user:
                self.emit_error("User Not Found", f"User {username} not found")
                return False

            user.failed_login_attempts = 0
            user.locked_until = None

            self.emit_success("Login Attempts Reset", f"Failed login attempts reset for {username}")
            return True

        except Exception as e:
            logger.error(f"Error resetting login attempts: {e}")
            return False

    def generate_jwt_token(self, user: User) -> str:
        """
        Generate JWT token for API access

        Args:
            user: User instance

        Returns:
            str: JWT token
        """
        try:
            payload = {
                'user_id': user.id,
                'username': user.username,
                'role': user.role.value,
                'exp': datetime.utcnow() + timedelta(hours=24),
                'iat': datetime.utcnow()
            }

            token = jwt.encode(payload, self.jwt_secret, algorithm='HS256')
            return token

        except Exception as e:
            logger.error(f"Error generating JWT token: {e}")
            return ""

    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token

        Args:
            token: JWT token to verify

        Returns:
            dict: Token payload if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
            return None
        except Exception as e:
            logger.error(f"Error verifying JWT token: {e}")
            return None

    def cleanup(self) -> None:
        """Clean up controller resources"""
        try:
            # Stop session monitoring
            if self._session_timer:
                self._session_timer.stop()
                self._session_timer = None

            # Clear current session
            self.current_user = None
            self.current_session = None

            # Clear active sessions
            self._sessions.clear()

            super().cleanup()
            logger.info("AuthController cleaned up successfully")

        except Exception as e:
            logger.error(f"Error during AuthController cleanup: {e}")
