from django.test import TestCase, override_settings
from django.urls import reverse


class PrivacyPolicyViewTests(TestCase):
    @override_settings(PRIVACY_CONTACT_EMAIL='privacidade@example.com')
    def test_privacy_policy_is_public_and_displays_contact(self):
        response = self.client.get(reverse('privacy-policy'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Política de Privacidade')
        self.assertContains(response, 'privacidade@example.com')
        self.assertContains(response, 'Exclusão da conta')
