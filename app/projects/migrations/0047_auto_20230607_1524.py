# Generated by Django 3.2.7 on 2023-06-07 15:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0046_alter_asset_annual_energy_consumption"),
    ]

    operations = [
        migrations.AlterField(
            model_name="asset",
            name="oep_column_name",
            field=models.CharField(max_length=120, null=True),
        ),
        migrations.AlterField(
            model_name="asset",
            name="oep_table_name",
            field=models.CharField(max_length=120, null=True),
        ),
    ]
