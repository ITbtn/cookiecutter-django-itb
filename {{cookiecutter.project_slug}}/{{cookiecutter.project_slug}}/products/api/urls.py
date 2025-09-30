from django.urls import include, path

from {{cookiecutter.project_slug}}.products.api.views.product import (
    GenericDetailsAPIView,
    GenericListCreateAPIView,
    MandatoryProductListAPIView,
    ProductAttributeAPIView,
    ProductAttributesAPIView,
    ProductCreateView,
    ProductGroupAPIView,
    ProductGroupRetrieveUpdateDeleteAPIView,
    ProductsByProductGroupAPIView,
    ProductsListAPIView,
    RelatedProductListAPIView,
)

from .views import (
    BrandListAPIView,
    ProductTypeListCreateAPIView,
    ProductTypeRetrieveUpdateDestroyAPIView,
)
from .views.attribute import (
    ProductAttributeListCreateAPIView,
    ProductAttributeRetrieveUpdateDeleteAPIView,
)
from .views.product_brand import BrandRetrieveDeleteUpdateAPIView
from .views.product_linueup import (
    ProductLineupListCreateAPIView,
    ProductLineupRetrieveUpdateDeleteAPIView,
)
from .views.product_type import ProductGroupsListType
from .views.promotions import (
    ProductPromotionListAPIView,
    PromotionsListCreateAPIView,
    PromotionsRetrieveUpdateDeleteAPIView,
)
from .views.unit import UnitListCreateAPIView
from .views.vat import VatListCreateAPIView

app_name = "{{cookiecutter.project_slug}}.products"


residential_patterns = (
    [
        path("", view=ProductsListAPIView.as_view(), name="list"),
        path("create/", view=ProductCreateView.as_view(), name="create"),
    ],
    "residential",
)


type_patterns = (
    [
        path("", view=ProductTypeListCreateAPIView.as_view(), name="list_create"),
        path(
            "<str:code>/",
            view=ProductTypeRetrieveUpdateDestroyAPIView.as_view(),
            name="retrieve_update_destroy",
        ),
        path(
            "<str:code>/groups/",
            view=ProductGroupsListType.as_view(),
            name="group_list_by_type",
        ),
    ],
    "types",
)

brand_patterns = (
    [
        path("", BrandListAPIView.as_view(), name="list"),
        path(
            "<str:code>/",
            BrandRetrieveDeleteUpdateAPIView.as_view(),
            name="create-update-delete",
        ),
    ],
    "brands",
)

lineup_patterns = (
    [
        path("", ProductLineupListCreateAPIView.as_view(), name="list-create"),
        path(
            "<int:id>/",
            ProductLineupRetrieveUpdateDeleteAPIView.as_view(),
            name="retrieve-update-delete",
        ),
    ],
    "lineups",
)

generic_patterns = (
    [
        path("", GenericListCreateAPIView.as_view(), name="list"),
        path("<str:code>/", view=GenericDetailsAPIView.as_view(), name="detail"),
        path(
            "<str:code>/product-attributes/",
            ProductAttributesAPIView.as_view(),
            name="product-attributes",
        ),
    ],
    "generic",
)

group_patterns = (
    [
        path("", ProductGroupAPIView.as_view(), name="list"),
        path(
            "<str:code>/",
            ProductGroupRetrieveUpdateDeleteAPIView.as_view(),
            name="group-retrieve-update-delete",
        ),
        path(
            "<str:code>/products/",
            ProductsByProductGroupAPIView.as_view(),
            name="products",
        ),
    ],
    "groups",
)


promotion_patterns = (
    [
        path("", PromotionsListCreateAPIView.as_view(), name="list-create"),
        path(
            "<str:code>/",
            PromotionsRetrieveUpdateDeleteAPIView.as_view(),
            name="retrieve-update-delete",
        ),
    ],
    "promotions",
)


vat_patterns = (
    [
        path("", VatListCreateAPIView.as_view(), name="list-create"),
    ],
    "vat",
)

unit_patterns = (
    [path("", UnitListCreateAPIView.as_view(), name="list-create")],
    "unit",
)


urlpatterns = [
    path("vats/", include(vat_patterns, namespace="vat")),
    path("units/", include(unit_patterns, namespace="unit")),
    path("promotions/", include(promotion_patterns, namespace="promotions")),
    path("lineups/", include(lineup_patterns, namespace="lineups")),
    path("groups/", include(group_patterns, namespace="groups")),
    path("types/", include(type_patterns, namespace="types")),
    path("brands/", include(brand_patterns, namespace="brands")),
    path("residential/", include(residential_patterns, namespace="residential")),
    path(
        "<code:product_code>/attributes/",
        ProductAttributeListCreateAPIView.as_view(),
        name="product-attribute-list",
    ),
    path(
        "<code:product_code>/attributes/<int:attribute_id>/",
        ProductAttributeRetrieveUpdateDeleteAPIView.as_view(),
        name="product-attribute-get-update-delete",
    ),
    path(
        "<code:product_code>/promotions/",
        ProductPromotionListAPIView.as_view(),
        name="product-promotion-list",
    ),
    path(
        "<code:product_code>/attributes/",
        ProductAttributeAPIView.as_view(),
        name="product-attributes",
    ),
    path(
        "<code:product_code>/related-products/",
        RelatedProductListAPIView.as_view(),
        name="related-product-list",
    ),
    path(
        "<code:product_code>/mandatory-products/",
        MandatoryProductListAPIView.as_view(),
        name="mandatory-product-list",
    ),
    path("", include(generic_patterns, namespace="generic")),
]
