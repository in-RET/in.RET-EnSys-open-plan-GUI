# Generated by Django 3.2.7 on 2023-08-14 16:18

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0053_asset_trafo_input_output_variation_choice"),
    ]

    operations = [
        migrations.AddField(
            model_name="asset",
            name="trafo_input_conversionf_1",
            field=models.FloatField(
                blank=True,
                null=True,
                validators=[django.core.validators.MinValueValidator(0.0)],
            ),
        ),
    ]
