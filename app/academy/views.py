from django.shortcuts import render
from app.academy.models import Settings, Contacts, Teacher, AboutPage, AboutObjects, AboutObjects2, Courses, Feedback, CoursesModel, CoursesPage, CourseApplication, TypeCourse, Students, AboutStudents
from django.core.mail import send_mail
from django.conf import settings as st
from django.views.generic import TemplateView
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
import requests
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt

def settings(request):
    if request.method == 'POST':
        print("\n== POST получен ==")

        # основные поля
        name_register = request.POST.get('name_register')
        phone_register = request.POST.get('phone_register')
        email_register = request.POST.get('email_register')
        course_id = request.POST.get('course_id')

        # новые поля анкеты
        grade = request.POST.get('grade')
        student_phone = request.POST.get('student_phone')
        parent_phone = request.POST.get('parent_phone')
        reason = request.POST.get('reason')
        plans = request.POST.get('plans')
        study_time = request.POST.get('study_time')
        skills = request.POST.get('skills')
        ready = request.POST.get('ready')

        if name_register and phone_register and course_id:
            try:
                course = get_object_or_404(Courses, id=course_id)

                app = CourseApplication.objects.create(
                    full_name=name_register,
                    phone=phone_register,
                    email=email_register,
                    course=course,
                    grade=grade,
                    student_phone=student_phone,
                    parent_phone=parent_phone,
                    reason=reason,
                    plans=plans,
                    study_time=study_time,
                    skills=skills,
                    ready=ready,
                )

                # WhatsApp уведомление
                whatsapp_number = '996504736767'
                api_key = '9478477'
                message = (
                    f"📚 Новая заявка на курс:\n"
                    f"👤 {app.full_name}\n"
                    f"🎓 Класс/Университет: {app.grade}\n"
                    f"📞 Тел. ученика: {app.student_phone}\n"
                    f"📱 Тел. родителя: {app.parent_phone}\n\n"
                    f"❓ Причина: {app.reason}\n"
                    f"🌍 Планы: {app.plans}\n"
                    f"⏱ Время: {app.study_time}\n"
                    f"📝 Навыки: {app.skills}\n"
                    f"✅ Готов посещать: {app.ready}\n\n"
                    f"📧 Email: {app.email}\n"
                    f"📲 Телефон: {app.phone}\n"
                    f"📖 Курс: {app.course.title}"
                )
                try:
                    requests.get(
                        f"https://api.callmebot.com/whatsapp.php?phone={whatsapp_number}&text={requests.utils.quote(message)}&apikey={api_key}"
                    )
                except Exception as e:
                    print(f"Ошибка отправки WhatsApp: {e}")

            except Exception as e:
                print(f"Ошибка сохранения: {e}")
            return redirect('/')   # ✅ возврат даже при ошибке

        # если это не анкета, а просто обратная связь
        else:
            name = request.POST.get('name')
            phone = request.POST.get('phone')
            email = request.POST.get('email')

            if name and phone:
                Feedback.objects.create(name=name, phone=phone, email=email)

                subject = 'Новая обратная связь'
                message = f'Имя: {name}\nТелефон: {phone}\nEmail: {email}'
                recipient_list = ['aruukelisa@gmail.com']
                send_mail(subject, message, st.DEFAULT_FROM_EMAIL, recipient_list)

            return redirect('/')

    # GET-запрос → рендерим главную
    settings_obj = Settings.objects.latest("id")
    contact = Contacts.objects.latest("id")
    teachers = Teacher.objects.prefetch_related('achievements')
    courses = Courses.objects.prefetch_related('programs', 'modals')
    model_all_dict = {model.courses.id: model for model in CoursesModel.objects.all()}

    return render(request, 'website/index.html', {
        'settings': settings_obj,
        'contact': contact,
        'teachers': teachers,
        'courses': courses,
        'model_all': model_all_dict
    })


class AboutView(TemplateView):
    template_name = 'website/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["about_id"] = AboutPage.objects.latest("id")
        context["settings_obj"] = Settings.objects.latest("id")
        objs1 = list(AboutObjects.objects.all())
        objs2 = list(AboutObjects2.objects.all())
        combined = []
        max_len = max(len(objs1), len(objs2))
        for i in range(max_len):
            if i < len(objs1):
                combined.append({'item': objs1[i], 'reverse': False, 'color': 'grey'})
            if i < len(objs2):
                combined.append({'item': objs2[i], 'reverse': True, 'color': 'green'})
        context["about_combined"] = combined
        return context

def courses(request):
    courses_page = CoursesPage.objects.latest("id")
    courses_all = Courses.objects.select_related('direction').prefetch_related('programs', 'modals')
    directions = TypeCourse.objects.all()
    settings_obj = Settings.objects.latest("id")
    return render(request, 'website/courses.html', {
        'courses_page': courses_page,
        'courses_all': courses_all,
        'directions': directions,
        'settings': settings_obj,
    })

def students_page(request):
    student = Students.objects.first()
    about_students = AboutStudents.objects.all()

    # Получаем выбранный год из GET-параметра
    selected_year = request.GET.get('year', '')

    if selected_year:
        about_students = about_students.filter(release_year=selected_year)

    # Список всех годов для фильтра
    years = AboutStudents.objects.values_list('release_year', flat=True).distinct().order_by('release_year')

    context = {
        'title': student.title if student else '',
        'description': student.description if student else '',
        'title2': student.title2 if student else '',
        'description2': student.description2 if student else '',
        'about_student': about_students,
        'years': years,
        'selected_year': selected_year
    }
    return render(request, 'website/student.html', context)
