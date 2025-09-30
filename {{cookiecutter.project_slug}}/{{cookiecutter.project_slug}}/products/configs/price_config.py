import pycountry
from django.utils.translation import gettext_lazy as _
from {{cookiecutter.project_slug}}.common.utils import add_choices


@add_choices
class PriceType:
    SALES_PRICE = "sales_price"
    BASE_PRICE = "base_price"
    RECURRING_PRICE = "recurring_price"
    CONNECTION_PRICE = "connection_price"
    PURCHASE_PRICE = "purchase_price"
    USAGES_PRICE = "usages_price"

    def price_type_name_convert(self, name):
        return name.lower().replace(" ", "_")

    def get_price_type_name_by_value(self, value):
        for choice in self.CHOICES:
            if choice[0] == value:
                return choice[1]
        return ""


class Currency:
    CHOICES = [
        (currency.alpha_3, currency.name) for currency in list(pycountry.currencies)
    ]


# TODO: Find the right place to define it. May be in the settings.
BASE_CURRENCY = "EUR"


@add_choices
class ProductItemPriceType:
    PURCHASE_PRICE = 'purchase_price'
    SALES_PRICE = 'sales_price'
    DEALER_PRICE = 'dealer_price'
    BASE_PRICE = 'base_price'
