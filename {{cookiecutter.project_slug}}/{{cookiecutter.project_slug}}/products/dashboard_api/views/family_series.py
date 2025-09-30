from rest_framework import status
from rest_framework.response import Response

from {{cookiecutter.project_slug}}.common.bases.api_views import (
    BaseDashboardListCreateAPIView,
    BaseDashboardRetrieveUpdateDestroyAPIView,
)

from ...services.family_series import FamilyService, SeriesService
from ..serializers.family_series import (
    DashboardFamilySerializer,
    DashboardSeriesSerializer,
    FamilyCreateSerializer,
    FamilyUpdateSerializer,
    SeriesInputSerializer,
)


class FamilyListCreateAPIView(BaseDashboardListCreateAPIView):
    service_class = FamilyService
    input_serializer_class = FamilyCreateSerializer
    output_serializer_class = DashboardFamilySerializer


class FamilyRetrieveUpdateDestroyAPIView(BaseDashboardRetrieveUpdateDestroyAPIView):
    service_class = FamilyService
    input_serializer_class = FamilyUpdateSerializer
    output_serializer_class = DashboardFamilySerializer
    read_by = "code"

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.service_class(
            tenant_code=request.tenant_code,
            site_profile=request.site_profile,
        ).delete_family(instance=instance)
        return Response(
            data={"message": "Deleted Successfully"}, status=status.HTTP_204_NO_CONTENT
        )


class SeriesListCreateAPIView(BaseDashboardListCreateAPIView):
    service_class = SeriesService
    input_serializer_class = SeriesInputSerializer
    output_serializer_class = DashboardSeriesSerializer

    def post(self, request, *args, **kwargs):
        service = self.service_class(
            tenant_code=request.tenant_code,
            site_profile=request.site_profile,
            user=request.user,
        )
        serializer = self.input_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = service.create_series(**serializer.validated_data)
        serializer = self.output_serializer_class(instance)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)


class SeriesRetrieveUpdateDestroyAPIView(BaseDashboardRetrieveUpdateDestroyAPIView):
    service_class = SeriesService
    input_serializer_class = SeriesInputSerializer
    output_serializer_class = DashboardSeriesSerializer
    read_by = "code"

    def put(self, request, *args, **kwargs):
        service = self.service_class(
            tenant_code=self.request.tenant_code,
            site_profile=self.request.site_profile,
            user=request.user,
        )
        instance = self.get_object()
        serializer = self.input_serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = service.update_series(instance=instance, **serializer.validated_data)
        return Response(data=self.output_serializer_class(instance).data)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.service_class(
            tenant_code=request.tenant_code, site_profile=request.site_profile
        ).delete_series(instance=instance)
        return Response(
            data={"message": "Deleted Successfully"}, status=status.HTTP_204_NO_CONTENT
        )
