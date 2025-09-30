from django.db import models
from django.utils.translation import gettext_lazy as _

from {{cookiecutter.project_slug}}.products.configs.product_config import ProductItemType
from {{cookiecutter.project_slug}}.products.models.base import ProductBase


class ProductType(ProductBase):
    name = models.CharField(max_length=50, help_text=_("Product type name."))
    system = models.BooleanField(
        default=False, help_text=_("System generated product type.")
    )
    description = models.TextField(
        blank=True, default="", help_text=_("Short description.")
    )
    system_type = models.CharField(
        max_length=20,
        choices=ProductItemType.CHOICES,
        default=ProductItemType.NONE_TYPE,
    )
    can_update_purchase_price = models.BooleanField(
        default=True,
        help_text=_("Purchase price of a product is updatable if True otherwise not."),
    )

    class Meta(ProductBase.Meta):
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["tenant_code", "code"]),
        ]

    def __str__(self):
        # Need to specify format
        return self.name
