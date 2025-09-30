from django.core.exceptions import ObjectDoesNotExist
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from {{cookiecutter.project_slug}}.common.bases import api_views
from {{cookiecutter.project_slug}}.contacts.services import ContactService
from {{cookiecutter.project_slug}}.products.api.serializers.product_group import (
    ProductGroupParentSerializer,
    ProductGroupSerializer,
)
from {{cookiecutter.project_slug}}.products.configs.product_config import ProductItemType
from {{cookiecutter.project_slug}}.products.exceptions import ProductNotFoundException
from {{cookiecutter.project_slug}}.products.services import ProductGroupService
from {{cookiecutter.project_slug}}.rest_utils.exceptions import BadRequestException
from {{cookiecutter.project_slug}}.users.services import UserService

from ...models import Product
from ...services import ProductService
from ...services.product_attribute_service import ProductAttributeService
from ..serializers.product import (
    ProductDetailAttributeSerializer,
    ProductDetailSerializer,
    ProductInputSerializer,
    ProductListSerializer,
    ProductOutputSerializer,
    ProductUpdateInputSerializer,
    RelationProductSerializer,
)
from ..serializers.product_create import ProductCreateSerializer
from ..serializers.product_feed import ProductFeedSerializer


class ProductAPIMixin:
    product_service_class = ProductService

    def get_product(self):
        try:
            if self.kwargs.get("product_code", None):
                return self.product_service_class(
                    tenant_code=self.request.tenant_code,
                    site_profile=self.request.site_profile,
                ).read_by_code(code_value=self.kwargs["product_code"])
            return self.product_service_class(
                tenant_code=self.request.tenant_code,
                site_profile=self.request.site_profile,
            ).read_by_pk(pk_value=self.kwargs["product_id"])
        except ObjectDoesNotExist:
            raise BadRequestException(message="Invalid product ID/code")


class ProductCreateView(CreateAPIView):
    # TODO: refactor the product create API, serializer
    serializer_class = ProductCreateSerializer
    service_class = ProductService

    def get_serializer(self, *args, **kwargs):
        if isinstance(self.request.data, list):
            kwargs["many"] = True

        context = super().get_serializer_context()
        context["tenant_code"] = self.request.tenant_code
        context["site_profile"] = self.request.site_profile
        return super().get_serializer(*args, context=context, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # update_product_image.delay(product_data=request.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductsListAPIView(api_views.BaseDashboardListAPIView):
    # filterset_class = ProductFilter
    service_class = ProductService
    serializer_class = ProductFeedSerializer

    def get_queryset(self):
        return Product.objects.filter(tenant_code=self.request.tenant_code)


class ProductAttributeAPIView(api_views.BaseListAPIView):
    service_class = ProductAttributeService

    @swagger_auto_schema(
        operation_description="Get product attributes",
        responses={
            status.HTTP_200_OK: "Product attributes",
        },
    )
    def get(self, request, *args, **kwargs):
        self.prepare_query_params_dict()
        service_class = self.service_class(
            tenant_code=request.tenant_code, site_profile=request.site_profile
        )
        product_attributes = service_class.get_product_attributes(
            product_code=kwargs["product_code"]
        )
        return Response(data=product_attributes, status=status.HTTP_200_OK)


class GenericListCreateAPIView(api_views.BaseDashboardListCreateAPIView):
    """
    Request: api/v1/products/?product_type=handset/tablet
    """

    service_class = ProductService
    serializer_class = ProductInputSerializer
    output_serializer_class = ProductListSerializer
    queryset = Product.objects.all()

    def check_product_type(self, product_type=None):
        if product_type:
            for item in ProductItemType.CHOICES:
                if item[0] == product_type:
                    return product_type
        return None

    def get_queryset(self):
        # We have a product type "none", so it's default
        query_params_dict = self.prepare_query_params_dict()
        product_type = self.check_product_type(
            query_params_dict.get("product_type", None)
        )
        if product_type:
            return self.queryset.filter(
                product_type__system_type=product_type,
                tenant_code=self.request.tenant_code,
            )
        return self.queryset.order_by("-id")

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.get_queryset())
        if page:
            serializer = self.output_serializer_class(
                instance=page, many=True, context=self.get_serializer_context()
            )
            return self.get_paginated_response(serializer.data)
        serializer = self.output_serializer_class(
            instance=self.get_queryset(),
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_obj = self.service_class(
            tenant_code=request.tenant_code,
            site_profile=request.site_profile,
            user=request.user,
        ).create_product_instance(**serializer.validated_data)
        output_serializer = self.output_serializer_class(
            instance=product_obj, context=self.get_serializer_context()
        )
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class ProductRetrieveUpdateDeleteAPIView(api_views.BaseRetrieveUpdateDestroyAPIView):
    service_class = ProductService
    serializer_class = ProductUpdateInputSerializer
    output_serializer_class = ProductOutputSerializer
    queryset = Product.objects.all()

    def get_object(self):
        try:
            return self.service_class().read_by_code(
                code_value=self.kwargs["code"],
                tenant_code=self.request.tenant_code,
                site_profile=self.request.site_profile,
            )
        except ObjectDoesNotExist:
            raise BadRequestException(message="Invalid product Code")


class GenericDetailsAPIView(api_views.BaseRetrieveAPIView):
    service_class = ProductService
    output_serializer_class = ProductDetailSerializer
    queryset = Product.objects.all()
    read_by = "code"
    permission_classes = [AllowAny]

    def get_object(self):
        try:
            return super().get_object()
        except ObjectDoesNotExist:
            raise ProductNotFoundException

    def retrieve(self, request, *args, **kwargs):
        # user_service = UserService(
        #     tenant_code=self.request.tenant_code, site_profile=self.request.site_profile
        # )
        product_service = ProductService(
            tenant_code=self.request.tenant_code, site_profile=self.request.site_profile
        )
        instance = self.get_object()
        # params = self.prepare_query_params()
        # contact = None
        # if not user_service.is_external(user=request.user):
        #     contact_uuid = request.query_params.get("contact_uuid", None)
        #     if contact_uuid:
        #         contact = ContactService(
        #             tenant_code=self.request.tenant_code,
        #             site_profile=self.request.site_profile,
        #         ).get_contact(uuid=contact_uuid)
        # else:
        #     contact = user_service.get_contact(user=self.request.user)
        # TOFIX: need to refactor the API
        product_dict = product_service.get_enriched_product(
            code=instance.code,
            # contact=contact,
            # user=request.user,
            # catalog_code=params.get("catalog_code", None),
        )
        serializer = self.get_serializer(
            product_dict, context=self.get_serializer_context()
        )
        return Response(serializer.data)


class ProductGroupAPIView(api_views.BaseListCreateAPIView):
    service_class = ProductGroupService
    serializer_class = ProductGroupSerializer
    output_serializer_class = ProductGroupParentSerializer

    def get_queryset(self):
        """
        :return:
        """
        service = self.service_class(
            tenant_code=self.request.tenant_code, site_profile=self.request.site_profile
        )
        query_params_dict = self.prepare_query_params_dict()
        show_all = query_params_dict.get("show_all", None)
        if self.request.user:
            query_params_dict["user"] = self.request.user
        if show_all:
            query_params_dict["parent__isnull"] = "true"
            query_params_dict["tenant_code"] = self.request.user.tenant_code
            qs = service.list(**query_params_dict)
        else:
            qs = service.list_by_catalog(**query_params_dict)
        return qs.order_by("-created_at")


class ProductGroupRetrieveUpdateDeleteAPIView(
    api_views.BaseRetrieveUpdateDestroyAPIView
):
    service_class = ProductGroupService
    serializer_class = ProductGroupSerializer
    output_serializer_class = ProductGroupParentSerializer

    def get_object(self):
        try:
            obj = self.service_class(
                tenant_code=self.request.tenant_code,
                site_profile=self.request.site_profile,
            ).read_by_code(
                code_value=self.kwargs["code"], tenant_code=self.request.tenant_code
            )
            return obj
        except ObjectDoesNotExist:
            raise BadRequestException(message="Invalid object id")


class ProductsByProductGroupAPIView(api_views.BaseListAPIView):
    service_class = ProductGroupService
    product_service = ProductService
    output_serializer_class = ProductListSerializer
    read_by = "code"

    def get_object(self):
        service = self.service_class(
            tenant_code=self.request.tenant_code, site_profile=self.request.site_profile
        )
        if self.read_by == "code":
            try:
                code = self.kwargs.get("code")
                return service.read_by_code(code_value=code)
            except Exception as e:
                raise BadRequestException(message=f"{e}")

    def get_queryset(self):
        qs = []
        product_group = self.get_object()
        product_filter = {
            "is_available": True,
            "tenant_code": self.request.tenant_code,
        }
        qs = product_group.primary_products.filter(**product_filter).order_by("id")
        return qs


class RelatedProductListAPIView(ProductAPIMixin, api_views.BaseListAPIView):
    service_class = ProductService
    serializer_class = RelationProductSerializer

    def get_queryset(self):
        _product = self.get_product()
        query_params_dict = self.prepare_query_params_dict()
        if query_params_dict.get("group-response", None):
            service = self.service_class(
                tenant_code=self.request.tenant_code,
                site_profile=self.request.site_profile,
            )
            return service.get_related_products_in_groups(product=_product)
        return _product.relation_product.filter(tenant_code=self.request.tenant_code)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if self.request.query_params.get("group-response", None):
            response = Response(queryset)
            response.data.update({"meta": {"device_name": self.get_product().name}})
            return response
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class MandatoryProductListAPIView(ProductAPIMixin, api_views.BaseListAPIView):
    service_class = ProductService
    serializer_class = RelationProductSerializer

    def get_contact(self):
        user_service = UserService(
            tenant_code=self.request.tenant_code, site_profile=self.request.site_profile
        )
        contact = None

        if not user_service.is_external(user=self.request.user):
            contact_uuid = self.request.query_params.get("contact_uuid", None)
            if contact_uuid:
                contact = ContactService(
                    tenant_code=self.request.tenant_code,
                    site_profile=self.request.site_profile,
                ).get_contact(uuid=contact_uuid)

        if not contact:
            contact = user_service.get_contact(user=self.request.user)

        return contact

    def get_queryset(self):
        _product = self.get_product()
        query_params_dict = self.prepare_query_params_dict()
        if query_params_dict.get("group-response", None):
            service = self.service_class(
                tenant_code=self.request.tenant_code,
                site_profile=self.request.site_profile,
            )
            return service.get_related_mandatory_products_in_groups(
                product=_product, contact=self.get_contact()
            )
        return _product.relation_product.filter(tenant_code=self.request.tenant_code)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if self.request.query_params.get("group-response", None):
            response = Response(queryset)
            return response
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ProductAttributesAPIView(api_views.BaseListAPIView):
    service_class = ProductService
    output_serializer_class = ProductDetailAttributeSerializer
    read_by = "code"

    def get(self, request, *args, **kwargs):
        product_instance = Product.objects.none()
        product_attr_service = ProductAttributeService(
            tenant_code=request.tenant_code, site_profile=request.site_profile
        )
        product_attributes = product_attr_service.get_product_attributes(
            product_code=kwargs["code"]
        )
        product_instance.product_attributes = product_attributes
        output_serializer = self.output_serializer_class(product_instance)
        return Response(data=output_serializer.data, status=status.HTTP_200_OK)
