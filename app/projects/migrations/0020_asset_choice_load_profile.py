# Generated by Django 3.2.16 on 2022-12-01 17:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("projects", "0019_alter_asset_balanced")]

    operations = [
        migrations.AddField(
            model_name="asset",
            name="choice_load_profile",
            field=models.CharField(
                choices=[
                    ("", "Choose..."),
                    ("load_profile_1", "load profile 1"),
                    ("load_profile_2", "load profile 2"),
                    ("load_profile_3", "load profile 3"),
                ],
                max_length=20,
                null=True,
            ),
        )
    ]
