from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth import views as auth_views
from django.contrib import messages
from .forms import CollegeRegistrationForm
from colleges.models import College
from .models import CustomUser

import random

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        user = CustomUser.objects.filter(email=email).first()
        if not user:
            messages.error(request, "No account registered with this email address.")
        else:
            otp = str(random.randint(100000, 999999))
            request.session['reset_email'] = email
            request.session['reset_otp'] = otp
            request.session['otp_verified'] = False
            
            # Print high-visibility OTP message to the terminal console
            print("\n" + "="*80)
            print(f" [PASSWORD RESET SERVICE] ".center(80, "="))
            print(f"To: {email}")
            print(f"Verification OTP Code: {otp}")
            print("="*80 + "\n")
            
            messages.info(request, "A verification OTP has been sent. Please check your Email.")

            return redirect('verify_otp')
    return render(request, 'accounts/password_reset_form.html')

def verify_otp(request):
    email = request.session.get('reset_email')
    if not email:
        messages.error(request, "Session expired or invalid. Please start over.")
        return redirect('password_reset')
        
    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '').strip()
        session_otp = request.session.get('reset_otp')
        if entered_otp == session_otp:
            request.session['otp_verified'] = True
            messages.success(request, "OTP verified successfully. Please set your new password.")
            return redirect('new_password')
        else:
            messages.error(request, "Invalid OTP code. Please check the terminal console and try again.")
            
    return render(request, 'accounts/verify_otp.html', {'email': email})

def new_password(request):
    email = request.session.get('reset_email')
    otp_verified = request.session.get('otp_verified')
    if not email or not otp_verified:
        messages.error(request, "Access denied. Please verify your identity first.")
        return redirect('password_reset')
        
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
        else:
            user = CustomUser.objects.get(email=email)
            user.set_password(password)
            user.save()
            
            # Clear session
            request.session.pop('reset_email', None)
            request.session.pop('reset_otp', None)
            request.session.pop('otp_verified', None)
            
            messages.success(request, "Your password has been reset successfully. Please log in.")
            return redirect('login')
            
    return render(request, 'accounts/new_password.html')


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