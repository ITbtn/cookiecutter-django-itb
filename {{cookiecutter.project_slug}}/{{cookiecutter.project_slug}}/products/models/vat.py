from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from {{cookiecutter.project_slug}}.common.validators import ScreenMethodValidator

from .base import ProductBase


class VAT(ProductBase):
    validators = [ScreenMethodValidator]

    name = models.CharField(
        max_length=256, verbose_name=_("Name"), help_text=_("Name of product.")
    )
    percent_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Value"),
        help_text=_("Value in percent"),
    )
    is_default = models.BooleanField(
        default=False, verbose_name=_("Default vat"), help_text=_("Default vat")
    )

    def __str__(self):
        return self.name

    def screen_is_default(self):
        if (
            self.is_default
            and self.__class__.objects.filter(
                tenant_code=self.tenant_code,
                is_available=True,
                is_default=True,
            )
            .exclude(id=self.id)
            .exists()
        ):
            raise ValidationError(
                message=f"Tenant ({self.tenant_code}) already has a default vat."
            )
