from django.core.cache import caches
from django.db.models import Q

from {{cookiecutter.project_slug}}.common.bases.services import BaseModelService
from {{cookiecutter.project_slug}}.products.configs.product_config import ProductItemType
from {{cookiecutter.project_slug}}.products.models import Product


class BaseProductService(BaseModelService):
    def get_first_channel_for_user(self, user):
        from {{cookiecutter.project_slug}}.users.services.user_service import UserService

        """
        support item: get the first channel codes for the user
        :param user:
        :return: string, channel_code or ""
        """
        return UserService(
            tenant_code=self.tenant_code, site_profile=self.site_profile
        ).get_first_channel_code_by_user(user=user)

    def get_available_add_ons(self, flow_type="", market_type="", channel=""):
        add_on_data = {}
        cache = caches["default"]
        cache_key = "available_add_ons_" + flow_type + market_type + channel
        cached_response = cache.get(cache_key)
        if cached_response:
            return cached_response

        add_on_qs = Product.objects.filter(
            product_type__system_type=ProductItemType.ADD_ON,
            is_available=True,
            campaign_code="",
        )
        if market_type:
            add_on_qs = add_on_qs.filter(
                Q(productmarkettype__market_type=market_type)
                | Q(productmarkettype__isnull=True)
            )
        else:
            add_on_qs = add_on_qs.filter(productmarkettype__isnull=True)
        if flow_type:
            add_on_qs = add_on_qs.filter(
                Q(productflowtype__flow_type=flow_type)
                | Q(productflowtype__isnull=True)
            )
        else:
            add_on_qs = add_on_qs.filter(productflowtype__isnull=True)
        if channel:
            add_on_qs = add_on_qs.filter(
                Q(productchannel__channel=channel)
                | Q(productchannel__channel__isnull=True)
            )
        else:
            add_on_qs = add_on_qs.filter(productchannel__channel__isnull=True)
        add_on_qs = add_on_qs.values(
            "id",
            "code",
            "name",
            "product_type__name",
            "product_type__code",
            "required_connection_type",
            "alternative_groups__code",
            "alternative_groups__max_product",
        )
        # todo: fetch the alternative groups, take the first one, put this group in the response
        for add_on in add_on_qs:
            add_on_data.update(
                {
                    add_on["id"]: {
                        "code": add_on["code"],
                        "name": add_on["name"],
                        "product_type_name": add_on["product_type__name"],
                        "product_type_code": add_on["product_type__code"],
                        "required_connection_type": [add_on["required_connection_type"]]
                        if add_on["required_connection_type"]
                        else [],
                        "alternative_groups_code": add_on["alternative_groups__code"],
                        "alternative_groups_max_product": add_on[
                            "alternative_groups__max_product"
                        ],
                    }
                }
            )
        cache.set(cache_key, add_on_data, 60 * 15)
        return add_on_data
