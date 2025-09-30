from django.db import models

from {{cookiecutter.project_slug}}.common.models import AbstractBaseModel
from {{cookiecutter.project_slug}}.products.models.product import Product


class ProductFlowType(AbstractBaseModel):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="flow_types"
    )
    flow_type = models.ForeignKey(
        "sales_context.FlowType", on_delete=models.PROTECT, related_name="products"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "flow_type"], name="unique_product_flow_type"
            )
        ]
