from {{cookiecutter.project_slug}}.common.bases import api_views
from {{cookiecutter.project_slug}}.products.dashboard_api.mixins import ProductAPIMixin
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers import (
    ProductChannelInputSerializer,
    ProductChannelOutputSerializer,
)
from {{cookiecutter.project_slug}}.products.services.product_sales_context import ProductChannelService


class ProductChannelListCreateAPIView(ProductAPIMixin, api_views.BaseDashboardListCreateAPIView):
    serializer_class = ProductChannelInputSerializer
    output_serializer_class = ProductChannelOutputSerializer
    service_class = ProductChannelService

    def get_queryset(self):
        product = self.get_product()
        return self.service_class(tenant_code=self.request.tenant_code,
                                  site_profile=self.request.tenant_code
                                  ).list(**{"product_id": product.id})

    def perform_create(self, serializer):
        data = serializer.validated_data
        data["product_id"] = self.get_product().id
        serializer.instance = self.service_class(tenant_code=self.request.tenant_code,
                                                 site_profile=self.request.tenant_code
                                                 ).create(**data)


class ProductChannelRetrieveUpdateDeleteAPIView(ProductAPIMixin,
                                                api_views.BaseRetrieveUpdateDestroyAPIView):
    serializer_class = ProductChannelInputSerializer
    output_serializer_class = ProductChannelOutputSerializer
    service_class = ProductChannelService

    def get_object(self):
        product = self.get_product()
        return self.service_class(tenant_code=self.request.tenant_code,
                                  site_profile=self.request.tenant_code).get_object(
            **{"channel": self.kwargs["channel_code"], "product_id": product.id}
        )
