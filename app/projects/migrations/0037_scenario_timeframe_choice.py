# Generated by Django 3.2.7 on 2023-05-10 18:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0036_remove_scenario_capex_fix'),
    ]

    operations = [
        migrations.AddField(
            model_name='scenario',
            name='timeframe_choice',
            field=models.CharField(choices=[('', 'Choose...'), ('Hour(s)', 'Hour(s)'), ('Day(s)', 'Day(s)'), ('Week(s)', 'Week(s)'), ('Month(s)', 'Month(s)'), ('Year', 'Year')], max_length=40, null=True),
        ),
    ]
