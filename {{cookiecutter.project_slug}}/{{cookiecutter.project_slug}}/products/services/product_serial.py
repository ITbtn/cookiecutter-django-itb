from django.core.exceptions import ObjectDoesNotExist

from {{cookiecutter.project_slug}}.common.bases import services
from {{cookiecutter.project_slug}}.products.exceptions import ProductSerialNotFoundException
from {{cookiecutter.project_slug}}.products.models import ProductSerial

from ..exceptions import (
    FoundDuplicateProductSerialNumbers,
    InvalidNumberOfProductSerialNumbers,
    InvalidProductSerialNumber,
    ProductSerialNumberIsRequired,
)


class ProductSerialService(services.BaseModelService):
    model = ProductSerial

    @staticmethod
    def validate_product_serials(product, product_quantity: int, product_serials: list):
        if product_serials:
            if len(product_serials) != product_quantity:
                raise InvalidNumberOfProductSerialNumbers()
            elif len(set(product_serials)) != product_quantity:
                raise FoundDuplicateProductSerialNumbers()
        elif product.is_serial_keeping:
            raise ProductSerialNumberIsRequired({"product": product.name})

    def create_product_serial(self, **data):
        if self.model.objects.filter(
            serial_number=data["serial_number"], tenant_code=self.tenant_code
        ).exists():
            raise InvalidProductSerialNumber(
                message="A product already exist with serial number {0}".format(
                    data["serial_number"]
                )
            )
        return self.create_model_instance(self.model, **data)

    def get_product_serial_object(self, product, serial_number):
        try:
            return self.model.objects.get(serial_number=serial_number, product=product)
        except ObjectDoesNotExist:
            raise ProductSerialNotFoundException(
                message="Product not found with serial number {0}".format(serial_number)
            )

    def get_product_by_serial(self, serial_number):
        try:
            return self.model.objects.get(serial_number=serial_number).product
        except ObjectDoesNotExist:
            raise ProductSerialNotFoundException(
                message="Product not found with serial number {0}".format(serial_number)
            )
