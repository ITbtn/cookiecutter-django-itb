from django.utils.translation import gettext_lazy as _

from {{cookiecutter.project_slug}}.common.utils import add_choices


@add_choices
class LineupType:
    VOICE = "voice"
    DATA = "data"
