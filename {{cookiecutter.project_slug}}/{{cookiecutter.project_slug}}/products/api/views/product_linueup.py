from django.core.exceptions import ObjectDoesNotExist

from {{cookiecutter.project_slug}}.common.bases import api_views
from {{cookiecutter.project_slug}}.products.api.serializers.product_lineup import LineupSerializer
from {{cookiecutter.project_slug}}.products.services.product_lineup import LineupService
from {{cookiecutter.project_slug}}.rest_utils.exceptions import BadRequestException


class ProductLineupListCreateAPIView(api_views.BaseDashboardListCreateAPIView):
    service_class = LineupService
    serializer_class = LineupSerializer


class ProductLineupRetrieveUpdateDeleteAPIView(
    api_views.BaseDashboardRetrieveUpdateDestroyAPIView
):
    service_class = LineupService
    serializer_class = LineupSerializer

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
            return BadRequestException(message="Invalid Lineup CODE")
