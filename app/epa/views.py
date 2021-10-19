from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.utils.translation import ugettext_lazy as _
import logging

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def imprint(request):
    return render(request, "legal/imprint.html")


@require_http_methods(["GET"])
def privacy(request):
    return render(request, "legal/privacy.html")