from django.db import models
from django.utils.translation import gettext_lazy as _

from {{cookiecutter.project_slug}}.products.configs.relation_config import CommonRelationType
from {{cookiecutter.project_slug}}.products.models.base import ProductBase
from {{cookiecutter.project_slug}}.products.models.product import Product


class ProductRelation(ProductBase):
    relation_type = models.CharField(max_length=50, choices=CommonRelationType.CHOICES)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="relation_product",
        help_text=_("id from PRODUCTS_PRODUCT to select the Product."),
    )
    product_to = models.ForeignKey(
        Product,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="relation_product_to",
        help_text=_("id from PRODUCTS_PRODUCT to select the related Product."),
    )
    required_product = models.ForeignKey(
        Product,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="required_product",
        help_text=_(
            "If a required product is defined, the relation between 2 products is only valid when the combination "
            "of products also has the defined required product."
        ),
    )
    is_mandatory = models.BooleanField(
        default=False, help_text=_("If true then the relation is mandatory.")
    )
    is_single = models.BooleanField(
        default=False, help_text=_("If true then only a one way relation will be made.")
    )
    is_default = models.BooleanField(
        default=False,
        help_text=_(
            "If true then relation will be displayed as selected, "
            "by default on the product detail page."
        ),
    )
    is_exclude = models.BooleanField(
        default=False,
        help_text=_("If true then the products cannot be selected together."),
    )
    valid_from = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("The datetime from when the relation is valid."),
    )
    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("The datetime when the relation will expire."),
    )
    last_import_update = models.DateTimeField(
        blank=True, null=True, help_text=_("Last import date.")
    )

    class Meta(ProductBase.Meta):
        indexes = [
            models.Index(fields=["relation_type", "product"]),
            models.Index(fields=["tenant_code", "code"]),
        ]
