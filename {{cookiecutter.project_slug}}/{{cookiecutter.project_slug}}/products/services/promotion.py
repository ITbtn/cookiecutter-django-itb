import decimal

from django.core.exceptions import ValidationError
from django.utils import timezone

from {{cookiecutter.project_slug}}.common.bases.services import BaseModelService
from {{cookiecutter.project_slug}}.common.utils import get_object_or_none
from {{cookiecutter.project_slug}}.products.exceptions import (
    ProductNotFoundException,
    PromotionNotFoundException,
    RelatedProductNotFoundException,
)
from {{cookiecutter.project_slug}}.products.services.product_service import ProductService
from {{cookiecutter.project_slug}}.rest_utils.exceptions import BadRequestException

from ..models import ProductPromotion, Promotion


class PromotionService(BaseModelService):
    model = Promotion

    def get_promotion(self, **kwargs):
        return get_object_or_none(self.model, **kwargs)

    def get_monthly_fee_discount(self, promotion_id, recurring_monthly_fee):
        monthly_fee_discount = decimal.Decimal("0.00")

        # TODO: Move to another method
        try:
            promotion_obj = self.model.objects.get(id=promotion_id)
        except self.model.DoesNotExist:
            promotion_obj = None

        if promotion_obj:
            if promotion_obj.monthly_fee_discount:
                monthly_fee_discount = promotion_obj.monthly_fee_discount
            elif promotion_obj.monthly_fee_discount_percentage:
                monthly_fee_discount = recurring_monthly_fee * (
                    promotion_obj.monthly_fee_discount_percentage / 100
                )

        return monthly_fee_discount


class ProductPromotionService(BaseModelService):
    model = ProductPromotion

    def get_product_promotion(self, **kwargs):
        return get_object_or_none(self.model, **kwargs)

    def get_product_promotion_by_date_range(
        self, product_id, date_to_filter=timezone.now()
    ):
        return self.model.objects.filter(
            product_id=product_id,
            promotion__active=True,
            promotion__start_datetime__lte=date_to_filter,
            promotion__end_datetime__gte=date_to_filter,
        ).first()

    def get_product_promotion_by_product_code(
        self, product_code, date_to_filter=timezone.now()
    ):
        return (
            self.model.objects.filter(
                tenant_code=self.get_tenant_code(),
                product__code=product_code,
                promotion__active=True,
                promotion__start_datetime__lte=date_to_filter,
                promotion__end_datetime__gte=date_to_filter,
            )
            .select_related("product", "promotion")
            .first()
        )

    def create_product_promotion(
        self, product_code, promotion_code, related_product_code=None
    ):
        product_obj = ProductService(
            tenant_code=self.tenant_code, site_profile=self.site_profile
        ).get_product(code=product_code)
        if not product_obj:
            raise ProductNotFoundException
        promotion_obj = PromotionService(
            tenant_code=self.tenant_code, site_profile=self.site_profile
        ).get_promotion(code=promotion_code)
        if not promotion_obj:
            raise PromotionNotFoundException
        if related_product_code:
            if product_code == related_product_code:
                raise BadRequestException(
                    "Product and related product would not be similar."
                )
            related_product_obj = ProductService(
                tenant_code=self.tenant_code, site_profile=self.site_profile
            ).get_product(code=related_product_code)
            if not related_product_obj:
                raise RelatedProductNotFoundException
        else:
            related_product_obj = None
        code = f"{product_obj.code}-{promotion_obj.code}"
        field_values = {
            "code": code,
            "promotion": promotion_obj,
            "product": product_obj,
            "related_product": related_product_obj,
        }
        field_values.update({"tenant_code": self.get_tenant_code()})
        try:
            self.create(**field_values)
        except ValidationError:
            raise BadRequestException(
                f"Product Promotion with this code {code} already exists."
            )

    def get_product_promotion_obj_by_product_promotion_code(
        self, product_code, product_promotion_code
    ):
        return self.read_by_code(
            code_value=product_promotion_code, product__code=product_code
        )

    def update_product_promotion_instance(
        self, product_code, instance, **serialized_values
    ):
        field_values = {}
        if "promotion_code" in serialized_values.keys():
            promotion_obj = PromotionService(
                tenant_code=self.tenant_code, site_profile=self.site_profile
            ).get_promotion(code=serialized_values.get("promotion_code"))
            if not promotion_obj:
                raise PromotionNotFoundException
            field_values["promotion"] = promotion_obj
            product_promotion_code = f"{product_code}-{promotion_obj.code}"
            field_values["code"] = product_promotion_code
        if (
            not serialized_values["related_product_code"]
            or serialized_values["related_product_code"] == ""
        ):
            field_values["related_product"] = None
        if "related_product" not in field_values.keys():
            if product_code == serialized_values.get("related_product_code"):
                raise BadRequestException(
                    "Product and related product would not be similar."
                )
            related_product_obj = ProductService(
                tenant_code=self.tenant_code, site_profile=self.site_profile
            ).get_product(code=serialized_values.get("related_product_code"))
            if not related_product_obj:
                raise RelatedProductNotFoundException
            field_values["related_product"] = related_product_obj
        try:
            return self.update_model_instance(instance, **field_values)
        except ValidationError:
            raise BadRequestException(
                f"Product Promotion with this code {product_promotion_code} already exists."
            )
