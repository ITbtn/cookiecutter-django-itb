from django.db import models
from django.utils.translation import gettext_lazy as _

from {{cookiecutter.project_slug}}.attributes.models import AttributeRelator


class ProductAttribute(AttributeRelator):
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="product_attributes",
        help_text=_("Related product"),
    )

    class Meta(AttributeRelator.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_code", "code"],
                name="product_attr_unique_tenant_wise_code",
            ),
            models.UniqueConstraint(
                fields=["product", "attribute"], name="unique_product_and_attribute"
            ),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.attribute.name}"
