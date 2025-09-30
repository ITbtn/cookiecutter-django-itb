from rest_framework import serializers

from {{cookiecutter.project_slug}}.products.models import ProductMarketType
from {{cookiecutter.project_slug}}.products.services.product_sales_context import ProductMarketTypeService


class ProductMarketTypeInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMarketType
        fields = ["market_type"]


class ProductMarketTypeOutputSerializer(serializers.ModelSerializer):
    market_type = serializers.SerializerMethodField(
        method_name="get_market_type_details"
    )

    class Meta:
        model = ProductMarketType
        fields = ["market_type"]

    def get_market_type_details(self, instance):
        data = {}
        request = self.context.get("request")
        market_type = ProductMarketTypeService(
            tenant_code=request.tenant_code, site_profile=request.site_profile
        ).market_type_service.read_by_code(code_value=instance.market_type)
        if market_type:
            data.update(
                {
                    "code": market_type.code,
                    "name": market_type.name,
                    "is_available": market_type.is_available,
                }
            )
        return data
