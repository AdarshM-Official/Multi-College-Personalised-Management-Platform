from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from management.models import StudentProfile, TeacherProfile, Department, Attendance, PlatformNotification
from colleges.models import College
from accounts.models import CustomUser

def home(request):
    # Featured colleges for landing page
    featured = College.objects.filter(status='APPROVED')[:3]
    return render(request, 'home.html', {'featured_colleges': featured})

def college_directory(request):
    query = request.GET.get('q', '')
    colleges = College.objects.filter(status='APPROVED')
    if query:
        colleges = colleges.filter(models.Q(name__icontains=query) | models.Q(address__icontains=query))
    
    return render(request, 'core/public_directory.html', {'colleges': colleges, 'query': query})

def public_college_detail(request, slug):
    college = get_object_or_404(College, slug=slug, status='APPROVED')
    # Fetch academic structure
    departments = Department.objects.filter(college=college).prefetch_related('specializations')
    return render(request, 'core/public_college_detail.html', {
        'college': college,
        'departments': departments,
    })

@login_required
def dashboard(request):
    user = request.user
    if user.role == 'SUPER_ADMIN':
        return redirect('college_approval_queue')
        
    context = {}
    if user.role == 'COLLEGE_ADMIN':
        context['stats'] = {
            'students': StudentProfile.objects.filter(college=user.college).count(),
            'teachers': TeacherProfile.objects.filter(college=user.college).count(),
            'departments': Department.objects.filter(college=user.college).count(),
        }
        context['platform_notifications'] = PlatformNotification.objects.filter(
            models.Q(college=user.college) | models.Q(college__isnull=True)
        ).order_by('-created_at')[:5]
        return render(request, 'dashboards/admin_dashboard.html', context)
    
    elif user.role == 'TEACHER':
        profile = getattr(user, 'teacher_profile', None)
        context['stats'] = {'dept': profile.department.name if profile and profile.department else "None"}
        return render(request, 'dashboards/teacher_dashboard.html', context)
    
    elif user.role == 'STUDENT':
        profile = getattr(user, 'student_profile', None)
        context['stats'] = {'attendance': Attendance.objects.filter(student=profile).count() if profile else 0}
        return render(request, 'dashboards/student_dashboard.html', context)
    
    return render(request, 'dashboard.html', context)

def pending_approval(request):
    return render(request, 'accounts/pending_approval.html')

@staff_member_required
def college_approval_queue(request):
    """SaaS Manager Dashboard (Super Admin)."""
    if request.user.role != 'SUPER_ADMIN':
        return redirect('dashboard')
        
    context = {
        'pending_colleges': College.objects.filter(status='PENDING'),
        'all_colleges': College.objects.all(),
        'stats': {
            'total_colleges': College.objects.count(),
            'approved_colleges': College.objects.filter(status='APPROVED').count(),
            'total_users': CustomUser.objects.count(),
        }
    }
    return render(request, 'core/super_admin_dashboard.html', context)

@staff_member_required
def approve_college(request, college_id, action):
    college = get_object_or_404(College, id=college_id)
    if action == 'approve':
        college.status = 'APPROVED'
        messages.success(request, f"{college.name} has been approved.")
    elif action == 'reject':
        college.status = 'REJECTED'
        messages.warning(request, f"{college.name} has been rejected.")
    college.save()
    return redirect('college_approval_queue')

@staff_member_required
def delete_college(request, college_id):
    if request.user.role != 'SUPER_ADMIN': return redirect('dashboard')
    college = get_object_or_404(College, id=college_id)
    name = college.name
    college.delete()
    messages.error(request, f"Institution {name} removed.")
    return redirect('college_approval_queue')

@staff_member_required
def send_platform_notification(request):
    if request.user.role != 'SUPER_ADMIN': return redirect('dashboard')
    if request.method == 'POST':
        college_id = request.POST.get('college_id')
        title = request.POST.get('title')
        message = request.POST.get('message')
        college = College.objects.get(id=college_id) if college_id != 'ALL' else None
        PlatformNotification.objects.create(college=college, title=title, message=message)
        messages.success(request, "Broadcast sent.")
    return redirect('college_approval_queue')