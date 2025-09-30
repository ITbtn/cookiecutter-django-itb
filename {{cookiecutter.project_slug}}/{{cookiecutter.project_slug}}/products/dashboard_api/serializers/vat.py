from rest_framework import serializers

from {{cookiecutter.project_slug}}.products.models import VAT


class VatSerializer(serializers.ModelSerializer):
    class Meta:
        model = VAT
        fields = [
            "code",
            "name",
            "is_available",
            "percent_value",
            "is_default",
            "export_id",
        ]

        ref_name = "dash_vat_seriealizer"


class VatUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VAT
        read_only_fields = ["code"]
        fields = [
            "code",
            "name",
            "is_available",
            "percent_value",
            "is_default",
            "export_id",
        ]
