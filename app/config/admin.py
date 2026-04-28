from django.contrib import admin

from app.settings.admin_site import crm_admin_site

from .models import CRMAbout, CRMBilling, CRMSetting


@admin.register(CRMSetting, site=crm_admin_site)
class CRMSettingAdmin(admin.ModelAdmin):
    list_display = ("key", "value", "updated_at")
    search_fields = ("key", "value")


@admin.register(CRMBilling, site=crm_admin_site)
class CRMBillingAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "expires_at", "created_at")
    list_filter = ("status",)
    search_fields = ("name",)


@admin.register(CRMAbout, site=crm_admin_site)
class CRMAboutAdmin(admin.ModelAdmin):
    list_display = ("title", "updated_at")
    search_fields = ("title", "body")

