"""
Base serializers package for Django REST Framework.

This package provides secure, reusable base serializers for consistent
API input/output handling across the application.

Components:
- BaseInputSerializer: Secure input validation with automatic XSS protection
- BaseOutputSerializer: Consistent output formatting with common utilities
- SecuredCharField: XSS-protected CharField replacement
- Security validators: Script injection and malicious content detection

Usage:
    from {{cookiecutter.project_slug}}.common.bases.serializers import (
        BaseInputSerializer,
        BaseOutputSerializer,
        SecuredCharField,
    )
    
    class UserInputSerializer(BaseInputSerializer):
        name = serializers.CharField(max_length=100)  # Auto-converted to SecuredCharField
        email = serializers.EmailField()
    
    class UserOutputSerializer(BaseOutputSerializer):
        id = serializers.IntegerField()
        name = serializers.CharField()
        email = serializers.EmailField()
        created_at = serializers.DateTimeField()
"""

from .custom_fields import SecuredCharField
from .custom_validators import remove_diacritics, validate_script_in_text
from .input import BaseInputSerializer
from .output import BaseOutputSerializer

__all__ = [
    # Base serializer classes
    'BaseInputSerializer',
    'BaseOutputSerializer',
    
    # Custom fields
    'SecuredCharField',
    
    # Validators and utilities
    'validate_script_in_text',
    'remove_diacritics',
]

# Version information
__version__ = '1.0.0'
__author__ = '{{cookiecutter.author_name}}'
