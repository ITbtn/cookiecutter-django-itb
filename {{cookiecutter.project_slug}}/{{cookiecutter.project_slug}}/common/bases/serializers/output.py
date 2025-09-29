from typing import Any, Dict, Optional, Type

from rest_framework import serializers


class BaseOutputSerializer(serializers.Serializer):
    """
    Base serializer for output/response data with common functionality.
    
    This serializer provides a foundation for all output serializers with:
    - Consistent data formatting and presentation
    - Common fields and methods for API responses
    - Type safety and documentation
    - Extensibility for specific use cases
    
    Features:
    - Consistent Output: Provides standardized output format
    - Type Safety: Includes type hints for better development experience
    - Extensibility: Can be extended by child serializers
    - Documentation: Well-documented for team understanding
    
    Usage:
        # Basic usage
        class UserOutputSerializer(BaseOutputSerializer):
            id = serializers.IntegerField()
            name = serializers.CharField()
            email = serializers.EmailField()
            created_at = serializers.DateTimeField()
            
        # With custom methods
        class ProductOutputSerializer(BaseOutputSerializer):
            id = serializers.IntegerField()
            name = serializers.CharField()
            price = serializers.DecimalField(max_digits=10, decimal_places=2)
            
            def get_formatted_price(self, obj):
                return f"${obj.price:.2f}"
    
    Note:
        This class focuses on output serialization and doesn't include
        input validation features like SecuredCharField conversion.
    """

    class Meta:
        abstract = True
    
    def to_representation(self, instance: Any) -> Dict[str, Any]:
        """
        Convert model instance to serialized representation.
        
        This method can be overridden in child classes to customize
        the output format or add additional processing.
        
        Args:
            instance: The model instance or data to serialize
            
        Returns:
            Dictionary representation of the serialized data
        """
        return super().to_representation(instance)
    
    def get_extra_context(self) -> Dict[str, Any]:
        """
        Get additional context data that might be useful for serialization.
        
        This method can be overridden in child classes to provide
        additional context data (like request user, permissions, etc.)
        
        Returns:
            Dictionary of extra context data
        """
        context = {}
        
        # Add request user if available
        if hasattr(self, 'context') and 'request' in self.context:
            request = self.context['request']
            if hasattr(request, 'user'):
                context['current_user'] = request.user
        
        return context
    
    def format_datetime_field(self, datetime_value: Any, format_string: Optional[str] = None) -> Optional[str]:
        """
        Format datetime fields consistently across all output serializers.
        
        Args:
            datetime_value: The datetime value to format
            format_string: Custom format string (defaults to ISO format)
            
        Returns:
            Formatted datetime string or None if value is None/empty
        """
        if not datetime_value:
            return None
            
        if hasattr(datetime_value, 'isoformat'):
            return datetime_value.isoformat() if not format_string else datetime_value.strftime(format_string)
        
        return str(datetime_value)
