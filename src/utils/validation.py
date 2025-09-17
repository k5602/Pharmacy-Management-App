"""
Validation Classes
Comprehensive validation for all controller operations in the Pharmacy Management System
"""

import re
import phonenumbers
from typing import Any, Optional, List, Dict, Union, Tuple
from datetime import datetime, date, timedelta
from enum import Enum
from phonenumbers import NumberParseException
from loguru import logger

from .validators import (
    validate_email, validate_phone, validate_age, validate_weight, validate_height,
    validate_percentage, validate_blood_pressure, validate_heart_rate, validate_blood_sugar,
    validate_date, validate_pharmacy_id, validate_password, validate_arabic_text,
    sanitize_input, validate_file_path
)


class ValidationSeverity(Enum):
    """Validation message severity levels"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationMessage:
    """Validation message with severity and details"""

    def __init__(self, message: str, severity: ValidationSeverity = ValidationSeverity.ERROR,
                 field: str = None, code: str = None):
        self.message = message
        self.severity = severity
        self.field = field
        self.code = code

    def to_dict(self) -> Dict[str, Any]:
        return {
            'message': self.message,
            'severity': self.severity.value,
            'field': self.field,
            'code': self.code
        }


class ValidationResult:
    """Comprehensive validation result"""

    def __init__(self):
        self.messages: List[ValidationMessage] = []
        self.data: Dict[str, Any] = {}

    def add_error(self, message: str, field: str = None, code: str = None):
        """Add an error message"""
        self.messages.append(ValidationMessage(message, ValidationSeverity.ERROR, field, code))

    def add_warning(self, message: str, field: str = None, code: str = None):
        """Add a warning message"""
        self.messages.append(ValidationMessage(message, ValidationSeverity.WARNING, field, code))

    def add_info(self, message: str, field: str = None, code: str = None):
        """Add an info message"""
        self.messages.append(ValidationMessage(message, ValidationSeverity.INFO, field, code))

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)"""
        return not any(msg.severity == ValidationSeverity.ERROR for msg in self.messages)

    @property
    def errors(self) -> List[str]:
        """Get error messages only"""
        return [msg.message for msg in self.messages if msg.severity == ValidationSeverity.ERROR]

    @property
    def warnings(self) -> List[str]:
        """Get warning messages only"""
        return [msg.message for msg in self.messages if msg.severity == ValidationSeverity.WARNING]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'messages': [msg.to_dict() for msg in self.messages],
            'data': self.data
        }


class BaseValidator:
    """Base validator class with common functionality"""

    def __init__(self):
        self.result = ValidationResult()

    def _validate_required(self, data: Dict[str, Any], field: str,
                          display_name: str = None) -> bool:
        """Validate required field"""
        display_name = display_name or field
        if field not in data or data[field] is None or data[field] == '':
            self.result.add_error(f"Field '{display_name}' is required", field, 'REQUIRED')
            return False
        return True

    def _validate_type(self, value: Any, expected_type: type, field: str,
                      display_name: str = None) -> bool:
        """Validate field type"""
        display_name = display_name or field
        if not isinstance(value, expected_type):
            self.result.add_error(
                f"Field '{display_name}' must be of type {expected_type.__name__}",
                field, 'TYPE_ERROR'
            )
            return False
        return True

    def _validate_length(self, value: str, min_length: int = None, max_length: int = None,
                        field: str = None, display_name: str = None) -> bool:
        """Validate string length"""
        display_name = display_name or field
        if min_length and len(value) < min_length:
            self.result.add_error(
                f"Field '{display_name}' must be at least {min_length} characters",
                field, 'MIN_LENGTH'
            )
            return False

        if max_length and len(value) > max_length:
            self.result.add_error(
                f"Field '{display_name}' must not exceed {max_length} characters",
                field, 'MAX_LENGTH'
            )
            return False

        return True

    def _validate_range(self, value: Union[int, float], min_value: Union[int, float] = None,
                       max_value: Union[int, float] = None, field: str = None,
                       display_name: str = None) -> bool:
        """Validate numeric range"""
        display_name = display_name or field
        if min_value is not None and value < min_value:
            self.result.add_error(
                f"Field '{display_name}' must be at least {min_value}",
                field, 'MIN_VALUE'
            )
            return False

        if max_value is not None and value > max_value:
            self.result.add_error(
                f"Field '{display_name}' must not exceed {max_value}",
                field, 'MAX_VALUE'
            )
            return False

        return True

    def _sanitize_string(self, value: str, max_length: int = None) -> str:
        """Sanitize string input"""
        return sanitize_input(value, max_length)


class ClientValidator(BaseValidator):
    """Validator for client-related operations"""

    def validate_client_data(self, data: Dict[str, Any], is_update: bool = False) -> Dict[str, Any]:
        """
        Validate client data for creation or update

        Args:
            data: Client data dictionary
            is_update: Whether this is an update operation

        Returns:
            dict: Validation result
        """
        self.result = ValidationResult()
        validated_data = {}

        # Required fields for new clients
        if not is_update:
            required_fields = ['first_name', 'last_name', 'phone_number']
            for field in required_fields:
                if not self._validate_required(data, field):
                    continue

        # Validate first name
        if 'first_name' in data and data['first_name']:
            first_name = self._sanitize_string(data['first_name'], 100)
            if self._validate_length(first_name, 1, 100, 'first_name', 'First Name'):
                if validate_arabic_text(first_name, allow_english=True):
                    validated_data['first_name'] = first_name
                else:
                    self.result.add_warning(
                        "First name contains invalid characters",
                        'first_name', 'INVALID_CHARS'
                    )
                    validated_data['first_name'] = first_name

        # Validate last name
        if 'last_name' in data and data['last_name']:
            last_name = self._sanitize_string(data['last_name'], 100)
            if self._validate_length(last_name, 1, 100, 'last_name', 'Last Name'):
                if validate_arabic_text(last_name, allow_english=True):
                    validated_data['last_name'] = last_name
                else:
                    self.result.add_warning(
                        "Last name contains invalid characters",
                        'last_name', 'INVALID_CHARS'
                    )
                    validated_data['last_name'] = last_name

        # Validate phone number
        if 'phone_number' in data and data['phone_number']:
            phone = self._sanitize_string(data['phone_number'], 20)
            if validate_phone(phone):
                validated_data['phone_number'] = phone
            else:
                self.result.add_error(
                    "Invalid phone number format",
                    'phone_number', 'INVALID_PHONE'
                )

        # Validate email (optional)
        if 'email' in data and data['email']:
            email = self._sanitize_string(data['email'], 255)
            if validate_email(email):
                validated_data['email'] = email.lower()
            else:
                self.result.add_error(
                    "Invalid email address format",
                    'email', 'INVALID_EMAIL'
                )

        # Validate birth date (optional)
        if 'birth_date' in data and data['birth_date']:
            if self._validate_birth_date(data['birth_date']):
                validated_data['birth_date'] = data['birth_date']

        # Validate gender (optional)
        if 'gender' in data and data['gender']:
            gender = data['gender'].lower()
            if gender in ['male', 'female', 'other']:
                validated_data['gender'] = gender.capitalize()
            else:
                self.result.add_error(
                    "Gender must be 'male', 'female', or 'other'",
                    'gender', 'INVALID_GENDER'
                )

        # Validate address (optional)
        if 'address' in data and data['address']:
            address = self._sanitize_string(data['address'], 500)
            validated_data['address'] = address

        # Validate emergency contact (optional)
        if 'emergency_contact' in data and data['emergency_contact']:
            emergency_contact = self._sanitize_string(data['emergency_contact'], 255)
            validated_data['emergency_contact'] = emergency_contact

        # Validate medical fields (optional)
        medical_fields = ['medical_conditions', 'allergies', 'current_medications', 'notes']
        for field in medical_fields:
            if field in data and data[field]:
                validated_data[field] = self._sanitize_string(data[field], 2000)

        self.result.data = validated_data
        return self.result.to_dict()

    def _validate_birth_date(self, birth_date: Any) -> bool:
        """Validate birth date"""
        try:
            if isinstance(birth_date, str):
                # Try to parse the date
                if not validate_date(birth_date):
                    self.result.add_error(
                        "Invalid birth date format",
                        'birth_date', 'INVALID_DATE'
                    )
                    return False
            elif isinstance(birth_date, date):
                pass  # Already a date object
            else:
                self.result.add_error(
                    "Birth date must be a date string or date object",
                    'birth_date', 'TYPE_ERROR'
                )
                return False

            # Check if date is not in the future
            if isinstance(birth_date, str):
                birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()

            if birth_date > date.today():
                self.result.add_error(
                    "Birth date cannot be in the future",
                    'birth_date', 'FUTURE_DATE'
                )
                return False

            # Check if age is reasonable (not over 150 years)
            age = (date.today() - birth_date).days / 365.25
            if age > 150:
                self.result.add_error(
                    "Birth date indicates age over 150 years",
                    'birth_date', 'UNREALISTIC_AGE'
                )
                return False

            return True

        except Exception as e:
            self.result.add_error(
                f"Error validating birth date: {str(e)}",
                'birth_date', 'VALIDATION_ERROR'
            )
            return False


class MedicalValidator(BaseValidator):
    """Validator for medical and health-related data"""

    def validate_bmi_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate BMI calculation data"""
        self.result = ValidationResult()
        validated_data = {}

        # Validate weight
        if self._validate_required(data, 'weight', 'Weight'):
            try:
                weight = float(data['weight'])
                if validate_weight(weight):
                    validated_data['weight'] = weight
                else:
                    self.result.add_error(
                        "Weight must be between 1 and 1000 kg",
                        'weight', 'INVALID_WEIGHT'
                    )
            except (ValueError, TypeError):
                self.result.add_error(
                    "Weight must be a valid number",
                    'weight', 'TYPE_ERROR'
                )

        # Validate height
        if self._validate_required(data, 'height', 'Height'):
            try:
                height = float(data['height'])
                if validate_height(height):
                    validated_data['height'] = height
                else:
                    self.result.add_error(
                        "Height must be between 30 and 300 cm",
                        'height', 'INVALID_HEIGHT'
                    )
            except (ValueError, TypeError):
                self.result.add_error(
                    "Height must be a valid number",
                    'height', 'TYPE_ERROR'
                )

        self.result.data = validated_data
        return self.result.to_dict()

    def validate_diet_data(self, data: Dict[str, Any], is_update: bool = False) -> Dict[str, Any]:
        """Validate diet record data"""
        self.result = ValidationResult()
        validated_data = {}

        # Required fields for new diet records
        if not is_update:
            required_fields = ['current_weight', 'height']
            for field in required_fields:
                if not self._validate_required(data, field):
                    continue

        # Validate current weight
        if 'current_weight' in data and data['current_weight'] is not None:
            try:
                weight = float(data['current_weight'])
                if validate_weight(weight):
                    validated_data['current_weight'] = weight
                else:
                    self.result.add_error(
                        "Current weight must be between 1 and 1000 kg",
                        'current_weight', 'INVALID_WEIGHT'
                    )
            except (ValueError, TypeError):
                self.result.add_error(
                    "Current weight must be a valid number",
                    'current_weight', 'TYPE_ERROR'
                )

        # Validate target weight (optional)
        if 'target_weight' in data and data['target_weight'] is not None:
            try:
                target_weight = float(data['target_weight'])
                if validate_weight(target_weight):
                    validated_data['target_weight'] = target_weight
                else:
                    self.result.add_error(
                        "Target weight must be between 1 and 1000 kg",
                        'target_weight', 'INVALID_WEIGHT'
                    )
            except (ValueError, TypeError):
                self.result.add_error(
                    "Target weight must be a valid number",
                    'target_weight', 'TYPE_ERROR'
                )

        # Validate height
        if 'height' in data and data['height'] is not None:
            try:
                height = float(data['height'])
                if validate_height(height):
                    validated_data['height'] = height
                else:
                    self.result.add_error(
                        "Height must be between 30 and 300 cm",
                        'height', 'INVALID_HEIGHT'
                    )
            except (ValueError, TypeError):
                self.result.add_error(
                    "Height must be a valid number",
                    'height', 'TYPE_ERROR'
                )

        # Validate activity level
        if 'activity_level' in data and data['activity_level']:
            valid_levels = ['sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extra_active']
            if data['activity_level'] in valid_levels:
                validated_data['activity_level'] = data['activity_level']
            else:
                self.result.add_error(
                    f"Activity level must be one of: {', '.join(valid_levels)}",
                    'activity_level', 'INVALID_ACTIVITY_LEVEL'
                )

        # Validate weight goal
        if 'weight_goal' in data and data['weight_goal']:
            valid_goals = ['lose_weight', 'gain_weight', 'maintain_weight']
            if data['weight_goal'] in valid_goals:
                validated_data['weight_goal'] = data['weight_goal']
            else:
                self.result.add_error(
                    f"Weight goal must be one of: {', '.join(valid_goals)}",
                    'weight_goal', 'INVALID_WEIGHT_GOAL'
                )

        # Validate target date (optional)
        if 'target_date' in data and data['target_date']:
            if self._validate_target_date(data['target_date']):
                validated_data['target_date'] = data['target_date']

        # Validate water intake target
        if 'water_intake_target' in data and data['water_intake_target'] is not None:
            try:
                water_intake = float(data['water_intake_target'])
                if self._validate_range(water_intake, 500, 10000, 'water_intake_target', 'Water Intake Target'):
                    validated_data['water_intake_target'] = water_intake
            except (ValueError, TypeError):
                self.result.add_error(
                    "Water intake target must be a valid number",
                    'water_intake_target', 'TYPE_ERROR'
                )

        # Validate text fields
        text_fields = ['dietary_restrictions', 'food_preferences', 'supplements', 'notes']
        for field in text_fields:
            if field in data and data[field]:
                validated_data[field] = self._sanitize_string(data[field], 2000)

        self.result.data = validated_data
        return self.result.to_dict()

    def _validate_target_date(self, target_date: Any) -> bool:
        """Validate target date for weight goals"""
        try:
            if isinstance(target_date, str):
                if not validate_date(target_date):
                    self.result.add_error(
                        "Invalid target date format",
                        'target_date', 'INVALID_DATE'
                    )
                    return False
                target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            elif not isinstance(target_date, date):
                self.result.add_error(
                    "Target date must be a date string or date object",
                    'target_date', 'TYPE_ERROR'
                )
                return False

            # Check if date is in the future
            if target_date <= date.today():
                self.result.add_error(
                    "Target date must be in the future",
                    'target_date', 'PAST_DATE'
                )
                return False

            # Check if date is not too far in the future (2 years max)
            max_date = date.today() + timedelta(days=730)
            if target_date > max_date:
                self.result.add_warning(
                    "Target date is more than 2 years in the future",
                    'target_date', 'FAR_FUTURE'
                )

            return True

        except Exception as e:
            self.result.add_error(
                f"Error validating target date: {str(e)}",
                'target_date', 'VALIDATION_ERROR'
            )
            return False


class NutritionValidator(BaseValidator):
    """Validator for nutrition and meal plan data"""

    def validate_meal_plan_data(self, data: Dict[str, Any], is_update: bool = False) -> Dict[str, Any]:
        """Validate meal plan data"""
        self.result = ValidationResult()
        validated_data = {}

        # Validate plan date
        if 'plan_date' in data and data['plan_date']:
            if self._validate_plan_date(data['plan_date']):
                validated_data['plan_date'] = data['plan_date']

        # Validate meal fields
        meal_fields = ['breakfast', 'morning_snack', 'lunch', 'afternoon_snack', 'dinner', 'evening_snack']
        for field in meal_fields:
            if field in data and data[field]:
                meal_content = self._sanitize_string(data[field], 1000)
                if self._validate_length(meal_content, 1, 1000, field, field.replace('_', ' ').title()):
                    validated_data[field] = meal_content

        # Validate water intake
        if 'water_intake' in data and data['water_intake'] is not None:
            try:
                water_intake = float(data['water_intake'])
                if self._validate_range(water_intake, 0, 10000, 'water_intake', 'Water Intake'):
                    validated_data['water_intake'] = water_intake
            except (ValueError, TypeError):
                self.result.add_error(
                    "Water intake must be a valid number",
                    'water_intake', 'TYPE_ERROR'
                )

        # Validate notes
        if 'notes' in data and data['notes']:
            notes = self._sanitize_string(data['notes'], 1000)
            validated_data['notes'] = notes

        # Validate compliance status
        if 'is_followed' in data:
            if isinstance(data['is_followed'], bool):
                validated_data['is_followed'] = data['is_followed']
            else:
                self.result.add_error(
                    "Compliance status must be true or false",
                    'is_followed', 'TYPE_ERROR'
                )

        self.result.data = validated_data
        return self.result.to_dict()

    def _validate_plan_date(self, plan_date: Any) -> bool:
        """Validate meal plan date"""
        try:
            if isinstance(plan_date, str):
                if not validate_date(plan_date):
                    self.result.add_error(
                        "Invalid plan date format",
                        'plan_date', 'INVALID_DATE'
                    )
                    return False
                plan_date = datetime.strptime(plan_date, '%Y-%m-%d').date()
            elif not isinstance(plan_date, date):
                self.result.add_error(
                    "Plan date must be a date string or date object",
                    'plan_date', 'TYPE_ERROR'
                )
                return False

            # Check if date is not too far in the past (1 year max)
            min_date = date.today() - timedelta(days=365)
            if plan_date < min_date:
                self.result.add_warning(
                    "Plan date is more than 1 year in the past",
                    'plan_date', 'OLD_DATE'
                )

            # Check if date is not too far in the future (1 month max)
            max_date = date.today() + timedelta(days=30)
            if plan_date > max_date:
                self.result.add_warning(
                    "Plan date is more than 1 month in the future",
                    'plan_date', 'FAR_FUTURE'
                )

            return True

        except Exception as e:
            self.result.add_error(
                f"Error validating plan date: {str(e)}",
                'plan_date', 'VALIDATION_ERROR'
            )
            return False


class ReportValidator(BaseValidator):
    """Validator for report generation data"""

    def validate_client_report_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate client report data"""
        self.result = ValidationResult()
        validated_data = {}

        # Validate client data exists
        if 'client' not in data or not data['client']:
            self.result.add_error(
                "Client data is required for report generation",
                'client', 'REQUIRED'
            )
        else:
            client_data = data['client']
            if not isinstance(client_data, dict):
                self.result.add_error(
                    "Client data must be a dictionary",
                    'client', 'TYPE_ERROR'
                )
            else:
                # Validate required client fields
                required_fields = ['id', 'full_name']
                for field in required_fields:
                    if field not in client_data or not client_data[field]:
                        self.result.add_error(
                            f"Client {field} is required",
                            f'client.{field}', 'REQUIRED'
                        )

                validated_data['client'] = client_data

        # Validate include sections
        if 'include_sections' in data and data['include_sections']:
            if isinstance(data['include_sections'], list):
                validated_data['include_sections'] = data['include_sections']
            else:
                self.result.add_error(
                    "Include sections must be a list",
                    'include_sections', 'TYPE_ERROR'
                )

        # Validate generation options
        if 'generation_options' in data and data['generation_options']:
            if isinstance(data['generation_options'], dict):
                validated_data['generation_options'] = data['generation_options']
            else:
                self.result.add_error(
                    "Generation options must be a dictionary",
                    'generation_options', 'TYPE_ERROR'
                )

        self.result.data = validated_data
        return self.result.to_dict()

    def validate_diet_report_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate diet report data"""
        self.result = ValidationResult()
        validated_data = {}

        # Validate client data
        if 'client' not in data or not data['client']:
            self.result.add_error(
                "Client data is required for diet report",
                'client', 'REQUIRED'
            )
        else:
            validated_data['client'] = data['client']

        # Validate date range
        if 'date_range' in data and data['date_range']:
            date_range = data['date_range']
            if isinstance(date_range, dict):
                if 'start_date' in date_range and 'end_date' in date_range:
                    try:
                        start_date = datetime.fromisoformat(date_range['start_date']).date()
                        end_date = datetime.fromisoformat(date_range['end_date']).date()

                        if start_date > end_date:
                            self.result.add_error(
                                "Start date must be before end date",
                                'date_range', 'INVALID_RANGE'
                            )
                        else:
                            validated_data['date_range'] = date_range
                    except ValueError:
                        self.result.add_error(
                            "Invalid date format in date range",
                            'date_range', 'INVALID_DATE'
                        )
                else:
                    self.result.add_error(
                        "Date range must include start_date and end_date",
                        'date_range', 'INCOMPLETE'
                    )
            else:
                self.result.add_error(
                    "Date range must be a dictionary",
                    'date_range', 'TYPE_ERROR'
                )

        self.result.data = validated_data
        return self.result.to_dict()


class AuthValidator(BaseValidator):
    """Validator for authentication and user data"""

    def validate_login_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate login credentials"""
        self.result = ValidationResult()
        validated_data = {}

        # Validate username
        if self._validate_required(data, 'username', 'Username'):
            username = self._sanitize_string(data['username'], 100)
            if self._validate_length(username, 3, 100, 'username', 'Username'):
                validated_data['username'] = username

        # Validate password
        if self._validate_required(data, 'password', 'Password'):
            password = data['password']  # Don't sanitize passwords
            if len(password) > 0:
                validated_data['password'] = password
            else:
                self.result.add_error(
                    "Password cannot be empty",
                    'password', 'EMPTY_PASSWORD'
                )

        self.result.data = validated_data
        return self.result.to_dict()

    def validate_user_data(self, data: Dict[str, Any], is_update: bool = False) -> Dict[str, Any]:
        """Validate user creation/update data"""
        self.result = ValidationResult()
        validated_data = {}

        # Required fields for new users
        if not is_update:
            required_fields = ['username', 'email', 'password', 'role']
            for field in required_fields:
                if not self._validate_required(data, field):
                    continue

        # Validate username
        if 'username' in data and data['username']:
            username = self._sanitize_string(data['username'], 50)
            if self._validate_length(username, 3, 50, 'username', 'Username'):
                if re.match(r'^[a-zA-Z0-9_-]+$', username):
                    validated_data['username'] = username
                else:
                    self.result.add_error(
                        "Username can only contain letters, numbers, hyphens, and underscores",
                        'username', 'INVALID_CHARS'
                    )

        # Validate email
        if 'email' in data and data['email']:
            email = self._sanitize_string(data['email'], 255)
            if validate_email(email):
                validated_data['email'] = email.lower()
            else:
                self.result.add_error(
                    "Invalid email address format",
                    'email', 'INVALID_EMAIL'
                )

        # Validate password (for new users or password changes)
        if 'password' in data and data['password']:
            password = data['password']
            password_result = validate_password(password)
            if password_result['is_valid']:
                validated_data['password'] = password
            else:
                for suggestion in password_result['suggestions']:
                    self.result.add_error(suggestion, 'password', 'WEAK_PASSWORD')

        # Validate role
        if 'role' in data and data['role']:
            valid_roles = ['admin', 'pharmacist', 'nutritionist', 'assistant', 'viewer']
            if data['role'] in valid_roles:
                validated_data['role'] = data['role']
            else:
                self.result.add_error(
                    f"Role must be one of: {', '.join(valid_roles)}",
                    'role', 'INVALID_ROLE'
                )

        # Validate is_active flag
        if 'is_active' in data:
            if isinstance(data['is_active'], bool):
                validated_data['is_active'] = data['is_active']
            else:
                self.result.add_error(
                    "Active status must be true or false",
                    'is_active', 'TYPE_ERROR'
                )

        self.result.data = validated_data
        return self.result.to_dict()

    def validate_password(self, password: str) -> Dict[str, Any]:
        """Validate password strength"""
        password_result = validate_password(password)

        return {
            'is_valid': password_result['is_valid'],
            'errors': password_result['suggestions'] if not password_result['is_valid'] else [],
            'warnings': [],
            'data': {'password': password} if password_result['is_valid'] else {}
        }


class ValidationMixin:
    """
    Mixin class providing common validation functionality for UI widgets.

    This mixin can be inherited by PyQt6 widgets to add validation capabilities
    without requiring changes to the widget hierarchy.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._validation_errors = {}
        self._validation_warnings = {}

    def validate_field(self, field_name: str, value: Any, validator_func=None) -> bool:
        """
        Validate a single field value.

        Args:
            field_name: Name of the field being validated
            value: Value to validate
            validator_func: Optional custom validator function

        Returns:
            bool: True if validation passes, False otherwise
        """
        try:
            if validator_func:
                result = validator_func(value)
                if not result:
                    self._validation_errors[field_name] = "Validation failed"
                    return False

            # Clear any existing errors for this field
            if field_name in self._validation_errors:
                del self._validation_errors[field_name]

            return True

        except Exception as e:
            self._validation_errors[field_name] = str(e)
            return False

    def add_validation_error(self, field_name: str, error_message: str):
        """Add a validation error for a field."""
        self._validation_errors[field_name] = error_message

    def add_validation_warning(self, field_name: str, warning_message: str):
        """Add a validation warning for a field."""
        self._validation_warnings[field_name] = warning_message

    def clear_validation_errors(self):
        """Clear all validation errors."""
        self._validation_errors.clear()

    def clear_validation_warnings(self):
        """Clear all validation warnings."""
        self._validation_warnings.clear()

    def get_validation_errors(self) -> Dict[str, str]:
        """Get all validation errors."""
        return self._validation_errors.copy()

    def get_validation_warnings(self) -> Dict[str, str]:
        """Get all validation warnings."""
        return self._validation_warnings.copy()

    def has_validation_errors(self) -> bool:
        """Check if there are any validation errors."""
        return bool(self._validation_errors)

    def has_validation_warnings(self) -> bool:
        """Check if there are any validation warnings."""
        return bool(self._validation_warnings)


# Convenience validator instances for common use
ClientValidation = ClientValidator()
MedicalValidation = MedicalValidator()
NutritionValidation = NutritionValidator()
ReportValidation = ReportValidator()
AuthValidation = AuthValidator()
