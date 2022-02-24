from .base_models import AbstractSimulation, Scenario


import json
import jsonschema
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from django.utils.translation import gettext_lazy as _

from projects.constants import USER_RATING
from projects.helpers import (
    sensitivity_analysis_payload,
    SA_OUPUT_NAMES_SCHEMA,
    sa_output_values_schema_generator,
    SA_MVS_TOKEN_SCHEMA,
    format_scenario_for_mvs,
)

from dashboard.helpers import nested_dict_crawler


class Simulation(AbstractSimulation):
    scenario = models.OneToOneField(Scenario, on_delete=models.CASCADE, null=False)
    user_rating = models.PositiveSmallIntegerField(
        null=True, choices=USER_RATING, default=None
    )

