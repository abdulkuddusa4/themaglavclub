from django.urls import path

from accounts.views import (
    # ProfileUpdateView,
    UserCreateAPIView,
    JTLoginView,
    request_password_reset,
    verify_otp,
    change_password,
    reset_password,
    ActivateAccountView
)

urlpatterns = [
    path('register/', UserCreateAPIView.as_view(), name='register'),
    path('login/', JTLoginView.as_view(), name='login'),
    path('activate/', ActivateAccountView.as_view(), name='activate'),
    # path('profile/', ProfileUpdateView.as_view(), name='profile'),
    path('request_password_reset/', request_password_reset),
    path('verify_otp/', verify_otp),
    path('change_password', change_password),
    path('reset_password/', reset_password),
]