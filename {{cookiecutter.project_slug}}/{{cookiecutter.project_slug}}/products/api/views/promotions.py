from django.core.exceptions import ObjectDoesNotExist
from django.db.models import ProtectedError
from rest_framework import filters

from {{cookiecutter.project_slug}}.common.bases import api_views
from {{cookiecutter.project_slug}}.products.api.serializers.promotions import PromotionSerializer
from {{cookiecutter.project_slug}}.products.api.views.product import ProductAPIMixin
from {{cookiecutter.project_slug}}.products.services import PromotionService
from {{cookiecutter.project_slug}}.rest_utils.exceptions import BadRequestException


class PromotionsListCreateAPIView(api_views.BaseDashboardListCreateAPIView):
    service_class = PromotionService
    serializer_class = PromotionSerializer

    filter_backends = [filters.SearchFilter]
    search_fields = ["code"]


class PromotionsRetrieveUpdateDeleteAPIView(
    api_views.BaseDashboardRetrieveUpdateDestroyAPIView
):
    service_class = PromotionService
    serializer_class = PromotionSerializer

    def get_object(self):
        try:
            return self.service_class(
                tenant_code=self.request.tenant_code,
                site_profile=self.request.site_profile,
            ).read_by_code(code_value=self.kwargs["code"])
        except ObjectDoesNotExist:
            raise BadRequestException(message="Invalid promotion CODE")

    def perform_destroy(self, instance):
        try:
            super().perform_destroy(instance)
        except ProtectedError:
            raise BadRequestException(
                message="Can not delete as, it is used in other instance"
            )


class ProductPromotionListAPIView(ProductAPIMixin, api_views.BaseDashboardListAPIView):
    service_class = PromotionService
    output_serializer_class = PromotionSerializer

    def get_queryset(self):
        product = self.get_product()
        return product.product_promotion.all()
