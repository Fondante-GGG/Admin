
from django.urls import path
from app.academy.views import AboutView, chat_message, courses, settings, students_page

urlpatterns = [
    path('', settings, name="settings"),
    path('chat/message/', chat_message, name='chat_message'),
    path("about/", AboutView.as_view(), name='about'),
    path("courses/", courses, name='courses'), 
    path('students/', students_page, name='student')
    

]
