from rest_framework import serializers

from {{cookiecutter.project_slug}}.products.models import ProductFlowType
from {{cookiecutter.project_slug}}.products.services.product_sales_context import ProductFlowTypeService


class ProductFlowTypeInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductFlowType
        fields = ["flow_type"]


class ProductFlowTypeOutputSerializer(serializers.ModelSerializer):
    flow_type = serializers.SerializerMethodField(method_name="get_flow_type_details")

    class Meta:
        model = ProductFlowType
        fields = ["flow_type"]

    def get_flow_type_details(self, instance):
        data = {}
        request = self.context.get("request")
        flow_type = ProductFlowTypeService(
            tenant_code=request.tenant_code, site_profile=request.site_profile
        ).flow_type_service.read_by_code(code_value=instance.flow_type)
        if flow_type:
            data.update(
                {
                    "code": flow_type.code,
                    "name": flow_type.name,
                    "is_available": flow_type.is_available,
                }
            )
        return data


