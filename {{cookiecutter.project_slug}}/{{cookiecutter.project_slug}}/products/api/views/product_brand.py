from django.core.exceptions import ObjectDoesNotExist

from {{cookiecutter.project_slug}}.common.bases import api_views
from {{cookiecutter.project_slug}}.products.api.serializers.brand_serializer import BrandSerializer
from {{cookiecutter.project_slug}}.products.services.product_brand import BrandService
from {{cookiecutter.project_slug}}.rest_utils.exceptions import BadRequestException


class BrandListAPIView(api_views.BaseDashboardListCreateAPIView):
    service_class = BrandService
    serializer_class = BrandSerializer


class BrandRetrieveDeleteUpdateAPIView(
    api_views.BaseDashboardRetrieveUpdateDestroyAPIView
):
    service_class = BrandService
    serializer_class = BrandSerializer

    def get_object(self):
        try:
            return self.service_class(
                tenant_code=self.request.tenant_code,
                site_profile=self.request.site_profile,
            ).read_by_code(
                code_value=self.kwargs["code"],
                tenant_code=self.request.user.tenant_code,
            )
        except ObjectDoesNotExist:
            raise BadRequestException(message="Invalid Brand Code")
