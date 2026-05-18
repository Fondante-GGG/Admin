import json

from django.test import TestCase

from app.academy.models import Contacts, Courses, TypeCourse
from app.settings.models import Lead, Organization


class ChatMessageViewTests(TestCase):
    def setUp(self):
        Organization.objects.create(name="American Dream")
        direction = TypeCourse.objects.create(title="IELTS")
        self.course = Courses.objects.create(
            title="IELTS Master",
            direction=direction,
            photo="courses/test.png",
            price=12000,
            duration_months=6,
            discounted_price=10000,
            monthly_price=3500,
            color_theme="green",
            title_model="IELTS",
            description_model="Course description",
        )
        Contacts.objects.create(
            phone_numbers="+996 700 000 000",
            email="academy@example.com",
            address="Osh",
            links_email="mailto:academy@example.com",
            links_address="https://maps.example.com",
        )

    def test_chat_message_creates_lead(self):
        response = self.client.post(
            "/chat/message/",
            data=json.dumps({"message": "Сколько стоит IELTS Master?"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Lead.objects.count(), 1)

        lead = Lead.objects.get()
        self.assertEqual(lead.source, "website_chat")
        self.assertIn("IELTS Master", lead.message)
        self.assertIn("IELTS Master", lead.bot_reply)

    def test_chat_message_updates_same_lead_for_same_session(self):
        self.client.post(
            "/chat/message/",
            data=json.dumps({"message": "Какие курсы есть?"}),
            content_type="application/json",
        )
        self.client.post(
            "/chat/message/",
            data=json.dumps(
                {
                    "message": "Мой номер +996 555 123 456, хочу записаться",
                    "name": "Алина",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(Lead.objects.count(), 1)

        lead = Lead.objects.get()
        self.assertEqual(lead.full_name, "Алина")
        self.assertEqual(lead.phone_number, "+996555123456")
        self.assertIn("Какие курсы есть?", lead.conversation_log)
        self.assertIn("хочу записаться", lead.conversation_log)
