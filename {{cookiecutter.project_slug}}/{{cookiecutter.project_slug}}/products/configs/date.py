from django.utils.translation import gettext_lazy as _


class ProductDateType:

    DEFAULT = "default"

    CHOICES = [
        (DEFAULT, _("Default date type")),
    ]
