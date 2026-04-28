from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import tenant_home, dashboard
from accounts.views import user_login, user_logout

urlpatterns = [
    path('', tenant_home, name='tenant_home'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    
    # We include management routes inside the tenant URLs
    path('management/', include('management.urls')),
    path('core/', include('core.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
