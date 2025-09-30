from django.core.exceptions import ObjectDoesNotExist

from .price import PriceService
from ..models import Product


class AddOnService:

    def __init__(self, subscription_id, required_product_id=None):
        self.subscription_id = subscription_id
        self.required_product_id = required_product_id

    def get_enriched_add_ons(self):
        """
        NOTE: This method is not in use anymore.
        :return:
        """
        add_on_data_list = self.get_add_ons()
        enriched_add_on_data_list = self.enrich_add_on_data(add_on_data_list=add_on_data_list)

        return enriched_add_on_data_list

    def get_add_ons(self):
        # TODO: Need to move import to top section
        #  For now to ignore circular import we had to import here
        from .product_service import ProductService
        product_service = ProductService()
        add_on_data_list = product_service.get_add_ons_by_product_id(
            product_id=self.subscription_id,
            required_product_id=self.required_product_id
        )

        return add_on_data_list

    def enrich_add_on_data(self, add_on_data_list):
        price_service = PriceService()

        for add_on_data in add_on_data_list:
            # TODO: Need to move into another method
            add_on_id = add_on_data["id"]
            product_type = None
            product_type_code = None
            list_recurring_monthly_fee = 0
            recurring_monthly_fee = 0

            try:
                product_obj = Product.objects.get(id=add_on_id)
            except ObjectDoesNotExist:
                product_obj = None

            if product_obj:
                product_type = product_obj.product_type.name
                product_type_code = product_obj.product_type.code
                list_recurring_monthly_fee = price_service.get_list_recurring_monthly_fee(
                    product_code=product_obj.code
                )
                recurring_monthly_fee = price_service.get_list_recurring_monthly_fee(
                    product_code=product_obj.code
                )

            add_on_data.update({
                "product_type": product_type,
                "product_type_code": product_type_code,
                "list_recurring_monthly_fee": list_recurring_monthly_fee,
                "recurring_monthly_fee": recurring_monthly_fee,
            })

        return add_on_data_list
