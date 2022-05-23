# Generated by Django 3.2 on 2022-04-04 19:48

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AssetsResults",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("assets_list", models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name="KPICostsMatrixResults",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("cost_values", models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name="KPIScalarResults",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("scalar_values", models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name="ReportItem",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(blank=True, default="", max_length=120)),
                (
                    "report_type",
                    models.CharField(
                        choices=[
                            ("timeseries", "Timeseries graph"),
                            ("timeseries_stacked", "Stacked timeseries graph"),
                            ("capacities", "Installed and optimized capacities"),
                            ("bar", "Bar chart"),
                            ("pie", "Pie chart"),
                            ("load_duration", "Load duration curve"),
                            ("sankey", "Sankey diagram"),
                        ],
                        max_length=50,
                    ),
                ),
                ("parameters", models.TextField(blank=True, default="")),
            ],
        ),
        migrations.CreateModel(
            name="SensitivityAnalysisGraph",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(blank=True, default="", max_length=120)),
                (
                    "report_type",
                    models.CharField(
                        default="sensitivity_analysis", editable=False, max_length=20
                    ),
                ),
                (
                    "y",
                    models.CharField(
                        choices=[
                            ("annual_total_flow", "Aggregated flow"),
                            (
                                "annuity_om",
                                "Annual operation, maintenance and dispatch expenses",
                            ),
                            ("annuity_total", "Annuity"),
                            ("average_flow", "Average flow"),
                            ("costs_cost_om", "Operation and maintenance costs"),
                            ("costs_dispatch", "Dispatch costs"),
                            ("costs_investment_over_lifetime", "Investment costs"),
                            (
                                "costs_om_total",
                                "Operation, maintenance and dispatch costs",
                            ),
                            ("costs_total", "Net Present Costs (NPC)"),
                            ("costs_upfront_in_year_zero", "Upfront investment costs"),
                            ("flow", "Dispatch of an asset"),
                            (
                                "levelized_cost_of_energy_of_asset",
                                "Levelized cost of throughput",
                            ),
                            ("optimizedAddCap", "Optimal additional capacity"),
                            ("peak_flow", "Peak flow"),
                            (
                                "replacement_costs_during_project_lifetime",
                                "Replacement costs",
                            ),
                            ("total_emissions", "Total GHG emissions"),
                        ],
                        max_length=50,
                    ),
                ),
            ],
        ),
    ]