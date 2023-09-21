# pylint: disable=undefined-variable, import-error, wildcard-import
# from bootstrap_modal_forms.generic import BSModalCreateView
import json
import logging
import traceback
import shutil
import numpy as np
from datetime import datetime
import re

import requests
from requests.exceptions import HTTPError
from requests import get
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.http.response import Http404
from django.shortcuts import *
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from dashboard.reportdash import createDashboard
from epa.settings import (
    INRETENSYS_CHECK_URL,
    INRETENSYS_LP_FILE_URL,
    OEP_URL,
)
from InRetEnsys import *
from InRetEnsys.types import Solver, Constraints
from jsonview.decorators import json_view
from projects.helpers import epc_calc, format_scenario_for_mvs, polate_unknown_capex, expert_trafo_parameter_visibility, build_oemof_trafo_expert
from projects.models import *

from .constants import DONE, ERROR, MODIFIED, PENDING
from .forms import *
from .requests import (
    fetch_mvs_simulation_results,
    mvs_simulation_request,
)
from .scenario_topology_helpers import (
    NodeObject,
    duplicate_scenario_connections,
    duplicate_scenario_objects,
    handle_asset_form_post,
    handle_bus_form_post,
    handle_storage_unit_form_post,
    load_project_from_dict,
    load_scenario_from_dict,
    load_scenario_topology_from_db,
    update_deleted_objects_from_database,
)
from .services import (
    create_or_delete_simulation_scheduler,
    excuses_design_under_development,
    get_selected_scenarios_in_cache,
    send_feedback_email,
)
from django.template.loader import get_template
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def not_implemented(request):
    """Function returns a message"""
    redirect_name = request.GET.get("url")
    excuses_design_under_development(request, link=True)

    return redirect(redirect_name)


@require_http_methods(["GET"])
def home(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("project_search"))
    else:
        return render(request, "index.html")


@login_required
@require_http_methods(["POST"])
def scenario_upload(request, proj_id):

    # read the scenario file to a dict
    scenario_data = request.FILES["file"].read()
    scenario_data = json.loads(scenario_data)

    project = get_object_or_404(Project, id=proj_id)

    if project.user != request.user:
        raise PermissionDenied

    new_scenario_name = request.POST.get("name")

    # make a single scenario within a list
    if isinstance(scenario_data, list) is False:
        scenario_data = [scenario_data]

    # load each of the scenario from the file into the database
    n_scenarios = len(scenario_data)
    for i, scen in enumerate(scenario_data):
        if new_scenario_name != "":
            if n_scenarios > 1:
                scen["name"] = f"{new_scenario_name}_{i+1}"
            else:
                scen["name"] = new_scenario_name

        scen_id = load_scenario_from_dict(scen, user=request.user, project=project)

    return HttpResponseRedirect(reverse("project_search", args=[proj_id, scen_id]))


# region Project


@login_required
@require_http_methods(["GET", "POST"])
def user_feedback(request):
    form = FeedbackForm(request.POST or None)
    if request.POST:
        if form.is_valid():
            feedback = form.save(commit=False)
            try:
                feedback.rating = [
                    key.split("-")[-1]
                    for key in request.POST.keys()
                    if key.startswith("rating")
                ][0]
            except:
                feedback.rating = None
            feedback.save()
            subject = f"[open_plan] Feedback for ensys tool - {feedback.subject}"
            body = f"Feedback form for ensys tool online api\n\nReceived Feedback\n-----------------\n\nTopic: {feedback.subject}\nContent: {feedback.feedback}\n\nInformation about sender\n------------------------\nName: {feedback.name}\n E-mail Address: {feedback.email}"
            try:
                send_feedback_email(subject, body)
                messages.success(request, f"Thank you for your feedback.")
            except Exception as e:
                messages.success(request, e)
            return HttpResponseRedirect(reverse("project_search"))
    return render(request, "feedback.html", {"form": form})


@login_required
@json_view
@require_http_methods(["GET"])
def project_members_list(request, proj_id):
    project = get_object_or_404(Project, pk=proj_id)

    if project.user != request.user:
        return JsonResponse(
            {"status": "error", "message": "Project does not belong to you."},
            status=403,
            content_type="application/json",
        )

    viewers = project.viewers.values_list("email", flat=True)
    return JsonResponse(
        {"status": "success", "viewers": list(viewers)},
        status=201,
        content_type="application/json",
    )


@login_required
@require_http_methods(["POST"])
def project_share(request, proj_id):
    qs = request.POST

    project = get_object_or_404(Project, id=proj_id)

    if project.user != request.user:
        raise PermissionDenied

    form_item = ProjectShareForm(qs)

    if form_item.is_valid():
        success, message = project.add_viewer_if_not_exist(**form_item.cleaned_data)
        if success is True:
            messages.success(request, message)
        else:
            messages.error(request, message)

    return HttpResponseRedirect(reverse("project_search", args=[proj_id]))


@login_required
@json_view
@require_http_methods(["POST"])
def project_revoke_access(request, proj_id=None):
    qs = request.POST

    project = get_object_or_404(Project, id=proj_id)

    if project.user != request.user:
        raise PermissionDenied
    form_item = ProjectRevokeForm(qs, proj_id=proj_id)
    if form_item.is_valid():
        success, message = project.revoke_access(**form_item.cleaned_data)
        if success is True:
            messages.success(request, message)
        else:
            messages.error(request, message)

    return HttpResponseRedirect(reverse("project_search", args=[proj_id]))


@login_required
@json_view
@require_http_methods(["POST"])
def ajax_project_viewers_form(request):

    if request.is_ajax():
        proj_id = int(request.POST.get("proj_id"))
        project = get_object_or_404(Project, id=proj_id)

        if project.user != request.user:
            raise PermissionDenied
        form_item = ProjectRevokeForm(proj_id=proj_id)

        return render(
            request,
            "project/project_viewers_form.html",
            context={"form_item": form_item},
        )


@login_required
@require_http_methods(["GET"])
def project_detail(request, proj_id):
    project = get_object_or_404(Project, pk=proj_id)

    if (project.user != request.user) and (request.user not in project.viewers.all()):
        raise PermissionDenied

    logger.info(f"Populating project and economic details in forms.")
    project_form = ProjectDetailForm(None, instance=project)
    economic_data_form = EconomicDataDetailForm(None, instance=project.economic_data)

    return render(
        request,
        "project/project_detail.html",
        {"project_form": project_form, "economic_data_form": economic_data_form},
    )


@login_required
@require_http_methods(["GET", "POST"])
def project_create(request):
    if request.POST:
        form = ProjectCreateForm(request.POST)
        if form.is_valid():
            logger.info(f"Creating new project with economic data.")
            economic_data = EconomicData.objects.create(
                # duration=form.cleaned_data["duration"],
                currency=form.cleaned_data["currency"],
                # discount=form.cleaned_data["discount"],
                # tax=form.cleaned_data["tax"],
            )

            project = Project.objects.create(
                name=form.cleaned_data["name"],
                description=form.cleaned_data["description"],
                country=form.cleaned_data["country"],
                longitude=form.cleaned_data["longitude"],
                latitude=form.cleaned_data["latitude"],
                unit_choice=form.cleaned_data["unit_choice"],
                unit_choice_co2=form.cleaned_data["unit_choice_co2"],
                user=request.user,
                economic_data=economic_data,
            )
            return HttpResponseRedirect(reverse("project_search", args=[project.id]))
    else:
        form = ProjectCreateForm()
    return render(request, "project/project_create.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def project_update(request, proj_id):
    project = get_object_or_404(Project, id=proj_id)

    if project.user != request.user:
        raise PermissionDenied
        # return HttpResponseForbidden()

    project_form = ProjectUpdateForm(request.POST or None, instance=project)
    economic_data_form = EconomicDataUpdateForm(
        request.POST or None, instance=project.economic_data
    )

    if (
        request.method == "POST"
        and project_form.is_valid()
        and economic_data_form.is_valid()
    ):
        logger.info(f"Updating project with economic data...")
        project_form.save()
        economic_data_form.save()
        # Save was successful, so send message
        messages.success(request, "Project Info updated successfully!")
        return HttpResponseRedirect(reverse("project_search", args=[proj_id]))

    return render(
        request,
        "project/project_update.html",
        {"project_form": project_form, "economic_data_form": economic_data_form},
    )


@login_required
@require_http_methods(["GET", "POST"])
def project_export(request, proj_id):

    project = get_object_or_404(Project, id=proj_id)

    if project.user != request.user:
        raise PermissionDenied

    if request.method == "POST":
        bind_scenario_data = request.POST.get("bind_scenario_data", True)
        if bind_scenario_data == "True":
            bind_scenario_data = True
        if bind_scenario_data == "False":
            bind_scenario_data = False
    else:
        bind_scenario_data = True

    if project.user != request.user:
        raise PermissionDenied

    response = HttpResponse(
        json.dumps(project.export(bind_scenario_data=bind_scenario_data)),
        content_type="application/json",
    )
    response["Content-Disposition"] = f"attachment; filename=project{project.id}.json"
    return response


@login_required
@require_http_methods(["POST"])
def project_upload(request):

    # read the project file to a dict
    project_data = request.FILES["file"].read()
    project_data = json.loads(project_data)

    new_project_name = request.POST.get("name")

    if new_project_name != "":
        project_data["name"] = new_project_name

    proj_id = load_project_from_dict(project_data, request.user)

    return HttpResponseRedirect(reverse("project_search", args=[proj_id]))


@login_required
@require_http_methods(["POST"])
def project_from_usecase(request):
    usecase_id = request.POST.get("usecase", None)
    if usecase_id is not None:
        usecase_id = int(usecase_id)
    else:
        usecase_id = 0
    usecase = get_object_or_404(UseCase, id=usecase_id)
    proj_id = usecase.assign(request.user)

    return HttpResponseRedirect(reverse("project_search", args=[proj_id]))


@login_required
@require_http_methods(["POST"])
def project_delete(request, proj_id):
    project = get_object_or_404(Project, id=proj_id)

    if project.user != request.user:
        raise PermissionDenied

    if request.method == "POST":
        project.delete()
        messages.success(request, "Project successfully deleted!")

    return HttpResponseRedirect(reverse("project_search"))


@login_required
@require_http_methods(["GET"])
def project_search(request, proj_id=None, scen_id=None):
    # project_list = Project.objects.filter(user=request.user)
    # shared_project_list = Project.objects.filter(viewers=request.user)
    combined_projects_list = Project.objects.filter(
        Q(user=request.user) | Q(viewers__user=request.user)
    ).distinct()

    scenario_upload_form = UploadFileForm(
        labels=dict(name=_("New scenario name"), file=_("Scenario file"))
    )
    project_upload_form = UploadFileForm(
        labels=dict(name=_("New project name"), file=_("Project file"))
    )
    project_share_form = ProjectShareForm()
    project_revoke_form = ProjectRevokeForm(proj_id=proj_id)
    usecase_form = UseCaseForm(
        usecase_qs=UseCase.objects.all(), usecase_url=reverse("usecase_search")
    )

    return render(
        request,
        "project/project_search.html",
        {
            "project_list": combined_projects_list,
            "proj_id": proj_id,
            "scen_id": scen_id,
            "scenario_upload_form": scenario_upload_form,
            "project_upload_form": project_upload_form,
            "project_share_form": project_share_form,
            "project_revoke_form": project_revoke_form,
            "usecase_form": usecase_form,
            "translated_text": {
                "showScenarioText": _("Show scenarios"),
                "hideScenarioText": _("Hide scenarios"),
            },
        },
    )


@login_required
@require_http_methods(["POST"])
def project_duplicate(request, proj_id):
    """Duplicates the selected project along with its associated scenarios"""
    project = get_object_or_404(Project, pk=proj_id)

    # duplicate the project
    dm = project.export(bind_scenario_data=True)
    new_proj_id = load_project_from_dict(dm, user=project.user)

    return HttpResponseRedirect(reverse("project_search", args=[new_proj_id]))


# endregion Project

# region Usecase
@login_required
@require_http_methods(["GET"])
def usecase_search(request, usecase_id=None, scen_id=None):

    usecase_list = UseCase.objects.all()

    return render(
        request,
        "usecase/usecase_search.html",
        {
            "usecase_list": usecase_list,
            "usecase_id": usecase_id,
            "scen_id": scen_id,
            "translated_text": {
                "showScenarioText": _("Show scenarios"),
                "hideScenarioText": _("Hide scenarios"),
            },
        },
    )


# endregion Usecase

# region Comment


@login_required
@require_http_methods(["GET", "POST"])
def comment_create(request, proj_id):
    project = get_object_or_404(Project, pk=proj_id)

    if request.POST:
        form = CommentForm(request.POST)
        if form.is_valid():
            Comment.objects.create(
                name=form.cleaned_data["name"],
                body=form.cleaned_data["body"],
                project=project,
            )
            return HttpResponseRedirect(reverse("scenario_search", args=[proj_id, 1]))

    else:  # GET
        form = CommentForm()

    return render(request, "comment/comment_create.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def comment_update(request, com_id):
    comment = get_object_or_404(Comment, pk=com_id)

    if comment.project.user != request.user:
        raise PermissionDenied

    if request.POST:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment.name = form.cleaned_data["name"]
            comment.body = form.cleaned_data["body"]
            comment.save()
            return HttpResponseRedirect(
                reverse("scenario_search", args=[comment.project.id, 1])
            )
    else:  # GET
        form = CommentForm(instance=comment)

    return render(request, "comment/comment_update.html", {"form": form})


@login_required
@require_http_methods(["POST"])
def comment_delete(request, com_id):
    comment = get_object_or_404(Comment, pk=com_id)

    if comment.project.user != request.user:
        raise PermissionDenied

    if request.POST:
        comment.delete()
        messages.success(request, "Comment successfully deleted!")
        return HttpResponseRedirect(
            reverse("scenario_search", args=[comment.project.id, 1])
        )


# endregion Comment


# region Scenario


@login_required
@require_http_methods(["GET"])
def scenario_search(request, proj_id, show_comments=0):
    """
    This view renders the scenarios and comments search html template.

    args: proj_id, show_comments
    proj_id: The Project id the user requests to observe associated scenarios and comments.
    show_comments: An integer flag to indicate wether the page will open on scenarios tab or comments tab.
    If show_comments==1 the html page will load and following a click event will change the active tab to comments.
    Otherwise the default scenarios tab will be presented to the user.

    Returns: A rendered html template.
    """
    project = get_object_or_404(Project, pk=proj_id)
    return render(
        request,
        "scenario/scenario_search.html",
        {
            "comment_list": project.comment_set.all(),
            "scenarios_list": project.scenario_set.all(),
            "project": project,
            "show_comments": show_comments,
        },
    )


STEP_LIST = [
    _("Scenario Setup"),
    _("Energy system design"),
    _("Constraints"),
    _("Simulation"),
    _("Results")
]


@login_required
@require_http_methods(["GET", "POST"])
def scenario_select_project(request, step_id=0, max_step=1):
    user_projects = request.user.project_set.all()
    if request.method == "GET":

        if user_projects.exists():
            form = ScenarioSelectProjectForm(project_queryset=user_projects)
            answer = render(
                request,
                f"scenario/scenario_step{step_id}.html",
                {
                    "form": form,
                    "step_id": step_id,
                    "step_list": [_("Project selection")] + STEP_LIST,
                    "max_step": max_step,
                },
            )
        else:
            messages.info(
                request, _("You have currently no projects, please create one first")
            )
            answer = HttpResponseRedirect(reverse("project_search"))

    elif request.method == "POST":
        form = ScenarioSelectProjectForm(request.POST, project_queryset=user_projects)

        if form.is_valid():
            proj_id = form.cleaned_data.get("project").id
            answer = HttpResponseRedirect(
                reverse("scenario_create_parameters", args=[proj_id])
            )

    return answer


@login_required
@require_http_methods(["GET", "POST"])
def scenario_create_parameters(request, proj_id, scen_id=None, step_id=1, max_step=2):

    project = get_object_or_404(Project, pk=proj_id)
    # all projects which the user is able to select (the one the user created)
    user_projects = request.user.project_set.all()

    form = ScenarioCreateForm(
        initial={"project": project,
                 "evaluated_period": 365}, 
        project_queryset=user_projects
    )
    if scen_id == "None":
        scen_id = None

    if request.method == "GET":
        if scen_id is not None:
            scenario = get_object_or_404(Scenario, id=scen_id)

            if (scenario.project.user != request.user) and (request.user not in scenario.project.viewers.all()):
                raise PermissionDenied

            form = ScenarioUpdateForm(None, instance=scenario, project_queryset=user_projects)

            # if a simulation object linked to this scenario exists, all steps have been already fullfilled
            qs_sim = Simulation.objects.filter(scenario=scenario)
            if qs_sim.exists():
                max_step = 6
            else:
                # if a connexion object linked to this scenario exists, topology has already been saved once
                qs_topo = ConnectionLink.objects.filter(scenario_id=scen_id)
                if qs_topo.exists():
                    max_step = 3
        else:
            scenario = None
        
        answer = render(
            request,
            f"scenario/scenario_step{step_id}.html",
            {
                "form": form,
                "proj_id": proj_id,
                "proj_name": project.name,
                "scenario": scenario,
                "scen_id": scen_id,
                "step_id": step_id,
                "step_list": STEP_LIST,
                "max_step": max_step,
            },
        )

    elif request.method == "POST":
        print("POST")
        print(request.POST)


        if scen_id is None:
            scenario = Scenario()
            form = ScenarioCreateForm(request.POST, project_queryset=user_projects)
        else:
            scenario = Scenario.objects.get(id=scen_id)
            form = ScenarioUpdateForm(request.POST, project_queryset=user_projects)

        print(form.errors)

        if form.is_valid():
            qs_sim = Simulation.objects.filter(scenario=scenario)
            # update the parameter values which are different from existing values
            for name, value in form.cleaned_data.items():
                if getattr(scenario, name) != value:
                    setattr(scenario, name, value)
                    if qs_sim.exists():
                        qs_sim.update(status=MODIFIED)

            # update the project associated to the scenario
            proj_id = scenario.project.id
            scenario.save()
            answer = HttpResponseRedirect(
                reverse("scenario_create_topology", args=[proj_id, scenario.id])
            )

    return answer


@login_required
@require_http_methods(["GET", "POST"])
def scenario_create_topology(request, proj_id, scen_id, step_id=2, max_step=3):

    components_default_user = {
        "production": {
            "myPredefinedSource": _("Predefined Source"),
        },
        "conversion": {
            "myPredefinedTransformer": _("Predefined Transformer"),
        },
        "storage": {
            "myPredefinedStorage": _("Predefined Storage"),
        },
        "demand": {
            "myExcess": _("Excess"),
            "myExport": _("Export"),
            "myPredefinedSink": _("Predefined Load Profile"),
            "myPredefinedSinkOEP": _("Load profile from the Open Energy Platform"),
        },
        "bus": {"bus": _("Connecting Line")},
    }
    
    components_expert = {
        "production": {
            "mySource": _("Source"),
            "myPredefinedSource": _("Predefined Source")
        },
        "conversion": {
            "myTransformer": _("Transformer"),
            "myPredefinedTransformer": _("Predefined Transformer"),
        },
        "storage": {
            "myGenericStorage": _("GenericStorage"),
            "myPredefinedStorage": _("Predefined Storage"),
        },
        "demand": {
            "mySink": _("Sink"),
            "myExcess": _("Excess"),
            "myPredefinedSinkOEP": _("Load profile from the Open Energy Platform")
        },
        "bus": {"bus": _("Bus")},
    }
    
    group_names_default_user = {group: _(group) for group in components_default_user.keys()}
    group_names_expert = {group: _(group) for group in components_expert.keys()}

    # TODO: if the scenario exists, load it, otherwise default form

    if request.method == "POST":
        # called by function save_topology() in templates/scenario/scenario_step2.html

        scenario = get_object_or_404(Scenario, pk=scen_id)
        if request.user != scenario.project.user:
            raise PermissionDenied

        topologies = json.loads(request.body)
        node_list = [NodeObject(topology) for topology in topologies]

        # delete objects from database which were deleted by the user
        update_deleted_objects_from_database(scen_id, node_list)
        # Make sure there are no connections in the Database to prevent inserting the same connections upon updating.
        ConnectionLink.objects.filter(scenario_id=scen_id).delete()
        for node_obj in node_list:
            node_obj.create_connection_links(scen_id)
            # node_obj.assign_asset_to_proper_group(node_to_db_mapping_dict)
        return JsonResponse({"success": True}, status=200)
    else:

        scenario = get_object_or_404(Scenario, pk=scen_id)
        print(scenario.user_mode_choice)
        print(scenario.simulation_year)
        
        if scenario.user_mode_choice == "Default User":
            components = components_default_user
            group_names = group_names_default_user
        elif scenario.user_mode_choice == "Expert":
            components = components_expert
            group_names = group_names_expert
            

        # if a simulation object linked to this scenario exists, all steps have been already fullfilled
        qs_sim = Simulation.objects.filter(scenario=scenario)
        if qs_sim.exists():
            max_step = 6

        # this is a dict with keys "busses", "assets" and "links"
        topology_data_list = load_scenario_topology_from_db(scen_id)
        return render(
            request,
            f"scenario/scenario_step{step_id}.html",
            {
                "scenario": scenario,
                "scen_id": scen_id,
                "proj_id": scenario.project.id,
                "proj_name": scenario.project.name,
                "topology_data_list": json.dumps(topology_data_list),
                "step_id": step_id,
                "step_list": STEP_LIST,
                "max_step": max_step,
                "components": components,
                "group_names": group_names,
                "choosenTimestamp": scenario.simulation_year,
            },
        )


@login_required
@require_http_methods(["GET", "POST"])
def scenario_create_constraints(request, proj_id, scen_id, step_id=3, max_step=4):

    constraints_labels = {
        # "minimal_degree_of_autonomy": _("Minimal degree of autonomy"),
        "minimal_renewable_factor": _(
            "'Bilanziell erneuerbar'/Bilanzielle Autarkie [MWh]"
        ),
        "maximum_emissions": _("Maximal CO2 emissions"),
        # "net_zero_energy": _("Net zero energy system"),
    }
    constraints_forms = {
        # "minimal_degree_of_autonomy": MinDOAConstraintForm,
        "minimal_renewable_factor": MinRenewableConstraintForm,
        "maximum_emissions": MaxEmissionConstraintForm,
        # "net_zero_energy": NZEConstraintForm,
    }

    constraints_models = {
        # "minimal_degree_of_autonomy": MinDOAConstraint,
        "minimal_renewable_factor": MinRenewableConstraint,
        "maximum_emissions": MaxEmissionConstraint,
        # "net_zero_energy": NZEConstraint,
    }

    scenario = get_object_or_404(Scenario, pk=scen_id)

    if (scenario.project.user != request.user) and (
        request.user not in scenario.project.viewers.all()
    ):
        raise PermissionDenied

    qs_sim = Simulation.objects.filter(scenario=scenario)

    if request.method == "GET":

        # if a simulation object linked to this scenario exists, all steps have been already fullfilled
        if qs_sim.exists():
            max_step = 6

        # prepare the forms for each constraint
        unbound_forms = {}
        for constraint_type, constraint_form in constraints_forms.items():
            # check whether the constraint is already associated to the scenario
            qs = constraints_models[constraint_type].objects.filter(scenario=scenario)
            if qs.exists():
                unbound_forms[constraint_type] = constraint_form(
                    prefix=constraint_type, instance=qs[0]
                )
            else:
                unbound_forms[constraint_type] = constraint_form(prefix=constraint_type)
        return render(
            request,
            f"scenario/scenario_step{step_id}.html",
            {
                "scenario": scenario,
                "scen_id": scen_id,
                "proj_id": scenario.project.id,
                "proj_name": scenario.project.name,
                "step_id": step_id,
                "step_list": STEP_LIST,
                "max_step": max_step,
                "forms": unbound_forms,
                "forms_labels": constraints_labels,
            },
        )
    elif request.method == "POST":
        for constraint_type, form_model in constraints_forms.items():
            form = form_model(request.POST, prefix=constraint_type)

            if form.is_valid():
                # check whether the constraint is already associated to the scenario
                qs = constraints_models[constraint_type].objects.filter(
                    scenario=scenario
                )
                if qs.exists():
                    if len(qs) == 1:
                        constraint_instance = qs[0]
                        for name, value in form.cleaned_data.items():
                            if getattr(constraint_instance, name) != value:
                                setattr(constraint_instance, name, value)
                                if qs_sim.exists():
                                    qs_sim.update(status=MODIFIED)

                else:
                    constraint_instance = form.save(commit=False)
                    constraint_instance.scenario = scenario

                if constraint_type == "net_zero_energy":
                    constraint_instance.value = constraint_instance.activated

                constraint_instance.save()

        return HttpResponseRedirect(reverse("scenario_review", args=[proj_id, scen_id]))


@login_required
@require_http_methods(["GET", "POST"])
def scenario_review(request, proj_id, scen_id, step_id=4, max_step=5):

    scenario = get_object_or_404(Scenario, pk=scen_id)

    if (scenario.project.user != request.user) and (request.user not in scenario.project.viewers.all()):
        raise PermissionDenied

    if request.method == "GET":
        html_template = f"scenario/simulation/no-status.html"
        context = {
            "scenario": scenario,
            "scen_id": scen_id,
            "proj_id": scenario.project.id,
            "proj_name": scenario.project.name,
            "step_id": step_id,
            "step_list": STEP_LIST,
            "max_step": max_step,
            "MVS_GET_URL": INRETENSYS_CHECK_URL,
            "MVS_LP_FILE_URL": INRETENSYS_LP_FILE_URL,
        }

        qs = Simulation.objects.filter(scenario_id=scen_id)

        if qs.exists():
            simulation = qs.first()

            if simulation.status == PENDING:
                fetch_mvs_simulation_results(simulation)

            context.update(
                {
                    "sim_id": simulation.id,
                    "simulation_status": simulation.status,
                    "secondsElapsed": simulation.elapsed_seconds,
                    "rating": simulation.user_rating,
                    "mvs_token": simulation.mvs_token,
                }
            )

            if simulation.status == ERROR:
                debugging = {"simulation_error_msg": simulation.errors.splitlines()}
                context.update(debugging)
                html_template = f"scenario/simulation/error.html"
            elif simulation.status == PENDING:
                html_template = f"scenario/simulation/pending.html"
            elif simulation.status == DONE:
                context.update({"max_step": 6})
                html_template = f"scenario/simulation/success.html"
        else:
            print("no simulation existing")

        return render(request, html_template, context)

@login_required
@require_http_methods(["GET", "POST"])
def scenario_results(request, proj_id, scen_id, step_id=5, max_step=6):
    qs = Simulation.objects.filter(scenario_id=scen_id)
    
    scenario = get_object_or_404(Scenario, pk=scen_id)

    if (scenario.project.user != request.user) and (
        request.user not in scenario.project.viewers.all()
    ):
        raise PermissionDenied

    if qs.exists():
        simulation = qs.first()

    createDashboard(simulation)

    html_template = f"scenario/scenario_step5.html"
    
    context = {
        "scenario": scenario,
        "scen_id": scen_id,
        "proj_id": scenario.project.id,
        "proj_name": scenario.project.name,
        "step_id": step_id,
        "step_list": STEP_LIST,
        "max_step": max_step,
        "MVS_GET_URL": INRETENSYS_CHECK_URL,
        "MVS_LP_FILE_URL": INRETENSYS_LP_FILE_URL,
        "workdir": simulation.mvs_token,
    }
    
    return render(request, html_template, context)


@login_required
@require_http_methods(["GET"])
def back_to_scenario_review(request, proj_id):

    selected_scenario = get_selected_scenarios_in_cache(request, proj_id)

    if len(selected_scenario) >= 1:
        scen_id = selected_scenario[0]
        answer = scenario_review(request, proj_id, scen_id)
    else:
        messages.error(
            request,
            _(
                "No scenario was available in the cache, try refreshing the page and make sure one scenario is selected."
            ),
        )
        answer = HttpResponseRedirect(request.headers.get("Referer"))

    return answer


SCENARIOS_STEPS = [
    scenario_create_parameters,
    scenario_create_topology,
    scenario_create_constraints,
    scenario_review,
    scenario_results,
]


@login_required
@require_http_methods(["GET"])
def scenario_steps(request, proj_id, step_id=None, scen_id=None):
    if request.method == "GET":
        if step_id is None:
            return HttpResponseRedirect(reverse("scenario_steps", args=[proj_id, 1]))

        return SCENARIOS_STEPS[step_id - 1](request, proj_id, scen_id, step_id)


# TODO delete this useless code here
@login_required
@require_http_methods(["GET"])
def scenario_view(request, scen_id, step_id):
    """Scenario View. GET request only."""
    scenario = get_object_or_404(Scenario, pk=scen_id)

    if (scenario.project.user != request.user) and (
        request.user not in scenario.project.viewers.all()
    ):
        raise PermissionDenied

    return HttpResponseRedirect(reverse("project_search", args=[scenario.project.id]))


# TODO delete this useless code here
@login_required
@require_http_methods(["GET"])
def scenario_update(request, scen_id, step_id):
    """Scenario Update View. POST request only."""
    scenario = get_object_or_404(Scenario, pk=scen_id)
    if scenario.project.user != request.user:
        raise PermissionDenied
    if request.POST:
        form = ScenarioUpdateForm(request.POST)
        if form.is_valid():
            [
                setattr(scenario, name, value)
                for name, value in form.cleaned_data.items()
            ]
            scenario.save(update_fields=form.cleaned_data.keys())
            return HttpResponseRedirect(
                reverse("project_search", args=[scenario.project.id])
            )
    else:
        raise Http404("An error occurred while updating the Scenario.")


@login_required
@require_http_methods(["GET"])
def scenario_duplicate(request, scen_id):
    """duplicates the selected scenario and all of its associated components (topology data included)"""
    scenario = get_object_or_404(Scenario, pk=scen_id)

    if scenario.project.user != request.user:
        raise PermissionDenied

    # We need to iterate over all the objects related to this scenario and duplicate them
    # and associate them with the new scenario id.
    asset_list = Asset.objects.filter(scenario=scenario)
    bus_list = Bus.objects.filter(scenario=scenario)
    connections_list = ConnectionLink.objects.filter(scenario=scenario)
    # simulation_list = Simulation.objects.filter(scenario=scenario)

    # first duplicate the scenario
    scenario.pk = None
    scenario.save()
    # from now on we are working with the duplicated scenario, not the original
    old2new_asset_ids_map = duplicate_scenario_objects(asset_list, scenario)
    old2new_bus_ids_map = duplicate_scenario_objects(
        bus_list, scenario, old2new_asset_ids_map
    )
    duplicate_scenario_connections(
        connections_list, scenario, old2new_asset_ids_map, old2new_bus_ids_map
    )
    # duplicate_scenario_objects(simulation_list, scenario)

    return HttpResponseRedirect(reverse("project_search", args=[scenario.project.id]))


@login_required
@require_http_methods(["POST"])
def scenario_export(request, proj_id):
    response = HttpResponseRedirect(reverse("project_search", args=[proj_id]))

    # get the selected scenarios under the project view and export them into a file
    scenario_ids = request.POST.get("scenario_ids")
    if scenario_ids is not None:
        scenario_ids = json.loads(scenario_ids)
        scenario_data = []
        for scen_id in scenario_ids:
            scenario = get_object_or_404(Scenario, id=int(scen_id))
            scenario_data.append(scenario.export(bind_project_data=True))
        response = HttpResponse(
            json.dumps(scenario_data), content_type="application/json"
        )
        response["Content-Disposition"] = "attachment; filename=scenario.json"
    return response


@login_required
@require_http_methods(["POST"])
def scenario_delete(request, scen_id):
    scenario = get_object_or_404(Scenario, id=scen_id)
    if scenario.project.user != request.user:
        logger.warning(
            f"Unauthorized user tried to delete project scenario with db id = {scen_id}."
        )
        raise PermissionDenied
    if request.POST:
        scenario.delete()
        messages.success(request, "scenario successfully deleted!")
        return HttpResponseRedirect(
            reverse("project_search", args=[scenario.project.id])
        )


# endregion Scenario

@login_required
@require_http_methods(["POST", "GET"])
def customising_form_expert_trafo(request):
    body_unicode = request.body.decode("utf-8")  # for POST
    body = json.loads(body_unicode)
    print(body)
    combination = body[0]["trafo_input_output_variation"]

    form = AssetCreateForm(
        asset_type="myTransformer",
        initial={
            "name": "",
            "trafo_input_output_variation_choice": combination
        },
    )
    expert_trafo_parameter_visibility(form, combination)
    
    
    
    form_html = get_template("asset/asset_create_form.html")
    return JsonResponse(
        {
            "success": True,
            "form_html": form_html.render(
                {
                    "form": form,
                    # "input_timeseries_data": input_timeseries,
                    # "input_timeseries_timestamps": 8760,
                }
            ),
        },
        status=200,
    )
    

# region Asset
@login_required
@require_http_methods(["POST", "GET"])  # , "POST"
def get_inputparameter_suggestion_source(request):
    body_unicode = request.body.decode("utf-8")  # for POST
    body = json.loads(body_unicode)
    print(body)
    capex, opex, lifetime, crate, efficiency, efficiency_el, efficiency_th = (None,) * 7
    input_timeseries = ""
    technology = body[0]["kindOfComponentSource"]
    year = body[1]["choosenTimestampSource"]
    asset_type_name = "myPredefinedSource"
    
    if (
        technology == "Wind"
        or technology == "Photovoltaic Free Field"
        or technology == "Roof Mounted Photovoltaic"
        # or technology == "Other" #empty queryset
    ):
        if year == "2025" or year == "2035":
            capex, opex, lifetime, input_timeseries = polate_unknown_capex(technology, year, asset_type_name)
        
        else: #2030, 2040, 2045           
            queryset = InputparameterSuggestion.objects.filter(technology=technology, year=year)
            for item in queryset:
                print(item.unique_id, item.capex)
                capex = item.capex
                opex = item.opex
                lifetime = item.lifetime
                # efficiency = item.efficiency
                # efficiency_el = item.efficiency_el
                # efficiency_th = item.efficiency_th
                input_timeseries = item.input_timeseries
            
        form = AssetCreateForm(
            asset_type=asset_type_name,
            initial={
                "name": technology,
                "source_choice": technology,
                "year_choice_source": year,
                "capex": capex,
                "opex": opex,
                "lifetime": lifetime,
            },
        )
        field = form.fields["input_timeseries"]
        field.widget = field.hidden_widget()
        
    elif technology == "Other":
        form = AssetCreateForm(
            asset_type=asset_type_name,
            initial={
                "name": "What ever you like",
                "source_choice": technology,
                "year_choice_source": year,
                "capex": "",
                "opex": "",
                "lifetime": "",
                "input_timeseries" : "" #would be the file
            },
        )
        input_timeseries = "" #for visualisation
        
    elif technology == "Solar thermal system": #from "So gehts", the same for all years
        # cwd = os.getcwd()
        queryset = InputparameterSuggestion.objects.filter(technology=technology)
        for item in queryset:
            input_timeseries = item.input_timeseries
            capex = item.capex
            opex = item.opex
            lifetime = item.lifetime
        
        form = AssetCreateForm(
            asset_type=asset_type_name,
            initial={
                "name": technology,
                "source_choice": technology,
                "year_choice_source": year,
                "capex": capex, #€/m2
                "opex": opex,
                "lifetime": lifetime
            },
        )
            
        # array_data = np.load('static/Solar thermal energy profile.npy')
        # input_timeseries = str(array_data)
        
    elif technology == "Run-of-river power plant": #from "So gehts", the same for all years
        queryset = InputparameterSuggestion.objects.filter(technology=technology)
        for item in queryset:
            input_timeseries = item.input_timeseries
            capex = item.capex
            opex = item.opex
            lifetime = item.lifetime
            
        form = AssetCreateForm(
            asset_type=asset_type_name,
            initial={
                "name": technology,
                "source_choice": technology,
                "year_choice_source": year,
                "capex": capex,
                "opex": opex,
                "lifetime": lifetime
            },
        )
        # array_data = np.load('static/Run-of-river power plant profile.npy')
        # input_timeseries = str(array_data)        
        
    elif technology == "Import Grid":
        form = AssetCreateForm(
            asset_type=asset_type_name,
            initial={
                "name": "Electricity supply grid",
                "source_choice": technology,
                "capex": 153030,
                "maximum": 300,
                "variable_costs": 70
            },
        )
        input_timeseries = ""
        
        field = form.fields["capex"]
        field.label = "Performance price"
        field = form.fields["opex"]
        field.widget = field.hidden_widget()
        field = form.fields["lifetime"]
        field.widget = field.hidden_widget()
        field = form.fields["existing"]
        field.widget = field.hidden_widget()
        
    elif technology == "Biomass supply":
        form = AssetCreateForm(
            asset_type=asset_type_name,
            initial={
                "name": "Biomass supply",
                "source_choice": technology,
                "year_choice_source": year,
                "summed_max": 83479,
                "variable_costs": 25
            },
        )
        input_timeseries = ""
        
        field = form.fields["capex"]
        field.widget = field.hidden_widget()
        field = form.fields["opex"]
        field.widget = field.hidden_widget()
        field = form.fields["lifetime"]
        field.widget = field.hidden_widget()
        field = form.fields["existing"]
        field.widget = field.hidden_widget()
        field = form.fields["maximum"]
        field.widget = field.hidden_widget()
        field = form.fields["minimum"]
        field.widget = field.hidden_widget()
        field = form.fields["offset"]
        field.widget = field.hidden_widget()
        field = form.fields["_max"]
        field.widget = field.hidden_widget()
        field = form.fields["_min"]
        field.widget = field.hidden_widget()
        
    if technology == "Wind" or technology == "Photovoltaic Free Field":
        field = form.fields["summed_max"]
        field.widget = field.hidden_widget()
        
        field = form.fields["summed_min"]
        field.widget = field.hidden_widget()
        
    field = form.fields["nominal_value"]
    field.widget = field.hidden_widget()
        
    # form_suggestion = SuggestionForm(initial={"capex": 600000, "opex": 2,
    #                                           "lifetime": 20})

    # form_html = get_template("asset/asset_create_form_param_suggestion.html")
    # return JsonResponse(
    #     {"success": True, "form_html": form_html.render({"form_suggestion": form_suggestion})},
    #     status=200
    # )
    # scenario = Scenario.objects.get(id=1)

    form_html = get_template("asset/asset_create_form.html")
    return JsonResponse(
        {
            "success": True,
            "form_html": form_html.render(
                {
                    "form": form,
                    "input_timeseries_data": input_timeseries,
                    "input_timeseries_timestamps": 8760,
                }
            ),
        },
        status=200,
    )


@login_required
@require_http_methods(["POST", "GET"])  # , "POST"
def get_inputparameter_suggestion_trafo(request):
    body_unicode = request.body.decode("utf-8")  # for POST
    body = json.loads(body_unicode)
    print(body)
    capex, opex, lifetime, crate, efficiency, efficiency_el, efficiency_th = (None,) * 7
    input_timeseries = ""
    technology = body[0]["kindOfComponentTrafo"]
    year = body[1]["choosenTimestampTrafo"]
    asset_type_name = "myPredefinedTransformer"
    
    if year == "2025" or year == "2035" and technology != "Other":
        (capex, opex, lifetime, efficiency, efficiency_el, 
         efficiency_th, input_timeseries) = polate_unknown_capex(technology, year, asset_type_name)
    
    else: 
        #2030, 2040, 2045
        queryset = InputparameterSuggestion.objects.filter(technology=technology, year=year)
        for item in queryset:
            print(item.unique_id, item.capex)
            capex = item.capex
            opex = item.opex
            lifetime = item.lifetime
            efficiency = item.efficiency
            efficiency_el = item.efficiency_el
            efficiency_th = item.efficiency_th
            input_timeseries = item.input_timeseries

    if (
        technology == "Biogas CHP"
        or technology == "Biogas injection (New facility)"
        or technology == "GuD"
        or technology == "PtL"
        or technology == "Methanisation"
        or technology == "Electrolysis"
        or technology == "Fuel cell"
        or technology == "Air source heat pump (large-scale)"
        or technology == "Electrode heating boiler"
        or technology == "Other"
    ):
        
        form = AssetCreateForm(
            asset_type=asset_type_name,
            initial={
                "name": "What ever you like",
                "trafo_choice": technology,
                "year_choice_trafo": year,
                "capex": capex,
                "opex": opex,
                "lifetime": lifetime,
                "efficiency": efficiency,
                "efficiency_el": efficiency_el,
                "efficiency_th": efficiency_th,
            },
        )
        if technology == "Biogas CHP" or technology == "GuD":
            field = form.fields["efficiency"]
            field.widget = field.hidden_widget()
        elif (
            technology == "Biogas injection (New facility)"
            or technology == "PtL"
            or technology == "Methanisation"
            or technology == "Electrolysis"
            or technology == "Fuel cell"
            or technology == "Air source heat pump (large-scale)"
            or technology == "Electrode heating boiler"
        ):

            field1 = form.fields["efficiency_el"]
            field2 = form.fields["efficiency_th"]
            field1.widget = field1.hidden_widget()
            field2.widget = field2.hidden_widget()
            # self.fields[""] = forms.CharField(widget=forms.HiddenInput())

    # form_suggestion = SuggestionForm(initial={"capex": 600000, "opex": 2,
    #                                           "lifetime": 20})

    form_html = get_template("asset/asset_create_form.html")
    return JsonResponse(
        {
            "success": True,
            "form_html": form_html.render(
                {
                    "form": form,
                    "input_timeseries_data": input_timeseries,
                    "input_timeseries_timestamps": 8760,
                }
            ),
        },
        status=200,
    )

@login_required
@require_http_methods(["POST", "GET"])  # , "POST"
def get_inputparameter_suggestion_storage(request):
    body_unicode = request.body.decode("utf-8")  # for POST
    body = json.loads(body_unicode)
    print(body)
    capex, opex, lifetime, crate, efficiency, efficiency_el, efficiency_th, thermal_loss_rate, fixed_losses_relative_gamma, fixed_losses_absolute_delta = (None,) * 10
    # input_timeseries = ""
    technology = body[0]["kindOfComponentStorage"]
    year = body[1]["choosenTimestampStorage"]
    asset_type_name = "myPredefinedStorage"
    
    if year == "2025" or year == "2035" and technology != "Other":
        (capex, opex, lifetime, crate, efficiency, thermal_loss_rate, 
         fixed_losses_relative_gamma, fixed_losses_absolute_delta) = polate_unknown_capex(technology, year, asset_type_name)
    
    else: 
        #2030, 2040, 2045
        queryset = InputparameterSuggestion.objects.filter(technology=technology, year=year)
        for item in queryset:
            print(item.unique_id, item.capex, item.fixed_losses_relative_gamma)
            capex = item.capex
            opex = item.opex
            lifetime = item.lifetime
            crate = item.crate
            efficiency = item.efficiency
            thermal_loss_rate = item.thermal_loss_rate
            fixed_losses_relative_gamma = item.fixed_losses_relative_gamma
            fixed_losses_absolute_delta = item.fixed_losses_absolute_delta
            # efficiency_el = item.efficiency_el
            # efficiency_th = item.efficiency_th
            # input_timeseries = item.input_timeseries

    
    form = StorageForm_II(
        asset_type=asset_type_name,
        initial={
            "name": "What ever you like",
            "storage_choice": technology,
            "year_choice_storage": year,
            "capex": capex,
            "opex": opex,
            "lifetime": lifetime,
            "invest_relation_input_capacity": crate,
            "invest_relation_output_capacity": crate,
            "inflow_conversion_factor": 1.0,
            "outflow_conversion_factor": efficiency,
            "thermal_loss_rate": thermal_loss_rate,
            "fixed_thermal_losses_relative": fixed_losses_relative_gamma,
            "fixed_thermal_losses_absolute": fixed_losses_absolute_delta
        },
    )

    # form_suggestion = SuggestionForm(initial={"capex": 600000, "opex": 2,
    #                                           "lifetime": 20})

    # form_html = get_template("asset/asset_create_form_param_suggestion.html")
    # return JsonResponse(
    #     {"success": True, "form_html": form_html.render({"form_suggestion": form_suggestion})},
    #     status=200
    # )
    # scenario = Scenario.objects.get(id=1)

    form_html = get_template("asset/storage_asset_create_form.html")
    return JsonResponse(
        {
            "success": True,
            "form_html": form_html.render(
                {
                    "form": form
                }
            ),
        },
        status=200,
    )

# @login_required
# @require_http_methods(["POST", "GET"])
# def check_choosen_time_period(request):
#     body_unicode = request.body.decode("utf-8")  # for POST
#     body = json.loads(body_unicode)
#     print(body)
#     name, timeframe_choice, evaluated_period = (None,) * 3
#     name = body[0]["scenarioName"]
#     timeframe_choice = body[1]["timeframeChoice"]
#     evaluated_period = body[2]["evaluatedPeriod"]
    
#     queryset = Project.objects.filter(name="Benchmark test for sector coupled system and electricity price time series")
#     for item in queryset:
#         print(item.id)
#         proj_id = item.id
    
#     project = get_object_or_404(Project, pk=proj_id)
#     # all projects which the user is able to select (the one the user created)
#     user_projects = request.user.project_set.all()

#     form = ScenarioCreateForm(
#         initial={"project": project,
#                  "name": name,
#                  "evaluated_period": evaluated_period,
#                  "timeframe_choice": timeframe_choice}, 
#         project_queryset=user_projects
#     )
    
#     form_html = get_template("scenario/scenario_step1.html")
    
#     step_id=1
#     return JsonResponse(
#         {
#             "success": True,
#             "form_html": form_html.render(
#                 {
#                     "form": form,
#                     "proj_id": proj_id,
#                     "proj_name": project.name,
#                     "scenario": None,
#                     "scen_id": None,
#                     "step_id": step_id,
#                     "step_list": STEP_LIST,
#                     "max_step": 5,
#                 }
#             ),
#         },
#         status=200,
#     )

@login_required
@require_http_methods(["GET"])
def get_asset_create_form(request, scen_id=0, asset_type_name="", asset_uuid=None):
    scenario = Scenario.objects.get(id=scen_id)
    print('inside get_asset_create_form')

    # collect the information about the connected nodes in the GUI
    input_output_mapping = {
        "inputs": json.loads(request.POST.get("inputs", "[]")),
        "outputs": json.loads(request.POST.get("outputs", "[]")),
    }

    if asset_type_name == "bus":
        if asset_uuid:
            existing_bus = get_object_or_404(Bus, pk=asset_uuid)
            form = BusForm(asset_type=asset_type_name, instance=existing_bus)
            # form.fields['name']='some bus name'
        else:
            bus_list = Bus.objects.filter(scenario=scenario)
            n_bus = len(bus_list)
            default_name = f"{asset_type_name}-{n_bus}"
            form = BusForm(asset_type=asset_type_name, initial={"name": default_name})
        return render(request, "asset/bus_create_form.html", {"form": form})

    elif asset_type_name in [
        "mySource",
        "mySink",
        "myTransformer",
        "myExcess",
        "myPredefinedSink",
        "myPredefinedSource",
        "myPredefinedTransformer",
        "myExport",
        "myPredefinedSinkOEP"
    ]:
        if asset_uuid:
            print(asset_uuid)
            existing_asset = get_object_or_404(Asset, unique_id=asset_uuid)
            form = AssetCreateForm(asset_type=asset_type_name, instance=existing_asset)
            input_timeseries_data = (
                existing_asset.input_timeseries
                if existing_asset.input_timeseries
                else ""
            )
            if asset_type_name == "myPredefinedSink" or asset_type_name == "myPredefinedSinkOEP":
                if existing_asset.choice_load_profile == "load_profile_1":
                    input_timeseries_data = [5] * 8760
                elif existing_asset.choice_load_profile == "load_profile_2":
                    input_timeseries_data = [6] * 8760
                elif existing_asset.choice_load_profile == "load_profile_3":
                    input_timeseries_data = [7] * 8760
                elif existing_asset.oep_table_name is not None:
                    try:
                        # s = requests.Session()
                        result = get(
                            OEP_URL + existing_asset.oep_table_name + "/rows"
                        )  # s.
                        jsonResponse = (
                            result.json()
                            if result and result.status_code == 200
                            else None
                        )
                        input_timeseries_data = [
                            item[existing_asset.oep_column_name]
                            for item in jsonResponse
                        ]
                    except HTTPError as http_err:
                        print(f"HTTP error occurred: {http_err}")
                    except Exception as err:
                        print(f"An other error occurred: {err}")
                else:
                    input_timeseries_data = ""

            elif asset_type_name == "myPredefinedTransformer":
                if (
                    existing_asset.trafo_choice == "Biogas CHP"
                    or existing_asset.trafo_choice == "GuD"
                ):

                    # Biogas CHP and GuD have el + th efficiency -- so hide field general efficiency
                    field = form.fields["efficiency"]
                    field.widget = field.hidden_widget()
                elif (
                    existing_asset.trafo_choice == "Biogas injection (New facility)"
                    or existing_asset.trafo_choice == "PtL"
                    or existing_asset.trafo_choice == "Methanisation"
                    or existing_asset.trafo_choice == "Electrolysis"
                    or existing_asset.trafo_choice == "Fuel cell"
                    or existing_asset.trafo_choice == "Air source heat pump (large-scale)"
                    or existing_asset.trafo_choice == "Electrode heating boiler"
                ):

                    # all other trafos have just one efficiency -- so hide el + th efficiency
                    field1 = form.fields["efficiency_el"]
                    field2 = form.fields["efficiency_th"]
                    field1.widget = field1.hidden_widget()
                    field2.widget = field2.hidden_widget()
                    

            elif asset_type_name == "myTransformer":
                bus_number = re.findall(r'\d+', existing_asset.trafo_input_bus_1)
                bus_object = Bus.objects.filter(id=int(bus_number[0]))
                for item in bus_object:
                    trafo_input_bus_1 = item.name
                    
                bus_number_output_bus_1 = re.findall(r'\d+', existing_asset.trafo_output_bus_1)
                bus_object_output_1 = Bus.objects.filter(id=int(bus_number_output_bus_1[0]))
                for item in bus_object_output_1:
                    trafo_output_bus_1 = item.name
                form = AssetCreateForm(asset_type=asset_type_name, instance=existing_asset,
                                        initial={"trafo_input_bus_1": trafo_input_bus_1,
                                                 "trafo_output_bus_1": trafo_output_bus_1}
                                       )
                if existing_asset.trafo_input_output_variation_choice == "1:2":
                    bus_number_output_bus_2 = re.findall(r'\d+', existing_asset.trafo_output_bus_2)
                    bus_object_output_2 = Bus.objects.filter(id=int(bus_number_output_bus_2[0]))
                    for item in bus_object_output_2:
                        trafo_output_bus_2 = item.name
                        
                    form = AssetCreateForm(asset_type=asset_type_name, instance=existing_asset,
                                            initial={"trafo_input_bus_1": trafo_input_bus_1,
                                                     "trafo_output_bus_1": trafo_output_bus_1,
                                                     "trafo_output_bus_2": trafo_output_bus_2
                                                     }
                                           )
                elif existing_asset.trafo_input_output_variation_choice == "2:1":
                    bus_number_input_bus_2 = re.findall(r'\d+', existing_asset.trafo_input_bus_2)
                    bus_object_input_2 = Bus.objects.filter(id=int(bus_number_input_bus_2[0]))
                    for item in bus_object_input_2:
                        trafo_input_bus_2 = item.name
                        
                    form = AssetCreateForm(asset_type=asset_type_name, instance=existing_asset,
                                            initial={"trafo_input_bus_1": trafo_input_bus_1,
                                                     "trafo_input_bus_2": trafo_input_bus_2,
                                                     "trafo_output_bus_1": trafo_output_bus_1
                                                     }
                                            )
                    
                expert_trafo_parameter_visibility(form, 
                                                  existing_asset.trafo_input_output_variation_choice)

        else:
            print(asset_type_name)
            asset_list = Asset.objects.filter(
                asset_type__asset_type=asset_type_name, scenario=scenario
            )
            n_asset = len(asset_list)
            default_name = f"{asset_type_name}-{n_asset}"
            form = AssetCreateForm(
                asset_type=asset_type_name, initial={"name": default_name}
            )
            # print(form.data.get('name'))
            input_timeseries_data = ""

        if asset_type_name == "myPredefinedSink" or asset_type_name == "myPredefinedSinkOEP":
            # print(json.dumps(scenario.get_timestamps(json_format=True)))

            context = {
                "form": form,
                "choice_load_profile_data": input_timeseries_data,
                "choice_load_profile_timestamps": json.dumps(
                    scenario.get_timestamps(json_format=True)
                ),
            }

        else:

            context = {
                "form": form,
                "input_timeseries_data": input_timeseries_data,
                "input_timeseries_timestamps": json.dumps(
                    scenario.get_timestamps(json_format=True)
                ),
            }
        # if asset_type_name == "myPredefinedSource":

        #     # print(form.asset_type_name)
        #     context = {
        #         "form": form,
        #         "input_timeseries_data": input_timeseries_data,
        #         "input_timeseries_timestamps": json.dumps(
        #             scenario.get_timestamps(json_format=True)
        #         ),
        #     }

        return render(request, "asset/asset_create_form.html", context)

    elif asset_type_name in ["myGenericStorage", "myPredefinedStorage"]:
        if asset_uuid:
            existing_ess_asset = get_object_or_404(Asset, unique_id=asset_uuid)
            ess_asset_children = Asset.objects.filter(
                parent_asset=existing_ess_asset.id
            )
            # ess_capacity_asset = ess_asset_children.get(
            #     asset_type__asset_type="capacity"
            # )
            # ess_charging_power_asset = ess_asset_children.get(
            #     asset_type__asset_type="charging_power"
            # )
            # ess_discharging_power_asset = ess_asset_children.get(
            #     asset_type__asset_type="discharging_power"
            # )
            # also get all child assets
            form = StorageForm_II(
                asset_type=asset_type_name,
                initial={
                    "name": existing_ess_asset.name,
                    "nominal_value": existing_ess_asset.nominal_value,
                    "variable_costs": existing_ess_asset.variable_costs,
                    "capex": existing_ess_asset.capex,
                    "opex": existing_ess_asset.opex,
                    "offset": existing_ess_asset.offset,
                    "maximum": existing_ess_asset.maximum,
                    "minimum": existing_ess_asset.minimum,
                    "lifetime": existing_ess_asset.lifetime,
                    "existing": existing_ess_asset.existing,
                    "invest_relation_output_capacity": existing_ess_asset.invest_relation_output_capacity,
                    "invest_relation_input_capacity": existing_ess_asset.invest_relation_input_capacity,
                    "initial_storage_level": existing_ess_asset.initial_storage_level,
                    "inflow_conversion_factor": existing_ess_asset.inflow_conversion_factor,
                    "outflow_conversion_factor": existing_ess_asset.outflow_conversion_factor,
                    "balanced": existing_ess_asset.balanced,
                    "nonconvex": existing_ess_asset.nonconvex,
                    "nominal_storage_capacity": existing_ess_asset.nominal_storage_capacity,
                    "thermal_loss_rate": existing_ess_asset.thermal_loss_rate,
                    "fixed_thermal_losses_relative": existing_ess_asset.fixed_thermal_losses_relative,
                    "fixed_thermal_losses_absolute": existing_ess_asset.fixed_thermal_losses_absolute,
                    "storage_choice": existing_ess_asset.storage_choice,
                    # "year_choice_storage": existing_ess_asset.year_choice_storage
                },
                input_output_mapping=input_output_mapping,
            )
        else:
            print(asset_type_name)
            asset_list = Asset.objects.filter(
                asset_type__asset_type=asset_type_name, scenario=scenario
            )
            n_asset = len(asset_list)
            print(n_asset)
            default_name = f"{asset_type_name}-{n_asset}"
            form = StorageForm_II(
                asset_type=asset_type_name, input_output_mapping=input_output_mapping,
                initial={"name": default_name}
            )
        return render(request, "asset/storage_asset_create_form.html", {"form": form})

    elif asset_type_name in ["bess", "h2ess", "gess", "hess"]:
        if asset_uuid:
            existing_ess_asset = get_object_or_404(Asset, unique_id=asset_uuid)
            ess_asset_children = Asset.objects.filter(
                parent_asset=existing_ess_asset.id
            )
            ess_capacity_asset = ess_asset_children.get(
                asset_type__asset_type="capacity"
            )
            ess_charging_power_asset = ess_asset_children.get(
                asset_type__asset_type="charging_power"
            )
            ess_discharging_power_asset = ess_asset_children.get(
                asset_type__asset_type="discharging_power"
            )
            # also get all child assets
            form = StorageForm(
                asset_type=asset_type_name,
                initial={
                    "name": existing_ess_asset.name,
                    "installed_capacity": ess_capacity_asset.installed_capacity,
                    "age_installed": ess_capacity_asset.age_installed,
                    "capex_fix": ess_capacity_asset.capex_fix,
                    "capex_var": ess_capacity_asset.capex_var,
                    "opex_fix": ess_capacity_asset.opex_fix,
                    "opex_var": ess_capacity_asset.opex_var,
                    "lifetime": ess_capacity_asset.lifetime,
                    "crate": ess_capacity_asset.crate,
                    "efficiency": ess_capacity_asset.efficiency,
                    "dispatchable": ess_capacity_asset.dispatchable,
                    "optimize_cap": ess_capacity_asset.optimize_cap,
                    "soc_max": ess_capacity_asset.soc_max,
                    "soc_min": ess_capacity_asset.soc_min,
                    "thermal_loss_rate": ess_capacity_asset.thermal_loss_rate,
                    "fixed_thermal_losses_relative": ess_capacity_asset.fixed_thermal_losses_relative,
                    "fixed_thermal_losses_absolute": ess_capacity_asset.fixed_thermal_losses_absolute,
                },
                input_output_mapping=input_output_mapping,
            )
        else:
            form = StorageForm(
                asset_type=asset_type_name, input_output_mapping=input_output_mapping
            )
        return render(request, "asset/storage_asset_create_form.html", {"form": form})
    else:  # all other assets

        if asset_uuid:
            existing_asset = get_object_or_404(Asset, unique_id=asset_uuid)
            form = AssetCreateForm(
                asset_type=asset_type_name,
                instance=existing_asset,
                input_output_mapping=input_output_mapping,
            )
            input_timeseries_data = (
                existing_asset.input_timeseries
                if existing_asset.input_timeseries
                else ""
            )
        else:
            asset_list = Asset.objects.filter(
                asset_type__asset_type=asset_type_name, scenario=scenario
            )
            n_asset = len(asset_list)
            default_name = f"{asset_type_name}-{n_asset}"
            form = AssetCreateForm(
                asset_type=asset_type_name,
                initial={"name": default_name},
                input_output_mapping=input_output_mapping,
            )
            input_timeseries_data = ""

        context = {
            "form": form,
            "asset_type_name": asset_type_name,
            "input_timeseries_data": input_timeseries_data,
            "input_timeseries_timestamps": json.dumps(
                scenario.get_timestamps(json_format=True)
            ),
        }

        return render(request, "asset/asset_create_form.html", context)


@login_required
@require_http_methods(["POST"])
def asset_create_or_update(request, scen_id=0, asset_type_name="", asset_uuid=None):
    if asset_type_name == "bus":
        answer = handle_bus_form_post(request, scen_id, asset_type_name, asset_uuid)
    elif asset_type_name in ["bess", "h2ess", "gess", "hess"]:
        answer = handle_storage_unit_form_post(
            request, scen_id, asset_type_name, asset_uuid
        )
    else:  # all assets
        answer = handle_asset_form_post(request, scen_id, asset_type_name, asset_uuid)
    return answer


@login_required
@require_http_methods(["GET"])
def get_asset_cops_form(request, scen_id=0, asset_type_name="", asset_uuid=None):
    opts = {}
    if asset_uuid:
        existing_asset = get_object_or_404(Asset, unique_id=asset_uuid)
        existing_cop = COPCalculator.objects.filter(asset=existing_asset)
        if existing_cop.exists():
            opts["instance"] = existing_cop.get()
    context = {"form": COPCalculatorForm(**opts)}

    return render(request, "asset/asset_cops_form.html", context)


@login_required
@require_http_methods(["POST"])
def asset_cops_create_or_update(
    request, scen_id=0, asset_type_name="", asset_uuid=None
):
    # collect the information about the connected nodes in the GUI

    opts = {}
    if asset_uuid:
        existing_asset = get_object_or_404(Asset, unique_id=asset_uuid)
        existing_cop = COPCalculator.objects.filter(asset=existing_asset)
        if existing_cop.exists():
            opts["instance"] = existing_cop.get()
    form = COPCalculatorForm(request.POST, request.FILES, **opts)

    scenario = get_object_or_404(Scenario, id=scen_id)
    if form.is_valid():
        cop = form.save(commit=False)
        cop.scenario = scenario
        cop.mode = asset_type_name
        if asset_uuid:
            cop.asset = existing_asset
        cop.save()

        try:
            cops = cop.calc_cops()
            return JsonResponse(
                {"success": True, "cop_id": cop.id, "cops": json.dumps(cops)},
                status=200,
            )
        except:
            return JsonResponse({"success": False, "cop_id": cop.id}, status=422)

    logger.warning(f"The submitted asset has erroneous field values.")

    form_html = get_template("asset/asset_cops_form.html")
    return JsonResponse(
        {"success": False, "form_html": form_html.render({"form": form})}, status=422
    )


# endregion Asset


# region MVS JSON Related


@json_view
@login_required
@require_http_methods(["GET"])
def view_mvs_data_input(request, scen_id=0, testing=False):
    if scen_id == 0:
        return JsonResponse(
            {"status": "error", "error": "No scenario id provided"},
            status=500,
            content_type="application/json",
        )
    # Load scenario
    scenario = Scenario.objects.get(id=scen_id)

    if scenario.project.user != request.user:

        logger.warning(
            f"Unauthorized user tried to access scenario with db id = {scen_id}."
        )
        raise PermissionDenied

    try:
        data_clean = format_scenario_for_mvs(scenario, testing)
    except Exception as e:

        logger.error(
            f"Scenario Serialization ERROR! User: {scenario.project.user.username}. Scenario Id: {scenario.id}. Thrown Exception: {traceback.format_exc()}."
        )
        return JsonResponse(
            {"error": f"Scenario Serialization ERROR! Thrown Exception: {e}."},
            status=500,
            content_type="application/json",
        )

    return JsonResponse(data_clean, status=200, content_type="application/json")


@json_view
@login_required
@require_http_methods(["GET"])
def test_mvs_data_input(request, scen_id=0):
    return view_mvs_data_input(request, scen_id=scen_id, testing=True)


# End-point to send MVS simulation request
# @json_view
@login_required
@require_http_methods(["GET", "POST"])
def request_mvs_simulation(request, scen_id=0):

    list_sources = []
    list_busses = []
    list_sinks = []
    list_storages = []
    list_transformers = []
    list_constraints = []

    if scen_id == 0:
        answer = JsonResponse(
            {"status": "error", "error": "No scenario id provided"},
            status=500,
            content_type="application/json",
        )
    # Load scenario
    scenario = Scenario.objects.get(pk=scen_id)
    results = None

    try:
        data_clean = format_scenario_for_mvs(scenario)
        interest_rate = data_clean["simulation_settings"]["interest_rate"]["value"]
        
        if data_clean["simulation_settings"]["time_step"] == 60:
            timesteps = int(
                data_clean["simulation_settings"]["evaluated_period"]["value"] * 24
            )
            freq='hourly'
        elif data_clean["simulation_settings"]["time_step"] == 15:
            timesteps = int(
                data_clean["simulation_settings"]["evaluated_period"]["value"] * 24 * 4
            )
            freq='quarter_hourly'
            
        print(timesteps)


        for k, v in data_clean.items():
            for i in v:
                if k == "energy_busses":
                    list_busses.append(InRetEnsysBus(label=i["label"]))
                    # print(list_busses)
                    # print(i['energy_vector'])

                elif k == "energy_production":
                    # print(i)
                    
                    if i['source_choice'] == "Biomass supply":
                        summed_max = i["summed_max"]["value"] if i["summed_max"] else None,
                        # print(summed_max[0])
                        nominal_value = summed_max[0]/timesteps,
                        # print(nominal_value[0])
                        list_sources.append(
                            InRetEnsysSource(
                                label=i["label"],
                                outputs={
                                    i["outflow_direction"]: InRetEnsysFlow(
                                        variable_costs=i["variable_costs"]["value"]
                                        if i["variable_costs"]
                                        else None,
                                        nominal_value=nominal_value[0],
                                        summed_max=summed_max[0]/nominal_value[0],
                                        summed_min=i["summed_min"]["value"]
                                        if i["summed_min"]
                                        else None,
                                        nonconvex=InRetEnsysNonConvex()
                                        if i["nonconvex"]["value"] == True
                                        else None,
                                        _min=i["_min"]["value"] if i["_min"] else None,
                                        _max=i["_max"]["value"] if i["_max"] else None,
                                        custom_attributes = {
                                            "emission_factor": i["emission_factor"]["value"] if i["emission_factor"] else None,
                                            "renewable_factor": i["renewable_factor"]["value"] if i["renewable_factor"] else None
                                            },
                                    )
                                },
                            )
                        )
                        
                        print("\nEnergy Production (Biomass Import): \n")
                        print("{} : {}".format(k, i))
                        
                    elif i['source_choice'] == "Import Grid":
                        list_sources.append(
                            InRetEnsysSource(
                                label=i["label"],
                                outputs={
                                    i["outflow_direction"]: InRetEnsysFlow(
                                        fix=i["input_timeseries"]["value"]
                                        if i["input_timeseries"]["value"]
                                        else None,
                                        variable_costs=i["variable_costs"]["value"]
                                        if i["variable_costs"]
                                        else None,
                                        nominal_value=i["nominal_value"]["value"]
                                        if i["nominal_value"]
                                        else None,
                                        summed_max=i["summed_max"]["value"]
                                        if i["summed_max"]
                                        else None,
                                        summed_min=i["summed_min"]["value"]
                                        if i["summed_min"]
                                        else None,
                                        nonconvex=InRetEnsysNonConvex()
                                        if i["nonconvex"]["value"] == True
                                        else None,
                                        _min=i["_min"]["value"] if i["_min"] else None,
                                        _max=i["_max"]["value"] if i["_max"] else None,
                                        custom_attributes = {
                                            "emission_factor": i["emission_factor"]["value"] if i["emission_factor"] else None,
                                            "renewable_factor": i["renewable_factor"]["value"] if i["renewable_factor"] else None
                                            },
                                        investment=InRetEnsysInvestment(
                                            ep_costs=i["capex"]["value"]
                                            if bool(i["capex"])
                                            else None,
                                            maximum=i["maximum"]["value"]
                                            if bool(i["maximum"])
                                            else 1000000,
                                            minimum=i["minimum"]["value"]
                                            if bool(i["minimum"])
                                            else 0,
                                            existing=i["existing"]["value"]
                                            if bool(i["existing"])
                                            else 0,
                                            offset=i["offset"]["value"]
                                            if bool(i["offset"])
                                            else 0,
                                            nonconvex=True if i["offset"] else False,
                                        )
                                        if bool(i["capex"])
                                        else None,
                                    )
                                },
                            )
                        )
                        print("\nEnergy Production (Grid): \n")
                        print("{} : {}".format(k, i))
                        
                    else:
                        
                        if bool(i["capex"]):
                            ep_costs = epc_calc(
                                i["capex"]["value"],
                                i["lifetime"]["value"],
                                i["opex"]["value"],
                                interest_rate
                            )
                        else:
                            ep_costs = None

                        try:
                            list_sources.append(
                                InRetEnsysSource(
                                    label=i["label"],
                                    outputs={
                                        i["outflow_direction"]: InRetEnsysFlow(
                                            fix=i["input_timeseries"]["value"]
                                            if i["input_timeseries"]["value"]
                                            else None,
                                            variable_costs=i["variable_costs"]["value"]
                                            if i["variable_costs"]
                                            else None,
                                            nominal_value=i["nominal_value"]["value"]
                                            if i["nominal_value"]
                                            else None,
                                            summed_max=i["summed_max"]["value"]
                                            if i["summed_max"]
                                            else None,
                                            summed_min=i["summed_min"]["value"]
                                            if i["summed_min"]
                                            else None,
                                            nonconvex=InRetEnsysNonConvex()
                                            if i["nonconvex"]["value"] == True
                                            else None,
                                            _min=i["_min"]["value"] if i["_min"] else None,
                                            _max=i["_max"]["value"] if i["_max"] else None,
                                            custom_attributes = {
                                                "emission_factor": i["emission_factor"]["value"] if i["emission_factor"] else None,
                                                "renewable_factor": i["renewable_factor"]["value"] if i["renewable_factor"] else None
                                                },
                                            investment=InRetEnsysInvestment(
                                                ep_costs=ep_costs,
                                                maximum=i["maximum"]["value"]
                                                if bool(i["maximum"])
                                                else 1000000,
                                                minimum=i["minimum"]["value"]
                                                if bool(i["minimum"])
                                                else 0,
                                                existing=i["existing"]["value"]
                                                if bool(i["existing"])
                                                else 0,
                                                offset=i["offset"]["value"]
                                                if bool(i["offset"])
                                                else 0,
                                                nonconvex=True if i["offset"] else False,
                                            )
                                            if bool(ep_costs)
                                            else None,
                                        )
                                    },
                                )
                            )
    
                        except Exception as e:
                            error_msg = f"Source Scenario Serialization ERROR! User: {scenario.project.user.username}. Scenario Id: {scenario.id}. Thrown Exception: {e}."
                            logger.error(error_msg)
    
                            messages.error(request, error_msg)
                            raise Exception(error_msg + " - 407")
                        
                        print("\nEnergy Production (all other): \n")
                        print("{} : {}".format(k, i))

                elif k == "energy_consumption":
                    try:
                        if i["asset_type"] == "myExport":
                            # print(k)
                            # print(i)
                            list_sinks.append(
                                InRetEnsysSink(
                                    label=i["label"],
                                    inputs={
                                        i["inflow_direction"]: InRetEnsysFlow(
                                            nominal_value=i["nominal_value"]["value"] if i["nominal_value"] else None,
                                            variable_costs=i["variable_costs"]["value"]*(-1) if i["variable_costs"] else None
                                        )
                                    },
                                )
                            )
                            # print("\nEnergy Consumption: \n")
                            # print("{} : {}".format(k, i))
                            
                        elif i["asset_type"] == "myPredefinedSink":
                            power = (i["annual_energy_consumption"]["value"]/
                                     sum(i["input_timeseries"]["value"]))
                            list_sinks.append(
                                InRetEnsysSink(
                                    label=i["label"],
                                    inputs={
                                        i["inflow_direction"]: InRetEnsysFlow(
                                            fix=i["input_timeseries"]["value"] if i["input_timeseries"] else None,
                                            nominal_value=power,
                                            variable_costs=i["variable_costs"]["value"] if i["variable_costs"] else None,
                                            custom_attributes = {
                                                "renewable_factor": i["renewable_factor"]["value"] if i["renewable_factor"] else None
                                            }
                                        )
                                    },
                                )
                            )
                            
                            # print("\nEnergy Consumption: \n")
                            # print("{} : {}".format(k, i))
                            
                        else:
                            # print(k)
                            # print(i)
                            list_sinks.append(
                                InRetEnsysSink(
                                    label=i["label"],
                                    inputs={
                                        i["inflow_direction"]: InRetEnsysFlow(
                                            fix=i["input_timeseries"]["value"] if i["input_timeseries"] else None,
                                            nominal_value=i["nominal_value"]["value"] if i["nominal_value"] else None,
                                            variable_costs=i["variable_costs"]["value"] if i["variable_costs"] else None,
                                            custom_attributes = {
                                                "renewable_factor": i["renewable_factor"]["value"] if i["renewable_factor"] else None
                                            }
                                        )
                                    },
                                )
                            )
                            
                            # print("\nEnergy Consumption: \n")
                            # print("{} : {}".format(k, i))

                    except Exception as e:
                        error_msg = f"Sink Scenario Serialization ERROR! User: {scenario.project.user.username}. Scenario Id: {scenario.id}. Thrown Exception: {e}."
                        logger.error(error_msg)

                        messages.error(request, error_msg)
                        raise Exception(error_msg + " - 407")

                elif k == "energy_storage":
                    if bool(i["capex"]):
                        ep_costs = epc_calc(
                            i["capex"]["value"],
                            i["lifetime"]["value"],
                            i["opex"]["value"],
                            interest_rate
                        )
                    else:
                        ep_costs = None

                    try:
                        list_storages.append(
                            InRetEnsysStorage(
                                label=i["label"],
                                inputs={
                                    i["inflow_direction"]: InRetEnsysFlow(
                                        nonconvex=InRetEnsysNonConvex() if i["nonconvex"]["value"] == True else None,
                                        nominal_value=i["nominal_value"]["value"] if bool(i["nominal_value"]) else None,
                                        variable_costs=i["variable_costs"]["value"] if bool(i["variable_costs"]) else None,
                                    )
                                },
                                outputs={
                                    i["outflow_direction"]: InRetEnsysFlow(
                                        nonconvex=InRetEnsysNonConvex() if i["nonconvex"]["value"] == True else None,
                                        nominal_value=i["nominal_value"]["value"] if bool(i["nominal_value"]) else None,
                                        variable_costs=i["variable_costs"]["value"] if bool(i["variable_costs"]) else None,
                                    )
                                },
                                loss_rate=i["thermal_loss_rate"]["value"] if i["thermal_loss_rate"] else 0,
                                fixed_losses_relative=i["fixed_thermal_losses_relative"]["value"] if i["fixed_thermal_losses_relative"] else 0,
                                fixed_losses_absolute=i["fixed_thermal_losses_absolute"]["value"] if i["fixed_thermal_losses_absolute"] else 0,
                                initial_storage_level=i["initial_storage_level"]["value"] if bool(i["initial_storage_level"]) else None,
                                balanced=i["balanced"]["value"],
                                invest_relation_input_capacity=i["invest_relation_input_capacity"]["value"] if bool(i["invest_relation_input_capacity"]) else None,
                                invest_relation_output_capacity=i["invest_relation_output_capacity"]["value"] if bool(i["invest_relation_output_capacity"]) else None,
                                inflow_conversion_factor=i["inflow_conversion_factor"]["value"],
                                outflow_conversion_factor=i["outflow_conversion_factor"]["value"],
                                nominal_storage_capacity=i["nominal_storage_capacity"]["value"] if bool(i["nominal_storage_capacity"]) else None,
                                investment=InRetEnsysInvestment(
                                    ep_costs=ep_costs,
                                    maximum=i["maximum"]["value"] if bool(i["maximum"]) else 1000000,
                                    minimum=i["minimum"]["value"] if bool(i["minimum"]) else 0,
                                    existing=i["existing"]["value"] if bool(i["existing"]) else 0,
                                    offset=i["offset"]["value"] if bool(i["offset"]) else 0,
                                    nonconvex=True if bool(i["offset"]) else False,
                                ) if bool(ep_costs) else None,
                            )
                        )
                        
                        # print("\nEnergy Storage: \n")
                        # print("{} : {}".format(k, i))

                    except Exception as e:
                        error_msg = f"Storage Scenario Serialization ERROR! User: {scenario.project.user.username}. Scenario Id: {scenario.id}. Thrown Exception: {e}."
                        logger.error(error_msg)

                        messages.error(request, error_msg)
                        raise Exception(error_msg + " - 407")
                    
                elif k == "energy_conversion":

                    if bool(i["capex"]):
                        ep_costs = epc_calc(
                            i["capex"]["value"],
                            i["lifetime"]["value"],
                            i["opex"]["value"],
                            interest_rate
                        )
                    else:
                        ep_costs = None
                        
                    if i['trafo_choice'] == "Biogas CHP":
                        print("\nEnergy Conversion (Biogas CHP): \n")
                        print("{} : {}".format(k, i))                        
                        
                        try:
                            output_first = ""
                            output_second = ""
                            
                            if not isinstance(i['outflow_direction'], list):
                                raise Exception("Your Biogas CHP is missing an output connection!")
                            elif len(i['outflow_direction']) > 2:
                                raise Exception("Your Biogas CHP has too many output connections!")
                                
                            queryset = Bus.objects.filter(name=i['outflow_direction'][0])
                            for item_0 in queryset:
                                print(item_0.type)
                                
                            if item_0.type == "Electricity" or item_0.type == "Heat":
                                if item_0.type == "Electricity":
                                    output_first = i['outflow_direction'][0]
                                elif item_0.type == "Heat":
                                    output_second = i['outflow_direction'][0]
                                
                            queryset = Bus.objects.filter(name=i['outflow_direction'][1])
                            for item_1 in queryset:
                                print(item_1.type)
                                
                            if item_1.type == "Electricity" or item_1.type == "Heat":
                                if item_0.type != item_1.type:
                                    if item_1.type == "Electricity":
                                        output_first = i['outflow_direction'][1]
                                    elif item_1.type == "Heat":
                                        output_second = i['outflow_direction'][1]
                            
                            if output_first == "" or output_second == "":
                                raise Exception("Your Biogas CHP is not connected to the right output buses! Please also note the selected energy carrier of the buses")
                            
                            # print(output_first, output_second)
                            
                            list_transformers.append(
                                InRetEnsysTransformer(
                                    label=i["label"],
                                    inputs={
                                        i["inflow_direction"]: InRetEnsysFlow(
                                            fix=[1]*timesteps,
                                            investment=InRetEnsysInvestment(),
                                            variable_costs=i["variable_costs"]["value"] if i["variable_costs"] else None,
                                            nonconvex=InRetEnsysNonConvex() if i["nonconvex"]["value"] == True else None,
                                            _min=i["_min"]["value"] if i["_min"] else None,
                                            _max=i["_max"]["value"] if i["_max"] else None,
                                        )
                                    },
                                    outputs={
                                        output_first: InRetEnsysFlow(
                                            fix=[1]*timesteps,
                                            variable_costs=i["variable_costs"]["value"] if i["variable_costs"] else None,
                                            nonconvex=InRetEnsysNonConvex() if i["nonconvex"]["value"] == True else None,
                                            _min=i["_min"]["value"] if i["_min"] else None,
                                            _max=i["_max"]["value"] if i["_max"] else None,
                                            #custom_attributes= {
                                            #    "renewable_factor": i["renewable_factor"]["value"] if i["renewable_factor"] else None,
                                            #},
                                            investment=InRetEnsysInvestment(#investment for electricity
                                                ep_costs=ep_costs,
                                                maximum=i["maximum"]["value"] if bool(i["maximum"]) else 1000000,
                                                minimum=i["minimum"]["value"] if bool(i["minimum"]) else 0,
                                                existing=i["existing"]["value"] if bool(i["existing"]) else 0,
                                                offset=i["offset"]["value"] if bool(i["offset"]) else 0,
                                                nonconvex=True if bool(i["offset"]) else False,
                                            )
                                            if bool(ep_costs) else InRetEnsysInvestment(),
                                        ),
                                        output_second: InRetEnsysFlow(
                                            # We first assume that it is a base load.
                                            fix=[1]*timesteps,
                                            investment=InRetEnsysInvestment(),
                                            variable_costs=i["variable_costs"]["value"] if i["variable_costs"] else None,
                                            nonconvex=InRetEnsysNonConvex() if i["nonconvex"]["value"] == True else None,
                                            _min=i["_min"]["value"] if i["_min"] else None,
                                            _max=i["_max"]["value"] if i["_max"] else None,
                                            #custom_attributes= {
                                            #    "renewable_factor": i["renewable_factor"]["value"] if i["renewable_factor"] else None
                                            #},
                                        )
                                    },
                                    conversion_factors={
                                        output_first: i["efficiency_el"]["value"],
                                        output_second: i["efficiency_th"]["value"]
                                    },
                                )
                            )
                        except Exception as e:
                            error_msg = f"Trafo Scenario Serialization ERROR! User: {scenario.project.user.username}. Scenario Id: {scenario.id}. Thrown Exception: {e}."
                            logger.error(error_msg)
    
                            raise Exception(error_msg + " - 407")
                            
                    elif i["asset_type"] == "myTransformer":
                        list_transformers = build_oemof_trafo_expert(list_transformers, k, 
                                                                     i, ep_costs)
                        
                        print(list_transformers)
                        
                    
                    else: # predefined trafos with one input and one output
                        try:
                            list_transformers.append(
                                InRetEnsysTransformer(
                                    label=i["label"],
                                    inputs={
                                        i["inflow_direction"]: InRetEnsysFlow(
                                            # We first assume that it is a base load.
                                            # fix=i["input_timeseries"]["value"]
                                            # if i["input_timeseries"]["value"]
                                            # else None,
                                            variable_costs=i["variable_costs"]["value"]
                                            if i["variable_costs"]
                                            else None,
                                            nominal_value=i["nominal_value"]["value"]
                                            if i["nominal_value"]
                                            else None,
                                            summed_max=i["summed_max"]["value"]
                                            if i["summed_max"]
                                            else None,
                                            summed_min=i["summed_min"]["value"]
                                            if i["summed_min"]
                                            else None,
                                            nonconvex=InRetEnsysNonConvex()
                                            if i["nonconvex"]["value"] == True
                                            else None,
                                            _min=i["_min"]["value"]
                                            if i["_min"]
                                            else None,
                                            _max=i["_max"]["value"]
                                            if i["_max"]
                                            else None,
                                            investment=InRetEnsysInvestment(
                                                ep_costs=ep_costs,
                                                maximum=i["maximum"]["value"]
                                                if bool(i["maximum"])
                                                else 1000000,
                                                minimum=i["minimum"]["value"]
                                                if bool(i["minimum"])
                                                else 0,
                                                existing=i["existing"]["value"]
                                                if bool(i["existing"])
                                                else 0,
                                                offset=i["offset"]["value"]
                                                if bool(i["offset"])
                                                else 0,
                                                nonconvex=True
                                                if bool(i["offset"])
                                                else False,
                                            )
                                            if bool(ep_costs)
                                            else None,
                                        )
                                    },
                                    outputs={
                                        i["outflow_direction"]: InRetEnsysFlow(
                                            # We first assume that it is a base load.
                                            # fix=i["input_timeseries"]["value"]
                                            # if i["input_timeseries"]["value"]
                                            # else None,
                                            variable_costs=i["variable_costs"]["value"]
                                            if i["variable_costs"]
                                            else None,
                                            nominal_value=i["nominal_value"]["value"]
                                            if i["nominal_value"]
                                            else None,
                                            summed_max=i["summed_max"]["value"]
                                            if i["summed_max"]
                                            else None,
                                            summed_min=i["summed_min"]["value"]
                                            if i["summed_min"]
                                            else None,
                                            nonconvex=InRetEnsysNonConvex()
                                            if i["nonconvex"]["value"] == True
                                            else None,
                                            _min=i["_min"]["value"]
                                            if i["_min"]
                                            else None,
                                            _max=i["_max"]["value"]
                                            if i["_max"]
                                            else None,
                                            custom_attributes= {
                                                "renewable_factor": i["renewable_factor"]["value"] if i["renewable_factor"] else None
                                            },
                                            investment=InRetEnsysInvestment(
                                                ep_costs=ep_costs,
                                                maximum=i["maximum"]["value"]
                                                if bool(i["maximum"])
                                                else 1000000,
                                                minimum=i["minimum"]["value"]
                                                if bool(i["minimum"])
                                                else 0,
                                                existing=i["existing"]["value"]
                                                if bool(i["existing"])
                                                else 0,
                                                offset=i["offset"]["value"]
                                                if bool(i["offset"])
                                                else 0,
                                                nonconvex=True
                                                if bool(i["offset"])
                                                else False,
                                            )
                                            if bool(ep_costs)
                                            else None,
                                        )
                                    },
                                    conversion_factors={
                                        i["outflow_direction"]: i["efficiency"]["value"]
                                    },
                                )
                            )
                            
                            print("\nEnergy Conversion: \n")
                            print("{} : {}".format(k, i))                        
                            
                        except Exception as e:
                            error_msg = f"Trafo Scenario Serialization ERROR! User: {scenario.project.user.username}. Scenario Id: {scenario.id}. Thrown Exception: {e}."
                            logger.error(error_msg)
    
                            raise Exception(error_msg + " - 407")

        print(data_clean["constraints"])
        print(data_clean["economic_data"])
        print(data_clean["simulation_settings"])
        print(data_clean["simulation_settings"]["evaluated_period"])
        print(data_clean["simulation_settings"]["evaluated_period"]["value"])
        
        
        energysystem = InRetEnsysEnergysystem(
            busses=list_busses,
            sinks=list_sinks,
            sources=list_sources,
            storages=list_storages,
            transformers=list_transformers,
            frequenz=freq,
            start_date=data_clean["simulation_settings"]["start_date"],
            time_steps=timesteps
        )

        #print(data_clean["constraints"])

        list_constraints.append(
            InRetEnsysConstraints(
                typ=Constraints.emission_limit,
                #keyword="emission_factor",
                limit=data_clean["constraints"]["maximum_emissions"]["value"],
            )
        ) if "maximum_emissions" in data_clean["constraints"] else None
        
        list_constraints.append(
            InRetEnsysConstraints(
                typ=Constraints.generic_integral_limit,
                keyword="renewable_factor",
                limit=data_clean["constraints"]["minimal_renewable_factor"][
                    "value"
                ],
            )
        ) if "minimal_renewable_factor" in data_clean["constraints"] else None
        

        if len(list_constraints) > 0:
            for item in list_constraints:
                energysystem.constraints.append(item)

        model = InRetEnsysModel(
            energysystem=energysystem,
            solver=Solver.cbc,
            solver_verbose=True,
            constraints=list_constraints,
        )

        # File output for debugging
        #file = os.path.join(os.getcwd(), "dumps", "mydump.json")
        #jf = open(file, 'wt')
        #jf.write(model.json())
        #jf.close()

        if request.method == "POST":
            output_lp_file = request.POST.get("output_lp_file", None)
        if output_lp_file == "on":
            data_clean["simulation_settings"]["output_lp_file"] = "true"

        results = mvs_simulation_request(model.model_dump_json(exclude_none=True, exclude_unset=True))
    except Exception as e:
        error_msg = f"Scenario Serialization ERROR! User: {scenario.project.user.username}. Scenario Id: {scenario.id}. Thrown Exception: {e}."
        logger.error(error_msg)
        messages.error(request, error_msg)
        
        raise Exception(error_msg + " - 407")
    
    try:
        # delete existing simulation
        Simulation.objects.filter(scenario_id=scen_id).delete()
        # Create empty Simulation model object
        simulation = Simulation(start_date=datetime.now(), scenario_id=scen_id)
        simulation.mvs_token = results["token"]

        if "status" in results.keys() and (
            results["status"] == DONE or results["status"] == ERROR
        ):
            simulation.status = results["status"]
            # simulation.results = results["results"]
            simulation.end_date = datetime.now()
        else:  # PENDING
            simulation.status = results["status"]
            # create a task which will update simulation status
            create_or_delete_simulation_scheduler(mvs_token=simulation.mvs_token)

        simulation.elapsed_seconds = (datetime.now() - simulation.start_date).seconds
        simulation.save()

        answer = HttpResponseRedirect(
            reverse("scenario_review", args=[scenario.project.id, scen_id])
        )
    except Exception as e:
        error_msg = "Could not communicate with the simulation server."
        logger.error(error_msg)
        messages.error(request, error_msg)
        # TODO redirect to prefilled feedback form / bug form

        raise Exception(error_msg + " - 407")

    return answer


@json_view
@login_required
@require_http_methods(["POST"])
def update_simulation_rating(request):
    try:
        simulation = Simulation.objects.filter(
            scenario_id=request.POST["scen_id"]
        ).first()
        simulation.user_rating = request.POST["user_rating"]
        simulation.save()
        return JsonResponse(
            {"success": True}, status=200, content_type="application/json"
        )
    except Exception as e:
        return JsonResponse(
            {"success": False, "cause": str(e)},
            status=200,
            content_type="application/json",
        )


@json_view
@login_required
@require_http_methods(["GET"])
def fetch_simulation_results(request, sim_id):
    simulation = get_object_or_404(Simulation, id=sim_id)
    status = fetch_mvs_simulation_results(simulation)

    return JsonResponse(
        dict(status=status),
        status=200,
        content_type="application/json",
    )


@login_required
@require_http_methods(["GET"])
def simulation_cancel(request, scen_id):
    scenario = get_object_or_404(Scenario, id=scen_id)

    if scenario.project.user != request.user:
        raise PermissionDenied

    qs = Simulation.objects.filter(scenario=scen_id)
    if qs.exists():
        scenario.simulation.delete()

    sim_folder = scenario.simulation.mvs_token
    full_path = os.path.join(os.getcwd(), "dumps", sim_folder)
    print(full_path)
    # os.removedirs(full_path)
    shutil.rmtree(full_path, ignore_errors=True)

    return HttpResponseRedirect(
        reverse("scenario_review", args=[scenario.project.id, scen_id])
    )


# endregion MVS JSON Related
