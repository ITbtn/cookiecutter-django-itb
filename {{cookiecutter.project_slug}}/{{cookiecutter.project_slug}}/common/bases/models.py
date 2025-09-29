import uuid
from typing import Any, Optional

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords

User = get_user_model()


class UUIDModel(models.Model):
    """
    Abstract base model that provides UUID as a unique identifier.
    
    Features:
    - Standard Django id as primary key (internal use)
    - UUID4 field for external references (API exposure)
    - Auto-generated UUIDs with database indexing
    - String representation using UUID
    """
    
    uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
        help_text="Unique identifier for external references"
    )
    
    class Meta:
        abstract = True
    
    def __str__(self) -> str:
        """Return string representation using UUID."""
        return str(self.uuid)


class TimeStampedModel(models.Model):
    """
    Abstract base model that provides timestamp fields and user tracking.
    
    Features:
    - Automatic created_at and updated_at timestamps
    - User tracking fields for created_by and updated_by
    - Timezone-aware timestamps
    
    Note:
    - User tracking fields must be set manually in views/services
    - No reverse relations are created (related_name="+")
    """
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the record was created"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
        help_text="User who created this record"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the record was last updated"
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
        help_text="User who last updated this record"
    )
    
    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Abstract base model that provides soft delete functionality.
    
    Features:
    - Soft delete with is_deleted field
    - Restore functionality
    - Deleted timestamp and user tracking
    - Override delete method to perform soft delete by default
    """
    
    is_deleted = models.BooleanField(
        default=False,
        help_text="Mark record as deleted instead of removing from database"
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the record was soft deleted"
    )
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
        help_text="User who soft deleted this record"
    )
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False, user=None, hard_delete=False):
        """
        Override delete to perform soft delete by default.
        
        :param using: Database alias
        :param keep_parents: Keep parent records
        :param user: User performing the deletion
        :param hard_delete: Force hard delete if True
        """
        if hard_delete:
            super().delete(using=using, keep_parents=keep_parents)
        else:
            self.soft_delete(user=user)
    
    def soft_delete(self, user=None):
        """
        Perform soft delete by setting is_deleted=True.
        
        :param user: User performing the deletion
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])
    
    def restore(self, user=None):
        """
        Restore a soft-deleted record.
        
        :param user: User performing the restoration
        """
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        
        # Update updated_by if this is a timestamped model
        if hasattr(self, 'updated_by') and user:
            self.updated_by = user
        
        update_fields = ['is_deleted', 'deleted_at', 'deleted_by']
        if hasattr(self, 'updated_by'):
            update_fields.append('updated_by')
        
        self.save(update_fields=update_fields)


class TenantModel(models.Model):
    """
    Abstract base model that provides tenant support.
    
    Features:
    - Tenant code field for multi-tenancy
    - Database indexing on tenant_code for performance
    """
    
    tenant_code = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Tenant identifier for multi-tenancy"
    )
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['tenant_code']),
        ]


class BaseGlobalModel(UUIDModel, TimeStampedModel, SoftDeleteModel):
    """
    Base model combining UUID, timestamps, and soft delete functionality.
    
    This is the base class for global models that don't require tenant isolation.
    
    Features:
    - Standard Django id as primary key (internal)
    - UUID field for external API references
    - Timestamp tracking (created_at, updated_at, created_by, updated_by)
    - Soft delete functionality
    
    Usage:
        class GlobalSettings(BaseGlobalModel):
            name = models.CharField(max_length=100)
            value = models.TextField()
            
            class Meta:
                verbose_name = "Global Setting"
                verbose_name_plural = "Global Settings"
    """
    
    class Meta:
        abstract = True


class BaseTenantModel(UUIDModel, TimeStampedModel, SoftDeleteModel, TenantModel):
    """
    Base model for tenant-aware models with full functionality.
    
    This combines all base functionality for tenant-specific models.
    
    Features:
    - Standard Django id as primary key (internal)
    - UUID field for external API references
    - Timestamp tracking
    - Soft delete functionality
    - Tenant isolation
    
    Usage:
        class Product(BaseTenantModel):
            name = models.CharField(max_length=100)
            description = models.TextField()
            price = models.DecimalField(max_digits=10, decimal_places=2)
            
            class Meta:
                verbose_name = "Product"
                verbose_name_plural = "Products"
                constraints = [
                    models.UniqueConstraint(
                        fields=['tenant_code', 'name'],
                        name='unique_product_name_per_tenant'
                    )
                ]
    """
    
    class Meta:
        abstract = True


class BaseHistoricalModel(BaseTenantModel):
    """
    Base model with historical tracking enabled.
    
    This extends BaseTenantModel with django-simple-history integration.
    
    Features:
    - All BaseTenantModel features
    - Historical record tracking with HistoricalRecords
    - Change tracking and audit trail
    
    Usage:
        class ImportantDocument(BaseHistoricalModel):
            title = models.CharField(max_length=200)
            content = models.TextField()
            
            class Meta:
                verbose_name = "Important Document"
                verbose_name_plural = "Important Documents"
    """
    
    history = HistoricalRecords(inherit=True)
    
    class Meta:
        abstract = True


class BaseGlobalHistoricalModel(BaseGlobalModel):
    """
    Base model for global models with historical tracking.
    
    Features:
    - All BaseGlobalModel features
    - Historical record tracking with HistoricalRecords
    - No tenant isolation
    
    Usage:
        class SystemAuditLog(BaseGlobalHistoricalModel):
            action = models.CharField(max_length=100)
            details = models.JSONField()
            
            class Meta:
                verbose_name = "System Audit Log"
                verbose_name_plural = "System Audit Logs"
    """
    
    history = HistoricalRecords(inherit=True)
    
    class Meta:
        abstract = True
