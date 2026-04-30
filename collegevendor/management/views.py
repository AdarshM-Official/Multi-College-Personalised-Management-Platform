from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
import pandas as pd
from .models import StudentProfile, TeacherProfile, Department, Specialization, Assignment, Submission, Attendance, HODProfile, TimeTable, ExamNotification
from accounts.models import CustomUser
from .forms import StudentForm, StudentEditForm, TeacherForm, TeacherEditForm, AssignmentForm, DepartmentForm, SpecializationForm, CollegeSettingsForm, ExcelImportForm, HODForm, TimeTableForm, ExamNotificationForm, HODEditForm, UserEditForm
from colleges.models import College, CollegeImage, CollegeAchievement

@login_required
def college_settings(request):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('dashboard')
    college = request.college
    if request.method == 'POST':
        form = CollegeSettingsForm(request.POST, request.FILES, instance=college)
        if form.is_valid():
            college = form.save(commit=False)
            universities = form.cleaned_data.get('university_affiliation', [])
            college.university_affiliation = ", ".join(universities)
            college.save()
            
            ach_title = request.POST.get('achievement_title')
            if ach_title:
                CollegeAchievement.objects.create(
                    college=college,
                    title=ach_title,
                    description=request.POST.get('achievement_description', ''),
                    date=request.POST.get('achievement_date') or None
                )
            
            gallery_images = request.FILES.getlist('gallery_images')
            for img in gallery_images:
                CollegeImage.objects.create(college=college, image=img)
            
            messages.success(request, "Institutional profile and gallery updated.")
            return redirect('college_settings')
    else:
        form = CollegeSettingsForm(instance=college)
    return render(request, 'management/college_settings.html', {'form': form, 'college': college})

@login_required
def delete_gallery_image(request, image_id):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('dashboard')
    image = get_object_or_404(CollegeImage, id=image_id, college=request.college)
    image.delete()
    messages.warning(request, "Gallery image removed.")
    return redirect('college_settings')

@login_required
def student_list(request):
    students = StudentProfile.objects.filter(college=request.college)
    specializations = None
    if request.user.role == 'HOD':
        dept = request.user.hod_profile.department
        students = students.filter(department=dept)
        specializations = Specialization.objects.filter(department=dept)
    
    # Optional: Filter by specialization if provided in GET
    spec_id = request.GET.get('specialization')
    if spec_id:
        students = students.filter(specialization_id=spec_id)
        
    return render(request, 'management/student_list.html', {
        'students': students,
        'specializations': specializations,
        'selected_spec': spec_id
    })

@login_required
def add_student(request):
    if request.user.role not in ['COLLEGE_ADMIN', 'HOD', 'SUPER_ADMIN']: 
        messages.error(request, "Permission Denied.")
        return redirect('student_list')
    
    spec_id = request.GET.get('specialization')
    
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, college=request.college, user_role=request.user.role, user_dept=getattr(request.user, 'hod_profile', None).department if request.user.role == 'HOD' else None)
        if form.is_valid():
            user = CustomUser.objects.create_user(
                email=form.cleaned_data['email'], password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'], last_name=form.cleaned_data['last_name'],
                role='STUDENT', college=request.college
            )
            StudentProfile.objects.create(
                user=user, college=request.college,
                profile_photo=form.cleaned_data.get('profile_photo'),
                university_reg_number=form.cleaned_data.get('university_reg_number'),
                roll_number=form.cleaned_data['roll_number'],
                phone_number=form.cleaned_data.get('phone_number'),
                father_name=form.cleaned_data.get('father_name'),
                mother_name=form.cleaned_data.get('mother_name'),
                address=form.cleaned_data.get('address'),
                date_of_birth=form.cleaned_data.get('date_of_birth'),
                ug_marklist=form.cleaned_data.get('ug_marklist'),
                plus_two_marklist=form.cleaned_data.get('plus_two_marklist'),
                last_passout_year=form.cleaned_data.get('last_passout_year'),
                department=form.cleaned_data['department'], 
                specialization=form.cleaned_data['specialization']
            )
            messages.success(request, f"Student {user.get_full_name()} added successfully.")
            return redirect('student_list')
    else:
        initial = {}
        if spec_id:
            initial['specialization'] = spec_id
            spec = Specialization.objects.filter(id=spec_id).first()
            if spec: initial['department'] = spec.department
            
        form = StudentForm(
            college=request.college, 
            user_role=request.user.role, 
            user_dept=getattr(request.user, 'hod_profile', None).department if request.user.role == 'HOD' else None,
            initial=initial
        )
    return render(request, 'management/add_student.html', {'form': form})

@login_required
def student_detail(request, student_id):
    student = get_object_or_404(StudentProfile, id=student_id, college=request.college)
    if request.user.role == 'HOD' and student.department != request.user.hod_profile.department:
        return redirect('student_list')
    return render(request, 'management/student_detail.html', {'student': student})

@login_required
def edit_student(request, student_id):
    student = get_object_or_404(StudentProfile, id=student_id, college=request.college)
    if request.user.role == 'HOD' and student.department != request.user.hod_profile.department:
        return redirect('student_list')
    
    if request.method == 'POST':
        form = StudentEditForm(request.POST, request.FILES, college=request.college, user_role=request.user.role, user_dept=getattr(request.user, 'hod_profile', None).department if request.user.role == 'HOD' else None)
        if form.is_valid():
            user = student.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            if form.cleaned_data.get('password'):
                user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Update profile fields
            if form.cleaned_data.get('profile_photo'):
                student.profile_photo = form.cleaned_data['profile_photo']
            
            student.university_reg_number = form.cleaned_data.get('university_reg_number')
            student.roll_number = form.cleaned_data['roll_number']
            student.phone_number = form.cleaned_data.get('phone_number')
            student.father_name = form.cleaned_data.get('father_name')
            student.mother_name = form.cleaned_data.get('mother_name')
            student.address = form.cleaned_data.get('address')
            student.last_passout_year = form.cleaned_data.get('last_passout_year')
            student.department = form.cleaned_data['department']
            student.specialization = form.cleaned_data['specialization']
            student.save()
            
            messages.success(request, "Student record updated.")
            return redirect('student_list')
    else:
        initial = {
            'first_name': student.user.first_name,
            'last_name': student.user.last_name,
            'email': student.user.email,
            'university_reg_number': student.university_reg_number,
            'roll_number': student.roll_number,
            'phone_number': student.phone_number,
            'father_name': student.father_name,
            'mother_name': student.mother_name,
            'address': student.address,
            'last_passout_year': student.last_passout_year,
            'department': student.department,
            'specialization': student.specialization,
        }
        form = StudentEditForm(college=request.college, user_role=request.user.role, user_dept=getattr(request.user, 'hod_profile', None).department if request.user.role == 'HOD' else None, initial=initial)
    
    return render(request, 'management/add_student.html', {'form': form, 'student': student, 'is_edit': True})

@login_required
def delete_student(request, student_id):
    student = get_object_or_404(StudentProfile, id=student_id, college=request.college)
    if request.user.role == 'HOD' and student.department != request.user.hod_profile.department:
        return redirect('student_list')
    
    user = student.user
    student.delete()
    user.delete()
    messages.warning(request, "Student record deleted.")
    return redirect('student_list')

@login_required
def teacher_list(request):
    departments = Department.objects.filter(college=request.college).prefetch_related('specializations')
    if request.user.role == 'HOD':
        departments = departments.filter(id=request.user.hod_profile.department.id)
    
    hierarchy = []
    for dept in departments:
        specs_list = []
        for spec in dept.specializations.all():
            teachers = TeacherProfile.objects.filter(specialization=spec)
            if teachers.exists():
                specs_list.append({'spec': spec, 'teachers': teachers})
        
        unassigned_teachers = TeacherProfile.objects.filter(department=dept, specialization__isnull=True)
        if unassigned_teachers.exists():
            specs_list.append({'spec': None, 'teachers': unassigned_teachers})
            
        if specs_list:
            hierarchy.append({'dept': dept, 'specs': specs_list})

    return render(request, 'management/teacher_list.html', {
        'hierarchy': hierarchy, 
        'total_count': TeacherProfile.objects.filter(department__in=departments).count()
    })

@login_required
def add_teacher(request):
    if request.user.role not in ['COLLEGE_ADMIN', 'HOD']: return redirect('teacher_list')
    if request.method == 'POST':
        form = TeacherForm(request.POST, college=request.college)
        if form.is_valid():
            user = CustomUser.objects.create_user(
                email=form.cleaned_data['email'], password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'], last_name=form.cleaned_data['last_name'],
                role='TEACHER', college=request.college
            )
            TeacherProfile.objects.create(
                user=user, college=request.college,
                qualification=form.cleaned_data['qualification'],
                phone_number=form.cleaned_data['phone_number'],
                department=form.cleaned_data['department'],
                specialization=form.cleaned_data['specialization']
            )
            messages.success(request, "Teacher added.")
            return redirect('teacher_list')
    else:
        initial = {}
        if request.user.role == 'HOD': initial['department'] = request.user.hod_profile.department
        form = TeacherForm(college=request.college, initial=initial)
    return render(request, 'management/add_teacher.html', {'form': form})

@login_required
def teacher_detail(request, teacher_id):
    teacher = get_object_or_404(TeacherProfile, id=teacher_id, college=request.college)
    return render(request, 'management/teacher_detail.html', {'teacher': teacher})

@login_required
def edit_teacher(request, teacher_id):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('teacher_list')
    teacher = get_object_or_404(TeacherProfile, id=teacher_id, college=request.college)
    if request.method == 'POST':
        form = TeacherEditForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            user = teacher.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.save()
            form.save()
            messages.success(request, "Teacher profile updated.")
            return redirect('teacher_list')
    else:
        form = TeacherEditForm(instance=teacher)
    return render(request, 'management/edit_teacher.html', {'form': form, 'teacher': teacher})

@login_required
def delete_teacher(request, teacher_id):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('teacher_list')
    teacher = get_object_or_404(TeacherProfile, id=teacher_id, college=request.college)
    user = teacher.user
    teacher.delete(); user.delete()
    messages.warning(request, "Teacher record and account removed.")
    return redirect('teacher_list')

@login_required
def department_list(request):
    if request.user.role not in ['COLLEGE_ADMIN', 'HOD']: return redirect('dashboard')
    
    departments = Department.objects.filter(college=request.college).prefetch_related('specializations')
    
    # If HOD, they can see all depts in directory, but template handles specific actions
    return render(request, 'management/department_list.html', {
        'ug_departments': departments.filter(category='UG'),
        'pg_departments': departments.filter(category='PG'),
    })

@login_required
def add_department(request):
    if request.user.role not in ['COLLEGE_ADMIN', 'HOD']: return redirect('dashboard')
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            if name == 'Other': name = form.cleaned_data['custom_name']
            dept = form.save(commit=False); dept.college = request.college; dept.name = name; dept.save()
            specs_text = form.cleaned_data.get('specializations_list')
            if specs_text:
                for s_name in [s.strip() for s in specs_text.split(',') if s.strip()]:
                    Specialization.objects.create(department=dept, name=s_name, college=request.college)
            messages.success(request, f"Department '{name}' created."); return redirect('department_list')
    else: form = DepartmentForm()
    return render(request, 'management/add_department.html', {'form': form, 'title': 'Add New Department'})

@login_required
def edit_department(request, dept_id):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('dashboard')
    dept = get_object_or_404(Department, id=dept_id, college=request.college)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            name = form.cleaned_data['name']
            if name == 'Other': name = form.cleaned_data['custom_name']
            dept = form.save(commit=False); dept.name = name; dept.save()
            messages.success(request, "Department updated."); return redirect('department_list')
    else:
        form = DepartmentForm(instance=dept)
        if dept.name not in [c[0] for c in DepartmentForm.DEGREE_CHOICES]:
            form.initial['name'] = 'Other'; form.initial['custom_name'] = dept.name
    return render(request, 'management/add_department.html', {'form': form, 'title': 'Edit Department'})

@login_required
def delete_department(request, dept_id):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('dashboard')
    dept = get_object_or_404(Department, id=dept_id, college=request.college)
    dept.delete(); messages.warning(request, "Department removed."); return redirect('department_list')

@login_required
def import_departments_excel(request):
    if request.user.role not in ['COLLEGE_ADMIN', 'HOD']: return redirect('dashboard')
    if request.method == 'POST':
        form = ExcelImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                df = pd.read_excel(request.FILES['excel_file'])
                created_count = 0
                for _, row in df.iterrows():
                    dept_name = row.get('Department Name')
                    category = row.get('Category', 'UG')
                    if dept_name:
                        dept, created = Department.objects.get_or_create(college=request.college, name=dept_name, defaults={'category': category})
                        if created: created_count += 1
                        specs = row.get('Specializations')
                        if pd.notna(specs):
                            for s_name in [s.strip() for s in str(specs).split(',')]:
                                Specialization.objects.get_or_create(department=dept, name=s_name, college=request.college)
                messages.success(request, f"Successfully imported {created_count} new departments.")
            except Exception as e: messages.error(request, f"Error processing file: {str(e)}")
            return redirect('department_list')
    return redirect('department_list')

@login_required
def download_department_template(request):
    df = pd.DataFrame(columns=['Department Name', 'Category', 'Specializations'])
    df.loc[0] = ['BSc Computer Science', 'UG', 'Data Science, AI, Networking']
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=department_import_template.xlsx'
    df.to_excel(response, index=False); return response

@login_required
def import_teachers_excel(request):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('dashboard')
    if request.method == 'POST':
        form = ExcelImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                df = pd.read_excel(request.FILES['excel_file'])
                for _, row in df.iterrows():
                    email = row.get('Email'); dept_name = row.get('Department')
                    if email and dept_name:
                        dept = Department.objects.filter(college=request.college, name=dept_name).first()
                        if dept:
                            user, created = CustomUser.objects.get_or_create(
                                email=email, college=request.college,
                                defaults={'first_name': row.get('First Name', ''), 'last_name': row.get('Last Name', ''), 'role': 'TEACHER'}
                            )
                            if created: user.set_password('teacher123'); user.save()
                            spec = Specialization.objects.filter(department=dept, name=row.get('Specialization')).first()
                            TeacherProfile.objects.update_or_create(user=user, college=request.college, defaults={'department': dept, 'specialization': spec, 'qualification': row.get('Qualification', 'NA')})
                messages.success(request, "Faculty import completed.")
            except Exception as e: messages.error(request, f"Error: {str(e)}")
            return redirect('teacher_list')
    return redirect('teacher_list')

@login_required
def download_teacher_template(request):
    df = pd.DataFrame(columns=['First Name', 'Last Name', 'Email', 'Department', 'Specialization', 'Qualification'])
    df.loc[0] = ['John', 'Doe', 'john@example.com', 'BSc Computer Science', 'Data Science', 'PhD CS']
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=teacher_import_template.xlsx'
    df.to_excel(response, index=False); return response

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
    if request.user.role not in ['TEACHER', 'HOD']: return redirect('dashboard')
    students = StudentProfile.objects.filter(college=request.college)
    if request.user.role == 'HOD':
        students = students.filter(department=request.user.hod_profile.department)
    
    if request.method == 'POST':
        date = request.POST.get('date')
        for student in students:
            status = request.POST.get(f'status_{student.id}')
            Attendance.objects.update_or_create(
                student=student, date=date, college=request.college,
                defaults={'status': status, 'marked_by': request.user}
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

@login_required
def add_hod(request):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('dashboard')
    dept_id = request.GET.get('department')
    if request.method == 'POST':
        form = HODForm(request.POST, request.FILES, college=request.college)
        if form.is_valid():
            user = CustomUser.objects.create_user(
                email=form.cleaned_data['email'], password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'], last_name=form.cleaned_data['last_name'],
                role='HOD', college=request.college
            )
            HODProfile.objects.create(
                user=user, college=request.college,
                department=form.cleaned_data['department'],
                profile_photo=form.cleaned_data.get('profile_photo'),
                phone_number=form.cleaned_data.get('phone_number', '')
            )
            TeacherProfile.objects.create(
                user=user, college=request.college,
                department=form.cleaned_data['department'],
                phone_number=form.cleaned_data.get('phone_number', ''),
                profile_photo=form.cleaned_data.get('profile_photo'),
                qualification="Head of Department"
            )
            messages.success(request, f"HOD {user.get_full_name()} added and enrolled as Faculty.")
            return redirect('hod_list')
    else:
        initial = {}
        if dept_id: initial['department'] = dept_id
        form = HODForm(college=request.college, initial=initial)
    return render(request, 'management/add_hod.html', {'form': form})

@login_required
def hod_list(request):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('dashboard')
    departments = Department.objects.filter(college=request.college).prefetch_related('hod_profile__user')
    return render(request, 'management/hod_list.html', {'departments': departments})

@login_required
def create_timetable(request):
    if request.user.role != 'HOD': return redirect('dashboard')
    if request.method == 'POST':
        form = TimeTableForm(request.POST, request.FILES)
        if form.is_valid():
            tt = form.save(commit=False); tt.college = request.college
            tt.department = request.user.hod_profile.department
            tt.uploaded_by = request.user.hod_profile; tt.save()
            messages.success(request, "Time table created."); return redirect('dashboard')
    else: form = TimeTableForm()
    return render(request, 'management/create_timetable.html', {'form': form, 'title': 'Upload Timetable'})

@login_required
def edit_timetable(request, tt_id):
    if request.user.role != 'HOD': return redirect('dashboard')
    tt = get_object_or_404(TimeTable, id=tt_id, department=request.user.hod_profile.department)
    if request.method == 'POST':
        form = TimeTableForm(request.POST, request.FILES, instance=tt)
        if form.is_valid():
            form.save(); messages.success(request, "Timetable updated."); return redirect('dashboard')
    else: form = TimeTableForm(instance=tt)
    return render(request, 'management/create_timetable.html', {'form': form, 'title': 'Edit Timetable'})

@login_required
def delete_timetable(request, tt_id):
    if request.user.role != 'HOD': return redirect('dashboard')
    tt = get_object_or_404(TimeTable, id=tt_id, department=request.user.hod_profile.department)
    tt.delete(); messages.warning(request, "Timetable deleted."); return redirect('dashboard')

@login_required
def create_exam_notification(request):
    if request.user.role != 'HOD': return redirect('dashboard')
    if request.method == 'POST':
        form = ExamNotificationForm(request.POST)
        if form.is_valid():
            en = form.save(commit=False); en.college = request.college
            en.department = request.user.hod_profile.department
            en.posted_by = request.user.hod_profile; en.save()
            messages.success(request, "Exam notification created."); return redirect('dashboard')
    else: form = ExamNotificationForm()
    return render(request, 'management/create_exam_notification.html', {'form': form})

@login_required
def edit_profile(request):
    user = request.user
    form_class = None
    instance = None
    
    if user.role == 'HOD':
        form_class = HODEditForm
        instance = getattr(user, 'hod_profile', None)
    elif user.role == 'TEACHER':
        form_class = TeacherEditForm
        instance = getattr(user, 'teacher_profile', None)
    elif user.role == 'STUDENT':
        form_class = StudentEditForm
        instance = getattr(user, 'student_profile', None)
    else:
        # College Admin or Super Admin
        form_class = UserEditForm
        instance = user

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            # Sync CustomUser fields if the form has them
            new_email = form.cleaned_data.get('email')
            if new_email and new_email != user.email:
                if CustomUser.objects.filter(email=new_email).exclude(id=user.id).exists():
                    messages.error(request, "This email is already in use.")
                    return render(request, 'management/edit_profile.html', {'form': form})
                user.email = new_email
                
            user.first_name = form.cleaned_data.get('first_name', user.first_name)
            user.last_name = form.cleaned_data.get('last_name', user.last_name)
            user.save()
            
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('dashboard')
    else:
        form = form_class(instance=instance)
            
    return render(request, 'management/edit_profile.html', {
        'form': form,
        'profile': instance if user.role in ['HOD', 'TEACHER', 'STUDENT'] else None
    })

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'management/change_password.html', {
        'form': form
    })
