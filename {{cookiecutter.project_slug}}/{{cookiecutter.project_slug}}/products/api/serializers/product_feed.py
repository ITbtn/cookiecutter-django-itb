from django.utils import timezone
from rest_framework import serializers

from {{cookiecutter.project_slug}}.attributes.models.options import Option
from {{cookiecutter.project_slug}}.products.models import (
    Price,
    Product,
    ProductAttribute,
    ProductGroup,
    ProductType,
    Unit,
)

EXCLUDE_FIELDS = ["created_by", "updated_by", "created_at", "updated_at"]


class PriceFeedSerializer(serializers.ModelSerializer):
    price_type = serializers.CharField(source="get_price_type_display", read_only=True)

    class Meta:
        model = Price
        exclude = EXCLUDE_FIELDS + ["product", "is_available"]

    def to_representation(self, instance):
        if self.context.get("is_catalog", None):
            current_datetime = timezone.now()
            if not instance.valid_from <= current_datetime.date() <= instance.valid_from:
                return None
        return super().to_representation(instance)


class ProductFeedOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ["name"]


class ProductFeedAttributeSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    code = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField()
    options = serializers.SerializerMethodField()

    class Meta:
        model = ProductAttribute
        fields = ["name", "code", "value", "options"]

    def get_name(self, instance):
        return instance.attribute.name

    def get_code(self, instance):
        return instance.attribute.code

    def get_value(self, instance):
        return getattr(instance, "value", None)

    def get_options(self, instance):
        options = instance.available_options.all()
        if options:
            return ProductFeedOptionSerializer(options, many=True, read_only=True).data
        return []


class ProductGroupChildFeedSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductGroup
        exclude = EXCLUDE_FIELDS


class ProductGroupFeedSerializer(ProductGroupChildFeedSerializer):
    sub_groups = ProductGroupChildFeedSerializer(
        source="productgroup_set", many=True, read_only=True
    )


class UnitFeedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        exclude = EXCLUDE_FIELDS


class ProductTypeFeedSerializer(serializers.ModelSerializer):
    system_type = serializers.CharField(
        source="get_system_type_display", read_only=True
    )

    class Meta:
        model = ProductType
        exclude = EXCLUDE_FIELDS


class ProductFeedBaseSerializer(serializers.ModelSerializer):
    price = PriceFeedSerializer(source="price_set", many=True, read_only=True)
    attributes = serializers.SerializerMethodField()
    product_type = ProductTypeFeedSerializer(read_only=True)
    product_group = ProductGroupFeedSerializer(read_only=True)
    unit = UnitFeedSerializer(read_only=True)
    alternative_groups = ProductGroupFeedSerializer(
        source="secondary_products", read_only=True, many=True
    )
    campaign_code = serializers.CharField(read_only=True)

    class Meta:
        model = Product
        exclude = EXCLUDE_FIELDS

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if self.context.get("is_catalog", None):
            representation["price"] = [
                price for price in representation.get("price") if price is not None
            ]
        return representation

    def get_attributes(self, instance):
        product_attributes = instance.product_attribute.all()
        if product_attributes:
            return ProductFeedAttributeSerializer(
                product_attributes, many=True, read_only=True
            ).data
        return []


class ProductFeedSerializer(ProductFeedBaseSerializer):
    alternative_product = ProductFeedBaseSerializer(
        source="product_alternatives", many=True, read_only=True
    )
