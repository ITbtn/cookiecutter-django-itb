from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ..configs.price_config import PriceType
from ..configs.product_config import ProductItemType
from .base import ProductBase
from .brand import Brand
from .product_group import ProductGroup
from .product_lineup import Lineup
from .product_type import ProductType
from .unit import Unit
from .vat import VAT


class Product(ProductBase):
    product_type = models.ForeignKey(
        ProductType,
        on_delete=models.PROTECT,
        help_text=_("id from PRODUCTS_PRODUCTTYPE OR choice field"),
    )
    name = models.CharField(max_length=256, help_text=_("Name of product."))
    short_description = models.TextField(
        help_text=_("Short summary, can be used in search results."),
        blank=True,
        default="",
    )
    long_description = models.TextField(
        help_text=_("Long Description"), blank=True, default=""
    )
    keywords = models.TextField(
        help_text=_(
            "Keywords for products, will be used in search and as meta tag on pages."
        ),
        blank=True,
        default="",
    )
    specification = models.TextField(
        help_text=_(
            "Specification of product. "
            " Can be different from the features of the product."
        ),
        blank=True,
        default="",
    )
    unit = models.ForeignKey(
        Unit,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text=_("Product unit like 1 piece, 1 pallet"),
    )
    slug = models.SlugField(
        max_length=256, help_text=_("Slug for the URL."), blank=True, default=""
    )
    alternative_product = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="product_alternatives",
        help_text=_("id from PRODUCTS_PRODUCT. To select alternative product."),
    )
    brand = models.ForeignKey(
        Brand,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_("id from PRODUCTS_BAND"),
    )
    product_group = models.ForeignKey(
        ProductGroup,
        on_delete=models.PROTECT,
        help_text=_("PRODUCTS_PRODUCTGROUP"),
        related_name="primary_products",
    )
    alternative_groups = models.ManyToManyField(
        "products.ProductGroup",
        related_name="secondary_products",
        verbose_name=_("Alternative groups"),
        help_text=_("Alternative product groups"),
        blank=True,
    )
    series = models.ForeignKey(
        "products.Series",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="products",
    )
    attributes = models.ManyToManyField(
        "attributes.Attribute",
        through="ProductAttribute",
        related_name="products",
        blank=True,
    )
    release_date = models.DateField(
        blank=True,
        null=True,
        help_text=_(
            "Release date. Product release on date, can be used "
            "for taking pre-orders."
        ),
    )
    weight = models.DecimalField(
        max_digits=13,
        decimal_places=3,
        blank=True,
        null=True,
        help_text=_(
            "Default weight of product. "
            "On variant level weight can be entered per product."
        ),
    )
    last_import_update = models.DateTimeField(
        blank=True, null=True, help_text=_("Last import date.")
    )
    duration = models.IntegerField(null=True, blank=True)
    sort_order = models.IntegerField(null=True, blank=True)
    technical_name = models.CharField(max_length=255, blank=True)
    ian = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name=_("IAN number"),
        help_text=_("Enter IAN (former EAN) number"),
    )
    valid_from = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Valid from"),
        help_text=_("Enter the datetime from which the product is valid"),
    )
    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Valid until"),
        help_text=_("Enter the datetime on which the product's validity expires"),
    )
    pre_order = models.BooleanField(
        default=False,
        verbose_name=_("Product is a pre-order product"),
        help_text=_("Can be pre ordered"),
    )
    lineup = models.ForeignKey(
        Lineup,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        verbose_name=_("Lineup"),
        help_text=_("Lineup to which this product belongs"),
    )
    vat = models.ForeignKey(
        VAT,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        verbose_name=_("VAT"),
    )
    is_serial_keeping = models.BooleanField(
        default=False, help_text=_("Does it has a serial number"), null=True
    )
    default_supplier = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="default_supplier",
        help_text="Default Supplier contact",
    )
    requires_quote = models.BooleanField(
        default=False,
        verbose_name=_("Requires quote"),
        help_text=_("Is a quote required"),
        blank=True,
    )
    search_keywords = models.TextField(
        blank=True,
        default="",
        help_text=_("Search on products will be done on this field."),
    )

    class Meta(ProductBase.Meta):
        indexes = [
            models.Index(fields=["sort_order", "name"]),
            models.Index(fields=["tenant_code", "code"]),
            models.Index(fields=["product_type", "sort_order"]),
        ]

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        # if not getattr(self, "unit", None):
        #     unit = Unit.objects.get_or_create(name="Piece")
        #     self.unit = unit[0]
        super().save(force_insert, force_update, using, update_fields)
        self.set_ian(self.ian)

    def set_ian(self, ian):
        """
        set new IAN
        :param ian:
        :return:
        """
        if ian and not self.ians.filter(ian=ian).exists():
            self.ians.create(ian=ian)

    def __str__(self):
        # Need to specify format
        return self.name

    def get_latest_sales_price(self):
        now = timezone.now()
        price = (
            self.price_set.filter(
                product_id=self.id,
                price_type=PriceType.SALES_PRICE,
                valid_from__lte=now,
                valid_until__gte=now,
            )
            .order_by("created_at")
            .last()
        )
        return price

    @property
    def non_stock_product(self):
        non_stock_product_types = [ProductItemType.SERVICE]
        if self.product_type.system_type in non_stock_product_types:
            return True
        return False
