from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from {{cookiecutter.project_slug}}.common.validators import ScreenMethodValidator
from {{cookiecutter.project_slug}}.products.models.base import ProductBase
from {{cookiecutter.project_slug}}.products.models.page_layout import PageLayout


class ProductGroup(ProductBase):
    validators = [ScreenMethodValidator]
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subgroups",
        help_text=_("id from PRODUCTS_PRODUCTGROUP (self)."),
    )
    name = models.CharField(max_length=128, help_text=_("Name of the Group."))
    slug = models.SlugField(
        max_length=256, blank=True, default="", help_text=_("Unique slug for the URL.")
    )
    description = models.TextField(
        blank=True, default="", help_text=_("Description of the product group.")
    )
    valid_from = models.DateTimeField(
        null=True, blank=True, help_text=_("Start date of the Group.")
    )
    valid_until = models.DateTimeField(
        null=True, blank=True, help_text=_("End date of the Group.")
    )
    min_product = models.IntegerField(
        blank=True,
        default=1,
        verbose_name=_("Minimum product"),
        help_text=_("Minimum product allowed"),
    )
    max_product = models.IntegerField(
        blank=True,
        default=9999,
        verbose_name=_("Maximum product"),
        help_text=_("Maximum allowed product"),
    )
    page_layout = models.ForeignKey(
        PageLayout,
        related_name="product_groups",
        on_delete=models.CASCADE,
        help_text=_("Page layout for the product group."),
        blank=True,
        null=True,
    )
    sort_order = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Sort order"),
        help_text=_("Order to sort product"),
    )
    purchase_financial_number = models.CharField(
        max_length=256,
        blank=True,
        default="",
        verbose_name=_("Purchase financial number"),
    )
    sales_financial_number = models.CharField(
        max_length=256,
        blank=True,
        default="",
        verbose_name=_("Sales financial number"),
    )

    class Meta(ProductBase.Meta):
        verbose_name_plural = _("Product Group")
        ordering = ["sort_order", "-id"]

    def __str__(self):
        # Need to specify format
        return self.name

    def screen_min_product(self):
        if self.min_product < 0:
            raise ValidationError(message="Minimum product should not be less than 0.")

    def screen_max_product(self):
        if self.min_product > self.max_product:
            raise ValidationError(
                message="Maximum product should not be less than minimum product."
            )
