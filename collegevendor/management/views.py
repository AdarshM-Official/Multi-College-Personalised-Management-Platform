from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
import pandas as pd
from .models import StudentProfile, TeacherProfile, Department, Specialization, Assignment, Submission, Attendance, HODProfile, TimeTable, ExamNotification, AcademicClass, InternalMarkCategory, InternalMark, TimeTablePeriod, Subject, DepartmentEvent, CollegeEnquiry
from accounts.models import CustomUser
from .forms import StudentForm, StudentEditForm, TeacherForm, TeacherEditForm, AssignmentForm, DepartmentForm, SpecializationForm, CollegeSettingsForm, ExcelImportForm, HODForm, TimeTableForm, ExamNotificationForm, HODEditForm, UserEditForm, AcademicClassForm, InternalMarkCategoryForm, SubjectForm, DepartmentEventForm
from colleges.models import College, CollegeImage, CollegeAchievement, CollegeLeader

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
            
            image_category = request.POST.get('image_category', 'OTHER')
            gallery_images = request.FILES.getlist('gallery_images[]')
            if not gallery_images:
                gallery_images = request.FILES.getlist('gallery_images')
            for img in gallery_images:
                CollegeImage.objects.create(college=college, image=img, category=image_category)
            
            leader_name = request.POST.get('leader_name')
            if leader_name:
                CollegeLeader.objects.create(
                    college=college,
                    name=leader_name,
                    designation=request.POST.get('leader_designation', ''),
                    bio=request.POST.get('leader_bio', ''),
                    image=request.FILES.get('leader_image')
                )
            
            if request.POST.get('action') == 'add_leader':
                if leader_name:
                    messages.success(request, "Leadership profile added successfully.")
                else:
                    messages.error(request, "Leader name is required.")
                return redirect(request.path + '#leadership')
                
            if request.POST.get('action') == 'upload_gallery':
                messages.success(request, "Gallery images uploaded successfully.")
                return redirect(request.path + '#gallery')
                
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
def delete_college_leader(request, leader_id):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('dashboard')
    leader = get_object_or_404(CollegeLeader, id=leader_id, college=request.college)
    leader.delete()
    messages.warning(request, "Leadership profile removed.")
    return redirect('college_settings')

@login_required
def delete_achievement(request, achievement_id):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('dashboard')
    achievement = get_object_or_404(CollegeAchievement, id=achievement_id, college=request.college)
    achievement.delete()
    messages.warning(request, "Achievement removed.")
    return redirect('/management/settings/#achievements')

@login_required
def student_list(request):
    students = StudentProfile.objects.filter(college=request.college).select_related('user', 'department', 'specialization', 'academic_class')
    
    if request.user.role == 'HOD':
        dept = request.user.hod_profile.department
        students = students.filter(department=dept)
        
    # Group students: Department -> Specialization (Program) -> AcademicClass (Batch/Year)
    grouped_data = {}
    for student in students:
        dept_name = student.department.name if student.department else "Unassigned Department"
        spec_name = student.specialization.name if student.specialization else "Unassigned Program"
        class_name = student.academic_class.name if student.academic_class else "Unassigned Class/Year"
        
        if dept_name not in grouped_data:
            grouped_data[dept_name] = {}
        if spec_name not in grouped_data[dept_name]:
            grouped_data[dept_name][spec_name] = {
                'students_count': 0,
                'classes': {}
            }
        if class_name not in grouped_data[dept_name][spec_name]['classes']:
            grouped_data[dept_name][spec_name]['classes'][class_name] = []
            
        grouped_data[dept_name][spec_name]['classes'][class_name].append(student)
        grouped_data[dept_name][spec_name]['students_count'] += 1
        
    return render(request, 'management/student_list.html', {
        'grouped_data': grouped_data,
        'total_count': students.count(),
        'students': students
    })

@login_required
def add_student(request):
    if request.user.role not in ['COLLEGE_ADMIN', 'HOD', 'SUPER_ADMIN']: 
        messages.error(request, "Permission Denied.")
        return redirect('student_list')
    
    class_id = request.GET.get('class_id')
    
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
                specialization=form.cleaned_data['specialization'],
                academic_class=form.cleaned_data.get('academic_class')
            )
            messages.success(request, f"Student {user.get_full_name()} added successfully.")
            return redirect('student_list')
    else:
        initial = {}
        if class_id:
            initial['academic_class'] = class_id
            cls = AcademicClass.objects.filter(id=class_id).first()
            if cls: initial['department'] = cls.department
            
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
        form = StudentEditForm(request.POST, request.FILES, instance=student, college=request.college, user_role=request.user.role, user_dept=getattr(request.user, 'hod_profile', None).department if request.user.role == 'HOD' else None)
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
            student.academic_class = form.cleaned_data.get('academic_class')
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
            'academic_class': student.academic_class,
        }
        form = StudentEditForm(instance=student, college=request.college, user_role=request.user.role, user_dept=getattr(request.user, 'hod_profile', None).department if request.user.role == 'HOD' else None, initial=initial)
    
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
    if request.user.role not in ['TEACHER', 'HOD']: 
        return redirect('dashboard')
        
    from django.utils import timezone
    
    # Get user's department safely
    if request.user.role == 'HOD':
        dept = getattr(request.user.hod_profile, 'department', None)
    else:
        dept = getattr(request.user.teacher_profile, 'department', None)

    if not dept:
        messages.error(request, "You are not assigned to any department.")
        return redirect('dashboard')

    academic_classes = AcademicClass.objects.filter(department=dept)
    
    selected_class = None
    selected_period = None
    selected_date = None
    students = []
    
    # Determine date safely
    date_str = request.GET.get('date') or request.POST.get('date')
    if date_str:
        try:
            from datetime import datetime
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.localdate()
    else:
        selected_date = timezone.localdate()

    present_count = 0
    absent_count = 0
    late_count = 0
    unmarked_count = 0
    attendance_rate = 0

    class_id = request.GET.get('class_id')
    period = request.GET.get('period')
    
    if class_id:
        selected_class = get_object_or_404(AcademicClass, id=class_id, department=dept)
        if period:
            selected_period = int(period)
            students = list(StudentProfile.objects.filter(academic_class=selected_class))
            
            # Fetch existing attendance records
            attendance_records = {
                att.student_id: att.status 
                for att in Attendance.objects.filter(
                    academic_class=selected_class,
                    period=selected_period,
                    date=selected_date
                )
            }
            
            for student in students:
                status = attendance_records.get(student.id)
                student.existing_status = status
                if status == 'PRESENT':
                    present_count += 1
                elif status == 'ABSENT':
                    absent_count += 1
                elif status == 'LATE':
                    late_count += 1
                else:
                    unmarked_count += 1
            
            total_count = len(students)
            if total_count > 0:
                attendance_rate = int(((present_count + late_count) / total_count) * 100)
                
    if request.method == 'POST':
        if request.user.role == 'HOD':
            messages.error(request, "Permission Denied: HODs are only permitted to view attendance records.")
            return redirect('mark_attendance')
            
        class_id = request.POST.get('class_id')
        selected_period = request.POST.get('period')
        
        if class_id and selected_period:
            selected_class = get_object_or_404(AcademicClass, id=class_id, department=dept)
            selected_period = int(selected_period)
            students = StudentProfile.objects.filter(academic_class=selected_class)
            
            for student in students:
                status = request.POST.get(f'status_{student.id}')
                if status:
                    Attendance.objects.update_or_create(
                        student=student,
                        date=selected_date,
                        period=selected_period,
                        defaults={
                            'status': status,
                            'marked_by': request.user,
                            'academic_class': selected_class,
                            'college': request.college
                        }
                    )
            messages.success(request, "Attendance saved successfully.")
            return redirect(f"/management/attendance/?class_id={selected_class.id}&period={selected_period}&date={selected_date.strftime('%Y-%m-%d')}")

    return render(request, 'management/mark_attendance.html', {
        'academic_classes': academic_classes,
        'selected_class': selected_class,
        'selected_period': selected_period,
        'selected_date': selected_date.strftime('%Y-%m-%d') if selected_date else '',
        'students': students,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
        'unmarked_count': unmarked_count,
        'attendance_rate': attendance_rate,
        'current_month': timezone.localdate().strftime('%Y-%m')
    })

@login_required
def print_monthly_attendance_report(request):
    if request.user.role not in ['HOD', 'COLLEGE_ADMIN']:
        return redirect('dashboard')
        
    from django.utils import timezone
    from django.shortcuts import get_object_or_404
    from django.contrib import messages
    from datetime import datetime
    
    class_id = request.GET.get('class_id')
    month_str = request.GET.get('month') # expected format: YYYY-MM
    
    if not class_id or not month_str:
        messages.error(request, "Class and Month must be selected.")
        return redirect('mark_attendance')
        
    # Get user's department
    if request.user.role == 'HOD':
        dept = getattr(request.user.hod_profile, 'department', None)
    else:
        dept = None

    # Retrieve selected class and month
    if dept:
        selected_class = get_object_or_404(AcademicClass, id=class_id, department=dept)
    else:
        selected_class = get_object_or_404(AcademicClass, id=class_id, college=request.college)
        
    try:
        year, month = map(int, month_str.split('-'))
        date_obj = datetime(year, month, 1)
        month_title = date_obj.strftime('%B %Y')
    except ValueError:
        messages.error(request, "Invalid month format.")
        return redirect('mark_attendance')
        
    # Fetch students in this class
    students = StudentProfile.objects.filter(academic_class=selected_class).order_by('roll_number')
    if not students.exists():
        messages.error(request, "No students enrolled in this class.")
        return redirect('mark_attendance')
        
    # Fetch attendance logs for this class, month, and year
    attendance_logs = Attendance.objects.filter(
        academic_class=selected_class,
        date__year=year,
        date__month=month
    ).order_by('date', 'period')
    
    # Find all unique (date, period) combinations chronologically
    sessions = sorted(list(set((log.date, log.period) for log in attendance_logs)))
    
    total_p = 0
    total_a = 0
    total_l = 0
    
    rows = []
    for student in students:
        p_count = 0
        a_count = 0
        l_count = 0
        
        student_logs = { (log.date, log.period): log.status for log in attendance_logs.filter(student=student) }
        
        session_statuses = []
        for session in sessions:
            status = student_logs.get(session)
            session_statuses.append(status)
            if status == 'PRESENT':
                p_count += 1
            elif status == 'ABSENT':
                a_count += 1
            elif status == 'LATE':
                l_count += 1
                
        total_p += p_count
        total_a += a_count
        total_l += l_count
        
        # Calculate percentage
        total_student_sessions = p_count + a_count + l_count
        pct = 100
        if total_student_sessions > 0:
            pct = int(((p_count + l_count) / total_student_sessions) * 100)
            
        rows.append({
            'roll_no': student.roll_number,
            'name': student.user.get_full_name(),
            'session_statuses': session_statuses,
            'p_count': p_count,
            'a_count': a_count,
            'l_count': l_count,
            'pct': pct
        })
        
    # Calculate overall averages
    total_logs = total_p + total_a + total_l
    present_rate = 100
    absent_rate = 0
    late_rate = 0
    if total_logs > 0:
        present_rate = int((total_p / total_logs) * 100)
        absent_rate = int((total_a / total_logs) * 100)
        late_rate = int((total_l / total_logs) * 100)
        
    return render(request, 'management/attendance_report_print.html', {
        'selected_class': selected_class,
        'month_str': month_str,
        'month_title': month_title,
        'sessions': sessions,
        'rows': rows,
        'present_rate': present_rate,
        'absent_rate': absent_rate,
        'late_rate': late_rate
    })

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
@login_required
def create_timetable(request):
    if request.user.role != 'HOD': return redirect('dashboard')
    
    classes = AcademicClass.objects.filter(department=request.user.hod_profile.department)
    teachers = TeacherProfile.objects.filter(department=request.user.hod_profile.department)
    
    class_id = request.GET.get('class_id')
    selected_class = None
    if class_id:
        selected_class = get_object_or_404(AcademicClass, id=class_id, department=request.user.hod_profile.department)
        
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    if request.GET.get('include_saturday'):
        days.append('Saturday')
        
    if request.method == 'POST' and selected_class:
        title = request.POST.get('title', f"Timetable for {selected_class.name}")
        tt = TimeTable.objects.create(
            department=request.user.hod_profile.department,
            academic_class=selected_class,
            title=title,
            uploaded_by=request.user.hod_profile,
            college=request.college
        )
        
        periods = range(1, selected_class.number_of_periods + 1)
        for day in days:
            for p in periods:
                subj = request.POST.get(f'subject_{day}_{p}')
                tid = request.POST.get(f'teacher_{day}_{p}')
                if subj or tid:
                    teacher = None
                    if tid:
                        teacher = TeacherProfile.objects.get(id=tid)
                    TimeTablePeriod.objects.create(
                        timetable=tt,
                        day_of_week=day,
                        period_number=p,
                        subject_name=subj,
                        teacher=teacher,
                        college=request.college
                    )
        messages.success(request, "Timetable created successfully.")
        return redirect('dashboard')
        
    subjects_json = "[]"
    if selected_class:
        subjects = list(selected_class.subjects.values_list('name', flat=True))
        import json
        subjects_json = json.dumps(subjects)

    return render(request, 'management/create_timetable.html', {
        'classes': classes,
        'selected_class': selected_class,
        'days': days,
        'teachers': teachers,
        'periods': range(1, (selected_class.number_of_periods + 1) if selected_class else 1),
        'title': 'Create Timetable',
        'subjects_json': subjects_json
    })

@login_required
def view_timetable(request, tt_id):
    tt = get_object_or_404(TimeTable, id=tt_id, college=request.college)
    selected_class = tt.academic_class
    
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    if tt.periods.filter(day_of_week='Saturday').exists():
        days.append('Saturday')
        
    existing_periods = {}
    for period in tt.periods.all():
        if period.day_of_week not in existing_periods:
            existing_periods[period.day_of_week] = {}
        existing_periods[period.day_of_week][period.period_number] = period

    return render(request, 'management/view_timetable.html', {
        'tt': tt,
        'selected_class': selected_class,
        'days': days,
        'periods': range(1, (selected_class.number_of_periods + 1) if selected_class else 7),
        'existing_periods': existing_periods,
        'title': tt.title
    })

@login_required
def edit_timetable(request, tt_id):
    if request.user.role != 'HOD': return redirect('dashboard')
    tt = get_object_or_404(TimeTable, id=tt_id, department=request.user.hod_profile.department)
    selected_class = tt.academic_class
    
    classes = AcademicClass.objects.filter(department=request.user.hod_profile.department)
    teachers = TeacherProfile.objects.filter(department=request.user.hod_profile.department)
    
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    if tt.periods.filter(day_of_week='Saturday').exists():
        days.append('Saturday')
        
    if request.method == 'POST':
        tt.title = request.POST.get('title', tt.title)
        tt.save()
        
        tt.periods.all().delete()
        
        periods = range(1, selected_class.number_of_periods + 1) if selected_class else range(1, 7)
        for day in days:
            for p in periods:
                subj = request.POST.get(f'subject_{day}_{p}')
                tid = request.POST.get(f'teacher_{day}_{p}')
                if subj or tid:
                    teacher = None
                    if tid:
                        teacher = TeacherProfile.objects.get(id=tid)
                    TimeTablePeriod.objects.create(
                        timetable=tt,
                        day_of_week=day,
                        period_number=p,
                        subject_name=subj,
                        teacher=teacher,
                        college=request.college
                    )
        messages.success(request, "Timetable updated successfully.")
        return redirect('dashboard')
        
    existing_periods = {}
    for period in tt.periods.all():
        if period.day_of_week not in existing_periods:
            existing_periods[period.day_of_week] = {}
        existing_periods[period.day_of_week][period.period_number] = period

    return render(request, 'management/create_timetable.html', {
        'tt': tt,
        'classes': classes,
        'selected_class': selected_class,
        'days': days,
        'teachers': teachers,
        'periods': range(1, (selected_class.number_of_periods + 1) if selected_class else 7),
        'existing_periods': existing_periods,
        'title': 'Edit Timetable'
    })

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
def create_department_event(request):
    if request.user.role != 'HOD': 
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = DepartmentEventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.college = request.college
            event.department = request.user.hod_profile.department
            event.posted_by = request.user.hod_profile
            event.save()
            messages.success(request, "Department event created and submitted for College Admin approval.")
            return redirect('dashboard')
    else:
        form = DepartmentEventForm()
    return render(request, 'management/create_department_event.html', {'form': form})

@login_required
def approve_department_event(request, event_id):
    if request.user.role != 'COLLEGE_ADMIN': 
        return redirect('dashboard')
    event = get_object_or_404(DepartmentEvent, id=event_id, college=request.college)
    event.is_approved = True
    event.approved_by = request.user
    event.save()
    messages.success(request, f"Event '{event.title}' approved successfully.")
    return redirect('dashboard')

@login_required
def reject_department_event(request, event_id):
    if request.user.role != 'COLLEGE_ADMIN': 
        return redirect('dashboard')
    event = get_object_or_404(DepartmentEvent, id=event_id, college=request.college)
    event.delete()
    messages.warning(request, f"Event request removed.")
    return redirect('dashboard')

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

@login_required
def student_grades(request):
    if request.user.role != 'STUDENT':
        return redirect('dashboard')
    student = request.user.student_profile
    submissions = Submission.objects.filter(student=student).exclude(marks__isnull=True).order_by('-submitted_at')
    return render(request, 'management/student_grades.html', {'submissions': submissions})

@login_required
def student_timetable(request):
    if request.user.role != 'STUDENT':
        return redirect('dashboard')
    student = request.user.student_profile
    if student.academic_class:
        timetables = TimeTable.objects.filter(academic_class=student.academic_class)
    else:
        timetables = TimeTable.objects.filter(department=student.department)
    return render(request, 'management/student_timetable.html', {'timetables': timetables})

@login_required
def student_attendance(request):
    if request.user.role != 'STUDENT':
        return redirect('dashboard')
    
    profile = getattr(request.user, 'student_profile', None)
    if not profile:
        messages.error(request, "Student profile not found.")
        return redirect('dashboard')
        
    attendances = Attendance.objects.filter(student=profile).order_by('-date', '-period')
    
    # Calculate attendance statistics
    total_records = attendances.count()
    present_count = attendances.filter(status='PRESENT').count()
    late_count = attendances.filter(status='LATE').count()
    absent_count = attendances.filter(status='ABSENT').count()
    
    attendance_rate = 0
    if total_records > 0:
        attendance_rate = int(((present_count + late_count) / total_records) * 100)
        
    return render(request, 'management/student_attendance.html', {
        'attendances': attendances,
        'total_records': total_records,
        'present_count': present_count,
        'late_count': late_count,
        'absent_count': absent_count,
        'attendance_rate': attendance_rate
    })

@login_required
def student_assignments(request):
    if request.user.role != 'STUDENT':
        return redirect('dashboard')
    return render(request, 'management/student_assignments.html', {})

@login_required
def department_configuration(request):
    if request.user.role != 'HOD':
        return redirect('dashboard')
    
    department = request.user.hod_profile.department
    
    if request.method == 'POST' and 'add_class' in request.POST:
        class_form = AcademicClassForm(request.POST)
        if class_form.is_valid():
            academic_class = class_form.save(commit=False)
            academic_class.department = department
            academic_class.college = request.college
            academic_class.save()
            messages.success(request, 'Class added successfully.')
            return redirect('department_configuration')
    else:
        class_form = AcademicClassForm()
        
    if request.method == 'POST' and 'add_subject' in request.POST:
        subject_form = SubjectForm(request.POST, department=department)
        if subject_form.is_valid():
            subject = subject_form.save(commit=False)
            subject.department = department
            subject.college = request.college
            subject.save()
            messages.success(request, 'Subject added successfully.')
            return redirect('department_configuration')
    else:
        subject_form = SubjectForm(department=department)
        
    if request.method == 'POST' and 'add_category' in request.POST:
        cat_form = InternalMarkCategoryForm(request.POST)
        if cat_form.is_valid():
            cat = cat_form.save(commit=False)
            cat.department = department
            cat.college = request.college
            cat.save()
            messages.success(request, 'Internal Mark Category added successfully.')
            return redirect('department_configuration')
    else:
        cat_form = InternalMarkCategoryForm()
        
    classes = AcademicClass.objects.filter(department=department)
    categories = InternalMarkCategory.objects.filter(department=department)
    subjects = Subject.objects.filter(department=department)
    
    return render(request, 'management/department_config.html', {
        'classes': classes,
        'categories': categories,
        'subjects': subjects,
        'class_form': class_form,
        'cat_form': cat_form,
        'subject_form': subject_form
    })

@login_required
def delete_academic_class(request, class_id):
    if request.user.role != 'HOD': return redirect('dashboard')
    cls = get_object_or_404(AcademicClass, id=class_id, department=request.user.hod_profile.department)
    cls.delete()
    messages.success(request, 'Class deleted.')
    return redirect('department_configuration')

@login_required
def delete_subject(request, subject_id):
    if request.user.role != 'HOD': return redirect('dashboard')
    subject = get_object_or_404(Subject, id=subject_id, department=request.user.hod_profile.department)
    subject.delete()
    messages.success(request, 'Subject deleted.')
    return redirect('department_configuration')

@login_required
def delete_internal_mark_category(request, category_id):
    if request.user.role != 'HOD': return redirect('dashboard')
    cat = get_object_or_404(InternalMarkCategory, id=category_id, department=request.user.hod_profile.department)
    cat.delete()
    messages.success(request, 'Category deleted.')
    return redirect('department_configuration')

@login_required
def assignment_submissions(request, pk):
    if request.user.role not in ['TEACHER', 'HOD']: return redirect('dashboard')
    assignment = get_object_or_404(Assignment, pk=pk)
    submissions = Submission.objects.filter(assignment=assignment)
    return render(request, 'management/assignment_submissions.html', {'assignment': assignment, 'submissions': submissions})

@login_required
def internal_marks_list(request):
    if request.user.role not in ['TEACHER', 'HOD']:
        return redirect('dashboard')
        
    if request.user.role == 'TEACHER':
        department = request.user.teacher_profile.department
    else:
        department = request.user.hod_profile.department
        
    classes = AcademicClass.objects.filter(department=department)
    categories = InternalMarkCategory.objects.filter(department=department)
    
    selected_class = None
    students = []
    
    class_id = request.GET.get('class_id')
    if class_id:
        selected_class = get_object_or_404(AcademicClass, id=class_id, department=department)
        students = StudentProfile.objects.filter(academic_class=selected_class)
        
    if request.method == 'POST' and selected_class:
        for student in students:
            for cat in categories:
                mark_key = f'marks_{student.id}_{cat.id}'
                if mark_key in request.POST:
                    mark_val = request.POST[mark_key]
                    if mark_val:
                        InternalMark.objects.update_or_create(
                            student=student,
                            category=cat,
                            academic_class=selected_class,
                            defaults={'marks_obtained': float(mark_val), 'college': request.college}
                        )
                    else:
                        InternalMark.objects.filter(
                            student=student,
                            category=cat,
                            academic_class=selected_class
                        ).delete()
        messages.success(request, 'Marks saved successfully.')
        return redirect(f"{request.path}?class_id={selected_class.id}")
        
    marks_dict = {}
    if selected_class:
        for student in students:
            marks_dict[student.id] = {}
            marks = InternalMark.objects.filter(student=student, academic_class=selected_class)
            for m in marks:
                marks_dict[student.id][m.category.id] = m.marks_obtained
                
    return render(request, 'management/internal_marks.html', {
        'classes': classes,
        'selected_class': selected_class,
        'categories': categories,
        'students': students,
        'marks_dict': marks_dict
    })

@login_required
def submit_assignment(request, pk):
    if request.user.role != 'STUDENT': return redirect('dashboard')
    assignment = get_object_or_404(Assignment, pk=pk)
    
    student = request.user.student_profile
    submission = Submission.objects.filter(assignment=assignment, student=student).first()
    
    if request.method == 'POST':
        if 'file' in request.FILES:
            if not submission:
                submission = Submission(assignment=assignment, student=student, college=request.college)
            submission.file = request.FILES['file']
            submission.save()
            messages.success(request, 'Assignment submitted successfully.')
            return redirect('student_assignments')
            
    return render(request, 'management/submit_assignment.html', {'assignment': assignment, 'submission': submission})

@login_required
def college_enquiries_list(request):
    if request.user.role != 'COLLEGE_ADMIN':
        return redirect('dashboard')
    
    status_filter = request.GET.get('status', '')
    enquiries = CollegeEnquiry.objects.filter(college=request.college).order_by('-created_at')
    
    if status_filter:
        enquiries = enquiries.filter(status=status_filter)
        
    return render(request, 'management/enquiries_list.html', {
        'enquiries': enquiries,
        'selected_status': status_filter,
    })

@login_required
def update_enquiry_status(request, enquiry_id, new_status):
    if request.user.role != 'COLLEGE_ADMIN':
        return redirect('dashboard')
    
    enquiry = get_object_or_404(CollegeEnquiry, id=enquiry_id, college=request.college)
    valid_statuses = dict(CollegeEnquiry.STATUS_CHOICES)
    if new_status in valid_statuses:
        enquiry.status = new_status
        enquiry.save()
        messages.success(request, f"Enquiry status updated to {valid_statuses[new_status]}.")
    else:
        messages.error(request, "Invalid status choice.")
        
    return redirect('college_enquiries_list')

@login_required
def delete_enquiry(request, enquiry_id):
    if request.user.role != 'COLLEGE_ADMIN':
        return redirect('dashboard')
    
    enquiry = get_object_or_404(CollegeEnquiry, id=enquiry_id, college=request.college)
    enquiry.delete()
    messages.warning(request, "Enquiry record deleted.")
    return redirect('college_enquiries_list')
