from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from .forms import CollegeRegistrationForm
from colleges.models import College
from .models import CustomUser

def register_college(request):
    if request.method == 'POST':
        form = CollegeRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            # 1. Create College
            universities = ", ".join(form.cleaned_data['university_affiliation'])
            college = College.objects.create(
                name=form.cleaned_data['college_name'],
                slug=form.cleaned_data['subdomain_alias'],
                address=form.cleaned_data['address'],
                district=form.cleaned_data['district'],
                university_affiliation=universities,
                theme_color=form.cleaned_data['theme_color'],
                registration_number=form.cleaned_data['registration_number'],
                website=form.cleaned_data['website'],
                verification_document=form.cleaned_data['verification_document'],
                status='PENDING',
                contact_email=form.cleaned_data['admin_email']
            )
            # 2. Create Admin User
            user = CustomUser.objects.create_user(
                email=form.cleaned_data['admin_email'],
                password=form.cleaned_data['admin_password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                role='COLLEGE_ADMIN',
                college=college
            )
            
            # 3. Send Registration Emails
            from django.core.mail import send_mail
            from django.conf import settings
            
            # To the College Admin
            try:
                send_mail(
                    subject="Registration Received - CollegeManager",
                    message=f"Hello {form.cleaned_data['first_name']},\n\nWe have received your registration for '{college.name}'. Your dedicated portal alias '{college.slug}' has been successfully reserved.\n\nOur platform administrators will review your verification documents and get back to you shortly.\n\nThank you for choosing CollegeManager!",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[form.cleaned_data['admin_email']],
                    fail_silently=True,
                )
            except Exception: pass
            
            # To Super Admins
            try:
                super_admins = CustomUser.objects.filter(role='SUPER_ADMIN').values_list('email', flat=True)
                if super_admins:
                    send_mail(
                        subject=f"New College Registration: {college.name}",
                        message=f"A new institution named '{college.name}' has just registered on the platform.\n\nDetails:\nRegistration Number: {college.registration_number}\nAlias: {college.slug}\nAdmin Email: {form.cleaned_data['admin_email']}\n\nPlease review the application on the admin dashboard.",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=list(super_admins),
                        fail_silently=True,
                    )
            except Exception: pass
            messages.success(request, f"Welcome! {college.name} registration successful. Please log in.")
            return redirect('login')
    else:
        form = CollegeRegistrationForm()
    return render(request, 'accounts/register_college.html', {'form': form})

# Standrd Login/Logout views can also be handled by Django's built-in views, 
# but we'll create simple ones for custom styling.

def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user:
            # Tenant Security Check
            if user.role == 'SUPER_ADMIN':
                # Super admins can log in from the main portal, bypassing college checks
                pass
            elif hasattr(request, 'college') and request.college:
                # If we are on a specific college's subdomain
                if user.college != request.college:
                    messages.error(request, "Access denied. You do not belong to this institution's portal.")
                    return redirect('login')
            else:
                if user.college and user.college.status == 'APPROVED':
                    login(request, user)
                    next_url = request.GET.get('next')
                    if next_url:
                        return redirect(f"{user.college.get_subdomain_url}{next_url}")
                    return redirect(f"{user.college.get_subdomain_url}/dashboard/")
                elif user.college:
                    pass # Allow them to see the pending page on the main domain
                    
            login(request, user)
            
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
                
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid credentials")
    return render(request, 'accounts/login.html')

def user_logout(request):
    logout(request)
    
    if getattr(request, 'urlconf', None) == 'collegevendor.tenant_urls':
        return redirect('tenant_home')
    return redirect('home')