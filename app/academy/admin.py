from django.contrib import admin
from app.academy.models import (
    Settings, Contacts, Achievement, Teacher, AboutPage,
    AboutObjects, AboutObjects2, CoursesProgram, Courses, CoursesModel,
    CoursesPage, CourseApplication, TypeCourse, Students, AboutStudents, Address
)

admin.site.register(Settings)
admin.site.register(TypeCourse)
admin.site.register(CoursesModel)
admin.site.register(CoursesPage)
admin.site.register(CourseApplication)
admin.site.register(AboutPage)
admin.site.register(AboutObjects)
admin.site.register(AboutObjects2)
admin.site.register(Students)

class AboutStudentsAdmin(admin.ModelAdmin):
    list_display = ('title', 'release_year', 'description')
    list_filter = ('release_year',)  # Добавляет фильтр по году в админке

admin.site.register(AboutStudents, AboutStudentsAdmin)

class AchievementInline(admin.TabularInline):
    model = Achievement
    extra = 1

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name', 'experience')
    inlines = [AchievementInline]

class CoursesProgramInline(admin.TabularInline):
    model = CoursesProgram
    extra = 1

@admin.register(Courses)
class CoursesAdmin(admin.ModelAdmin):
    list_display = ('title', 'direction', 'price', 'monthly_price')
    inlines = [CoursesProgramInline]

class AddressInline(admin.TabularInline):
    model = Address
    extra = 1

@admin.register(Contacts)
class ContactsAdmin(admin.ModelAdmin):
    list_display = ("email", "phone_numbers")
    inlines = [AddressInline]