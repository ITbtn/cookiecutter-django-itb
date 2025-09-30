from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext as _
from simple_history.admin import SimpleHistoryAdmin


class BaseReadOnlyAdmin(admin.ModelAdmin):
    readonly_fields = ["created_by", "updated_by", "created_at", "updated_at"]
    autocomplete_fields = []
    search_fields = []

    def save_model(self, request, obj, form, change):
        """
        Given a model instance save it to the database.
        """
        if not change:
            obj.created_by = request.user
        else:
            obj.updated_by = request.user
        obj.save()

    def get_tenant_code(self, obj):
        return obj.tenant_code if hasattr(obj, "tenant_code") else ""

    def get_list_display(self, request):
        list_display = super().get_list_display(request)
        # sometimes its set with tuple, as we need to modify it, we convert it to mutable first
        if not isinstance(list_display, list):
            list_display = list(list_display)
        if hasattr(self.model, "tenant_code"):
            return list_display + ["get_tenant_code"]
        return list_display

    def get_list_filter(self, request):
        list_filter = super().get_list_filter(request) or []
        # sometimes its set with tuple or Sequence, as we need to modify it, we convert it to mutable first
        if not isinstance(list_filter, list):
            list_filter = list(list_filter)
        if hasattr(self.model, "tenant_code") and "tenant_code" not in list_filter:
            list_filter.append("tenant_code")
        return list_filter

    get_tenant_code.short_description = "Tenant Code"


class BaseHistoryAdmin(SimpleHistoryAdmin):
    history_list_display = ["changed_fields", "list_changes"]

    def changed_fields(self, obj):
        fields = ""
        if obj.prev_record:
            delta = obj.diff_against(obj.prev_record)
            for change in delta.changes:
                fields += f"<strong>{change.field}</strong> <br/>"
            return format_html(fields)
        return None

    def list_changes(self, obj):
        fields = ""
        if obj.prev_record:
            delta = obj.diff_against(obj.prev_record)

            for change in delta.changes:
                fields += (
                    f"<strong>{change.field}</strong> changed from <span style='background-color:#ffb5ad'>"
                    f"{change.old}</span> to <span style='background-color:#b3f7ab'>{change.new}</span>. <br/>"
                )
            return format_html(fields)
        return None

    def get_tenant_code(self, obj):
        return obj.tenant_code if hasattr(obj, "tenant_code") else ""

    def get_list_display(self, request):
        list_display = super().get_list_display(request)
        # sometimes its set with tuple, as we need to modify it, we convert it to mutable first
        if isinstance(list_display, tuple):
            list_display = list(list_display)
        if hasattr(self.model, "tenant_code"):
            return list_display + ["get_tenant_code"]
        return list_display

    def get_list_filter(self, request):
        list_filter = super().get_list_filter(request) or []
        # sometimes its set with tuple, as we need to modify it, we convert it to mutable first
        if isinstance(list_filter, tuple):
            list_filter = list(list_filter)
        if hasattr(self.model, "tenant_code") and "tenant_code" not in list_filter:
            list_filter.append("tenant_code")
        return list_filter

    get_tenant_code.short_description = "Tenant Code"


class BaseReadonlyHistoryAdmin(BaseHistoryAdmin):
    readonly_fields = ["created_by", "updated_by", "created_at", "updated_at"]
    autocomplete_fields = []
    search_fields = []
    history_list_display = ["changed_fields", "list_changes"]

    def save_model(self, request, obj, form, change):
        """
        Given a model instance save it to the database.
        """
        if not change:
            obj.created_by = request.user
        else:
            obj.updated_by = request.user
        obj.save()


class BaseStackedInline(admin.StackedInline):
    readonly_fields = ["created_by", "updated_by", "created_at", "updated_at"]
    extra = 1


class BaseTabularInline(admin.TabularInline):
    readonly_fields = ["created_by", "updated_by", "created_at", "updated_at"]
