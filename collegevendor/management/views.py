from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import StudentProfile, TeacherProfile, Department, Specialization, Assignment, Submission, Attendance
from accounts.models import CustomUser
from .forms import StudentForm, TeacherForm, TeacherEditForm, AssignmentForm, DepartmentForm, SpecializationForm, CollegeSettingsForm
from colleges.models import College, CollegeImage, CollegeAchievement

@login_required
def college_settings(request):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('dashboard')
    college = request.college
    if request.method == 'POST':
        form = CollegeSettingsForm(request.POST, request.FILES, instance=college)
        if form.is_valid():
            college = form.save(commit=False)
            # Handle university affiliation list -> string
            universities = form.cleaned_data.get('university_affiliation', [])
            college.university_affiliation = ", ".join(universities)
            college.save()
            
            # Handle Achievement addition
            ach_title = request.POST.get('achievement_title')
            if ach_title:
                CollegeAchievement.objects.create(
                    college=college,
                    title=ach_title,
                    description=request.POST.get('achievement_description', ''),
                    date=request.POST.get('achievement_date') or None
                )
            
            # Handle Gallery Images
            gallery_images = request.FILES.getlist('gallery_images')
            for img in gallery_images:
                CollegeImage.objects.create(college=college, image=img)
            
            messages.success(request, "Institutional profile and gallery updated.")
            return redirect('college_settings')
    else:
        form = CollegeSettingsForm(instance=college)
    return render(request, 'management/college_settings.html', {'form': form, 'college': college})

@login_required
def student_list(request):
    students = StudentProfile.objects.filter(college=request.college)
    return render(request, 'management/student_list.html', {'students': students})

@login_required
def add_student(request):
    # Admission management is restricted from College Admin per current policy
    if request.user.role != 'SUPER_ADMIN': 
        messages.error(request, "Permission Denied: Student onboarding is managed by platform administration.")
        return redirect('student_list')
    if request.method == 'POST':
        form = StudentForm(request.POST, college=request.college)
        if form.is_valid():
            user = CustomUser.objects.create_user(
                email=form.cleaned_data['email'], password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'], last_name=form.cleaned_data['last_name'],
                role='STUDENT', college=request.college
            )
            StudentProfile.objects.create(
                user=user, college=request.college, roll_number=form.cleaned_data['roll_number'],
                department=form.cleaned_data['department'], specialization=form.cleaned_data['specialization']
            )
            messages.success(request, "Student added.")
            return redirect('student_list')
    else:
        form = StudentForm(college=request.college)
    return render(request, 'management/add_student.html', {'form': form})

@login_required
def teacher_list(request):
    # Hierarchical grouping: Departments -> Specializations -> Teachers
    # We fetch all departments for the college
    departments = Department.objects.filter(college=request.college).prefetch_related('specializations')
    
    # We'll build a structure: {dept: {spec: [teachers]}}
    hierarchy = []
    for dept in departments:
        specs_list = []
        for spec in dept.specializations.all():
            teachers = TeacherProfile.objects.filter(specialization=spec)
            if teachers.exists():
                specs_list.append({'spec': spec, 'teachers': teachers})
        
        # Also catch teachers assigned to dept but NO spec
        unassigned_teachers = TeacherProfile.objects.filter(department=dept, specialization__isnull=True)
        if unassigned_teachers.exists():
            specs_list.append({'spec': None, 'teachers': unassigned_teachers})
            
        if specs_list:
            hierarchy.append({'dept': dept, 'specs': specs_list})

    return render(request, 'management/teacher_list.html', {'hierarchy': hierarchy, 'total_count': TeacherProfile.objects.filter(college=request.college).count()})

@login_required
def add_teacher(request):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('dashboard')
    if request.method == 'POST':
        form = TeacherForm(request.POST, request.FILES, college=request.college)
        if form.is_valid():
            user = CustomUser.objects.create_user(
                email=form.cleaned_data['email'], password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'], last_name=form.cleaned_data['last_name'],
                role='TEACHER', college=request.college
            )
            TeacherProfile.objects.create(
                user=user, college=request.college, 
                department=form.cleaned_data['department'], 
                specialization=form.cleaned_data['specialization'],
                qualification=form.cleaned_data['qualification'],
                profile_photo=form.cleaned_data.get('profile_photo'),
                phone_number=form.cleaned_data.get('phone_number', ''),
                address=form.cleaned_data.get('address', '')
            )
            messages.success(request, f"Teacher {user.get_full_name()} added.")
            return redirect('teacher_list')
    else:
        form = TeacherForm(college=request.college)
    return render(request, 'management/add_teacher.html', {'form': form})

@login_required
def teacher_detail(request, teacher_id):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('dashboard')
    teacher = get_object_or_404(TeacherProfile, id=teacher_id, college=request.college)
    return render(request, 'management/teacher_detail.html', {'teacher': teacher})

@login_required
def edit_teacher(request, teacher_id):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('dashboard')
    teacher = get_object_or_404(TeacherProfile, id=teacher_id, college=request.college)
    if request.method == 'POST':
        form = TeacherEditForm(request.POST, request.FILES, college=request.college)
        if form.is_valid():
            user = teacher.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            
            teacher.department = form.cleaned_data['department']
            teacher.specialization = form.cleaned_data['specialization']
            teacher.qualification = form.cleaned_data['qualification']
            teacher.phone_number = form.cleaned_data.get('phone_number', '')
            teacher.address = form.cleaned_data.get('address', '')
            if form.cleaned_data.get('profile_photo'):
                teacher.profile_photo = form.cleaned_data['profile_photo']
            teacher.save()
            
            messages.success(request, f"Profile for {user.get_full_name()} updated.")
            return redirect('teacher_list')
    else:
        initial = {
            'first_name': teacher.user.first_name,
            'last_name': teacher.user.last_name,
            'email': teacher.user.email,
            'department': teacher.department,
            'specialization': teacher.specialization,
            'qualification': teacher.qualification,
            'phone_number': teacher.phone_number,
            'address': teacher.address,
        }
        form = TeacherEditForm(initial=initial, college=request.college)
    return render(request, 'management/add_teacher.html', {'form': form, 'title': 'Edit Faculty Profile'})

@login_required
def delete_teacher(request, teacher_id):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('dashboard')
    teacher = get_object_or_404(TeacherProfile, id=teacher_id, college=request.college)
    user = teacher.user
    name = user.get_full_name()
    user.delete() # Also deletes profile due to Cascade
    messages.warning(request, f"Faculty account for {name} has been removed.")
    return redirect('teacher_list')

@login_required
def department_list(request):
    depts = Department.objects.filter(college=request.college)
    context = {
        'departments': depts,
        'ug_departments': depts.filter(category='UG'),
        'pg_departments': depts.filter(category='PG'),
    }
    return render(request, 'management/department_list.html', context)

@login_required
def add_department(request):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('dashboard')
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            dept = form.save(commit=False)
            dept.college = request.college
            
            # Handle "Other" custom degree type
            if form.cleaned_data['name'] == 'Other':
                dept.name = form.cleaned_data['custom_name']
            else:
                dept.name = form.cleaned_data['name']
                
            dept.save()
            
            # Bulk Create Specializations
            specs_raw = form.cleaned_data.get('specializations_list', '')
            if specs_raw:
                specs = [s.strip() for s in specs_raw.split(',') if s.strip()]
                for s_name in specs:
                    Specialization.objects.create(
                        department=dept,
                        name=s_name,
                        college=request.college
                    )
            
            messages.success(request, f"Department '{dept.name}' created with {len(specs) if specs_raw else 0} courses.")
            return redirect('department_list')
    else: form = DepartmentForm()
    return render(request, 'management/add_department.html', {'form': form, 'title': 'Create New Department'})

@login_required
def edit_department(request, dept_id):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('dashboard')
    dept = get_object_or_404(Department, id=dept_id, college=request.college)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            form.save(); messages.success(request, "Department updated."); return redirect('department_list')
    else: form = DepartmentForm(instance=dept)
    return render(request, 'management/add_department.html', {'form': form, 'title': 'Edit Department'})

@login_required
def delete_department(request, dept_id):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('dashboard')
    dept = get_object_or_404(Department, id=dept_id, college=request.college)
    dept.delete(); messages.warning(request, "Department removed."); return redirect('department_list')

@login_required
def add_specialization(request):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('dashboard')
    if request.method == 'POST':
        form = SpecializationForm(request.POST, college=request.college)
        if form.is_valid():
            spec = form.save(commit=False); spec.college = request.college; spec.save()
            messages.success(request, "Specialization added."); return redirect('department_list')
    else: form = SpecializationForm(college=request.college)
    return render(request, 'management/add_department.html', {'form': form, 'title': 'Add Specialization/Course'})

@login_required
def edit_specialization(request, spec_id):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('dashboard')
    spec = get_object_or_404(Specialization, id=spec_id, college=request.college)
    if request.method == 'POST':
        form = SpecializationForm(request.POST, instance=spec, college=request.college)
        if form.is_valid():
            form.save(); messages.success(request, "Specialization updated."); return redirect('department_list')
    else: form = SpecializationForm(instance=spec, college=request.college)
    return render(request, 'management/add_department.html', {'form': form, 'title': 'Edit Specialization'})

@login_required
def delete_specialization(request, spec_id):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('dashboard')
    spec = get_object_or_404(Specialization, id=spec_id, college=request.college)
    spec.delete(); messages.warning(request, "Specialization removed."); return redirect('department_list')

@login_required
def assignment_list(request):
    assignments = Assignment.objects.filter(college=request.college)
    if request.user.role == 'TEACHER': assignments = assignments.filter(teacher=request.user.teacher_profile)
    return render(request, 'management/assignment_list.html', {'assignments': assignments})

@login_required
def create_assignment(request):
    if request.user.role != 'TEACHER': return redirect('dashboard')
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False); assignment.college = request.college
            assignment.teacher = request.user.teacher_profile; assignment.save()
            messages.success(request, "Assignment created."); return redirect('assignment_list')
    else: form = AssignmentForm()
    return render(request, 'management/create_assignment.html', {'form': form})

@login_required
def mark_attendance(request):
    if request.user.role != 'TEACHER': return redirect('dashboard')
    students = StudentProfile.objects.filter(college=request.college)
    if request.method == 'POST':
        date = request.POST.get('date')
        for student in students:
            status = request.POST.get(f'status_{student.id}')
            Attendance.objects.update_or_create(
                student=student, date=date, college=request.college,
                defaults={'status': status, 'marked_by': request.user.teacher_profile}
            )
        messages.success(request, "Attendance marked."); return redirect('dashboard')
    return render(request, 'management/mark_attendance.html', {'students': students})

@login_required
def generate_sample_data(request):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('dashboard')
    college = request.college
    depts = ["Computer Science", "Engineering", "Science"]
    for d_name in depts:
        Department.objects.get_or_create(name=d_name, college=college)
    messages.success(request, "Sample Data setup completed.")
    return redirect('department_list')
