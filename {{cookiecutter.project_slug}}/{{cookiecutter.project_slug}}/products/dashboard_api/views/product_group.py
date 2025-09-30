from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.response import Response

from {{cookiecutter.project_slug}}.common.bases import api_views

from ...exceptions import ProductGroupNotFoundException
from ...services.product_group import ProductGroupService
from ..serializers.product_group import (
    ProductGroupInputSerializer,
    ProductGroupParentSerializer,
)


class ProductGroupListCreateAPIView(api_views.BaseDashboardListCreateAPIView):
    service_class = ProductGroupService
    serializer_class = ProductGroupInputSerializer
    output_serializer_class = ProductGroupParentSerializer
    sort_order = ["sort_order", "-id"]

    def post(self, request, *args, **kwargs):
        service = self.service_class(
            tenant_code=request.tenant_code,
            site_profile=request.site_profile,
            user=request.user,
        )
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = service.create_product_group(**serializer.validated_data)
        serializer = self.output_serializer_class(instance)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)


class ProductGroupRetrieveUpdateDestroyAPIView(
    api_views.BaseDashboardRetrieveUpdateDestroyAPIView
):
    service_class = ProductGroupService
    serializer_class = ProductGroupInputSerializer
    output_serializer_class = ProductGroupParentSerializer

    def get_object(self):
        try:
            return self.service_class(
                tenant_code=self.request.tenant_code,
                site_profile=self.request.site_profile,
            ).read_by_code(
                code_value=self.kwargs["product_group_code"],
            )
        except ObjectDoesNotExist:
            raise ProductGroupNotFoundException

    def update(self, request, *args, **kwargs):
        service = self.service_class(
            tenant_code=self.request.tenant_code,
            site_profile=self.request.site_profile,
            user=request.user,
        )
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = service.update_product_group(
            instance=instance, **serializer.validated_data
        )
        return Response(data=self.output_serializer_class(instance).data)

    def delete(self, request, *args, **kwargs):
        service = self.service_class(
            tenant_code=self.request.tenant_code, site_profile=self.request.site_profile
        )
        instance = self.get_object()
        service.delete_product_group(instance)
        return Response(
            data={"message": "Deleted Successfully."}, status=status.HTTP_204_NO_CONTENT
        )
