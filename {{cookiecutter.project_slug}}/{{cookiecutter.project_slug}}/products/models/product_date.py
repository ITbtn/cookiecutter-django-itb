from django.db import models
from .product import Product
from {{cookiecutter.project_slug}}.common.models import base
from django.utils.translation import gettext_lazy as _
from {{cookiecutter.project_slug}}.products.configs.date import ProductDateType


class ProductDate(base.BaseHistoryModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="product_dates",
        help_text=_("Product of which dates are saved")
    )
    date_type = models.CharField(
        max_length=255,
        choices=ProductDateType.CHOICES,
        default=ProductDateType.DEFAULT,
        help_text=_("The type of date saved for the product")
    )
    date_value = models.DateField(
        null=True,
        blank=True,
        help_text=_("The date value of 'date_type' of the product")
    )
