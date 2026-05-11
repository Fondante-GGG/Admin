from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse

from app.settings.models import User, Lesson, Exam, Cursues, GroupCourse, IndividualCourse, Mentor


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


def _redirect_by_role(user: User):
    role = getattr(user, "role", "")
    if role == "Админ" or user.is_superuser:
        return redirect("/admin/")
    if role == "Менеджер":
        return redirect("/admin/")
    if role == "Ментор" and hasattr(user, "mentor_profile"):
        return redirect("/portal/mentor/")
    if role == "Студент" and hasattr(user, "student"):
        return redirect("/portal/student/")
    if role == "Родитель" and hasattr(user, "parent_profile"):
        return redirect("/portal/parent/")
    return redirect("/admin/")


@login_required
def mentor_dashboard(request):
    try:
        if getattr(request.user, "role", "") != "Ментор":
            return render(request, "errors/403.html", status=403)
        return render(request, "portal/mentor_dashboard.html", {"active": "home"})
    except Exception:
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
            })
        
        group_courses = GroupCourse.objects.filter(mentors=mentor_profile).active().order_by('title')
        individual_courses = IndividualCourse.objects.filter(mentors=mentor_profile).active().order_by('title')
        
        exams = Exam.objects.filter(mentor=mentor_profile).active().order_by('-created_at')
        
        print(f"[DEBUG] Found {group_courses.count()} group courses, {individual_courses.count()} individual courses and {exams.count()} exams")
        
        # Объединяем все курсы
        all_courses = list(group_courses) + list(individual_courses)
        
        return render(request, "portal/mentor_lessons.html", {
            "active": "lessons",
            "group_courses": group_courses,
            "individual_courses": individual_courses,
            "all_courses": all_courses,
            "exams": exams,
        })
    except Exception as e:
        print(f"[DEBUG] Error in mentor_lessons: {e}")
        import traceback
        traceback.print_exc()
        return render(request, "errors/500.html", status=500)


@login_required
def mentor_homework(request):
    try:
        if getattr(request.user, "role", "") != "Ментор":
            return render(request, "errors/403.html", status=403)
        return render(request, "portal/mentor_homework.html", {"active": "homework"})
    except Exception:
        return render(request, "errors/500.html", status=500)


@login_required
def mentor_schedule(request):
    try:
        if getattr(request.user, "role", "") != "Ментор":
            return render(request, "errors/403.html", status=403)
        return render(request, "portal/mentor_schedule.html", {"active": "schedule"})
    except Exception:
        return render(request, "errors/500.html", status=500)


@login_required
def mentor_gradebook(request):
    try:
        if getattr(request.user, "role", "") != "Ментор":
            return render(request, "errors/403.html", status=403)
        return render(request, "portal/mentor_gradebook.html", {"active": "gradebook"})
    except Exception:
        return render(request, "errors/500.html", status=500)


@login_required
def mentor_students(request):
    try:
        if getattr(request.user, "role", "") != "Ментор":
            return render(request, "errors/403.html", status=403)
        return render(request, "portal/mentor_students.html", {"active": "students"})
    except Exception:
        return render(request, "errors/500.html", status=500)


@login_required
def mentor_curriculum(request):
    try:
        if getattr(request.user, "role", "") != "Ментор":
            return render(request, "errors/403.html", status=403)
        return render(request, "portal/mentor_curriculum.html", {"active": "curriculum"})
    except Exception:
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
def student_dashboard(request):
    try:
        if getattr(request.user, "role", "") != "Студент":
            return render(request, "errors/403.html", status=403)
        return render(request, "portal/student_dashboard.html")
    except Exception:
        return render(request, "errors/500.html", status=500)


@login_required
def parent_dashboard(request):
    try:
        if getattr(request.user, "role", "") != "Родитель":
            return render(request, "errors/403.html", status=403)
        return render(request, "portal/parent_dashboard.html")
    except Exception:
        return render(request, "errors/500.html", status=500)


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
