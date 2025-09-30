from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT

from {{cookiecutter.project_slug}}.common.bases import api_views
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers import PageLayoutsSerializer
from {{cookiecutter.project_slug}}.products.services.page_layout_service import PageLayoutService


class PageLayoutsListCreateAPIView(api_views.BaseDashboardListCreateAPIView):
    service_class = PageLayoutService
    serializer_class = PageLayoutsSerializer


class PageLayoutsRetrieveUpdateDestroyAPIView(
    api_views.BaseDashboardRetrieveUpdateDestroyAPIView
):
    service_class = PageLayoutService
    serializer_class = PageLayoutsSerializer

    def get_object(self):
        return self.service_class(
            tenant_code=self.request.tenant_code, site_profile=self.request.tenant_code
        ).get_page_layout(code=self.kwargs["code"])

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.service_class(
            tenant_code=self.request.tenant_code, site_profile=self.request.tenant_code
        ).delete_page_layout(instance=instance)
        return Response(
            data={"message": "Deleted Successfully"}, status=HTTP_204_NO_CONTENT
        )
