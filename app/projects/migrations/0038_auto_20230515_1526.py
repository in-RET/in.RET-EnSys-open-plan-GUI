# Generated by Django 3.2.7 on 2023-05-15 15:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0037_scenario_timeframe_choice"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="scenario",
            name="timeframe_choice",
        ),
        migrations.AddField(
            model_name="scenario",
            name="user_mode_choice",
            field=models.CharField(
                choices=[
                    ("", "Choose..."),
                    ("Default User", "Default User"),
                    ("Expert", "Expert"),
                ],
                max_length=40,
                null=True,
            ),
        ),
    ]
