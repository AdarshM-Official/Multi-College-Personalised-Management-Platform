from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import home, dashboard, college_directory, public_college_detail
from accounts.views import register_college, user_login, user_logout

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('explore/', college_directory, name='public_college_directory'),
    path('college/<slug:slug>/', public_college_detail, name='public_college_detail'),
    path('dashboard/', dashboard, name='dashboard'),
    
    # Auth & Approval
    path('register/', register_college, name='register_college'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('pending-approval/', include([
        path('', include('core.urls')), # We'll put them in core.urls for cleanliness
    ])),
    
    # Apps
    path('management/', include('management.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
