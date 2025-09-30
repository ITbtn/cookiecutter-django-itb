from django.db import models
from django.utils.translation import gettext_lazy as _

from {{cookiecutter.project_slug}}.common.models import HistoricalLogBase
from {{cookiecutter.project_slug}}.common.utils import generate_unique_code


class ProductSeriesDimensionalAttribute(HistoricalLogBase):
    # Product series wise dimensional attributes
    code = models.CharField(max_length=128, help_text=_("Unique code reference"))
    is_available = models.BooleanField(
        default=True, help_text=_("if TRUE the record is available")
    )
    product_attribute = models.ForeignKey(
        "products.ProductAttribute",
        on_delete=models.PROTECT,
        related_name="series_dimensional_attr",
        help_text=_("Product and its dimensional attributes of a series"),
    )
    series = models.ForeignKey(
        "products.Series",
        on_delete=models.PROTECT,
        related_name="series_dimensional_attr",
        verbose_name=_("Product Series"),
        help_text=_("The product series"),
    )

    class Meta(HistoricalLogBase.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["product_attribute", "series"],
                name="unique_product_series_dimensional_attribute",
            )
        ]
        indexes = [
            models.Index(fields=["code"]),
        ]

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if not self.code:
            self.code = generate_unique_code()
        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return f"{self.product_attribute} - {self.series}"
