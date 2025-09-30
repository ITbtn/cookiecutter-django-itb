from rest_framework import serializers

from {{cookiecutter.project_slug}}.products.models import Brand


class BrandSerializer(serializers.ModelSerializer):
    code = serializers.CharField(required=False)

    class Meta:
        model = Brand
        fields = ["code", "name", "description", "is_available", "sort_order"]
        ref_name = "dashboard_brand_serializer"
