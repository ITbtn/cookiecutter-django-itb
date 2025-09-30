from django.db import models
from django.utils.translation import gettext_lazy as _

from {{cookiecutter.project_slug}}.common.models.base import CodeBaseHistoryModel


class ProductGroupAttribute(CodeBaseHistoryModel):
    product_group = models.ForeignKey(
        "products.ProductGroup",
        on_delete=models.PROTECT,
        related_name="product_group_attributes",
    )
    attribute = models.ForeignKey(
        "attributes.Attribute",
        on_delete=models.PROTECT,
        related_name="product_group_attributes",
    )
    is_searchable = models.BooleanField(
        default=False,
        verbose_name=_("Searchable"),
        help_text=_("Is this attribute searchable"),
    )
    is_dimensional = models.BooleanField(
        default=False,
        verbose_name=_("Dimensional"),
        help_text=_("Is this attribute dimesional"),
    )

    def __str__(self):
        return f"Product Group: {self.product_group}, Attribute: {self.attribute}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product_group", "attribute"],
                name="unique_product_group_and_attribute",
            )
        ]
