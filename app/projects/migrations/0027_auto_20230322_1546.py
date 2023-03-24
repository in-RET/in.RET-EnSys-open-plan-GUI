# Generated by Django 3.2.7 on 2023-03-22 15:46

import django.core.validators
from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [("projects", "0026_inputparametersuggestion")]

    operations = [
        migrations.AddField(
            model_name="inputparametersuggestion",
            name="crate",
            field=models.FloatField(
                blank=True,
                null=True,
                validators=[django.core.validators.MinValueValidator(0.0)],
            ),
        ),
        migrations.AddField(
            model_name="inputparametersuggestion",
            name="efficiency",
            field=models.FloatField(
                blank=True,
                null=True,
                validators=[django.core.validators.MinValueValidator(0.0)],
            ),
        ),
        migrations.AddField(
            model_name="inputparametersuggestion",
            name="efficiency_el",
            field=models.FloatField(
                blank=True,
                null=True,
                validators=[django.core.validators.MinValueValidator(0.0)],
            ),
        ),
        migrations.AddField(
            model_name="inputparametersuggestion",
            name="efficiency_th",
            field=models.FloatField(
                blank=True,
                null=True,
                validators=[django.core.validators.MinValueValidator(0.0)],
            ),
        ),
        migrations.AddField(
            model_name="inputparametersuggestion",
            name="input_timeseries",
            field=jsonfield.fields.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name="inputparametersuggestion",
            name="technology",
            field=models.CharField(max_length=120, null=True),
        ),
        migrations.AlterField(
            model_name="inputparametersuggestion",
            name="unique_id",
            field=models.AutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="inputparametersuggestion",
            name="year",
            field=models.IntegerField(null=True),
        ),
    ]
