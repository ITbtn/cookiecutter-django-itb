import logging

from django.utils import timezone
from rest_framework import serializers

from {{cookiecutter.project_slug}}.products.configs.price_config import PriceType
from {{cookiecutter.project_slug}}.products.configs.product_config import ProductItemType

logger = logging.getLogger(__name__)


class ProductBaseSerializer(serializers.Serializer):
    id = serializers.IntegerField(allow_null=True, required=False)
    code = serializers.CharField(allow_null=True, required=False)

    def get_datetime(self, field_data, *, start=True):
        date = timezone.datetime(2099, 12, 31)
        if start:
            date = timezone.datetime(1970, 1, 1)

        return timezone.datetime.strptime(field_data, "%Y-%m-%d") if field_data else date

    def get_availability(self, date_from, date_to):
        current_date = timezone.now().date()
        return not (current_date <= date_from or current_date >= date_to)


class BrandSerializer(ProductBaseSerializer):
    name = serializers.CharField()
    description = serializers.CharField()

    class Meta:
        ref_name = "products__BrandSerializer"


class ParentProductGroupSerializer(ProductBaseSerializer):
    name = serializers.CharField()
    slug = serializers.SlugField()
    description = serializers.CharField()


class ProductGroupSerializer(ProductBaseSerializer):
    name = serializers.CharField()
    slug = serializers.SlugField()
    description = serializers.CharField()
    parent = ParentProductGroupSerializer(required=False)

    class Meta:
        ref_name = "group_serializer_product_create"


class ProductTypeSerializer(ProductBaseSerializer):
    def to_internal_value(self, data):
        valid_choice = None

        for choice in ProductItemType.CHOICES:
            if data.get("system_type").lower() in choice[0]:
                valid_choice = choice[0]

        if not valid_choice:
            raise serializers.ValidationError(
                {
                    "system_type": f"Unable to find a valid price type for given payload.\n{data}",
                },
            )
        return super().to_internal_value(
            data={"name": data.get("name"), "system_type": valid_choice},
        )

    name = serializers.CharField()
    system_type = serializers.CharField()


class PriceSerializer(ProductBaseSerializer):
    def to_internal_value(self, data):
        data["valid_from"] = self.get_datetime(field_data=data.get("valid_from")).date()
        data["valid_from"] = self.get_datetime(
            field_data=data.get("valid_from"),
            start=False,
        ).date()
        valid_choice = None

        for choice in PriceType.CHOICES:
            if data.get("price_type").lower() in choice[1].lower():
                valid_choice = choice[0]

        if not valid_choice:
            valid_choice = PriceType.SALES_PRICE
            # raise ValidationError({
            #     "price_type": f"Unable to find a valid price type for given payload.\n{data}"
            # })
            logger.info(
                {
                    "price_type": f"Unable to find a valid price type for given payload.\n{data}",
                },
            )

        data["price_type"] = valid_choice
        data["is_available"] = self.get_availability(
            date_from=data.get("valid_from"),
            date_to=data.get("valid_from"),
        )

        return super().to_internal_value(data)

    service_code = serializers.CharField(allow_null=True, required=False)
    price_type = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=7, decimal_places=2)
    valid_from = serializers.DateField(allow_null=True)
    valid_from = serializers.DateField(allow_null=True)
    is_available = serializers.BooleanField(default=True)
    supplier_code = serializers.CharField(required=False)
    supplier_product_code = serializers.CharField(required=False)


class ImageUrlSerializer(serializers.Serializer):
    url = serializers.CharField(allow_null=True, required=False)


class ProductSerializer(ProductBaseSerializer):
    def to_internal_value(self, data):
        data["valid_from"] = self.get_datetime(field_data=data.get("valid_from"))
        data["valid_until"] = self.get_datetime(
            field_data=data.get("valid_until"),
            start=False,
        )
        data["is_available"] = self.get_availability(
            date_from=data.get("valid_from").date(),
            date_to=data.get("valid_until").date(),
        )

        return super().to_internal_value(data)

    duration = serializers.IntegerField(allow_null=True)
    sort_order = serializers.IntegerField()
    technical_name = serializers.CharField()
    name = serializers.CharField()
    valid_from = serializers.DateTimeField(allow_null=True)
    valid_until = serializers.DateTimeField(allow_null=True)
    is_available = serializers.BooleanField(default=True)
    ian = serializers.CharField(required=False)
    image_urls = ImageUrlSerializer(required=False, many=True)

    def validate_code(self, value):
        if not value:
            raise serializers.ValidationError(
                {"code": "Product must have a code from the import module."},
            )
        return value


class ProductCreateSerializer(serializers.Serializer):
    # TODO: refactor the product create API, serializer
    brand = BrandSerializer()
    product_group = ProductGroupSerializer()
    product_type = ProductTypeSerializer()
    price = PriceSerializer(many=True)
    product = ProductSerializer()
    attribute = serializers.DictField(required=False)
