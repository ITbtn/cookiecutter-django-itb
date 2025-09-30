from {{cookiecutter.project_slug}}.products.dashboard_api.serializers.brand import BrandSerializer
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers.channel import (
    ProductChannelInputSerializer,
    ProductChannelOutputSerializer,
)
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers.flow_type import (
    ProductFlowTypeInputSerializer,
    ProductFlowTypeOutputSerializer,
)
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers.market_type import (
    ProductMarketTypeInputSerializer,
    ProductMarketTypeOutputSerializer,
)
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers.page_layout import (
    PageLayoutsSerializer,
)
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers.price import (
    PriceInputSerializer,
    PriceListContactGroupSerializer,
    PriceSerializer,
)
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers.product import (
    BasicProductOutputSerializer,
    DashboardProductActivePriceListItemOutputSerializer,
    DashboardProductCreateSerializer,
    DashboardProductUpdateSerializer,
    DashboardProductListSerializer,
    DashboardProductOutputSerializer,
)
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers.product_attribute import (
    DashboardProductAttributeInputSerializer,
    DashboardProductAttributeOutputSerializer,
    DashboardProductAttributeSerializer,
)
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers.product_group import (
    BasicProductGroupSerializer,
    ProductGroupParentSerializer,
    ProductGroupSerializer,
)
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers.product_group_attribute import (
    DashboardProductGroupAttributeInputSerializer,
    DashboardProductGroupAttributeOutputSerializer,
)
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers.product_promotion import (
    ProductPromotionInputSerializer,
    ProductPromotionOutputSerializer,
    ProductPromotionUpdateSerializer,
)
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers.product_type import (
    BasicProductTypeSerializer,
    DashProductTypeOutputSerializer,
)
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers.related_product import (
    RelatedProductImportInputSerializer,
    RelatedProductInputSerializer,
    RelatedProductOutputSerializer,
    RelatedProductUpdateSerializer,
)
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers.unit import UnitSerializer
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers.vat import (
    VatSerializer,
    VatUpdateSerializer,
)
