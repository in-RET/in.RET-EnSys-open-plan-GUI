import os
import smtplib
import ssl

import exchangelib
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetView
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.http import require_http_methods

from app.settings import (
    EMAIL_HOST_USER,
    EMAIL_HOST_PASSWORD,
    EMAIL_HOST,
    TIME_ZONE,
    DEFAULT_FROM_EMAIL,
)
from .forms import CustomUserCreationForm, CustomUserChangeForm

UserModel = get_user_model()


def signup(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            mail_subject = "Activate your account."
            email = render_to_string(
                "registration/acc_active_email.html",
                {
                    "user": user,
                    "domain": get_current_site(request).domain,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": default_token_generator.make_token(user),
                },
            )

            tz = exchangelib.EWSTimeZone(TIME_ZONE)
            cred = exchangelib.Credentials(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            config = exchangelib.Configuration(server=EMAIL_HOST, credentials=cred)

            account = exchangelib.Account(
                primary_smtp_address=DEFAULT_FROM_EMAIL,
                credentials=cred,
                autodiscover=False,
                default_timezone=tz,
                config=config,
            )

            msg = exchangelib.Message(
                account=account,
                subject=mail_subject,
                body=email,
                to_recipients=[form.cleaned_data.get("email")],
            )

            msg.send_and_save()

            messages.info(
                request,
                "Please confirm your email address to complete the registration",
            )
            return redirect("home")
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/signup.html", {"form": form})


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = UserModel._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(
            request,
            "Thank you for your email confirmation. Now you can login your account.",
        )
        return redirect("login")
    else:
        return HttpResponse("Activation link is invalid!")


@login_required
@require_http_methods(["GET", "POST"])
def user_info(request):
    if request.method == "POST":
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save()
            messages.success(request, "User info successfully updated!")
            return redirect("user_info")
        else:
            messages.error(request, "Please check errors and resubmit!")
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, "registration/user_info.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, "Your password was successfully updated!")
            return redirect("change_password")
        else:
            messages.error(request, "Please check errors and resubmit!")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "registration/change_password.html", {"form": form})


def reset_password_request(request):
    return render(
        request=request,
        template_name="registration/password_reset_form.html",
        context={},
    )


@login_required
@require_http_methods(["POST"])
def user_deletion_request(request):
    user_pk = request.user.pk
    logout(request)
    user_model = get_user_model()
    user_model.objects.filter(pk=user_pk).delete()
    messages.info(request, "Your user account has been deleted.")
    return redirect("home")
