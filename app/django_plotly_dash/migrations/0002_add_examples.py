# Generated by Django 2.0.5 on 2018-06-08 20:03

# pylint: skip-file

from django.db import migrations
from ..util import insert_demo_migrations

def addExamples(apps, schema_editor):

    if not insert_demo_migrations():
        return

    DashApp = apps.get_model("django_plotly_dash","DashApp")
    StatelessApp = apps.get_model("django_plotly_dash","StatelessApp")

    sa1 = StatelessApp(app_name="SimpleExample",
                       slug="simple-example")

    sa1.save()

    da1 = DashApp(stateless_app=sa1,
                  instance_name="SimpleExample-1",
                  slug="simpleexample-1",
                  base_state='{"dropdown-color":{"value":"blue"},"dropdown-size":{"value":"small"}}')

    da1.save()

    sa2 = StatelessApp(app_name="LiveOutput",
                       slug="liveoutput")

    sa2.save()

    sa21 = StatelessApp(app_name="LiveInput",
                       slug="liveinput")

    sa21.save()

    da2 = DashApp(stateless_app=sa2,
                  instance_name="liveoutput-2",
                  slug="liveoutput-2",
                  base_state='''{"named_count_pipe": {
                      "label": "named_counts",
                      "channel_name": "live_button_counter",
                      "value": null},
 "state_uid": {"value": "635c89ae-c996-4488-84df-041c1153fdef"}}
''',
                  save_on_change=True)

    da2.save()

    sa3 = StatelessApp(app_name="Ex2",
                       slug="ex2")

    sa3.save()

    da3 = DashApp(stateless_app=sa3,
                  instance_name="Ex2-1",
                  slug="ex2-3",
                  base_state='{"dropdown-one":{"value":"Nitrogen"}}',
                  save_on_change=True)

    da3.save()

    sa4 = StatelessApp(app_name="MultipleCallbackValues",
                       slug="multiple-callback-values")

    sa4.save()

    da4 = DashApp(stateless_app=sa4,
                  instance_name="Multiple Callback Values Example 1",
                  slug="multiple-callback-values-1")

    da4.save()

    sa5 = StatelessApp(app_name="MultipleCallbackValuesExpanded",
                       slug="multiple-callback-values-exapnded")

    sa5.save()

    da5 = DashApp(stateless_app=sa5,
                  instance_name="Multiple Callback Values Example 2",
                  slug="multiple-callback-values-expanded")

    da5.save()

    sa6 = StatelessApp(app_name="PatternStateCallbacks",
                       slug="pattern-state-callback")

    sa6.save()

    da6 = DashApp(stateless_app=sa6,
                  instance_name="Pattern and State saving Example",
                  slug="pattern-state-callback")

    da6.save()


def remExamples(apps, schema_editor):

    DashApp = apps.get_model("django_plotly_dash","DashApp")
    StatelessApp = apps.get_model("django_plotly_dash","StatelessApp")

    DashApp.objects.all().delete()
    StatelessApp.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('django_plotly_dash', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(addExamples, remExamples),
    ]