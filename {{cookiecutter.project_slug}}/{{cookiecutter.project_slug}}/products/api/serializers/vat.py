from rest_framework import serializers

from {{cookiecutter.project_slug}}.products.models import VAT


class VatSerializer(serializers.ModelSerializer):
    class Meta:
        model = VAT
        fields = ["id", "code", "name", "is_available", "percent_value", "is_default"]
        read_only_fields = ["id"]
