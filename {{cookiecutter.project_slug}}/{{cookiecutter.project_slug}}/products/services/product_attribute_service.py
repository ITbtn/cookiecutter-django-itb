from django.core.cache import caches
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict

from {{cookiecutter.project_slug}}.attributes.constants import AttributeType
from {{cookiecutter.project_slug}}.attributes.models.attribute import Attribute
from {{cookiecutter.project_slug}}.attributes.services.attribute import AttributeService
from {{cookiecutter.project_slug}}.attributes.services.options import OptionService
from {{cookiecutter.project_slug}}.common.bases import BaseModelService
from {{cookiecutter.project_slug}}.common.utils import get_object_or_none
from {{cookiecutter.project_slug}}.products.utils.attribute import MOBILE_NUMBER_TYPE_DICT
from {{cookiecutter.project_slug}}.rest_utils.exceptions import BadRequestException

from ..configs.attribute import (
    ACCOUNT_TYPE_CODE,
    CAN_APPLY_DISCOUNT,
    NO_TKH_ATTRIBUTE_CODE,
    PRODUCT_GROUP_LOCK_ATTRIBUTE_CODE,
    SAP_TKH_ATTRIBUTE_CODE,
)
from ..models import ProductAttribute


class ProductAttributeService(BaseModelService):
    model = ProductAttribute

    def __init__(self, *args, **kwargs):
        super(ProductAttributeService, self).__init__(*args, **kwargs)

    def get_mobile_number_type(self, mobile_number):
        if mobile_number:
            if "097" in mobile_number[:3]:
                return "097"
            return "06"
        return mobile_number

    def get_mobile_number_type_name(self, mobile_number_type):
        return MOBILE_NUMBER_TYPE_DICT.get(mobile_number_type, "")

    def get_specific_attribute(self, product_code, attribute_code):
        cache = caches["default"]
        cache_key = "attr-code-{}-{}".format(product_code, attribute_code)
        cached_response = cache.get(cache_key)
        if cached_response:
            return cached_response
        result = ProductAttribute.objects.filter(
            product__code=product_code, attribute__code=attribute_code
        ).values(
            "value_text",
            "value_integer",
            "value_boolean",
            "value_float",
            "value_richtext",
            "value_date",
            "value_image",
        )
        cache.set(cache_key, result, 60 * 60)
        return result

    def set_specific_attribute(self, product_code, attribute_code, value, value_field):
        product_attribute_qs = ProductAttribute.objects.filter(
            product__code=product_code, attribute__code=attribute_code
        )
        if product_attribute_qs:
            product_attribute = product_attribute_qs.first()
            setattr(product_attribute, value_field, value)
            product_attribute.save()
            return True
        return False

    def get_specific_attribute_by_name(self, product_code, attribute_name):
        cache = caches["default"]
        cache_key = "attr-name-{}-{}".format(product_code, attribute_name)
        cached_response = cache.get(cache_key)
        if cached_response:
            return cached_response

        result = ProductAttribute.objects.filter(
            product__code=product_code, attribute__name=attribute_name
        ).values(
            "value_text",
            "value_integer",
            "value_boolean",
            "value_float",
            "value_richtext",
            "value_date",
            "value_image",
        )
        cache.set(cache_key, result, 60 * 60)
        return result

    def get_product_related_available_attributes(self, product_code, catalog=None):
        from {{cookiecutter.project_slug}}.products.services.product_service import ProductService

        product_service = ProductService(
            tenant_code=self.get_tenant_code(), site_profile=self.site_profile
        )
        product_attributes = []
        attribute_values_set = set()
        sibling_products = product_service.get_sibling_products(
            product_code=product_code, catalog=catalog
        )
        product_instance = product_service.get_product(code=product_code)
        sibling_products.append(product_instance)
        product_attributes_qs = []
        for product in sibling_products:
            product_attr = product.product_attribute.filter(
                is_available=True,
                attribute__is_available=True,
                tenant_code=self.get_tenant_code(),
                attribute__code__in=["color", "memory_size"],
            ).select_related("attribute", "option")
            product_attributes_qs.extend(product_attr)

        for product_attribute_obj in product_attributes_qs:
            # attribute_name = None
            attribute_code = None
            attribute_value = product_attribute_obj.value
            color_code = ""

            if product_attribute_obj.attribute:
                attribute_obj = product_attribute_obj.attribute
                # attribute_name = attribute_obj.name
                attribute_code = attribute_obj.code

            if product_attribute_obj.option:
                option_obj = product_attribute_obj.option
                attribute_value = option_obj.name
                color_code = option_obj.color_code

            if attribute_value in attribute_values_set:
                continue
            else:
                attribute_values_set.add(attribute_value)
            key = None
            for product_attribute in product_attributes:
                if product_attribute["attribute_code"] == attribute_code:
                    key = product_attributes.index(product_attribute)
                    break

            attribute_values = {
                "attribute_value": attribute_value,
                "color_code": color_code,
            }

            if key is not None:
                product_attributes[key]["attribute_values"].append(attribute_values)
            else:
                product_attributes.append(
                    {
                        "attribute_code": attribute_code,
                        "attribute_values": [attribute_values],
                    }
                )

        return product_attributes

    def get_product_attributes(self, product_code):
        cache_key = f"product_attributes_{product_code}"
        cached_data = self.cache_service.get(cache_key)
        product_attributes = []
        if not cached_data:
            product_attributes_qs = ProductAttribute.objects.filter(
                product__code=product_code,
                is_available=True,
                attribute__is_available=True,
                tenant_code=self.get_tenant_code(),
                attribute__attribute_group__is_visible=True,
            )

            for product_attribute_obj in product_attributes_qs:
                attribute_group = None
                attribute_group_code = None
                suppress_attribute_name = False
                attribute_name = None
                attribute_code = None
                attribute_value = product_attribute_obj.value
                if (
                    hasattr(product_attribute_obj, "attribute")
                    and product_attribute_obj.attribute
                ):
                    attribute_obj = product_attribute_obj.attribute
                    attribute_name = attribute_obj.name
                    attribute_code = attribute_obj.code

                    if (
                        hasattr(attribute_obj, "attribute_group")
                        and attribute_obj.attribute_group
                    ):
                        attribute_group_obj = attribute_obj.attribute_group
                        attribute_group = attribute_group_obj.name
                        attribute_group_code = attribute_group_obj.code
                        suppress_attribute_name = (
                            attribute_group_obj.is_suppress_attribute_name
                        )

                if attribute_code in [
                    "color",
                    "memory_size",
                    "contract_duration",
                    "voice_sms",
                ]:
                    if (
                        hasattr(product_attribute_obj, "option")
                        and product_attribute_obj.option
                    ):
                        option_obj = product_attribute_obj.option
                        attribute_value = option_obj.name

                key = None
                for product_attribute in product_attributes:
                    if product_attribute["group"] == attribute_group:
                        key = product_attributes.index(product_attribute)
                        break

                attribute = {
                    "attribute_code": attribute_code,
                    "attribute_name": attribute_name,
                    "attribute_value": attribute_value,
                }

                if suppress_attribute_name:
                    attribute.pop("attribute_name")

                if key is not None:
                    product_attributes[key]["attributes"].append(attribute)
                else:
                    product_attributes.append(
                        {
                            "group": attribute_group,
                            "group_code": attribute_group_code,
                            "attributes": [attribute],
                        }
                    )
            self.cache_service.set(product_attributes, cache_key)
        else:
            product_attributes = cached_data
        return product_attributes

    def get_product_attribute_details(self, product_code):
        product_attributes = []
        product_attributes_qs = ProductAttribute.objects.filter(
            product__code=product_code,
            is_available=True,
            attribute__is_available=True,
        ).select_related(
            "product", "attribute__attribute_group", "option__option_group"
        )

        for product_attribute_obj in product_attributes_qs:
            # attribute_group = None
            attribute_name = None
            attribute_code = None
            option_dict = {}
            attribute_value = product_attribute_obj.value

            if (
                hasattr(product_attribute_obj, "attribute")
                and product_attribute_obj.attribute
            ):
                attribute_obj = product_attribute_obj.attribute
                attribute_name = attribute_obj.name
                attribute_code = attribute_obj.code

            if attribute_code in [
                "color",
                "memory_size",
                "contract_duration",
                "voice_sms",
            ]:
                if (
                    hasattr(product_attribute_obj, "option")
                    and product_attribute_obj.option
                ):
                    option_obj = product_attribute_obj.option
                    if option_obj.name:
                        attribute_value = option_obj.name
                    option_dict = model_to_dict(
                        option_obj, fields=["name", "code", "color_code"]
                    )

            attribute = {
                "attribute_name": attribute_name,
                "attribute_value": str(attribute_value),
                "attribute_code": attribute_code,
                "option": option_dict,
            }
            product_attributes.append(attribute)

        return product_attributes

    def get_value_field_combination(self, value):
        """
        Currently we are saving only two types of values:
        1. value_text,
        2. value_integer
        So this method is implemented to support only these two value_[] fields

        :param value:
        :return:

        TODO: enrich to support all value_[] fields
        """
        if type(value) is int:
            return {AttributeType.VALUE_MAP[AttributeType.INTEGER]: value}
        elif type(value) is str:
            return {AttributeType.VALUE_MAP[AttributeType.TEXT]: value}
        else:
            return {AttributeType.VALUE_MAP[AttributeType.RICH_TEXT]: value}

    def get_no_tkh_product_attribute_value(self, product_code):
        no_tkh_product_attribute_value = False
        product_attributes = self.get_specific_attribute(
            product_code=product_code, attribute_code=NO_TKH_ATTRIBUTE_CODE
        )

        if product_attributes:
            product_attribute = product_attributes[0]

            if product_attribute and product_attribute["value_boolean"] is True:
                no_tkh_product_attribute_value = True

        return no_tkh_product_attribute_value

    def get_sap_tkh_product_attribute_value(self, product_code):
        sap_tkh_product_attribute_value = 0
        product_attributes = self.get_specific_attribute(
            product_code=product_code, attribute_code=SAP_TKH_ATTRIBUTE_CODE
        )

        if product_attributes:
            product_attribute = product_attributes[0]

            if product_attribute:
                sap_tkh_product_attribute_value = product_attribute["value_integer"]

        return sap_tkh_product_attribute_value

    def get_can_apply_discount_attribute_value(self, product_code):
        can_apply_discount = False
        product_attributes = self.get_specific_attribute(
            product_code=product_code, attribute_code=CAN_APPLY_DISCOUNT
        )

        if product_attributes:
            product_attribute = product_attributes[0]

            if product_attribute and product_attribute["value_boolean"] is True:
                can_apply_discount = True

        return can_apply_discount

    def get_product_attributes_by_product(self, product):
        product_attributes_qs = self.list(
            product=product, tenant_code=self.get_tenant_code()
        )
        return product_attributes_qs

    def create_product_attribute(self, user, **data_dict):
        available_options = []
        data_dict["created_by"] = user
        if data_dict.get("attribute"):
            data_dict["attribute"] = AttributeService(
                tenant_code=self.tenant_code, site_profile=self.site_profile
            ).get_attribute_by_code(data_dict["attribute"])
        if data_dict.get("option"):
            data_dict["option"] = OptionService(
                tenant_code=self.tenant_code, site_profile=self.site_profile
            ).get_option_by_code(data_dict["option"])
        if data_dict.get("available_options") is not None:
            available_options = data_dict.pop("available_options")
        data_dict.update({"tenant_code": self.get_tenant_code()})

        product_attribute_qs = get_object_or_none(
            ProductAttribute,
            product=data_dict.get("product"),
            attribute=data_dict.get("attribute"),
        )
        if product_attribute_qs:
            raise BadRequestException("Attribute with this Product already exist.")

        product_attribute_instance = ProductAttribute(**data_dict)
        product_attribute_instance.save()
        if available_options:
            for available_option in available_options:
                product_attribute_instance.available_options.add(
                    OptionService(
                        tenant_code=self.tenant_code, site_profile=self.site_profile
                    ).get_option_by_code(available_option)
                )
        return product_attribute_instance

    def get_product_attribute_by_attribute_code(self, attribute_code, **kwargs):
        try:
            return self.read_by_code(code_value=attribute_code, **kwargs)
        except ObjectDoesNotExist:
            raise BadRequestException(
                f"Invalid product attribute code {attribute_code}."
            )

    def is_product_group_update_locked(self, product_obj):
        """
        If product attribute is there for PRODUCT_GROUP_LOCK_ATTRIBUTE_CODE and boolean value is true
        then product group is not allowed to update
        """
        product_group_update_locked = False
        product_attributes = self.get_product_attributes_by_product(product=product_obj)
        product_group_lock_attributes = product_attributes.filter(
            attribute__code=PRODUCT_GROUP_LOCK_ATTRIBUTE_CODE
        )
        if (
            product_group_lock_attributes.last()
            and product_group_lock_attributes.last().value_boolean
        ):
            product_group_update_locked = True

        return product_group_update_locked

    def get_unused_attributes(self, product, attribute_codes):
        """Get unused/available product attributes

        Args:
            product (Product): Product instance of attributes
            attribute_codes (list): list of attribute codes for checking used or not

        Returns:
            Attributes: List of unused/available attributes
        """
        existing_attributes = self.get_product_attributes_by_product(product=product)
        existing_attribute_codes = existing_attributes.values_list(
            "attribute__code", flat=True
        )
        unused_attribute_codes = list(
            set(attribute_codes) - set(existing_attribute_codes)
        )
        unused_attributes = Attribute.objects.filter(code__in=unused_attribute_codes)
        return unused_attributes

    def get_account_type_required(self, product_code):
        """
        For IOT shop, we need account type information. The configuration is store in product attribute section
        """
        account_type_required = False
        product_attributes = self.get_specific_attribute(
            product_code=product_code, attribute_code=ACCOUNT_TYPE_CODE
        )
        if product_attributes.exists():
            product_attribute = product_attributes.first()
            if product_attribute.get("value_boolean"):
                account_type_required = True

        return account_type_required

    def get_create_update_product_attribute(
        self, product, attribute_code, **field_data
    ):
        attribute = AttributeService(
            tenant_code=self.tenant_code, site_profile=self.site_profile
        ).read_by_code(code_value=attribute_code, tenant_code=self.tenant_code)
        try:
            product_attribute_obj = self.model.objects.get(
                product__code=product.code,
                attribute__code=attribute_code,
                tenant_code=self.tenant_code,
            )
        except ObjectDoesNotExist:
            data = {
                "product": product,
                "attribute": attribute,
                "is_available": True,
            }
            data.update(field_data)
            self.create(**data)
        else:
            self.update_model_instance(instance=product_attribute_obj, **field_data)
