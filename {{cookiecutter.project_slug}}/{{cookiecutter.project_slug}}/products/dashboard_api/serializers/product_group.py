from rest_framework import serializers

from {{cookiecutter.project_slug}}.common.serializers.base import LogBaseSerializer
from {{cookiecutter.project_slug}}.products.dashboard_api.serializers.page_layout import (
    PageLayoutsSerializer,
)
from {{cookiecutter.project_slug}}.products.models import ProductGroup


class BasicProductGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductGroup
        fields = [
            "code",
            "name",
            "description",
        ]


class ProductGroupSerializer(serializers.ModelSerializer):
    page_layout_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, write_only=True
    )

    class Meta:
        model = ProductGroup
        fields = "__all__"
        ref_name = "group_serializer_for_generic_product"


class ProductGroupInputSerializer(serializers.ModelSerializer):
    # auto generate if not provided
    code = serializers.CharField(required=False, allow_null=False, allow_blank=False)
    slug = serializers.CharField(required=False, allow_blank=False)
    parent = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, write_only=True
    )
    page_layout_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, write_only=True
    )

    class Meta:
        model = ProductGroup
        fields = "__all__"


class ProductGroupParentSerializer(LogBaseSerializer, ProductGroupSerializer):
    parent = BasicProductGroupSerializer()
    sub_groups = serializers.SerializerMethodField()
    page_layout = PageLayoutsSerializer(required=False)

    class Meta:
        model = ProductGroup
        fields = [
            "code",
            "name",
            "is_available",
            "description",
            "min_product",
            "max_product",
            "sort_order",
            "parent",
            "sub_groups",
            "page_layout",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
            "purchase_financial_number",
            "sales_financial_number",
        ]
        ref_name = "dashboard_product_group_parent_serializer"

    def get_sub_groups(self, obj):
        return BasicProductGroupSerializer(instance=obj.subgroups.all(), many=True).data
