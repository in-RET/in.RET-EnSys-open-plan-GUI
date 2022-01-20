from django.core.exceptions import PermissionDenied
from django.http.response import Http404, HttpResponse
from dashboard.helpers import *
from dashboard.models import AssetsResults, KPICostsMatrixResults, KPIScalarResults, KPI_COSTS_TOOLTIPS, KPI_COSTS_UNITS, KPI_SCALAR_TOOLTIPS, KPI_SCALAR_UNITS
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from jsonview.decorators import json_view
from projects.models import Project, Scenario, Simulation
from projects.services import excuses_design_under_development
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from io import BytesIO
import xlsxwriter
import json
import datetime
import logging
import ast
logger = logging.getLogger(__name__)


@login_required
@json_view
@require_http_methods(["GET"])
def scenario_available_results(request, scen_id):
    scenario = get_object_or_404(Scenario, pk=scen_id)
    if (scenario.project.user != request.user) and (request.user not in scenario.project.viewers.all()):
        raise PermissionDenied

    try:
        assets_results_obj = AssetsResults.objects.get(simulation=scenario.simulation)
        assets_results_json = json.loads(assets_results_obj.assets_list)

        # bring all storage subasset one level up to show their flows.
        storage_asset_to_list(assets_results_json)

        # Generate available asset category JSON
        asset_category_json = [{'assetCategory': asset_category} for asset_category in assets_results_json.keys()]
        # Generate available asset type JSON
        assets_names_json = [
            [
                {
                    'assetCategory': asset_category,
                    'assetName': asset['label']
                }
                for asset in assets_results_json[asset_category]
                # show only assets of a certain Energy Vector
                if asset['energy_vector'] == request.GET['energy_vector']
                   and any(key in ['flow', 'timeseries_soc'] for key in asset.keys())
            ]
            for asset_category in assets_results_json.keys()
        ]
        response_json = {'options': assets_names_json, 'optgroups': asset_category_json}
        return JsonResponse(response_json, status=200, content_type='application/json')
    except Exception as e:
        logger.error(f"Dashboard ERROR: MVS Req Id: {scenario.simulation.mvs_token}. Thrown Exception: {e}")
        return JsonResponse({"error": "Could not retrieve asset names and categories."},
                            status=404, content_type='application/json')


@login_required
@json_view
@require_http_methods(["GET"])
def scenario_request_results(request, scen_id):
    scenario = get_object_or_404(Scenario, pk=scen_id)

    # if scenario.project.user != request.user:
    #     return HttpResponseForbidden()
    if (scenario.project.user != request.user) and (request.user not in scenario.project.viewers.all()):
        raise PermissionDenied

    # real data
    try:
        asset_name_list = request.GET.get('assetNameList').split(',')
        assets_results_obj = AssetsResults.objects.get(simulation=scenario.simulation)
        assets_results_json = json.loads(assets_results_obj.assets_list)

        # Generate available asset category list
        asset_category_list = [asset_category for asset_category in assets_results_json.keys()]

        # bring all storage subasset one level up to show their flows.
        storage_asset_to_list(assets_results_json)

        # Asset category to asset type
        asset_name_to_category = {
            asset_name['label']: asset_category
            for asset_category in asset_category_list
            for asset_name in assets_results_json[asset_category]
        }

        # Create the datetimes index. Constrains: step in minutes and evaluated_period in days
        base_date = scenario.start_date
        datetime_list = [
            datetime.datetime.timestamp(base_date + datetime.timedelta(minutes=step))
            for step in range(0, 24 * scenario.evaluated_period * scenario.time_step, scenario.time_step)
        ]

        # Generate results JSON per asset name
        results_json = [
            {
                'xAxis':
                    {
                        'values': datetime_list,
                        'label': 'Time'
                    },
                'yAxis':
                    {
                        'values': asset['flow']['value'] if 'flow' in asset else asset['timeseries_soc']['value'],
                        'label': asset['flow']['unit'] if 'flow' in asset else asset['timeseries_soc']['unit'],
                        # 'Power'
                    },
                'title': asset_name
            }
            for asset_name in asset_name_list
            for asset in assets_results_json[asset_name_to_category[asset_name]]
            if asset['label'] == asset_name
        ]

        return JsonResponse(results_json, status=200, content_type='application/json', safe=False)
    except Exception as e:
        logger.error(f"Dashboard ERROR: MVS Req Id: {scenario.simulation.mvs_token}. Thrown Exception: {e}")
        return JsonResponse({"Error": "Could not retrieve timeseries data."}, status=404,
                            content_type='application/json', safe=False)

@login_required
@require_http_methods(["POST", "GET"])
def scenario_visualize_results(request, proj_id=None, scen_id=None):

    excuses_design_under_development(request)

    user_projects = request.user.project_set.all()

    if request.POST:
        proj_id = int(request.POST.get("proj_id"))
        request.session["selected_scenarios"] = []

    if proj_id is None:
        proj_id = request.user.project_set.first().id

    project = get_object_or_404(Project, pk=proj_id)
    if (project.user != request.user) and (request.user not in project.viewers.all()):
        raise PermissionDenied

    user_scenarios = project.get_scenarios_with_results()

    if user_scenarios.exists() is False:
        pass
    else:
        if len(request.session.get("selected_scenarios", [])) == 0:
            scen_id = user_scenarios.first().id
            request.session["selected_scenarios"] = [str(scen_id)]



    if scen_id is None:
        context = {"project_list": user_projects, 'proj_id': proj_id, "scenario_list": user_scenarios, "kpi_list": KPI_PARAMETERS, "table_styles": TABLES}
        default_scen_id = request.session.get("selected_scenarios", [])
        if len(default_scen_id) > 0:
            context["scen_id"] = default_scen_id[0]
        answer = render(request, 'scenario/scenario_results_page.html', context)
    else:


        scenario = get_object_or_404(Scenario, pk=scen_id)
        # TODO: change this when multi-scenario selection is allowed
        request.session["selected_scenarios"] = [str(scenario.id)]
        proj_id = scenario.project.id

        if (scenario.project.user != request.user) and (request.user not in scenario.project.viewers.all()):
            raise PermissionDenied

        qs = Simulation.objects.filter(scenario=scenario)

        if qs.exists():
            kpi_scalar_results_obj = KPIScalarResults.objects.get(simulation=scenario.simulation)
            kpi_scalar_values_dict = json.loads(kpi_scalar_results_obj.scalar_values)

            scalar_kpis_json = kpi_scalars_list(kpi_scalar_values_dict, KPI_SCALAR_UNITS, KPI_SCALAR_TOOLTIPS)
            answer = render(request, 'scenario/scenario_results_page.html', {'scen_id': scen_id, 'scalar_kpis': scalar_kpis_json, 'proj_id': proj_id, "project_list": user_projects, "scenario_list": user_scenarios, "kpi_list": KPI_PARAMETERS, "table_styles": TABLES})

        else:
            # redirect to the page where the simulation is started, or results fetched again
            messages.error(request,
                           _("Your scenario was never simulated, the results are still pending or there is an error in the simulation. Please click on 'Run simulation', 'Update results' or 'Check status' button "))
            answer = HttpResponseRedirect(reverse('scenario_review', args=[proj_id, scen_id]))

    return answer

@login_required
@json_view
@require_http_methods(["GET"])
def update_selected_scenarios(request, scen_id):
    if request.is_ajax():
        selected_scenario = request.session.get("selected_scenarios", [])     #array with scenario id's ['1','5','10']
        status_code = 200
        if scen_id in selected_scenario:
            if len(selected_scenario) > 1:
                selected_scenario.pop(selected_scenario.index(scen_id))
                msg = _(f"Scenario {scen_id} was deselected")
            else:
                msg = _(f"At least one scenario need to be selected")
                status_code = 405
        else:
            # TODO: uncomment following and delete the line after when multi-scenario selection is allowed
            # selected_scenario.append(scen_id)
            selected_scenario = [scen_id]
            msg = _(f"Scenario {scen_id} was selected")
            # TODO maybe store the data in the session

        request.session["selected_scenarios"] = selected_scenario
        answer = JsonResponse({"success": msg}, status=status_code, content_type='application/json')
    else:
        answer = JsonResponse({"error": "This url is only for AJAX calls"}, status=405, content_type='application/json')
    return answer


@login_required
@json_view
@require_http_methods(["GET"])
def request_kpi_table(request, table_style=None):

    # TODO fetch selected scenarios values here
    selected_scenario = request.session.get("selected_scenarios", [])
    scen_id = int(selected_scenario[0])  # TODO: fetch multiple scenarios results
    scenario = get_object_or_404(Scenario, pk=scen_id)

    kpi_scalar_results_obj = KPIScalarResults.objects.get(simulation=scenario.simulation)
    kpi_scalar_results_dict = json.loads(kpi_scalar_results_obj.scalar_values)
    proj = get_object_or_404(Project)
    unit_conv = {'currency': proj.economic_data.currency, 'Faktor': '%'}
    table = TABLES.get(table_style, None)

    # do some unit substitution
    for l in table.values():
        for e in l:
            if e['unit'] in unit_conv:
                sub = unit_conv[e['unit']]
                e['unit'] = sub

    if table is not None:
        for subtable_title, subtable_content in table.items():
            for param in subtable_content:
                # TODO: provide multiple scenarios results
                param["scen_values"] = [round_only_numbers(kpi_scalar_results_dict.get(param["id"], "not implemented yet"), 2)]
        answer = JsonResponse(table, status=200, content_type='application/json')

    else:
        allowed_styles = ", ".join(TABLES.keys())
        answer = JsonResponse({"error":f"The kpi table sytle {table_style} is not implemented. Please try one of {allowed_styles}"}, status=404, content_type='application/json')

    return answer

@login_required
@json_view
@require_http_methods(["GET"])
def scenario_economic_results(request, scen_id=None):
    """
    This view gathers all simulation specific cost matrix KPI results
    and sends them to the client for representation.
    """
    if scen_id is None:
        return JsonResponse({"error":"No scenario name provided"}, status=404, content_type='application/json', safe=False)

    scenario = get_object_or_404(Scenario, pk=scen_id)

    # if scenario.project.user != request.user:
    #     return HttpResponseForbidden()
    if (scenario.project.user != request.user) and (request.user not in scenario.project.viewers.all()):
        raise PermissionDenied

    try:
        kpi_cost_results_obj = KPICostsMatrixResults.objects.get(simulation=scenario.simulation)
        kpi_cost_values_dict = json.loads(kpi_cost_results_obj.cost_values)

        new_dict = dict()
        for asset_name in kpi_cost_values_dict.keys():
            for category, v in kpi_cost_values_dict[asset_name].items():
                new_dict.setdefault(category, {})[asset_name] = v

        # non-dummy data
        results_json = [
            {
                'values': [(round(value, 3) if '€/kWh' in KPI_COSTS_UNITS[category] else round(value, 2))
                           for value in new_dict[category].values()],
                'labels': [asset.replace('_', ' ').upper() for asset in new_dict[category].keys()],
                'type': 'pie',
                'title': category.replace('_', ' ').upper(),
                'titleTooltip': KPI_COSTS_TOOLTIPS[category],
                'units': [KPI_COSTS_UNITS[category] for _ in new_dict[category].keys()]
            }
            for category in new_dict.keys()
            if category in KPI_COSTS_UNITS.keys() and sum(
                new_dict[category].values()) > 0.0  # there is at least one non zero value
               and len(list(filter(lambda asset_name: new_dict[category][asset_name] > 0.0, new_dict[category]))) > 1.0
            # there are more than one assets with value > 0
        ]

        return JsonResponse(results_json, status=200, content_type='application/json', safe=False)
    except Exception as e:
        logger.error(f"Dashboard ERROR: MVS Req Id: {scenario.simulation.mvs_token}. Thrown Exception: {e}")
        return JsonResponse({"error": f"Could not retrieve kpi cost data."}, status=404,
                            content_type='application/json', safe=False)


# TODO: Improve automatic unit recognition and selection
# TODO: If providers are used in model, delete duplicate time-series "DSO_consumption_period"
#  (naive string matching solution in get_asset_and_ts() done)
@login_required
@json_view
@require_http_methods(["GET"])
def scenario_visualize_timeseries(request, scen_id):
    scenario = get_object_or_404(Scenario, pk=scen_id)
    if (scenario.project.user != request.user) and (request.user not in scenario.project.viewers.all()):
        raise PermissionDenied

    try:
        assets_results_obj = AssetsResults.objects.get(simulation=scenario.simulation)
        assets_results_json = json.loads(assets_results_obj.assets_list)
        ts_data = get_asset_and_ts(assets_results_json)
        datetime_list = scenario.get_timestamps(json_format=True)

        results_json = [
            {'values':
                [
                    {
                        'x': datetime_list,
                        'y': asset_obj['flow']['value'],
                        'name': asset_obj['label'].replace('_', ' ').upper()+' in '+asset_obj['flow']['unit']
                                if asset_obj['flow']['unit']!='?'
                                else asset_obj['label'].replace('_', ' ').upper()+' in kWh',
                        'type': 'scatter',
                        'line': {'shape': 'hv'},

                    }
                    for asset, asset_list in ts_data.items()
                    for asset_obj in asset_list
                ],
            'title': 'Alle Zeitreihen',
            'yaxistitle': 'Energie',
            'div': 'all_timeseries',
            }
        ]

        return JsonResponse(results_json, status=200, content_type='application/json', safe=False)
    except Exception as e:
        logger.error(f"Dashboard ERROR: MVS Req Id: {scenario.simulation.mvs_token}. Thrown Exception: {e}")
        return JsonResponse({"error": f"Could not retrieve kpi cost data."}, status=404,
                            content_type='application/json', safe=False)


def scenario_visualize_stacked_timeseries(request, scen_id):
    scenario = get_object_or_404(Scenario, pk=scen_id)
    if (scenario.project.user != request.user) and (request.user not in scenario.project.viewers.all()):
        raise PermissionDenied

    try:
        assets_results_obj = AssetsResults.objects.get(simulation=scenario.simulation)
        assets_results_json = json.loads(assets_results_obj.assets_list)

        # create new dict which has as its keys the commodities (Electricity, Heat, Gas, H2)
        # and as its values the corresponding asset dictionaries {energy_consumption: [{asset_type: ...}, .. ], ..}

        new_dict = {
            commodity: {
                asset: [
                     asset_obj
                    for asset_obj in asset_list
                    if asset_obj['energy_vector'] == commodity
                ]
                for asset, asset_list in assets_results_json.items()
            }
            for commodity in sectors
        }

        ts_data = {commodity: get_asset_and_ts(asset_dict) for commodity, asset_dict in new_dict.items()}
        datetime_list = scenario.get_timestamps(json_format=True)

        results_json = [
            {'values':
                [
                    {
                        'x': datetime_list,
                        'y': asset_obj['flow']['value'],
                        'name': asset_obj['label'].replace('_', ' ').upper()+' in '+asset_obj['flow']['unit']
                                if asset_obj['flow']['unit']!='?'
                                else asset_obj['label'].replace('_', ' ').upper()+' in kWh',
                        'type': 'scatter',
                        'line': {'shape': 'hv'},
                        'stackgroup': asset_obj['type_oemof'],
                        'fill': 'none' if asset_obj['type_oemof'] == 'sink' else 'tonexty',
                        'mode': 'none' if asset_obj['type_oemof'] != 'sink' else '',
                    }

                    for asset, asset_list in asset_list.items()
                    for asset_obj in asset_list
                    if asset_obj['flow']['value']
                ],
                'commodity': commodity,
                'yaxistitle': 'Energie',
                'div': 'stacked_timeseries',
            }
            for commodity, asset_list in ts_data.items()
        ]

        return JsonResponse(results_json, status=200, content_type='application/json', safe=False)
    except Exception as e:
        logger.error(f"Dashboard ERROR: MVS Req Id: {scenario.simulation.mvs_token}. Thrown Exception: {e}")
        return JsonResponse({"error": f"Could not retrieve kpi cost data."}, status=404,
                            content_type='application/json', safe=False)


# TODO: Sector coupling must be refined (including transformer flows)
def scenario_visualize_stacked_total_flow(request, scen_id):
    scenario = get_object_or_404(Scenario, pk=scen_id)
    if (scenario.project.user != request.user) and (request.user not in scenario.project.viewers.all()):
        raise PermissionDenied

    try:
        assets_results_obj = AssetsResults.objects.get(simulation=scenario.simulation)
        assets_results_json = json.loads(assets_results_obj.assets_list)
        ts_data = get_asset_and_ts(assets_results_json)

        results_json = [
            {'values':
                [
                    {
                        'x': ['Erzeugung', 'Verbrauch'],
                        'y': [sum(asset_obj['flow']['value']), 0]
                        if asset_obj['type_oemof'] == 'source'
                        else [0, sum(asset_obj['flow']['value'])],
                        'name': asset_obj['label'].replace('_', ' ').upper()+' in '+asset_obj['flow']['unit']
                                if asset_obj['flow']['unit']!='?'
                                else asset_obj['label'].replace('_', ' ').upper()+' in kWh',
                        'type': 'bar',

                    }
                    for asset, asset_list in ts_data.items()
                    for asset_obj in asset_list
                    if asset_obj['type_oemof'] in ['source', 'sink']
                ],
                'title': 'Erzeugung und Verbrauch',
                'yaxistitle': 'Kumulierte Energie',
                'div': 'stacked_total_flow',
            }
        ]

        return JsonResponse(results_json, status=200, content_type='application/json', safe=False)
    except Exception as e:
        logger.error(f"Dashboard ERROR: MVS Req Id: {scenario.simulation.mvs_token}. Thrown Exception: {e}")
        return JsonResponse({"error": f"Could not retrieve kpi cost data."}, status=404,
                            content_type='application/json', safe=False)


def scenario_visualize_stacked_capacities(request, scen_id):
    scenario = get_object_or_404(Scenario, pk=scen_id)
    if (scenario.project.user != request.user) and (request.user not in scenario.project.viewers.all()):
        raise PermissionDenied

    try:
        assets_results_obj = AssetsResults.objects.get(simulation=scenario.simulation)
        assets_results_json = json.loads(assets_results_obj.assets_list)

        ts_data = get_asset_and_ts(assets_results_json)

        results_json = [
            {'values':
                [
                    {
                        'x': ['Installierte Kapazität'],
                        'y': [asset_obj['installed_capacity']['value']],
                        'name': asset_obj['label'].replace('_', ' ').upper()+' in '+asset_obj['flow']['unit']
                                if asset_obj['flow']['unit']!='?'
                                else asset_obj['label'].replace('_', ' ').upper()+' in kWh',
                        'type': 'bar',

                    }
                    for asset, asset_list in ts_data.items()
                    for asset_obj in asset_list
                ],
            'title': 'Installierte Kapazität',
            'yaxistitle': 'Leistung',
            'div': 'capacities',
            }
        ]

        return JsonResponse(results_json, status=200, content_type='application/json', safe=False)
    except Exception as e:
        logger.error(f"Dashboard ERROR: MVS Req Id: {scenario.simulation.mvs_token}. Thrown Exception: {e}")
        return JsonResponse({"error": f"Could not retrieve kpi cost data."}, status=404,
                            content_type='application/json', safe=False)

# TODO: push optimizedAddCap for DSO to KPI as "Spitzenlast"/ "Peak Demand"
# TODO: Make a note appear if all components have optimized_capacity = False because no figure will be shown
def scenario_visualize_stacked_optimized_capacities(request, scen_id):
    scenario = get_object_or_404(Scenario, pk=scen_id)
    if (scenario.project.user != request.user) and (request.user not in scenario.project.viewers.all()):
        raise PermissionDenied

    try:
        results_dict = json.loads(Scenario.objects.first().simulation.results)
        kpi_scalar_matrix = results_dict['kpi']['scalar_matrix']
        assets_results_obj = AssetsResults.objects.get(simulation=scenario.simulation)
        assets_results_json = json.loads(assets_results_obj.assets_list)
        asset_optimizeCap = dict()

        for asset, asset_list in assets_results_json.items():
            for asset_obj in asset_list:
                asset_optimizeCap[asset_obj['label']] = asset_obj['optimize_capacity']['value']

        results_json = [
            {'values':
                [
                    {
                        'x': ['Optimierte Kapazität'],
                        'y': [asset_parameters['optimizedAddCap']],
                        'name': asset.replace('_', ' ').upper()+' in '+asset_parameters['unit']
                                if asset_parameters['unit']!='?'
                                else asset.replace('_', ' ').upper()+' in kW',
                        'type': 'bar',

                    }
                    for asset, asset_parameters in kpi_scalar_matrix.items()
                    if asset_optimizeCap[asset] is True
                ],
            'title': 'Optimierte Kapazität',
            'yaxistitle': 'Leistung',
            'div': 'capacities',
            }
        ]

        return JsonResponse(results_json, status=200, content_type='application/json', safe=False)
    except Exception as e:
        logger.error(f"Dashboard ERROR: MVS Req Id: {scenario.simulation.mvs_token}. Thrown Exception: {e}")
        return JsonResponse({"error": f"Could not retrieve kpi cost data."}, status=404,
                            content_type='application/json', safe=False)


@login_required
@require_http_methods(["GET"])
def download_scalar_results(request, scen_id):
    scenario = get_object_or_404(Scenario, pk=scen_id)

    if (scenario.project.user != request.user) and (request.user not in scenario.project.viewers.all()):
        raise PermissionDenied

    try:
        kpi_scalar_results_obj = KPIScalarResults.objects.get(simulation=scenario.simulation)
        kpi_scalar_values_dict = json.loads(kpi_scalar_results_obj.scalar_values)
        scalar_kpis_json = kpi_scalars_list(kpi_scalar_values_dict, KPI_SCALAR_UNITS, KPI_SCALAR_TOOLTIPS)

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Scalars')

        for idx, kpi_obj in enumerate(scalar_kpis_json):
            if idx == 0:
                worksheet.write_row(0, 0, kpi_obj.keys())
            worksheet.write_row(idx + 1, 0, kpi_obj.values())

        workbook.close()
        output.seek(0)
    except Exception as e:
        logger.error(
            f"Dashboard ERROR: Could not generate KPI Scalars download file with Scenario Id: {scen_id}. Thrown Exception: {e}")
        raise Http404()

    filename = 'kpi_scalar_results.xlsx'
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={filename}'

    return response


@login_required
@require_http_methods(["GET"])
def download_cost_results(request, scen_id):
    scenario = get_object_or_404(Scenario, pk=scen_id)

    if (scenario.project.user != request.user) and (request.user not in scenario.project.viewers.all()):
        raise PermissionDenied

    try:
        kpi_cost_results_obj = KPICostsMatrixResults.objects.get(simulation=scenario.simulation)
        kpi_cost_values_dict = json.loads(kpi_cost_results_obj.cost_values)

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Costs')

        for col, asset in enumerate(kpi_cost_values_dict.items()):
            asset_name, asset_dict = asset
            if col == 0:
                worksheet.write_column(1, 0, asset_dict.keys())
                worksheet.write_row(0, 1, kpi_cost_values_dict.keys())
            worksheet.write_column(1, col + 1, asset_dict.values())

        workbook.close()
        output.seek(0)
    except Exception as e:
        logger.error(
            f"Dashboard ERROR: Could not generate KPI Costs download file with Scenario Id: {scen_id}. Thrown Exception: {e}")
        raise Http404()

    filename = 'kpi_individual_costs.xlsx'
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={filename}'

    return response


@login_required
@require_http_methods(["GET"])
def download_timeseries_results(request, scen_id):
    scenario = get_object_or_404(Scenario, pk=scen_id)

    if (scenario.project.user != request.user) and (request.user not in scenario.project.viewers.all()):
        raise PermissionDenied

    try:
        assets_results_obj = AssetsResults.objects.get(simulation=scenario.simulation)
        assets_results_json = json.loads(assets_results_obj.assets_list)
        # Create the datetimes index. Constrains: step in minutes and evaluated_period in days
        base_date = scenario.start_date
        datetime_list = [
            datetime.datetime.timestamp(base_date + datetime.timedelta(minutes=step))
            for step in range(0, 24 * scenario.evaluated_period * scenario.time_step, scenario.time_step)
        ]

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        merge_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
        })

        KEY1, KEY2, KEY3, KEY4 = ('timeseries_soc', 'input power', 'output power', 'storage capacity')

        for key in assets_results_json.keys():
            worksheet = workbook.add_worksheet(key)
            worksheet.write(0, 0, 'Timestamp')
            if key != 'energy_storage':
                worksheet.write_column(2, 0, datetime_list)
                for col, asset in enumerate(assets_results_json[key]):
                    if all(key in asset.keys() for key in ['label', 'flow']):
                        worksheet.write(0, col + 1, asset['label'])
                        worksheet.write(1, col + 1, asset['flow']['unit'])
                        worksheet.write_column(2, col + 1, asset['flow']['value'])
            else:
                worksheet.write_column(3, 0, datetime_list)
                col = 0
                for idx, storage_asset in enumerate(assets_results_json[key]):
                    if all(key in storage_asset.keys() for key in ['label', KEY1, KEY2, KEY3, KEY4]):
                        worksheet.merge_range(0, col + 1, 0, col + 4, storage_asset['label'], merge_format)

                        worksheet.write(1, col + 1, KEY1)
                        worksheet.write(2, col + 1, storage_asset[KEY1]['unit'])
                        worksheet.write_column(3, col + 1, storage_asset[KEY1]['value'])

                        worksheet.write(1, col + 2, KEY2)
                        worksheet.write(2, col + 2, storage_asset[KEY2]['flow']['unit'])
                        worksheet.write_column(3, col + 2, storage_asset[KEY2]['flow']['value'])

                        worksheet.write(1, col + 3, KEY3)
                        worksheet.write(2, col + 3, storage_asset[KEY3]['flow']['unit'])
                        worksheet.write_column(3, col + 3, storage_asset[KEY3]['flow']['value'])

                        worksheet.write(1, col + 4, KEY4)
                        worksheet.write(2, col + 4, storage_asset[KEY4]['flow']['unit'])
                        worksheet.write_column(3, col + 4, storage_asset[KEY3]['flow']['value'])

                        col += 5

        workbook.close()
        output.seek(0)

        filename = 'timeseries_results.xlsx'
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response
    except Exception as e:
        logger.error(
            f"Dashboard ERROR: Could not generate Timeseries Results file for the Scenario with Id: {scen_id}. Thrown Exception: {e}")
        raise Http404()
