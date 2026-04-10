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
                address=form.cleaned_data['address'],
                district=form.cleaned_data['district'],
                university_affiliation=universities,
                theme_color=form.cleaned_data['theme_color'],
                registration_number=form.cleaned_data['registration_number'],
                website=form.cleaned_data['website'],
                verification_document=form.cleaned_data['verification_document'],
                status='PENDING'
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
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid credentials")
    return render(request, 'accounts/login.html')

def user_logout(request):
    logout(request)
    return redirect('login')