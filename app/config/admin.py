from django.contrib import admin
from django.db import models
from django.shortcuts import redirect
from django.urls import reverse

from app.settings.admin_site import crm_admin_site

from .models import CRMAbout, CRMBilling, CRMSetting


def _role(user) -> str:
    role = getattr(user, "role", "") or ""
    return "Администратор" if role == "Админ" else role


class ConfigRoleRestrictedAdminMixin:
    allowed_roles: set[str] | None = None

    def _has_crm_access(self, request) -> bool:
        user = request.user
        role = _role(user)
        return bool(
            user.is_authenticated
            and user.is_active
            and user.is_staff
            and (self.allowed_roles is None or role in self.allowed_roles)
        )

    def has_module_permission(self, request):
        return self._has_crm_access(request)

    def has_view_permission(self, request, obj=None):
        return self._has_crm_access(request)

    def has_add_permission(self, request):
        return self._has_crm_access(request)

    def has_change_permission(self, request, obj=None):
        return self._has_crm_access(request)

    def has_delete_permission(self, request, obj=None):
        return self._has_crm_access(request)

    def get_model_perms(self, request):
        if not self.has_module_permission(request):
            return {}
        return {
            "add": self.has_add_permission(request),
            "change": self.has_change_permission(request),
            "delete": self.has_delete_permission(request),
            "view": self.has_view_permission(request),
        }


@admin.register(CRMSetting, site=crm_admin_site)
class CRMSettingAdmin(ConfigRoleRestrictedAdminMixin, admin.ModelAdmin):
    allowed_roles = {"Администратор", "Менеджер"}
    list_display = ("key", "value", "updated_at")
    search_fields = ("key", "value")

    def changelist_view(self, request, extra_context=None):
        return redirect(reverse("crm_admin:settings_index"))


@admin.register(CRMBilling, site=crm_admin_site)
class CRMBillingAdmin(ConfigRoleRestrictedAdminMixin, admin.ModelAdmin):
    allowed_roles = {"Администратор", "Менеджер"}
    list_display = ("name", "status", "expires_at", "created_at")
    list_filter = ("status",)
    search_fields = ("name",)


@admin.register(CRMAbout, site=crm_admin_site)
class CRMAboutAdmin(ConfigRoleRestrictedAdminMixin, admin.ModelAdmin):
    allowed_roles = {"Администратор", "Менеджер"}
    list_display = ("title", "updated_at")
    search_fields = ("title", "body")
    formfield_overrides = {
        models.TextField: {"widget": admin.widgets.AdminTextareaWidget(attrs={"rows": 4})},
    }

    fieldsets = (
        ("Заголовок", {"fields": ("title",)}),
        ("О нас (карточка)", {"fields": ("about_subtitle", "about_text", "about_site_url")}),
        ("Оставить отзыв (карточка)", {"fields": ("feedback_phone", "feedback_whatsapp", "feedback_email", "feedback_person")}),
        ("Контакты (карточка)", {"fields": ("contacts_text", "contacts_phone", "contacts_whatsapp", "contacts_email")}),
        ("Политика конфиденциальности", {"fields": ("privacy_text",)}),
        ("Пользовательское соглашение", {"fields": ("agreement_text",)}),
        ("Старое поле (если нужно)", {"fields": ("body",), "classes": ("collapse",)}),
    )
