from {{cookiecutter.project_slug}}.common.bases import api_views
from {{cookiecutter.project_slug}}.products.api.serializers.attribute import (
    ProductAttributeOutputSerializer,
    ProductAttributeSerializer,
)
from {{cookiecutter.project_slug}}.products.api.views.product import ProductAPIMixin
from {{cookiecutter.project_slug}}.products.services.product_attribute_service import (
    ProductAttributeService,
)


class ProductAttributeListCreateAPIView(
    ProductAPIMixin, api_views.BaseDashboardCreateAPIView
):
    service_class = ProductAttributeService
    serializer_class = ProductAttributeSerializer
    output_serializer_class = ProductAttributeOutputSerializer

    def get_queryset(self):
        product = self.get_product()
        return product.product_attribute.filter(
            tenant_code=self.request.user.tenant_code
        )

    def perform_create(self, serializer):
        data = serializer.validated_data
        data["product_id"] = self.get_product().id
        data["tenant_code"] = self.request.user.tenant_code
        serializer.instance = self.service_class().create(**data)


class ProductAttributeRetrieveUpdateDeleteAPIView(
    ProductAPIMixin, api_views.BaseDashboardRetrieveUpdateDestroyAPIView
):
    service_class = ProductAttributeService
    serializer_class = ProductAttributeSerializer
    output_serializer_class = ProductAttributeOutputSerializer

    def get_object(self):
        # product = self.get_product()
        return self.service_class().read_by_pk(pk_value=self.kwargs["attribute_id"])
