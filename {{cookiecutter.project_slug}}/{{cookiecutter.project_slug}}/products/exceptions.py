from contextlib import contextmanager

from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from rest_framework import status

from {{cookiecutter.project_slug}}.products.models import Product
from {{cookiecutter.project_slug}}.common.exceptions import BaseException, IntegrityErrorException


class ProductNotFoundException(BaseException):
    code = "PRODUCT_NOT_FOUND"
    errors = "Product not found"
    message = _("Product not found")
    status_code = status.HTTP_404_NOT_FOUND


class PriceNotFoundException(BaseException):
    errors = {
        "code": "PRICE_NOT_FOUND.",
        "error_code": "PRICE_NOT_FOUND.",
        "message": _("Prijs niet gevonden. "),
    }
    status_code = status.HTTP_404_NOT_FOUND


class ProductGroupAttributeNotFoundException(BaseException):
    code = ("PRODUCT_GROUP_ATTRIBUTE_NOT_FOUND.",)
    error_code = ("PRODUCT_GROUP_ATTRIBUTE_NOT_FOUND.",)
    message = (_("Product group attribute not found."),)
    status_code = status.HTTP_404_NOT_FOUND


class ProductGroupNotFoundException(BaseException):
    code = ("PRODUCT_GROUP_NOT_FOUND.",)
    error_code = ("PRODUCT_GROUP_NOT_FOUND.",)
    message = (_("Product group not found."),)
    status_code = status.HTTP_404_NOT_FOUND


@contextmanager
def product_exceptions():
    try:
        yield
    except Product.DoesNotExist:
        raise ProductNotFoundException()
    except IntegrityError:
        # Extract more specific information from the IntegrityError
        error_message = str(e)
        if "unique constraint" in error_message.lower():
            raise IntegrityErrorException(message="This record already exists.")
        elif "foreign key constraint" in error_message.lower():
            raise IntegrityErrorException(message="Referenced record does not exist.")
        else:
            # Generic integrity error
            raise IntegrityErrorException()
    except PriceNotFoundException as pnfe:
        raise pnfe
    except ProductGroupNotFoundException as pgnf:
        raise pgnf
    except ProductGroupAttributeNotFoundException as pgsenf:
        raise pgsenf


class PromotionNotFoundException(BaseException):
    code = "PROMOTION_NOT_FOUND"
    errors = "Promotion not found"
    message = _("Promotion not found")
    status_code = status.HTTP_404_NOT_FOUND


class ProductPromotionNotFoundException(BaseException):
    code = "PRODUCT_PROMOTION_NOT_FOUND"
    errors = "Product promotion not found"
    message = _("Product promotion not found")
    status_code = status.HTTP_404_NOT_FOUND


class RelatedProductNotFoundException(BaseException):
    code = "RELATED_PRODUCT_NOT_FOUND"
    errors = "Related product not found"
    message = _("Related product not found")
    status_code = status.HTTP_404_NOT_FOUND


class ProductTypeNotFoundException(BaseException):
    code = "PRODUCT_TYPE_NOT_FOUND"
    error_code = "PRODUCT_TYPE_NOT_FOUND"
    message = _("Product type not found")
    status_code = status.HTTP_400_BAD_REQUEST


class ProductSerialNotFoundException(BaseException):
    code = "PRODUCT_SERIAL_NOT_FOUND"
    error_code = "PRODUCT_SERIAL_NOT_FOUND"
    message = _("Product serial not found")
    status_code = status.HTTP_400_BAD_REQUEST


class ProductGroupAttributeAlreadyExistsException(BaseException):
    code = "PRODUCT_GROUP_ATTRIBUTE_ALREADY_EXISTS"
    error_code = "PRODUCT_GROUP_ATTRIBUTE_ALREADY_EXISTS"
    message = _("Product group attribute already exists")
    status_code = status.HTTP_400_BAD_REQUEST


class InvalidLockFieldException(BaseException):
    code = "PRODUCT_LOCK_FIELD_INVALID"
    error_code = code
    message = _("An invalid field name is used for locking the product.")
    status_code = status.HTTP_400_BAD_REQUEST


class BrandNotFoundException(BaseException):
    code = "BRAND_NOT_FOUND"
    error_code = code
    message = _("Brand not found")
    status_code = status.HTTP_404_NOT_FOUND


class ProductRelationAlreadyExistsException(BaseException):
    code = "PRODUCT_RELATION_ALREADY_EXISTS"
    error_code = code
    message = _("Product relation already exists")
    status_code = status.HTTP_400_BAD_REQUEST


class InvalidNumberOfProductSerialNumbers(BaseException):
    code = "INVALID_NUMBER_OF_PRODUCT_SERIAL_NUMBERS"
    errors = "Invalid number of product serial numbers"
    message = _("Invalid number of product serial numbers")
    status_code = status.HTTP_400_BAD_REQUEST


class FoundDuplicateProductSerialNumbers(BaseException):
    code = "FOUND_DUPLICATE_PRODUCT_SERIAL_NUMBERS"
    errors = "Duplicate product serial found"
    message = _("Duplicate product serial found")
    status_code = status.HTTP_400_BAD_REQUEST


class InvalidProductSerialNumber(BaseException):
    code = "INVALID_PRODUCT_SERIAL_NUMBER"
    errors = "A product already exist with the given serial number"
    message = _("A product already exist with the given serial number")
    status_code = status.HTTP_400_BAD_REQUEST


class ProductSerialNumberIsRequired(BaseException):
    code = "PRODUCT_SERIAL_NUMBER_REQUIRED"
    error_code = code
    message = _("Product serial number is required for {product}")
    status_code = status.HTTP_400_BAD_REQUEST
