from datetime import datetime

from rest_framework import serializers

from {{cookiecutter.project_slug}}.common.serializers.base import LogBaseSerializer
from {{cookiecutter.project_slug}}.common.utils import generate_unique_code
from {{cookiecutter.project_slug}}.prices.models import PriceListContactGroup
from {{cookiecutter.project_slug}}.products.configs.price_config import PriceType
from {{cookiecutter.project_slug}}.products.models import Price


class PriceSerializer(LogBaseSerializer, serializers.ModelSerializer):
    price_type = serializers.CharField(source="get_price_type_display", read_only=True)
    price = serializers.DecimalField(max_digits=15, decimal_places=2)
    price_ex_vat = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=False
    )
    is_active = serializers.SerializerMethodField()

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
            "is_active",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
        ]
        ref_name = "price_serializer_for_generic_product"

    def get_is_active(self, obj):
        today = datetime.today()
        return (
            True
            if obj.valid_from <= today.date() and obj.valid_until >= today.date()
            else False
        )

    def to_representation(self, instance):
        new_data = super().to_representation(instance=instance)
        if instance.price_type == PriceType.PURCHASE_PRICE:
            supplier = instance.get_supplier()
            if supplier:
                new_data["supplier"] = {
                    "contact_name": supplier.contact_name,
                    "company_name": supplier.company_name,
                    "uuid": supplier.uuid,
                }
            else:
                new_data["supplier"] = None
        else:
            new_data["supplier"] = None
        return new_data


class PriceInputSerializer(serializers.ModelSerializer):
    code = serializers.CharField(required=False)

    class Meta:
        model = Price
        fields = [
            "code",
            "price_type",
            "valid_from",
            "valid_until",
            "currency",
            "supplier_uuid",
            "price",
            "price_ex_vat",
        ]
        read_only_fields = ["id", "product"]
        extra_kwargs = {
            "price": {"required": False},
            "price_ex_vat": {"required": False},
        }

    def validate(self, data):
        price = data.get("price")
        price_ex_vat = data.get("price_ex_vat")

        if price is None and price_ex_vat is None:
            raise serializers.ValidationError(
                "price or price_ex_vat at least one is required"
            )
        # code isn't required from FE, so if not provided, generate a unique code
        if data.get("code") is None:
            data["code"] = generate_unique_code()
        return data


class PriceListContactGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceListContactGroup
        fields = ["price_list", "contact_group_code"]
