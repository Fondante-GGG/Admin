from __future__ import annotations

import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from app.settings.models import (
    AccountingEntry,
    CalendarEvent,
    Call,
    CourseDrop,
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


FIRST_NAMES = [
    "Harry",
    "Hermione",
    "Ron",
    "Draco",
    "Luna",
    "Neville",
    "Ginny",
    "Fred",
    "George",
    "Cedric",
    "Cho",
    "Severus",
    "Albus",
    "Minerva",
    "Rubeus",
    "Sirius",
    "Remus",
    "Nymphadora",
    "Molly",
    "Arthur",
]
LAST_NAMES = [
    "Potter",
    "Granger",
    "Weasley",
    "Malfoy",
    "Lovegood",
    "Longbottom",
    "Diggory",
    "Chang",
    "Snape",
    "Dumbledore",
    "McGonagall",
    "Hagrid",
    "Black",
    "Lupin",
    "Tonks",
]


def _phone():
    return "0" + "".join(str(random.randint(0, 9)) for _ in range(9))


def _name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


class Command(BaseCommand):
    help = "Seed demo data for CRM admin UI."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing demo data first.")
        parser.add_argument("--students", type=int, default=25)
        parser.add_argument("--mentors", type=int, default=6)
        parser.add_argument("--courses", type=int, default=10)

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts["reset"]:
            self._reset()

        now = timezone.now()
        today = timezone.localdate()

        # superuser for quick login (if not exists)
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={"is_staff": True, "is_superuser": True, "email": "admin@example.com", "phone_number": _phone()},
        )
        if created:
            admin_user.set_password("admin")
            admin_user.save(update_fields=["password"])

        mentors = self._create_mentors(opts["mentors"])
        students = self._create_students(opts["students"])

        group_titles = [
            "LVL 0 MS NIGORA MORNING",
            "ABC-0 miss Muslima 9:30-10:30",
            "Lvl 0 Mrs Zamira",
            "ABC-1 mrs Darygul 8:30-10:00",
            "lvl-0 ms Safya 08",
            "LVL 0 MS NIGORA 14:00-15:30 TTS",
        ]
        course_titles = group_titles[:]
        while len(course_titles) < opts["courses"]:
            course_titles.append(f"Курс {len(course_titles)+1} — {_name()}")

        courses = []
        for i, title in enumerate(course_titles[: opts["courses"]]):
            course_type = Cursues.CourseType.GROUP if i % 2 == 0 else Cursues.CourseType.INDIVIDUAL
            course = Cursues.objects.create(
                title=title,
                course_type=course_type,
                start=today - timedelta(days=random.randint(0, 120)),
                duration_days=random.choice([30, 60, 90, 180]),
                status=random.choice(["Подготовка", "Готов к запуску", "Запущен", "Приостановлен", "Закончен"]),
                subject=random.choice(["English", "Math", "Python", "Design", ""]),
                price=random.choice([2500, 3500, 4500, 5500]),
                capacity=random.choice([10, 12, 15]),
                room=random.choice(["4 КАБ.", "2 КАБ.", "1 КАБ.", ""]),
                schedule_note=random.choice(["Пн/Ср/Пт 16:00-18:00", "Вт/Чт 14:00-15:30", ""]),
            )
            course.mentors.set(random.sample(mentors, k=min(len(mentors), random.randint(1, 2))))
            courses.append(course)

        # enrollments + payments + drops
        for course in courses:
            group = random.sample(students, k=min(len(students), random.randint(4, 14)))
            course.students.set(group)
            for st in group:
                tuition = random.choice([course.price, course.price * 2, course.price * 3])
                Enrollment.objects.get_or_create(student=st, course=course, defaults={"tuition_amount": tuition})
                paid = random.choice([0, tuition * 0.5, tuition])
                if paid:
                    Payment.objects.create(
                        student=st,
                        course=course,
                        amount=paid,
                        method=random.choice(["cash", "bank", "card"]),
                        created_at=now - timedelta(days=random.randint(0, 40)),
                    )

            # a couple drops
            for st in random.sample(group, k=min(len(group), random.randint(0, 2))):
                CourseDrop.objects.get_or_create(
                    course=course,
                    student=st,
                    defaults={"reason": random.choice(["Переезд", "Не успевает", "По здоровью", ""])},
                )

        # salaries
        for m in mentors:
            Salary.objects.create(mentor=m, amount=random.choice([15000, 25000, 35000]), created_at=now - timedelta(days=random.randint(0, 50)))

        # leads
        for _ in range(20):
            Lead.objects.create(
                full_name=_name(),
                phone_number=_phone(),
                status=random.choice([Lead.Status.NEW, Lead.Status.IN_PROGRESS, Lead.Status.WON, Lead.Status.LOST]),
                created_at=now - timedelta(days=random.randint(0, 45)),
            )

        # calls
        for _ in range(15):
            Call.objects.create(
                contact_name=_name(),
                phone_number=_phone(),
                status=random.choice([Call.Status.NEW, Call.Status.DONE, Call.Status.MISSED]),
                created_at=now - timedelta(days=random.randint(0, 20)),
            )

        # calendar
        for d in range(1, 8):
            start = now + timedelta(days=d, hours=random.randint(9, 17))
            CalendarEvent.objects.create(
                title=random.choice(["Созвон", "Встреча", "Планирование", "Урок"]),
                course=random.choice(courses),
                start_at=start,
                end_at=start + timedelta(hours=1),
                location=random.choice(["", "Офис", "Каб. 4"]),
                online_link=random.choice(["", "https://meet.google.com/demo-link"]),
                description=random.choice(["", "Короткое описание мероприятия"]),
                note=random.choice(["", "По Zoom", "В офисе"]),
            )

        # accounting
        for _ in range(10):
            AccountingEntry.objects.create(
                entry_type=random.choice([AccountingEntry.Type.INCOME, AccountingEntry.Type.EXPENSE]),
                title=random.choice(["Аренда", "Реклама", "Канцелярия", "Оплата обучения"]),
                amount=random.choice([5000, 12000, 25000, 3500]),
                created_at=now - timedelta(days=random.randint(0, 60)),
            )

        # tasks
        for _ in range(8):
            Task.objects.create(
                title=random.choice(["Позвонить лиду", "Собрать оплату", "Проверить посещаемость", "Сформировать отчет"]),
                due_date=today + timedelta(days=random.randint(0, 5)),
                is_done=random.choice([False, False, True]),
            )

        self.stdout.write(self.style.SUCCESS("Demo data seeded. Login: admin / admin"))

    def _create_mentors(self, count: int):
        mentors = []
        for i in range(count):
            full_name = _name()
            username = f"mentor{i+1}"
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": full_name.split(" ")[0],
                    "last_name": full_name.split(" ")[1],
                    "phone_number": _phone(),
                    "email": f"{username}@example.com",
                    "is_staff": True,
                },
            )
            mentor, _ = Mentor.objects.get_or_create(user=user)
            mentors.append(mentor)
        return mentors

    def _create_students(self, count: int):
        students = []
        for i in range(count):
            full_name = _name()
            username = f"student{i+1}"
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": full_name.split(" ")[0],
                    "last_name": full_name.split(" ")[1],
                    "phone_number": _phone(),
                    "email": f"{username}@example.com",
                },
            )
            student, _ = Student.objects.get_or_create(user=user)
            students.append(student)
        return students

    def _reset(self):
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
        Student.objects.all().delete()
        Mentor.objects.all().delete()
