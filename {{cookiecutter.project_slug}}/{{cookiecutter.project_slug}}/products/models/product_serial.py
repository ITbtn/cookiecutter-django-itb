from django.db import models
from django.utils.translation import gettext_lazy as _

from {{cookiecutter.project_slug}}.common.models import BaseHistoryModel


class ProductSerial(BaseHistoryModel):
    serial_number = models.CharField(
        max_length=128, help_text=_("Unique serial number")
    )
    warehouse_location = models.ForeignKey(
        "logistics.WarehouseLocation",
        related_name="product_serial",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text=_("In which warehouse/location the product can be."),
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="serials",
        verbose_name=_("Product"),
        help_text=_("Product it belongs to"),
    )
    dispatch_line = models.ForeignKey(
        "purchase_orders.DispatchNoticeLine",
        blank=True,
        null=True,
        related_name="product_serials",
        on_delete=models.PROTECT,
        help_text=_("Related dispatch line"),
    )
    receival_line = models.ForeignKey(
        "purchase_orders.ReceivalLine",
        blank=True,
        null=True,
        related_name="product_serials",
        on_delete=models.PROTECT,
        help_text=_("Related receival line"),
    )

    class Meta(BaseHistoryModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_code", "serial_number", "product"],
                name="%(class)s_unique_serial_number",
            )
        ]
        indexes = [
            models.Index(fields=["tenant_code", "serial_number"]),
        ]
