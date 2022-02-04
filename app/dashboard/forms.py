from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.forms import ModelForm
from dashboard.models import ReportItem


class ReportItemForm(ModelForm):
    class Meta:
        model = ReportItem
        exclude = ['id']
