from django.db import models
from {{cookiecutter.project_slug}}.common.models import BaseHistoryModel
from django.utils.translation import gettext_lazy as _


class PageLayout(BaseHistoryModel):
    description = models.TextField(
        blank=True, default="", help_text=_("Description of the page layout.")
    )

    def __str__(self):
        return self.code + " - " + self.description
