from django.urls import path, re_path
from .views import *

urlpatterns = [
    path('scenario/results/visualize', scenario_visualize_results, name='scenario_visualize_results'),
    path('scenario/results/visualize/<int:scen_id>', scenario_visualize_results, name='scenario_visualize_results'),
    re_path(r'^project/(?P<proj_id>\d+)/results/visualize/scenario/(?P<scen_id>(?:\w+/)+)/$', scenario_visualize_results, name='scenario_visualize_results'),
    path('scenario/results/request/<int:scen_id>', scenario_request_results, name='scenario_request_results'),
    path('scenario/results/available/<int:scen_id>', scenario_available_results, name='scenario_available_results'),
    path('scenario/results/request_economic_data/<int:scen_id>', scenario_economic_results, name='scenario_economic_results'),
    re_path(r'^scenario/results/request_kpi_table/(?P<table_style>\w+)?$', request_kpi_table, name='request_kpi_table'),
    re_path(r'^scenario/results/update_selected_scenarios/(?P<scen_id>\d+)?$', update_selected_scenarios, name='update_selected_scenarios'),
    path('scenario/results/request_minh_test/<int:scen_id>', scenario_visualize_timeseries, name='scenario_visualize_timeseries'),
    path('scenario/results/request_minh_test1/<int:scen_id>', scenario_visualize_stacked_timeseries, name='scenario_visualize_stacked_timeseries'),
    path('scenario/results/request_minh_test2/<int:scen_id>', scenario_visualize_stacked_total_flow, name='scenario_visualize_stacked_total_flow'),
    path('scenario/results/request_minh_test3/<int:scen_id>', scenario_visualize_stacked_capacities, name='scenario_visualize_stacked_capacities'),
    path('scenario/results/download_scalars/<int:scen_id>', download_scalar_results, name='download_scalar_results'),
    path('scenario/results/download_costs/<int:scen_id>', download_cost_results, name='download_cost_results'),
    path('scenario/results/download_timeseries/<int:scen_id>', download_timeseries_results, name='download_timeseries_results'),
]
