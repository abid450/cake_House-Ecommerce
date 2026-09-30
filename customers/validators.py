# apps/customers/validators.py

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class StrongPasswordValidator:
    """
    Strong Password Validator
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - At least 1 special character
    """
    
    def __init__(self, min_length=8):
        self.min_length = min_length
    
    def validate(self, password, user=None):
        errors = []
        
        # Check minimum length
        if len(password) < self.min_length:
            errors.append(f'পাসওয়ার্ড কমপক্ষে {self.min_length} অক্ষর হতে হবে।')
        
        # Check uppercase
        if not re.search(r'[A-Z]', password):
            errors.append('পাসওয়ার্ডে কমপক্ষে ১টি বড় হাতের অক্ষর (A-Z) থাকতে হবে।')
        
        # Check lowercase
        if not re.search(r'[a-z]', password):
            errors.append('পাসওয়ার্ডে কমপক্ষে ১টি ছোট হাতের অক্ষর (a-z) থাকতে হবে।')
        
        # Check digit
        if not re.search(r'[0-9]', password):
            errors.append('পাসওয়ার্ডে কমপক্ষে ১টি সংখ্যা (0-9) থাকতে হবে।')
        
        # Check special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', password):
            errors.append('পাসওয়ার্ডে কমপক্ষে ১টি বিশেষ চিহ্ন (!@#$%^&* ইত্যাদি) থাকতে হবে।')
        
        # Check for common passwords
        common_passwords = [
            'password', 'password123', '12345678', 'qwerty123', 
            'admin123', 'letmein', 'welcome', 'abc12345',
            'password1', 'admin1234', '123456789', 'qwertyuiop'
        ]
        if password.lower() in common_passwords:
            errors.append('এই পাসওয়ার্ডটি খুব সাধারণ। অন্য পাসওয়ার্ড ব্যবহার করুন।')
        
        # Check for sequential characters
        if re.search(r'(012|123|234|345|456|567|678|789|890|abc|bcd|cde|def)', password.lower()):
            errors.append('পাসওয়ার্ডে ধারাবাহিক অক্ষর বা সংখ্যা ব্যবহার করবেন না।')
        
        # Check if password contains username
        if user and hasattr(user, 'username') and user.username:
            if user.username.lower() in password.lower():
                errors.append('পাসওয়ার্ডে আপনার ইউজারনেম থাকতে পারবে না।')
        
        # Check if password contains email
        if user and hasattr(user, 'email') and user.email:
            email_parts = user.email.split('@')[0]
            if email_parts.lower() in password.lower():
                errors.append('পাসওয়ার্ডে আপনার ইমেইলের অংশ থাকতে পারবে না।')
        
        # Raise error if any issues
        if errors:
            raise ValidationError(errors)
    
    def get_help_text(self):
        return _(
            "পাসওয়ার্ডে অবশ্যই থাকতে হবে:\n"
            "• কমপক্ষে ৮টি অক্ষর\n"
            "• ১টি বড় হাতের অক্ষর (A-Z)\n"
            "• ১টি ছোট হাতের অক্ষর (a-z)\n"
            "• ১টি সংখ্যা (0-9)\n"
            "• ১টি বিশেষ চিহ্ন (!@#$%^&*)"
        )


class PasswordStrengthValidator:
    """
    Password strength checker with score calculation
    """
    
    COMMON_PASSWORDS = [
        'password', 'password123', '12345678', 'qwerty123',
        'admin123', 'letmein', 'welcome', 'abc12345',
        'password1', 'admin1234', '123456789', 'qwertyuiop',
        '123456', 'password', '123456789', 'qwerty',
        'admin', 'welcome', 'letmein', 'monkey',
    ]
    
    @staticmethod
    def calculate_strength(password):
        """
        Calculate password strength score (0-100)
        """
        if not password:
            return 0
        
        score = 0
        
        # Length scoring
        if len(password) >= 8:
            score += 20
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 10
        
        # Character variety
        if re.search(r'[A-Z]', password):
            score += 15
        if re.search(r'[a-z]', password):
            score += 15
        if re.search(r'[0-9]', password):
            score += 15
        if re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', password):
            score += 15
        
        # Penalties
        if password.lower() in PasswordStrengthValidator.COMMON_PASSWORDS:
            score -= 50
        
        if re.search(r'(.)\1{2,}', password):  # Repeated characters
            score -= 10
        
        if re.search(r'(012|123|234|345|456|567|678|789|890)', password):
            score -= 10
        
        if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password.lower()):
            score -= 10
        
        return max(0, min(100, score))
    
    @staticmethod
    def get_strength_label(score):
        """
        Get label for password strength
        """
        if score < 30:
            return {'label': 'দুর্বল', 'color': '#dc2626', 'icon': 'fa-times-circle'}
        elif score < 60:
            return {'label': 'মাঝারি', 'color': '#f59e0b', 'icon': 'fa-exclamation-triangle'}
        elif score < 80:
            return {'label': 'ভালো', 'color': '#3b82f6', 'icon': 'fa-info-circle'}
        else:
            return {'label': 'শক্তিশালী', 'color': '#22c55e', 'icon': 'fa-check-circle'}
    
    @staticmethod
    def get_requirements_status(password):
        """
        Get status of each requirement
        """
        return {
            'length': {
                'label': 'কমপক্ষে ৮ অক্ষর',
                'met': len(password) >= 8 if password else False,
            },
            'uppercase': {
                'label': '১টি বড় হাতের অক্ষর (A-Z)',
                'met': bool(re.search(r'[A-Z]', password)) if password else False,
            },
            'lowercase': {
                'label': '১টি ছোট হাতের অক্ষর (a-z)',
                'met': bool(re.search(r'[a-z]', password)) if password else False,
            },
            'digit': {
                'label': '১টি সংখ্যা (0-9)',
                'met': bool(re.search(r'[0-9]', password)) if password else False,
            },
            'special': {
                'label': '১টি বিশেষ চিহ্ন (!@#$%^&*)',
                'met': bool(re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', password)) if password else False,
            },
        }
    
    @staticmethod
    def validate_password_strength(password):
        """
        Validate password and return list of errors
        """
        errors = []
        
        if not password:
            errors.append('পাসওয়ার্ড প্রয়োজন।')
            return errors
        
        if len(password) < 8:
            errors.append('কমপক্ষে ৮ অক্ষর হতে হবে।')
        
        if not re.search(r'[A-Z]', password):
            errors.append('কমপক্ষে ১টি বড় হাতের অক্ষর (A-Z) থাকতে হবে।')
        
        if not re.search(r'[a-z]', password):
            errors.append('কমপক্ষে ১টি ছোট হাতের অক্ষর (a-z) থাকতে হবে।')
        
        if not re.search(r'[0-9]', password):
            errors.append('কমপক্ষে ১টি সংখ্যা (0-9) থাকতে হবে।')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', password):
            errors.append('কমপক্ষে ১টি বিশেষ চিহ্ন (!@#$%^&*) থাকতে হবে।')
        
        if password.lower() in PasswordStrengthValidator.COMMON_PASSWORDS:
            errors.append('এই পাসওয়ার্ডটি খুব সাধারণ।')
        
        return errors


# Validate function for Django settings
def validate_password_strength(password):
    """Wrapper function for Django settings"""
    validator = StrongPasswordValidator()
    validator.validate(password)