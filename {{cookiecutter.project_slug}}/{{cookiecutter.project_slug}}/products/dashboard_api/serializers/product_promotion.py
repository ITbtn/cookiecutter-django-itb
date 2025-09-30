from rest_framework import serializers

from {{cookiecutter.project_slug}}.common.validators import validate_char_field
from {{cookiecutter.project_slug}}.products.api.serializers.promotions import PromotionSerializer
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers.product import BasicProductOutputSerializer
from {{cookiecutter.project_slug}}.products.models import ProductPromotion


class ProductPromotionInputSerializer(serializers.Serializer):
    promotion_code = serializers.CharField(
        max_length=128, validators=[validate_char_field]
    )
    related_product_code = serializers.CharField(
        max_length=128,
        validators=[validate_char_field],
        required=False,
        allow_null=True,
    )


class ProductPromotionUpdateSerializer(serializers.Serializer):
    promotion_code = serializers.CharField(
        max_length=128,
        validators=[validate_char_field],
        required=False,
        allow_null=True,
    )
    related_product_code = serializers.CharField(
        max_length=128,
        validators=[validate_char_field],
        required=False,
        allow_null=True,
        allow_blank=True,
    )


class ProductPromotionOutputSerializer(serializers.ModelSerializer):
    promotion = PromotionSerializer()
    related_product = BasicProductOutputSerializer()

    class Meta:
        model = ProductPromotion
        exclude = ["id", "created_by", "updated_by", "is_available", "export_id"]


