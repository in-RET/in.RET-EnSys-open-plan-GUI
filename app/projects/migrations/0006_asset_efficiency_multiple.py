# Generated by Django 3.2 on 2022-08-08 19:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("projects", "0005_usecase")]

    operations = [
        migrations.AddField(
            model_name="asset",
            name="efficiency_multiple",
            field=models.TextField(null=True),
        )
    ]
