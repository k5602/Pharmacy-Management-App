"""
Utils Package
Utility functions and helper classes for the Pharmacy Management System v2.0

This package contains common utility functions and helper classes that are used
throughout the application:

- Validators: Data validation functions for various input types
- Formatters: Text and data formatting utilities
- Resource Manager: Application resource loading and management
- Helpers: Common helper functions for various operations
- Decorators: Useful decorators for logging, caching, etc.
- Constants: Application-wide constants and enums

These utilities provide reusable functionality that supports the MVC architecture
without containing business logic or UI components.
"""

from typing import Any, Optional, Dict, List, Callable
import re
from datetime import datetime, date

# Import validators
try:
    from .validators import (
        validate_email,
        validate_phone,
        validate_age,
        validate_weight,
        validate_height,
        validate_percentage,
        validate_blood_pressure,
        validate_heart_rate,
        validate_blood_sugar,
        validate_date,
        validate_pharmacy_id,
        validate_password,
        validate_arabic_text,
        validate_client_data,
        validate_diet_data,
        sanitize_input,
        validate_file_path
    )
except ImportError:
    # Validators not available
    validate_email = None
    validate_phone = None
    validate_age = None
    validate_weight = None
    validate_height = None
    validate_percentage = None
    validate_blood_pressure = None
    validate_heart_rate = None
    validate_blood_sugar = None
    validate_date = None
    validate_pharmacy_id = None
    validate_password = None
    validate_arabic_text = None
    validate_client_data = None
    validate_diet_data = None
    sanitize_input = None
    validate_file_path = None

# Import resource manager
try:
    from .resource_manager import ResourceManager, get_resource_manager
except ImportError:
    ResourceManager = None
    get_resource_manager = None

# Version information
__version__ = "2.0.0"
__author__ = "Khaled Alam"

# Common constants
DEFAULT_DATE_FORMAT = "%Y-%m-%d"
DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_TIME_FORMAT = "%H:%M:%S"

# Arabic text constants
ARABIC_UNICODE_RANGE = r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]'

# Common regex patterns
PATTERNS = {
    'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    'phone': r'^[\+]?[1-9][\d]{7,14}$',
    'pharmacy_id': r'^[A-Za-z0-9]{3,20}$',
    'arabic_text': ARABIC_UNICODE_RANGE,
    'numeric': r'^\d+(\.\d+)?$',
    'integer': r'^\d+$'
}

def format_date(date_obj: Any, format_str: str = DEFAULT_DATE_FORMAT) -> str:
    """
    Format date object to string

    Args:
        date_obj: Date object (datetime, date, or string)
        format_str: Format string

    Returns:
        str: Formatted date string
    """
    try:
        if isinstance(date_obj, str):
            # Try to parse string first
            date_obj = datetime.strptime(date_obj, format_str).date()
        elif isinstance(date_obj, datetime):
            date_obj = date_obj.date()

        if isinstance(date_obj, date):
            return date_obj.strftime(format_str)

        return str(date_obj)

    except Exception:
        return str(date_obj) if date_obj else ""

def format_datetime(datetime_obj: Any, format_str: str = DEFAULT_DATETIME_FORMAT) -> str:
    """
    Format datetime object to string

    Args:
        datetime_obj: Datetime object
        format_str: Format string

    Returns:
        str: Formatted datetime string
    """
    try:
        if isinstance(datetime_obj, str):
            # Try to parse string first
            datetime_obj = datetime.strptime(datetime_obj, format_str)

        if isinstance(datetime_obj, datetime):
            return datetime_obj.strftime(format_str)

        return str(datetime_obj)

    except Exception:
        return str(datetime_obj) if datetime_obj else ""

def format_arabic_text(text: str) -> str:
    """
    Format Arabic text for proper display

    Args:
        text: Arabic text to format

    Returns:
        str: Formatted Arabic text
    """
    try:
        if not text:
            return ""

        # Try to import Arabic text processing libraries
        try:
            import arabic_reshaper
            from bidi.algorithm import get_display

            reshaped_text = arabic_reshaper.reshape(text)
            bidi_text = get_display(reshaped_text)
            return bidi_text

        except ImportError:
            # Fallback to original text if libraries not available
            return text

    except Exception:
        return text

def format_number(number: Any, decimal_places: int = 2) -> str:
    """
    Format number with specified decimal places

    Args:
        number: Number to format
        decimal_places: Number of decimal places

    Returns:
        str: Formatted number string
    """
    try:
        if number is None:
            return ""

        float_number = float(number)
        return f"{float_number:.{decimal_places}f}"

    except (ValueError, TypeError):
        return str(number) if number is not None else ""

def format_percentage(value: Any, decimal_places: int = 1) -> str:
    """
    Format value as percentage

    Args:
        value: Value to format (0-100)
        decimal_places: Number of decimal places

    Returns:
        str: Formatted percentage string
    """
    try:
        if value is None:
            return ""

        float_value = float(value)
        return f"{float_value:.{decimal_places}f}%"

    except (ValueError, TypeError):
        return str(value) if value is not None else ""

def format_phone(phone: str) -> str:
    """
    Format phone number for display

    Args:
        phone: Phone number string

    Returns:
        str: Formatted phone number
    """
    try:
        if not phone:
            return ""

        # Remove non-digit characters
        digits = re.sub(r'\D', '', phone)

        if len(digits) >= 10:
            # Format as (XXX) XXX-XXXX for 10+ digits
            if len(digits) == 10:
                return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
            else:
                # International format
                return f"+{digits[:-10]} ({digits[-10:-7]}) {digits[-7:-4]}-{digits[-4:]}"

        return phone

    except Exception:
        return phone

def safe_cast(value: Any, target_type: type, default: Any = None) -> Any:
    """
    Safely cast value to target type

    Args:
        value: Value to cast
        target_type: Target type
        default: Default value if casting fails

    Returns:
        Any: Casted value or default
    """
    try:
        if value is None:
            return default

        return target_type(value)

    except (ValueError, TypeError):
        return default

def is_empty(value: Any) -> bool:
    """
    Check if value is empty (None, empty string, empty list, etc.)

    Args:
        value: Value to check

    Returns:
        bool: True if empty, False otherwise
    """
    if value is None:
        return True
    elif isinstance(value, str):
        return value.strip() == ""
    elif isinstance(value, (list, dict, tuple)):
        return len(value) == 0
    elif isinstance(value, (int, float)):
        return False
    else:
        return not bool(value)

def clean_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Clean and sanitize text input

    Args:
        text: Text to clean
        max_length: Maximum length to truncate to

    Returns:
        str: Cleaned text
    """
    if not text:
        return ""

    # Remove leading/trailing whitespace
    cleaned = text.strip()

    # Remove control characters except newlines and tabs
    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', cleaned)

    # Truncate if needed
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length]

    return cleaned

def calculate_bmi(weight: float, height: float) -> Optional[float]:
    """
    Calculate BMI from weight and height

    Args:
        weight: Weight in kg
        height: Height in cm

    Returns:
        Optional[float]: BMI value or None if invalid input
    """
    try:
        if not weight or not height or weight <= 0 or height <= 0:
            return None

        height_m = height / 100  # Convert cm to meters
        bmi = weight / (height_m ** 2)
        return round(bmi, 2)

    except (ValueError, TypeError, ZeroDivisionError):
        return None

def get_bmi_category(bmi: float) -> str:
    """
    Get BMI category in Arabic

    Args:
        bmi: BMI value

    Returns:
        str: BMI category in Arabic
    """
    if bmi < 18.5:
        return "نقص الوزن"
    elif 18.5 <= bmi < 25:
        return "طبيعي"
    elif 25 <= bmi < 30:
        return "زيادة الوزن"
    elif 30 <= bmi < 35:
        return "سمنة درجة أولى"
    elif 35 <= bmi < 40:
        return "سمنة درجة ثانية"
    else:
        return "سمنة مفرطة"

def retry_on_exception(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator to retry function on exception

    Args:
        max_retries: Maximum number of retries
        delay: Delay between retries in seconds

    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            import time

            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep(delay)
                    else:
                        raise last_exception

        return wrapper
    return decorator

def cache_result(ttl_seconds: int = 300):
    """
    Decorator to cache function results

    Args:
        ttl_seconds: Time to live for cache in seconds

    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        cache = {}

        def wrapper(*args, **kwargs):
            import time

            # Create cache key
            key = str(args) + str(sorted(kwargs.items()))

            # Check if cached result is still valid
            if key in cache:
                result, timestamp = cache[key]
                if time.time() - timestamp < ttl_seconds:
                    return result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache[key] = (result, time.time())

            return result

        return wrapper
    return decorator

def get_utils_info():
    """Get information about available utilities"""
    return {
        "version": __version__,
        "available_validators": [
            name for name in globals()
            if name.startswith("validate_") and globals()[name] is not None
        ],
        "available_formatters": [
            "format_date", "format_datetime", "format_arabic_text",
            "format_number", "format_percentage", "format_phone"
        ],
        "available_helpers": [
            "safe_cast", "is_empty", "clean_text", "calculate_bmi",
            "get_bmi_category"
        ],
        "available_decorators": [
            "retry_on_exception", "cache_result"
        ]
    }

# Export commonly used items
__all__ = [
    # Validators
    "validate_email",
    "validate_phone",
    "validate_age",
    "validate_weight",
    "validate_height",
    "validate_percentage",
    "validate_blood_pressure",
    "validate_heart_rate",
    "validate_blood_sugar",
    "validate_date",
    "validate_pharmacy_id",
    "validate_password",
    "validate_arabic_text",
    "validate_client_data",
    "validate_diet_data",
    "sanitize_input",
    "validate_file_path",

    # Resource manager
    "ResourceManager",
    "get_resource_manager",

    # Formatters
    "format_date",
    "format_datetime",
    "format_arabic_text",
    "format_number",
    "format_percentage",
    "format_phone",

    # Helpers
    "safe_cast",
    "is_empty",
    "clean_text",
    "calculate_bmi",
    "get_bmi_category",

    # Decorators
    "retry_on_exception",
    "cache_result",

    # Constants
    "DEFAULT_DATE_FORMAT",
    "DEFAULT_DATETIME_FORMAT",
    "DEFAULT_TIME_FORMAT",
    "ARABIC_UNICODE_RANGE",
    "PATTERNS",

    # Utility functions
    "get_utils_info"
]
