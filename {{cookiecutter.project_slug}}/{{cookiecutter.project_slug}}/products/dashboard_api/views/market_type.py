from {{cookiecutter.project_slug}}.common.bases import api_views
from {{cookiecutter.project_slug}}.products.dashboard_api.mixins import ProductAPIMixin
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers import (
    ProductMarketTypeInputSerializer,
    ProductMarketTypeOutputSerializer,
)
from {{cookiecutter.project_slug}}.products.services.product_sales_context import ProductMarketTypeService


class ProductMarketTypeListCreateAPIView(ProductAPIMixin, api_views.BaseDashboardListCreateAPIView):
    serializer_class = ProductMarketTypeInputSerializer
    output_serializer_class = ProductMarketTypeOutputSerializer
    service_class = ProductMarketTypeService

    def get_queryset(self):
        product = self.get_product()
        return self.service_class(tenant_code=self.request.tenant_code,
                                  site_profile=self.request.tenant_code).list(**{"product_id": product.id})

    def perform_create(self, serializer):
        data = serializer.validated_data
        data["product_id"] = self.get_product().id
        serializer.instance = self.service_class(tenant_code=self.request.tenant_code,
                                  site_profile=self.request.tenant_code).create(**data)


class ProductMarketTypeRetrieveUpdateDeleteAPIView(ProductAPIMixin, api_views.BaseDashboardRetrieveUpdateDestroyAPIView):
    serializer_class = ProductMarketTypeInputSerializer
    output_serializer_class = ProductMarketTypeOutputSerializer
    service_class = ProductMarketTypeService

    def get_object(self):
        product = self.get_product()
        return self.service_class(tenant_code=self.request.tenant_code,
                                  site_profile=self.request.tenant_code).get_object(
            **{"market_type": self.kwargs["markettype_code"], "product_id": product.id}
        )

