"""
Validation Utilities
Provides data validation functions for the Pharmacy Management System
"""

import re
import phonenumbers
from typing import Any, Optional, List, Dict, Union
from datetime import datetime, date
from phonenumbers import NumberParseException


def validate_email(email: str) -> bool:
    """
    Validate email address format

    Args:
        email: Email address to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False

    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email.strip()) is not None


def validate_phone(phone: str, country_code: str = None) -> bool:
    """
    Validate phone number format

    Args:
        phone: Phone number to validate
        country_code: Country code (e.g., 'EG' for Egypt, 'US' for United States)

    Returns:
        bool: True if valid, False otherwise
    """
    if not phone or not isinstance(phone, str):
        return False

    try:
        # Clean the phone number
        phone = phone.strip()

        # Try to parse with phonenumbers library
        if country_code:
            parsed_number = phonenumbers.parse(phone, country_code)
        else:
            # Try to parse with international format
            if not phone.startswith('+'):
                phone = '+' + phone
            parsed_number = phonenumbers.parse(phone, None)

        return phonenumbers.is_valid_number(parsed_number)

    except NumberParseException:
        # Fallback to basic regex validation
        phone_pattern = r'^[\+]?[1-9][\d]{7,14}$'
        return re.match(phone_pattern, re.sub(r'[\s\-\(\)]', '', phone)) is not None


def validate_age(age: Union[int, str]) -> bool:
    """
    Validate age value

    Args:
        age: Age to validate

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        age_int = int(age)
        return 0 <= age_int <= 150
    except (ValueError, TypeError):
        return False


def validate_weight(weight: Union[float, str]) -> bool:
    """
    Validate weight value in kg

    Args:
        weight: Weight to validate

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        weight_float = float(weight)
        return 1.0 <= weight_float <= 1000.0  # Reasonable weight range
    except (ValueError, TypeError):
        return False


def validate_height(height: Union[float, str]) -> bool:
    """
    Validate height value in cm

    Args:
        height: Height to validate

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        height_float = float(height)
        return 30.0 <= height_float <= 300.0  # Reasonable height range
    except (ValueError, TypeError):
        return False


def validate_percentage(percentage: Union[float, str]) -> bool:
    """
    Validate percentage value (0-100)

    Args:
        percentage: Percentage to validate

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        percentage_float = float(percentage)
        return 0.0 <= percentage_float <= 100.0
    except (ValueError, TypeError):
        return False


def validate_blood_pressure(systolic: Union[int, str], diastolic: Union[int, str]) -> bool:
    """
    Validate blood pressure values

    Args:
        systolic: Systolic pressure
        diastolic: Diastolic pressure

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        sys_int = int(systolic)
        dia_int = int(diastolic)

        # Reasonable blood pressure ranges
        return (70 <= sys_int <= 300 and
                40 <= dia_int <= 200 and
                sys_int > dia_int)
    except (ValueError, TypeError):
        return False


def validate_heart_rate(heart_rate: Union[int, str]) -> bool:
    """
    Validate heart rate value

    Args:
        heart_rate: Heart rate to validate

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        hr_int = int(heart_rate)
        return 30 <= hr_int <= 300  # Reasonable heart rate range
    except (ValueError, TypeError):
        return False


def validate_blood_sugar(blood_sugar: Union[float, str]) -> bool:
    """
    Validate blood sugar level (mg/dL)

    Args:
        blood_sugar: Blood sugar level to validate

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        bs_float = float(blood_sugar)
        return 20.0 <= bs_float <= 600.0  # Reasonable blood sugar range
    except (ValueError, TypeError):
        return False


def validate_date(date_value: Union[str, date, datetime]) -> bool:
    """
    Validate date value

    Args:
        date_value: Date to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if isinstance(date_value, (date, datetime)):
        return True

    if not isinstance(date_value, str):
        return False

    # Try common date formats
    date_formats = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%m/%d/%Y',
        '%Y/%m/%d',
        '%d-%m-%Y',
        '%m-%d-%Y'
    ]

    for fmt in date_formats:
        try:
            datetime.strptime(date_value.strip(), fmt)
            return True
        except ValueError:
            continue

    return False


def validate_pharmacy_id(pharmacy_id: str) -> bool:
    """
    Validate pharmacy ID format

    Args:
        pharmacy_id: Pharmacy ID to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not pharmacy_id or not isinstance(pharmacy_id, str):
        return False

    # Allow numeric IDs (5 digits) or alphanumeric IDs
    pharmacy_id = pharmacy_id.strip()

    # Check for numeric format (5 digits)
    if pharmacy_id.isdigit() and len(pharmacy_id) == 5:
        return True

    # Check for alphanumeric format (3-20 characters)
    if re.match(r'^[A-Za-z0-9]{3,20}$', pharmacy_id):
        return True

    return False


def validate_password(password: str, min_length: int = 8) -> Dict[str, Any]:
    """
    Validate password strength

    Args:
        password: Password to validate
        min_length: Minimum password length

    Returns:
        dict: Validation result with score and requirements
    """
    result = {
        'is_valid': False,
        'score': 0,
        'requirements': {
            'min_length': False,
            'has_uppercase': False,
            'has_lowercase': False,
            'has_digit': False,
            'has_special': False
        },
        'suggestions': []
    }

    if not password or not isinstance(password, str):
        result['suggestions'].append('كلمة المرور مطلوبة')
        return result

    # Check minimum length
    if len(password) >= min_length:
        result['requirements']['min_length'] = True
        result['score'] += 1
    else:
        result['suggestions'].append(f'يجب أن تحتوي كلمة المرور على {min_length} أحرف على الأقل')

    # Check for uppercase letter
    if re.search(r'[A-Z]', password):
        result['requirements']['has_uppercase'] = True
        result['score'] += 1
    else:
        result['suggestions'].append('يجب أن تحتوي على حرف كبير واحد على الأقل')

    # Check for lowercase letter
    if re.search(r'[a-z]', password):
        result['requirements']['has_lowercase'] = True
        result['score'] += 1
    else:
        result['suggestions'].append('يجب أن تحتوي على حرف صغير واحد على الأقل')

    # Check for digit
    if re.search(r'\d', password):
        result['requirements']['has_digit'] = True
        result['score'] += 1
    else:
        result['suggestions'].append('يجب أن تحتوي على رقم واحد على الأقل')

    # Check for special character
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result['requirements']['has_special'] = True
        result['score'] += 1
    else:
        result['suggestions'].append('يجب أن تحتوي على رمز خاص واحد على الأقل')

    # Password is valid if it meets at least 3 requirements
    result['is_valid'] = result['score'] >= 3

    return result


def validate_arabic_text(text: str, allow_english: bool = True) -> bool:
    """
    Validate Arabic text

    Args:
        text: Text to validate
        allow_english: Whether to allow English characters

    Returns:
        bool: True if valid, False otherwise
    """
    if not text or not isinstance(text, str):
        return False

    text = text.strip()
    if not text:
        return False

    # Arabic Unicode range
    arabic_pattern = r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]'

    # Check if text contains Arabic characters
    has_arabic = re.search(arabic_pattern, text) is not None

    if allow_english:
        # Allow Arabic, English, numbers, spaces, and common punctuation
        valid_pattern = r'^[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFFa-zA-Z0-9\s\.,\-_!?()]+$'
        return re.match(valid_pattern, text) is not None
    else:
        # Only Arabic characters, numbers, spaces, and common punctuation
        valid_pattern = r'^[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF0-9\s\.,\-_!?()]+$'
        return has_arabic and re.match(valid_pattern, text) is not None


def validate_client_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate complete client data

    Args:
        data: Client data dictionary

    Returns:
        dict: Validation result
    """
    errors = []
    warnings = []

    # Required fields
    required_fields = ['client_name', 'age', 'phone']
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f'الحقل {field} مطلوب')

    # Validate specific fields
    if 'client_name' in data and data['client_name']:
        if not validate_arabic_text(data['client_name']):
            warnings.append('اسم العميل يحتوي على أحرف غير صالحة')

    if 'age' in data and data['age']:
        if not validate_age(data['age']):
            errors.append('العمر غير صالح')

    if 'phone' in data and data['phone']:
        if not validate_phone(data['phone']):
            errors.append('رقم الهاتف غير صالح')

    if 'email' in data and data['email']:
        if not validate_email(data['email']):
            errors.append('البريد الإلكتروني غير صالح')

    if 'client_pharmacy_id' in data and data['client_pharmacy_id']:
        if not validate_pharmacy_id(data['client_pharmacy_id']):
            errors.append('رقم العميل بالصيدلية غير صالح')

    return {
        'is_valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


def validate_diet_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate diet/nutrition data

    Args:
        data: Diet data dictionary

    Returns:
        dict: Validation result
    """
    errors = []
    warnings = []

    # Validate measurements
    if 'height' in data and data['height']:
        if not validate_height(data['height']):
            errors.append('الطول غير صالح')

    if 'current_weight' in data and data['current_weight']:
        if not validate_weight(data['current_weight']):
            errors.append('الوزن الحالي غير صالح')

    if 'previous_weight' in data and data['previous_weight']:
        if not validate_weight(data['previous_weight']):
            errors.append('الوزن السابق غير صالح')

    # Validate body composition percentages
    percentage_fields = ['fat_percentage', 'muscle_percentage', 'water_percentage', 'mineral_percentage']
    for field in percentage_fields:
        if field in data and data[field]:
            if not validate_percentage(data[field]):
                errors.append(f'{field} غير صالح')

    # Validate vital signs
    if 'blood_pressure_systolic' in data and 'blood_pressure_diastolic' in data:
        if data['blood_pressure_systolic'] and data['blood_pressure_diastolic']:
            if not validate_blood_pressure(data['blood_pressure_systolic'], data['blood_pressure_diastolic']):
                errors.append('ضغط الدم غير صالح')

    if 'heart_rate' in data and data['heart_rate']:
        if not validate_heart_rate(data['heart_rate']):
            errors.append('معدل ضربات القلب غير صالح')

    if 'blood_sugar' in data and data['blood_sugar']:
        if not validate_blood_sugar(data['blood_sugar']):
            errors.append('مستوى السكر في الدم غير صالح')

    # Check for reasonable BMI if height and weight are provided
    if ('height' in data and data['height'] and
        'current_weight' in data and data['current_weight']):
        try:
            height_m = float(data['height']) / 100
            weight_kg = float(data['current_weight'])
            bmi = weight_kg / (height_m ** 2)

            if bmi < 10 or bmi > 80:
                warnings.append('قيم الطول والوزن قد تكون غير دقيقة (BMI غير طبيعي)')
        except (ValueError, ZeroDivisionError):
            pass

    return {
        'is_valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


def sanitize_input(text: str, max_length: int = None) -> str:
    """
    Sanitize user input text

    Args:
        text: Text to sanitize
        max_length: Maximum allowed length

    Returns:
        str: Sanitized text
    """
    if not isinstance(text, str):
        return ''

    # Remove leading/trailing whitespace
    text = text.strip()

    # Remove control characters except newlines and tabs
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

    # Limit length if specified
    if max_length and len(text) > max_length:
        text = text[:max_length]

    return text


def validate_file_path(file_path: str, allowed_extensions: List[str] = None) -> bool:
    """
    Validate file path and extension

    Args:
        file_path: File path to validate
        allowed_extensions: List of allowed file extensions

    Returns:
        bool: True if valid, False otherwise
    """
    if not file_path or not isinstance(file_path, str):
        return False

    # Check for path traversal attempts
    if '..' in file_path or file_path.startswith('/'):
        return False

    # Check file extension if specified
    if allowed_extensions:
        file_extension = file_path.lower().split('.')[-1]
        return file_extension in [ext.lower().lstrip('.') for ext in allowed_extensions]

    return True
