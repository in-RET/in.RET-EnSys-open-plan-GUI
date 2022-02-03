import os
import csv
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils.translation import ugettext_lazy as _
from numbers import Number
import pickle
from django.conf import settings as django_settings
from .models import ReportItem

#### CONSTANTS ####

sectors = ['Electricity', 'Heat', 'Gas', 'H2']

KPIS = {}
MANAGEMENT_CAT = "management"
ECONOMIC_CAT = "economic"
TECHNICAL_CAT = "technical"
ENVIRONEMENTAL_CAT = "environemental"
TABLES = {MANAGEMENT_CAT: {}, ECONOMIC_CAT: {}, TECHNICAL_CAT: {}, ENVIRONEMENTAL_CAT: {}}
EMPTY_SUBCAT = "none"

with open(staticfiles_storage.path("MVS_kpis_list.csv")) as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for i, row in enumerate(csvreader):
        if i == 0:
            hdr = row
            label_idx = hdr.index("label")
            verbose_idx = hdr.index("verbose")
            unit_idx = hdr.index(":Unit:")
            cat_idx = hdr.index("category")
            subcat_idx = hdr.index("subcategory")
        else:
            label = row[label_idx]
            verbose = row[verbose_idx]
            unit = row[unit_idx]
            KPIS[label] = {k: v for k, v in zip(hdr, row)}

            cat = row[cat_idx]
            subcat = row[subcat_idx]
            if subcat == MANAGEMENT_CAT:
                # reverse the category and the subcategory for this special table (management is not a parameter type, whereas all other table are also parameter types)
                subcat = cat
                cat = MANAGEMENT_CAT

            if subcat != EMPTY_SUBCAT:
                if cat in TABLES:
                    if subcat not in TABLES[cat]:
                        TABLES[cat][subcat] = []
                    if label not in TABLES[cat][subcat]:
                        # the _() make the text translatable if it is mentionned in the django.po file
                        TABLES[cat][subcat].append(
                            {"name": _(verbose), "id": label, "unit": _(unit)}
                        )

KPI_PARAMETERS = {}
with open(staticfiles_storage.path("MVS_kpis_list.csv")) as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for i, row in enumerate(csvreader):
        if i == 0:
            hdr = [el.replace(' ', '_').replace(':', '').lower() for el in row]
            print(hdr)
            label_idx = hdr.index("label")
            cat_idx = hdr.index("category")
        else:
            label = row[label_idx]
            category = row[cat_idx]
            if category != "files":
                KPI_PARAMETERS[label] = {k: _(v) if k == "verbose" or k == "definition" else v for k, v in zip(hdr, row)}


#### FUNCTIONS ####


def storage_asset_to_list(assets_results_json):
    """
    bring all storage subassets one level up to show their flows.
    restructure the main json dict to contain storage 
    'charging power','discharging power' and 'capacity' in the same level as storage.
    """
    if 'energy_storage' in assets_results_json.keys():
        for storage_asset in assets_results_json['energy_storage']:
            for subasset in storage_asset.values():
                if isinstance(subasset, dict) and 'flow' in subasset.keys():
                    subasset['energy_vector'] = storage_asset['energy_vector']
                    subasset['label'] = storage_asset['label']+subasset['label']
                    assets_results_json['energy_storage'].append(subasset)


def kpi_scalars_list(kpi_scalar_values_dict, KPI_SCALAR_UNITS, KPI_SCALAR_TOOLTIPS):
    return (
        [
            {
                'kpi': key.replace('_',' '),
                'value': round(val, 3) if 'currency/kWh' in KPI_SCALAR_UNITS[key] else round(val,2),
                'unit': KPI_SCALAR_UNITS[key],
                'tooltip': KPI_SCALAR_TOOLTIPS[key]
            }
            if key in KPI_SCALAR_UNITS.keys()
            else 
            {
                'kpi': key.replace('_',' '),
                'value': round(val, 3),
                'unit': 'N/A',
                'tooltip': ''
            }
            for key, val in kpi_scalar_values_dict.items()
        ]
    )


def round_only_numbers(input, decimal_place):
    if isinstance(input, Number):
        return round(input, decimal_place)
    else:
        return input


def nested_dict_crawler(dct, path=None, path_dct=None):
    r"""A recursive algorithm that crawls through a (nested) dictionary and returns
    a dictionary of keys and a list of its paths within the (nested) dictionary to the respective key
            Parameters
            ----------
            dct: dict
                the (potentially nested) dict from which we want to get the value
            path: list
                storing the current path that the algorithm is on
            path_dct: dict
                result dictionary where each key is assigned to its (multiple) paths within the (nested) dictionary
            Returns
            -------
            Dictionary of key and paths to the respective key within the nested dictionary structure
            Example
            -------
            >>> dct = dict(a=dict(a1=1, a2=2),b=dict(b1=dict(b11=11,b12=dict(b121=121))))
            >>> nested_dict_crawler(dct)
            {
                "a1": [("a", "a1")],
                "a2": [("a", "a2")],
                "b11": [("b", "b1", "b11")],
                "b121": [("b", "b1", "b12", "b121")],
            }
            """
    if path is None:
        path = []
    if path_dct is None:
        path_dct = dict()

    for key, value in dct.items():
        path.append(key)
        if isinstance(value, dict):
            if 'value' in value.keys() and 'unit' in value.keys():
                if path[-1] in path_dct:
                    path_dct[path[-1]].append(tuple(path))
                else:
                    path_dct[path[-1]] = [tuple(path)]
            else:
                nested_dict_crawler(value, path, path_dct)
        else:
            if path[-1] in path_dct:
                path_dct[path[-1]].append(tuple(path))
            else:
                path_dct[path[-1]] = [tuple(path)]
        path.pop()
    return path_dct


def dict_keyword_mapper(results_dct,kw_dct, kw):
    r"""Get a list of key paths from nested dict structure
            Parameters
            ----------
            results_dct: dict
                the (potentially nested) dict from which we want to get a value
            kw_dct: dict
                keyword dictionary of results_dct that contains a list of paths to a key assigned to the respective key
            kw: string
                keyword from which we want the value within results_dct without knowing the path to it
            Returns
            -------
            List of key paths within the nested dictionary structure, each key path is itself a list.
            Example
            -------
            >>> dct = dict(a=dict(a1=1, a2=2),b=dict(b1=dict(b11=11,b12=dict(b121=121))))
            >>> dict_keyword_mapper(dct, nested_dict_crawler(dct), 'b121')
            121
            """
    if kw in kw_dct:
        if len(kw_dct[kw]) == 1:
            return get_nested_value(results_dct, kw_dct[kw][0])
        else:
            return kw_dct[kw]
    else:
        return f'No key found for {kw}'


def get_nested_value(dct, keys):
    r"""Get a value from a succession of keys within a nested dict structure

    Parameters
    ----------
    dct: dict
        the (potentially nested) dict from which we want to get a value
    keys: tuple
        Tuple containing the succession of keys which lead to the value within the nested dict

    Returns
    -------
    The value under the path within the (potentially nested) dict

    Example
    -------
    >>> dct = dict(a=dict(a1=1, a2=2),b=dict(b1=dict(b11=11,b12=dict(b121=121))))
    >>> print(get_nested_value(dct, ("b", "b1", "b12","b121")))
    121
    """
    if isinstance(keys, tuple) is True:
        if len(keys) > 1:
            answer = get_nested_value(dct[keys[0]], keys[1:])
        elif len(keys) == 1:
            answer = dct[keys[0]]
        else:
            raise ValueError(
                "The tuple argument 'keys' from get_nested_value() should not be empty"
            )
    else:
        raise TypeError("The argument 'keys' from get_nested_value() should be a tuple")
    return answer


class KPIFinder():
    """Helper to access a kpi value in a nested dict only providing the kpi name"""
    def __init__(self, results_dct):
        self.results_dct = results_dct
        self.kpi_mapping = nested_dict_crawler(self.results_dct)

    def get(self, kpi_name):
        return dict_keyword_mapper(self.results_dct, self.kpi_mapping, kpi_name)

    def get_value(self, kpi_name):
        return dict_keyword_mapper(self.results_dct, self.kpi_mapping, kpi_name)['value']

    def get_unit(self, kpi_name):
        return dict_keyword_mapper(self.results_dct, self.kpi_mapping, kpi_name)['unit']


def get_project_reportitems(project):
    """Given a project, return the ReportItem instances linked to that project"""
    qs = project.scenario_set.filter(simulation__isnull=False).filter(simulation__reportitem__isnull=False).values_list("simulation__reportitem", flat=True).distinct()
    return ReportItem.objects.filter(id__in=[ri for ri in qs])
