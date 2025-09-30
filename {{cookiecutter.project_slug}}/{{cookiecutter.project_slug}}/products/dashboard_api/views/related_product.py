from rest_framework import status
from rest_framework.response import Response

from {{cookiecutter.project_slug}}.common.bases import api_views
from {{cookiecutter.project_slug}}.products.dashboard_api.mixins import ProductAPIMixin
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers import (
    RelatedProductInputSerializer,
    RelatedProductOutputSerializer,
    RelatedProductUpdateSerializer,
)
from {{cookiecutter.project_slug}}.products.services import ProductRelationService, ProductService


class RelatedProductsListCreateAPIView(
    ProductAPIMixin, api_views.BaseDashboardListCreateAPIView
):
    service_class = ProductRelationService
    product_service = ProductService
    input_serializer_class = RelatedProductInputSerializer
    output_serializer_class = RelatedProductOutputSerializer

    def get(self, request, *args, **kwargs):
        product_instance = self.get_product()
        related_products_qs = self.service_class(
            tenant_code=request.tenant_code, site_profile=request.site_profile
        ).get_related_products(product=product_instance)
        page = self.paginate_queryset(related_products_qs)
        if page is not None:
            serializer = self.output_serializer_class(
                page, many=True, context=self.get_serializer_context()
            )
            return self.get_paginated_response(serializer.data)
        serializer = self.output_serializer_class(
            related_products_qs, many=True, context=self.get_serializer_context()
        )
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        service = self.service_class(
            tenant_code=self.request.tenant_code, site_profile=self.request.site_profile
        )
        user = request.user
        related_product_data = request.data
        product_dict = self.product_service(
            tenant_code=self.request.tenant_code, site_profile=self.request.site_profile
        ).get_enriched_product(code=self.kwargs.get("product_code"))
        related_product_data["product"] = product_dict.get("code")
        serializer = self.input_serializer_class(data=related_product_data)
        serializer.is_valid(raise_exception=True)
        related_product_qs = service.create_related_products(
            user, **serializer.validated_data
        )
        output_serializer = self.output_serializer_class(
            related_product_qs, context=self.get_serializer_context()
        )
        return Response(data=output_serializer.data, status=status.HTTP_201_CREATED)


class RelatedProductsRetrieveDestroyAPIView(
    ProductAPIMixin, api_views.BaseDashboardRetrieveUpdateDestroyAPIView
):
    service_class = ProductRelationService
    product_service = ProductService
    serializer_class = RelatedProductUpdateSerializer
    output_serializer_class = RelatedProductOutputSerializer

    def patch(self, request, *args, **kwargs):
        user = request.user
        related_product_data = request.data
        product_dict = self.service_class(
            tenant_code=request.tenant_code, site_profile=request.site_profile
        ).get_enriched_product(self.kwargs.get("product_code"))
        related_product_data["product"] = product_dict.get("code")
        serializer = self.serializer_class(
            data=related_product_data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        related_product_instance = self.service_class(
            tenant_code=request.tenant_code, site_profile=request.site_profile
        ).get_related_product(code=self.kwargs.get("code"))
        related_product_qs = self.service_class(
            tenant_code=self.request.tenant_code, site_profile=self.request.site_profile
        ).update_related_product(
            related_product_instance, user, **serializer.validated_data
        )
        output_serializer = self.output_serializer_class(
            related_product_qs, context=self.get_serializer_context()
        )
        return Response(data=output_serializer.data, status=status.HTTP_201_CREATED)
