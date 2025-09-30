from {{cookiecutter.project_slug}}.common.bases.api_views import (
    BaseListAPIView,
    BaseListCreateAPIView,
    BaseRetrieveUpdateDestroyAPIView,
)
from {{cookiecutter.project_slug}}.prices.dashboard_api.serializers import ProductGroupSerializer

from ...services import ProductTypeService
from ..serializers import ProductTypeInputSerializer, ProductTypeOutputSerializer


class ProductTypeListCreateAPIView(BaseListCreateAPIView):
    """
    List create API view for product type
    """

    service_class = ProductTypeService
    serializer_class = ProductTypeInputSerializer
    output_serializer_class = ProductTypeOutputSerializer


class ProductTypeRetrieveUpdateDestroyAPIView(BaseRetrieveUpdateDestroyAPIView):
    """
    Retrieve, update and destroy API view for product type
    """

    service_class = ProductTypeService
    serializer_class = ProductTypeInputSerializer
    output_serializer_class = ProductTypeOutputSerializer


class ProductGroupsListType(BaseListAPIView):
    service_class = ProductTypeService
    output_serializer_class = ProductGroupSerializer

    def get_queryset(self):
        service = self.service_class(
            tenant_code=self.request.tenant_code, site_profile=self.request.site_profile
        )
        return service.list_list_all_groups_for_type(type_code=self.kwargs["code"])
