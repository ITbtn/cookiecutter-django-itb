from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.response import Response

from {{cookiecutter.project_slug}}.common.bases import api_views
from {{cookiecutter.project_slug}}.products.dashboard_api.mixins import ProductAPIMixin
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers import (
    DashboardProductAttributeInputSerializer,
    DashboardProductAttributeOutputSerializer,
    DashboardProductAttributeSerializer,
)
from {{cookiecutter.project_slug}}.products.services import ProductAttributeService


class ProductAttributeListCreateAPIView(
    ProductAPIMixin, api_views.BaseDashboardListCreateAPIView
):
    service_class = ProductAttributeService
    serializer_class = DashboardProductAttributeInputSerializer
    output_serializer_class = DashboardProductAttributeOutputSerializer

    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["attribute__code", "attribute__name"]
    filterset_fields = ["is_searchable"]

    def get(self, request, *args, **kwargs):
        service = self.service_class(
            tenant_code=self.request.tenant_code, site_profile=self.request.site_profile
        )
        product_instance = self.get_product()
        product_attributes_qs = service.get_product_attributes_by_product(
            product=product_instance
        )
        product_attributes_qs = self.filter_queryset(product_attributes_qs)
        page = self.paginate_queryset(product_attributes_qs)
        if page is not None:
            serializer = self.output_serializer_class(
                page, many=True, context=self.get_serializer_context()
            )
            return self.get_paginated_response(serializer.data)
        output_serializer = self.output_serializer_class(
            product_attributes_qs, many=True, context=self.get_serializer_context()
        )
        return Response(data=output_serializer.data)

    def post(self, request, *args, **kwargs):
        service = self.service_class(
            tenant_code=self.request.tenant_code, site_profile=self.request.site_profile
        )
        user = request.user
        product_instance = self.get_product()
        attribute_data = request.data
        attribute_data["product"] = product_instance.pk
        serializer = self.serializer_class(
            data=attribute_data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        attribute_instance = service.create_product_attribute(
            user, **serializer.validated_data
        )
        self.product_service_class(
            tenant_code=request.tenant_code, site_profile=request.site_profile
        ).update_product_to_elastic_by_code(product_code=product_instance.code)
        output_serializer = self.output_serializer_class(
            attribute_instance, context=self.get_serializer_context()
        )
        return Response(data=output_serializer.data, status=status.HTTP_201_CREATED)


class ProductAttributeRetrieveUpdateDestroyAPIView(
    ProductAPIMixin, api_views.BaseDashboardRetrieveUpdateDestroyAPIView
):
    service_class = ProductAttributeService
    serializer_class = DashboardProductAttributeSerializer
    output_serializer_class = DashboardProductAttributeOutputSerializer

    def get_object(self):
        # product_instance = self.get_product()
        return self.service_class(
            tenant_code=self.request.tenant_code, site_profile=self.request.site_profile
        ).get_product_attribute_by_attribute_code(
            attribute_code=self.kwargs.get("attribute_code"),
            tenant_code=self.request.user.tenant_code,
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # reindex
        self.product_service_class(
            tenant_code=request.tenant_code, site_profile=request.site_profile
        ).update_product_to_elastic_by_code(product_code=instance.product.code)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_product_code = instance.product.code
        instance.delete()

        # reindex
        self.product_service_class(
            tenant_code=request.tenant_code, site_profile=request.site_profile
        ).update_product_to_elastic_by_code(product_code=instance_product_code)
        return Response(data=None, status=status.HTTP_200_OK)
