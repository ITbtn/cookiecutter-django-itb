from django.contrib import admin

from {{cookiecutter.project_slug}}.common.admin import BaseReadonlyHistoryAdmin

from .models import (
    VAT,
    Family,
    Lineup,
    Price,
    Product,
    ProductAttribute,
    ProductGroupAttribute,
    ProductIAN,
    ProductPromotion,
    ProductRelation,
    ProductSerial,
    Promotion,
    Series,
)
from .models.brand import Brand
from .models.page_layout import PageLayout
from .models.product_channel import ProductChannel
from .models.product_flow_type import ProductFlowType
from .models.product_group import ProductGroup
from .models.product_market_type import ProductMarketType
from .models.product_type import ProductType
from .models.unit import Unit


class PriceInline(admin.StackedInline):
    model = Price
    readonly_fields = ["created_by", "updated_by", "tenant_code"]
    extra = 0


class ProductRelationInline(admin.StackedInline):
    model = ProductRelation
    fk_name = "product"
    autocomplete_fields = ["product_to", "required_product"]
    readonly_fields = ["created_by", "updated_by", "tenant_code"]
    extra = 0


class ProductAttributeInline(admin.StackedInline):
    model = ProductAttribute
    extra = 0


class ProductAdmin(BaseReadonlyHistoryAdmin):
    inlines = [PriceInline, ProductRelationInline, ProductAttributeInline]

    list_display = [
        "name",
        "code",
        "product_type",
        "short_description",
        "long_description",
    ]

    search_fields = ["name", "product_type__name", "code"]

    readonly_fields = ["created_by", "updated_by"]
    list_filter = ["is_available"]

    autocomplete_fields = [
        "product_group",
        "alternative_groups",
        "alternative_product",
    ]


class PriceAdmin(BaseReadonlyHistoryAdmin):
    list_display = ["price_type", "product", "price", "valid_from", "valid_until"]

    search_fields = ["product__name", "price_type", "price", "valid_until"]

    readonly_fields = ["created_by", "updated_by"]


class ProductIANAdmin(admin.ModelAdmin):
    autocomplete_fields = ["product"]


class ProductGroupAdmin(BaseReadonlyHistoryAdmin):
    list_display = ["code", "name"]
    search_fields = ["code", "name"]
    list_filter = ["is_available"]


class VATAdmin(BaseReadonlyHistoryAdmin):
    search_fields = ["code", "name"]
    list_display = ["tenant_code", "code", "name", "percent_value", "is_default"]


def active_attribute(modeladmin, request, queryset):
    for attribute in queryset:
        attribute.is_available = True
        attribute.save()


active_attribute.short_description = "Active search attribute"


def deactive_attribute(modeladmin, request, queryset):
    for attribute in queryset:
        attribute.is_available = False
        attribute.save()


deactive_attribute.short_description = "Deactive search attribute"


class ProductGroupAttributeAdmin(BaseReadonlyHistoryAdmin):
    raw_id_fields = ["product_group", "attribute"]
    list_display = [
        "product_group",
        "attribute",
        "is_available",
        "is_searchable",
        "is_dimensional",
    ]
    list_filter = ["is_available"]
    actions = [active_attribute, deactive_attribute]


class ProductSerialAdmin(BaseReadonlyHistoryAdmin):
    list_display = ["product", "warehouse_location", "serial_number"]
    search_fields = ["product__code", "serial_number"]


admin.site.register(Product, ProductAdmin)
admin.site.register(Price, PriceAdmin)
admin.site.register(Brand, BaseReadonlyHistoryAdmin)
admin.site.register(ProductType, BaseReadonlyHistoryAdmin)
admin.site.register(ProductGroup, ProductGroupAdmin)
admin.site.register(Unit, BaseReadonlyHistoryAdmin)
admin.site.register(ProductChannel)
admin.site.register(ProductFlowType)
admin.site.register(ProductMarketType)
admin.site.register(Promotion, BaseReadonlyHistoryAdmin)
admin.site.register(ProductPromotion, BaseReadonlyHistoryAdmin)
admin.site.register(Lineup, BaseReadonlyHistoryAdmin)
admin.site.register(ProductAttribute, BaseReadonlyHistoryAdmin)
admin.site.register(VAT, VATAdmin)
admin.site.register(ProductIAN, ProductIANAdmin)
admin.site.register(ProductGroupAttribute, ProductGroupAttributeAdmin)
admin.site.register(PageLayout, BaseReadonlyHistoryAdmin)
admin.site.register(Family, BaseReadonlyHistoryAdmin)
admin.site.register(Series, BaseReadonlyHistoryAdmin)
admin.site.register(ProductSerial, ProductSerialAdmin)
