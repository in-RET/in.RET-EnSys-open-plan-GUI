import json
import uuid
from datetime import timedelta

import oemof.thermal.compression_heatpumps_and_chillers as cmpr_hp_chiller
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.forms.models import model_to_dict
from django.utils.translation import gettext_lazy as _

from projects.constants import (
    ASSET_CATEGORY,
    ASSET_TYPE,
    COUNTRY,
    CURRENCY,
    ENERGY_VECTOR,
    COP_MODES,
    FLOW_DIRECTION,
    MVS_TYPE,
    SIMULATION_STATUS,
    PENDING,
    TRUE_FALSE_CHOICES,
    BOOL_CHOICES,
    USER_RATING,
    LOAD_PROFILE_CHOICE,
    FLOW_CHOICE,
    SOURCE_CHOICE,
    TRAFO_CHOICE,
    STORAGE_CHOICE,
    # TIME_CHOICE,
    USER_MODE,
    MW_KW_CHOICE,
    CO2_UNIT_CHOICE,
    TRAFO_I_O_VARIATION_CHOICE,
)
from users.models import CustomUser


# import jsonfield


class Feedback(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=200)
    subject = models.CharField(max_length=200)
    feedback = models.TextField()
    rating = models.PositiveSmallIntegerField(choices=USER_RATING, null=True)


class EconomicData(models.Model):
    # duration = models.PositiveSmallIntegerField()
    currency = models.CharField(max_length=3, choices=CURRENCY)
    # discount = models.FloatField(
    #     validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    # )
    # tax = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])


class Viewer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    share_rights = models.CharField(
        max_length=10, choices=(("edit", _("Edit")), ("read", _("Read")))
    )

    def __str__(self):
        return f"{self.user.email} [{self.share_rights}]"


class Project(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=120)
    description = models.TextField()
    country = models.CharField(max_length=50, choices=COUNTRY)
    latitude = models.FloatField()
    longitude = models.FloatField()
    economic_data = models.OneToOneField(
        EconomicData, on_delete=models.SET_NULL, null=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True
    )
    viewers = models.ManyToManyField(Viewer, related_name="viewer_projects")
    unit_choice = models.CharField(
        null=True, blank=False, choices=MW_KW_CHOICE, max_length=40
    )
    unit_choice_co2 = models.CharField(
        null=True, blank=False, choices=CO2_UNIT_CHOICE, max_length=40
    )

    def __str__(self):
        return self.name

    def get_scenarios_with_results(self):
        return self.scenario_set.filter(simulation__isnull=False).filter(
            simulation__results__isnull=False
        )

    def export(self, bind_scenario_data=True):
        """
        Parameters
        ----------
        bind_scenario_data : bool
            when True, the scenarios of the project are saved
            Default: False.
        ...
        Returns
        -------
        A dict with the parameters describing a scenario model
        """
        dm = model_to_dict(self, exclude=["id", "user", "viewers"])
        dm["economic_data"] = model_to_dict(self.economic_data, exclude=["id"])
        if bind_scenario_data is True:
            scenario_data = []
            for scenario in self.scenario_set.all():
                scenario_data.append(scenario.export())
            dm["scenario_set_data"] = scenario_data
        return dm

    def add_viewer_if_not_exist(self, email=None, share_rights=""):
        user = None
        success = False
        if email is not None:
            users = CustomUser.objects.filter(email=email)
            if users.exists():
                user = users.first()
        else:
            message = _(
                f"No email address provided to find the user to share the project '{self.name}' with"
            )

        if user is not None:
            viewers = Viewer.objects.filter(user=user)
            if viewers.exists():
                viewer = viewers.get()
            else:
                if user == self.user:
                    viewer = None
                    message = _("You cannot share a project with yourself")
                else:
                    viewer = Viewer.objects.create(user=user, share_rights=share_rights)

            if viewer not in self.viewers.all() and viewer is not None:
                self.viewers.add(viewer)
                success = True
                message = _(
                    f"'{email}' belongs to a valid user, they will be able to {share_rights} the project '{self.name}'"
                )
            else:
                if viewer is not None:
                    if viewer.share_rights != share_rights:
                        success = True
                        message = _(
                            f"The share rights of the user registered under {email} for the project '{self.name}' have been changed from '{viewer.share_rights}' to '{share_rights}'"
                        )
                        viewer.share_rights = share_rights
                        viewer.save()
                    else:
                        message = _(
                            f"The user registered under {email} for the project '{self.name}' already have '{share_rights}' access"
                        )

        else:
            message = _(
                f"We could not find a user registered under the email address you provided: {email}"
            )
        return (success, message)

    def revoke_access(self, viewers=None):
        """Given a queryset of viewers or a list of viewers ids, remove those viewers from projects viewers"""
        success = False
        if isinstance(viewers, int):
            viewers = Viewer.objects.filter(id__in=[viewers])
        elif isinstance(viewers, list):
            viewers = Viewer.objects.filter(id__in=viewers)

        if viewers is not None:
            existing_viewers = viewers.intersection(self.viewers.all())
            if existing_viewers.exists():

                for viewer_id in existing_viewers.values_list("id", flat=True):
                    self.viewers.remove(viewer_id)
                success = True
                message = _(
                    f"The user(s) {','.join(existing_viewers.values_list('user__email', flat=True))} rights to the project '{self.name}' have been revoked"
                )
            else:
                message = _(
                    f"The user(s) {','.join(viewers.values_list('user__email', flat=True))} does not belong to the viewers of the project '{self.name}'"
                )
        else:
            message = _(
                "The user(s) you selected seems to not be registered in the open_plan tool"
            )
        return success, message


class Comment(models.Model):
    name = models.CharField(max_length=60)
    body = models.TextField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name


class Scenario(models.Model):
    name = models.CharField(max_length=60)

    start_date = models.DateTimeField()
    time_step = models.IntegerField(validators=[MinValueValidator(0)])
    # capex_fix = models.FloatField(
    #     validators=[MinValueValidator(0.0)], default=0, blank=True
    # )
    # The next 3 fields make no sense for a scenario, they are asset fields.
    # Removing them caused trouble with existing database though, so default values are used instead
    # related to https://github.com/open-plan-tool/gui/issues/32
    capex_var = models.FloatField(
        validators=[MinValueValidator(0.0)], default=0, blank=True
    )
    opex_fix = models.FloatField(
        validators=[MinValueValidator(0.0)], default=0, blank=True
    )
    opex_var = models.FloatField(
        validators=[MinValueValidator(0.0)], default=0, blank=True
    )
    evaluated_period = models.IntegerField(validators=[MinValueValidator(0)])
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True)

    # timeframe_choice = models.CharField(
    #     null=True, blank=False, choices=TIME_CHOICE, max_length=40
    # )

    # BUG: Reset of choosen Values via Default Value after editing
    user_mode_choice = models.CharField(
        null=True, blank=False, choices=USER_MODE, max_length=40, default="Default User"
    )

    interest_rate = models.FloatField(
        null=True, blank=False, validators=[MinValueValidator(0.0)]
    )

    # BUG: Reset of choosen Values via Default Value after editing
    simulation_year = models.IntegerField(
        validators=[MinValueValidator(2024)], default=2025
    )

    def __str__(self):
        return self.name

    def get_timestamps(self, json_format=False):
        answer = []

        n_occurence_per_day = int((24 * 60) / self.time_step)

        for i in range(self.evaluated_period):
            for j in range(n_occurence_per_day):
                iter_date = self.start_date + timedelta(
                    days=i + 1, minutes=self.time_step * (j + 1)
                )
                if json_format is True:
                    iter_date = iter_date.isoformat().replace("T", " ")
                answer.append(iter_date)
        return answer

    def get_currency(self):
        return self.project.economic_data.currency

    @property
    def energy_vectors(self):
        """Return a list of energy vectors used in a scenario"""
        vectors = []
        for vector in self.bus_set.all().values_list("type", flat=True):
            if vector not in vectors:
                vectors.append(vector)
        return vectors

    def export(self, bind_project_data=False):
        """
        Parameters
        ----------
        bind_project_data : bool
            when True, the project data is saved along the scenario data
            Default: False.
        ...
        Returns
        -------
        A dict with the parameters describing a scenario model
        """
        dm = model_to_dict(self, exclude=["id"])
        dm["start_date"] = str(dm["start_date"])
        if bind_project_data is True:
            dm["project"] = self.project.export(bind_scenario_data=False)
        else:
            dm.pop("project")

        energy_model_assets = self.asset_set.all()
        dm["assets"] = []
        for asset in energy_model_assets:
            dm["assets"].append(asset.export())

        clinks = self.connectionlink_set.all()
        bus_ids = list(set(clinks.values_list("bus", flat=True)))
        busses = []
        for bus_id in bus_ids:
            bus = Bus.objects.get(id=bus_id)
            bus_data = model_to_dict(bus, exclude=["id", "parent_asset", "scenario"])
            bus_data["inputs"] = []
            bus_data["outputs"] = []
            for connection in bus.connectionlink_set.all():
                if connection.flow_direction == "A2B":
                    bus_data["inputs"].append(connection.export())
                elif connection.flow_direction == "B2A":
                    bus_data["outputs"].append(connection.export())
            busses.append(bus_data)
        dm["busses"] = busses
        return dm


class AssetType(models.Model):
    asset_type = models.CharField(
        max_length=30, choices=ASSET_TYPE, null=False, unique=True
    )
    asset_category = models.CharField(max_length=30, choices=ASSET_CATEGORY)
    energy_vector = models.CharField(max_length=20, choices=ENERGY_VECTOR)
    mvs_type = models.CharField(max_length=20, choices=MVS_TYPE)
    # TODO Could be listCharField ...
    asset_fields = models.TextField(null=True)
    unit = models.CharField(max_length=30, null=True)

    def export(self):
        """
        Returns
        -------
        A dict with the parameters describing an asset type model
        """
        dm = model_to_dict(self, exclude=["id"])
        return dm

    @property
    def visible_fields(self):
        return self.asset_fields.replace("[", "").replace("]", "").split(",")

    def add_field(self, field_name):
        temp = self.visible_fields
        if field_name not in temp:
            temp.append(field_name)
            self.asset_fields = "[" + ",".join(temp) + "]"

    def remove_field(self, field_name):
        temp = self.visible_fields
        if field_name in temp:
            temp.pop(temp.index(field_name))
            self.asset_fields = "[" + ",".join(temp) + "]"


class TopologyNode(models.Model):
    name = models.CharField(max_length=60, null=False, blank=False)
    pos_x = models.FloatField(default=0.0)
    pos_y = models.FloatField(default=0.0)
    scenario = models.ForeignKey(
        Scenario, on_delete=models.CASCADE, null=False, blank=False
    )
    parent_asset = models.ForeignKey(
        to="Asset", on_delete=models.CASCADE, null=True, blank=True
    )

    class Meta:
        abstract = True


class ValueType(models.Model):
    type = models.CharField(max_length=30, null=False, unique=True)
    unit = models.CharField(max_length=30, null=True)


class InputparameterSuggestion(models.Model):
    unique_id = models.AutoField(
        verbose_name="ID", serialize=False, auto_created=True, primary_key=True
    )
    technology = models.CharField(max_length=120, null=True, blank=False)

    capex = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0.0)]
    )
    opex = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])
    lifetime = models.IntegerField(
        null=True, blank=True, validators=[MinValueValidator(0)]
    )
    year = models.IntegerField(null=True, blank=False)
    crate = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0.0)]
    )
    efficiency = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0.0)]
    )
    efficiency_el = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0.0)]
    )
    efficiency_th = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0.0)]
    )
    # input_timeseries = jsonfield.JSONField()
    input_timeseries = models.TextField(null=True, blank=True)
    thermal_loss_rate = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0.0)]
    )
    fixed_losses_relative_gamma = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0.0)]
    )
    fixed_losses_absolute_delta = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0.0)]
    )


class Asset(TopologyNode):
    def save(self, *args, **kwargs):
        if self.asset_type.asset_type in ["dso", "gas_dso", "h2_dso", "heat_dso"]:
            self.optimize_cap = False
        super().save(*args, **kwargs)

    unique_id = models.CharField(
        max_length=120, default=uuid.uuid4, unique=True, editable=False
    )
    capex_fix = models.FloatField(
        null=True, blank=False, validators=[MinValueValidator(0.0)]
    )  # development_costs
    capex_var = models.FloatField(
        null=True, blank=False, validators=[MinValueValidator(0.0)]
    )  # specific_costs
    opex_fix = models.FloatField(
        null=True, blank=False, validators=[MinValueValidator(0.0)]
    )  # specific_costs_om
    opex_var = models.FloatField(
        null=True, blank=False, validators=[MinValueValidator(0.0)]
    )  # dispatch_price
    # lifetime = models.IntegerField(
    #     null=True, blank=False, validators=[MinValueValidator(0)]
    # )

    crate = models.FloatField(
        null=True, blank=False, default=1, validators=[MinValueValidator(0.0)]
    )
    efficiency = models.TextField(null=True, blank=True)
    # used in the case of transformers with one input and two outputs
    # or two inputs and one output
    efficiency_multiple = models.TextField(null=True, blank=False)

    soc_max = models.FloatField(
        null=True,
        blank=False,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    soc_min = models.FloatField(
        null=True,
        blank=False,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    dispatchable = models.BooleanField(
        null=True, blank=False, choices=TRUE_FALSE_CHOICES, default=None
    )
    maximum_capacity = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0.0)]
    )
    energy_price = models.TextField(null=True, blank=False)
    feedin_tariff = models.TextField(null=True, blank=False)

    feedin_cap = models.FloatField(
        default=None, null=True, blank=True, validators=[MinValueValidator(0.0)]
    )

    peak_demand_pricing = models.FloatField(
        null=True, blank=False, validators=[MinValueValidator(0.0)]
    )
    peak_demand_pricing_period = models.SmallIntegerField(
        null=True, blank=False, validators=[MinValueValidator(0)]
    )
    renewable_share = models.FloatField(
        null=True,
        blank=False,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    renewable_asset = models.BooleanField(
        null=True, blank=False, choices=TRUE_FALSE_CHOICES, default=None
    )
    asset_type = models.ForeignKey(
        AssetType, on_delete=models.CASCADE, null=False, blank=True
    )
    optimize_cap = models.BooleanField(
        null=True, blank=False, choices=BOOL_CHOICES, default=False
    )
    installed_capacity = models.FloatField(
        null=True, blank=False, validators=[MinValueValidator(0.0)]
    )
    age_installed = models.FloatField(
        null=True, blank=False, validators=[MinValueValidator(0.0)]
    )

    ###########################################################################
    input_timeseries = models.TextField(
        null=True, blank=True
    )  # , validators=[validate_timeseries])
    variable_costs = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0.0)]
    )
    nominal_value = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0.0)]
    )
    _max = models.FloatField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    _min = models.FloatField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    nonconvex = models.BooleanField(
        null=True, blank=False, choices=TRUE_FALSE_CHOICES, default=False
    )
    summed_max = models.FloatField(
        default=None, blank=True, null=True, validators=[MinValueValidator(0.0)]
    )
    summed_min = models.FloatField(
        default=None, blank=True, null=True, validators=[MinValueValidator(0.0)]
    )
    maximum = models.FloatField(
        default=None, blank=True, null=True, validators=[MinValueValidator(0.0)]
    )
    minimum = models.FloatField(
        default=None, blank=True, null=True, validators=[MinValueValidator(0.0)]
    )
    existing = models.FloatField(
        default=None, blank=True, null=True, validators=[MinValueValidator(0.0)]
    )
    capex = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0.0)]
    )
    opex = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])
    offset = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0.0)]
    )
    lifetime = models.IntegerField(
        null=True, blank=True, validators=[MinValueValidator(0)]
    )

    thermal_loss_rate = models.FloatField(
        default=None, null=True, blank=True, validators=[MinValueValidator(0.0)]
    )
    fixed_thermal_losses_relative = models.FloatField(
        null=True, blank=True, default=None
    )
    fixed_thermal_losses_absolute = models.FloatField(
        null=True, blank=True, default=None
    )

    balanced = models.BooleanField(
        null=True, blank=False, choices=BOOL_CHOICES, default=True
    )
    invest_relation_input_capacity = models.FloatField(
        null=True, blank=True, default=None, validators=[MinValueValidator(0.0)]
    )
    invest_relation_output_capacity = models.FloatField(
        null=True, blank=True, default=None, validators=[MinValueValidator(0.0)]
    )
    initial_storage_level = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    inflow_conversion_factor = models.FloatField(
        null=True,
        blank=False,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    outflow_conversion_factor = models.FloatField(
        null=True,
        blank=False,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    nominal_storage_capacity = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0.0)]
    )
    choice_load_profile = models.CharField(
        null=True, blank=False, choices=LOAD_PROFILE_CHOICE, max_length=20
    )
    eco_params_flow_choice = models.CharField(
        null=True, blank=False, choices=FLOW_CHOICE, max_length=40
    )
    tec_params_flow_choice = models.CharField(
        null=True, blank=False, choices=FLOW_CHOICE, max_length=40
    )
    emission_factor = models.FloatField(default=None, blank=True, null=True)
    renewable_factor = models.FloatField(default=None, blank=True, null=True)
    oep_table_name = models.CharField(max_length=120, null=True, blank=False)
    oep_column_name = models.CharField(max_length=120, null=True, blank=False)
    source_choice = models.CharField(
        null=True, blank=False, choices=SOURCE_CHOICE, max_length=40
    )
    # year_choice_source = models.IntegerField(
    #     null=True, blank=False, choices=YEAR_CHOICE
    # )
    # year_choice_trafo = models.IntegerField(null=True, blank=False, choices=YEAR_CHOICE)
    trafo_choice = models.CharField(
        null=True, blank=False, choices=TRAFO_CHOICE, max_length=40
    )
    efficiency_el = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0.0)]
    )
    efficiency_th = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0.0)]
    )
    storage_choice = models.CharField(
        null=True, blank=False, choices=STORAGE_CHOICE, max_length=40
    )
    # year_choice_storage = models.IntegerField(
    #     null=True, blank=False, choices=YEAR_CHOICE
    # )
    annual_energy_consumption = models.FloatField(
        null=True, blank=False, validators=[MinValueValidator(0.0)]
    )
    ##########
    # expert trafo
    trafo_input_output_variation_choice = models.CharField(
        null=True, blank=False, choices=TRAFO_I_O_VARIATION_CHOICE, max_length=40
    )
    # trafo input bus
    trafo_input_bus_1 = models.CharField(
        default="Choose", max_length=128  # at least one input
    )
    trafo_input_bus_2 = models.CharField(
        default="Choose", max_length=128, null=True, blank=True
    )
    trafo_input_bus_3 = models.CharField(
        default="Choose", max_length=128, null=True, blank=True
    )
    # trafo input conversion factor
    trafo_input_conversionf_1 = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0.0)]
    )
    trafo_input_conversionf_2 = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0.0)]
    )
    trafo_input_conversionf_3 = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0.0)]
    )

    # trafo output bus
    trafo_output_bus_1 = models.CharField(
        default="Choose", max_length=128  # at least one output
    )
    trafo_output_bus_2 = models.CharField(
        default="Choose", max_length=128, null=True, blank=True
    )
    trafo_output_bus_3 = models.CharField(
        default="Choose", max_length=128, null=True, blank=True
    )
    # trafo output conversion factor
    trafo_output_conversionf_1 = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0.0)]
    )
    trafo_output_conversionf_2 = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0.0)]
    )
    trafo_output_conversionf_3 = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0.0)]
    )
    ###
    trafo_technicalp_bus_choice = models.CharField(
        default="Choose", max_length=128, null=True, blank=True
    )
    trafo_invest_bus_choice = models.CharField(
        default="Choose", max_length=128, null=True, blank=True
    )
    trafo_variableCosts_bus_choice = models.CharField(
        default="Choose", max_length=128, null=True, blank=True
    )

    @property
    def fields(self):
        return [f.name for f in self._meta.fields + self._meta.many_to_many]

    @property
    def visible_fields(self):
        visible_fields = self.asset_type.visible_fields
        # renaming the model variable might be too dangerous with existing database
        if "optimize_cap" in visible_fields:
            visible_fields[visible_fields.index("optimize_cap")] = "optimize_capacity"
        return visible_fields

    def has_parameter(self, param_name):
        return param_name in self.visible_fields

    def parameter_path(self, param_name):
        # TODO for storage
        if self.has_parameter(param_name):
            # TODO if (unit, value) formatting, add "value" at the end
            if self.asset_type.asset_category == "energy_provider":
                asset_category = "energy_providers"
            else:
                asset_category = self.asset_type.asset_category
            # renaming the model variable might be too dangerous with existing database
            if param_name == "optimize_cap":
                param_name = "optimize_capacity"
            answer = (asset_category, self.name, param_name)
        else:
            answer = None
        return answer

    @property
    def is_provider(self):
        return self.asset_type.asset_type in ["dso", "gas_dso", "h2_dso", "heat_dso"]

    @property
    def is_storage(self):
        return self.asset_type.asset_category == "energy_storage"

    @property
    def timestamps(self):
        return self.scenario.get_timestamps()

    @property
    def input_timeseries_values(self):
        if self.is_input_timeseries_empty() is False:
            answer = json.loads(self.input_timeseries)
        else:
            answer = []
        return answer

    def export(self):
        """
        Returns
        -------
        A dict with the parameters describing an asset model
        """

        fields = (
            self.asset_type.asset_fields.replace("[", "").replace("]", "").split(",")
        )
        fields += ["name", "pos_x", "pos_y"]
        dm = model_to_dict(self, fields=fields)
        dm["asset_info"] = self.asset_type.export()

        # check for parent assets
        if self.parent_asset is not None:
            dm["parent_asset"] = self.parent_asset.name

        return dm

    def is_input_timeseries_empty(self):
        return self.input_timeseries == ""


class COPCalculator(models.Model):

    scenario = models.ForeignKey(
        Scenario, on_delete=models.CASCADE, null=False, blank=False
    )
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, null=True, blank=True)

    temperature_high = models.TextField(null=False, blank=False)
    temperature_low = models.TextField(null=False, blank=False)

    temp_threshold_icing = quality_grade = models.FloatField(
        null=True, default=2, validators=[MinValueValidator(-273.15)]
    )

    quality_grade = models.FloatField(
        null=True,
        default=1,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    factor_icing = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )

    mode = models.CharField(max_length=20, choices=COP_MODES)

    @property
    def temp_high(self):
        try:
            answer = json.loads(self.temperature_high)
        except json.decoder.JSONDecodeError:
            answer = []
        if isinstance(answer, float):
            answer = [answer]
        return answer

    @property
    def temp_low(self):
        try:
            answer = json.loads(self.temperature_low)
        except json.decoder.JSONDecodeError:
            answer = []
        if isinstance(answer, float):
            answer = [answer]
        return answer

    def calc_cops(self):
        cops = cmpr_hp_chiller.calc_cops(
            temp_high=self.temp_high,
            temp_low=self.temp_low,
            mode=self.mode,
            quality_grade=self.quality_grade,
            factor_icing=self.factor_icing,
            temp_threshold_icing=self.temp_threshold_icing,
        )
        if len(cops) == 1:
            cops = cops[0]
        return cops


class Bus(TopologyNode):
    type = models.CharField(max_length=20, choices=ENERGY_VECTOR, default="Electricity")
    # TODO now these parameters are useless ...
    input_ports = models.IntegerField(null=False, default=1)
    output_ports = models.IntegerField(null=False, default=1)


class ConnectionLink(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, null=False)
    bus_connection_port = models.CharField(null=False, max_length=12)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, null=False)
    flow_direction = models.CharField(max_length=15, choices=FLOW_DIRECTION, null=False)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, null=False)

    def export(self):
        """
        Returns
        -------
        A dict with the parameters describing a connectionlink model
        """
        dm = model_to_dict(self, exclude=["id", "scenario", "bus"])
        dm["asset"] = self.asset.name
        return dm


class Constraint(models.Model):
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, null=False)
    activated = models.BooleanField(
        null=True, blank=False, choices=BOOL_CHOICES, default=False
    )

    class Meta:
        abstract = True


class MinRenewableConstraint(Constraint):
    value = models.FloatField(
        null=False,
        blank=False,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        default=0.2,
    )
    unit = models.CharField(max_length=6, default="factor", editable=False)
    name = models.CharField(
        max_length=30, default="minimal_renewable_factor", editable=False
    )


class MaxEmissionConstraint(Constraint):
    value = models.FloatField(
        null=False, blank=False, validators=[MinValueValidator(0.0)], default=0.0
    )
    unit = models.CharField(max_length=9, default="kgCO2eq/a", editable=False)
    name = models.CharField(max_length=30, default="maximum_emissions", editable=False)


class MinDOAConstraint(Constraint):
    value = models.FloatField(
        null=False,
        blank=False,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        default=0.3,
    )
    unit = models.CharField(max_length=6, default="factor", editable=False)
    name = models.CharField(
        max_length=30, default="minimal_degree_of_autonomy", editable=False
    )


class NZEConstraint(Constraint):
    value = models.BooleanField(
        null=True, blank=False, choices=BOOL_CHOICES, default=False
    )
    unit = models.CharField(max_length=4, default="bool", editable=False)
    name = models.CharField(max_length=30, default="net_zero_energy", editable=False)


class ScenarioFile(models.Model):
    title = models.CharField(max_length=50)
    file = models.FileField(upload_to="tempFiles/", null=True, blank=True)


class AbstractSimulation(models.Model):
    start_date = models.DateTimeField(auto_now_add=True, null=False)
    end_date = models.DateTimeField(null=True)
    elapsed_seconds = models.FloatField(null=True)
    mvs_token = models.CharField(max_length=200, null=True)
    status = models.CharField(
        max_length=20, choices=SIMULATION_STATUS, null=False, default=PENDING
    )
    results = models.TextField(null=True, max_length=30e6)
    errors = models.TextField(null=True)

    class Meta:
        abstract = True
