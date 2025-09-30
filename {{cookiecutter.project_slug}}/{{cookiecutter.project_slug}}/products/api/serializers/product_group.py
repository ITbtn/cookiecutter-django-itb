from rest_framework import serializers

from {{cookiecutter.project_slug}}.products.models import PageLayout, ProductGroup


class PageLayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageLayout
        fields = [
            "code",
            "description",
        ]


class ProductGroupSerializer(serializers.ModelSerializer):
    page_layout = PageLayoutSerializer(read_only=True)

    class Meta:
        model = ProductGroup
        fields = "__all__"
        ref_name = "group_serializer_for_generic_product"


class ProductGroupParentSerializer(ProductGroupSerializer):
    sub_groups = serializers.SerializerMethodField()
    parent_details = serializers.SerializerMethodField()

    class Meta:
        model = ProductGroup
        fields = "__all__"

    def get_sub_groups(self, obj):
        # get sub_groups recursively
        qs = obj.productgroup_set.all()
        if qs:
            return self.__class__(qs, many=True).data
        else:
            return []

    def get_parent_details(self, obj):
        parent_obj = obj.parent
        if parent_obj:
            return ProductGroupSerializer(parent_obj).data
        else:
            return {}
