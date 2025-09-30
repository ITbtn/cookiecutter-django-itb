import decimal
import logging
import re
from collections import OrderedDict

from django.core.cache import caches
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db.models import F, Q
from django.forms.models import model_to_dict
from django.utils import timezone
from django.utils.functional import cached_property

from {{cookiecutter.project_slug}}.attributes.constants import AttributeType
from {{cookiecutter.project_slug}}.attributes.models import Attribute, AttributeGroup
from {{cookiecutter.project_slug}}.common.constants import ZERO
from {{cookiecutter.project_slug}}.common.utils import fix_external_decimal_places, get_object_or_none
from {{cookiecutter.project_slug}}.contacts.configs.purchase_gateways import PurchaseGateways
from {{cookiecutter.project_slug}}.documents.constants import (
    MEDIA_TYPE_IMAGES,
    MEDIA_TYPE_PDFS,
    ImageType,
)
from {{cookiecutter.project_slug}}.prices.constants import PriceListItemType, PriceListType
from {{cookiecutter.project_slug}}.prices.services.price_list_item_service import PriceListItemService
from {{cookiecutter.project_slug}}.rest_utils.exceptions import BadRequestException, NotFoundException
from {{cookiecutter.project_slug}}.search.signals import task_es_registry_update

from ..configs.price_config import PriceType
from ..configs.product_config import PRODUCT_BASIC_INFO_FIELDS, ProductItemType
from ..configs.relation_config import (
    MANDATORY_RELATED_PRODUCT_RELATION_TYPES,
    CommonRelationType,
)
from ..exceptions import InvalidLockFieldException, ProductNotFoundException
from ..models import Product, ProductAttribute, ProductRelation
from ..services.bases import BaseProductService
from ..services.product_attribute_service import ProductAttributeService
from ..services.product_brand import BrandService
from ..services.product_type import ProductTypeService
from ..utils.attribute import build_attributes_new
from .family_series import SeriesService
from .price import PriceService
from .product_serial import ProductSerialService
from .unit import UnitService
from .vat import VatService

logger = logging.getLogger(__name__)


class ProductService(BaseProductService):
    model = Product

    def __init__(self, user=None, *args, **kwargs):
        super(ProductService, self).__init__(*args, **kwargs)
        self.user = user

    @cached_property
    def product_attribute_service(self):
        return ProductAttributeService(
            tenant_code=self.tenant_code, site_profile=self.site_profile
        )

    @cached_property
    def product_serial_service(self):
        return ProductSerialService(
            tenant_code=self.tenant_code, site_profile=self.site_profile
        )

    @cached_property
    def brand_service(self):
        return BrandService(
            tenant_code=self.tenant_code, site_profile=self.site_profile
        )

    @cached_property
    def price_service(self):
        return PriceService(
            tenant_code=self.tenant_code, site_profile=self.site_profile
        )

    @cached_property
    def product_type_service(self):
        return ProductTypeService(
            tenant_code=self.tenant_code, site_profile=self.site_profile
        )

    @cached_property
    def product_group_service(self):
        from {{cookiecutter.project_slug}}.products.services import ProductGroupService

        return ProductGroupService(
            tenant_code=self.tenant_code, site_profile=self.site_profile
        )

    @cached_property
    def unit_service(self):
        return UnitService(tenant_code=self.tenant_code, site_profile=self.site_profile)

    @cached_property
    def vat_service(self):
        return VatService(tenant_code=self.tenant_code, site_profile=self.site_profile)

    @cached_property
    def series_service(self):
        return SeriesService(
            tenant_code=self.tenant_code, site_profile=self.site_profile
        )

    def get_product(self, **kwargs):
        if hasattr(self, "tenant_code"):
            kwargs.update({"tenant_code": self.tenant_code})
        return get_object_or_none(self.model, **kwargs)

    def read_by_code(self, code_value, **kwargs):
        try:
            return super().read_by_code(code_value, **kwargs)
        except ObjectDoesNotExist:
            raise ProductNotFoundException

    def get_catalog_service(self):
        from {{cookiecutter.project_slug}}.catalog.services.catalog_services import CatalogService

        catalog_service = CatalogService(
            tenant_code=self.tenant_code, site_profile=self.site_profile
        )
        return catalog_service

    def product_purchase_price_update_allowed(self, code):
        cache = caches["default"]
        cache_key = f"{self.get_tenant_code()}_{code}_purchase_price_update_allowed"
        cached_response = cache.get(cache_key)
        if cached_response:
            return cached_response

        can_update_purchase_price = False
        product = (
            Product.objects.filter(
                tenant_code=self.get_tenant_code(), code__iexact=code
            )
            .prefetch_related("price_set")
            .annotate(
                can_update_purchase_price=F("product_type__can_update_purchase_price")
            )
        )
        if product:
            can_update_purchase_price = product[0].can_update_purchase_price

        cache.set(cache_key, can_update_purchase_price, 60 * 60)
        return can_update_purchase_price

    def get_enriched_product(self, code):
        # CACHING
        # We could use from django.core.cache import cache which is equivalent to caches['default']. To make it flexible
        # we have used it explicitly
        cache = caches["default"]
        cache_key = self.get_tenant_code() + "_" + code
        cached_response = cache.get(cache_key)
        if cached_response:
            return cached_response

        product_data = {}
        product = (
            Product.objects.filter(
                tenant_code=self.get_tenant_code(), code__iexact=code
            )
            .prefetch_related("price_set")
            .annotate(
                type=F("product_type__system_type"),
                lineup_type=F("lineup__lineup_type"),
                can_update_purchase_price=F("product_type__can_update_purchase_price"),
                vat_code=F("vat__code"),
                vat_percentage=F("vat__percent_value"),
            )
            .values(
                "id",
                "code",
                "name",
                "export_id",
                "type",
                "duration",
                "product_type__system_type",
                "product_type__code",
                "product_type__can_update_purchase_price",
                "lineup_type",
                "brand__name",
                "can_update_purchase_price",
                "is_available",
                "valid_from",
                "valid_until",
                "vat_code",
                "vat_percentage",
                "default_supplier",
                "is_serial_keeping",
                "requires_quote",
            )
        )
        now = timezone.now()
        if product:
            product_obj = Product.objects.get(
                tenant_code=self.get_tenant_code(), code__iexact=code
            )
            product_data = product[0]
            product_doc = product_obj.documents.filter(
                Q(is_available=True)
                & Q(document__mime_type__in=MEDIA_TYPE_IMAGES)
                & Q(document__image_type=ImageType.SMALL)
                | Q(document__image_type=ImageType.MEDIUM)
            ).last()

            document_image = product_doc.document if product_doc else None
            product_data["product_thumbnail"] = (
                document_image.media.url
                if document_image and document_image.media
                else ""
            )
            product_data[
                "no_tkh"
            ] = self.product_attribute_service.get_no_tkh_product_attribute_value(
                product_code=product_data["code"]
            )
            product_data[
                "tkh"
            ] = self.product_attribute_service.get_sap_tkh_product_attribute_value(
                product_code=product_data["code"]
            )
            product_data[
                "can_apply_discount"
            ] = self.product_attribute_service.get_can_apply_discount_attribute_value(
                product_code=product_data["code"]
            )
            product_data[
                "account_type_required"
            ] = self.product_attribute_service.get_account_type_required(
                product_code=product_data["code"]
            )
            product_data[
                "terms_and_conditions"
            ] = self.prepare_terms_and_conditions_of_product(product_data["code"])

            default_price_data = {"price_value": ZERO, "price_type": "Undefined"}
            # Set default price type and price value.
            if product_data and "code" in product_data:
                default_price_obj = None
                price_qs = product_obj.price_set.filter(
                    price_type=PriceType.SALES_PRICE,
                    valid_from__lte=now,
                    valid_until__gte=now,
                ).order_by("-updated_at")

                # Still the product has multiple prices
                if price_qs.count() > 1:
                    # remove Zero prices if it has non Zero price
                    if price_qs.exclude(price=ZERO).count() > 0:
                        price_qs = price_qs.exclude(price=ZERO)
                    # Still the product has multiple prices
                    if price_qs.count() > 1:
                        price_qs = price_qs.order_by("price_type").distinct(
                            "price_type"
                        )
                        # Still the product has multiple prices
                        if price_qs.count() > 1:
                            # Now we have multiple not ZERO prices for different price types
                            # TODO: define the logic here. For the time being we are taking the last one.
                            default_price_obj = price_qs.last()
                        else:
                            default_price_obj = price_qs.first()
                    else:
                        default_price_obj = price_qs.first()
                else:
                    default_price_obj = price_qs.first()

                if default_price_obj is not None:
                    default_price_data["price_type"] = default_price_obj.price_type
                    default_price_data["price_value"] = default_price_obj.price

            product_data["price_type"] = default_price_data["price_type"]
            product_data["price_value"] = default_price_data["price_value"]
            product_data["market_types"] = self.get_market_type_list(product_obj)
            product_data["flow_types"] = self.get_flow_type_list(product_obj)
            product_data["channels"] = self.get_channel_list(product_obj)
            # Cache the product information for an hour.
            cache.set(cache_key, product_data, 60 * 60)
        return product_data

    def get_enriched_product_list(self, product_code_list):
        """
        :params: product_code_list ["893123", "512123"]
        this method will return a dictonary with prouct details
        without fetching multiple product individually this method will fetch
        multiple data at once and that is imporving performance a little bit
        {
            "893123": {
                "id": 1,
                "code": "893123",
                "name": "Apple"
            },
            "512123": {
                "id": 2,
                "code": "512123",
                "name": "Samsung"
            }
        }
        """
        product_wise_enriched_data = {}
        new_product_code_list = []
        for product_code in product_code_list:
            cached_response = self.cache_service.get(cache_key=product_code)
            if cached_response:
                product_wise_enriched_data[product_code] = cached_response
            else:
                new_product_code_list.append(product_code)

        product_queryset = (
            Product.objects.filter(
                tenant_code=self.get_tenant_code(), code__in=new_product_code_list
            )
            .prefetch_related("price_set")
            .annotate(
                type=F("product_type__system_type"),
                lineup_type=F("lineup__lineup_type"),
                vat_code=F("vat__code"),
                vat_percentage=F("vat__percent_value"),
            )
            .values(
                "id",
                "code",
                "name",
                "export_id",
                "type",
                "duration",
                "product_type__system_type",
                "product_type__code",
                "lineup_type",
                "campaign_code",
                "brand__name",
                "is_available",
                "valid_from",
                "valid_until",
                "vat_code",
                "vat_percentage",
            )
        )
        now = timezone.now()
        for product_data in product_queryset:
            # TODO: need to check this for photo
            product_obj = Product.objects.get(
                tenant_code=self.get_tenant_code(), code=product_data["code"]
            )
            product_doc = product_obj.documents.filter(
                Q(is_available=True)
                & Q(document__mime_type__in=MEDIA_TYPE_IMAGES)
                & Q(document__image_type=ImageType.SMALL)
                | Q(document__image_type=ImageType.MEDIUM)
            ).last()

            document_image = product_doc.document if product_doc else None
            product_data["product_thumbnail"] = (
                document_image.media.url
                if document_image and document_image.media
                else ""
            )
            if not product_data["image"] and product_data["product_thumbnail"]:
                product_data["image"] = product_data["product_thumbnail"]

            product_data[
                "no_tkh"
            ] = self.product_attribute_service.get_no_tkh_product_attribute_value(
                product_code=product_data["code"]
            )
            product_data[
                "tkh"
            ] = self.product_attribute_service.get_sap_tkh_product_attribute_value(
                product_code=product_data["code"]
            )
            product_data[
                "can_apply_discount"
            ] = self.product_attribute_service.get_can_apply_discount_attribute_value(
                product_code=product_data["code"]
            )

            # TODO: move this price calculation in price service
            default_price_data = {"price_value": ZERO, "price_type": "Undefined"}
            # Set default price type and price value.
            # todo: make sure we use the regular price routine?
            if product_data and "code" in product_data:
                default_price_obj = None
                price_qs = product_obj.price_set.filter(
                    valid_from__lte=now, valid_from__gte=now
                ).order_by("-updated_at")
                # filter out purchase price
                price_qs = price_qs.exclude(price_type=PriceType.PURCHASE_PRICE)

                # Still the product has multiple prices
                if price_qs.count() > 1:
                    # remove Zero prices if it has non Zero price
                    if price_qs.exclude(price=ZERO).count() > 0:
                        price_qs = price_qs.exclude(price=ZERO)
                    # Still the product has multiple prices
                    if price_qs.count() > 1:
                        price_qs = price_qs.order_by("price_type").distinct(
                            "price_type"
                        )
                        # Still the product has multiple prices
                        if price_qs.count() > 1:
                            # Now we have multiple not ZERO prices for different price types
                            # TODO: define the logic here. For the time being we are taking the last one.
                            default_price_obj = price_qs.last()
                        else:
                            default_price_obj = price_qs.first()
                    else:
                        default_price_obj = price_qs.first()
                else:
                    default_price_obj = price_qs.first()

                if default_price_obj is not None:
                    default_price_data["price_type"] = default_price_obj.price_type
                    default_price_data["price_value"] = default_price_obj.price

            product_data["price_type"] = default_price_data["price_type"]
            product_data["price_value"] = default_price_data["price_value"]
            product_data["market_types"] = self.get_market_type_list(product_obj)
            product_data["flow_types"] = self.get_flow_type_list(product_obj)
            product_data["channels"] = self.get_channel_list(product_obj)
            # Cache the product information for an hour.
            self.cache_service.set(
                cache_value=product_data,
                cache_key=product_data["code"],
                timeout=60 * 60,
            )
            product_wise_enriched_data[product_data["code"]] = product_data

        return product_wise_enriched_data

    # The purpose of get_product_detail and get_enriched_product are same but get_enriched_product are heavily used,
    # so instead of modifying it we are going to create new one.

    def get_product_detail(self, code):
        # CACHING
        # We could use from django.core.cache import cache which is equivalent to caches['default']. To make it flexible
        # we have used it explicitly
        cache = caches["default"]
        cache_key = self.tenant_code + "_" + code + "_detail"
        cached_response = cache.get(cache_key)
        if cached_response:
            return cached_response

        # Though there is no chance to get multiple products by same code, we have used filter to use select_related
        product_qs = Product.objects.filter(
            tenant_code=self.get_tenant_code(), code=code
        ).select_related("product_group", "brand")
        if product_qs.exists():
            product = product_qs[0]
            guarantee_period = self.product_attribute_service.get_specific_attribute(
                product_code=code, attribute_code="guarantee_period"
            ).first()
            can_apply_discount = self.product_attribute_service.get_specific_attribute(
                product_code=code, attribute_code="can_apply_discount"
            ).first()

        else:
            return {
                "product_id": "",
                "product_item_type": "",
                "description": "",
                "product_group": "",
                "product_group_name": "",
                "brand": "",
                "image_url": "",
                "guarantee_period": "",
                "can_apply_discount": "",
            }

        product_data = {
            "product_id": product.id,
            "product_item_type": product.product_type.system_type,
            "description": product.short_description,
            "product_group": product.product_group.code,
            "product_group_name": product.product_group.name,
            "brand": product.brand.code if product.brand else "",
            "guarantee_period": guarantee_period["value_integer"]
            if guarantee_period
            else "",
            "can_apply_discount": can_apply_discount["value_boolean"]
            if can_apply_discount
            else False,
            "vat_code": product.vat.code if product.vat else "",
            "vat_percentage": product.vat.percent_value if product.vat else "",
            "requires_quote": product.requires_quote,
        }
        # Cache the product information for an hour.
        cache.set(cache_key, product_data, 60 * 60)
        return product_data

    def filter_by_market_type(self, market_type=None):
        queryset = self.model.objects.all()
        if market_type:
            return queryset.filter(
                Q(productmarkettype__market_type=market_type)
                | Q(productmarkettype__market_type__isnull=True)
            )
        return queryset

    def filter(self, **kwargs):
        return self.model.objects.filter(**kwargs).prefetch_related("price_set")

    def get_add_ons_by_product_id(self, product_id, required_product_id=None):
        now = timezone.now()
        product_relation_qs = ProductRelation.objects.filter(
            product_id=product_id,
            relation_type=CommonRelationType.ADD_ON,
            product_to__product_type__system_type=ProductItemType.ADD_ON,
            product_to__is_available=True,
            valid_from__lte=now,
            valid_from__gte=now,
            is_available=True,
        ).filter(
            Q(required_product_id__isnull=True)
            | Q(required_product_id=required_product_id)
        )

        add_on_data_list = [
            model_to_dict(product_relation.product_to)
            for product_relation in product_relation_qs
        ]

        return add_on_data_list

    def get_sibling_products(self, product_code: str, catalog=None) -> list:
        sibling_product_list = []
        # reading the product on so many methods is not a good idea, maybe we need to pass the product in the argument.
        # product = self.read_by_code(code_value=product_code)
        # TOFIX find the sibling products with product series
        return sibling_product_list

    def get_siblings_by_product_id(self, product_id):
        try:
            return Product.objects.get(id=product_id)
        except ObjectDoesNotExist:
            return []

        # TOFIX find the sibling products with product series
        sibling_qs = []
        sibling_data_list = [model_to_dict(sibling) for sibling in sibling_qs]

        return sibling_data_list

    def get_sibling_dimensional_attributes_by_product_id(self, product_id):
        try:
            product_obj = Product.objects.get(id=product_id)
        except ObjectDoesNotExist:
            return []

        dimensional_attribute_qs = product_obj.product_attribute.filter(
            attribute__code__in=["color", "memory_size"]
        )

        dimensional_attribute_data_list = []
        for dimensional_attribute in dimensional_attribute_qs:
            dimensional_attribute_data = model_to_dict(dimensional_attribute)
            dimensional_attribute_data["value"] = dimensional_attribute.value
            dimensional_attribute_data[
                "attribute_code"
            ] = dimensional_attribute.attribute.code
            dimensional_attribute_data["option_code"] = (
                dimensional_attribute.option.code
                if dimensional_attribute.option
                else ""
            )
            dimensional_attribute_data_list.append(dimensional_attribute_data)

        return dimensional_attribute_data_list

    def get_flow_type_list(self, product):
        """
        Get the list of flow_types associated with the product.
        :param product: Instance of Product model.
        :return: List of flow_types.
        """
        if not product.flow_types.exists():
            return []

        flow_type_list = [
            flow_type
            for flow_type in product.flow_types.all().values_list(
                "flow_type", flat=True
            )
        ]
        return flow_type_list

    def get_market_type_list(self, product):
        """
        Get the list of market_types associated with the product.
        :param product: Instance of Product model.
        :return: List of market_types.
        """
        if not product.market_types.exists():
            return []

        market_type_list = [
            market_type
            for market_type in product.market_types.all().values_list(
                "market_type", flat=True
            )
        ]
        return market_type_list

    def get_channel_list(self, product):
        """
        Get the list of channels associated with the product.
        :param product: Instance of Product model.
        :return: List of channels.
        """
        if not product.channels.exists():
            return []

        channel_list = [
            channel
            for channel in product.channels.all().values_list("channel", flat=True)
        ]
        return channel_list

    # It will be used to create catalog from category. But we should make it a generic one.
    @staticmethod
    def complex_filter(filter_options_dict=None, fields=None, queryset=False):
        """
        This method will be used by other external services to apply different complex filters on products.
        :param filter_options_dict: dictionary that will contain complex filter options like and, not etc.
        :param fields: fields of the model to return
        :param queryset: if True returns the queryset without field mapping
        :return:
        """
        #  Ideally if there is no filter option supplied then we should return all products but that's not feasible.
        #  We decided that a service or service method always take dict and return dict.
        if not filter_options_dict:
            return {}
        and_filter_options = filter_options_dict.get("and", {})
        not_filter_options = filter_options_dict.get("not", {})
        or_filter_options = filter_options_dict.get("or", {})

        or_condition = None
        for key, val in or_filter_options.items():
            temp_dict = {key: val}
            if not or_condition:
                or_condition = Q(**temp_dict)
            else:
                or_condition |= Q(**temp_dict)

        products_qs = Product.objects.filter(**and_filter_options).exclude(
            **not_filter_options
        )
        if or_condition:
            products_qs = products_qs.filter(or_condition)

        products_qs = products_qs.distinct()

        if queryset:
            return products_qs
        if fields:
            products_qs = products_qs.values(*fields)
        else:
            products_qs = products_qs.values()
        products_list = list(products_qs)
        return products_list

    def get_is_discount_allowed(self, product_code):
        """
        :param product_code:
        :return:
        """
        discount_allowed = False
        product_details = self.get_product_detail(code=product_code)
        can_apply_discount = product_details.get("can_apply_discount")
        if can_apply_discount:
            discount_allowed = True
        return discount_allowed

    @staticmethod
    def extract_brand_name(product_name):
        # get first word from a sentence
        regex = re.compile(r"^[^\s]+")
        re_match = regex.match(product_name)
        if re_match:
            return re_match.group(0)

    def get_related_products_in_groups(self, product):
        now = timezone.now()
        product_group_data = OrderedDict()
        main_product = product
        related_products = main_product.relation_product.filter(
            product_to__is_available=True,
            product_to__valid_from__lte=now,
            product_to__valid_until__gte=now,
            valid_from__lte=now,
            valid_from__gte=now,
            is_available=True,
            tenant_code=self.get_tenant_code(),
        ).exclude(relation_type__in=MANDATORY_RELATED_PRODUCT_RELATION_TYPES)
        for relation in related_products:
            product_dict = {}
            product = relation.product_to
            if (
                not product
                or product.product_type.system_type == ProductItemType.SUBSCRIPTION
            ):
                continue
            sales_price = product.get_latest_sales_price()
            product_group = product.product_group
            stock = self.get_stock_by_product_code(product_code=product.code)
            price = model_to_dict(sales_price) if sales_price else {}
            if price:
                price["price"] = str(
                    fix_external_decimal_places(
                        decimal_value=decimal.Decimal(price["price"])
                    )
                )

            product_documents = (
                product.documents.filter(
                    is_available=True,
                    document__mime_type__in=MEDIA_TYPE_IMAGES,
                    document__image_type__in=[ImageType.MEDIUM, ImageType.SMALL],
                )
                .select_related("document")
                .order_by("document__image_type")
            )

            image_url = ""
            if product_documents.exists():
                product_document = product_documents.first()
                if product_document.document.media:
                    image_url = product_document.document.media.url

            product_dict.update(
                {
                    "id": product.id,
                    "code": product.code,
                    "name": product.name,
                    "short_description": product.short_description,
                    "long_description": product.long_description,
                    "specification": product.specification,
                    "slug": product.slug,
                    "brand": product.brand.name if product.brand else "",
                    "release_date": product.release_date,
                    "image": image_url,
                    "technical_name": product.technical_name,
                    "ian": product.ian,
                    "price": price,
                    "stock": stock,
                }
            )
            if product_group.name not in product_group_data:
                product_group_data[product_group.name] = []
            product_group_data[product_group.name].append(product_dict)

        return product_group_data

    def get_related_mandatory_products_in_groups(self, product, contact) -> dict:
        """get all related products of a product in group (mandatory & optional)

        Args:
            product (Product): product object for which related products will be fetched
            contact (Contact): contact object of the requester

        Returns: list
        [
            {
                "product_group": "Group name",
                "min_required": "0", # so this is optional
                "max_required": "1", # so only 1 item can be selected
                "products": [
                ....list of products ....
                ]
            },
            {
                "product_group": "another group",
                "min_required": "1", # so this is required
                "max_required": "1", # so only 1 item can be selected
                "products": [
                ....list of products ....
                ]
            },
            {
                "product_group": "1 items required, 1 optional",
                "min_required": "1", # so this is required
                "max_required": "2", # so only 1 item can be selected
                "products": [
                ....list of products ....
                ]
            },
            {
                "product_group": "0 items required, 5 optional",
                "min_required": "0", # all optional
                "max_required": "5", # but max 5 can be selected
                "products": [
                ....list of products ....
                ]
            }
        ]
        """
        from {{cookiecutter.project_slug}}.catalog.services.catalog_contact_group import (
            CatalogContactGroupService,
        )
        from {{cookiecutter.project_slug}}.catalog.services.catalog_services import CatalogProductService
        from {{cookiecutter.project_slug}}.products.services import ProductRelationService

        related_product_service = ProductRelationService(
            tenant_code=self.tenant_code,
            site_profile=self.site_profile,
        )
        catalog_contact_group_service = CatalogContactGroupService(
            tenant_code=self.tenant_code,
            site_profile=self.site_profile,
        )
        catalog_product_service = CatalogProductService(
            tenant_code=self.tenant_code,
            site_profile=self.site_profile,
        )

        data = []
        contact_group_code = None

        if not contact:
            return data

        if contact.contact_group:
            contact_group_code = contact.contact_group.code

        catalog_codes = (
            catalog_contact_group_service.catalog_codes_by_contact_group_code(
                contact_group_code=contact_group_code
            )
        ) or []

        related_products = (
            related_product_service.get_available_mandatory_related_products(
                product_code=product.code
            )
        )

        product_groups = related_products.values_list(
            "product_to__product_group_id", flat=True
        ).order_by("product_to__product_group__sort_order")
        product_groups = list(OrderedDict.fromkeys(product_groups))

        for product_group in product_groups:
            products = []
            catalog_product_codes = []
            related_products_by_product_group = related_products.filter(
                product_to__product_group_id=product_group
            )

            for related_product in related_products_by_product_group:
                for catalog_code in catalog_codes:
                    try:
                        catalog_product = catalog_product_service.get_catalog_product(
                            catalog_code=catalog_code,
                            product_code=related_product.product_to.code,
                        )
                        catalog_product_codes.append(catalog_product.product.code)
                        break
                    except ObjectDoesNotExist:
                        catalog_product = None

            catalog_products_dict = self.get_enriched_product_list(
                product_code_list=catalog_product_codes
            )

            for product_code, product_dict in catalog_products_dict.items():
                sales_price = self.get_product_sales_price(
                    product_code=product_code, contact_id=contact.id
                )
                sales_price_ex_vat = str(
                    fix_external_decimal_places(
                        decimal_value=self.get_product_sales_price_ex_vat(
                            product_code=product_code, price=sales_price
                        )
                    )
                )

                sales_price = str(
                    fix_external_decimal_places(decimal_value=sales_price)
                )

                # pop data
                for key in ["id"]:
                    product_dict.pop(key)

                product_dict.update(
                    {
                        "sales_price": sales_price,
                        "sales_price_ex_vat": sales_price_ex_vat,
                    }
                )
                products.append(product_dict)

            # if no catalog product found, then related products of this product_group
            # are not connected with any catalog or catalog_contact_group
            if catalog_product_codes:
                product_group = (
                    related_products_by_product_group.first().product_to.product_group
                )
                data.append(
                    {
                        "product_group": product_group.name,
                        "min_required": product_group.min_product,
                        "max_required": product_group.max_product,
                        "sort_order": product_group.sort_order,
                        "products": products,
                    }
                )

        return data

    def get_discount_products(self, product_code):
        if product_code is None:
            return Product.objects.none()

        now = timezone.now()
        discount_product_id_qs = ProductRelation.objects.filter(
            product__code=product_code,
            relation_type=CommonRelationType.DISCOUNT,
            product_to__product_type__system_type=ProductItemType.DISCOUNT,
            product__is_available=True,
            product_to__is_available=True,
            valid_from__lte=now,
            valid_from__gte=now,
            is_available=True,
        ).values_list("product_to_id", flat=True)
        discount_product_id_list = list(discount_product_id_qs)
        # TODO: Service shouldn't return queryset to other service. Needs to be a dict.
        return Product.objects.filter(id__in=discount_product_id_list)

    def read_by_ian(self, ian_value, **kwargs):
        """
        Read object by ian value
        :param ian_value: ian of the desired product
        :return: model instance
        """
        product_obj = None
        try:
            product_obj = self._get_queryset(**kwargs).get(ian=ian_value)
        except self.model.DoesNotExist:
            try:
                product_obj = self._get_queryset(**kwargs).get(ians__ian=ian_value)
            except self.model.DoesNotExist:
                raise ObjectDoesNotExist
            except MultipleObjectsReturned:
                logger.error(f"Error: For IAN {ian_value}, multiple objects returned.")
        except MultipleObjectsReturned:
            logger.error(f"Error: For IAN {ian_value}, multiple objects returned.")
        return product_obj

    def filter_products_by_ian(self, **kwargs):
        """
        Expected input:
            ian__in="12335,345434,34343"
            or
            ian="12334"
        """
        query_dict = {}
        products = self._get_queryset(**kwargs)
        if not products:
            if kwargs.get("ian__in"):
                query_dict["ians__ian__in"] = kwargs.get("ian__in", "")
            else:
                query_dict["ians__ian"] = kwargs.get("ian", "")
            products = self._get_queryset(**query_dict)
        return products

    def get_dropshipment_supplier_of_product(self, product_code):
        """
        Get a list of dropshipment suppliers for the given product_code
        :param product_code:
        :return:
        """
        dropshipment_suppliers = self.price_service.get_dropshipment_suppliers(
            product_code=product_code
        )
        return dropshipment_suppliers

    def is_dropshipment_allowed(self, product_code):
        """
        Check if drop_shipment is allowed, we only allow drop_shipment if the supplier has stock
        TODO: if product has multiple suppliers, define the proper business rules
        :param product_code:
        :return: True if dropshipment is allowed
        """
        has_dropshipment_stock = False
        has_dropshipment_supplier = self.price_service.has_dropshipment_supplier(
            product_code=product_code
        )
        if has_dropshipment_supplier:
            dropshipment_stock = 0
            for uuid in self.get_dropshipment_supplier_of_product(
                product_code=product_code
            ).keys():
                # TODO: have to fix
                dropshipment_stock = dropshipment_stock + 0
            # check if there is stock at the suppliers
            has_dropshipment_stock = dropshipment_stock > 0
        return has_dropshipment_supplier and has_dropshipment_stock

    def get_preferred_supplier_data(self, product_code):
        # TODO: Define the preferred supplier logic. Currently we are taking a random suppler. First we are checking
        #  if there is supplier with gateway configured, if not then we check for supplier without gateway.
        #  This will work until we integrate OneTrail.
        all_supplier_data_dict = self.price_service.get_all_supplier_data(
            product_code=product_code
        )
        first_dropshipment_supplier = {}
        first_non_dropshipment_supplier = {}
        for uuid, supplier_data_dict in all_supplier_data_dict.items():
            if supplier_data_dict["purchase_gateway"] != PurchaseGateways.NO_GATEWAY:
                first_dropshipment_supplier = supplier_data_dict
                break
            else:
                if not first_non_dropshipment_supplier:
                    first_non_dropshipment_supplier = supplier_data_dict
        return (
            first_dropshipment_supplier
            if first_dropshipment_supplier
            else first_non_dropshipment_supplier
        )

    def get_all_purchase_prices(self, product_code):
        all_purchase_prices = self.price_service.get_all_supplier_price_data_of_product(
            product_code=product_code
        )
        return all_purchase_prices

    def get_supplier_product_price_data(self, product_code, supplier_uuid):
        return self.price_service.get_supplier_price_data(
            product_code=product_code, supplier_uuid=supplier_uuid
        )

    def get_active_price_list_item_by_product_code(self, product_code, **kwargs):
        price_list_item_service = PriceListItemService(
            tenant_code=self.get_tenant_code(), site_profile=self.get_site_profile()
        )
        self.read_by_code(code_value=product_code)
        kwargs.update(
            {
                "price_list_period__start_datetime__lte": timezone.now(),
                "price_list_period__end_datetime__gte": timezone.now(),
            }
        )
        active_price_list_items = price_list_item_service.list(
            product_code=product_code, **kwargs
        )
        return active_price_list_items

    def get_product_sales_price(self, product_code, contact_id):
        sales_price = self.price_service.get_sales_price_for_contact(
            product_code, contact_id
        )
        return sales_price

    def get_product_sales_price_ex_vat(self, product_code, price):
        return self.price_service.get_price_without_vat(product_code, price)

    def is_product_available(self, product_code, flow_type, market_type, channel):
        """
        :param product_code: Product Code
        :param flow_type: Flow Type Code
        :param market_type: Market Type Code
        :param channel: Channel Code

        Check if the product is available
        Checking criteria:
        1. product is_available = True
        2. active in valid_from to valid_until
        3. If market_type, flow_type and channel is not given to check then product is available
        4. If product has no market_type, flow_type and channel configured then product is available
        5. If market_type, flow_type and channel is given for check and
            product has no market_type, flow_type and channel configured then product is available
        6. If market_type, flow_type and channel is given for check and
            product has market_type, flow_type and channel configured and
            given sales context matched with product sales context then is available
        7. else not available
        """
        now = timezone.now()
        product_available = True

        product = self.get_enriched_product(code=product_code)
        if not product:
            product_available = False
        else:
            if not product["is_available"] or (
                product["valid_from"]
                and product["valid_until"]
                and not product["valid_from"] <= now <= product["valid_until"]
            ):
                product_available = False
            if flow_type and product["flow_types"]:
                product_available = flow_type in product["flow_types"]
            if market_type and product["market_types"]:
                product_available = market_type in product["market_types"]
            if channel and product["channels"]:
                product_available = channel in product["channels"]

        return product_available

    def get_product_promotions_by_product_code(self, product_code):
        try:
            product_obj = self.read_by_code(
                code_value=product_code, tenant_code=self.get_tenant_code()
            )
            return product_obj.product_promotion.all()
        except ObjectDoesNotExist:
            raise ProductNotFoundException

    def get_all_products(self, **kwargs):
        """
        Get and return all products qs
        :param kwargs: dict, containing keys of the filters that needs to be applied
        :return: qs, containing all products
        """
        return self.list(**kwargs).order_by("-id")

    def get_related_products_code(self, product_code):
        product = self.read_by_code(code_value=product_code)
        now = timezone.now()
        related_products = (
            product.relation_product.filter(
                Q(valid_from__lte=now) | Q(valid_from__isnull=True),
                Q(valid_until__gte=now) | Q(valid_until__isnull=True),
                is_available=True,
                tenant_code=self.tenant_code,
                product_to__is_available=True,
                product_to__valid_from__lte=now,
                product_to__valid_until__gte=now,
            )
            .select_related("product_to")
            .values_list("product_to__code", flat=True)
        )
        return related_products

    def get_order_unit_for_product(self, product_id, contact_id, user):
        """
        This method is created to call cart validator service from search app
        Calling CartValidator service directly raises circular import issues.
        We will fix circular import issues first then responsibility of this method will be deprecated.
        """
        from {{cookiecutter.project_slug}}.cart_validator.services import CartValidatorService

        validator_service = CartValidatorService(
            tenant_code=self.get_tenant_code(),
            user=user,
            site_profile=self.site_profile,
        )
        # for anonymous user calls we can't check order unit because there are no contact or user
        if contact_id is None and user.is_anonymous:
            return 1
        cache_key = f"order_unit-{product_id}-{contact_id}"
        data = self.cache_service.get(cache_key=cache_key)
        if data:
            return data
        else:
            data = validator_service.get_order_unit(
                product_id=product_id, contact_id=contact_id
            )
            self.cache_service.set(cache_value=data, cache_key=cache_key)
            return data

    def get_product_usages_prices(self, product_code, contact):
        """
        Get the usages pricing of the product from pricelist prices that are related to usages prices.
        :param product_code: the product code from which we want the usages pricing
        :param contact: if specified we check if we can fetch the contact specific pricing
        """
        from {{cookiecutter.project_slug}}.prices.services.price_list_service import PriceListService

        price_list_service = PriceListService(
            tenant_code=self.tenant_code, site_profile=self.site_profile
        )
        product_usages_prices = self.get_actual_product_usages_prices(
            product_code=product_code
        )
        usages_prices = price_list_service.get_price_of_item_in_active_period(
            product_code=product_code,
            contact=contact,
            price_list_type=PriceListType.USAGES,
        )
        usages_prices = self.calculate_usages_prices(
            product_code, product_usages_prices, usages_prices
        )
        return usages_prices

    def get_actual_product_usages_prices(self, product_code):
        price = ZERO
        price_ex_vat = ZERO
        product = self.get_product(**{"code": product_code})

        if product:
            usage_price = product.price_set.filter(
                price_type=PriceType.USAGES_PRICE
            ).first()
            if usage_price:
                price = usage_price.price
                price_ex_vat = usage_price.price_ex_vat
        return price, price_ex_vat

    def calculate_usages_prices(
        self, product_code, product_usages_prices, price_list_prices
    ):
        prices = []
        price, price_ex_vat = product_usages_prices

        # price from product itself
        default_usages_price = {
            "product_code": product_code,
            "quantity": 1,
            "percentage": "00.00",
            "price": str(price),
            "price_ex_vat": str(price_ex_vat),
            "price_type": PriceListItemType.USAGES,
        }

        if price_list_prices:
            prices.append(default_usages_price)

        for price_list_price in price_list_prices:
            if price_list_price.price_type == PriceListItemType.DISCOUNT:
                discount_percentage = price_list_price.percentage
                price_list_price.price = price - (price * (discount_percentage / 100))
                price_list_price.price_ex_vat = price_ex_vat - (
                    price_ex_vat * (discount_percentage / 100)
                )

            instance_dict = {
                "product_code": price_list_price.product_code,
                "quantity": price_list_price.quantity,
                "percentage": str(price_list_price.percentage),
                "price": str(price_list_price.price),
                "price_ex_vat": str(price_list_price.price_ex_vat),
                "price_type": price_list_price.price_type,
            }
            prices.append(instance_dict)

        # no price list found but has usages price in product itself
        if not prices and (price or price_ex_vat):
            prices.append(default_usages_price)
        return prices

    def save_product_data(self, product, data, user=None):
        """
        This method is created to save product data in db
        :param product: product object
        :param data: data to be saved ( we got from ot api)
        :return: updated product object
        """
        brand_data = data.get("brand")
        # attr_data = data.get("attributes")
        product_data = data.get("product")
        # product_documents = product_data.get("image_data")

        if not product.brand_id and brand_data:
            brand_data["tenant_code"] = self.get_tenant_code()
            brand = self.brand_service.get_or_create(
                get_data={
                    "code": brand_data["code"],
                    "tenant_code": self.get_tenant_code(),
                },
                default_data=brand_data,
            )
            product_data["brand_id"] = brand.id

        # changing dict key name, description to long_description to save the data.
        product_data["long_description"] = product_data["description"]

        # we don't want to update product_code, valid_from, valid_until
        keys_to_remove = ("code", "ian", "valid_from", "valid_until")
        for key in keys_to_remove:
            product_data.pop(key)

        # if lock product group attribute is there and boolean value is true
        # then product group is not available for update.
        if not self.product_attribute_service.is_product_group_update_locked(
            product_obj=product
        ):
            product.product_group_id = data.get("product_group_id")

        # update product info
        product_data["updated_by"] = user
        self.update_model_instance(product, **product_data)
        # set alternative group
        product.alternative_groups.add(*data.get("alternative_groups_id", []))

        return product

    def update_product_to_elastic_by_code(self, product_code):
        """Get a product with product code and update it in elastic search"""
        try:
            product_instance = self.read_by_code(code_value=product_code)
            task_es_registry_update.delay(
                product_instance.pk,
                product_instance._meta.app_label,
                product_instance._meta.concrete_model.__name__,
            )
        except ObjectDoesNotExist:
            pass

    def update_product_group(self, product_group_code, product_instance):
        from {{cookiecutter.project_slug}}.products.services import ProductGroupService

        try:
            product_group = ProductGroupService(
                tenant_code=self.tenant_code, site_profile=self.site_profile
            ).read_by_code(code_value=product_group_code)
        except ObjectDoesNotExist:
            raise BadRequestException(
                message=f"Product group {product_group_code} doesnt exist"
            )

        product_instance.product_group = product_group
        product_instance.save()
        return product_instance

    def create_product(self, product_data, supplier):
        """
        this is a generic product create method.
        We can create product that we got from onetrail. and any other sources.
        sample product_data dict
        {
            "brand": {
                "code": "hp-enterprise",
                "name": "HP ENTERPRISE",
                "description": "HP ENTERPRISE",
            },
            "product": {
                "code": "hl2p5e",
                "name": "HPE Foundation Care Next Business Day Exchange Service",
                "valid_from": "2020-11-17",
                "valid_until": "2099-12-30",
                "ian": "",
                "seller_product_code": "5169273",
                "technical_name": "Next Business Day Exchange Service",
                "short_description": "",
                "description": "",
                "product_model": "Next Business Day Exchange Service",
                "product_line": "HPE Foundation Care",
                "image_data": [
                    {
                        "url": "url",
                        "code": "5a759a8883418983",
                        "mimetype": "image/jpeg",
                        "media_type": "Brand logo",
                        "width": 200,
                        "height": 150,
                        "size": 5235,
                    }
                ]
            },
            "attributes": [
                {
                    "code": "extendedspecifications",
                    "name": "Extendedspecifications",
                    "attributes": [
                        {
                            "code": "H0000513T0002871B6140518",
                            "name": "Ontworpen voor",
                            "value": "P/N: JL728A, JL728AR",
                        }
                    ]
                }
            ],
            "prices": [
                {
                    "quantity": 1,
                    "price_type": "purchase_price",
                    "price_ex_vat": "436.570000",
                    "updated_at": "2023-01-02T08:35:42.430030+01:00",
                    "supplier": {
                        "code": "8714253023106",
                        "name": "Ingram Micro BV",
                        "company_code": "company_code"
                    },
                },
            ],
            "product_type": {"name": "Service", "system_type": "service"},
            "product_group": [
                {
                    "code": "",
                    "name": "",
                    "sub_groups": [
                        {
                            "code": "",
                            "name": "",
                            "sub_groups": [
                                {
                                    "code": "",
                                    "name": "",
                                    "sub_groups": [
                                        {
                                            "code": "",
                                            "name": "",
                                            "sub_groups": [],
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
            "product_group_id": 55101,
            "alternative_groups_id": [],
        }

        """

        # TODO: Have to work for supplier.
        _product = product_data.get("product", {})
        product_type_dict = product_data.pop("product_type")
        brand_dict = product_data.pop("brand")
        # product_group_dict = product_data.pop("product_group")
        product_attributes = product_data.pop("attributes", [])
        # image_data = _product.get("image_data", [])
        # price we get from Onetrail
        prices = product_data.get("prices", [])
        brand_obj = None
        # we will only save purchase price data we get from Onetrail
        # purchase_prices = [
        #     price
        #     for price in prices
        #     if price.get("price_type") == ProductItemPriceType.PURCHASE_PRICE
        # ]
        # sales_prices = [
        #     price
        #     for price in prices
        #     if price.get("price_type") == ProductItemPriceType.SALES_PRICE
        # ]

        if brand_dict:
            brand_obj = self.brand_service.get_or_create(
                get_data={"tenant_code": self.tenant_code, "code": brand_dict["code"]},
                default_data=brand_dict,
            )
        try:
            product_type = self.product_type_service.get_or_create(
                get_data={
                    "tenant_code": self.tenant_code,
                    "system_type": product_type_dict["system_type"],
                    "name": product_type_dict["name"],
                },
                default_data=product_type_dict,
            )
        except MultipleObjectsReturned as ex:
            message = f"""
                Product create, multiple product type found: {ex}
                for system type : {product_type_dict['system_type']}"""
            logger.error(message)
            product_type = self.product_type_service.model.objects.filter(
                system_type=product_type_dict["system_type"]
            ).first()

        product = {
            "tenant_code": self.tenant_code,
            "product_type_id": product_type.id,
            "product_group_id": product_data.get("product_group_id", None),
            "name": _product.get("name", "")[:256],
            "short_description": _product.get("short_description", ""),
            "long_description": _product.get("description", ""),
            "valid_from": _product.get("valid_from", ""),
            "valid_until": _product.get("valid_until", ""),
            "code": _product.get("code", ""),
            "ian": _product.get("ian", ""),
            "brand": brand_obj,
            "last_import_update": timezone.now(),
            "technical_name": _product.get("technical_name", ""),
            "product_family": _product.get("product_line", ""),
            "product_series": _product.get("product_model", "")[:50],
            # in our product model we can only save upto 50 chars.
            "default_supplier_uuid": supplier.uuid,
        }
        product_data.update(product)
        product = self.create(**product_data)
        # set alternative group
        product.alternative_groups.add(*product_data.get("alternative_groups_id", []))

        if prices:
            self.price_service.save_product_price(
                product=product, prices=prices, **_product
            )
        build_attributes_new(
            tenant_code=self.tenant_code,
            product_id=product.id,
            attributes=product_attributes,
        )

        return product

    def enrich_field_data_for_product(self, data):
        # dict pattern -> {serializer_field_name: [model_field_name, service_class]}
        field_mapping = {
            "alternative_product": ["alternative_product", self],
            "product_type": ["product_type", self.product_type_service],
            "unit": ["unit", self.unit_service],
            "brand": ["brand", self.brand_service],
            "product_group": ["product_group", self.product_group_service],
            "series": ["series", self.series_service],
            "vat": ["vat", self.vat_service],
        }
        # model_field_names = ["alternative_product", "product_type", "unit", "brand", "product_group", "series", "vat"]
        for serializer_field in field_mapping.keys():
            model_field_name = field_mapping[serializer_field][0]
            service_class = field_mapping[serializer_field][1]
            code_value = data.pop(serializer_field, None)
            if code_value == "":
                data.update({model_field_name: None})
            elif code_value:
                try:
                    instance = service_class.read_by_code(
                        code_value=code_value, tenant_code=self.tenant_code
                    )
                except ObjectDoesNotExist:
                    raise NotFoundException(message=f"{serializer_field} not found")
                data.update({model_field_name: instance})

        return data

    def create_product_instance(self, **field_data):
        self.enrich_field_data_for_product(field_data)
        field_data.update({"created_by": self.user})
        alternative_group_codes = field_data.pop("alternative_group", [])
        if field_data.get("default_supplier"):
            from {{cookiecutter.project_slug}}.contacts.services import ContactService

            field_data["default_supplier"] = ContactService(
                tenant_code=self.tenant_code, site_profile=self.site_profile
            ).get_contact_by_uuid(field_data["default_supplier"])

        try:
            instance = self.create(**field_data)
            if alternative_group_codes:
                alternative_groups = self.product_group_service.list(
                    code__in=alternative_group_codes
                )
                instance.alternative_groups.set(alternative_groups)
        except Exception as e:
            raise BadRequestException(
                error_code="VALIDATION_ERROR", message=f"{e.messages[0]}"
            )
        else:
            return instance

    def update_product_instance(self, product_obj, **field_data):
        self.enrich_field_data_for_product(field_data)
        field_data.update({"updated_by": self.user})
        if field_data.get("default_supplier"):
            from {{cookiecutter.project_slug}}.contacts.services import ContactService

            field_data["default_supplier"] = ContactService(
                tenant_code=self.tenant_code, site_profile=self.site_profile
            ).get_contact_by_uuid(field_data["default_supplier"])
        if (
            field_data.get("alternative_group_ids")
            or field_data.get("alternative_group_ids") == []
        ):
            alternative_group_ids = field_data.pop("alternative_group_ids")
        else:
            alternative_group_ids = None
        try:
            product_instance = self.update_model_instance(product_obj, **field_data)
            if alternative_group_ids is not None:
                product_instance.alternative_groups.set(alternative_group_ids)

        except Exception as e:
            raise BadRequestException(
                errors="VALIDATION_ERROR", message=f"{e.messages[0]}"
            )
        else:
            return product_instance

    def has_lock(self, field_type, product_obj):
        """
        Check if product is locked for update.
        :param field_type:
        :param product_obj:
        :return:
        """
        attribute = self.get_lock_attribute(field_type)
        return attribute.product_attribute.filter(
            product_id=product_obj.id, value_boolean=True
        ).exists()

    def unlock_field(self, field_type, product_obj):
        """
        Unlock field if product is locked for update.
        :param field_type:
        :param product_obj:
        :return:
        """
        attribute = self.get_lock_attribute(field_type)
        if attribute.attribute.product_attribute.filter(
            product_id=product_obj.id, value_boolean=True
        ).exists():
            lock_attr = attribute.attribute.product_attribute.filter(
                product_id=product_obj.id, value_boolean=True
            ).first()
            lock_attr.value_boolean = False
            lock_attr.save()

    def lock_field(self, attribute, product_obj):
        """
        Lock field if product is locked for update.
        :param attribute:
        :param product_obj:
        :return:
        """
        try:
            lock_attr = ProductAttribute.objects.get(
                tenant_code=self.tenant_code,
                product_id=product_obj.id,
                attribute_id=attribute.id,
            )
            lock_attr.value_boolean = True
            lock_attr.save()
        except ProductAttribute.DoesNotExist:
            lock_attr = ProductAttribute.objects.create(
                tenant_code=self.tenant_code,
                product_id=product_obj.id,
                attribute_id=attribute.id,
                value_boolean=True,
            )

    def get_lock_code(self, field_type):
        if hasattr(self.model, field_type):
            return f"lock_{field_type}"

    def get_lock_attribute(self, field_type):
        """
        Get lock attribute for field type.
        :param field_type:
        :return:
        """
        attribute_code = self.get_lock_code(field_type=field_type)
        if not attribute_code:
            raise InvalidLockFieldException()
        try:
            group = AttributeGroup.objects.get(
                tenant_code=self.tenant_code, code="update_lock"
            )
        except AttributeGroup.DoesNotExist:
            group = AttributeGroup.objects.create(
                tenant_code=self.tenant_code,
                code="update_lock",
                name="Update Lock",
                description="Update Lock",
            )
        try:
            attribute = Attribute.objects.get(
                tenant_code=self.tenant_code,
                code=attribute_code,
                attribute_group=group,
                attribute_type=AttributeType.BOOLEAN,
            )
        except Attribute.DoesNotExist:
            attribute = Attribute.objects.get(
                tenant_code=self.tenant_code,
                code=attribute_code,
                attribute_group=group,
                name=attribute_code.upper(),
                attribute_type=AttributeType.BOOLEAN,
            )
        return attribute

    def lock_product_update(self, field_type, product_obj):
        """
        Lock product update if product is locked for update.
        :param field_type:
        :param product_obj:
        :return:
        """
        attribute = self.get_lock_attribute(field_type)

        if attribute:
            self.lock_field(attribute, product_obj)

    def get_attributes(self, attribute_qs):
        # TODO: Cache the data
        attribute_list = []
        for product_attr in attribute_qs:
            attribute = {
                "attribute_code": "",
                "attribute_name": "",
                "attribute_value": product_attr.value,
                "option_value": "",
            }
            if product_attr.attribute:
                attribute["attribute_code"] = product_attr.attribute.code
                attribute["attribute_name"] = product_attr.attribute.name
            if product_attr.option:
                attribute["option_value"] = product_attr.option.name
            attribute_list.append(attribute)
        return attribute_list

    def get_dimensional_attributes(self, product):
        # TODO: Cache the data
        dimensional_attribute_data_list = []
        dimensional_attributes = self.get_attributes(
            product.product_attribute.filter(
                attribute__code__in=["memory_size", "color"]
            ).select_related("option", "attribute")
        )
        for dimensional_attribute in dimensional_attributes:
            dimentional_attribute_data = {
                "attribute_code": dimensional_attribute.get("attribute_code", ""),
                "attribute_name": dimensional_attribute.get("attribute_name", ""),
                "attribute_value": dimensional_attribute.get("attribute_value", ""),
                "option_value": dimensional_attribute.get("option_value", ""),
            }
            dimensional_attribute_data_list.append(dimentional_attribute_data)
        return dimensional_attribute_data_list

    def get_sales_price(self, product_code, contact_id):
        sales_price = self.get_product_sales_price(
            product_code=product_code, contact_id=contact_id
        )
        return sales_price

    def get_sales_price_ex_vat(self, product_code, price):
        price_ex_vat = self.get_product_sales_price_ex_vat(product_code, price)
        return price_ex_vat

    def get_order_unit(self, product_id, contact_id, user):
        return self.get_order_unit_for_product(
            product_id=product_id, contact_id=contact_id, user=user
        )

    def get_siblings(self, product, catalog=None):
        sibling_data_list = []
        if product.product_series:
            sibling_list = self.get_sibling_products(
                product_code=product.code, catalog=catalog
            )
            for sibling in sibling_list:
                sibling_data = model_to_dict(sibling, fields=PRODUCT_BASIC_INFO_FIELDS)
                sibling_data[
                    "dimensional_attributes"
                ] = self.get_dimensional_attributes(product=sibling)
                sibling_data_list.append(sibling_data)
        return sibling_data_list

    def get_product_image_documents(self, product):
        product_documents = product.documents.filter(
            is_available=True,
            document__mime_type__in=MEDIA_TYPE_IMAGES,
            document__image_type=ImageType.MEDIUM,
        ).select_related("document")
        product_document_list = []
        for pro_document in product_documents:
            product_document_list.append(
                {
                    "sort_order": pro_document.sort_order,
                    "images": pro_document.document.media.url
                    if pro_document.document.media
                    else "",
                    "image_type": pro_document.document.image_type,
                }
            )
        return product_document_list

    def get_product_pdf_documents(self, product):
        product_documents = product.documents.filter(
            is_available=True,
            document__mime_type__in=MEDIA_TYPE_PDFS,
        ).select_related("document")
        product_document_list = []
        for pro_document in product_documents:
            product_document_list.append(
                {
                    "sort_order": pro_document.sort_order,
                    "document": pro_document.document.media.url
                    if pro_document.document.media
                    else "",
                    "document_type": pro_document.document.mime_type,
                    "document_name": pro_document.document.media.name.split("/")[-1],
                }
            )
        return product_document_list

    def get_related_attributes(self, product, catalog=None):
        catalog_code = catalog.code if catalog else "no_catalog"
        cache_key = f"related_attributes_{product.code}_{catalog_code}"
        cached_data = self.cache_service.get(cache_key=cache_key)
        if not cached_data:
            product_attributes = (
                self.product_attribute_service.get_product_related_available_attributes(
                    product_code=product.code, catalog=catalog
                )
            )
            self.cache_service.set(cache_value=product_attributes, cache_key=cache_key)
        else:
            product_attributes = cached_data
        return product_attributes

    def get_catalog(self, catalog_code):
        """
        :param catalog_code:
        :return:
        """
        cache_key = f"selected_{catalog_code}"
        cached_data = self.cache_service.get(cache_key=cache_key)
        if not cached_data:
            users_catalogs = self.get_catalog_service().read_by_code(
                code_value=catalog_code
            )
            self.cache_service.set(cache_value=users_catalogs, cache_key=cache_key)
        else:
            users_catalogs = cached_data
        return users_catalogs

    def get_catalogs_by_product_code(self, code):
        """
        Get catalogs by product code.
        :param code
        :return: list of catalogs
        """
        catalogs = []
        product = self.read_by_code(code)
        if product:
            catalogs = product.catalogproduct_set.all()
        return catalogs

    def prepare_terms_and_conditions_of_product(self, code):
        """
        Get terms and conditions of product.
        :param code
        :return: list of terms and conditions
        """
        terms_and_conditions = []
        catalogs = self.get_catalogs_by_product_code(code)
        if catalogs:
            catalog_codes = [
                data["catalog__code"] for data in catalogs.values("catalog__code")
            ]
            from {{cookiecutter.project_slug}}.terms_and_conditions.services import (
                TermsAndConditionsService,
            )

            terms_and_condition_service = TermsAndConditionsService(
                tenant_code=self.tenant_code, site_profile=self.site_profile
            )
            terms_and_conditions = terms_and_condition_service.model.objects.filter(
                catalog_code__in=catalog_codes
            )
        return [
            {
                "name": terms_and_condition.name,
                "code": terms_and_condition.code,
                "export_id": terms_and_condition.export_id,
            }
            for terms_and_condition in terms_and_conditions
        ]
