from django.contrib import admin


class AuditAdmin(admin.ModelAdmin):
    """Stamps created_by/updated_by from the admin user."""

    def save_model(self, request, obj, form, change):
        if not change and hasattr(obj, "created_by_id"):
            obj.created_by = request.user
        if hasattr(obj, "updated_by_id"):
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)
