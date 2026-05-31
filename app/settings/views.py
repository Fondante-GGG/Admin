from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie

from app.settings.models import (
    User, Lesson, Exam, Cursues, GroupCourse, IndividualCourse, Mentor,
    LessonLink, StudentGrade, Student, Schedule,
    CurriculumModule, Parent,
)


@never_cache
@ensure_csrf_cookie
def portal_login(request):
    error = None
    logged_in_user = request.user if request.user.is_authenticated else None

    if request.method == "POST":
        try:
            username = request.POST.get("username", "").strip()
            password = request.POST.get("password", "").strip()
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return _redirect_by_role(user)
            else:
                from app.settings.models import User
                try:
                    u = User.objects.get(username=username)
                    print(f"[DEBUG] user found: {u.username}, is_active={u.is_active}, check_pass={u.check_password(password)}")
                except User.DoesNotExist:
                    print(f"[DEBUG] user not found: {username}")
                error = "Неверное имя пользователя или пароль"
        except Exception:
            error = "Ошибка сервера при входе. Попробуйте позже."

    return render(request, "portal/login.html", {"error": error, "logged_in_user": logged_in_user})


@never_cache
def portal_logout(request):
    auth_logout(request)
    return redirect("portal_login")


def _redirect_by_role(user: User):
    role = getattr(user, "role", "")
    if role == "Админ" or user.is_superuser:
        return redirect(reverse("crm_admin:index"))
    if role == "Менеджер":
        return redirect(reverse("crm_admin:index"))
    if role == "Ментор" and hasattr(user, "mentor_profile"):
        return redirect("/portal/mentor/")
    if role == "Студент" and hasattr(user, "student"):
        return redirect("/portal/student/")
    if role == "Родитель" and hasattr(user, "parent_profile"):
        return redirect("/portal/parent/")
    return redirect(reverse("crm_admin:index"))


@login_required
def mentor_dashboard(request):
    try:
        if getattr(request.user, "role", "") != "Ментор":
            return render(request, "errors/403.html", status=403)
        
        mentor_profile = Mentor.objects.get(user=request.user)
        
        # Получаем все курсы ментора
        mentor_courses = Cursues.objects.filter(mentors=mentor_profile)
        
        return render(request, "portal/mentor_dashboard.html", {
            "active": "home",
            "groups": mentor_courses,
        })
    except Exception as e:
        print(f"[DEBUG] Error in mentor_dashboard: {e}")
        import traceback
        traceback.print_exc()
        return render(request, "errors/500.html", status=500)


@login_required
def mentor_lessons(request):
    try:
        if getattr(request.user, "role", "") != "Ментор":
            return render(request, "errors/403.html", status=403)
        
        try:
            mentor_profile = request.user.mentor_profile
            print(f"[DEBUG] Mentor profile found: {mentor_profile}")
        except AttributeError:
            print(f"[DEBUG] No mentor profile for user: {request.user.username}")
            return render(request, "portal/mentor_lessons.html", {
                "active": "lessons",
                "group_courses": [],
                "individual_courses": [],
                "exams": [],
                "groups": [],
            })
        
        group_courses = GroupCourse.objects.filter(mentors=mentor_profile).active().order_by('title')
        individual_courses = IndividualCourse.objects.filter(mentors=mentor_profile).active().order_by('title')
        
        exams = Exam.objects.filter(mentor=mentor_profile).active().order_by('-created_at')
        
        print(f"[DEBUG] Found {group_courses.count()} group courses, {individual_courses.count()} individual courses and {exams.count()} exams")
        
        all_courses = list(group_courses) + list(individual_courses)
        
        # Фильтрация по группе
        group_id = request.GET.get('group_id')
        if group_id:
            all_courses = [c for c in all_courses if str(c.id) == group_id]
        
        all_lessons = Lesson.objects.filter(mentor=mentor_profile).select_related('course').order_by('course__title', 'order')
        
        # Фильтрация уроков по группе
        if group_id:
            all_lessons = all_lessons.filter(course_id=group_id)
        
        lessons_by_course = {}
        lessons_with_links = {}
        for lesson in all_lessons:
            if lesson.course:
                if lesson.course not in lessons_by_course:
                    lessons_by_course[lesson.course] = []
                lessons_by_course[lesson.course].append(lesson)
        
        return render(request, "portal/mentor_lessons.html", {
            "active": "lessons",
            "group_courses": group_courses,
            "individual_courses": individual_courses,
            "all_courses": all_courses,
            "lessons_by_course": lessons_by_course,
            "exams": exams,
            "groups": all_courses,
        })
    except Exception as e:
        print(f"[DEBUG] Error in mentor_lessons: {e}")
        import traceback
        traceback.print_exc()
        return render(request, "errors/500.html", status=500)


@login_required
def mentor_schedule(request):
    try:
        if getattr(request.user, "role", "") != "Ментор":
            return render(request, "errors/403.html", status=403)
        
        mentor_profile = Mentor.objects.get(user=request.user)
        
        # Получаем все курсы ментора
        mentor_courses = Cursues.objects.filter(mentors=mentor_profile)
        
        from datetime import date
        import calendar
        
        today = date.today()
        year = today.year
        month = today.month
        
        if request.GET.get('month'):
            try:
                month = int(request.GET.get('month'))
                year = int(request.GET.get('year', year))
            except (ValueError, TypeError):
                month = today.month
                year = today.year
        
        cal = calendar.monthcalendar(year, month)
        month_name = calendar.month_name[month]
        
        schedules = Schedule.objects.filter(
            mentor=mentor_profile,
            is_active=True
        ).select_related('course', 'time_slot').order_by('time_slot__day_of_week', 'time_slot__start_time')
        
        # Фильтрация по группе
        group_id = request.GET.get('group_id')
        if group_id:
            schedules = schedules.filter(course_id=group_id)
        
        schedule_by_date = {}
        
        for schedule in schedules:
            day_of_week = schedule.time_slot.day_of_week
            day_map = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            
            target_weekday = day_map.get(day_of_week)
            if target_weekday is None:
                continue
            
            for week_num, week_days in enumerate(cal):
                for day_num, day_date in enumerate(week_days):
                    if day_date == 0:
                        continue
                    if day_num == target_weekday:
                        date_key = date(year, month, day_date)
                        if date_key not in schedule_by_date:
                            schedule_by_date[date_key] = []
                        schedule_by_date[date_key].append(schedule)
        
        if month == 1:
            prev_month = 12
            prev_year = year - 1
        else:
            prev_month = month - 1
            prev_year = year
        
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year
        
        return render(request, "portal/mentor_schedule.html", {
            "active": "schedule",
            "calendar": cal,
            "month_name": month_name,
            "year": year,
            "month": month,
            "schedule_by_date": schedule_by_date,
            "prev_month": prev_month,
            "prev_year": prev_year,
            "next_month": next_month,
            "next_year": next_year,
            "today": today,
            "groups": mentor_courses,
        })
    except Exception as e:
        print(f"[DEBUG] Error in mentor_schedule: {e}")
        import traceback
        traceback.print_exc()
        return render(request, "errors/500.html", status=500)


@login_required
def mentor_gradebook(request):
    try:
        if getattr(request.user, "role", "") != "Ментор":
            return render(request, "errors/403.html", status=403)
        
        mentor_profile = Mentor.objects.get(user=request.user)
        
        # Получаем все курсы ментора
        mentor_courses = Cursues.objects.filter(mentors=mentor_profile)
        
        # Получаем оценки студентов ментора
        from app.settings.models import StudentGrade
        grades = StudentGrade.objects.filter(
            lesson__course__mentors=mentor_profile
        ).select_related('student', 'lesson', 'student__user').order_by('-created_at')
        
        group_id = request.GET.get('group_id')
        if group_id:
            grades = grades.filter(student__enrollment__course_id=group_id)
        
        attendance_data = {}
        selected_group = None
        lessons_in_course = []
        
        group_id = request.GET.get('group_id')
        if group_id:
            selected_group = mentor_courses.filter(id=group_id).first()
            if selected_group:
                from app.settings.models import Student, Lesson
                students_in_group = Student.objects.filter(
                    enrollment__course=selected_group
                ).select_related('user')
                print(f"Found {students_in_group.count()} students in group {selected_group.title}")
                lessons_in_course = Lesson.objects.filter(
                    course=selected_group
                ).order_by('order')
                
                for student in students_in_group:
                    student_name = f"{student.user.last_name} {student.user.first_name}"
                    
                    # Данные посещаемости (на основе оценок 0/1)
                    attendance_data[student.id] = {
                        'student_name': student_name,
                        'lessons': {},
                        'total': 0
                    }
                    
                    for lesson in lessons_in_course:
                        # Получаем оценку для урока
                        grade = StudentGrade.objects.filter(
                            student=student, 
                            lesson=lesson
                        ).first()
                        
                        if grade:
                            # Посещаемость (1 - присутствовал, 0 - отсутствовал)
                            attendance_data[student.id]['lessons'][lesson.id] = grade.grade
                            attendance_data[student.id]['total'] += grade.grade
                        else:
                            attendance_data[student.id]['lessons'][lesson.id] = 0
        
        return render(request, "portal/mentor_gradebook.html", {
            "active": "gradebook",
            "grades": grades,
            "groups": mentor_courses,
            "selected_group": selected_group,
            "attendance_data": attendance_data,
            "lessons_in_course": lessons_in_course,
        })
    except Exception as e:
        print(f"[DEBUG] Error in mentor_gradebook: {e}")
        import traceback
        traceback.print_exc()
        return render(request, "errors/500.html", status=500)


@login_required
def mentor_students(request):
    try:
        if getattr(request.user, "role", "") != "Ментор":
            return render(request, "errors/403.html", status=403)
        
        mentor_profile = Mentor.objects.get(user=request.user)
        
        # Получаем все курсы ментора
        mentor_courses = Cursues.objects.filter(mentors=mentor_profile)
        
        # Получаем всех студентов ментора через Enrollment (связь Student-Cursues)
        from django.db.models import Q
        students = Student.objects.filter(
            Q(enrollment__course__mentors=mentor_profile) |
            Q(payment__course__mentors=mentor_profile)
        ).distinct().select_related('user')
        
        # Фильтрация по группе
        group_id = request.GET.get('group_id')
        if group_id:
            students = students.filter(
                Q(enrollment__course_id=group_id) |
                Q(payment__course_id=group_id)
            ).distinct()
        
        return render(request, "portal/mentor_students.html", {
            "active": "students",
            "students": students,
            "groups": mentor_courses,
        })
    except Exception as e:
        print(f"[DEBUG] Error in mentor_students: {e}")
        import traceback
        traceback.print_exc()
        return render(request, "errors/500.html", status=500)


def _curriculum_sections_for_course(course, lessons_sorted):
    """Секции аккордеона по месяцам (модулям). Модули показываются даже без уроков."""
    modules = list(
        CurriculumModule.objects.filter(course=course).order_by("order")
    )
    if modules:
        by_module_id = {m.id: [] for m in modules}
        unassigned = []
        for les in lessons_sorted:
            mid = les.curriculum_module_id
            if mid and mid in by_module_id:
                by_module_id[mid].append(les)
            else:
                unassigned.append(les)
        sections = []
        for i, m in enumerate(modules, start=1):
            title_part = m.title.strip() if m.title else ""
            heading = f"Месяц {i}. {title_part}" if title_part else f"Месяц {i}"
            sections.append(
                {
                    "month_index": i,
                    "heading": heading,
                    "lessons": by_module_id[m.id],
                }
            )
        if unassigned:
            sections.append(
                {
                    "month_index": len(modules) + 1,
                    "heading": "Без раздела",
                    "lessons": unassigned,
                }
            )
        return sections
    if lessons_sorted:
        return [
            {
                "month_index": 1,
                "heading": "Учебный план",
                "lessons": lessons_sorted,
            }
        ]
    return []


@login_required
def mentor_curriculum(request):
    try:
        if getattr(request.user, "role", "") != "Ментор":
            return render(request, "errors/403.html", status=403)

        try:
            mentor_profile = Mentor.objects.get(user=request.user)
        except Mentor.DoesNotExist:
            return render(
                request,
                "portal/mentor_curriculum.html",
                {
                    "active": "curriculum",
                    "selected_course": None,
                    "curriculum_sections": [],
                    "invalid_group": False,
                    "needs_group_choice": False,
                    "groups": [],
                    "mentor_profile_missing": True,
                },
            )

        mentor_courses = (
            Cursues.objects.filter(mentors=mentor_profile)
            .order_by("title")
        )

        group_id = (request.GET.get("group_id") or "").strip()

        if not group_id and mentor_courses.count() == 1:
            only = mentor_courses.first()
            return redirect(f"{reverse('mentor_curriculum')}?group_id={only.pk}")

        selected_course = None
        curriculum_sections = []
        invalid_group = False

        if group_id:
            selected_course = mentor_courses.filter(pk=group_id).first()
            if not selected_course:
                invalid_group = True
            else:
                lessons_list = list(
                    Lesson.objects.filter(
                        course=selected_course,
                        is_archived=False,
                    )
                    .select_related("curriculum_module")
                    .order_by("order")
                )
                curriculum_sections = _curriculum_sections_for_course(
                    selected_course, lessons_list
                )

        return render(
            request,
            "portal/mentor_curriculum.html",
            {
                "active": "curriculum",
                "selected_course": selected_course,
                "curriculum_sections": curriculum_sections,
                "invalid_group": invalid_group,
                "needs_group_choice": not group_id and mentor_courses.count() > 1,
                "groups": mentor_courses,
            },
        )
    except Exception as e:
        print(f"[DEBUG] Error in mentor_curriculum: {e}")
        import traceback
        traceback.print_exc()
        return render(request, "errors/500.html", status=500)


@login_required
def mentor_profile(request):
    try:
        if getattr(request.user, "role", "") != "Ментор":
            return render(request, "errors/403.html", status=403)
        
        # Получаем профиль ментора
        try:
            mentor_profile = request.user.mentor_profile
        except AttributeError:
            return render(request, "errors/500.html", status=500)
        
        if request.method == "POST":
            # Обновляем данные профиля
            mentor_profile.middle_name = request.POST.get("middle_name", "")
            mentor_profile.birth_date = request.POST.get("birth_date") or None
            mentor_profile.skills = request.POST.get("skills", "")
            mentor_profile.workplace = request.POST.get("workplace", "")
            mentor_profile.documents_folder = request.POST.get("documents_folder", "")
            mentor_profile.payment_form = request.POST.get("payment_form", Mentor.PaymentForm.FIXED)
            mentor_profile.payment_rate = request.POST.get("payment_rate") or None
            mentor_profile.fixed_rate = request.POST.get("fixed_rate") or 0
            mentor_profile.percentage_rate = request.POST.get("percentage_rate") or None
            mentor_profile.note = request.POST.get("note", "")
            
            # Обновляем данные пользователя
            request.user.first_name = request.POST.get("first_name", "")
            request.user.last_name = request.POST.get("last_name", "")
            request.user.phone_number = request.POST.get("phone_number", "")
            
            mentor_profile.save()
            request.user.save()
            
            return render(request, "portal/mentor_profile.html", {
                "active": "profile",
                "mentor": mentor_profile,
                "success": True,
            })
        
        return render(request, "portal/mentor_profile.html", {
            "active": "profile",
            "mentor": mentor_profile,
        })
    except Exception as e:
        print(f"[DEBUG] Error in mentor_profile: {e}")
        import traceback
        traceback.print_exc()
        return render(request, "errors/500.html", status=500)


@login_required
def lesson_detail(request, lesson_id):
    try:
        if getattr(request.user, "role", "") != "Ментор":
            return render(request, "errors/403.html", status=403)
        
        # Получаем профиль ментора
        try:
            mentor_profile = request.user.mentor_profile
        except AttributeError:
            return render(request, "errors/500.html", status=500)
        
        # Получаем урок
        try:
            lesson = Lesson.objects.get(id=lesson_id, mentor=mentor_profile)
        except Lesson.DoesNotExist:
            return render(request, "errors/404.html", status=404)
        
        # Получаем студентов курса, если урок привязан к курсу
        students = []
        if lesson.course:
            students = lesson.course.students.all()
        
        # Получаем связанные данные
        links = lesson.links.all().order_by('order')
        grades = StudentGrade.objects.filter(lesson=lesson).select_related('student')
        
        if request.method == "POST":
            # Обновляем урок
            lesson.title = request.POST.get("title", "")
            lesson.description = request.POST.get("description", "")
            lesson.date = request.POST.get("date") or None
            lesson.save()
            
            # Обновляем ссылки
            lesson.links.all().delete()
            link_titles = request.POST.getlist("link_title")
            link_urls = request.POST.getlist("link_url")
            for i, (title, url) in enumerate(zip(link_titles, link_urls)):
                if title and url:
                    LessonLink.objects.create(
                        lesson=lesson,
                        title=title,
                        url=url,
                        order=i
                    )
            links = lesson.links.all().order_by('order')
            # Обновляем оценки студентов
            for student in students:
                grade_key = f"grade_{student.id}"
                comment_key = f"comment_{student.id}"
                grade_value = request.POST.get(grade_key)
                comment_value = request.POST.get(comment_key, "")
                
                if grade_value in ['0', '1']:
                    StudentGrade.objects.update_or_create(
                        lesson=lesson,
                        student=student,
                        defaults={
                            'grade': int(grade_value),
                            'comment': comment_value
                        }
                    )
                elif grade_value == '' or grade_value is None:
                    # Удаляем оценку, если она была сброшена
                    StudentGrade.objects.filter(lesson=lesson, student=student).delete()
            
            # Обновляем данные оценок после сохранения
            updated_grades = StudentGrade.objects.filter(lesson=lesson).select_related('student')
            
            return render(request, "portal/lesson_detail.html", {
                "active": "lessons",
                "lesson": lesson,
                "students": students,
                "links": links,
                "grades": updated_grades,
                "success": True,
            })
        
        return render(request, "portal/lesson_detail.html", {
            "active": "lessons",
            "lesson": lesson,
            "students": students,
            "links": links,
            "grades": grades,
        })
    except Exception as e:
        print(f"[DEBUG] Error in lesson_detail: {e}")
        import traceback
        traceback.print_exc()
        return render(request, "errors/500.html", status=500)


@login_required
def student_dashboard(request):
    try:
        if getattr(request.user, "role", "") != "Студент":
            return render(request, "errors/403.html", status=403)
        return render(request, "portal/student_dashboard.html")
    except Exception:
        return render(request, "errors/500.html", status=500)


def _parent_selected_object(objects, selected_id):
    if not selected_id:
        return objects[0] if objects else None
    for obj in objects:
        if str(obj.pk) == selected_id:
            return obj
    return objects[0] if objects else None


@login_required
def parent_dashboard(request):
    try:
        if getattr(request.user, "role", "") != "Родитель":
            return render(request, "errors/403.html", status=403)

        try:
            parent_profile = request.user.parent_profile
        except AttributeError:
            return render(request, "errors/500.html", status=500)

        students = list(
            parent_profile.students.filter(is_archived=False)
            .select_related("user")
            .order_by("user__last_name", "user__first_name", "id")
        )
        selected_student = _parent_selected_object(
            students,
            (request.GET.get("student_id") or "").strip(),
        )

        courses = []
        selected_course = None
        lesson_cells = []
        attendance_total = 0
        attendance_marked = 0
        comment_count = 0

        if selected_student:
            courses = list(
                Cursues.objects.active()
                .filter(
                    Q(students=selected_student)
                    | Q(enrollment__student=selected_student)
                    | Q(lessons__grades__student=selected_student)
                )
                .prefetch_related("mentors__user")
                .distinct()
                .order_by("title", "id")
            )
            selected_course = _parent_selected_object(
                courses,
                (request.GET.get("course_id") or request.GET.get("group_id") or "").strip(),
            )

        if selected_student and selected_course:
            lessons = list(
                Lesson.objects.filter(
                    course=selected_course,
                    is_archived=False,
                ).order_by("order", "id")
            )
            grades = {
                grade.lesson_id: grade
                for grade in StudentGrade.objects.filter(
                    student=selected_student,
                    lesson__course=selected_course,
                )
                .select_related("lesson")
                .order_by("lesson__order", "lesson_id")
            }

            for lesson in lessons:
                grade = grades.get(lesson.id)
                grade_value = grade.grade if grade else None
                if grade_value is not None:
                    attendance_marked += 1
                    if grade_value == 1:
                        attendance_total += 1
                if grade and grade.comment:
                    comment_count += 1

                lesson_cells.append(
                    {
                        "lesson": lesson,
                        "grade": grade,
                        "grade_value": grade_value,
                        "status_label": (
                            "Присутствовал"
                            if grade_value == 1
                            else "Отсутствовал"
                            if grade_value == 0
                            else "Не отмечено"
                        ),
                    }
                )

        return render(
            request,
            "portal/parent_dashboard.html",
            {
                "parent_profile": parent_profile,
                "students": students,
                "selected_student": selected_student,
                "courses": courses,
                "selected_course": selected_course,
                "lesson_cells": lesson_cells,
                "attendance_total": attendance_total,
                "attendance_marked": attendance_marked,
                "missed_total": max(attendance_marked - attendance_total, 0),
                "comment_count": comment_count,
                "attendance_percent": (
                    round((attendance_total / attendance_marked) * 100)
                    if attendance_marked
                    else None
                ),
            },
        )
    except Exception as e:
        print(f"[DEBUG] Error in parent_dashboard: {e}")
        import traceback
        traceback.print_exc()
        return render(request, "errors/500.html", status=500)


@require_http_methods(["GET"])
def search_students(request):
    """API для поиска студентов (используется в форме регистрации родителя)"""
    q = (request.GET.get('q') or '').strip()
    
    if len(q) < 2:
        return JsonResponse({'students': []})
    
    students = Student.objects.select_related('user').filter(
        is_archived=False
    ).filter(
        Q(user__first_name__icontains=q) |
        Q(user__last_name__icontains=q) |
        Q(user__username__icontains=q) |
        Q(middle_name__icontains=q)
    ).order_by('user__last_name', 'user__first_name')[:10]
    
    result = []
    for student in students:
        full_name = student.user.get_full_name() or student.user.username
        result.append({
            'id': student.id,
            'name': full_name,
            'details': f"{'Статус: ' + student.get_status_display() if student.status else ''}"
        })
    
    return JsonResponse({'students': result})


@require_http_methods(["POST"])
def public_registration(request):
    """Публичная регистрация для студентов, менторов и родителей"""
    error = None
    success_message = None
    
    role = request.POST.get('role', 'student')
    
    if role == 'student':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        phone = request.POST.get('phone_number', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        
        if not first_name or not last_name or not password:
            error = 'Укажите имя, фамилию и пароль'
        else:
            try:
                from django.utils.text import slugify
                base_username = slugify(f"{first_name}-{last_name}")[:40] or 'student'
                username = base_username
                n = 0
                while User.objects.filter(username=username).exists():
                    n += 1
                    username = f"{base_username}{n}"
                
                user = User.objects.create(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    middle_name=middle_name,
                    phone_number=phone,
                    email=email,
                    role='Студент',
                    is_staff=False,
                )
                user.set_password(password)
                user.save()
                
                Student.objects.create(user=user, status='active')
                
                success_message = f'Студент зарегистрирован! Логин: {username}'
            except Exception as e:
                error = f'Ошибка регистрации: {e}'
    
    elif role == 'mentor':
        first_name = request.POST.get('mentor_first_name', '').strip()
        last_name = request.POST.get('mentor_last_name', '').strip()
        middle_name = request.POST.get('mentor_middle_name', '').strip()
        phone = request.POST.get('mentor_phone', '').strip()
        email = request.POST.get('mentor_email', '').strip()
        password = request.POST.get('mentor_password', '')
        
        if not first_name or not last_name or not password:
            error = 'Укажите имя, фамилию и пароль'
        else:
            try:
                from django.utils.text import slugify
                base_username = slugify(f"{first_name}-{last_name}")[:40] or 'mentor'
                username = base_username
                n = 0
                while User.objects.filter(username=username).exists():
                    n += 1
                    username = f"{base_username}{n}"
                
                user = User.objects.create(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    middle_name=middle_name,
                    phone_number=phone,
                    email=email,
                    role='Ментор',
                    is_staff=False,
                )
                user.set_password(password)
                user.save()
                
                Mentor.objects.create(user=user)
                
                success_message = f'Ментор зарегистрирован! Логин: {username}'
            except Exception as e:
                error = f'Ошибка регистрации: {e}'
    
    elif role == 'parent':
        first_name = request.POST.get('parent_first_name', '').strip()
        last_name = request.POST.get('parent_last_name', '').strip()
        phone = request.POST.get('parent_phone', '').strip()
        password = request.POST.get('parent_password', '')
        student_id = request.POST.get('parent_student_id', '').strip()
        
        if not first_name or not last_name or not password:
            error = 'Укажите имя, фамилию и пароль'
        elif not student_id:
            error = 'Выберите студента для привязки'
        else:
            try:
                student = Student.objects.get(pk=student_id, is_archived=False)
                
                from django.utils.text import slugify
                base_username = slugify(f"{first_name}-{last_name}")[:40] or 'parent'
                username = base_username
                n = 0
                while User.objects.filter(username=username).exists():
                    n += 1
                    username = f"{base_username}{n}"
                
                user = User.objects.create(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    phone_number=phone,
                    role='Родитель',
                    is_staff=False,
                )
                user.set_password(password)
                user.save()
                
                parent = Parent.objects.create(user=user, phone_number=phone)
                parent.students.add(student)
                
                success_message = f'Родитель зарегистрирован! Логин: {username}. Привязан к студенту: {student.user.get_full_name() or student.user.username}'
            except Student.DoesNotExist:
                error = 'Студент не найден'
            except Exception as e:
                error = f'Ошибка регистрации: {e}'
    
    else:
        error = 'Неверная роль'
    
    return render(request, 'portal/registration.html', {
        'error': error,
        'success_message': success_message,
    })


def error_404(request, exception=None):
    try:
        return render(request, "errors/404.html", status=404)
    except Exception:
        return render(request, "errors/500.html", status=500)


def error_500(request):
    return render(request, "errors/500.html", status=500)


def error_403(request, exception=None):
    try:
        return render(request, "errors/403.html", status=403)
    except Exception:
        return render(request, "errors/500.html", status=500)


def error_401(request):
    try:
        return render(request, "errors/401.html", status=401)
    except Exception:
        return render(request, "errors/500.html", status=500)


@login_required
def tabel_view(request):
    try:
        if getattr(request.user, "role", "") not in ["Ментор", "Админ"]:
            return render(request, "errors/403.html", status=403)
        
        mentor_profile = Mentor.objects.get(user=request.user)
        
        # Получаем все оценки студентов ментора
        from app.settings.models import StudentGrade
        grades = StudentGrade.objects.filter(
            lesson__course__mentors=mentor_profile
        ).select_related('student', 'lesson', 'lesson__course', 'student__user').order_by('-created_at')
        
        # Подготавливаем данные для таблицы
        records = []
        for grade in grades:
            # Определяем класс для оценки
            grade_class = "satisfactory"  # по умолчанию
            if grade.grade >= 5:
                grade_class = "excellent"
            elif grade.grade >= 4:
                grade_class = "good"
            elif grade.grade < 3:
                grade_class = "poor"
            
            records.append({
                'student_name': f"{grade.student.user.last_name} {grade.student.user.first_name}",
                'lesson_number': f"Урок {grade.lesson.order or grade.lesson.id}",
                'course_name': grade.lesson.course.title if grade.lesson.course else "Без курса",
                'grade': grade.grade,
                'grade_class': grade_class,
                'date': grade.created_at,
                'comment': grade.comment or ""
            })
        
        return render(request, "tabel.html", {
            "records": records,
        })
    except Exception as e:
        print(f"[DEBUG] Error in tabel_view: {e}")
        import traceback
        traceback.print_exc()
        return render(request, "errors/500.html", status=500)
