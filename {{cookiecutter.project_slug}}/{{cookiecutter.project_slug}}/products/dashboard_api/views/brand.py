from rest_framework import filters, status
from rest_framework.response import Response

from {{cookiecutter.project_slug}}.common.bases import api_views
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers import BrandSerializer
from {{cookiecutter.project_slug}}.products.services.product_brand import BrandService


class BrandListCreateAPIView(api_views.BaseDashboardListCreateAPIView):
    service_class = BrandService
    serializer_class = BrandSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "code"]

    sort_order = "-created_at"

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
        attribute_instance = service.create_brand(**serializer.validated_data)
        output_serializer = self.serializer_class(attribute_instance)
        return Response(data=output_serializer.data, status=status.HTTP_201_CREATED)


class BrandRetrieveUpdateAPIView(api_views.BaseDashboardRetrieveUpdateDestroyAPIView):
    service_class = BrandService
    serializer_class = BrandSerializer
    read_by = "code"
