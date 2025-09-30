from {{cookiecutter.project_slug}}.common.bases import api_views
from {{cookiecutter.project_slug}}.products.dashboard_api.mixins import ProductAPIMixin
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers import (
    ProductFlowTypeInputSerializer,
    ProductFlowTypeOutputSerializer,
)
from {{cookiecutter.project_slug}}.products.services.product_sales_context import ProductFlowTypeService


class ProductFlowTypeListCreateAPIView(ProductAPIMixin,
                                       api_views.BaseDashboardListCreateAPIView):
    serializer_class = ProductFlowTypeInputSerializer
    output_serializer_class = ProductFlowTypeOutputSerializer
    service_class = ProductFlowTypeService

    def get_queryset(self):
        product = self.get_product()
        return self.service_class(tenant_code=self.request.tenant_code,
                                  site_profile=self.request.tenant_code).list(**{"product_id": product.id})

    def perform_create(self, serializer):
        data = serializer.validated_data
        data["product_id"] = self.get_product().id
        serializer.instance = self.service_class(tenant_code=self.request.tenant_code,
                                  site_profile=self.request.tenant_code).create(**data)


class ProductFlowTypeRetrieveUpdateDeleteAPIView(ProductAPIMixin, api_views.BaseRetrieveUpdateDestroyAPIView):
    serializer_class = ProductFlowTypeInputSerializer
    output_serializer_class = ProductFlowTypeOutputSerializer
    service_class = ProductFlowTypeService

    def get_object(self):
        product = self.get_product()
        return self.service_class(tenant_code=self.request.tenant_code,
                                  site_profile=self.request.tenant_code).get_object(
            **{"flow_type": self.kwargs["flowtype_code"], "product_id": product.id}
        )
