from {{cookiecutter.project_slug}}.common.bases import api_views
from {{cookiecutter.project_slug}}.products.dashboard_api.mixins import ProductAPIMixin
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers import (
    PriceInputSerializer,
    PriceSerializer,
)
from {{cookiecutter.project_slug}}.products.services import PriceService


class ProductPriceListCreateAPIView(
    ProductAPIMixin, api_views.BaseDashboardListCreateAPIView
):
    serializer_class = PriceInputSerializer
    output_serializer_class = PriceSerializer
    service_class = PriceService

    def get_queryset(self):
        product = self.get_product()
        return product.price_set.all().order_by("price_type")

    def perform_create(self, serializer):
        data = serializer.validated_data
        product = self.get_product()
        data["product_id"] = product.id
        data["product_code"] = product.code

        service = self.service_class(
            tenant_code=self.request.user.tenant_code,
            site_profile=self.request.site_profile,
            user=self.request.user,
        )
        service.create_price(user=self.request.user, **data)


class ProductPriceRetrieveUpdateDeleteAPIView(
    ProductAPIMixin, api_views.BaseDashboardRetrieveUpdateDestroyAPIView
):
    serializer_class = PriceInputSerializer
    output_serializer_class = PriceSerializer
    service_class = PriceService

    def get_object(self):
        return self.service_class(
            tenant_code=self.request.tenant_code, site_profile=self.request.site_profile
        ).read_by_code(code_value=self.kwargs["price_code"])

    def perform_update(self, serializer):
        service = self.service_class(
            tenant_code=self.request.user.tenant_code,
            site_profile=self.request.site_profile,
            user=self.request.user,
        )
        data = serializer.validated_data
        product = self.get_product()
        data["product_id"] = product.id
        data["product_code"] = product.code
        service.update_price(user=self.request.user, **data)
