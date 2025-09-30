from {{cookiecutter.project_slug}}.common.bases import api_views
from {{cookiecutter.project_slug}}.products.api.serializers.unit import UnitSerializer
from {{cookiecutter.project_slug}}.products.services.unit import UnitService


class UnitListCreateAPIView(api_views.BaseDashboardListCreateAPIView):
    service_class = UnitService
    serializer_class = UnitSerializer
