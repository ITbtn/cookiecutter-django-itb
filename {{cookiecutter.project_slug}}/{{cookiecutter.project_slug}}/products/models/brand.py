from django.db import models
from django.utils.translation import gettext_lazy as _

from {{cookiecutter.project_slug}}.products.models.base import ProductBase


class Brand(ProductBase):
    name = models.CharField(max_length=128, help_text=_("Name of the Option Group"))
    description = models.TextField(
        default="", blank=True, help_text=_("Description of the Option Group")
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Sort Order"),
        help_text=_("Sort order."),
    )

    def __str__(self):
        # Need to specify format
        return self.name
