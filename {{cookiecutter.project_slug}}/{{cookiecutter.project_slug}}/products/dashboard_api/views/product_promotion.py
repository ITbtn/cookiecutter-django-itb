from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.response import Response

from {{cookiecutter.project_slug}}.common.bases import api_views
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers import (
    ProductPromotionInputSerializer,
    ProductPromotionOutputSerializer,
    ProductPromotionUpdateSerializer,
)
from {{cookiecutter.project_slug}}.products.exceptions import ProductPromotionNotFoundException
from {{cookiecutter.project_slug}}.products.services import ProductPromotionService, ProductService


class ProductPromotionListCreateAPIView(api_views.BaseDashboardListCreateAPIView):
    service_class = ProductPromotionService
    product_service_class = ProductService
    input_serializer_class = ProductPromotionInputSerializer
    output_serializer_class = ProductPromotionOutputSerializer

    def list(self, request, *args, **kwargs):
        product_service = self.product_service_class(
            tenant_code=self.request.user.tenant_code,
            site_profile=self.request.site_profile,
        )
        product_promotions_qs = product_service.get_product_promotions_by_product_code(
            product_code=self.kwargs["product_code"]
        )
        page = self.paginate_queryset(product_promotions_qs)
        if page is not None:
            serializer = self.output_serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.output_serializer_class(product_promotions_qs, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = self.input_serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        service = self.service_class(
            tenant_code=self.request.user.tenant_code,
            site_profile=self.request.site_profile,
        )
        service.create_product_promotion(
            product_code=self.kwargs["product_code"],
            promotion_code=data.get("promotion_code"),
            related_product_code=data.get("related_product_code"),
        )
        return Response(status=status.HTTP_201_CREATED)


class ProductPromotionRetrieveUpdateDestroyAPIView(
    api_views.BaseDashboardRetrieveUpdateDestroyAPIView
):
    service_class = ProductPromotionService
    serializer_class = ProductPromotionUpdateSerializer
    output_serializer_class = ProductPromotionOutputSerializer

    def get_object(self):
        try:
            product_promotion_instance = self.service_class(
                tenant_code=self.request.tenant_code,
                site_profile=self.request.site_profile,
            ).get_product_promotion_obj_by_product_promotion_code(
                product_code=self.kwargs["product_code"],
                product_promotion_code=self.kwargs["product_promotion_code"],
            )
            return product_promotion_instance
        except ObjectDoesNotExist:
            raise ProductPromotionNotFoundException

    def update(self, request, *args, **kwargs):
        product_promotion_instance = self.service_class(
            tenant_code=request.tenant_code, site_profile=request.tenant_code
        ).get_product_promotion(code=self.kwargs["product_promotion_code"])
        if not product_promotion_instance:
            raise ProductPromotionNotFoundException
        input_serializer = self.serializer_class(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        update_response = self.service_class(
            tenant_code=request.tenant_code, site_profile=request.tenant_code
        ).update_product_promotion_instance(
            self.kwargs["product_code"],
            product_promotion_instance,
            **input_serializer.validated_data
        )
        output_serializer = self.output_serializer_class(update_response)
        return Response(data=output_serializer.data, status=status.HTTP_200_OK)
