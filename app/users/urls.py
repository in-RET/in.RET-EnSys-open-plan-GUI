from django.urls import path

from .views import signup, change_password, user_info, activate, password_reset_request

urlpatterns = [
    path("signup/", signup, name="signup"),
    path("change_password/", change_password, name="change_password"),
    path("user_info/", user_info, name="user_info"),
    path("activate/<uidb64>/<token>/", activate, name="activate"),
    #path("password_reset", password_reset_request, name="password_reset"),
    path("password_reset", ExchangePasswordResetView.as_view(), name="password_reset"),
    path("user_deletion", user_deletion_request, name="user_deletion"),

]
