from django.utils.translation import gettext_lazy as _

from {{cookiecutter.project_slug}}.common.utils import add_choices
from {{cookiecutter.project_slug}}.products.configs.price_config import PriceType
from {{cookiecutter.project_slug}}.products.configs.product_config import ProductItemType


@add_choices
class CommonRelationType:
    SUBSCRIPTION = "subscription"
    ADD_ON = "add_on"
    RELATED = "related"
    INSURANCE = "insurance"
    SERVICE = "service"
    WARRANTY = "warranty"
    DISCOUNT = "discount"


MANDATORY_RELATED_PRODUCT_RELATION_TYPES = [
    CommonRelationType.ADD_ON,
    CommonRelationType.SERVICE,
    CommonRelationType.WARRANTY,
]
