from django.core.management.base import BaseCommand, CommandError
from projects.models import Scenario
from projects.models import *
from projects.models.usecases import load_usecase_from_dict


class Command(BaseCommand):
    help = "Create a usecase from a project provided its id"

    def add_arguments(self, parser):
        parser.add_argument("proj_id", nargs="+", type=int)

    def handle(self, *args, **options):
        for proj_id in options["proj_id"]:
            try:
                project = Project.objects.get(pk=proj_id)
                dm = project.export()
                load_usecase_from_dict(dm)
            except Scenario.DoesNotExist:
                raise CommandError('proj_id "%s" does not exist' % proj_id)
