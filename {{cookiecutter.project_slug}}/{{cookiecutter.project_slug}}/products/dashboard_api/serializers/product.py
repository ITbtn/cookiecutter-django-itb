from decimal import Decimal

from rest_framework import serializers

from {{cookiecutter.project_slug}}.common.serializers.base import LogBaseSerializer
from {{cookiecutter.project_slug}}.common.serializers.mixins import ExcludeFieldsMixin
from {{cookiecutter.project_slug}}.common.utils import fix_external_decimal_places
from {{cookiecutter.project_slug}}.common.validators import validate_char_field
from {{cookiecutter.project_slug}}.contacts.dashboard_api.serializers import (
    DashboardContactBasicOutputSerializer,
)

from ...models import Product
from .brand import BrandSerializer
from .family_series import DashboardSeriesLiteSerializer
from .price import PriceSerializer
from .product_group import BasicProductGroupSerializer
from .product_lineup import DashboardLineupSerializer
from .product_type import BasicProductTypeSerializer
from .unit import UnitSerializer
from .vat import VatSerializer


class BasicProductOutputSerializer(ExcludeFieldsMixin, serializers.ModelSerializer):
    product_type = serializers.CharField(required=False, read_only=True)

    class Meta:
        model = Product
        fields = [
            "code",
            "name",
            "product_type",
            "is_serial_keeping",
        ]


class DashboardProductCreateSerializer(serializers.ModelSerializer, LogBaseSerializer):
    code = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    product_type = serializers.CharField()
    slug = serializers.CharField(required=False, allow_blank=True)
    unit = serializers.CharField(required=False, allow_blank=True)
    brand = serializers.CharField(required=False, allow_blank=True)
    product_group = serializers.CharField(required=False, allow_blank=True)
    series = serializers.CharField(required=False, allow_blank=True)
    vat = serializers.CharField(required=False, allow_blank=True)
    default_supplier = serializers.UUIDField(required=False, allow_null=True)
    alternative_group = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    alternative_product = serializers.CharField(
        max_length=128,
        validators=[validate_char_field],
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = [
            "id",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
        ]


class DashboardProductUpdateSerializer(DashboardProductCreateSerializer):
    code = serializers.CharField(read_only=True)
    change_reason = serializers.CharField(required=False)

    class Meta(DashboardProductCreateSerializer.Meta):
        read_only_fields = [
            "id",
            "created_by",
            "updated_by",
            "create_at",
            "updated_at",
        ]


class DashboardProductOutputSerializer(
    ExcludeFieldsMixin, serializers.ModelSerializer, LogBaseSerializer
):
    product_type = BasicProductTypeSerializer()
    product_group = BasicProductGroupSerializer()
    brand = BrandSerializer()
    series = DashboardSeriesLiteSerializer()
    unit = UnitSerializer()
    vat = VatSerializer()
    lineup = DashboardLineupSerializer()
    price = serializers.SerializerMethodField()
    alternative_groups = BasicProductGroupSerializer(many=True)
    alternative_product = BasicProductOutputSerializer(many=True)
    default_supplier = DashboardContactBasicOutputSerializer()

    class Meta:
        model = Product
        fields = [
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "code",
            "name",
            "is_available",
            "is_serial_keeping",
            "short_description",
            "long_description",
            "keywords",
            "specification",
            "weight",
            "sort_order",
            "ian",
            "valid_from",
            "valid_until",
            "search_keywords",
            "product_type",
            "product_group",
            "brand",
            "series",
            "unit",
            "vat",
            "lineup",
            "price",
            "alternative_groups",
            "alternative_product",
            "default_supplier",
        ]

    def get_price(self, obj):
        _price = obj.get_latest_sales_price()
        data = PriceSerializer(_price).data
        price = data["price"]
        if price:
            data["price"] = str(
                fix_external_decimal_places(decimal_value=Decimal(price))
            )
        return data


class DashboardProductListSerializer(serializers.ModelSerializer, LogBaseSerializer):
    product_type = BasicProductTypeSerializer()
    product_group = BasicProductGroupSerializer()
    brand = BrandSerializer()
    series = DashboardSeriesLiteSerializer()
    # price = serializers.SerializerMethodField()
    # flow_type = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "created_at",
            "created_by",
            "code",
            "name",
            "is_available",
            "is_serial_keeping",
            "product_type",
            "product_group",
            "brand",
            "series",
            # "price",
            # "flow_type",
        ]

    def get_product_type(self, instance):
        return BasicProductTypeSerializer(instance.product_type).data

    def get_product_group(self, instance):
        return BasicProductGroupSerializer(instance.product_group).data


class DashboardProductActivePriceListItemOutputSerializer(serializers.Serializer):
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    price_list = serializers.ReadOnlyField(source="price_list_period.price_list.name")
    valid_from = serializers.ReadOnlyField(source="price_list_period.start_datetime")
    valid_from = serializers.ReadOnlyField(source="price_list_period.end_datetime")
    price = serializers.DecimalField(max_digits=15, decimal_places=2)
    price_ex_vat = serializers.DecimalField(max_digits=15, decimal_places=2)

    def get_created_by(self, obj):
        return obj.created_by.username if obj.created_by else ""

    def get_updated_by(self, obj):
        return obj.updated_by.username if obj.updated_by else ""
