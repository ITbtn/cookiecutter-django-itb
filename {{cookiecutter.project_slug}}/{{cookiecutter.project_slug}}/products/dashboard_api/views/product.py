from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.response import Response

from {{cookiecutter.project_slug}}.common.bases import api_views
from {{cookiecutter.project_slug}}.products.dashboard_api.mixins import ProductAPIMixin
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers import (
    DashboardProductActivePriceListItemOutputSerializer,
    DashboardProductCreateSerializer,
    DashboardProductListSerializer,
    DashboardProductOutputSerializer,
    DashboardProductUpdateSerializer,
)
from {{cookiecutter.project_slug}}.products.models import Product
from {{cookiecutter.project_slug}}.products.services import ProductService
from {{cookiecutter.project_slug}}.rest_utils.exceptions import BadRequestException


class ProductListCreateAPIView(api_views.BaseDashboardListCreateAPIView):
    service_class = ProductService
    output_serializer_class = DashboardProductListSerializer
    input_serializer_class = DashboardProductCreateSerializer

    # filterset_class = ProductFilter
    search_fields = [
        "code",
        "name",
        "technical_name",
        "product_type__name",
        "brand__name",
    ]

    def get_queryset(self):
        service = self.service_class(
            tenant_code=self.request.tenant_code, site_profile=self.request.site_profile
        )
        queryset = service.get_all_products()
        if self.request.query_params.get("related_products_of"):
            related_products_code = service.get_related_products_code(
                product_code=self.request.query_params["related_products_of"]
            )
            queryset = queryset.filter(code__in=related_products_code)
        return queryset

    def post(self, request, *args, **kwargs):
        service = self.service_class(
            tenant_code=request.tenant_code,
            site_profile=request.site_profile,
            user=request.user,
        )
        serializer = self.input_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = service.create_product_instance(**serializer.validated_data)
        serializer = self.output_serializer_class(instance)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)


class ProductRetrieveUpdateDeleteAPIView(
    api_views.BaseDashboardRetrieveUpdateDestroyAPIView
):
    service_class = ProductService
    serializer_class = DashboardProductUpdateSerializer
    output_serializer_class = DashboardProductOutputSerializer
    queryset = Product.objects.all()

    def get_object(self):
        try:
            return self.service_class(
                tenant_code=self.request.tenant_code,
                site_profile=self.request.site_profile,
            ).read_by_code(code_value=self.kwargs["code"])
        except ObjectDoesNotExist:
            raise BadRequestException(message="Invalid product Code")

    def update(self, request, *args, **kwargs):
        product_instance = self.get_object()
        input_serializer = self.serializer_class(data=request.data, partial=True)
        input_serializer.is_valid(raise_exception=True)
        instance = self.service_class(
            tenant_code=request.tenant_code,
            site_profile=request.site_profile,
            user=request.user,
        ).update_product_instance(product_instance, **input_serializer.validated_data)
        output_serializer = self.output_serializer_class(
            instance=instance, context=self.get_serializer_context()
        )
        return Response(data=output_serializer.data)


class DashboardProductActivePriceListItemListAPIView(
    api_views.BaseDashboardListAPIView
):
    service_class = ProductService
    output_serializer_class = DashboardProductActivePriceListItemOutputSerializer

    def list(self, request, *args, **kwargs):
        active_product_price_list_items = self.service_class(
            tenant_code=request.tenant_code, site_profile=request.site_profile
        ).get_active_price_list_item_by_product_code(
            product_code=self.kwargs["product_code"],
            tenant_code=self.request.user.tenant_code,
        )
        page = self.paginate_queryset(active_product_price_list_items)
        if page is not None:
            serializer = self.output_serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.output_serializer_class(
            active_product_price_list_items, many=True
        )
        return Response(data=serializer.data)


class FetchProductDataFromOTAPIView(
    ProductAPIMixin, api_views.BaseDashboardRetrieveAPIView
):
    service_class = ProductService
    output_serializer_class = DashboardProductOutputSerializer

    def get(self, request, *args, **kwargs):
        service = self.service_class(
            tenant_code=self.request.user.tenant_code,
            site_profile=self.request.site_profile,
        )
        product = service.enrich_product_data_from_ot(
            product=self.get_product(), user=self.request.user, **kwargs
        )
        return Response(data=self.output_serializer_class(product).data)
