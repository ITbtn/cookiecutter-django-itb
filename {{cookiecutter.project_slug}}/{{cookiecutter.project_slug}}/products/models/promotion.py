from django.db import models
from django.utils.translation import gettext_lazy as _

from {{cookiecutter.project_slug}}.products.models import Product
from {{cookiecutter.project_slug}}.products.models.base import ProductBase


class Promotion(ProductBase):
    description = models.CharField(max_length=255, help_text=_("Short description."))
    long_description = models.TextField(
        blank=True, default="", help_text=_("Long description.")
    )
    start_datetime = models.DateTimeField(help_text=_("Start date of promotion."))
    end_datetime = models.DateTimeField(help_text=_("End date of promotion."))
    extra_sac = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Extra SAC discount"),
    )
    discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Discount on package (price)."),
    )
    connection_cost_discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Discount on connection cost"),
    )
    connection_cost_discount_percentage = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Discount on connection cost in percentage."),
    )
    monthly_fee_discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Discount on monthly fee."),
    )
    monthly_fee_discount_percentage = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Discount on monthly fee in percentage."),
    )
    monthly_fee_discount_duration = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_(
            "How many months will the discount be applied. "
            "special values:\n-1: indefinitely, even after the "
            "contract period has expired\n-2: for the time of "
            "the contract period"
        ),
    )
    active = models.BooleanField(default=False, help_text=_("If promotion active now."))
    promotion_group = models.CharField(
        max_length=128, blank=True, default="", help_text=_("Promotion group.")
    )
    last_import_update = models.DateTimeField(help_text=_("Last import date."))
    products = models.ManyToManyField(
        Product,
        related_name="promotion_products",
        through="ProductPromotion",
        through_fields=("promotion", "product"),
    )
