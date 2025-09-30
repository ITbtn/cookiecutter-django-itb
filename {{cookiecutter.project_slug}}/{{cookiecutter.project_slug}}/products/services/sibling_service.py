class SiblingService:

    def __init__(self, handset_id):
        self.subscription_id = handset_id

    def get_enriched_siblings(self):
        sibling_data_list = self.get_siblings()
        enriched_sibling_data_list = self.enrich_sibling_data(sibling_data_list=sibling_data_list)

        return enriched_sibling_data_list

    def get_siblings(self):
        # TODO: Need to move import to top section
        #  For now to ignore circular import we had to import here
        from .product_service import ProductService
        product_service = ProductService()
        sibling_data_list = product_service.get_siblings_by_product_id(
            product_id=self.subscription_id
        )

        return sibling_data_list

    def enrich_sibling_data(self, sibling_data_list):
        # TODO: Need to move import to top section
        #  For now to ignore circular import we had to import here
        from .product_service import ProductService
        product_service = ProductService()

        for sibling_data in sibling_data_list:
            sibling_id = sibling_data["id"]
            dimensional_attribute_data_list = product_service.get_sibling_dimensional_attributes_by_product_id(
                product_id=sibling_id
            )

            sibling_data.update({
                "dimensional_attributes": dimensional_attribute_data_list
            })

        return sibling_data_list
