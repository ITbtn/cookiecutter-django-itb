from django.db import models
from django.utils.translation import gettext_lazy as _

from {{cookiecutter.project_slug}}.products.models.base import ProductBase


class Family(ProductBase):
    export_id = None
    name = models.CharField(max_length=128, help_text=_("Name of the product family"))
    description = models.TextField(
        default="", blank=True, help_text=_("Description of the product family")
    )

    def __str__(self):
        return self.name


class Series(ProductBase):
    export_id = None
    family = models.ForeignKey(
        Family,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Product Family"),
        help_text=_("Product family of the series"),
    )
    name = models.CharField(max_length=128, help_text=_("Name of the product series"))
    description = models.TextField(
        default="", blank=True, help_text=_("Description of the product series")
    )

    def __str__(self):
        return self.name
