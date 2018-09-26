import logging
import requests

from django.template.response import TemplateResponse
from django.views.generic.base import TemplateView


class RewardsView(TemplateView):
    template_name = 'index.html'

    def __init__(self, logger=logging.getLogger(__name__)):
        self.logger = logger

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        response = requests.get("http://rewardsservice:7050/rewards")
        context['rewards_data'] = response.json()
        response = requests.get("http://rewardsservice:7050/customer_rewards")
        context["customer_rewards_data"] = response.json()

        return TemplateResponse(
            request,
            self.template_name,
            context
        )
