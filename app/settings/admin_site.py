from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from datetime import date, timedelta
from urllib.parse import urlsplit

from django.conf import settings as django_settings
from django.contrib.admin import AdminSite
from django.http import HttpResponse
from django.http import JsonResponse
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import path, reverse
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.utils.text import slugify
from django.template.response import TemplateResponse
from django.core.paginator import Paginator
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt

from .models import (
    AccountingAccount,
    AccountingCategory,
    AccountingEntry,
    AccountingProject,
    CalendarEvent,
    Cursues,
    Enrollment,
    Lead,
    Mentor,
    Payment,
    Salary,
    Student,
    Task,
    User,
)
from app.config.models import CRMAbout


@dataclass(frozen=True)
class MonthSeries:
    labels: list[str]
    values: list[float]


def _last_month_starts(months: int) -> list[date]:
    today = timezone.localdate()
    first_of_this_month = today.replace(day=1)
    starts: list[date] = []
    year = first_of_this_month.year
    month = first_of_this_month.month
    for _ in range(months):
        starts.append(date(year, month, 1))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return list(reversed(starts))


def _sum_by_month(qs, months: int, field: str) -> MonthSeries:
    month_starts = _last_month_starts(months)
    start = month_starts[0]
    end = (month_starts[-1].replace(day=28) + timedelta(days=4)).replace(day=1)

    grouped = (
        qs.filter(created_at__gte=start, created_at__lt=end)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(total=Sum(field))
        .order_by("month")
    )
    totals = {row["month"].date(): float(row["total"] or 0) for row in grouped if row["month"]}

    labels: list[str] = []
    values: list[float] = []
    for m in month_starts:
        labels.append(m.strftime("%b %y"))
        values.append(totals.get(m, 0.0))
    return MonthSeries(labels=labels, values=values)


def _count_by_month(qs, months: int) -> MonthSeries:
    month_starts = _last_month_starts(months)
    start = month_starts[0]
    end = (month_starts[-1].replace(day=28) + timedelta(days=4)).replace(day=1)

    grouped = (
        qs.filter(created_at__gte=start, created_at__lt=end)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )
    totals = {row["month"].date(): float(row["total"] or 0) for row in grouped if row["month"]}

    labels: list[str] = []
    values: list[float] = []
    for m in month_starts:
        labels.append(m.strftime("%b"))
        values.append(totals.get(m, 0.0))
    return MonthSeries(labels=labels, values=values)


def _count_by_day(qs, days: int) -> MonthSeries:
    today = timezone.localdate()
    start = today - timedelta(days=days - 1)
    grouped = (
        qs.filter(created_at__date__gte=start, created_at__date__lte=today)
        .values("created_at__date")
        .annotate(total=Count("id"))
        .order_by("created_at__date")
    )
    totals = {row["created_at__date"]: float(row["total"] or 0) for row in grouped}

    labels: list[str] = []
    values: list[float] = []
    for i in range(days):
        d = start + timedelta(days=i)
        labels.append(d.strftime("%d.%m"))
        values.append(totals.get(d, 0.0))
    return MonthSeries(labels=labels, values=values)


class CRMAdminSite(AdminSite):
    site_header = "Codify CRM"
    site_title = "Codify CRM"
    index_title = "Дашборд"
    index_template = "admin/crm_index.html"

    @staticmethod
    def _role(user) -> str:
        role = getattr(user, "role", "") or ""
        return "Администратор" if role == "Админ" else role

    def _is_manager(self, request) -> bool:
        return self._role(request.user) == "Менеджер"

    def _deny_accounting_for_manager(self, request):
        if self._is_manager(request):
            return HttpResponseForbidden("Managers cannot access accounting.")
        return None

    def has_permission(self, request):
        user = request.user
        if not user.is_authenticated or not user.is_active:
            return False
        return super().has_permission(request)

    def _path_matches(self, request, url: str | None, *, exact: bool = False) -> bool:
        if not url:
            return False
        target = (urlsplit(url).path or "").rstrip("/") or "/"
        current = (request.path or "").rstrip("/") or "/"
        if exact:
            return current == target
        return current == target or current.startswith(f"{target}/")

    def _sidebar_item(
        self,
        request,
        *,
        title: str,
        icon: str,
        url: str | None = None,
        children: list[dict] | None = None,
        exact: bool = False,
        match_url: bool = True,
        force_open: bool = False,
    ) -> dict:
        children = children or []
        child_active = any(child.get("active") or child.get("open") for child in children)
        active = child_active or (match_url and self._path_matches(request, url, exact=exact))
        return {
            "title": title,
            "icon": icon,
            "url": url,
            "children": children,
            "active": active,
            "open": force_open or child_active,
        }

    def _build_sidebar_menu(self, request) -> list[dict]:
        jazzmin_settings = getattr(django_settings, "JAZZMIN_SETTINGS", {})
        icon_map = jazzmin_settings.get("icons", {})
        hidden_models = {m.lower() for m in jazzmin_settings.get("hide_models", [])}
        ordered_models = [m.lower() for m in jazzmin_settings.get("order_with_respect_to", []) if "." in m]
        default_child_icon = jazzmin_settings.get("default_icon_children", "far fa-circle")

        model_map: dict[str, dict] = {}
        model_order: list[str] = []
        for app in self.get_app_list(request):
            app_label = app["app_label"].lower()
            for model in app.get("models", []):
                model_str = f"{app_label}.{model['object_name']}".lower()
                if model_str in hidden_models:
                    continue
                model_map[model_str] = {
                    "title": model.get("name") or model["object_name"],
                    "icon": icon_map.get(model_str, default_child_icon),
                    "url": model.get("admin_url"),
                }
                model_order.append(model_str)

        index_url = reverse(f"{self.name}:index")
        menu: list[dict] = []
        handled: set[str] = set()

        org_items = getattr(django_settings, "CRM_ORGANIZATIONS", None)
        if not org_items:
            site_brand = jazzmin_settings.get("site_brand") or self.site_header
            org_items = [site_brand]

        org_children = []
        for org in org_items:
            if isinstance(org, dict):
                org_title = (org.get("title") or org.get("name") or "").strip()
                org_url = org.get("url") or f"{index_url}?organization={slugify(org_title or 'default')}"
            else:
                org_title = str(org).strip()
                org_url = f"{index_url}?organization={slugify(org_title or 'default')}"
            if not org_title:
                continue
            org_children.append(
                self._sidebar_item(
                    request,
                    title=org_title,
                    icon="fas fa-angle-right",
                    url=org_url,
                    match_url=False,
                )
            )

        if org_children:
            menu.append(
                self._sidebar_item(
                    request,
                    title="Мои организации",
                    icon="fas fa-map-marker-alt",
                    children=org_children,
                    match_url=False,
                    force_open=True,
                )
            )

        menu.append(
            self._sidebar_item(
                request,
                title="Дашборд",
                icon="fas fa-th-large",
                url=index_url,
                exact=True,
            )
        )

        def take_model(model_str: str, *, title: str | None = None, icon: str | None = None, url: str | None = None) -> dict | None:
            item = model_map.get(model_str)
            if not item:
                return None
            handled.add(model_str)
            return self._sidebar_item(
                request,
                title=title or item["title"],
                icon=icon or item["icon"],
                url=url or item["url"],
            )

        def add_courses_tree():
            course_children = []
            group_item = take_model("settings.groupcourse")
            if group_item:
                course_children.append(group_item)
            individual_item = take_model("settings.individualcourse")
            if individual_item:
                course_children.append(individual_item)

            handled.add("settings.cursues")
            if course_children:
                menu.append(
                    self._sidebar_item(
                        request,
                        title="Курсы",
                        icon=icon_map.get("settings.cursues", "fas fa-book"),
                        children=course_children,
                    )
                )
            else:
                course_item = take_model("settings.cursues", title="Курсы")
                if course_item:
                    menu.append(course_item)

        for model_str in ordered_models:
            if model_str in handled or model_str in {"settings.groupcourse", "settings.individualcourse"}:
                continue
            if model_str == "settings.cursues":
                add_courses_tree()
                continue
            if model_str == "settings.calendarevent" and model_str in model_map:
                handled.add(model_str)
                menu.append(
                    self._sidebar_item(
                        request,
                        title=model_map[model_str]["title"],
                        icon=model_map[model_str]["icon"],
                        url=reverse(f"{self.name}:calendar"),
                    )
                )
                continue
            item = take_model(model_str)
            if item:
                menu.append(item)

        if "settings.cursues" in model_map and "settings.cursues" not in handled:
            add_courses_tree()

        for model_str in model_order:
            if model_str in handled or model_str in {"settings.groupcourse", "settings.individualcourse"}:
                continue
            if model_str == "settings.calendarevent":
                handled.add(model_str)
                menu.append(
                    self._sidebar_item(
                        request,
                        title=model_map[model_str]["title"],
                        icon=model_map[model_str]["icon"],
                        url=reverse(f"{self.name}:calendar"),
                    )
                )
                continue
            item = take_model(model_str)
            if item:
                menu.append(item)

        menu.append(
            self._sidebar_item(
                request,
                title="Архив",
                icon="fas fa-archive",
                url=reverse(f"{self.name}:archive_index"),
            )
        )
        return menu

    def each_context(self, request):
        context = super().each_context(request)
        context.update(
            {
                "crm_admin_site_name": self.name,
                "crm_sidebar_index_url": reverse(f"{self.name}:index"),
                "crm_sidebar_menu": self._build_sidebar_menu(request),
            }
        )
        return context

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label=app_label)
        role = self._role(request.user)

        if role == "Администратор":
            return app_list

        def filter_models(models):
            if role == "Менеджер":
                blocked = {"AccountingEntry", "AccountingAccount", "AccountingProject", "AccountingCategory"}
                return [m for m in models if m.get("object_name") not in blocked]
            if role == "Ментор":
                allowed = {
                    "Cursues",
                    "Student",
                    "Mentor",
                    "StudentPayments",
                    "TuitionPayment",
                    "DebtorEnrollment",
                    "CalendarEvent",
                }
                return [m for m in models if m.get("object_name") in allowed]
            return models

        out = []
        for app in app_list:
            models = filter_models(app.get("models", []))
            if models:
                app2 = dict(app)
                app2["models"] = models
                out.append(app2)
        return out

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "settings/course/<int:course_id>/students.csv",
                self.admin_view(self.course_students_csv),
                name="course_students_csv",
            ),
            path(
                "settings/course/<int:course_id>/update/",
                self.admin_view(self.course_update),
                name="course_update",
            ),
            path(
                "settings/course/<int:course_id>/status/",
                self.admin_view(self.course_status_update),
                name="course_status_update",
            ),
            path("archive/", self.admin_view(self.archive_index), name="archive_index"),
            path("calendar/", self.admin_view(self.calendar_view), name="calendar"),
            path("calendar/events/", self.admin_view(self.calendar_events), name="calendar_events"),
            path("calendar/events/create/", self.admin_view(self.calendar_event_create), name="calendar_event_create"),
            path("students.csv", self.admin_view(self.students_csv), name="students_csv"),
            path("students.pdf", self.admin_view(self.students_pdf), name="students_pdf"),
            path("students/<int:student_id>/drawer/", self.admin_view(self.student_drawer), name="student_drawer"),
            path("about/", self.admin_view(self.about_view), name="about"),
            path("accounting/meta/", self.admin_view(self.accounting_meta), name="accounting_meta"),
            path("accounting/entry/create/", self.admin_view(self.accounting_entry_create), name="accounting_entry_create"),
            path("accounting/transfer/create/", self.admin_view(self.accounting_transfer_create), name="accounting_transfer_create"),
        ]
        return custom + urls

    def about_view(self, request):
        about = CRMAbout.objects.order_by("-updated_at").first()
        role = self._role(request.user)
        can_edit = role in ("Администратор", "Менеджер") and request.user.is_staff
        context = {
            "title": "О нас",
            "about": about,
            "can_edit": can_edit,
            **self.each_context(request),
        }
        return TemplateResponse(request, "admin/about.html", context)

    def accounting_meta(self, request):
        denied = self._deny_accounting_for_manager(request)
        if denied:
            return denied
        accounts = list(AccountingAccount.objects.order_by("title").values("id", "title"))
        projects = list(AccountingProject.objects.order_by("title").values("id", "title"))
        categories = list(AccountingCategory.objects.order_by("title").values("id", "title"))
        return JsonResponse({"accounts": accounts, "projects": projects, "categories": categories})

    def accounting_entry_create(self, request):
        denied = self._deny_accounting_for_manager(request)
        if denied:
            return denied
        if request.method != "POST":
            return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)
        entry_type = (request.POST.get("entry_type") or "").strip()
        if entry_type not in (AccountingEntry.Type.INCOME, AccountingEntry.Type.EXPENSE):
            return JsonResponse({"ok": False, "error": "invalid entry_type"}, status=400)

        account_id = (request.POST.get("account") or "").strip()
        amount_raw = (request.POST.get("amount") or "").strip()
        operated_at_raw = (request.POST.get("operated_at") or "").strip()
        project_id = (request.POST.get("project") or "").strip()
        category_id = (request.POST.get("category") or "").strip()
        title = (request.POST.get("title") or "").strip()

        if not account_id:
            return JsonResponse({"ok": False, "error": "account required"}, status=400)
        try:
            amount = float(amount_raw or 0)
        except ValueError:
            return JsonResponse({"ok": False, "error": "invalid amount"}, status=400)
        if amount <= 0:
            return JsonResponse({"ok": False, "error": "amount must be > 0"}, status=400)

        operated_at = timezone.now()
        if operated_at_raw:
            dt = timezone.datetime.fromisoformat(operated_at_raw)
            operated_at = dt if timezone.is_aware(dt) else timezone.make_aware(dt, timezone.get_current_timezone())

        AccountingEntry.objects.create(
            entry_type=entry_type,
            title=title or ("Приход" if entry_type == AccountingEntry.Type.INCOME else "Расход"),
            amount=amount,
            operated_at=operated_at,
            account_id=int(account_id),
            project_id=int(project_id) if project_id else None,
            category_id=int(category_id) if category_id else None,
        )
        return JsonResponse({"ok": True})

    def course_update(self, request, course_id: int):
        if request.method != "POST":
            return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)
        course = get_object_or_404(Cursues, pk=course_id)

        title = (request.POST.get("title") or "").strip()
        subject = (request.POST.get("subject") or "").strip()
        room = (request.POST.get("room") or "").strip()
        status = (request.POST.get("status") or "").strip()
        schedule_note = (request.POST.get("schedule_note") or "").strip()

        if title:
            course.title = title

        capacity_raw = (request.POST.get("capacity") or "").strip()
        if capacity_raw:
            try:
                course.capacity = max(0, int(capacity_raw))
            except ValueError:
                pass

        start_raw = (request.POST.get("start") or "").strip()
        if start_raw:
            try:
                parsed = (
                    timezone.datetime.fromisoformat(start_raw).date()
                    if "T" in start_raw
                    else date.fromisoformat(start_raw)
                )
            except ValueError:
                parsed = None
            if parsed:
                course.start = parsed

        duration_raw = (request.POST.get("duration_months") or "").strip()
        if duration_raw:
            try:
                duration_months = max(0, int(duration_raw))
                course.duration_days = duration_months * 30
            except ValueError:
                pass

        price_raw = (request.POST.get("price") or "").strip()
        if price_raw:
            try:
                course.price = Decimal(price_raw)
            except (InvalidOperation, ValueError):
                pass

        if status:
            course.status = status
        course.subject = subject
        course.room = room
        course.schedule_note = schedule_note
        course.save()

        next_url = (request.POST.get("next") or "").strip() or reverse(f"{self.name}:settings_groupcourse_change", args=[course.pk])
        return redirect(next_url)

    def course_status_update(self, request, course_id: int):
        if request.method != "POST":
            return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)
        course = get_object_or_404(Cursues, pk=course_id)
        action = (request.POST.get("action") or "").strip()

        if action == "finish":
            course.status = "Завершенные курсы"
            course.save(update_fields=["status"])
        elif action == "archive":
            course.is_archived = True
            course.archived_at = timezone.now()
            course.save(update_fields=["is_archived", "archived_at"])

        if action == "archive":
            next_url = reverse(f"{self.name}:settings_groupcourse_changelist")
            next_url = f"{next_url}?archived=1"
        else:
            next_url = (request.POST.get("next") or "").strip() or reverse(
                f"{self.name}:settings_groupcourse_change",
                args=[course.pk],
            )
        return redirect(next_url)

    def accounting_transfer_create(self, request):
        denied = self._deny_accounting_for_manager(request)
        if denied:
            return denied
        if request.method != "POST":
            return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)
        from_account = (request.POST.get("from_account") or "").strip()
        to_account = (request.POST.get("to_account") or "").strip()
        amount_raw = (request.POST.get("amount") or "").strip()
        operated_at_raw = (request.POST.get("operated_at") or "").strip()
        project_id = (request.POST.get("project") or "").strip()
        category_id = (request.POST.get("category") or "").strip()
        title = (request.POST.get("title") or "").strip() or "Перевод"

        if not from_account or not to_account:
            return JsonResponse({"ok": False, "error": "accounts required"}, status=400)
        if from_account == to_account:
            return JsonResponse({"ok": False, "error": "accounts must differ"}, status=400)
        try:
            amount = float(amount_raw or 0)
        except ValueError:
            return JsonResponse({"ok": False, "error": "invalid amount"}, status=400)
        if amount <= 0:
            return JsonResponse({"ok": False, "error": "amount must be > 0"}, status=400)

        operated_at = timezone.now()
        if operated_at_raw:
            dt = timezone.datetime.fromisoformat(operated_at_raw)
            operated_at = dt if timezone.is_aware(dt) else timezone.make_aware(dt, timezone.get_current_timezone())

        group = timezone.now().strftime("tr%Y%m%d%H%M%S%f")
        with transaction.atomic():
            AccountingEntry.objects.create(
                entry_type=AccountingEntry.Type.EXPENSE,
                title=title,
                amount=amount,
                operated_at=operated_at,
                account_id=int(from_account),
                project_id=int(project_id) if project_id else None,
                category_id=int(category_id) if category_id else None,
                transfer_group=group,
            )
            AccountingEntry.objects.create(
                entry_type=AccountingEntry.Type.INCOME,
                title=title,
                amount=amount,
                operated_at=operated_at,
                account_id=int(to_account),
                project_id=int(project_id) if project_id else None,
                category_id=int(category_id) if category_id else None,
                transfer_group=group,
            )
        return JsonResponse({"ok": True})

    def course_students_csv(self, request, course_id: int):
        course = Cursues.objects.get(pk=course_id)
        enrollments = (
            Enrollment.objects.select_related("student__user")
            .filter(course=course)
            .order_by("student__user__username")
        )

        lines = ["ФИО,Телефон,Курс"]
        for e in enrollments:
            user = e.student.user
            full_name = (user.get_full_name() or user.username).replace(",", " ")
            phone = (user.phone_number or "").replace(",", " ")
            lines.append(f"{full_name},{phone},{course.title.replace(',', ' ')}")

        content = "\n".join(lines)
        resp = HttpResponse(content, content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="course_{course_id}_students.csv"'
        return resp

    def archive_index(self, request):
        items = [
            {"title": "Курсы", "url": "/admin/settings/cursues/?archived=1"},
            {"title": "Лиды", "url": "/admin/settings/lead/?archived=1"},
            {"title": "Звонки", "url": "/admin/settings/call/?archived=1"},
            {"title": "Календарь", "url": "/admin/settings/calendarevent/?archived=1"},
            {"title": "Задачи", "url": "/admin/settings/task/?archived=1"},
        ]
        if not self._is_manager(request):
            items.insert(4, {"title": "Бухгалтерия", "url": "/admin/settings/accountingentry/?archived=1"})
        context = {"title": "Архив", "items": items, **self.each_context(request)}
        return TemplateResponse(request, "admin/archive_index.html", context)

    def calendar_view(self, request):
        courses = Cursues.objects.filter(is_archived=False).order_by("title")
        mentors = Mentor.objects.select_related("user").order_by("user__username")
        subjects = (
            Cursues.objects.exclude(subject="")
            .values_list("subject", flat=True)
            .distinct()
            .order_by("subject")
        )
        context = {
            "title": "Календарь активных курсов",
            "courses": courses,
            "mentors": mentors,
            "subjects": subjects,
            **self.each_context(request),
        }
        return TemplateResponse(request, "admin/calendar.html", context)

    def calendar_events(self, request):
        qs = CalendarEvent.objects.filter(is_archived=False)

        course = request.GET.get("course")
        if course:
            # allow both id and title
            if course.isdigit():
                qs = qs.filter(course_id=course)
            else:
                qs = qs.filter(course__title=course)

        subject = request.GET.get("subject")
        if subject:
            qs = qs.filter(course__subject=subject)

        mentor_id = request.GET.get("mentor")
        if mentor_id:
            if mentor_id.isdigit():
                qs = qs.filter(course__mentors__id=mentor_id).distinct()
            else:
                qs = qs.filter(course__mentors__user__username=mentor_id).distinct()

        events = []
        for e in qs.select_related("course").order_by("start_at")[:2000]:
            color = None
            if e.course and e.course.subject:
                palette = {
                    "English": "#9ee7e5",
                    "Math": "#b7c3d9",
                    "Python": "#a7f3d0",
                    "Design": "#f5b48f",
                }
                color = palette.get(e.course.subject)

            events.append(
                {
                    "id": e.id,
                    "title": e.title,
                    "start": e.start_at.isoformat(),
                    "end": e.end_at.isoformat() if e.end_at else None,
                    "backgroundColor": color,
                    "borderColor": color,
                }
            )
        return JsonResponse(events, safe=False)

    def calendar_event_create(self, request):
        if request.method != "POST":
            return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)
        title = (request.POST.get("title") or "").strip()
        start = (request.POST.get("start_at") or "").strip()
        end = (request.POST.get("end_at") or "").strip()
        course_id = (request.POST.get("course") or "").strip() or None
        location = (request.POST.get("location") or "").strip()
        online_link = (request.POST.get("online_link") or "").strip()
        description = (request.POST.get("description") or "").strip()

        if not title or not start:
            return JsonResponse({"ok": False, "error": "title/start_at required"}, status=400)

        try:
            start_dt = timezone.datetime.fromisoformat(start)
            if timezone.is_naive(start_dt):
                start_dt = timezone.make_aware(start_dt, timezone.get_current_timezone())
        except ValueError:
            return JsonResponse({"ok": False, "error": "invalid start_at"}, status=400)

        end_dt = None
        if end:
            try:
                end_dt = timezone.datetime.fromisoformat(end)
                if timezone.is_naive(end_dt):
                    end_dt = timezone.make_aware(end_dt, timezone.get_current_timezone())
            except ValueError:
                return JsonResponse({"ok": False, "error": "invalid end_at"}, status=400)

        ev = CalendarEvent.objects.create(
            title=title,
            course_id=course_id,
            start_at=start_dt,
            end_at=end_dt,
            location=location,
            online_link=online_link,
            description=description,
        )
        return JsonResponse({"ok": True, "id": ev.id})

    def students_csv(self, request):
        qs = Student.objects.select_related("user")
        status = request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        archived = request.GET.get("archived")
        if archived == "1":
            qs = qs.filter(is_archived=True)
        elif archived == "0":
            qs = qs.filter(is_archived=False)
        q = (request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(user__username__icontains=q) | qs.filter(user__first_name__icontains=q) | qs.filter(
                user__last_name__icontains=q
            )

        lines = ["ID,ФИО,Телефон,Статус"]
        for s in qs.order_by("id")[:5000]:
            u = s.user
            full_name = (u.get_full_name() or u.username).replace(",", " ")
            phone = (u.phone_number or "").replace(",", " ")
            lines.append(f"{s.id},{full_name},{phone},{s.get_status_display()}")
        content = "\n".join(lines)
        resp = HttpResponse(content, content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = 'attachment; filename="students.csv"'
        return resp

    def students_pdf(self, request):
        qs = Student.objects.select_related("user")
        status = request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        archived = request.GET.get("archived")
        if archived == "1":
            qs = qs.filter(is_archived=True)
        elif archived == "0":
            qs = qs.filter(is_archived=False)
        q = (request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(user__username__icontains=q) | qs.filter(user__first_name__icontains=q) | qs.filter(
                user__last_name__icontains=q
            )

        rows = []
        for s in qs.order_by("id")[:1000]:
            u = s.user
            rows.append(
                [
                    str(s.id),
                    (u.get_full_name() or u.username),
                    (u.phone_number or ""),
                    s.get_status_display(),
                ]
            )

        content = _simple_pdf_table(
            title="Students",
            headers=["ID", "Name", "Phone", "Status"],
            rows=rows,
        )
        resp = HttpResponse(content, content_type="application/pdf")
        resp["Content-Disposition"] = 'attachment; filename="students.pdf"'
        return resp

    def student_drawer(self, request, student_id: int):
        student = Student.objects.select_related("user").get(pk=student_id)
        enrollment = (
            Enrollment.objects.select_related("course")
            .filter(student=student, course__is_archived=False)
            .order_by("-created_at")
            .first()
        )
        paid_total = 0
        tuition_amount = 0
        course = None
        if enrollment:
            course = enrollment.course
            tuition_amount = float(enrollment.tuition_amount or 0)
            paid_total = float(enrollment.paid_total or 0)

        months_total = 0
        months_paid = 0
        if course and course.price:
            months_total = max(1, int(round(tuition_amount / float(course.price or 1)))) if tuition_amount else 0
            months_paid = min(months_total, int(round(paid_total / float(course.price or 1)))) if months_total else 0

        payments_qs = Payment.objects.filter(student=student).select_related("course").order_by("-created_at")
        payments_total = float(payments_qs.aggregate(total=Sum("amount"))["total"] or 0)
        page_size = 10
        paginator = Paginator(payments_qs, page_size)
        page_number = request.GET.get("p") or 1
        payments_page = paginator.get_page(page_number)

        context = {
            "student": student,
            "user": student.user,
            "enrollment": enrollment,
            "course": course,
            "tuition_amount": tuition_amount,
            "paid_total": paid_total,
            "months_total": months_total,
            "months_paid": months_paid,
            "payments_page": payments_page,
            "payments_total": payments_total,
            **self.each_context(request),
        }
        return TemplateResponse(request, "admin/student_drawer.html", context)


def _pdf_escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def _simple_pdf_table(title: str, headers: list[str], rows: list[list[str]]) -> bytes:
    # Minimal PDF generator (single font: Helvetica). Good enough for demo exports.
    # Page: A4 portrait, 595x842 points.
    width, height = 595, 842
    margin_x, margin_y = 40, 48
    line_h = 14
    y = height - margin_y

    lines: list[str] = []
    lines.append(f"/F1 16 Tf {margin_x} {y} Td ({_pdf_escape(title)}) Tj")
    y -= 24

    def emit_row(cells: list[str], bold: bool = False):
        nonlocal y
        if y < margin_y + 60:
            # new page marker
            lines.append("__NEW_PAGE__")
            y = height - margin_y
        font_size = 10
        lines.append(f"/F1 {font_size} Tf {margin_x} {y} Td ({_pdf_escape(' | '.join(cells))}) Tj")
        y -= line_h

    emit_row(headers)
    emit_row(["-" * 80])
    for r in rows:
        emit_row(r)

    # Split into pages
    pages: list[list[str]] = [[]]
    for l in lines:
        if l == "__NEW_PAGE__":
            pages.append([])
        else:
            pages[-1].append(l)

    objects: list[bytes] = []

    def add_obj(data: str) -> int:
        objects.append(data.encode("utf-8"))
        return len(objects)

    # Catalog + Pages + Font
    font_obj = add_obj("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    page_objs: list[int] = []
    content_objs: list[int] = []

    pages_kids = []
    for page_lines in pages:
        stream = "BT\n" + "\n".join(page_lines) + "\nET\n"
        content_obj = add_obj(f"<< /Length {len(stream.encode('utf-8'))} >>\nstream\n{stream}endstream")
        content_objs.append(content_obj)
        page_obj = add_obj(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] "
            f"/Resources << /Font << /F1 {font_obj} 0 R >> >> /Contents {content_obj} 0 R >>"
        )
        page_objs.append(page_obj)
        pages_kids.append(f"{page_obj} 0 R")

    pages_obj = add_obj(f"<< /Type /Pages /Kids [ {' '.join(pages_kids)} ] /Count {len(page_objs)} >>")
    # ensure Pages is object 2 (we referenced it); if not, patch by inserting dummy
    # Simpler: rebuild with fixed ordering if needed.
    if pages_obj != 2:
        # rebuild objects with fixed order: [Catalog, Pages, Font, contents..., pages...]
        objects = []
        # placeholders for indices
        catalog_idx = add_obj("<< /Type /Catalog /Pages 2 0 R >>")
        pages_idx = add_obj("<< >>")  # temp
        font_idx = add_obj("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        page_objs = []
        pages_kids = []
        for page_lines in pages:
            stream = "BT\n" + "\n".join(page_lines) + "\nET\n"
            content_obj = add_obj(f"<< /Length {len(stream.encode('utf-8'))} >>\nstream\n{stream}endstream")
            page_obj = add_obj(
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] "
                f"/Resources << /Font << /F1 {font_idx} 0 R >> >> /Contents {content_obj} 0 R >>"
            )
            page_objs.append(page_obj)
            pages_kids.append(f"{page_obj} 0 R")
        objects[pages_idx - 1] = f"<< /Type /Pages /Kids [ {' '.join(pages_kids)} ] /Count {len(page_objs)} >>".encode(
            "utf-8"
        )
    else:
        # add catalog after pages to keep references fine
        add_obj("<< /Type /Catalog /Pages 2 0 R >>")

    # build xref
    out = bytearray()
    out.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f"{i} 0 obj\n".encode("utf-8"))
        out.extend(obj)
        out.extend(b"\nendobj\n")

    xref_start = len(out)
    out.extend(f"xref\n0 {len(objects)+1}\n".encode("utf-8"))
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode("utf-8"))
    out.extend(
        f"trailer\n<< /Size {len(objects)+1} /Root {len(objects)} 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode(
            "utf-8"
        )
    )
    return bytes(out)

    def index(self, request, extra_context=None):
        context = extra_context or {}

        today = timezone.localdate()
        start_month = today.replace(day=1)
        start_year = today.replace(month=1, day=1)
        start_week = today - timedelta(days=6)

        leads_qs = Lead.objects.all()
        students_qs = Student.objects.all()
        payments_qs = Payment.objects.all()
        salary_qs = Salary.objects.all()

        money_paid_today = float(payments_qs.filter(created_at__date=today).aggregate(total=Sum("amount"))["total"] or 0)
        money_paid_week = float(
            payments_qs.filter(created_at__date__gte=start_week).aggregate(total=Sum("amount"))["total"] or 0
        )
        money_paid_month = float(
            payments_qs.filter(created_at__date__gte=start_month).aggregate(total=Sum("amount"))["total"] or 0
        )
        money_paid_year = float(
            payments_qs.filter(created_at__date__gte=start_year).aggregate(total=Sum("amount"))["total"] or 0
        )

        leads_today = leads_qs.filter(created_at__date=today).count()
        leads_week = leads_qs.filter(created_at__date__gte=start_week).count()
        leads_month = leads_qs.filter(created_at__date__gte=start_month).count()
        leads_year = leads_qs.filter(created_at__date__gte=start_year).count()

        students_today = students_qs.filter(created_at__date=today).count()
        students_week = students_qs.filter(created_at__date__gte=start_week).count()
        students_month = students_qs.filter(created_at__date__gte=start_month).count()
        students_year = students_qs.filter(created_at__date__gte=start_year).count()

        courses_income = (
            payments_qs.values("course_id", "course__title")
            .annotate(income=Sum("amount"))
            .order_by("-income")
        )
        courses_income = [c for c in courses_income if c.get("course_id")][:8]
        courses_top = []
        for row in courses_income:
            income = float(row["income"] or 0)
            courses_top.append(
                {
                    "title": row.get("course__title") or "—",
                    "income": income,
                    "salary": 0.0,
                    "profit": income,
                }
            )

        series = {
            "income": _sum_by_month(payments_qs, months=12, field="amount").__dict__,
            "expense": _sum_by_month(salary_qs, months=12, field="amount").__dict__,
            "payments_6m": _sum_by_month(payments_qs, months=6, field="amount").__dict__,
            "leads_6m": _count_by_month(leads_qs, months=6).__dict__,
            "students_6m": _count_by_month(students_qs, months=6).__dict__,
            "leads_30d": _count_by_day(leads_qs, days=30).__dict__,
        }

        context.update(
            {
                "kpi": {
                    "students": students_qs.count(),
                    "mentors": Mentor.objects.count(),
                    "leads": leads_qs.count(),
                    "courses": Cursues.objects.count(),
                },
                "courses_top": courses_top,
                "cards": {
                    "leads": {"today": leads_today, "week": leads_week, "month": leads_month, "year": leads_year},
                    "students": {
                        "today": students_today,
                        "week": students_week,
                        "month": students_month,
                        "year": students_year,
                    },
                },
                "money": {"paid": {"today": money_paid_today, "week": money_paid_week, "month": money_paid_month, "year": money_paid_year}},
                "series": series,
            }
        )

        return super().index(request, extra_context=context)


crm_admin_site = CRMAdminSite(name="crm_admin")
