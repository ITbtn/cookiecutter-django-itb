from {{cookiecutter.project_slug}}.common.bases import services
from {{cookiecutter.project_slug}}.products.models import (
    ProductChannel,
    ProductFlowType,
    ProductMarketType
)
from {{cookiecutter.project_slug}}.sales_context.services import (
    ChannelServices,
    FlowTypeServices,
    MarketTypeServices
)


class ProductChannelService(services.BaseModelService):
    model = ProductChannel

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel_service = ChannelServices(tenant_code=self.tenant_code, site_profile=self.site_profile)

    def get_channel_id_list(self, product_channels):
        return [p_channel.channel for p_channel in product_channels]

    def get_channels(self, product):
        query = {
            "product_id": product.id
        }
        product_channels = self.list(**query)
        return self.channel_service.model.objects.filter(
            code__in=self.get_channel_id_list(product_channels)
        )

    def get_object(self, **kwargs):
        return self.model.objects.get(**kwargs)


class ProductFlowTypeService(services.BaseModelService):
    model = ProductFlowType

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.flow_type_service = FlowTypeServices(tenant_code=self.tenant_code, site_profile=self.site_profile)

    def get_flow_type_id_list(self, product_flow_types):
        return [p_flow_types.flow_type for p_flow_types in product_flow_types]

    def get_flow_types(self, product):
        query = {
            "product_id": product.id
        }
        product_flow_types = self.list(**query)
        return self.flow_type_service.model.objects.filter(
            code__in=self.get_flow_type_id_list(product_flow_types)
        )

    def get_object(self, **kwargs):
        return self.model.objects.get(**kwargs)


class ProductMarketTypeService(services.BaseModelService):
    model = ProductMarketType

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.market_type_service = MarketTypeServices(tenant_code=self.tenant_code, site_profile=self.site_profile)

    def get_market_type_id_list(self, product_market_types):
        return [p_market_types.market_type for p_market_types in product_market_types]

    def get_market_types(self, product):
        query = {
            "product_id": product.id
        }
        product_market_types = self.list(**query)
        return self.market_type_service.model.objects.filter(
            code__in=self.get_market_type_id_list(product_market_types)
        )

    def get_object(self, **kwargs):
        return self.model.objects.get(**kwargs)
