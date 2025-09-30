from rest_framework import serializers

from {{cookiecutter.project_slug}}.common.validators import validate_char_field
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers.product import (
    BasicProductOutputSerializer,
)
from {{cookiecutter.project_slug}}.products.models import ProductRelation
from {{cookiecutter.project_slug}}.products.services import ProductRelationService, ProductService
from {{cookiecutter.project_slug}}.rest_utils.exceptions import BadRequestException


class RelatedProductInputSerializer(serializers.ModelSerializer):
    product = serializers.CharField(max_length=128, validators=[validate_char_field])
    product_to = serializers.CharField(max_length=128, validators=[validate_char_field])
    required_product = serializers.CharField(
        max_length=128,
        validators=[validate_char_field],
        allow_null=True,
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = ProductRelation
        exclude = ["id", "code"]


class RelatedProductUpdateSerializer(serializers.ModelSerializer):
    relation_type = serializers.CharField(max_length=128, required=False)

    class Meta:
        model = ProductRelation
        exclude = ["id", "code", "product"]

    def to_internal_value(self, data):
        request = self.context.get("request")
        if data.get("product_to"):
            product_obj = ProductService(
                tenant_code=request.tenant_code, site_profile=request.site_profile
            ).get_product(code=data.pop("product_to"))
            if product_obj:
                data["product_to"] = product_obj.pk
            else:
                raise BadRequestException("Invalid related product code.")

        if data.get("required_product"):
            product_obj = ProductService(
                tenant_code=request.tenant_code, site_profile=request.site_profile
            ).get_product(code=data.pop("required_product"))
            if product_obj:
                data["required_product"] = product_obj.pk
            else:
                raise BadRequestException("Invalid required product code.")
        return super().to_internal_value(data)


class RelatedProductOutputSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="product_to.name")
    product_to = serializers.SerializerMethodField()
    product_type = serializers.CharField(source="product_to.product_type.name")
    required_product = serializers.SerializerMethodField()
    flow_types = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    class Meta:
        model = ProductRelation
        exclude = ["id", "product"]

    @staticmethod
    def get_flow_types(obj):
        return [flow_type.flow_type for flow_type in obj.product_to.flow_types.all()]

    @staticmethod
    def get_product_to(obj):
        if obj.product_to:
            return BasicProductOutputSerializer(instance=obj.product_to).data

    @staticmethod
    def get_required_product(obj):
        if obj.required_product:
            return BasicProductOutputSerializer(instance=obj.required_product).data

    def get_price(self, obj):
        if obj.product_to:
            return ProductRelationService(
                tenant_code=self.context["request"].tenant_code,
                site_profile=self.context["request"].site_profile,
            ).get_product_price(obj.product_to.code)

    @staticmethod
    def get_created_by(obj):
        if obj.created_by:
            return obj.created_by.username

    @staticmethod
    def get_updated_by(obj):
        if obj.updated_by:
            return obj.updated_by.username


class RelatedProductImportInputSerializer(serializers.Serializer):
    import_file = serializers.FileField()
