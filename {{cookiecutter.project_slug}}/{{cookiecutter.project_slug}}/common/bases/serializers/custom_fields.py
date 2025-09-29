from rest_framework import serializers

from .custom_validators import validate_script_in_text


class SecuredCharField(serializers.CharField):
    """
    A CharField subclass that automatically applies script injection validation.
    
    This field extends the standard DRF CharField to include built-in protection
    against XSS and script injection attacks. It automatically adds the
    validate_script_in_text validator to prevent malicious content.
    
    Features:
    - Inherits all CharField functionality
    - Automatic XSS protection through validation
    - Script tag detection and prevention
    - HTML entity decoding for thorough validation
    - Diacritic normalization to prevent bypass attempts
    
    Usage:
        class MySerializer(serializers.Serializer):
            safe_text = SecuredCharField(max_length=100)
            # This field will automatically validate against script injection
    
    Note:
        This field is automatically used by BaseInputSerializer to replace
        all CharField instances for consistent security.
    """

    def __init__(self, **kwargs):
        """
        Initialize the SecuredCharField with script validation.
        
        Args:
            **kwargs: Standard CharField arguments (max_length, required, etc.)
        """
        super().__init__(**kwargs)
        # Add the validator if it's not already present
        if validate_script_in_text not in self.validators:
            self.validators.append(validate_script_in_text)
