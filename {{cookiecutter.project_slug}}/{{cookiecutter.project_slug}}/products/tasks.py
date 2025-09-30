import logging
from io import BytesIO

import requests
from celery import shared_task
from django.core import files

from {{cookiecutter.project_slug}}.products.services import ProductService

logger = logging.getLogger(__name__)


@shared_task()
def update_product_image(product_image_data_list):
    """
    :param product_image_data_list:
    :return:
    """
    for product_image_data in product_image_data_list:
        update_single_product_image(product_image_data)


@shared_task()
def update_single_product_image(product_image_data):
    """
    Fetch the images for 1 single product
    The format of the product_image_data:
    {
        'code' : <product_code>,
        'images': [ 'url': <url_of_image>, 'field_name': <name_of_the_field_with_image_on_product ]
    }
    :param product_image_data: mapped_dict with product image stuff
    :return: Nothing
    """
    product_service = ProductService()
    product_code = product_image_data.get("code")
    product = product_service.get_product(**{"code": product_code})
    if not product:
        return
    for image in product_image_data.get("images"):
        image_url = image.get("url")
        field = image.get("field_name")
        # we skip fetching the image if there is already an image on the product
        # otherwise we keep fetching images over and over and that is killing the S3 spaces (on size)
        # for now if force_image=True, we fetch it anyway default should be False off course
        # todo: if required: delete the old image and the fetch it again.
        # to consider: if we delete the image and another system is still having the old reference, the image for them
        # is gone as well
        if image_url and (
            getattr(product, field) in ["", None]
            or product_image_data.get("force_image_fetch", False)
        ):
            try:
                r = requests.get(image_url)
                if r.status_code == requests.codes.ok:
                    file_name = image_url.split("/")[-1]
                    file = BytesIO()
                    file.write(r.content)
                    getattr(product, field).save(file_name, files.File(file))
            except Exception as e:
                logger.error(f"Error: {e} - image not saved")
    product.save()
