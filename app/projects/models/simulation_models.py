from .base_models import AbstractSimulation, Scenario


import json
import jsonschema
import numpy as np
import logging
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


class SensitivityAnalysis(AbstractSimulation):
    name = models.CharField(max_length=50)
    # attribute linked to output_parameter_names
    output_parameters_names = models.TextField()
    # attributes linked to variable_parameter_name
    variable_name = models.CharField(max_length=100)
    # attributes to compute the variable_parameter_range
    variable_min = models.FloatField()
    variable_max = models.FloatField()
    variable_step = models.FloatField(validators=[MinValueValidator(0.0)])
    # attributes linked to variable_parameter_ref_val
    variable_reference = models.FloatField(
        help_text=_(
            "The value of the variable parameter for the reference scenario of the sensitivity analysis, if is it different than the value of the current scenario user need to decide whether to take current scenario as reference with its actual value for this parameter, duplicate the scenario and use the duplicata with chosen reference value or keep current scenario but change parameter value to chosen one"
        )
    )  # label=_("Variable parameter of the reference scenario"),
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, null=True)
    # attribute linked to the output values of the sensitivity analysis
    output_parameters_values = models.TextField()
    nested_dict_pathes = None

    # TODO look at jsonschema to create a custon TextField --> https://dev.to/saadullahaleem/adding-validation-support-for-json-in-django-models-5fbm

    def save(self, *args, **kwargs):
        # if self.output_parameters_names is not None:
        #     self.output_parameters_names = json.dumps(self.output_parameters_names)
        super().save(*args, **kwargs)
        if self.scenario is not None:
            self.nested_dict_pathes = nested_dict_crawler(
                format_scenario_for_mvs(self.scenario)
            )

    def set_reference_scenario(self, scenario):
        self.scenario = scenario
        self.save()

    def collect_simulations_tokens(self, server_response):
        try:
            jsonschema.validate(server_response, SA_MVS_TOKEN_SCHEMA)
        except jsonschema.exceptions.ValidationError:
            answer = {}

    @property
    def variable_range(self):
        return np.arange(
            self.variable_min, self.variable_max, self.variable_step
        ).tolist()

    @property
    def output_names(self):
        try:
            answer = json.loads(self.output_parameters_names)
            try:
                jsonschema.validate(answer, SA_OUPUT_NAMES_SCHEMA)
            except jsonschema.exceptions.ValidationError:
                answer = []
        except json.decoder.JSONDecodeError:
            answer = []

        return answer

    @property
    def output_values(self):
        try:
            answer = json.loads(self.output_parameters_values)
            try:
                jsonschema.validate(
                    answer, sa_output_values_schema_generator(self.output_names)
                )
            except jsonschema.exceptions.ValidationError:
                answer = {}
        except json.decoder.JSONDecodeError:
            answer = {}
        return answer

    @property
    def payload(self):
        return sensitivity_analysis_payload(
            variable_parameter_name=self.variable_name_path,
            variable_parameter_range=self.variable_range,
            variable_parameter_ref_val=self.variable_reference,
            output_parameter_names=self.output_names,
        )

    @property
    def variable_name_path(self):
        """Provided with a (nested) dict, find the path to the variable_name"""
        if self.nested_dict_pathes is None:
            variable_name_path = self.variable_name
        else:
            if "." in self.variable_name:
                asset_name, variable_name = self.variable_name.split(".")
            else:
                variable_name = self.variable_name
                asset_name = None
            variable_name_path = self.nested_dict_pathes.get(variable_name, None)
            if variable_name_path is None:
                if asset_name is not None:
                    asset = self.scenario.asset_set.get(name=asset_name)
                    variable_name_path = asset.parameter_path(variable_name)
                if variable_name_path is None:
                    logging.error(
                        f"The variable '{self.variable_name}' cannot be found in the scenario json structure"
                    )

            if isinstance(variable_name_path, list):
                variable_name_path = variable_name_path[0]
        return variable_name_path
