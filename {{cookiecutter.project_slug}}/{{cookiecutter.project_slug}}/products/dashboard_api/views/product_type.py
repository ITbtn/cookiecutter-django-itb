from rest_framework import status
from rest_framework.response import Response

from {{cookiecutter.project_slug}}.common.bases.api_views import (
    BaseDashboardListCreateAPIView,
    BaseDashboardRetrieveUpdateAPIView,
)

from ...services import ProductTypeService
from ..serializers.product_type import (
    DashProductTypeInputSerializer,
    DashProductTypeOutputSerializer,
    DashProductTypeUpdateSerializer,
)


class ProductTypeListCreateAPIView(BaseDashboardListCreateAPIView):
    """
    List create API view for product type
    """

    service_class = ProductTypeService
    serializer_class = DashProductTypeInputSerializer
    output_serializer_class = DashProductTypeOutputSerializer

    def create(self, request, *args, **kwargs):
        service = self.service_class(
            tenant_code=self.request.tenant_code,
            site_profile=self.request.site_profile,
            user=request.user,
        )
        serializer = self.serializer_class(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        attribute_instance = service.create_product_type(**serializer.validated_data)
        output_serializer = self.output_serializer_class(attribute_instance)
        return Response(data=output_serializer.data, status=status.HTTP_201_CREATED)


class ProductTypeRetrieveUpdateDestroyAPIView(BaseDashboardRetrieveUpdateAPIView):
    """
    Retrieve, update and destroy API view for product type
    """

    service_class = ProductTypeService
    serializer_class = DashProductTypeUpdateSerializer
    output_serializer_class = DashProductTypeOutputSerializer
