from rest_framework import status
from rest_framework.response import Response

from {{cookiecutter.project_slug}}.common.bases import api_views
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers import (
    VatSerializer,
    VatUpdateSerializer,
)
from {{cookiecutter.project_slug}}.products.services import VatService


class VatListCreateAPIView(api_views.BaseListCreateAPIView):
    service_class = VatService
    serializer_class = VatSerializer


class VatRetrieveUpdateDestroyAPIView(api_views.BaseRetrieveUpdateDestroyAPIView):
    service_class = VatService
    serializer_class = VatUpdateSerializer

    def get_object(self):
        code = self.kwargs.get("code")
        if code is not None:
            return self.service_class(
                tenant_code=self.request.tenant_code,
                site_profile=self.request.site_profile,
            ).read_by_code(code)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
