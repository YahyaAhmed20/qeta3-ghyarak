from django.urls import path

from .views import MeView, RequestLoginOTPView,VerifyLoginOTPView



app_name = "accounts"


urlpatterns = [
    path(
        "auth/login/request-otp/",
        RequestLoginOTPView.as_view(),
        name="request-login-otp",
    ),
    path(
        "auth/login/verify-otp/",
        VerifyLoginOTPView.as_view(),
        name="verify-login-otp",
),
    path(
        "auth/me/",
        MeView.as_view(),
        name="me",
    ),
]