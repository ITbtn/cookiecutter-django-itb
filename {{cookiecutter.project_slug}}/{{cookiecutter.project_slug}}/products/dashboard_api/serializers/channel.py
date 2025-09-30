from rest_framework import serializers

from {{cookiecutter.project_slug}}.products.models import ProductChannel
from {{cookiecutter.project_slug}}.products.services.product_sales_context import ProductChannelService


class ProductChannelInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductChannel
        fields = ["channel"]


class ProductChannelOutputSerializer(serializers.ModelSerializer):
    channel = serializers.SerializerMethodField(method_name="get_channel_details")

    class Meta:
        model = ProductChannel
        fields = ["channel"]

    def get_channel_details(self, instance):
        data = {}
        request = self.context.get("request")
        channel = ProductChannelService(
            tenant_code=request.tenant_code, site_profile=request.site_profile
        ).channel_service.read_by_code(code_value=instance.channel)
        if channel:
            data.update(
                {
                    "code": channel.code,
                    "name": channel.name,
                    "is_available": channel.is_available,
                }
            )
        return data


