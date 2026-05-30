from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from app.settings.admin import CRMUserCreationForm
from app.settings.admin_site import _require_valid_password
from app.settings.models import Cursues, Lesson, Mentor, Parent, Student, StudentGrade, User


class ParentDashboardViewTests(TestCase):
    def setUp(self):
        self.parent_user = User.objects.create_user(
            username="parent-user",
            password="testpass123",
            first_name="Айжан",
            last_name="Токтосунова",
            phone_number="+996700000001",
            role="Родитель",
        )
        self.parent_profile = Parent.objects.create(
            user=self.parent_user,
            phone_number="+996700000001",
        )

        self.mentor_user = User.objects.create_user(
            username="mentor-user",
            password="testpass123",
            first_name="Руслан",
            last_name="Эшимов",
            phone_number="+996700000002",
            role="Ментор",
        )
        self.mentor = Mentor.objects.create(user=self.mentor_user)

        self.student_user = User.objects.create_user(
            username="student-one",
            password="testpass123",
            first_name="Алмаз",
            last_name="Садыков",
            phone_number="+996700000003",
            role="Студент",
        )
        self.student = Student.objects.create(user=self.student_user, status=Student.Status.ACTIVE)

        self.other_student_user = User.objects.create_user(
            username="student-two",
            password="testpass123",
            first_name="Нуржан",
            last_name="Ибраимов",
            phone_number="+996700000004",
            role="Студент",
        )
        self.other_student = Student.objects.create(
            user=self.other_student_user,
            status=Student.Status.ACTIVE,
        )

        self.parent_profile.students.add(self.student)

        self.course = Cursues.objects.create(
            title="IELTS Evening",
            start=date(2026, 1, 10),
            status="Активные курсы",
            subject="IELTS",
        )
        self.course.students.add(self.student)

        self.lesson_one = Lesson.objects.create(
            mentor=self.mentor,
            course=self.course,
            title="Reading Basics",
            order=1,
            date=date(2026, 1, 10),
        )
        self.lesson_two = Lesson.objects.create(
            mentor=self.mentor,
            course=self.course,
            title="Listening Basics",
            order=2,
            date=date(2026, 1, 12),
        )
        StudentGrade.objects.create(
            lesson=self.lesson_one,
            student=self.student,
            grade=1,
            comment="Хорошая активность",
        )
        StudentGrade.objects.create(
            lesson=self.lesson_two,
            student=self.student,
            grade=0,
            comment="Пропуск без предупреждения",
        )

        self.other_course = Cursues.objects.create(
            title="SAT Morning",
            start=date(2026, 2, 1),
            status="Активные курсы",
            subject="SAT",
        )
        self.other_course.students.add(self.other_student)
        self.other_lesson = Lesson.objects.create(
            mentor=self.mentor,
            course=self.other_course,
            title="Math Drill",
            order=1,
            date=date(2026, 2, 1),
        )
        StudentGrade.objects.create(
            lesson=self.other_lesson,
            student=self.other_student,
            grade=1,
            comment="Не должен отображаться у другого родителя",
        )

    def test_parent_dashboard_shows_only_linked_student_data(self):
        self.client.force_login(self.parent_user)

        response = self.client.get(reverse("parent_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_student"], self.student)
        self.assertEqual(response.context["selected_course"], self.course)
        self.assertEqual(len(response.context["lesson_cells"]), 2)
        self.assertEqual(response.context["attendance_total"], 1)
        self.assertContains(response, "Алмаз Садыков")
        self.assertNotContains(response, "Нуржан Ибраимов")

    def test_parent_can_switch_between_linked_students(self):
        self.parent_profile.students.add(self.other_student)
        self.client.force_login(self.parent_user)

        response = self.client.get(
            reverse("parent_dashboard"),
            {"student_id": self.other_student.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_student"], self.other_student)
        self.assertEqual(response.context["selected_course"], self.other_course)
        self.assertEqual(len(response.context["lesson_cells"]), 1)
        self.assertContains(response, "SAT Morning")

    def test_non_parent_cannot_open_parent_dashboard(self):
        self.client.force_login(self.student_user)

        response = self.client.get(reverse("parent_dashboard"))

        self.assertEqual(response.status_code, 403)

    def test_authenticated_parent_can_open_login_page_for_account_switch(self):
        self.client.force_login(self.parent_user)

        response = self.client.get(reverse("portal_login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Сейчас вы вошли как")
        self.assertContains(response, "Выйти из текущего аккаунта")

    def test_portal_logout_clears_session(self):
        self.client.force_login(self.parent_user)

        response = self.client.get(reverse("portal_logout"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("portal_login"))
        response = self.client.get(reverse("parent_dashboard"))
        self.assertEqual(response.status_code, 302)


class AdminUserPasswordTests(TestCase):
    def test_user_creation_form_hashes_password(self):
        form = CRMUserCreationForm(
            data={
                "username": "manager-user",
                "first_name": "Менеджер",
                "last_name": "Тестовый",
                "email": "manager@example.com",
                "phone_number": "+996700000005",
                "role": "Менеджер",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
                "is_staff": "on",
                "is_active": "on",
            }
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        user = form.save()
        self.assertNotEqual(user.password, "StrongPass123")
        self.assertTrue(user.check_password("StrongPass123"))

    def test_required_password_helper_rejects_empty_password(self):
        user = User(username="temp-user", phone_number="+996700000006", role="Менеджер")

        with self.assertRaises(ValidationError):
            _require_valid_password("", user)
