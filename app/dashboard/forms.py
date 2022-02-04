from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.forms import ModelForm
from dashboard.models import ReportItem


class ReportItemForm(ModelForm):
    class Meta:
        model = ReportItem
        exclude = ['id']

class TimeseriesGraphForm(forms.Form):
    vector = forms.ChoiceField(
        label=_("Energy vector"), choices=ENERGY_VECTOR, initial=ENERGY_VECTOR[1][0]
    )
    y = forms.MultipleChoiceField(
        label=_("Timeseries variable(s)"),
        choices=tuple([(k, KPI_PARAMETERS[k]["verbose"]) for k in KPI_PARAMETERS]),
    )


def graph_parameters_form_factory(report_type, *args, **kwargs):
    if report_type == GRAPH_TIMESERIES:
        answer = TimeseriesGraphForm(*args, **kwargs)
    # GRAPH_TIMESERIES_STACKED,
    # GRAPH_CAPACITIES,
    # GRAPH_BAR,
    # GRAPH_PIE,
    # GRAPH_LOAD_DURATION,
    # GRAPH_SANKEY,
    return answer
