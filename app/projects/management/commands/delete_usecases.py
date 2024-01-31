from django.core.management.base import BaseCommand
from projects.models import *


class Command(BaseCommand):
    help = "Delete all usecase"

    def handle(self, *args, **options):
        UseCase.objects.all().delete()
