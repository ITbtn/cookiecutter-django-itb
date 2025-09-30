from django.db import models

from {{cookiecutter.project_slug}}.common.models import AbstractBaseModel
from {{cookiecutter.project_slug}}.products.models.product import Product


class ProductMarketType(AbstractBaseModel):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="market_types"
    )
    market_type = models.ForeignKey(
        "sales_context.MarketType", on_delete=models.PROTECT, related_name="products"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "market_type"], name="unique_product_market_type"
            )
        ]
