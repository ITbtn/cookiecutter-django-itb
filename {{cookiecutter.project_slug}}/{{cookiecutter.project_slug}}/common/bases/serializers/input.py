from rest_framework import serializers

from .custom_fields import SecuredCharField


class BaseInputSerializer(serializers.Serializer):
    """
    Base serializer for input validation with built-in security features.

    This serializer automatically converts all CharField instances to SecuredCharField
    to provide built-in script injection protection.

    Features:
    - Automatic XSS protection: CharField → SecuredCharField conversion
    - Preserves all original field attributes and validators
    - Prevents infinite recursion during field processing
    - Extensible for child serializers

    Usage:
        class UserInputSerializer(BaseInputSerializer):
            name = serializers.CharField(max_length=100)  # Auto-secured
            email = serializers.EmailField()              # Unchanged
            bio = serializers.CharField()                 # Auto-secured

    Note:
        The field conversion happens once during get_fields() call with
        recursion prevention to ensure CharField instances are properly secured.
    """

    class Meta:
        abstract = True

    def get_fields(self):
        fields = super().get_fields()

        # Avoid modifying fields during validation
        # This is to prevent the infinite recursion
        if hasattr(self, '_fields_converted'):
            return fields

        # Mark that we've already processed the fields
        self._fields_converted = True

        # Replace all CharField instances with SecuredCharField for security
        for field_name, field in list(fields.items()):
            if isinstance(field, serializers.CharField) and not isinstance(field, SecuredCharField):
                field_kwargs = {
                    'required': field.required,
                    'allow_null': field.allow_null,
                    'allow_blank': getattr(field, 'allow_blank', False),
                    'default': field.default,
                    'initial': field.initial,
                    'source': field.source,
                    'label': field.label,
                    'help_text': field.help_text,
                    'style': field.style,
                    'error_messages': field.error_messages,
                    'validators': field.validators,
                    'max_length': getattr(field, 'max_length', None),
                    'min_length': getattr(field, 'min_length', None),
                    'trim_whitespace': getattr(field, 'trim_whitespace', True),
                }

                # Filter out None values and empty values to use field defaults
                field_kwargs = {k: v for k, v in field_kwargs.items() 
                              if v is not None and v != serializers.empty}

                # Create new SecuredCharField with preserved attributes
                fields[field_name] = SecuredCharField(**field_kwargs)

        return fields
