from django.test import SimpleTestCase
from django.urls import reverse


class PortalLoginTemplateTests(SimpleTestCase):
    def test_login_page_keeps_csrf_token_in_sync(self):
        response = self.client.get(reverse("portal_login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="portal-login-form"')
        self.assertContains(response, "syncCsrfToken")
        self.assertContains(response, 'getCookie("csrftoken")')
