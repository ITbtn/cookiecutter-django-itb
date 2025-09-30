from django.utils import timezone
from django.utils.functional import cached_property

from {{cookiecutter.project_slug}}.common.bases.services import BaseModelService
from {{cookiecutter.project_slug}}.common.cache import TenantBaseCache

from ...rest_utils.exceptions import BadRequestException
from ..configs.price_config import PriceType
from ..configs.relation_config import MANDATORY_RELATED_PRODUCT_RELATION_TYPES
from ..exceptions import ProductNotFoundException, ProductRelationAlreadyExistsException
from ..models import ProductRelation
from .price import PriceService
from .product_service import ProductService


class ProductRelationService(BaseModelService):
    model = ProductRelation

    def __init__(self, *args, **kwargs):
        super(ProductRelationService, self).__init__(*args, **kwargs)

    @cached_property
    def cache_service(self):
        return TenantBaseCache(
            tenant_code=self.tenant_code, site_profile=self.site_profile
        )

    @cached_property
    def product_service(self):
        return ProductService(
            tenant_code=self.tenant_code, site_profile=self.site_profile
        )

    def get_mandatory_related_products(self, product_code, required_product_code=None):
        """
        Retrieve mandatory related products. Currently we are returning a list of product_code. In the future we can
        return enriched product data.

        :param product_code: Code of the product for which we need to get related products
        :param required_product_code: Optional. If we need related product for a certain combination, then we need it.
        :return: List of related product_codes.
        """
        now = timezone.now()
        mandatory_product_list = []
        mandatory_product_relations_qs = self.model.objects.filter(
            product__code=product_code,
            product__is_available=True,
            product_to__is_available=True,
            valid_from__lte=now,
            valid_until__gte=now,
            is_mandatory=True,
            is_available=True,
            tenant_code=self.get_tenant_code(),
        )
        if required_product_code:
            mandatory_product_relations_qs = mandatory_product_relations_qs.filter(
                required_product__code=required_product_code
            )
        mandatory_product_list = mandatory_product_relations_qs.values_list(
            "product_to__code", flat=True
        )
        return mandatory_product_list

    def get_related_product(self, **kwargs):
        try:
            return ProductRelation.objects.get(**kwargs)
        except ProductRelation.DoesNotExist:
            pass

    def get_enriched_product(self, code):
        product_dict = self.product_service.get_enriched_product(code=code)
        if not product_dict:
            raise ProductNotFoundException
        return product_dict

    def get_related_products(self, product):
        return product.relation_product.all()

    def create_related_product(self, user, **data_dict):
        if data_dict.get("product") == data_dict.get("product_to"):
            raise BadRequestException(
                "related product and product itself can't be same."
            )

        if data_dict.get("product") == data_dict.get("required_product"):
            raise BadRequestException(
                "product itself and the required product can't be same."
            )

        if data_dict.get("product_to") == data_dict.get("required_product"):
            raise BadRequestException(
                "related product and the required product can't be same."
            )

        related_product_qs = self.get_related_product(
            product__code=data_dict.get("product"),
            product_to__code=data_dict.get("product_to"),
            relation_type=data_dict.get("relation_type"),
        )
        if related_product_qs:
            message = f"Already found a relation between {data_dict.get('product')} and {data_dict.get('product_to')}."
            raise ProductRelationAlreadyExistsException(message)

        data_dict["created_by"] = user
        data_dict["product_id"] = self.get_enriched_product(
            code=data_dict.pop("product")
        ).get("id")
        data_dict["product_to_id"] = self.get_enriched_product(
            code=data_dict.pop("product_to")
        ).get("id")

        required_product = data_dict.pop("required_product", None)
        if required_product:
            data_dict["required_product_id"] = self.get_enriched_product(
                code=required_product
            ).get("id")

        data_dict.update({"tenant_code": self.get_tenant_code()})

        related_product_instance = self.create(**data_dict)
        return related_product_instance

    def update_related_product(self, related_product_instance, user, **data_dict):
        if not related_product_instance:
            raise BadRequestException("Product relation not found.")

        if data_dict.get(
            "product_to", related_product_instance.product_to
        ) == data_dict.get(
            "required_product", related_product_instance.required_product
        ):
            raise BadRequestException(
                "related product and the required product can't be same."
            )

        if data_dict.get("product_to") == related_product_instance.product:
            raise BadRequestException("related product and the product can't be same.")

        if data_dict.get("required_product") == related_product_instance.product:
            raise BadRequestException("required product and the product can't be same.")

        data_dict["updated_by"] = user
        related_product_qs = self.update_model_instance(
            related_product_instance, **data_dict
        )
        return related_product_qs

    def get_product_price(self, product_code):
        product_dict = self.product_service.get_enriched_product(product_code)
        if not product_dict:
            raise BadRequestException("Product Not found.")

        price = PriceService(
            tenant_code=self.tenant_code, site_profile=self.site_profile
        ).get_product_price_from_db(
            product_code=product_code,
            price_type=PriceType.RECURRING_PRICE,
            vat_code=None,
        )
        if not price:
            price = PriceService(
                tenant_code=self.tenant_code, site_profile=self.site_profile
            ).get_product_price_from_db(
                product_code=product_code,
                price_type=PriceType.SALES_PRICE,
                vat_code=None,
            )
        return price

    def get_available_mandatory_related_products(self, product_code, **kwargs):
        """
        Get all valid related products by product_code

        :param product_code: Code of the product for which we need to get related products
        :return: Queryset of related products.
        """
        now = timezone.now()
        cache_key = f"related_products_{product_code}"
        cache = self.cache_service.get(cache_key)
        if cache:
            return cache

        related_product_qs = (
            self.model.objects.filter(
                relation_type__in=MANDATORY_RELATED_PRODUCT_RELATION_TYPES,
                product__code=product_code,
                product_to__is_available=True,
                product_to__valid_from__lte=now,
                product_to__valid_until__gte=now,
                valid_from__lte=now,
                valid_until__gte=now,
                is_available=True,
                tenant_code=self.tenant_code,
                **kwargs,
            )
            .select_related("product", "product_to")
            .prefetch_related("product_to__product_group")
        )
        self.cache_service.set(related_product_qs, cache_key)
        return related_product_qs

    def create_related_products(self, user, **data_dict):
        """generate related product relation
        1. Make a relation between accessory and parent product
        2. Make relation from parent product to accessory

        Args:
            user (Request.user): requested user
            data_dict (dict): dict of relation making data
        """
        _data_dict = data_dict.copy()
        product = self.product_service.get_product(code=data_dict["product"])
        product_to = self.product_service.get_product(code=data_dict["product_to"])

        if not product:
            raise ProductNotFoundException(
                message=f"Product (code={data_dict['product']}) not found"
            )

        if not product_to:
            raise ProductNotFoundException(
                message=f"Product (code={data_dict['product_to']}) not found"
            )

        try:
            self.create_related_product(user=user, **_data_dict)
        except ProductRelationAlreadyExistsException:
            pass

    def prepare_related_product_dict(self, product_from, product_to, data_dict):
        """prepare related product dict with product_from and product_to"""
        data = data_dict
        data["product"] = product_from
        data["product_to"] = product_to
        return data
