# Generated by Django 3.2.16 on 2022-11-22 17:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("projects", "0018_alter_asset_input_timeseries")]

    operations = [
        migrations.AlterField(
            model_name="asset",
            name="balanced",
            field=models.BooleanField(
                choices=[(True, "Yes"), (False, "No")], default=True, null=True
            ),
        )
    ]
