from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import ProductBase


class AvailableCreditProduct(ProductBase):
    subscription = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="available_credit_products",
        verbose_name=_("Subscription"),
        help_text=_("Subscription")
    )
    credit_products = models.ManyToManyField(
        "products.Product",
        related_name="+",
        help_text=_('Credit products'),
        verbose_name=_('Credit products'),
    )
    sales_price_minimum = models.DecimalField(max_digits=12, decimal_places=6)
    sales_price_maximum = models.DecimalField(max_digits=12, decimal_places=6)
    deviating_range = models.BooleanField(default=False)
    flow_type = models.ForeignKey(
        "sales_context.FlowType",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("Flow Type"),
        help_text=_("Flow type")
    )

    class Meta(ProductBase.Meta):
        unique_together = ('subscription', 'sales_price_minimum', 'deviating_range', 'flow_type')
