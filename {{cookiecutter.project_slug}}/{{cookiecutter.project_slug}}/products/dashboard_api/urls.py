from django.urls import include, path

from {{cookiecutter.project_slug}}.products.dashboard_api.views import (
    BrandListCreateAPIView,
    BrandRetrieveUpdateAPIView,
    DashboardProductActivePriceListItemListAPIView,
    FamilyListCreateAPIView,
    FamilyRetrieveUpdateDestroyAPIView,
    FetchProductDataFromOTAPIView,
    PageLayoutsListCreateAPIView,
    PageLayoutsRetrieveUpdateDestroyAPIView,
    ProductAttributeListCreateAPIView,
    ProductAttributeRetrieveUpdateDestroyAPIView,
    ProductChannelListCreateAPIView,
    ProductChannelRetrieveUpdateDeleteAPIView,
    ProductFlowTypeListCreateAPIView,
    ProductFlowTypeRetrieveUpdateDeleteAPIView,
    ProductGroupListCreateAPIView,
    ProductGroupRetrieveUpdateDestroyAPIView,
    ProductListCreateAPIView,
    ProductMarketTypeListCreateAPIView,
    ProductMarketTypeRetrieveUpdateDeleteAPIView,
    ProductPriceListCreateAPIView,
    ProductPriceRetrieveUpdateDeleteAPIView,
    ProductPromotionListCreateAPIView,
    ProductPromotionRetrieveUpdateDestroyAPIView,
    ProductRetrieveUpdateDeleteAPIView,
    ProductTypeListCreateAPIView,
    ProductTypeRetrieveUpdateDestroyAPIView,
    RelatedProductsListCreateAPIView,
    RelatedProductsRetrieveDestroyAPIView,
    SeriesListCreateAPIView,
    SeriesRetrieveUpdateDestroyAPIView,
    UnitListCreateAPIView,
    UnitRetrieveUpdateDestroyAPIView,
    VatListCreateAPIView,
    VatRetrieveUpdateDestroyAPIView,
)

app_name = "{{cookiecutter.project_slug}}.products"


brand_patterns = (
    [
        path("", BrandListCreateAPIView.as_view(), name="brand-list-create"),
        path(
            "<str:code>/",
            BrandRetrieveUpdateAPIView.as_view(),
            name="brand-details-update-delete",
        ),
    ],
    "brands",
)

group_pattern = (
    [
        path(
            "",
            ProductGroupListCreateAPIView.as_view(),
            name="product-group-list-create",
        ),
        path(
            "<str:product_group_code>/",
            ProductGroupRetrieveUpdateDestroyAPIView.as_view(),
            name="product-group-retrieve-update-destroy",
        ),
    ],
    "product-groups",
)

family_series_patterns = (
    [
        path("family/", FamilyListCreateAPIView.as_view(), name="family-list-create"),
        path(
            "family/<str:code>/",
            FamilyRetrieveUpdateDestroyAPIView.as_view(),
            name="family-details-update-delete",
        ),
        path("series/", SeriesListCreateAPIView.as_view(), name="series-list-create"),
        path(
            "series/<str:code>/",
            SeriesRetrieveUpdateDestroyAPIView.as_view(),
            name="series-details-update-delete",
        ),
    ],
    "family-series",
)

type_patterns = (
    [
        path("", view=ProductTypeListCreateAPIView.as_view(), name="dash-list-create"),
        path(
            "<str:code>/",
            view=ProductTypeRetrieveUpdateDestroyAPIView.as_view(),
            name="dash-retrieve-update-destroy",
        ),
    ],
    "types",
)

vat_patterns = (
    [
        path("", VatListCreateAPIView.as_view(), name="list-create"),
        path(
            "<str:code>/",
            view=VatRetrieveUpdateDestroyAPIView.as_view(),
            name="vat-retrieve-update-destroy",
        ),
    ],
    "vats",
)

urlpatterns = [
    path("", ProductListCreateAPIView.as_view(), name="product-list-create"),
    path("brands/", include(brand_patterns, namespace="brands")),
    path("product-group/", include(group_pattern, namespace="product-groups")),
    path("family-series/", include(family_series_patterns, namespace="family-series")),
    path("types/", include(type_patterns, namespace="types")),
    path("units/", UnitListCreateAPIView.as_view(), name="unit-list-create"),
    path("vats/", include(vat_patterns, namespace="vats")),
    path(
        "units/<str:code>/",
        UnitRetrieveUpdateDestroyAPIView.as_view(),
        name="unit-detail-update-delete",
    ),
    path(
        "page-layouts/",
        PageLayoutsListCreateAPIView.as_view(),
        name="page-layouts-list-create",
    ),
    path(
        "page-layouts/<str:code>/",
        PageLayoutsRetrieveUpdateDestroyAPIView.as_view(),
        name="page-layouts-retrieve-update-destroy",
    ),
    path(
        "<str:code>/",
        ProductRetrieveUpdateDeleteAPIView.as_view(),
        name="retrieve-update-delete",
    ),
    path(
        "<str:product_code>/pricelist-prices/",
        DashboardProductActivePriceListItemListAPIView.as_view(),
        name="product-price-list-listview",
    ),
    path(
        "<str:product_code>/prices/",
        ProductPriceListCreateAPIView.as_view(),
        name="product-price-list",
    ),
    path(
        "<str:product_code>/prices/<str:price_code>/",
        ProductPriceRetrieveUpdateDeleteAPIView.as_view(),
        name="product-price-get-update-delete",
    ),
    path(
        "<str:product_code>/product-promotions/",
        ProductPromotionListCreateAPIView.as_view(),
        name="product-promotions-list-create",
    ),
    path(
        "<str:product_code>/product-promotions/<str:product_promotion_code>/",
        ProductPromotionRetrieveUpdateDestroyAPIView.as_view(),
        name="product-promotions-retrieve-update-destroy",
    ),
    path(
        "<str:product_code>/attributes/",
        ProductAttributeListCreateAPIView.as_view(),
        name="product-attribute-list-create",
    ),
    path(
        "<str:product_code>/attribute/<str:attribute_code>/",
        ProductAttributeRetrieveUpdateDestroyAPIView.as_view(),
        name="product-attribute-retrieve-update-delete",
    ),
    path(
        "<str:product_code>/related-products/",
        RelatedProductsListCreateAPIView.as_view(),
        name="related-products-list-create",
    ),
    path(
        "<str:product_code>/related-products/<str:code>/",
        RelatedProductsRetrieveDestroyAPIView.as_view(),
        name="related-products-retrieve-update-destroy",
    ),
    path(
        "<str:product_code>/channels/",
        ProductChannelListCreateAPIView.as_view(),
        name="product-channel-list-add",
    ),
    path(
        "<str:product_code>/channels/<code:channel_code>/",
        ProductChannelRetrieveUpdateDeleteAPIView.as_view(),
        name="product-channel-update-retrieve-delete",
    ),
    path(
        "<str:product_code>/flow-type/",
        ProductFlowTypeListCreateAPIView.as_view(),
        name="product-flowtype-list-add",
    ),
    path(
        "<str:product_code>/flow-type/<code:flowtype_code>/",
        ProductFlowTypeRetrieveUpdateDeleteAPIView.as_view(),
        name="product-flowtype-update-retrieve-delete",
    ),
    path(
        "<str:product_code>/market-type/",
        ProductMarketTypeListCreateAPIView.as_view(),
        name="product-markettype-list-add",
    ),
    path(
        "<str:product_code>/market-type/<code:markettype_code>/",
        ProductMarketTypeRetrieveUpdateDeleteAPIView.as_view(),
        name="product-markettype-update-retrieve-delete",
    ),
    path(
        "<str:product_code>/enrich-product/",
        FetchProductDataFromOTAPIView.as_view(),
        name="fetch-product",
    ),
]
