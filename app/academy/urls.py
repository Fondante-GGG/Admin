
from django.urls import path
from app.academy.views import settings, AboutView, courses, students_page

urlpatterns = [
    path('', settings, name="settings"),
    path("about/", AboutView.as_view(), name='about'),
    path("courses/", courses, name='courses'), 
    path('students/', students_page, name='student')
    

]
