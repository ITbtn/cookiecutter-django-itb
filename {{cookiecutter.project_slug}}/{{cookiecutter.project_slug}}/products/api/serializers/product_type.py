from rest_framework import serializers

from ...models import ProductType


class ProductTypeInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductType
        exclude = ("id",)


class ProductTypeOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductType
        fields = "__all__"


class ProductTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductType
        fields = ["code", "name", "system_type"]
        ref_name = "type_serializer_for_generic_product"
