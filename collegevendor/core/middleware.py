from colleges.models import College
from django.shortcuts import get_object_or_404, redirect

class CollegeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0]
        
        request.college = None
        
        # Check if doing wildcard subdomain
        parts = host.split('.')
        # E.g. 'chmm.localhost' -> parts = ['chmm', 'localhost']
        if len(parts) >= 2 and parts[0] != 'www' and parts[0] != 'localhost':
            subdomain = parts[0]
            try:
                # Try finding the college
                college = College.objects.get(slug=subdomain)
                request.college = college
                
                # If they are pending or rejected, unless they are at /pending_approval or /login, redirect
                if college.status != 'APPROVED':
                    allowed_paths = ['/pending_approval/', '/logout/', '/admin/']
                    # We might need to handle this more deeply, but for now we let it pass because we rely on the views to deny access to unapproved users.
                
                # Switch to Tenant URLs scope safely for this request only
                request.urlconf = 'collegevendor.tenant_urls'
            except College.DoesNotExist:
                pass
        
        # Original fallback logic for logged in users on main domain
        if request.user.is_authenticated and not request.college:
            if hasattr(request.user, 'college') and request.user.college:
                request.college = request.user.college
                if request.user.role != 'SUPER_ADMIN' and request.college.status != 'APPROVED':
                    allowed_paths = ['/pending-approval/', '/logout/', '/admin/']
                    if not any(request.path.startswith(path) for path in allowed_paths):
                        return redirect('pending_approval')

        response = self.get_response(request)
        return response
