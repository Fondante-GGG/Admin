from django.contrib import admin

from app.academy.models import (
    Settings,
    Contacts,
    Achievement,
    Teacher,
    AboutPage,
    AboutObjects,
    AboutObjects2,
    CoursesProgram,
    Courses,
    CoursesModel,
    CoursesPage,
    CourseApplication,
    TypeCourse,
    Students,
    AboutStudents,
    Address,
    Feedback,
)
from app.settings.admin_site import crm_admin_site


def _crm_role(user) -> str:
    role = getattr(user, "role", "") or ""
    return "Администратор" if role == "Админ" else role


class SiteSettingsAdminMixin:
    """Права на контент сайта по роли CRM, без отдельных Django-permissions."""

    site_settings_roles = frozenset({"Администратор", "Менеджер", "Админ"})

    def _can_manage_site(self, request) -> bool:
        user = request.user
        if not user.is_authenticated or not user.is_active or not user.is_staff:
            return False
        if user.is_superuser:
            return True
        return _crm_role(user) in self.site_settings_roles

    def has_module_permission(self, request):
        return self._can_manage_site(request)

    def has_view_permission(self, request, obj=None):
        return self._can_manage_site(request)

    def has_add_permission(self, request):
        return self._can_manage_site(request)

    def has_change_permission(self, request, obj=None):
        return self._can_manage_site(request)

    def has_delete_permission(self, request, obj=None):
        return self._can_manage_site(request)


class SiteSettingsChangeListMixin:
    change_list_template = "admin/academy_changelist.html"


@admin.register(Settings, site=crm_admin_site)
class SettingsAdmin(SiteSettingsAdminMixin, SiteSettingsChangeListMixin, admin.ModelAdmin):
    list_display = ("title_banner",)


@admin.register(Contacts, site=crm_admin_site)
class ContactsAdmin(SiteSettingsAdminMixin, SiteSettingsChangeListMixin, admin.ModelAdmin):
    list_display = ("email", "phone_numbers")

    class AddressInline(admin.TabularInline):
        model = Address
        extra = 1

    inlines = [AddressInline]


@admin.register(AboutPage, site=crm_admin_site)
class AboutPageAdmin(SiteSettingsAdminMixin, SiteSettingsChangeListMixin, admin.ModelAdmin):
    list_display = ("title", "title_banner")


@admin.register(AboutObjects, site=crm_admin_site)
class AboutObjectsAdmin(SiteSettingsAdminMixin, SiteSettingsChangeListMixin, admin.ModelAdmin):
    list_display = ("title",)


@admin.register(AboutObjects2, site=crm_admin_site)
class AboutObjects2Admin(SiteSettingsAdminMixin, SiteSettingsChangeListMixin, admin.ModelAdmin):
    list_display = ("title",)


@admin.register(TypeCourse, site=crm_admin_site)
class TypeCourseAdmin(SiteSettingsAdminMixin, SiteSettingsChangeListMixin, admin.ModelAdmin):
    list_display = ("title",)


class AchievementInline(admin.TabularInline):
    model = Achievement
    extra = 1


@admin.register(Teacher, site=crm_admin_site)
class TeacherAdmin(SiteSettingsAdminMixin, SiteSettingsChangeListMixin, admin.ModelAdmin):
    list_display = ("name", "experience")
    inlines = [AchievementInline]


class CoursesProgramInline(admin.TabularInline):
    model = CoursesProgram
    extra = 1


@admin.register(Courses, site=crm_admin_site)
class CoursesAdmin(SiteSettingsAdminMixin, SiteSettingsChangeListMixin, admin.ModelAdmin):
    list_display = ("title", "direction", "price", "monthly_price")
    inlines = [CoursesProgramInline]


@admin.register(CoursesModel, site=crm_admin_site)
class CoursesModelAdmin(SiteSettingsAdminMixin, SiteSettingsChangeListMixin, admin.ModelAdmin):
    list_display = ("courses",)


@admin.register(CoursesPage, site=crm_admin_site)
class CoursesPageAdmin(SiteSettingsAdminMixin, SiteSettingsChangeListMixin, admin.ModelAdmin):
    list_display = ("title",)


@admin.register(CourseApplication, site=crm_admin_site)
class CourseApplicationAdmin(SiteSettingsAdminMixin, SiteSettingsChangeListMixin, admin.ModelAdmin):
    list_display = ("full_name", "course", "phone", "created_at")
    list_filter = ("created_at",)
    readonly_fields = ("created_at",)


@admin.register(Students, site=crm_admin_site)
class StudentsAdmin(SiteSettingsAdminMixin, SiteSettingsChangeListMixin, admin.ModelAdmin):
    list_display = ("title", "title2")


@admin.register(AboutStudents, site=crm_admin_site)
class AboutStudentsAdmin(SiteSettingsAdminMixin, SiteSettingsChangeListMixin, admin.ModelAdmin):
    list_display = ("title", "release_year", "description")
    list_filter = ("release_year",)


@admin.register(Feedback, site=crm_admin_site)
class FeedbackAdmin(SiteSettingsAdminMixin, SiteSettingsChangeListMixin, admin.ModelAdmin):
    list_display = ("name", "phone", "email", "created_at")
    readonly_fields = ("created_at",)
