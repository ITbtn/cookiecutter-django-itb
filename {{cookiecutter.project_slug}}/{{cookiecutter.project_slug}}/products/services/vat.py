import decimal

from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict

from {{cookiecutter.project_slug}}.common.bases import services
from {{cookiecutter.project_slug}}.common.cache import TenantBaseCache
from {{cookiecutter.project_slug}}.common.utils import fix_internal_decimal_places
from {{cookiecutter.project_slug}}.products.models import VAT
from {{cookiecutter.project_slug}}.rest_utils.exceptions import BadRequestException


class VatService(services.BaseModelService):
    model = VAT

    def create_default_vat_codes(self):
        """
        create default VAT codes if they do not exist.
        We need at least:
        code        name        value
        vat_0       0% VAT      0%
        vat_high    High VAT    21% (NL)
        vat_reverse reverse charge  0%
        """
        self.model.objects.get_or_create(
            tenant_code=self.tenant_code,
            code="vat_0",
            defaults={"name": "0% VAT", "percent_value": decimal.Decimal("0.0")},
        )
        self.model.objects.get_or_create(
            tenant_code=self.tenant_code,
            code="vat_high",
            defaults={
                "name": "21% VAT",
                "percent_value": decimal.Decimal("21.0"),
                "is_default": True,
            },
        )
        self.model.objects.get_or_create(
            tenant_code=self.tenant_code,
            code="vat_reverse_charge",
            defaults={
                "name": "Reverse charges",
                "percent_value": decimal.Decimal("0.0"),
            },
        )

    def get_default_vat_code(self):
        """
        return the default VAT code, will be vat_high for now
        """
        return "vat_high"

    def get_or_create_default_vat(self):
        try:
            vat = self.list().get(is_available=True, is_default=True)
        except self.model.DoesNotExist:
            # create default vats
            self.create_default_vat_codes()
            vat = self.list().get(is_available=True, is_default=True)
        return vat

    def get_vat_by_code(self, code):
        """
        get the VAT code, do it from cache if possible
        """
        vat_cache = TenantBaseCache(
            tenant_code=self.get_tenant_code(),
            site_profile=self.site_profile,
            cache_key="VAT_" + code,
        )
        cached_response = vat_cache.get()
        if cached_response:
            return cached_response
        else:
            vat = self.read_by_code(code)
            vat_dict = model_to_dict(vat)
            vat_cache.set(vat_dict)
            return vat_dict

    def get_vat_as_dict(self, vat_obj):
        """
        get the VAT as dict
        """
        vat_cache = TenantBaseCache(
            tenant_code=self.get_tenant_code(),
            site_profile=self.site_profile,
            cache_key="VAT_" + vat_obj.code,
        )
        vat_dict = model_to_dict(vat_obj)
        vat_cache.set(vat_dict)
        return vat_dict

    def get_price_incl_vat(self, price_ex_vat, price_incl_vat, vat_code):
        """
        Calculate the sales price with the given input.
        To do the proper price calculation including VAT we need to know the price ex_vat and the correct vat_code
        Specially when a user has a reverse_charge: then the default price incl VAT we have is not the price
        the user will pay. Because in that case we need to look at the ex_vat price and take the proper
        VAT percentage.
        :param price_ex_vat: price of the product excluding VAT
        :param price_incl_vat: known price of the product incl. vat
        :param vat_code: VAT code to use
        Pls note: currently we do not use the price_in_vat, but we will need this for consumer orders in the future.
        """
        if not vat_code:
            vat_code = self.get_default_vat_code()
        vat = self.get_vat_by_code(vat_code)
        vat_percentage = vat.get("percent_value")
        if vat_percentage > 0:
            price = price_ex_vat * (1 + (vat.get("percent_value") / 100))
        else:
            price = price_ex_vat
        return fix_internal_decimal_places(price)

    def get_price_ex_vat(self, price_incl_vat, vat_code):
        """
        Calculate the price ex with the given input.
        basically we should not use this, but for some old code we need to calculate the ex_vat price
        :param price_incl_vat: known price of the product incl. vat
        :param vat_code: VAT code to use
        Pls note: currently we do not use the price_in_vat, but we will need this for consumer orders in the future.
        """
        if not vat_code:
            vat_code = self.get_default_vat_code()
        vat = self.get_vat_by_code(vat_code)
        vat_percentage = vat.get("percent_value")
        if vat_percentage > 0:
            percentage = vat_percentage / 100
            price = price_incl_vat - (percentage * (price_incl_vat / (1 + percentage)))
        else:
            price = price_incl_vat
        return fix_internal_decimal_places(price)

    def read_by_code(self, code_value, **kwargs):
        try:
            return super().read_by_code(code_value, **kwargs)
        except ObjectDoesNotExist:
            raise BadRequestException(f"Vat not found with code: {code_value}.")

    def get_export_id_by_code(self, code):
        vat_dict = self.get_vat_by_code(code)
        export_id = vat_dict.get("export_id", "")
        # return "Geen" for SnelStart if export_id is None
        external_code = export_id or "Geen"
        return external_code
