import decimal
import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, Q
from django.forms.models import model_to_dict
from django.utils import timezone
from django.utils.functional import cached_property

from {{cookiecutter.project_slug}}.common.bases.services import BaseModelService
from {{cookiecutter.project_slug}}.common.constants import VAT, ZERO
from {{cookiecutter.project_slug}}.common.utils import (
    datetime_string_to_tz_aware_datetime,
    fix_external_decimal_places,
    fix_internal_decimal_places,
)
from {{cookiecutter.project_slug}}.contacts.configs.purchase_gateways import PurchaseGateways
from {{cookiecutter.project_slug}}.products.configs.price_config import ProductItemPriceType
from {{cookiecutter.project_slug}}.rest_utils.exceptions import BadRequestException

from ..configs.price_config import BASE_CURRENCY, PriceType
from ..models import Price, Product, ProductPromotion
from .vat import VatService

logger = logging.getLogger(__name__)


class PriceService(BaseModelService):
    model = Price

    def __init__(
        self, date_to_filter=None, use_cache=True, exchange_rate=None, *args, **kwargs
    ):
        if date_to_filter is None:
            date_to_filter = timezone.now().date()
        super().__init__(*args, **kwargs)
        self.date_to_filter = date_to_filter
        self.use_cache = use_cache
        self.exchange_rate = exchange_rate if exchange_rate else {}
        self.vat_service = VatService(
            tenant_code=self.get_tenant_code(), site_profile=self.site_profile
        )

    def prepare_price_data(self, **data):
        """
        Prepare and validate the price data, ensuring price and price_ex_vat are consistent.
        """
        data.update({"tenant_code": self.get_tenant_code()})

        # If there is a price value but either price_ex_vat is None or not given
        if data.get("price", None) and not data.get("price_ex_vat", None):
            # Then calculate price_ex_vat
            data["price_ex_vat"] = fix_external_decimal_places(
                self.get_price_without_vat(
                    product_code=data["product_code"], price=data["price"]
                )
            )

        # If there is price_ex_vat value but price is None or not given
        elif data.get("price_ex_vat") and not data.get("price", None):
            # Then calculate price
            data["price"] = fix_internal_decimal_places(
                self.get_price_with_vat(
                    product_code=data["product_code"], price=data["price_ex_vat"]
                )
            )

        # price and price_ex_vat both are given
        elif data.get("price") and data.get("price_ex_vat"):
            # Check if the price_ex_vat is correct to 1 cent precision
            actual_price_ex_vat = self.get_price_without_vat(
                product_code=data["product_code"], price=data["price"]
            )
            if round(data.get("price_ex_vat"), 1) != round(actual_price_ex_vat, 1):
                raise BadRequestException(message="Verkeerde prijs exclusief btw")

        return data

    def update_price(self, user=None, **data):
        """
        Update an existing price instance with the given data.
        """
        data = self.prepare_price_data(**data)
        price = self.read_by_code(code_value=data["code"])
        return self.update_model_instance(price, **data)

    def create_price(self, **data):
        """
        Create a new price instance with the given data.
        """
        data = self.prepare_price_data(**data)
        try:
            self.read_by_code(code_value=data["code"])
            raise BadRequestException(message="Price with code already exist.")
        except ObjectDoesNotExist:
            pass
        return self.create_model_instance(self.model, **data)

    @cached_property
    def default_vat_percent(self):
        #  TODO: Take the default value from database.
        return decimal.Decimal("21.00")

    @cached_property
    def all_vat_percent(self):
        all_product_vat_qs = Product.objects.exclude(vat=None).values(
            "id", "vat__percent_value"
        )
        vat_percent_map = {
            product["id"]: product["vat__percent_value"]
            for product in all_product_vat_qs
        }
        return vat_percent_map

    def get_price_without_vat(self, product_code, price):
        """
        Return the price without VAT.

        :param product_code: product_code
        :param price: price including VAT
        :return: price excluding VAT
        """
        # it should use the cached version but this gives circulair imports now
        product = Product.objects.get(tenant_code=self.tenant_code, code=product_code)
        if not product.vat:
            vat_code = self.vat_service.get_default_vat_code()
        else:
            vat_code = product.vat.code
        price_without_vat = self.vat_service.get_price_ex_vat(price, vat_code)
        return price_without_vat

    def get_price_with_vat(self, product_code, price):
        """
        Return the price with VAT.

        :param product_id: product_id
        :param price: price excluding VAT
        :return: price including VAT
        """
        product = Product.objects.get(tenant_code=self.tenant_code, code=product_code)
        if not product.vat:
            vat = self.vat_service.get_or_create_default_vat()
        else:
            vat = product.vat
        price_with_vat = self.vat_service.get_price_incl_vat(price, 0, vat.code)
        return price_with_vat

    @cached_property
    def all_product_price(self):
        all_price_dict = {}
        all_price_qs = self.model.objects.filter(
            product__tenant_code=self.get_tenant_code(),
            valid_from__lte=self.date_to_filter,
            valid_until__gt=self.date_to_filter,
        ).values("product_id", "price_type", "price", "price_ex_vat", "product__code")
        for price_data in all_price_qs:
            # product_id = price_data["product_id"]
            product_code = price_data["product__code"]
            price_type = price_data["price_type"]
            price_type_ex = str(price_data["price_type"]) + "_ex_vat"
            price = price_data["price"]
            price_ex_vat = price_data["price_ex_vat"]
            if product_code in all_price_dict:
                all_price_dict[product_code].update(
                    {price_type: price, price_type_ex: price_ex_vat}
                )
            else:
                all_price_dict.update(
                    {product_code: {price_type: price, price_type_ex: price_ex_vat}}
                )
        return all_price_dict

    def get_all_product_price(self, **kwargs):
        prices = self.model.objects.filter(**kwargs).values(
            "price_type",
            "valid_from",
            "valid_until",
            "currency",
            "price",
            "price_ex_vat",
            product_code=F("product__code"),
        )
        for price in prices:
            price_type = PriceType()
            price["price_type"] = price_type.get_price_type_name_by_value(
                price["price_type"]
            )
        return prices

    @cached_property
    def all_product_fallback_price(self):
        all_price_dict = {}
        all_price_qs = self.model.objects.filter(
            product__tenant_code=self.get_tenant_code(),
            valid_from__lte=self.date_to_filter,
            valid_until__gte=self.date_to_filter,
        ).values("product_id", "price_type", "price", "price_ex_vat", "product__code")
        for price_data in all_price_qs:
            # product_id = price_data["product_id"]
            price_type = price_data["price_type"]
            product_code = price_data["product__code"]
            price_type_ex = str(price_data["price_type"]) + "_ex_vat"
            price = price_data["price"]
            price_ex_vat = price_data["price_ex_vat"]
            if product_code in all_price_dict:
                all_price_dict[product_code].update(
                    {price_type: price, price_type_ex: price_ex_vat}
                )
            else:
                all_price_dict.update(
                    {product_code: {price_type: price, price_type_ex: price_ex_vat}}
                )
        return all_price_dict

    @cached_property
    def all_promotions(self):
        #  TODO: change to self.data_to_filter
        now = timezone.now()
        promotions = {}
        product_promotion_qs = ProductPromotion.objects.filter(
            promotion__start_datetime__lte=now,
            promotion__end_datetime__gte=now,
            promotion__active=True,
        ).values(
            "product_id",
            "promotion__monthly_fee_discount",
            "promotion__monthly_fee_discount_percentage",
            "product__code",
        )
        for product_promotion in product_promotion_qs:
            promotions.update(
                {
                    product_promotion["product_code"]: {
                        "monthly_fee_discount": product_promotion[
                            "promotion__monthly_fee_discount"
                        ],
                        "monthly_fee_discount_percentage": product_promotion[
                            "promotion__monthly_fee_discount_percentage"
                        ],
                    }
                }
            )
        return promotions

    #  This is the non cached version of get_product_price
    def get_product_price_from_db(self, product_code, price_type, vat_code):
        product_price = decimal.Decimal("0.00")

        all_price_qs = self.model.objects.filter(
            product__tenant_code=self.get_tenant_code(),
            valid_from__lte=self.date_to_filter,
            valid_until__gt=self.date_to_filter,
            product__code=product_code,
            price_type=price_type,
        )
        all_fallback_price_qs = self.model.objects.filter(
            product__tenant_code=self.get_tenant_code(),
            valid_from__lte=self.date_to_filter,
            valid_until__gte=self.date_to_filter,
            product__code=product_code,
            price_type=price_type,
        )

        #  In the all_product_price cached_property, last price is considered if there are multiple prices exists
        #  within the same date range. We are keeping same behaviour here.
        if all_price_qs.exists():
            product_price_instance = all_price_qs.last()
            if vat_code:
                product_price = self.vat_service.get_price_incl_vat(
                    product_price_instance.price_ex_vat,
                    product_price_instance.price,
                    vat_code=vat_code,
                )
            else:
                product_price = product_price_instance.price
        elif all_fallback_price_qs.exists():
            product_price_instance = all_fallback_price_qs.last()
            if vat_code:
                product_price = self.vat_service.get_price_incl_vat(
                    product_price_instance.price_ex_vat,
                    product_price_instance.price,
                    vat_code=vat_code,
                )
            else:
                product_price = product_price_instance.price
        else:
            product_price_instance = None

        # Checking if we need to perform currency conversion
        if self.exchange_rate:
            if (
                product_price_instance
                and product_price_instance.currency != BASE_CURRENCY
            ):
                if (
                    self.exchange_rate["currency_from"]
                    == product_price_instance.currency
                    and self.exchange_rate["currency_to"] == BASE_CURRENCY
                ):
                    exchange_rate = self.exchange_rate["rate"]
                    product_price = fix_internal_decimal_places(
                        product_price * exchange_rate
                    )
                else:
                    # TODO: The price is not defined in the base currency and there is no conversion rate define.
                    #  What should we do in that case?
                    pass
        return product_price

    def get_product_price(self, product_code, price_type, vat_code=None):
        if self.use_cache is False and product_code:
            return self.get_product_price_from_db(
                product_code, price_type, vat_code=vat_code
            )
        product_price = decimal.Decimal("0.00")
        product_price_ex_vat = decimal.Decimal("0.00")
        price_type_ex_vat = str(price_type) + "_ex_vat"
        price_found = False
        if product_code in self.all_product_price:
            if price_type in self.all_product_price[product_code]:
                product_price = self.all_product_price[product_code][price_type]
                product_price_ex_vat = self.all_product_price[product_code][
                    price_type_ex_vat
                ]
                price_found = True
        if not price_found:
            if product_code in self.all_product_fallback_price:
                if price_type in self.all_product_fallback_price[product_code]:
                    product_price = self.all_product_fallback_price[product_code][
                        price_type
                    ]
                    product_price_ex_vat = self.all_product_fallback_price[
                        product_code
                    ][price_type_ex_vat]
        # TODO: We should consider currency_exchange_rates here as well but that's related to PH for now and
        #  PH is using price without cache. So, we are skipping currency here for the time being.
        # todo: fix this
        if vat_code:
            price = self.vat_service.get_price_incl_vat(
                product_price_ex_vat, product_price, vat_code
            )
        else:
            price = product_price
        return price

    def get_list_price(self, product_code, excl_vat=False):
        sales_price = self.get_product_price(
            product_code=product_code,
            price_type=PriceType.SALES_PRICE,
        )
        if excl_vat:
            return self.get_price_without_vat(
                product_code=product_code, price=sales_price
            )
        return sales_price

    def get_purchase_price(self, product_code, excl_vat=False):
        purchase_price = self.get_product_price(
            product_code=product_code,
            price_type=PriceType.PURCHASE_PRICE,
        )
        if excl_vat:
            return self.get_price_without_vat(
                product_code=product_code, price=purchase_price
            )
        return purchase_price

    def get_price(self, product_code, excl_vat=False):
        price = self.get_list_price(product_code)
        if excl_vat:
            return self.get_price_without_vat(product_code=product_code, price=price)
        return price

    def get_list_recurring_monthly_fee(self, product_code, excl_vat=False):
        list_recurring_monthly_fee = self.get_product_price(
            product_code=product_code,
            price_type=PriceType.RECURRING_PRICE,
        )
        if excl_vat:
            return self.get_price_without_vat(
                product_code=product_code, price=list_recurring_monthly_fee
            )
        return list_recurring_monthly_fee

    def get_recurring_monthly_fee(self, product_code, excl_vat=False):
        list_recurring_monthly_fee = self.get_list_recurring_monthly_fee(product_code)
        promotion_monthly_fee_discount = decimal.Decimal("0.00")

        if product_code in self.all_promotions:
            promotion_data = self.all_promotions[product_code]
            if promotion_data["monthly_fee_discount"]:
                promotion_monthly_fee_discount = promotion_data["monthly_fee_discount"]
            elif promotion_data["monthly_fee_discount_percentage"]:
                promotion_monthly_fee_discount = list_recurring_monthly_fee * (
                    promotion_data["monthly_fee_discount_percentage"] / 100
                )
        recurring_monthly_fee = (
            list_recurring_monthly_fee - promotion_monthly_fee_discount
        )
        if excl_vat:
            return self.get_price_without_vat(
                product_code=product_code, price=recurring_monthly_fee
            )
        return recurring_monthly_fee

    def get_sac_price(self, product_code):
        sac_price = self.get_product_price(
            product_code=product_code,
            price_type=PriceType.SAC_PRICE,
        )
        return sac_price

    def update_or_create(self, **price_data):
        price_check_fields = ("product", "price_type", "currency")
        filter_options = {
            price_field: price_data[price_field] for price_field in price_check_fields
        }
        price_qs = Price.objects.filter(**filter_options)
        price_qs = price_qs.filter(
            Q(valid_from__lte=price_data["valid_from"]),
            Q(valid_until__gte=price_data["valid_from"])
            | Q(valid_from__lte=price_data["valid_until"]),
            Q(valid_until__gte=price_data["valid_until"]),
        )
        if price_qs.exists():
            # TODO: Need to decide what to do? Update the price value or
            # update the valid_until of the existing record like
            pass
        else:
            self.create(**price_data)

    def get_all_supplier_data(self, product_code):
        from {{cookiecutter.project_slug}}.contacts.services import ContactService

        all_supplier_data_dict = {}
        now = timezone.now()
        # TODO: Implement caching after the logic is finalized.
        price_qs = Price.objects.filter(
            product__tenant_code=self.get_tenant_code(),
            price_type=PriceType.PURCHASE_PRICE,
            product__code=product_code,
            valid_from__lte=now,
            valid_until__gte=now,
        ).exclude(Q(supplier_product_code="") | Q(supplier_uuid=None))
        contact_service = ContactService(
            tenant_code=self.get_tenant_code(), site_profile=self.site_profile
        )
        for price_obj in price_qs:
            supplier_obj = contact_service.read_by_uuid(
                uuid_value=price_obj.supplier_uuid
            )
            supplier_data = model_to_dict(supplier_obj)
            supplier_data["uuid"] = supplier_obj.uuid
            all_supplier_data_dict[supplier_obj.uuid] = supplier_data
        return all_supplier_data_dict

    def get_dropshipment_suppliers(self, product_code):
        all_supplier_data_dict = self.get_all_supplier_data(product_code=product_code)
        items_to_delete = []
        for uuid in all_supplier_data_dict.keys():
            if (
                all_supplier_data_dict[uuid].get("purchase_gateway")
                == PurchaseGateways.NO_GATEWAY
            ):
                items_to_delete.append(uuid)
        for item_to_delete in items_to_delete:
            del all_supplier_data_dict[item_to_delete]
        return all_supplier_data_dict

    def has_dropshipment_supplier(self, product_code):
        all_supplier_data_dict = self.get_dropshipment_suppliers(
            product_code=product_code
        )
        if all_supplier_data_dict:
            return True
        return False

    def get_supplier_price_data(self, product_code, supplier_uuid):
        now = timezone.now()
        # TODO: Implement caching after the logic is finalized.
        price_qs = Price.objects.filter(
            product__tenant_code=self.get_tenant_code(),
            price_type=PriceType.PURCHASE_PRICE,
            product__code=product_code,
            valid_from__lte=now,
            valid_until__gte=now,
            supplier_uuid=supplier_uuid,
        )
        # There shouldn't be more then one price but we are taking the last for safety
        supplier_price = price_qs.last()
        if not supplier_price:
            return {}
        supplier_price_data = model_to_dict(supplier_price)
        supplier_price_data["supplier_uuid"] = supplier_price.supplier_uuid
        return supplier_price_data

    def get_all_supplier_price_data_of_product(self, product_code):
        all_supplier_price_data = []
        all_supplier_data_dict = self.get_all_supplier_data(product_code)
        for uuid, supplier_data_dict in all_supplier_data_dict.items():
            supplier_price_data = self.get_supplier_price_data(product_code, uuid)
            supplier_price_data["supplier_code"] = supplier_data_dict["company_code"]
            all_supplier_price_data.append(supplier_price_data)
        return all_supplier_price_data

    def cleanup_existing_price_data(self, existing_price_qs):
        # Now we are going remove duplicate identical entries. Though it shouldn't be part of this method but
        # for now we need it.
        compact_data_code_set = set()
        invalid_id_list = []

        for existing_price in existing_price_qs.order_by("-id"):
            compact_data_code = "-".join(
                [
                    str(existing_price.price_type),
                    str(existing_price.valid_from),
                    str(existing_price.valid_until),
                    str(existing_price.currency),
                    str(existing_price.price),
                    str(existing_price.supplier_product_code),
                    str(existing_price.supplier_uuid),
                ]
            )
            if compact_data_code not in compact_data_code_set:
                compact_data_code_set.add(compact_data_code)
            else:
                invalid_id_list.append(existing_price.id)

        if invalid_id_list:
            existing_price_qs.filter(id__in=invalid_id_list).delete()
            # we are retrieving all to get data from DB instead of cache
            existing_price_qs = existing_price_qs.all()

        # Now we have to fix the date overlaps
        # First make a data list of dict.
        date_data_dict_list = []
        updated_date_data_dict = {}
        for existing_price in existing_price_qs.order_by("valid_from"):
            date_data_dict_list.append(
                dict(
                    valid_from=existing_price.valid_from,
                    valid_until=existing_price.valid_until,
                    id=existing_price.id,
                )
            )
        data_len = len(date_data_dict_list)
        for index in range(data_len):
            date_data_dict = date_data_dict_list[index]
            # check do we have next items
            if index + 1 < data_len:
                valid_valid_until = date_data_dict_list[index + 1]["valid_from"]
                if (
                    date_data_dict["valid_from"] <= valid_valid_until
                    and date_data_dict["valid_until"] != valid_valid_until
                ):
                    # The valid to is not valid. So, we have to update it.
                    date_data_dict["valid_until"] = valid_valid_until
                    updated_date_data_dict[date_data_dict["id"]] = dict(
                        valid_until=valid_valid_until
                    )
        if updated_date_data_dict:
            # there are wrong data. So, that needs to be corrected in DB.
            bulk_update_object_list = []
            bulk_update_fields = ["valid_until"]
            for existing_price in existing_price_qs.order_by("valid_from"):
                if updated_date_data_dict.get(existing_price.id) and isinstance(
                    updated_date_data_dict.get(existing_price.id), dict
                ):
                    for key, val in updated_date_data_dict[existing_price.id].items():
                        setattr(existing_price, key, val)
                    bulk_update_object_list.append(existing_price)
            Price.objects.bulk_update(
                objs=bulk_update_object_list, fields=bulk_update_fields, batch_size=100
            )

    def create_prices_with_manual_validity(
        self, price_data_list, start_date, user=None
    ):
        """
        Import price to the price table from pre imported price data
        If the price exists, and value hasn't changed then leave it, Else create a new price
        :param start_date:
        :param price_data_list:
        :param user: user who's creating the price
        :return:
        """
        tz_aware_start_datetime = datetime_string_to_tz_aware_datetime(
            datetime_str=start_date.strftime("%Y-%m-%dT%H:%M:%S")
        )
        yesterday = tz_aware_start_datetime - timezone.timedelta(days=1)
        for price_data in price_data_list:
            # recalculate price with vat of the product
            product = price_data["product"]
            price_with_vat = self.get_price_with_vat(
                product_code=product.code, price=price_data["price_ex_vat"]
            )

            # check import price is equal to (1 decimal place) price_with_vat
            # if yes then keep import price otherwise keep vat calculated price
            if round(price_data.get("price"), 1) != round(price_with_vat, 1):
                price_data["price"] = price_with_vat

            if price_data["price_type"] == PriceType.PURCHASE_PRICE and price_data.get(
                "supplier_uuid"
            ):
                price_obj = (
                    self.model.objects.filter(
                        product_id=price_data["product"].id,
                        price_type=price_data["price_type"],
                        supplier_uuid=price_data.get("supplier_uuid"),
                    )
                    .order_by("created_at")
                    .last()
                )
            else:
                price_obj = (
                    self.model.objects.filter(
                        product_id=price_data["product"].id,
                        price_type=price_data["price_type"],
                    )
                    .order_by("created_at")
                    .last()
                )
            # If there is a previous price
            if price_obj:
                # if price has changed
                if fix_internal_decimal_places(
                    price_obj.price
                ) != fix_internal_decimal_places(
                    price_data["price"]
                ) or fix_internal_decimal_places(
                    price_obj.price_ex_vat
                ) != fix_internal_decimal_places(
                    price_data["price_ex_vat"]
                ):
                    # then end the validity
                    price_obj.valid_until = yesterday
                    price_obj.updated_by = user
                    price_obj.save()

                    # Create a new price
                    price_data["valid_from"] = tz_aware_start_datetime
                    Price.objects.create(**price_data)

                # here, we're adding supplier uuid and supplier product code to the existing purchase_price,
                # which does not have the supplier_uuid.
                if (
                    price_obj.price_type == PriceType.PURCHASE_PRICE
                    and not price_obj.supplier_uuid
                ):
                    price_obj.supplier_uuid = price_data.get("supplier_uuid", "")
                    price_obj.supplier_product_code = price_data.get(
                        "supplier_product_code"
                    )
                    price_obj.save()

            else:
                # There is no previous price, we need to create
                price_data["created_by"] = user
                Price.objects.create(**price_data)

    def get_sales_price_for_contact(self, product_code, contact_id, vat_code=None):
        """
        :param product_code:
        :param contact_id:
        :return:
        """
        from {{cookiecutter.project_slug}}.price_calculation.services import CartPriceCalculationService

        return CartPriceCalculationService(
            tenant_code=self.get_tenant_code(), site_profile=self.site_profile
        ).get_product_price(
            product_code, PriceType.SALES_PRICE, contact_id, vat_code=vat_code
        )

    def get_latest_price_by_product(
        self, product_code, price_type, vat_code=None
    ) -> decimal.Decimal:
        """
        filter first product price based on product code and price type
        return the product price or 0
        """
        price_dict = (
            Price.objects.filter(
                product__tenant_code=self.get_tenant_code(),
                product__code=product_code,
                price_type=price_type,
                valid_from__lte=timezone.now(),
                valid_until__gte=timezone.now(),
            )
            .values("price", "price_ex_vat")
            .first()
        )
        if vat_code and price_dict:
            price = self.vat_service.get_price_incl_vat(
                price_dict["price_ex_vat"], price_dict["price"], vat_code
            )
        else:
            price = price_dict["price"] if price_dict else decimal.Decimal("0.00")
        return price

    def get_latest_price_ex_vat(self, product_code, price_type):
        """
        filter first product price based on product code and price type
        return the product price or 0
        """
        price_obj = Price.objects.filter(
            product__tenant_code=self.tenant_code,
            product__code=product_code,
            price_type=price_type,
            valid_from__lte=timezone.now(),
            valid_until__gte=timezone.now(),
        ).first()
        return price_obj.price_ex_vat if price_obj else ZERO

    def save_product_price(self, product, prices, supplier_uuid="", **kwargs):
        """
        :param product: product object
        :param prices: price data dict
        :param supplier_uuid: supplier_uuid
        :return:
        "prices": [
                {
                    "quantity": 1,
                    "price_type": "purchase_price",
                    "price_ex_vat": "436.570000",
                    "updated_at": "2023-01-02T08:35:42.430030+01:00",
                    "supplier": {"code": "8714253023106", "name": "Ingram Micro BV", "company_code": "company_code"},
                },
                {
                    "quantity": 1,
                    "price_type": "sales_price",
                    "price_ex_vat": "501.000000",
                    "updated_at": "2022-12-31T23:38:03.279204+01:00",
                    "supplier": {
                                    "code": "8714253023205", "name":
                                    "Tech Data Nederland B.V.",
                                    "company_code": "company_code"
                                },
                },
            ]
        """
        prices_to_import_in_price_table = []
        tenant_code = self.tenant_code
        site_profile = self.site_profile
        from {{cookiecutter.project_slug}}.contacts.services import ContactService

        contact_service = ContactService(
            tenant_code=tenant_code, site_profile=site_profile
        )
        price_type_dict = {
            ProductItemPriceType.PURCHASE_PRICE: PriceType.PURCHASE_PRICE,
            ProductItemPriceType.SALES_PRICE: PriceType.SALES_PRICE,
        }

        for price in prices:
            price["tenant_code"] = tenant_code
            if isinstance(price.get("supplier"), dict):
                _supplier = price.get("supplier")

                # from onetrail we receive code as export_id, so we are searching here in both ways
                supplier_contact = contact_service.get_contact(
                    tenant_code=tenant_code,
                    export_id=_supplier.get("code"),
                    is_supplier=True,
                )
                if not supplier_contact:
                    supplier_contact = contact_service.get_contact(
                        tenant_code=tenant_code,
                        company_code=_supplier.get("company_code"),
                        is_supplier=True,
                    )
                if not supplier_contact:
                    supplier_contact = contact_service.create_contact(
                        **{
                            "tenant_code": tenant_code,
                            "contact_name": _supplier.get("name"),
                            "company_code": _supplier.get("company_code", ""),
                            "export_id": _supplier.get("code", ""),
                            "is_supplier": True,
                        }
                    )
                supplier_uuid = supplier_contact.uuid
                # remove unnecessary key from dict
                for key in ["quantity", "supplier"]:
                    if key in price:
                        del price[key]

            if price["price_type"] in [
                ProductItemPriceType.SALES_PRICE,
                ProductItemPriceType.PURCHASE_PRICE,
            ]:
                price["product"] = product

            if price["price_type"] == ProductItemPriceType.PURCHASE_PRICE:
                price["supplier_uuid"] = supplier_uuid
                price["supplier_product_code"] = (
                    kwargs.get("seller_product_code") or product.code
                )

            price["price_type"] = price_type_dict.get(price["price_type"])

            try:
                price["price_ex_vat"] = decimal.Decimal(price.get("price_ex_vat", ZERO))

                if not price.get("price", None):
                    price["price"] = fix_internal_decimal_places(
                        price["price_ex_vat"] * VAT
                    )
            except Exception as ex:
                logger.error(f"Error calculating product prices: {ex}")
                price["price"] = ZERO

            prices_to_import_in_price_table.append(price)

        # if there is not sales price, make it 0 for now
        # TODO: we need to take decision on this, Otherwise quote line price will be zero
        if not any(
            price.get("price_type")
            == price_type_dict.get(ProductItemPriceType.SALES_PRICE)
            for price in prices_to_import_in_price_table
        ):
            prices_to_import_in_price_table.append(
                {
                    "tenant_code": tenant_code,
                    "price_type": price_type_dict.get(ProductItemPriceType.SALES_PRICE),
                    "product": product,
                    "price_ex_vat": ZERO,
                    "price": ZERO,
                }
            )

        # if there not purchase price, we are creating a purchase price 0 with the default supplier
        if not any(
            price.get("price_type")
            == price_type_dict.get(ProductItemPriceType.PURCHASE_PRICE)
            for price in prices_to_import_in_price_table
        ):
            prices_to_import_in_price_table.append(
                {
                    "tenant_code": tenant_code,
                    "price_type": price_type_dict.get(
                        ProductItemPriceType.PURCHASE_PRICE
                    ),
                    "product": product,
                    "price_ex_vat": ZERO,
                    "price": ZERO,
                    "supplier_uuid": supplier_uuid,
                }
            )

        if prices_to_import_in_price_table:
            try:
                self.create_prices_with_manual_validity(
                    price_data_list=prices_to_import_in_price_table,
                    start_date=timezone.now().date(),
                )
            except Exception as e:
                logger.error(f"Error saving product prices: {e}")
