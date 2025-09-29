from django.core.exceptions import ObjectDoesNotExist, ValidationError
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class CreateAPIMixin:
    """
    Create API mixin
    """

    def prepare_raw_data(self, request, *args, **kwargs):
        """
        Prepare data to be saved. By default it's request.data.
        Override this method if you want to update the posted raw data.

        :param request: request
        :param args: additional positional arguments
        :param kwargs: additional keyword arguments
        :return: Data to be saved
        """
        request_data = request.data
        # Write you code here to update raw posted data
        return request_data

    def create(self, request, *args, **kwargs):
        """
        This method overrides the 'create' method of 'CreateModelMixin' class of DRF.
        prepare_raw_data method is used to get raw data instead of request.data.
        :param request: request
        :param args: additional positional arguments
        :param kwargs: additional keyword arguments
        :return: HTTP response with saved data
        """

        raw_data = self.prepare_raw_data(request, *args, **kwargs)
        serializer = self.get_serializer(data=raw_data)
        # TODO(Iftekhar): can be done with self.check_serializer, have to check later.
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        #  The following line is commented out because we are not using uuid for now.
        # if serializer.instance:
        #     serializer.data.update({"uuid": serializer.instance.uuid})
        if (
            serializer.instance
            and hasattr(self, "output_serializer_class")
            and self.output_serializer_class
        ):
            output_serializer = self.output_serializer_class(serializer.instance, context=self.get_serializer_context())
            headers = self.get_success_headers(output_serializer.data)
            return Response(
                output_serializer.data, status=status.HTTP_201_CREATED, headers=headers
            )
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer):
        """
        Perform the actual creation of the object using service.
        
        This method uses the service pattern for write operations.
        Service class is required for create operations.
        
        Args:
            serializer: The validated serializer instance
        """
        if not hasattr(self, 'service_class') or not self.service_class:
            raise NotImplementedError(
                "Views using CreateAPIMixin must define a service_class attribute"
            )
        
        try:
            # Initialize service (services don't require tenant/user context like selectors)
            service = self.service_class()
            
            # Add tenant_code to validated data if available
            create_data = serializer.validated_data.copy()
            tenant_code = getattr(self.request, 'tenant_code', None)
            if tenant_code and 'tenant_code' not in create_data:
                create_data['tenant_code'] = tenant_code
            
            # Use service create method
            instance = service.create(**create_data)
            serializer.instance = instance
            
        except ValidationError as ex:
            if hasattr(ex, "message_dict"):
                raise DRFValidationError(ex.message_dict)
            else:
                raise DRFValidationError(ex)
        except ObjectDoesNotExist as ex:
            raise NotFound(detail=str(ex))


class BaseQuerysetMixin:
    """
    Base mixin to handle query parameters and queryset retrieval.
    
    This mixin provides common functionality for filtering querysets
    based on request parameters. Uses selectors for read operations.
    """

    def prepare_query_params_dict(self):
        """
        Prepare query parameter dictionary from request query parameters.
        
        Override this method to customize query parameter processing.
        
        Returns:
            dict: Processed query parameters
        """
        return dict(self.request.query_params)
    
    def get_base_queryset(self, query_params_dict=None):
        """
        Get the base queryset for this view using selector.
        
        Args:
            query_params_dict: Dictionary of query parameters for filtering
            
        Returns:
            QuerySet: The base queryset for this view
        """
        if query_params_dict is None:
            query_params_dict = {}
            
        # Use selector_class for read operations
        if not hasattr(self, 'selector_class') or not self.selector_class:
            raise NotImplementedError(
                "Views using BaseQuerysetMixin must define a selector_class attribute"
            )
        
        # Initialize selector with tenant and user context
        tenant_code = getattr(self.request, 'tenant_code', None)
        request_user = getattr(self.request, 'user', None)
        
        if not tenant_code:
            raise ValueError("tenant_code is required for selector operations")
            
        selector = self.selector_class(
            tenant_code=tenant_code,
            request_user=request_user
        )
        
        # Use get_filtered_qs method
        return selector.get_filtered_qs(**query_params_dict)
    


class RetrieveAPIMixin(BaseQuerysetMixin):
    """
    Mixin for retrieving single objects using selectors.
    
    Provides functionality to retrieve objects by UUID or code using
    selector pattern for read operations.
    """
    
    # Default read method - can be overridden
    read_by = "uuid"

    def get_queryset(self):
        """
        Get the queryset for object retrieval using selector.
        
        Returns:
            QuerySet: Filtered queryset from selector
        """
        query_params_dict = self.prepare_query_params_dict()
        return self.get_base_queryset(query_params_dict)

    def get_object(self):
        """
        Retrieve a single object using selector methods.
        
        Returns:
            Model instance: The retrieved object
            
        Raises:
            NotFound: If object doesn't exist
        """
        if not hasattr(self, 'selector_class') or not self.selector_class:
            raise NotImplementedError(
                "Views using RetrieveAPIMixin must define a selector_class attribute"
            )
        
        # Initialize selector with tenant and user context
        tenant_code = getattr(self.request, 'tenant_code', None)
        request_user = getattr(self.request, 'user', None)
        
        if not tenant_code:
            raise ValueError("tenant_code is required for selector operations")
            
        selector = self.selector_class(
            tenant_code=tenant_code,
            request_user=request_user
        )
        
        query_params_dict = self.prepare_query_params_dict()
        
        try:
            if self.read_by == "code":
                lookup_value = self.kwargs.get("code")
                if not lookup_value:
                    raise NotFound("No code provided")
                return selector.get_by_code(lookup_value, filters=query_params_dict)
            else:
                lookup_value = self.kwargs.get("uuid")
                if not lookup_value:
                    raise NotFound("No uuid provided")
                return selector.get_by_uuid(lookup_value, filters=query_params_dict)
        except ObjectDoesNotExist:
            field_name = "code" if self.read_by == "code" else "uuid"
            raise NotFound(f"Object with {field_name} '{lookup_value}' not found")


class ListAPIMixin(BaseQuerysetMixin):
    """
    Mixin for listing objects using selectors.
    
    Provides functionality for listing objects with filtering and pagination
    support using selector pattern for read operations.
    """
    
    def get_queryset(self):
        """
        Get the queryset for listing objects using selector.
        
        Returns:
            QuerySet: Filtered and optionally sorted queryset from selector
        """
        query_params_dict = self.prepare_query_params_dict()
        
        # Add sorting if specified
        if hasattr(self, "sort_order"):
            query_params_dict["sort_order"] = self.sort_order

        return self.get_base_queryset(query_params_dict)

    def list(self, request, *args, **kwargs):
        """
        List objects with pagination support using selector.
        
        Returns:
            Response: Paginated list of objects
        """
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UpdateAPIMixin:
    """
    Mixin for updating objects using services.
    
    Provides functionality to update objects using service pattern
    for write operations.
    """
    
    def perform_update(self, serializer):
        """
        Perform the actual update of the object using service.
        
        This method uses the service pattern for write operations.
        Service class is required for update operations.
        
        Args:
            serializer: The validated serializer instance
        """
        if not hasattr(self, 'service_class') or not self.service_class:
            raise NotImplementedError(
                "Views using UpdateAPIMixin must define a service_class attribute"
            )
        
        try:
            # Initialize service
            service = self.service_class()
            
            # Use service update method
            instance = service.update(serializer.instance, **serializer.validated_data)
            serializer.instance = instance
            
        except ValidationError as ex:
            if hasattr(ex, "message_dict"):
                raise DRFValidationError(ex.message_dict)
            else:
                raise DRFValidationError(ex)
        except ObjectDoesNotExist as ex:
            raise NotFound(detail=str(ex))


class DestroyAPIMixin:
    """
    Mixin for deleting objects using services.
    
    Provides functionality to delete objects using service pattern
    for write operations.
    """
    
    def perform_destroy(self, instance):
        """
        Perform the actual deletion of the object using service.
        
        This method uses the service pattern for write operations.
        Service class is required for delete operations.
        
        Args:
            instance: The model instance to delete
        """
        if not hasattr(self, 'service_class') or not self.service_class:
            raise NotImplementedError(
                "Views using DestroyAPIMixin must define a service_class attribute"
            )
        
        try:
            # Initialize service
            service = self.service_class()
            
            # Use service delete method (try both delete and destroy method names)
            if hasattr(service, 'delete'):
                service.delete(instance)
            elif hasattr(service, 'destroy'):
                service.destroy(instance)
            else:
                raise NotImplementedError(
                    f"Service {service.__class__.__name__} must implement either 'delete' or 'destroy' method"
                )
            
        except ValidationError as ex:
            if hasattr(ex, "message_dict"):
                raise DRFValidationError(ex.message_dict)
            else:
                raise DRFValidationError(ex)
        except ObjectDoesNotExist as ex:
            raise NotFound(detail=str(ex))


class BaseAPIPermissionMixin:
    """
    Base mixin for API permissions.
    
    Provides a foundation for implementing custom permission logic
    with support for exempt URLs for anonymous users.
    """
    
    additional_permissions = []
    exempt_urls = []  # URLs that allow anonymous access

    def get_permissions(self):
        """
        Return the list of permissions required for this view.
        
        Checks if the current URL is in exempt_urls for anonymous access.
        
        Returns:
            list: List of permission instances
        """
        permissions = super().get_permissions() if hasattr(super(), 'get_permissions') else []
        
        # Check if current URL is exempt from authentication
        try:
            current_url_name = self.request.resolver_match.url_name if self.request.resolver_match else None
            if current_url_name not in self.exempt_urls:
                # Require authentication for non-exempt URLs
                permissions.append(IsAuthenticated())
        except Exception:
            # If URL resolution fails, require authentication by default
            permissions.append(IsAuthenticated())
        
        # Add any additional permissions specified by the view
        if hasattr(self, 'additional_permissions') and self.additional_permissions:
            permissions.extend([perm() for perm in self.additional_permissions])
        
        return permissions
