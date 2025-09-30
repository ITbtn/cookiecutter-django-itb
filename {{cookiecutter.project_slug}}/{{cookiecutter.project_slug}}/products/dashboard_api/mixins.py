from django.core.exceptions import ObjectDoesNotExist

from {{cookiecutter.project_slug}}.products.services import ProductService
from {{cookiecutter.project_slug}}.rest_utils.exceptions import BadRequestException


class ProductAPIMixin:
    product_service_class = ProductService

    def get_product(self):
        try:
            if self.kwargs.get("product_code", None):
                return self.product_service_class(tenant_code=self.request.tenant_code,
                                                  site_profile=self.request.site_profile
                                                  ).read_by_code(code_value=self.kwargs["product_code"],
                                                                 tenant_code=self.request.user.tenant_code)
            return self.product_service_class(tenant_code=self.request.tenant_code,
                                                  site_profile=self.request.site_profile).read_by_pk(pk_value=self.kwargs["product_id"])
        except ObjectDoesNotExist:
            raise BadRequestException(message=f"Invalid product ID/code")
