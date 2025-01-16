from django.urls import path

from .views import (
    signup,
    change_password,
    user_info,
    activate,
    user_deletion_request,
    reset_password_request,
)

urlpatterns = [
    path("signup/", signup, name="signup"),
    path("change_password/", change_password, name="change_password"),
    path("user_info/", user_info, name="user_info"),
    path("activate/<uidb64>/<token>/", activate, name="activate"),
    path("password_reset", reset_password_request, name="password_reset"),
    path("user_deletion", user_deletion_request, name="user_deletion"),
]
