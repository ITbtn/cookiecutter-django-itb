from django.utils.translation import gettext_lazy as _


class ProductItemType:
    NONE_TYPE = "none"
    SUBSCRIPTION = "subscription"
    ADD_ON = "add_on"
    SIMCARD = "simcard"
    DIGITAL = "digital"
    HANDSET = "handset"
    ACCESSORY = "accessory"
    CREDIT = "credit"
    TABLET = "tablet"
    PREPAID = "prepaid"
    PREPAID_TOPUP = "prepaid_topup"
    PROMOTION = "promotion"
    INSURANCE = "insurance"
    DISCOUNT = "discount"
    PACKAGE = "package"
    ADDITIONAL_COST = "additional_cost"
    SERVICE = "service"
    SPECIAL_SERVICE = "special_service"
    HARDWARE = "hardware"
    WARRANTY = "warranty"
    COUPON = "coupon"
    VOUCHER = "voucher"
    SUPPORT = "support"
    SOFTWARE = "software"
    ENGINEER = "engineer"
    DEPOT = "depot"

    CHOICES = (
        (NONE_TYPE, _("User defined")),
        (SUBSCRIPTION, _("Subscription (Telco)")),
        (SIMCARD, _("Sim Card (Telco)")),
        (ADD_ON, _("Add-ons (Telco)")),
        (DIGITAL, _("Digital")),
        (HANDSET, _("Handset (Telco)")),
        (ACCESSORY, _("Accessory (Telco)")),
        (CREDIT, _("Credit")),
        (TABLET, _("Tablet/data-only")),
        (PREPAID, _("Prepaid")),
        (PREPAID_TOPUP, _("Prepaid Top-Up")),
        (PROMOTION, _("Promotion products")),
        (INSURANCE, _("Insurance products")),
        (DISCOUNT, _("Discount products")),
        (PACKAGE, _("Package products")),
        (ADDITIONAL_COST, _("Additional Cost")),
        (SERVICE, _("Service Products")),
        (SPECIAL_SERVICE, _("Special Service Products")),
        (HARDWARE, _("Hardware Products")),
        (WARRANTY, _("Warranty Products")),
        (COUPON, _("Coupon")),
        (VOUCHER, _("Voucher")),
        (SUPPORT, _("Support")),
        (SOFTWARE, _("Software")),
        (ENGINEER, _("Engineer")),
        (DEPOT, _("Depot")),
    )


class ConnectionType:
    """
    None/Fixed/Mobile.
    """

    NONE_TYPE = ""
    FIXED = "fixed"
    MOBILE = "mobile"

    CHOICES = (
        (NONE_TYPE, _("")),
        (FIXED, _("Fixed")),
        (MOBILE, _("Mobile")),
    )


class TKHType:
    """
    TKH options
    """

    NO_TKH = 0
    TKH_HANDSET = 1
    TKH_TABLET = 2
    TKH_ACCESSORY = 3
    TKH_REFURBISHED_HANDSET = 4
    TKH_REFURBISHED_TABLET = 5
    TKH_REFURBISHED_ACCESSORY = 6

    CHOICES = (
        (NO_TKH, _("No TKH")),
        (TKH_HANDSET, _("TKH Handset")),
        (TKH_TABLET, _("TKH Tablet")),
        (TKH_ACCESSORY, _("TKH Accessory")),
        (TKH_REFURBISHED_HANDSET, _("TKH refurbished handset")),
        (TKH_REFURBISHED_TABLET, _("TKH refurbished Tablet")),
        (TKH_REFURBISHED_ACCESSORY, _("TKH refurbished accessory")),
    )


class ProductFieldTypes:
    PRODUCT_GROUP = "product_group"
    PRODUCT_TYPE = "product_type"
    PRODUCT_NAME = "name"
    SHORT_DESCRIPTION = "short_description"
    LONG_DESCRIPTION = "long_description"
    PRODUCT_FAMILY = "product_family"
    PRODUCT_SERIES = "product_series"


class INACTIVE_PRODUCT_REASONS:
    NOT_AVAILABLE = "Product not available."
    CATALOG_NOT_VALID = "CatalogProduct has been expired."
    PRODUCT_NOT_VALID = "Product has been expired."
    SALES_PRICE_NOT_VALID = "Sales price has been expired."
    NO_SALES_PRICE = "Product has no sales price."
    NO_VALID_DATE = "Product has no valid_until date."


PRODUCT_BASIC_INFO_FIELDS = ["code", "name", "short_description", "long_description"]
