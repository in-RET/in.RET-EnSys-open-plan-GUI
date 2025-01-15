import os
import smtplib
import ssl

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetView
from django.contrib.sites.shortcuts import get_current_site
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.http import require_http_methods

from projects.services import send_email as send_email_exchange

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser

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

            to_email = form.cleaned_data.get("email")
            sender = os.getenv("EMAIL_SENDER")

            with smtplib.SMTP(host=os.getenv("EMAIL_HOST_IP"), port=587) as mailserver:
                mailserver.ehlo()
                mailserver.starttls(context=ssl.create_default_context())
                mailserver.ehlo()
                mailserver.login(os.getenv("EMAIL_HOST_USER"), os.getenv("EMAIL_HOST_PASSWORD"))

                header = 'To:' + to_email + '\n' + 'From:' + sender + '\n' + 'Subject:' + mail_subject + '\n\n'
                mailserver.sendmail(sender, to_email, header + email)
                mailserver.close()

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


#@login_required
@require_http_methods(["GET", "POST"])
def password_reset_request(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            user = get_user_model().objects.get(email=form.cleaned_data["email"])
        else:
            user = get_object_or_404(CustomUser, username=request.user)

        print(user)

        mail_subject = "Password Reset Requested"
        email = render_to_string(
            "registration/acc_reset_password.html",
            {
                "user": user,
                "domain": get_current_site(request).domain
            }
        )

        to_email = user.email
        sender = os.getenv("EMAIL_SENDER")

        with smtplib.SMTP(host=os.getenv("EMAIL_HOST_IP"), port=587) as mailserver:
            mailserver.ehlo()
            mailserver.starttls(context=ssl.create_default_context())
            mailserver.ehlo()
            mailserver.login(os.getenv("EMAIL_HOST_USER"), os.getenv("EMAIL_HOST_PASSWORD"))

            header = 'To:' + to_email + '\n' + 'From:' + sender + '\n' + 'Subject:' + mail_subject + '\n\n'
            mailserver.sendmail(sender, to_email, header + email)
            mailserver.close()

        return render(
            request=request,
            template_name="registration/password_reset_done.html"
        )
    else:
        if request.user.is_authenticated:
            return render(
                request=request,
                template_name="registration/password_reset_form.html"
            )
        else:
            form = PasswordResetForm()
            return render(
                request=request,
                template_name="registration/password_reset_form.html",
                context={"form": form}
            )

#     if request.method == "POST":
#         password_reset_form = PasswordResetForm(request.POST)
#         if password_reset_form.is_valid():
#             data = password_reset_form.cleaned_data["email"]
#             associated_users = CustomUser.objects.filter(Q(email=data))
#             if associated_users.exists():
#                 for user in associated_users:
#                     subject = "Password Reset Requested"
#                     email_template_name = "registration/password_reset_email.txt"
#                     c = {
#                         "email": user.email,
#                         "domain": EMAIL_HOST,
#                         "site_name": "open_plan",
#                         "uid": urlsafe_base64_encode(force_bytes(user.pk)),
#                         "user": user,
#                         "token": default_token_generator.make_token(user),
#                         "protocol": "http",
#                     }
#                     email = render_to_string(email_template_name, c)
#                     try:
#                         send_mail(
#                             subject,
#                             email,
#                             DEFAULT_FROM_EMAIL,
#                             [user.email],
#                             fail_silently=False,
#                         )
#                     except BadHeaderError:
#                         return HttpResponse("Invalid header found.")
#                     return redirect("/password_reset/done/")
#     password_reset_form = PasswordResetForm()
#     return render(
#         request=request,
#         template_name="registration/password_reset_form.html",
#         context={"password_reset_form": password_reset_form},
#     )


class ExchangePasswordResetForm(PasswordResetForm):
    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        """
        Send a django.core.mail.EmailMultiAlternatives to `to_email`.
        """
        subject = render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = "".join(subject.splitlines())
        # Force the https for the production
        if settings.DEBUG is False:
            context["protocol"] = "https"
        message = render_to_string(email_template_name, context)
        send_email_exchange(to_email=to_email, subject=subject, message=message)


class ExchangePasswordResetView(PasswordResetView):
    form_class = ExchangePasswordResetForm


@login_required
@require_http_methods(["POST"])
def user_deletion_request(request):
    user_pk = request.user.pk
    logout(request)
    user_model = get_user_model()
    user_model.objects.filter(pk=user_pk).delete()
    messages.info(request, "Your user account has been deleted.")
    return redirect("home")