from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import ValidationError

from {{cookiecutter.project_slug}}.attributes.constants import AttributeType
from {{cookiecutter.project_slug}}.attributes.models.attribute import Attribute, AttributeGroup

from ..models import ProductAttribute

MOBILE_NUMBER_TYPE_DICT = {"06": "VOICE", "097": "DATA"}


def create_attribute_type(tenant_code, attribute_group, key, value, name=""):
    """
    NONE = 0
    TEXT = 1
    INTEGER = 2
    BOOLEAN = 3
    FLOAT = 4
    RICH_TEXT = 5
    DATE = 6
    IMAGE = 7
    """
    attribute_dict = dict(
        tenant_code=tenant_code,
        attribute_group=attribute_group,
        code=key,
        name=name if name != "" else key,
    )

    if isinstance(value, bool) and isinstance(value, int):
        attribute_dict.update(attribute_type=AttributeType.BOOLEAN)

    if isinstance(value, str) and ("image" not in key):
        attribute_dict.update(attribute_type=AttributeType.TEXT)

    if value is None:
        attribute_dict.update(attribute_type=AttributeType.NONE)

    if isinstance(value, dict):
        attribute_dict.update(attribute_type=AttributeType.RICH_TEXT)

    if isinstance(value, int) and not isinstance(value, bool):
        attribute_dict.update(attribute_type=AttributeType.INTEGER)

    if "image" in key:
        attribute_dict.update(attribute_type=AttributeType.IMAGE)

    attribute_type = attribute_dict.get("attribute_type")
    if not attribute_type and attribute_type is not AttributeType.NONE:
        raise ValidationError({f"{key}": "Unable to find data type for this attribute"})

    return Attribute.objects.get_or_create(
        code=attribute_dict["code"], tenant_code=tenant_code, defaults=attribute_dict
    )


def create_product_attribute(
    tenant_code, product_id, attribute_id, attribute_type, attribute_value
):
    try:
        product_attribute = ProductAttribute.objects.get(
            tenant_code=tenant_code, attribute_id=attribute_id, product_id=product_id
        )
    except ObjectDoesNotExist:
        product_attribute = ProductAttribute.objects.create(
            tenant_code=tenant_code, attribute_id=attribute_id, product_id=product_id
        )

    setattr(
        product_attribute,
        AttributeType.VALUE_MAP.get(attribute_type),
        attribute_value,
    )
    product_attribute.save()


def create_attribute(tenant_code, product_id, attribute_group, key, value, name=""):
    attribute = create_attribute_type(
        tenant_code=tenant_code,
        attribute_group=attribute_group,
        key=key,
        value=value,
        name=name,
    )
    if attribute[0].attribute_type:
        create_product_attribute(
            tenant_code=tenant_code,
            product_id=product_id,
            attribute_id=attribute[0].id,
            attribute_type=attribute[0].attribute_type,
            attribute_value=value,
        )


def set_attribute(tenant_code, product_id, attribute, attribute_name):
    if attribute and isinstance(attribute, dict):
        attribute_group = AttributeGroup.objects.get_or_create(name=attribute_name)

        for key, value in attribute.items():
            create_attribute(
                tenant_code=tenant_code,
                product_id=product_id,
                attribute_group=attribute_group[0],
                key=key,
                value=value,
            )


def build_extension_attribute(tenant_code, product_id, attribute_data):
    extension = attribute_data.get("extension")
    set_attribute(
        tenant_code=tenant_code,
        product_id=product_id,
        attribute=extension,
        attribute_name="extension",
    )


def build_ui_presentation_attribute(tenant_code, product_id, attribute_data):
    ui_presentation_attribute = attribute_data.get("ui_presentation")
    set_attribute(
        tenant_code=tenant_code,
        product_id=product_id,
        attribute=ui_presentation_attribute,
        attribute_name="ui_presentation_attribute",
    )


def build_attributes(tenant_code, product_id, attribute_dict):
    """
    {
        "extension": {
            "attr_name": attr_value
        },
        "ui_presentation_attribute": {
            "attr_name": attr_value
        },
        "attr_group_name": {
            "attr_name": "attr_value"
        }
        ....
    }
    """

    for key in attribute_dict.keys():
        if key == "extension":
            build_extension_attribute(
                tenant_code=tenant_code,
                product_id=product_id,
                attribute_data=attribute_dict,
            )
        if key == "ui_presentation_attribute":
            build_ui_presentation_attribute(
                tenant_code=tenant_code,
                product_id=product_id,
                attribute_data=attribute_dict,
            )
        else:
            set_attribute(
                tenant_code=tenant_code,
                product_id=product_id,
                attribute=attribute_dict[key],
                attribute_name=key,
            )


def set_attribute_new(tenant_code, product_id, attribute):
    child_attributes = attribute.pop("attributes")

    attribute_group, _ = AttributeGroup.objects.get_or_create(
        tenant_code=tenant_code,
        code=attribute.get("code"),
        defaults={"name": attribute.get("name", "")},
    )

    for data in child_attributes:
        create_attribute(
            tenant_code=tenant_code,
            product_id=product_id,
            attribute_group=attribute_group,
            key=data.get("code"),
            value=data.get("value"),
            name=data.get("name"),
        )


def build_attributes_new(tenant_code, product_id, attributes):
    """
    "attributes": [
        {
            "code": "extendedspecifications",
            "name": "Extendedspecifications",
            "attributes": [
                {
                    "code": "H0000010T0002088B0001976",
                    "name": "Service & Support",
                    "value": "Beperkte garantie - onderdelen en werkuren - 1 jaar"
                },
                {
                    "code": "H0000232T0006000B3302301",
                    "name": "Aansluiting (tweede uiteinde)",
                    "value": "Apple Lightning - male"
                }
                ...
            ]
        }
        ...
    ]
    """

    for attribute in attributes:
        set_attribute_new(
            tenant_code=tenant_code, product_id=product_id, attribute=attribute
        )
