from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from {{cookiecutter.project_slug}}.common.constants import ZERO
from {{cookiecutter.project_slug}}.products.configs.price_config import Currency, PriceType
from {{cookiecutter.project_slug}}.products.models.base import ProductBase
from {{cookiecutter.project_slug}}.products.models.product import Product


class Price(ProductBase):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, help_text=_("FK to product")
    )
    price_type = models.CharField(max_length=50, choices=PriceType.CHOICES)
    valid_from = models.DateField(default=timezone.datetime(1970, 1, 1).date())
    valid_until = models.DateField(default=timezone.datetime(2099, 12, 31).date())
    currency = models.CharField(max_length=5, choices=Currency.CHOICES, default="EUR")
    price = models.DecimalField(max_digits=15, decimal_places=6)
    price_ex_vat = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        blank=True,
        default=ZERO,
        verbose_name=_("Price Ex. VAT"),
        help_text=_("Price excluding VAT"),
    )
    supplier_uuid = models.UUIDField(
        blank=True,
        null=True,
        verbose_name=_("UUID of the supplier"),
        help_text=_("UUID of the supplier contact"),
    )
    supplier_product_code = models.CharField(
        max_length=128,
        blank=True,
        default="",
        verbose_name=_("Supplier product code"),
        help_text=_("Product code that is being used by the supplier"),
    )

    class Meta(ProductBase.Meta):
        indexes = [
            models.Index(fields=["product", "price_type"]),
            models.Index(fields=["tenant_code", "code"]),
        ]

    def screen_price(self):
        price_filter = self._meta.default_manager.filter(
            product=self.product, price_type=self.price_type
        )
        if price_filter.exists():
            if price_filter.filter(
                Q(valid_from__lte=self.valid_from),
                Q(valid_until__gte=self.valid_from)
                | Q(valid_from__lte=self.valid_until),
                Q(valid_until__gte=self.valid_until),
            ).exists():
                raise ValidationError(
                    "Sales price valid date range for this price type already exists"
                )

    def get_supplier(self):
        """
        Return the contact object of the order
        :return: Contact object
        # todo: return a dict
        """
        from {{cookiecutter.project_slug}}.contacts.services import contact_service

        return contact_service.ContactService.get_contact(
            **{"uuid": self.supplier_uuid}
        )

    def get_supplier_company_code(self):
        supplier = self.get_supplier()
        return supplier.company_code if supplier else ""

    supplier_company_code = property(get_supplier_company_code)
