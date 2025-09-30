from {{cookiecutter.project_slug}}.common.bases import api_views
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers import UnitSerializer
from {{cookiecutter.project_slug}}.products.services.unit import UnitService


class UnitListCreateAPIView(api_views.BaseDashboardListCreateAPIView):
    service_class = UnitService
    serializer_class = UnitSerializer

    sort_order = "-created_at"


class UnitRetrieveUpdateDestroyAPIView(
    api_views.BaseDashboardRetrieveUpdateDestroyAPIView
):
    service_class = UnitService
    serializer_class = UnitSerializer
    read_by = "code"
