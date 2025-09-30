from django.db import models
from django.utils.translation import gettext_lazy as _

from {{cookiecutter.project_slug}}.products.models.base import ProductBase
from ..configs.lineup import LineupType
from {{cookiecutter.project_slug}}.common.validators import ScreenMethodValidator


class Lineup(ProductBase):
    validators = [ScreenMethodValidator]

    name = models.CharField(max_length=128, help_text=_("Name of the lineup"))
    description = models.TextField(
        blank=True, default="", help_text=_("Description of the lineup")
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name=_("Default lineup"),
        help_text=_("Default lineup for specific type")
    )
    lineup_type = models.CharField(
        max_length=20,
        choices=LineupType.CHOICES,
        default=LineupType.VOICE
    )

    def __str__(self):
        return self.name

    def screen_is_default(self):
        if self.is_default and self.__class__.objects.filter(is_default=True, lineup_type=self.lineup_type).exclude(id=self.id).exists():
            return {"is_default": ["Default lineup already exists for {}.".format(self.lineup_type)]}
        else:
            return
