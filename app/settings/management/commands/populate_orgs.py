from __future__ import annotations

import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from app.settings.models import (
    AccountingAccount,
    AccountingCategory,
    AccountingEntry,
    AccountingProject,
    CalendarEvent,
    Call,
    CourseDrop,
    Cursues,
    Enrollment,
    Lead,
    Mentor,
    Organization,
    Payment,
    Salary,
    Student,
    Task,
    User,
)

FIRST_NAMES = [
    "Harry", "Hermione", "Ron", "Draco", "Luna", "Neville", "Ginny",
    "Fred", "George", "Cedric", "Cho", "Severus", "Albus", "Minerva",
    "Rubeus", "Sirius", "Remus", "Nymphadora", "Molly", "Arthur",
    "Bill", "Charlie", "Percy", "Oliver", "Dean", "Seamus", "Parvati",
    "Padma", "Katie", "Angelina", "Alicia", "Lee", "Colin", "Dennis",
    "Lavender", "Ernie", "Hannah", "Susan", "Justin", "Zacharias",
]

LAST_NAMES = [
    "Potter", "Granger", "Weasley", "Malfoy", "Lovegood", "Longbottom",
    "Diggory", "Chang", "Snape", "Dumbledore", "McGonagall", "Hagrid",
    "Black", "Lupin", "Tonks", "Creevey", "Abbott", "Macmillan",
    "Bones", "Boot", "Smith", "Finnigan", "Patil", "Bell", "Johnson",
    "Spinnet", "Jordan", "Brown", "Finnigan", "Thomas",
]

COURSE_TITLES = [
    "LVL 0 MS NIGORA MORNING", "ABC-0 miss Muslima 9:30-10:30",
    "Lvl 0 Mrs Zamira", "ABC-1 mrs Darygul 8:30-10:00",
    "lvl-0 ms Safya 08", "LVL 0 MS NIGORA 14:00-15:30 TTS",
    "Python Basics", "Web Design Pro", "English Advanced",
    "Math Olympiad", "Data Science 101", "Mobile Development",
    "UI/UX Fundamentals", "Backend Architecture", "Frontend React",
]


def _phone():
    return "0" + "".join(str(random.randint(0, 9)) for _ in range(9))


def _name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


class Command(BaseCommand):
    help = "Create 3 organizations with demo data (20+ records per model)."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing demo data first.")

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts["reset"]:
            self._reset()

        now = timezone.now()
        today = timezone.localdate()

        # Ensure admin user exists
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={"is_staff": True, "is_superuser": True, "email": "admin@example.com", "phone_number": _phone()},
        )
        if created:
            admin_user.set_password("admin")
            admin_user.save(update_fields=["password"])

        # Create 3 organizations
        org_data = [
            {"name": "American Dream", "students": 25, "mentors": 6, "courses": 10},
            {"name": "Apex Education", "students": 30, "mentors": 7, "courses": 12},
            {"name": "Bright Future", "students": 20, "mentors": 5, "courses": 8},
        ]

        for od in org_data:
            org, _ = Organization.objects.get_or_create(name=od["name"])
            self.stdout.write(self.style.NOTICE(f"Populating {org.name}..."))

            mentors = self._create_mentors(od["mentors"], org, now)
            students = self._create_students(od["students"], org, now)
            courses = self._create_courses(od["courses"], org, today, mentors)

            # Enrollments + payments + drops
            for course in courses:
                group_size = min(len(students), random.randint(4, 14))
                group = random.sample(students, k=group_size)
                course.students.set(group)
                for st in group:
                    tuition = random.choice([course.price, course.price * 2, course.price * 3])
                    Enrollment.objects.get_or_create(student=st, course=course, defaults={"tuition_amount": tuition})
                    paid = random.choice([0, tuition * 0.3, tuition * 0.5, tuition, tuition * 1.2])
                    if paid > 0:
                        Payment.objects.create(
                            student=st, course=course, amount=paid,
                            method=random.choice(["cash", "bank", "card", "aiti_transfer", "aiti_cash"]),
                            created_at=now - timedelta(days=random.randint(0, 60)),
                            organization=org,
                        )
                for st in random.sample(group, k=min(len(group), random.randint(0, 3))):
                    CourseDrop.objects.get_or_create(
                        course=course, student=st,
                        defaults={"reason": random.choice(["Переезд", "Не успевает", "По здоровью", "Финансовые причины", ""])},
                    )

            # Salaries (20+)
            for _ in range(20):
                m = random.choice(mentors)
                Salary.objects.create(
                    mentor=m, amount=random.choice([15000, 25000, 35000, 42000, 18000]),
                    created_at=now - timedelta(days=random.randint(0, 90)),
                    organization=org,
                )

            # Leads (25)
            for _ in range(25):
                Lead.objects.create(
                    full_name=_name(), phone_number=_phone(),
                    status=random.choice([Lead.Status.NEW, Lead.Status.IN_PROGRESS, Lead.Status.WON, Lead.Status.LOST]),
                    created_at=now - timedelta(days=random.randint(0, 60)),
                    organization=org,
                )

            # Calls (25)
            for _ in range(25):
                Call.objects.create(
                    contact_name=_name(), phone_number=_phone(),
                    status=random.choice([Call.Status.NEW, Call.Status.DONE, Call.Status.MISSED]),
                    created_at=now - timedelta(days=random.randint(0, 40)),
                    organization=org,
                )

            # Calendar events (25)
            for d in range(1, 26):
                start = now + timedelta(days=d, hours=random.randint(8, 18))
                CalendarEvent.objects.create(
                    title=random.choice(["Созвон", "Встреча", "Планирование", "Урок", "Консультация", "Экзамен"]),
                    course=random.choice(courses) if courses else None,
                    start_at=start, end_at=start + timedelta(hours=1),
                    location=random.choice(["", "Офис", "Каб. 4", "Каб. 2", "Онлайн"]),
                    online_link=random.choice(["", "https://meet.google.com/demo-link"]),
                    description=random.choice(["", "Короткое описание", "Подготовка к занятию"]),
                    note=random.choice(["", "По Zoom", "В офисе", "Запись будет"]),
                    organization=org,
                )

            # Accounting entries (25)
            for _ in range(25):
                AccountingEntry.objects.create(
                    entry_type=random.choice([AccountingEntry.Type.INCOME, AccountingEntry.Type.EXPENSE]),
                    title=random.choice(["Аренда", "Реклама", "Канцелярия", "Оплата обучения", "Зарплата", "Коммунальные", "Продукты"]),
                    amount=random.choice([5000, 12000, 25000, 3500, 8000, 15000, 22000]),
                    created_at=now - timedelta(days=random.randint(0, 90)),
                    organization=org,
                )

            # Tasks (25)
            for _ in range(25):
                Task.objects.create(
                    title=random.choice([
                        "Позвонить лиду", "Собрать оплату", "Проверить посещаемость",
                        "Сформировать отчет", "Написать план", "Проверить домашку",
                        "Встреча с родителями", "Обновить расписание",
                    ]),
                    due_date=today + timedelta(days=random.randint(-5, 10)),
                    is_done=random.choice([False, False, True, False]),
                    organization=org,
                )

            # Accounting meta (Accounts, Projects, Categories)
            for acc_title in ["Основной", "Наличные", "Банк"]:
                AccountingAccount.objects.get_or_create(title=f"{acc_title} — {org.name}", defaults={"organization": org})
            for proj_title in ["Обучение", "Реклама", "Аренда"]:
                AccountingProject.objects.get_or_create(title=f"{proj_title} — {org.name}", defaults={"organization": org})
            for cat_title in ["Операционные", "Капитальные", "Прочие"]:
                AccountingCategory.objects.get_or_create(title=f"{cat_title} — {org.name}", defaults={"organization": org})

            self.stdout.write(self.style.SUCCESS(f"  Done: {org.name}"))

        self.stdout.write(self.style.SUCCESS("All 3 organizations populated! Login: admin / admin"))

    def _create_mentors(self, count: int, org, now):
        mentors = []
        for i in range(count):
            full_name = _name()
            first, last = full_name.split(" ", 1)
            username = f"mentor_{org.name.lower().replace(' ', '_')}_{i+1}"
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={"first_name": first, "last_name": last, "phone_number": _phone(),
                          "email": f"{username}@example.com", "is_staff": True},
            )
            mentor, _ = Mentor.objects.get_or_create(user=user, defaults={"organization": org})
            if not mentor.organization:
                mentor.organization = org
                mentor.save(update_fields=["organization"])
            mentors.append(mentor)
        return mentors

    def _create_students(self, count: int, org, now):
        students = []
        for i in range(count):
            full_name = _name()
            first, last = full_name.split(" ", 1)
            username = f"student_{org.name.lower().replace(' ', '_')}_{i+1}"
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={"first_name": first, "last_name": last, "phone_number": _phone(),
                          "email": f"{username}@example.com"},
            )
            student, _ = Student.objects.get_or_create(user=user, defaults={"organization": org})
            if not student.organization:
                student.organization = org
                student.save(update_fields=["organization"])
            students.append(student)
        return students

    def _create_courses(self, count: int, org, today, mentors):
        courses = []
        titles = COURSE_TITLES[:]
        while len(titles) < count:
            titles.append(f"Курс {len(titles)+1} — {_name()}")
        for i, title in enumerate(titles[:count]):
            course_type = Cursues.CourseType.GROUP if i % 2 == 0 else Cursues.CourseType.INDIVIDUAL
            course = Cursues.objects.create(
                title=title,
                course_type=course_type,
                start=today - timedelta(days=random.randint(0, 120)),
                duration_days=random.choice([30, 60, 90, 180]),
                status=random.choice(["Подготовка", "Готов к запуску", "Запущен", "Приостановлен", "Закончен"]),
                subject=random.choice(["English", "Math", "Python", "Design", "Marketing", ""]),
                price=random.choice([2500, 3500, 4500, 5500, 6000]),
                capacity=random.choice([10, 12, 15, 8]),
                room=random.choice(["4 КАБ.", "2 КАБ.", "1 КАБ.", "3 КАБ.", ""]),
                schedule_note=random.choice(["Пн/Ср/Пт 16:00-18:00", "Вт/Чт 14:00-15:30", "Пн-Пт 10:00-12:00", ""]),
                organization=org,
            )
            course.mentors.set(random.sample(mentors, k=min(len(mentors), random.randint(1, 2))))
            courses.append(course)
        return courses

    def _reset(self):
        self.stdout.write("Resetting demo data...")
        CourseDrop.objects.all().delete()
        Enrollment.objects.all().delete()
        Payment.objects.all().delete()
        Salary.objects.all().delete()
        Lead.objects.all().delete()
        Call.objects.all().delete()
        CalendarEvent.objects.all().delete()
        AccountingEntry.objects.all().delete()
        Task.objects.all().delete()
        Cursues.objects.all().delete()
        # Delete users created by this command (optional, keep admin)
        Student.objects.all().delete()
        Mentor.objects.all().delete()
        Organization.objects.all().delete()
        self.stdout.write("Reset complete.")
