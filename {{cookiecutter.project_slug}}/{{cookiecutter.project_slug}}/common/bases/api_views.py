from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView

from .api_mixins import (
    CreateAPIMixin,
    ListAPIMixin,
    RetrieveAPIMixin,
    UpdateAPIMixin,
    DestroyAPIMixin,
    BaseAPIPermissionMixin,
)


class BaseGenericAPIView:
    """
    Base API view providing common functionality for all API views.
    
    This view provides:
    - Consistent serializer class selection based on HTTP method
    - Service initialization support for write operations
    - Selector initialization support for read operations
    - Input/Output serializer handling
    
    Architecture:
    - Uses selectors for read operations (GET)
    - Uses services for write operations (POST/PUT/PATCH/DELETE)
    """

    read_by = "uuid"  # Default lookup method
    service_class = None  # For write operations
    selector_class = None  # For read operations
    additional_permissions = []

    def initial(self, request, *args, **kwargs):
        """
        Initialize the view before processing the request.
        """
        super().initial(request, *args, **kwargs)
        self.init_services()

    def get_serializer_class(self):
        """
        Return the serializer class based on the HTTP method.
        
        For GET requests, uses output_serializer_class if available.
        For other requests, uses input_serializer_class if available.
        
        Returns:
            Serializer class
        """
        if self.request.method == "GET":
            if hasattr(self, "output_serializer_class") and self.output_serializer_class:
                return self.output_serializer_class
            elif hasattr(self, "output_serializer") and self.output_serializer:
                return self.output_serializer
        else:
            if hasattr(self, "input_serializer_class") and self.input_serializer_class:
                return self.input_serializer_class
            elif hasattr(self, "input_serializer") and self.input_serializer:
                return self.input_serializer
        
        return super().get_serializer_class()

    def get_input_serializer(self, *args, **kwargs):
        """
        Get an input serializer instance.
        
        Returns:
            Serializer instance for input validation
        """
        if hasattr(self, "input_serializer_class") and self.input_serializer_class:
            return self.input_serializer_class(*args, **kwargs)
        raise NotImplementedError("No input serializer class found")

    def get_output_serializer(self, *args, **kwargs):
        """
        Get an output serializer instance.
        
        Returns:
            Serializer instance for output formatting
        """
        if hasattr(self, "output_serializer_class") and self.output_serializer_class:
            return self.output_serializer_class(*args, **kwargs)
        raise NotImplementedError("No output serializer class found")

    def init_services(self):
        """
        Initialize any services and selectors needed by the view.
        
        This method initializes:
        - Selectors for read operations
        - Services for write operations
        
        Override this method to customize initialization.
        """
        # Initialize selector for read operations
        if hasattr(self, "selector_class") and self.selector_class:
            self.selector = self.selector_class()
            
        # Initialize service for write operations
        if hasattr(self, "service_class") and self.service_class:
            self.service = self.service_class()


class AbstractListAPIView(BaseGenericAPIView, ListAPIMixin, generics.ListAPIView):
    """
    Abstract base class for list API views.
    """
    pass


class AbstractCreateAPIView(BaseGenericAPIView, CreateAPIMixin, generics.CreateAPIView):
    """
    Abstract base class for create API views.
    """
    pass


class AbstractListCreateAPIView(BaseGenericAPIView, ListAPIMixin, CreateAPIMixin, generics.ListCreateAPIView):
    """
    Abstract base class for list and create API views.
    """
    pass


class AbstractRetrieveUpdateDestroyAPIView(BaseGenericAPIView, RetrieveAPIMixin, UpdateAPIMixin, DestroyAPIMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Abstract base class for retrieve, update and destroy API views.
    Uses selectors for read operations and services for write operations.
    """
    pass


class AbstractRetrieveUpdateAPIView(BaseGenericAPIView, RetrieveAPIMixin, UpdateAPIMixin, generics.RetrieveUpdateAPIView):
    """
    Abstract base class for retrieve and update API views.
    Uses selectors for read operations and services for write operations.
    """
    pass


class AbstractRetrieveAPIView(BaseGenericAPIView, RetrieveAPIMixin, generics.RetrieveAPIView):
    """
    Abstract base class for retrieve API views.
    Uses selectors for read operations.
    """
    pass


class AbstractUpdateAPIView(BaseGenericAPIView, UpdateAPIMixin, generics.UpdateAPIView):
    """
    Abstract base class for update API views.
    Uses services for write operations.
    """
    pass


class BaseListAPIView(BaseAPIPermissionMixin, AbstractListAPIView):
    """
    Base list API view with permission handling.
    
    Provides listing functionality with automatic filtering based on
    query parameters and permission checks.
    
    Uses selector_class for read operations.
    """
    pass


class BaseCreateAPIView(BaseAPIPermissionMixin, AbstractCreateAPIView):
    """
    Base create API view with permission handling.
    
    Provides object creation functionality with permission checks
    and optional output serializer for the response.
    
    Uses service_class for write operations.
    """
    pass


class BaseListCreateAPIView(BaseAPIPermissionMixin, AbstractListCreateAPIView):
    """
    Base list and create API view with permission handling.
    
    Combines listing and creation functionality in a single view.
    
    Uses selector_class for read operations and service_class for write operations.
    """
    pass


class BaseRetrieveAPIView(BaseAPIPermissionMixin, AbstractRetrieveAPIView):
    """
    Base retrieve API view with permission handling.
    
    Provides single object retrieval functionality.
    
    Uses selector_class for read operations.
    """
    pass


class BaseRetrieveUpdateAPIView(BaseAPIPermissionMixin, AbstractRetrieveUpdateAPIView):
    """
    Base retrieve and update API view with permission handling.
    
    Provides retrieval and update functionality for single objects.
    
    Uses selector_class for read operations and service_class for write operations.
    """
    pass


class BaseRetrieveUpdateDestroyAPIView(BaseAPIPermissionMixin, AbstractRetrieveUpdateDestroyAPIView):
    """
    Base retrieve, update and destroy API view with permission handling.
    
    Provides full CRUD functionality for single objects.
    
    Uses selector_class for read operations and service_class for write operations.
    """
    pass


class BaseUpdateAPIView(BaseAPIPermissionMixin, AbstractUpdateAPIView):
    """
    Base update API view with permission handling.
    
    Provides object update functionality with permission checks.
    
    Uses service_class for write operations.
    """
    pass
