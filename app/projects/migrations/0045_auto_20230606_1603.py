# Generated by Django 3.2.7 on 2023-06-06 16:03

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0044_auto_20230606_1429"),
    ]

    operations = [
        migrations.AddField(
            model_name="asset",
            name="annual_energy_consumption",
            field=models.FloatField(
                blank=True,
                null=True,
                validators=[django.core.validators.MinValueValidator(0.0)],
            ),
        ),
        migrations.AlterField(
            model_name="asset",
            name="storage_choice",
            field=models.CharField(
                choices=[
                    ("", "Choose..."),
                    ("Sodium storage", "Sodium storage"),
                    ("Lithium Ion Battery Storage", "Lithium Ion Battery Storage"),
                    ("Pumped storage power plant", "Pumped storage power plant"),
                    ("Heat storage", "Heat storage (seasonal)"),
                    ("Heat storage (short term)", "Heat storage (short term)"),
                    ("Gas storage", "Gas storage"),
                    ("Hydrogen storage", "Hydrogen storage"),
                    ("Other", "Other"),
                ],
                max_length=40,
                null=True,
            ),
        ),
    ]
