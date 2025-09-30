from django.db import models
from django.utils.translation import gettext_lazy as _

from {{cookiecutter.project_slug}}.products.models.base import ProductBase
from {{cookiecutter.project_slug}}.products.models.product import Product
from {{cookiecutter.project_slug}}.products.models.promotion import Promotion


class ProductPromotion(ProductBase):
    promotion = models.ForeignKey(
        Promotion, on_delete=models.PROTECT, help_text=_("id from PRODUCTS_PROMOTION")
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="product_promotion",
        help_text=_("id from PRODUCTS_PRODUCT"),
    )
    related_product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="related_product_promotion",
        help_text=_("id from PRODUCTS_PRODUCT"),
        blank=True,
        null=True,
    )
