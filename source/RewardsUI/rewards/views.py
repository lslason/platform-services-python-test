import logging
import requests

from django.template.response import TemplateResponse
from django.views.generic.base import TemplateView

from .forms import SubmitRewardsForm, CustomerFilterForm


class RewardsView(TemplateView):
    template_name = 'index.html'
    api = "rewardsservice:7050"

    def _load_data(self, context, customer_filter=None):
        response = requests.get("http://{}/rewards".format(self.api))
        context['rewards_data'] = response.json()
        # self.logger.info("MSG=Retrieved rewards, COUNT{}".format(len(context["rewards_data"])))
        if customer_filter:
            response = requests.get("http://{}/customer_rewards?email={}".format(self.api, customer_filter))
        else:
            response = requests.get("http://{}/customer_rewards".format(self.api))
        context["customer_rewards_data"] = response.json()
        context["order_form"] = SubmitRewardsForm()
        context["customer_filter_form"] = CustomerFilterForm({"email":customer_filter})


    def __init__(self, logger=logging.getLogger(__name__)):
        self.logger = logger

    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        form = CustomerFilterForm(request.GET)
        form.is_valid()
        data = form.cleaned_data
        self._load_data(context, customer_filter=data.get("email"))
        return TemplateResponse(request, self.template_name, context)

    
    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        form = SubmitRewardsForm(request.POST)
        form.is_valid()
        data = form.cleaned_data
        normalized = {"email":data["email"], "order_total":float(data["order"])}
        response = requests.put("http://{}/customer_rewards".format(self.api), json=normalized)
        self._load_data(context)
        return TemplateResponse(request, self.template_name, context)
