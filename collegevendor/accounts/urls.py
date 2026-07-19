from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Password Reset
    path('password-reset/', views.forgot_password, name='password_reset'),
    path('password-reset/verify-otp/', views.verify_otp, name='verify_otp'),
    path('password-reset/new-password/', views.new_password, name='new_password'),
]