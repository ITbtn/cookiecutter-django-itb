from typing import Type, TypeVar, Generic, Optional, Dict, Any, List

from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.utils import timezone

User = get_user_model()
T = TypeVar("T", bound=models.Model)


class BaseModelService(Generic[T]):
    """
    Base service class for handling business logic operations on Django models.
    Provides common CRUD operations with multi-tenancy support.
    
    Usage:
        class UserService(BaseModelService[User]):
            model_class = User
            selector_class = UserSelector
            
        service = UserService(tenant_code="tenant1", request_user=user)
        new_user = service.create({"name": "John", "email": "john@example.com"})
    """
    model_class: Type[T] = None
    selector_class = None

    def __init__(self, tenant_code: str, request_user):
        """
        Initialize the service with tenant context and requesting user.
        
        :param tenant_code: The tenant identifier for multi-tenancy
        :param request_user: The user making the request (for auditing/permissions)
        """
        self.tenant_code = tenant_code
        self.request_user = request_user
        self.selector: Optional[Any] = None
        
        # Validate required attributes
        if self.model_class is None:
            raise ValueError(f"{self.__class__.__name__} must define a model_class attribute")
        
        # Initialize selector if provided (only needs tenant_code)
        if self.selector_class is not None:
            self.selector = self.selector_class(tenant_code=self.tenant_code)
    
    def create(self, data: Dict[str, Any], **kwargs) -> T:
        """
        Create a new model instance with tenant context.
        
        :param data: Dictionary of field values for the new instance
        :param kwargs: Additional keyword arguments
        :return: Created model instance
        """
        # Add tenant context to data
        create_data = data.copy()
        create_data.setdefault('tenant_code', self.tenant_code)
        
        with transaction.atomic():
            # Validate data if model has a clean method
            instance = self.model_class(**create_data)
            if hasattr(instance, 'full_clean'):
                instance.full_clean()
            instance.save()
            return instance
    
    def update(self, instance: T, data: Dict[str, Any], **kwargs) -> T:
        """
        Update an existing model instance.
        
        :param instance: The model instance to update
        :param data: Dictionary of field values to update
        :param kwargs: Additional keyword arguments
        :return: Updated model instance
        """
        with transaction.atomic():
            for field, value in data.items():
                if hasattr(instance, field):
                    setattr(instance, field, value)
            
            if hasattr(instance, 'full_clean'):
                instance.full_clean()
            instance.save()
            return instance
    
    def delete(self, instance: T, soft_delete: bool = True, **kwargs) -> bool:
        """
        Delete or soft-delete a model instance.
        
        :param instance: The model instance to delete
        :param soft_delete: If True, performs soft delete; if False, hard delete
        :param kwargs: Additional keyword arguments
        :return: True if deletion was successful
        """
        with transaction.atomic():
            if soft_delete:
                if hasattr(instance, 'is_active'):
                    instance.is_active = False
                if hasattr(instance, 'deleted_at'):
                    instance.deleted_at = timezone.now()
                instance.save()
            else:
                instance.delete()
            return True
    
    def bulk_create(self, data_list: List[Dict[str, Any]], **kwargs) -> List[T]:
        """
        Create multiple model instances efficiently.
        
        :param data_list: List of dictionaries with field values
        :param kwargs: Additional keyword arguments
        :return: List of created model instances
        """
        instances = []
        for data in data_list:
            create_data = data.copy()
            create_data.setdefault('tenant_code', self.tenant_code)
            instances.append(self.model_class(**create_data))
        
        with transaction.atomic():
            return self.model_class.objects.bulk_create(instances, **kwargs)

    def bulk_update(self, instances: List[T], fields: List[str], **kwargs) -> int:
        """
        Update multiple model instances efficiently.
        
        :param instances: List of model instances to update
        :param fields: List of fields to update
        :param kwargs: Additional keyword arguments
        :return: Number of rows updated
        """
        with transaction.atomic():
            return self.model_class.objects.bulk_update(instances, fields, **kwargs)
    