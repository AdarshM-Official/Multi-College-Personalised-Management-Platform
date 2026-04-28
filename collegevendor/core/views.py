from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from management.models import StudentProfile, TeacherProfile, Department, Attendance, PlatformNotification, TimeTable, ExamNotification
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

def tenant_home(request):
    """Branded homepage for a specific college (via subdomain)."""
    if not request.college:
        return redirect('home')
    
    college = request.college
    departments = Department.objects.filter(college=college).prefetch_related('specializations')
    
    return render(request, 'core/tenant_home.html', {
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
    
    elif user.role == 'HOD':
        profile = getattr(user, 'hod_profile', None)
        context['stats'] = {'dept': profile.department.name if profile and profile.department else "None"}
        if profile and profile.department:
            context['timetables'] = TimeTable.objects.filter(department=profile.department)
            context['exam_notifications'] = ExamNotification.objects.filter(department=profile.department).order_by('-id')[:5]
            context['teachers_list'] = TeacherProfile.objects.filter(department=profile.department)[:5]
        else:
            context['stats'] = {'dept': "None", 'teachers': 0, 'students': 0, 'subjects': 0}
            context['teachers_list'] = []
        return render(request, 'dashboards/hod_dashboard.html', context)
    
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
def college_detail_admin(request, college_id):
    """View full profile of a registration request."""
    if request.user.role != 'SUPER_ADMIN': return redirect('dashboard')
    college = get_object_or_404(College, id=college_id)
    return render(request, 'core/admin_college_detail.html', {'college': college})

@staff_member_required
def approve_college(request, college_id, action):
    from django.core.mail import send_mail
    from django.conf import settings
    
    college = get_object_or_404(College, id=college_id)
    admin_email = college.contact_email # Assuming contact_email is the one to notify
    
    if action == 'approve':
        college.status = 'APPROVED'
        college.rejection_reason = None
        college.save()
        
        # Send Approval Email
        try:
            send_mail(
                subject=f"Institution Approved: {college.name}",
                message=f"Congratulations! Your institution '{college.name}' has been approved on the CollegeManager platform.\n\nYou can now access your branded portal at: {college.get_subdomain_url}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin_email],
                fail_silently=True,
            )
        except Exception: pass
        
        messages.success(request, f"{college.name} has been approved.")
        
    elif action == 'reject':
        if request.method == 'POST':
            reason_category = request.POST.get('reason_category')
            custom_details = request.POST.get('rejection_details')
            full_reason = f"{reason_category}: {custom_details}" if custom_details else reason_category
            
            college.status = 'REJECTED'
            college.rejection_reason = full_reason
            college.save()
            
            # Send Rejection Email
            try:
                send_mail(
                    subject=f"Registration Update: {college.name}",
                    message=f"We regret to inform you that the registration for '{college.name}' was not approved at this time.\n\nReason: {full_reason}\n\nPlease address the issues and contact support if needed.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin_email],
                    fail_silently=True,
                )
            except Exception: pass
            
            messages.warning(request, f"{college.name} has been rejected.")
        else:
            return redirect('college_approval_queue')
            
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

@staff_member_required
def test_email(request):
    if request.user.role != 'SUPER_ADMIN': return redirect('dashboard')
    
    from django.core.mail import send_mail
    from django.conf import settings
    
    try:
        sent = send_mail(
            subject="Test System Notification",
            message="This is a test email generated from the CollegeManager Super Admin dashboard. If you are reading this, the email configuration is fully functional.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
            fail_silently=False,
        )
        if sent:
            messages.success(request, f"Test email successfully dispatched to {request.user.email}!")
        else:
            messages.warning(request, "Email send command executed, but no emails were delivered.")
    except Exception as e:
        messages.error(request, f"Email delivery failed: {str(e)}")
        
    return redirect('college_approval_queue')


