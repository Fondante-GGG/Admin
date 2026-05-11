from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from app.settings.admin_site import crm_admin_site
from app.settings.views import (
    portal_login, mentor_dashboard, student_dashboard, parent_dashboard,
    error_404, error_500, error_403, error_401,
)

urlpatterns = [
    path('admin/', crm_admin_site.urls),
    path('login/', portal_login, name='portal_login'),
    path('portal/mentor/', mentor_dashboard, name='mentor_dashboard'),
    path('portal/student/', student_dashboard, name='student_dashboard'),
    path('portal/parent/', parent_dashboard, name='parent_dashboard'),
]

handler404 = "app.settings.views.error_404"
handler500 = "app.settings.views.error_500"
handler403 = "app.settings.views.error_403"

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
