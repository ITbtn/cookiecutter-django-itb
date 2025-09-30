from {{cookiecutter.project_slug}}.products.dashboard_api.views.brand import (
    BrandListCreateAPIView,
    BrandRetrieveUpdateAPIView,
)
from {{cookiecutter.project_slug}}.products.dashboard_api.views.channel import (
    ProductChannelListCreateAPIView,
    ProductChannelRetrieveUpdateDeleteAPIView,
)
from {{cookiecutter.project_slug}}.products.dashboard_api.views.flow_type import (
    ProductFlowTypeListCreateAPIView,
    ProductFlowTypeRetrieveUpdateDeleteAPIView,
)
from {{cookiecutter.project_slug}}.products.dashboard_api.views.market_type import (
    ProductMarketTypeListCreateAPIView,
    ProductMarketTypeRetrieveUpdateDeleteAPIView,
)
from {{cookiecutter.project_slug}}.products.dashboard_api.views.page_layout import (
    PageLayoutsListCreateAPIView,
    PageLayoutsRetrieveUpdateDestroyAPIView,
)
from {{cookiecutter.project_slug}}.products.dashboard_api.views.price import (
    ProductPriceListCreateAPIView,
    ProductPriceRetrieveUpdateDeleteAPIView,
)
from {{cookiecutter.project_slug}}.products.dashboard_api.views.product import (
    DashboardProductActivePriceListItemListAPIView,
    FetchProductDataFromOTAPIView,
    ProductListCreateAPIView,
    ProductRetrieveUpdateDeleteAPIView,
)
from {{cookiecutter.project_slug}}.products.dashboard_api.views.product_attribute import (
    ProductAttributeListCreateAPIView,
    ProductAttributeRetrieveUpdateDestroyAPIView,
)
from {{cookiecutter.project_slug}}.products.dashboard_api.views.product_group import (
    ProductGroupListCreateAPIView,
    ProductGroupRetrieveUpdateDestroyAPIView,
)
from {{cookiecutter.project_slug}}.products.dashboard_api.views.product_promotion import (
    ProductPromotionListCreateAPIView,
    ProductPromotionRetrieveUpdateDestroyAPIView,
)
from {{cookiecutter.project_slug}}.products.dashboard_api.views.related_product import (
    RelatedProductsListCreateAPIView,
    RelatedProductsRetrieveDestroyAPIView,
)
from {{cookiecutter.project_slug}}.products.dashboard_api.views.unit import (
    UnitListCreateAPIView,
    UnitRetrieveUpdateDestroyAPIView,
)
from .family_series import (
    FamilyListCreateAPIView,
    FamilyRetrieveUpdateDestroyAPIView,
    SeriesListCreateAPIView,
    SeriesRetrieveUpdateDestroyAPIView,
)
from .product_type import (
    ProductTypeListCreateAPIView,
    ProductTypeRetrieveUpdateDestroyAPIView,
)
from .product_vat import (
    VatListCreateAPIView,
    VatRetrieveUpdateDestroyAPIView,
)
