from django.conf import settings
from django.views.generic import TemplateView


class PrivacyPolicyView(TemplateView):
    template_name = 'app/privacy_policy.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['privacy_contact_email'] = settings.PRIVACY_CONTACT_EMAIL
        return context
