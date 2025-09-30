from decimal import Decimal

from rest_framework import serializers

from {{cookiecutter.project_slug}}.attributes.models.options import Option
from {{cookiecutter.project_slug}}.common.constants import ZERO
from {{cookiecutter.project_slug}}.common.utils import fix_external_decimal_places
from {{cookiecutter.project_slug}}.common.validators import validate_char_field
from {{cookiecutter.project_slug}}.products.api.serializers.brand_serializer import BrandSerializer
from {{cookiecutter.project_slug}}.products.api.serializers.price import PriceSerializer
from {{cookiecutter.project_slug}}.products.api.serializers.product_group import ProductGroupSerializer
from {{cookiecutter.project_slug}}.products.api.serializers.product_lineup import LineupSerializer
from {{cookiecutter.project_slug}}.products.api.serializers.product_type import (
    ProductTypeOutputSerializer,
    ProductTypeSerializer,
)
from {{cookiecutter.project_slug}}.products.api.serializers.unit import UnitSerializer
from {{cookiecutter.project_slug}}.products.api.serializers.vat import VatSerializer
from {{cookiecutter.project_slug}}.products.models import Product, ProductRelation
from {{cookiecutter.project_slug}}.products.services import PriceService


class ProductInputSerializer(serializers.ModelSerializer):
    alternative_group_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
    )
    alternative_product_code = serializers.CharField(
        max_length=128,
        validators=[validate_char_field],
        required=False,
    )

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ["id", "created_by", "updated_by", "create_at", "updated_at"]


class ProductUpdateInputSerializer(ProductInputSerializer):
    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = [
            "id",
            "code",
            "created_by",
            "updated_by",
            "create_at",
            "updated_at",
        ]


class ProductOutputSerializer(serializers.ModelSerializer):
    product_type = serializers.SerializerMethodField(
        method_name="get_product_type_details",
    )
    product_group = serializers.SerializerMethodField(
        method_name="get_product_group_details",
    )
    alternative_product = serializers.SerializerMethodField(
        method_name="get_alternative_product_details",
    )
    unit = serializers.SerializerMethodField(method_name="get_unit_details")
    brand = serializers.SerializerMethodField(method_name="get_brand_details")
    vat = serializers.SerializerMethodField(method_name="get_vat_details")
    lineup = serializers.SerializerMethodField(method_name="get_lineup_details")

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = [
            "id",
            "code",
            "created_by",
            "updated_by",
            "create_at",
            "updated_at",
        ]

    def get_product_type_details(self, instance):
        return ProductTypeOutputSerializer(instance=instance.product_type).data

    def get_product_group_details(self, instance):
        return ProductGroupSerializer(instance.product_group).data

    def get_alternative_product_details(self, instance):
        if instance.alternative_product:
            return ProductInputSerializer(instance=instance.alternative_product).data
        return None

    def get_unit_details(self, instance):
        return UnitSerializer(instance=instance.unit).data

    def get_brand_details(self, instance):
        if instance.brand:
            return BrandSerializer(instance.brand).data
        return None

    def get_vat_details(self, instance):
        if instance.vat:
            return VatSerializer(instance=instance.vat).data
        return None

    def get_lineup_details(self, instance):
        if instance.lineup:
            return LineupSerializer(instance=instance.lineup).data
        return None


class RelationProductSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="product_to.name")
    code = serializers.CharField(source="product_to.code")
    relation = serializers.CharField(source="get_relation_type_display")
    product_type = serializers.CharField(source="product_to.product_type.name")
    required_product = serializers.SerializerMethodField(
        method_name="get_required_product_data",
    )
    flow_types = serializers.SerializerMethodField(method_name="get_flow_type_list")
    price = serializers.SerializerMethodField()

    class Meta:
        model = ProductRelation
        exclude = ["created_by", "updated_by", "created_at", "updated_at"]

    def get_flow_type_list(self, obj):
        return [flow_type.flow_type for flow_type in obj.product_to.productflowtype_set.all()]

    def get_required_product_data(self, obj):
        data = {}
        if obj.required_product:
            data.update(
                {
                    "id": obj.required_product.id,
                    "product_name": obj.required_product.name,
                    "product_code": obj.required_product.code,
                },
            )
        return data

    def get_price(self, obj):
        _price = ZERO
        price_obj = obj.product_to.get_latest_sales_price()
        if price_obj:
            _price = price_obj.price
        return _price


class ProductListSerializer(serializers.ModelSerializer):
    product_type = ProductTypeSerializer()
    product_group = ProductGroupSerializer()
    # image = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    flow_type = serializers.SerializerMethodField()
    stock = serializers.SerializerMethodField()
    alternative_groups = serializers.SerializerMethodField()
    alternative_product = serializers.SerializerMethodField()
    created_by = serializers.CharField(
        source="created_by.get_username_without_tenant_code",
        read_only=True,
    )
    updated_by = serializers.CharField(
        source="updated_by.get_username_without_tenant_code",
        read_only=True,
    )

    class Meta:
        model = Product
        fields = "__all__"

    # def get_image(self, obj):
    #     if obj.image:
    #         return obj.image.url

    def get_price(self, obj):
        _price = obj.get_latest_sales_price()
        data = PriceSerializer(_price).data
        price = data["price"]
        if price:
            data["price"] = str(
                fix_external_decimal_places(decimal_value=Decimal(price)),
            )
        return data

    def get_flow_type(self, obj):
        flow_types = obj.flow_types.all()
        return [flow_type.get_flow_type().name for flow_type in flow_types]

    def get_stock(self, obj):
        # TODO: will fix later
        return 0

    def get_alternative_groups(self, obj):
        return ProductGroupSerializer(obj.alternative_groups, many=True).data

    def get_alternative_product(self, obj):
        return ProductInputSerializer(instance=obj.alternative_product).data if obj.alternative_product else None


class ProductOptionsSerializer(serializers.ModelSerializer):
    attribute_code = serializers.SerializerMethodField()

    class Meta:
        model = Option
        fields = ["code", "name", "color_code", "attribute_code"]

    def get_attribute_code(self, obj):
        """
        :param obj:
        :return:
        """
        return obj.attribute_code


class ProductDimentionalAttributeSerializer(serializers.Serializer):
    attribute_code = serializers.CharField()
    attribute_name = serializers.CharField()
    attribute_value = serializers.CharField()


class ProductDimentionalAttributeMixin:
    def get_dimensional_attributes(self, obj):
        dimensional_attributes = self.get_attributes(
            obj.product_attribute.filter(
                attribute__code__in=["memory_size", "color"],
            ).select_related("option", "attribute"),
        )
        return ProductDimentionalAttributeSerializer(
            dimensional_attributes,
            many=True,
        ).data

    def get_attributes(self, attribute_qs):
        attribute_list = []
        for product_attr in attribute_qs:
            attribute = {
                "attribute_code": "",
                "attribute_name": "",
                "attribute_value": "",
            }
            attribute["attribute_value"] = product_attr.value
            if product_attr.attribute:
                attribute["attribute_code"] = product_attr.attribute.code
                attribute["attribute_name"] = product_attr.attribute.name
            if product_attr.option:
                attribute["attribute_value"] = product_attr.option.name
            attribute_list.append(attribute)
        return attribute_list


class ProductDetailSerializer(serializers.ModelSerializer):
    product_type = serializers.SerializerMethodField()
    # order_unit = serializers.IntegerField()
    sales_price = serializers.SerializerMethodField()
    sales_price_ex_vat = serializers.SerializerMethodField()
    stock = serializers.SerializerMethodField()
    product_attributes = serializers.SerializerMethodField()
    siblings = serializers.SerializerMethodField()
    dimensional_attributes = serializers.SerializerMethodField()
    image_documents = serializers.SerializerMethodField()
    pdf_documents = serializers.SerializerMethodField()
    related_attributes = serializers.SerializerMethodField()
    product_group = serializers.SerializerMethodField()
    tier_prices = serializers.SerializerMethodField()
    usages_prices = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "code",
            "name",
            "product_type",
            "short_description",
            "long_description",
            "sales_price",
            "sales_price_ex_vat",
            # "order_unit",
            "stock",
            "product_attributes",
            "siblings",
            "dimensional_attributes",
            "image_documents",
            "pdf_documents",
            "related_attributes",
            "product_group",
            "tier_prices",
            "usages_prices",
            "pre_order",
            "release_date",
        ]

    def get_product_type(self, obj):
        return obj.get("product_type", {})

    def get_product_group(self, obj):
        return obj.get("product_group", {})

    def get_stock(self, obj):
        return obj.get("stock", 0)

    def get_product_attributes(self, obj):
        return obj.get("product_attributes", [])

    def get_siblings(self, obj):
        return obj.get("siblings", [])

    def get_image_documents(self, obj):
        return obj.get("image_documents", [])

    def get_pdf_documents(self, obj):
        return obj.get("pdf_documents", [])

    def get_related_attributes(self, obj):
        return obj.get("related_attributes", [])

    def get_dimensional_attributes(self, obj):
        return obj.get("dimensional_attributes", [])

    def get_tier_prices(self, obj):
        return obj.get("tier_prices", [])

    def get_usages_prices(self, obj):
        return obj.get("usages_prices", [])

    def get_sales_price(self, obj):
        return str(obj.get("sales_price", 0))

    def get_sales_price_ex_vat(self, obj):
        return str(obj.get("sales_price_ex_vat", 0))


class ProductDetailAttributeSerializer(serializers.ModelSerializer):
    product_attributes = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "product_attributes",
        ]

    def get_product_attributes(self, instance):
        return instance.product_attributes


class DiscountProductOutputSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    price_ex_vat = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "code",
            "name",
            "price",
            "price_ex_vat",
        ]

    def get_price(self, obj):
        return PriceService().get_price(product_code=obj.code)

    def get_price_ex_vat(self, obj):
        return PriceService().get_price(product_code=obj.code, excl_vat=True)
