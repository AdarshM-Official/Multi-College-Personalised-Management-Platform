from colleges.models import College
from django.shortcuts import get_object_or_404

class CollegeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Logic to identify college
        # Option 1: From URL Slug (e.g. /mit/dashboard/)
        # Option 2: From Subdomain (e.g. mit.saas.com)
        # Option 3: From User profile (if logged in)
        
        request.college = None
        
        if request.user.is_authenticated:
            request.college = request.user.college
            
            # If college is not approved, block access except for the pending page
            # SUPER_ADMIN bypasses this check as they manage the platform
            if request.user.role == 'SUPER_ADMIN':
                pass
            elif request.college and request.college.status != 'APPROVED':
                # Allow access to logout and a landing 'pending' page
                allowed_paths = ['/pending-approval/', '/logout/', '/admin/']
                if not any(request.path.startswith(path) for path in allowed_paths):
                    from django.shortcuts import redirect
                    return redirect('pending_approval')

        response = self.get_response(request)
        return response
