from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse

from app.settings.models import User


def portal_login(request):
    """Единая страница входа для студентов, менторов, родителей, менеджеров и админов."""
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
                # --- временная отладка ---
                from app.settings.models import User
                try:
                    u = User.objects.get(username=username)
                    print(f"[DEBUG] user found: {u.username}, is_active={u.is_active}, check_pass={u.check_password(password)}")
                except User.DoesNotExist:
                    print(f"[DEBUG] user not found: {username}")
                # ------------------------
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
        return render(request, "portal/mentor_lessons.html", {"active": "lessons"})
    except Exception:
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
