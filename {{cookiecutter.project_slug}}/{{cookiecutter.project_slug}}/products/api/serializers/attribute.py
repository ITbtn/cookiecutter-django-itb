from rest_framework import serializers

from {{cookiecutter.project_slug}}.products.models import ProductAttribute


class ProductAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttribute
        exclude = ["created_by", "updated_by", "created_at", "updated_at"]
        read_only_fields = ["id", "attribute", "product"]


class ProductAttributeOutputSerializer(serializers.ModelSerializer):
    group = serializers.CharField(source="attribute.attribute_group.name")
    name = serializers.CharField(source="attribute.name")
    code = serializers.CharField(source="attribute.code")
    information = serializers.ReadOnlyField(source="value")

    class Meta:
        model = ProductAttribute
        exclude = ["created_by", "updated_by", "created_at", "updated_at"]
        read_only_fields = ["id"]
