import logging
import os
import traceback
from django_q.models import Schedule
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from projects.models import Simulation
from projects.requests import fetch_mvs_simulation_status
from projects.constants import PENDING
from concurrent.futures import ThreadPoolExecutor
from exchangelib import (
    Account,
    Credentials,
    Mailbox,
    Message,
    EWSTimeZone,
    Configuration,
)


logger = logging.getLogger(__name__)

# email account which will send the feedback emails
EXCHANGE_ACCOUNT = os.getenv("EXCHANGE_ACCOUNT")
EXCHANGE_PW = os.getenv("EXCHANGE_PW")
EXCHANGE_EMAIL = os.getenv("EXCHANGE_EMAIL")
EXCHANGE_SERVER = os.getenv("EXCHANGE_SERVER")
# email addresses to which the feedback emails will be sent
RECIPIENTS = os.getenv("RECIPIENTS").split(",")


r"""Functions meant to be powered by Django-Q.

Those functions require Django-Q cluster to run along with Django Server.
To achieve this `python manage.py qcluster` command needs to be executed.

"""


def check_simulation_objects(**kwargs):
    pending_simulations = Simulation.objects.filter(status=PENDING)
    if pending_simulations.count() == 0:
        logger.debug(f"No pending simulation found. Deleting Scheduler.")
        Schedule.objects.all().delete()
    # fetch_mvs_simulation_status mostly waits for MVS API to respond, so no ProcessPool is required.
    with ThreadPoolExecutor() as pool:
        pool.map(fetch_mvs_simulation_status, pending_simulations)
    logger.debug(f"Finished round for checking Simulation objects status.")


def create_or_delete_simulation_scheduler(**kwargs):
    r"""Initialize a Django-Q Scheduler for all Simulation objects.

    If there are Simulation objects in the database, being in "PENDING" state
    a Scheduler is created to check periodically each Simulation (utilizes MVS API).
    If there is no Simulation is "PENDING" state the Scheduler object is deleted.

    Parameters
    ----------
    **kwargs : dict
        Possible future keyword arguments.

    Returns
    -------
    bool :
        True if Scheduler object is created or False otherwise.

    """
    mvs_token = kwargs.get("mvs_token", "")

    if Schedule.objects.count() == 0:
        logger.info(
            f"No Scheduler found. Creating a new Scheduler to check Simulation {mvs_token}."
        )
        schedule = Schedule.objects.create(
            name=f"djangoQ_Scheduler-{mvs_token}",
            func="projects.services.check_simulation_objects",
            # args='5',
            schedule_type=Schedule.MINUTES,
            minutes=1
            # kwargs={'test_arg': 1, 'test_arg2': "test"}
        )
        if schedule.id:
            logger.info(
                f"New Scheduler Created to track simulation {mvs_token} objects status."
            )
            return True
        else:
            logger.debug(f"Scheduler already exists for {mvs_token}. Skipping.")
            return False


def send_feedback_email(subject, body):
    tz = EWSTimeZone("Europe/Copenhagen")
    try:
        credentials = Credentials(EXCHANGE_ACCOUNT, EXCHANGE_PW)

        config = Configuration(server=EXCHANGE_SERVER, credentials=credentials)

        account = Account(
            EXCHANGE_EMAIL,
            credentials=credentials,
            autodiscover=False,
            default_timezone=tz,
            config=config,
        )
        recipients = [Mailbox(email_address=recipient) for recipient in RECIPIENTS]
        mail = Message(
            account=account,
            folder=account.sent,
            subject=subject,
            body=body,
            to_recipients=recipients,
        )
        mail.send_and_save()
    except Exception as ex:
        logger.warning(
            f"Couldn't send feedback email. Exception raised: {traceback.format_exc()}."
        )
        raise ex


def excuses_design_under_development(request, link=False):
    if link is False:
        msg = """This page is still under development. What you see is a design draft of how it should look like. If you have ideas or feedback about the design, you are welcome to submit it using the <a href='{url}'>feedback form</a>"""
    else:
        msg = """This website is still under development and not all buttons link to what they should yet. This is the case of the link or button you just clicked on. If you have ideas or feedback on how to improve the design, you are welcome to submit it using the <a href='{url}'>feedback form</a>"""

    url = reverse("user_feedback")
    messages.warning(request, _(mark_safe(msg.format(url=url))))
