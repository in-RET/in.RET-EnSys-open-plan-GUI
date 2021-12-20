import os
import csv
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils.translation import ugettext_lazy as _
import pickle
from django.conf import settings as django_settings

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

