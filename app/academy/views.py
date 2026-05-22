import json
import re

import requests
from django.conf import settings as st
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from app.academy.models import AboutObjects, AboutObjects2, AboutPage, AboutStudents, Contacts, CourseApplication, Courses, CoursesModel, CoursesPage, Feedback, Settings, Students, Teacher, TypeCourse
from app.settings.models import Lead, Organization


def _plain_text(value: str) -> str:
    return re.sub(r"\s+", " ", strip_tags(value or "")).strip()


def _extract_phone_number(*values: str) -> str:
    for value in values:
        if not value:
            continue
        match = re.search(r"(\+?\d[\d\s()\-]{7,}\d)", value)
        if match:
            return re.sub(r"[^\d+]", "", match.group(1))[:64]
    return ""


def _first_public_organization():
    return Organization.objects.order_by("id").first()


def _match_course(message: str, courses: list[Courses]) -> Courses | None:
    normalized_message = message.lower()
    best_match = None
    best_score = 0

    for course in courses:
        tokens = re.findall(r"[\w+]+", f"{course.title} {course.direction}".lower())
        long_tokens = {token for token in tokens if len(token) >= 4}
        score = sum(1 for token in long_tokens if token in normalized_message)
        if course.title.lower() in normalized_message:
            score += 3
        if score > best_score:
            best_score = score
            best_match = course

    return best_match if best_score > 0 else None


def _course_overview(course: Courses) -> str:
    programs = [
        _plain_text(program.title)
        for program in course.programs.all()[:3]
        if _plain_text(program.title)
    ]
    programs_text = f" Основные темы: {', '.join(programs)}." if programs else ""
    return (
        f"{course.title}: {course.monthly_price} сом/мес, "
        f"полная стоимость {course.discounted_price} сом, "
        f"длительность {course.duration_months} мес.{programs_text}"
    )


def _courses_reply(courses: list[Courses]) -> str:
    if not courses:
        return "Сейчас список курсов временно недоступен. Оставьте номер телефона, и менеджер подскажет актуальные варианты."
    course_titles = ", ".join(course.title for course in courses[:6])
    return f"Сейчас доступны курсы: {course_titles}. Если нужен конкретный курс, напишите его название, и я подскажу цену и длительность."


def _pricing_reply(courses: list[Courses]) -> str:
    if not courses:
        return "По ценам лучше уточнить у менеджера. Можете оставить номер телефона прямо в чате."
    lines = [f"{course.title}: {course.monthly_price} сом/мес" for course in courses[:4]]
    return "По основным курсам цены такие: " + "; ".join(lines) + "."


def _contacts_reply(contact: Contacts | None) -> str:
    if not contact:
        return "Контакты сейчас недоступны. Оставьте сообщение и номер телефона, и менеджер свяжется с вами."

    parts = []
    phone_text = _plain_text(contact.phone_numbers)
    if phone_text:
        parts.append(f"Телефон: {phone_text}.")
    if contact.email:
        parts.append(f"Email: {contact.email}.")
    addresses = [_plain_text(address.address) for address in contact.addresses.all() if _plain_text(address.address)]
    if addresses:
        parts.append(f"Адрес: {'; '.join(addresses[:2])}.")
    return " ".join(parts)


def _teachers_reply(teachers: list[Teacher]) -> str:
    if not teachers:
        return "Информация о преподавателях скоро появится. Пока можете оставить вопрос, и администратор ответит вручную."
    names = ", ".join(teacher.name for teacher in teachers[:5])
    return f"У нас преподаватели: {names}. Если хотите, могу подсказать курс под вашу цель."


def _build_chatbot_reply(message: str, courses: list[Courses], contact: Contacts | None, teachers: list[Teacher]) -> str:
    text = message.lower()
    matched_course = _match_course(text, courses)

    if any(word in text for word in ("привет", "здравствуйте", "салам", "hello", "добрый")):
        return "Здравствуйте! Я онлайн-помощник American Dream. Могу подсказать по курсам, ценам, длительности, преподавателям и контактам."

    if matched_course and any(word in text for word in ("цена", "стоим", "сколько", "курс", "ielts", "sat", "toefl", "duolingo", "english", "англий")):
        return _course_overview(matched_course)

    if any(word in text for word in ("контакт", "телефон", "whatsapp", "почта", "email", "адрес", "где вы")):
        return _contacts_reply(contact)

    if any(word in text for word in ("курс", "программ", "обучен", "направлен")):
        return _courses_reply(courses)

    if any(word in text for word in ("цена", "стоим", "сколько стоит", "оплата", "сом")):
        return _pricing_reply(courses)

    if any(word in text for word in ("длитель", "месяц", "сколько идет", "сколько длится")):
        if matched_course:
            return f"Курс {matched_course.title} длится {matched_course.duration_months} мес. Полная стоимость {matched_course.discounted_price} сом."
        return "Длительность зависит от курса. Напишите название курса, и я сразу подскажу сроки."

    if any(word in text for word in ("распис", "когда занятия", "время", "дни")):
        if matched_course:
            return f"Расписание для курса {matched_course.title} зависит от набора группы. Оставьте номер телефона, и менеджер отправит точное время."
        return "Расписание зависит от курса и группы. Напишите нужный курс или оставьте номер телефона для связи."

    if any(word in text for word in ("учител", "преподав", "ментор")):
        return _teachers_reply(teachers)

    if any(word in text for word in ("запис", "оставить заявку", "хочу учиться", "поступить")):
        return "Можно оставить номер телефона прямо в этом чате или заполнить форму на странице. Я сохраню обращение в лиды, и менеджер свяжется с вами."

    return (
        "Я работаю локально без внешних ИИ и отвечаю по данным сайта. "
        "Могу помочь с курсами, ценами, длительностью, преподавателями и контактами. "
        "Если вопрос нестандартный, оставьте номер телефона, и менеджер ответит вручную."
    )


def _append_conversation(log: str, user_message: str, bot_reply: str) -> str:
    stamp = timezone.localtime().strftime("%d.%m.%Y %H:%M")
    chunk = f"[{stamp}] Клиент: {user_message}\n[{stamp}] Бот: {bot_reply}"
    return f"{log.strip()}\n\n{chunk}".strip() if log else chunk


def _save_chat_lead(session_key: str, name: str, phone: str, email: str, message: str, reply: str) -> Lead:
    lead = Lead.objects.filter(session_key=session_key, source="website_chat", is_archived=False).first()
    visitor_name = name or "Посетитель сайта"

    if lead is None:
        lead = Lead.objects.create(
            organization=_first_public_organization(),
            full_name=visitor_name,
            phone_number=phone,
            email=email,
            source="website_chat",
            session_key=session_key,
            message=message,
            bot_reply=reply,
            conversation_log=_append_conversation("", message, reply),
        )
        return lead

    if name:
        lead.full_name = name
    elif not lead.full_name:
        lead.full_name = visitor_name
    if phone:
        lead.phone_number = phone
    if email:
        lead.email = email
    lead.message = message
    lead.bot_reply = reply
    lead.conversation_log = _append_conversation(lead.conversation_log, message, reply)
    if not lead.organization:
        lead.organization = _first_public_organization()
    lead.save(
        update_fields=[
            "organization",
            "full_name",
            "phone_number",
            "email",
            "message",
            "bot_reply",
            "conversation_log",
        ]
    )
    return lead

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


@require_POST
def chat_message(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        payload = request.POST

    message = (payload.get("message") or "").strip()
    if not message:
        return JsonResponse({"error": "Пустое сообщение."}, status=400)

    if not request.session.session_key:
        request.session.create()

    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip()
    phone = _extract_phone_number((payload.get("phone") or "").strip(), message)

    courses = list(Courses.objects.select_related("direction").prefetch_related("programs").all())
    contact = Contacts.objects.prefetch_related("addresses").order_by("-id").first()
    teachers = list(Teacher.objects.order_by("id")[:6])
    reply = _build_chatbot_reply(message, courses, contact, teachers)
    lead = _save_chat_lead(request.session.session_key, name, phone, email, message, reply)

    return JsonResponse(
        {
            "reply": reply,
            "lead_id": lead.pk,
        }
    )


class AboutView(TemplateView):
    template_name = 'website/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["about_id"] = AboutPage.objects.latest("id")
        settings_obj = Settings.objects.latest("id")
        context["settings_obj"] = settings_obj
        context["settings"] = settings_obj
        context["contact"] = Contacts.objects.prefetch_related("addresses").order_by("-id").first()
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
