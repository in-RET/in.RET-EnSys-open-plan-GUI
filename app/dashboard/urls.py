from django.urls import path, re_path

from .views import *

urlpatterns = [
    path(
        "scenario/results/visualize",
        scenario_visualize_results,
        name="scenario_visualize_results",
    ),
    path(
        "scenario/results/visualize/<int:scen_id>",
        scenario_visualize_results,
        name="scenario_visualize_results",
    ),
    path(
        "project/<int:proj_id>/scenario/<int:scen_id>/results/visualize",
        scenario_visualize_results,
        name="scenario_visualize_results",
    ),
    path(
        "project/<int:proj_id>/scenario/results/visualize",
        scenario_visualize_results,
        name="project_visualize_results",
    ),
    path(
        "project/<int:proj_id>/scenario/results/compare",
        project_compare_results,
        name="project_compare_results",
    ),
    path("result-change-project", result_change_project, name="result_change_project"),
    re_path(
        r"^project/(?P<proj_id>\d+)/scenario/results/update-selected-single-scenario/(?P<scen_id>\d+)?$",
        update_selected_single_scenario,
        name="update_selected_single_scenario",
    ),
]
