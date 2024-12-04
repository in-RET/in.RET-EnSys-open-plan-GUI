import logging

from dashboard.helpers import *
from dashboard.models import (
    get_project_reportitems,
)
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import HttpResponseRedirect, get_object_or_404
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from jsonview.decorators import json_view
from projects.constants import COMPARE_VIEW
from projects.models import (
    Project,
    Simulation,
)
from projects.services import (
    get_selected_scenarios_in_cache,
)

from .reportdash import createDashboard

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def result_change_project(request):
    proj_id = int(request.POST.get("proj_id"))
    if request.session[COMPARE_VIEW] is False:
        answer = HttpResponseRedirect(
            reverse("project_visualize_results", args=[proj_id])
        )
    else:
        answer = HttpResponseRedirect(
            reverse("project_compare_results", args=[proj_id])
        )
    return answer


@login_required
@require_http_methods(["POST", "GET"])
def scenario_visualize_results(request, proj_id=None, scen_id=None):
    qs = Simulation.objects.filter(scenario_id=scen_id)

    if qs.exists():
        simulation = qs.first()

    createDashboard(simulation)

    answer = render(
        request,
        "report/single_scenario.html",
        {"proj_id": proj_id, "scen_id": scen_id, "workdir": simulation.mvs_token},
    )

    return answer


@login_required
@require_http_methods(["POST", "GET"])
def project_compare_results(request, proj_id):
    request.session[COMPARE_VIEW] = True
    user_projects = request.user.project_set.all()

    project = get_object_or_404(Project, id=proj_id)
    if (project.user != request.user) and (request.user not in project.viewers.all()):
        raise PermissionDenied

    user_scenarios = project.get_scenarios_with_results()
    report_items_data = [
        ri.render_json
        for ri in get_project_reportitems(project)
        .annotate(c=Count("simulations"))
        .filter(c__gt=1)
    ]

    selected_scenarios = get_selected_scenarios_in_cache(request, proj_id)
    return render(
        request,
        "report/compare_scenario.html",
        {
            "proj_id": proj_id,
            "project_list": user_projects,
            "scenario_list": user_scenarios,
            "selected_scenarios": selected_scenarios,
            "report_items_data": report_items_data,
            "kpi_list": KPI_PARAMETERS,
            "table_styles": TABLES,
        },
    )


@login_required
@json_view
@require_http_methods(["GET"])
def update_selected_single_scenario(request, proj_id, scen_id):
    proj_id = str(proj_id)
    scen_id = str(scen_id)
    if request.is_ajax():
        status_code = 200
        selected_scenarios_per_project = request.session.get("selected_scenarios", {})
        selected_scenario = selected_scenarios_per_project.get(proj_id, [])

        if scen_id in selected_scenario:
            if len(selected_scenario) > 1:
                selected_scenario.pop(selected_scenario.index(scen_id))
                msg = _(f"Scenario {scen_id} was deselected")
            else:
                msg = _(f"At least one scenario need to be selected")
                status_code = 405
        else:
            selected_scenario = [scen_id]
            msg = _(f"Scenario {scen_id} was selected")
        selected_scenarios_per_project[proj_id] = selected_scenario
        request.session["selected_scenarios"] = selected_scenarios_per_project
        answer = JsonResponse(
            {"success": msg}, status=status_code, content_type="application/json"
        )
    else:
        answer = JsonResponse(
            {"error": "This url is only for AJAX calls"},
            status=405,
            content_type="application/json",
        )
    return answer
