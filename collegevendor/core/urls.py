from django.urls import path
from . import views

urlpatterns = [
    path('', views.pending_approval, name='pending_approval'),
    path('queue/', views.college_approval_queue, name='college_approval_queue'),
    path('approve/<int:college_id>/<str:action>/', views.approve_college, name='approve_college'),
    path('queue/<int:college_id>/', views.college_detail_admin, name='college_detail_admin'),
    path('delete/<int:college_id>/', views.delete_college, name='delete_college'),
    path('notify/', views.send_platform_notification, name='send_platform_notification'),
    path('test-email/', views.test_email, name='test_email'),
]