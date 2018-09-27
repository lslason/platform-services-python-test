from django import forms

class SubmitRewardsForm(forms.Form):
    email = forms.CharField(required=True)
    order = forms.DecimalField(required=True)


class CustomerFilterForm(forms.Form):
    email = forms.CharField(required=False)
