from django.db import models

from {{cookiecutter.project_slug}}.common.models import AbstractBaseModel
from {{cookiecutter.project_slug}}.products.models.product import Product


class ProductChannel(AbstractBaseModel):
    channel = models.ForeignKey(
        "sales_context.Channel",
        on_delete=models.PROTECT,
        related_name="products",
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="channels"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "channel"], name="unique_product_channel"
            )
        ]
