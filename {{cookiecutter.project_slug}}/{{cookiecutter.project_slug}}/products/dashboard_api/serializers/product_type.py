from rest_framework import serializers

from {{cookiecutter.project_slug}}.products.models import ProductType


class DashProductTypeInputSerializer(serializers.ModelSerializer):
    code = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = ProductType
        exclude = ["id"]


class DashProductTypeUpdateSerializer(serializers.ModelSerializer):
    code = serializers.CharField(read_only=True)

    class Meta:
        model = ProductType
        exclude = ["id"]


class DashProductTypeOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductType
        fields = [
            "name",
            "code",
            "system_type",
            "system",
            "description",
            "can_update_purchase_price",
        ]


class BasicProductTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductType
        fields = ["code", "name", "system_type"]
