from rest_framework import serializers

from {{cookiecutter.project_slug}}.products.models import Price


class PriceSerializer(serializers.ModelSerializer):
    price_type = serializers.CharField(source="get_price_type_display", read_only=True)
    price = serializers.DecimalField(max_digits=15, decimal_places=2)
    price_ex_vat = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
    )

    class Meta:
        model = Price
        fields = [
            "id",
            "code",
            "price_type",
            "valid_from",
            "valid_until",
            "currency",
            "price",
            "price_ex_vat",
        ]
        ref_name = "price_serializer_for_generic_product"
