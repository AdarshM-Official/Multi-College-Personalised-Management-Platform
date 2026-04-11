from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import pandas as pd
from .models import StudentProfile, TeacherProfile, Department, Specialization, Assignment, Submission, Attendance
from accounts.models import CustomUser
from .forms import StudentForm, TeacherForm, TeacherEditForm, AssignmentForm, DepartmentForm, SpecializationForm, CollegeSettingsForm, ExcelImportForm
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
def import_departments_excel(request):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('dashboard')
    if request.method == 'POST':
        form = ExcelImportForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['excel_file']
            try:
                # Load Excel file
                df = pd.read_excel(file)
                
                # Normalize column names to lowercase and strip spaces
                df.columns = [str(c).strip().lower() for c in df.columns]
                
                # Check for mandatory columns (Department Name and Category are essential)
                # We also support optional 'Description' and 'Specializations'
                name_col = next((c for c in df.columns if 'name' in c or 'department' in c), None)
                cat_col = next((c for c in df.columns if 'category' in c or 'type' in c), None)
                desc_col = next((c for c in df.columns if 'desc' in c), None)
                spec_col = next((c for c in df.columns if 'spec' in c or 'course' in c), None)

                if not name_col or not cat_col:
                    messages.error(request, "Excel must contain 'Department Name' and 'Category' (UG/PG) columns.")
                    return redirect('department_list')
                
                created_count = 0
                for _, row in df.iterrows():
                    name = str(row[name_col]).strip()
                    category = str(row[cat_col]).strip().upper()
                    description = str(row[desc_col]).strip() if desc_col and pd.notna(row[desc_col]) else ""
                    specializations = str(row[spec_col]).strip() if spec_col and pd.notna(row[spec_col]) else ""
                    
                    if not name or category not in ['UG', 'PG']:
                        continue
                    
                    # Create or update department
                    dept, created = Department.objects.get_or_create(
                        college=request.college,
                        name=name,
                        category=category,
                        defaults={'description': description}
                    )
                    
                    # Process specializations if provided
                    if specializations:
                        specs = [s.strip() for s in specializations.split(',') if s.strip()]
                        for s_name in specs:
                            Specialization.objects.get_or_create(
                                department=dept,
                                name=s_name,
                                college=request.college
                            )
                    created_count += 1
                
                messages.success(request, f"Successfully processed {created_count} departments from Excel.")
            except Exception as e:
                import traceback
                print(traceback.format_exc())
                messages.error(request, f"Error processing file: {str(e)}")
            return redirect('department_list')
    return redirect('department_list')

@login_required
def download_department_template(request):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('dashboard')
    
    # Define columns
    columns = ['Department Name', 'Category', 'Description', 'Specializations']
    # Example data
    data = [
        ['Bachelor of Computer Applications (BCA)', 'UG', 'IT and Computer Science department', 'Software Engineering, Web Development, Cyber Security'],
        ['Master of Science (MSc)', 'PG', 'Postgraduate Science Research', 'Applied Physics, Organic Chemistry']
    ]
    
    df = pd.DataFrame(data, columns=columns)
    
    # Create the Excel file in memory
    import io
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=department_import_template.xlsx'
    return response

@login_required
def download_teacher_template(request):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('dashboard')
    
    columns = [
        'First Name', 'Last Name', 'Email', 'Password', 
        'Phone Number', 'Address', 'Department', 'Specialization', 'Qualification'
    ]
    
    # Get some departments and specializations for example data
    dept = Department.objects.filter(college=request.college).first()
    spec = Specialization.objects.filter(department=dept).first() if dept else None
    
    dept_name = dept.name if dept else "Computer Science"
    spec_name = spec.name if spec else "Software Engineering"
    
    data = [
        ['John', 'Doe', 'john.doe@example.com', 'Pass1234', '9876543210', '123 Tech Lane', dept_name, spec_name, 'PhD in CS'],
        ['Jane', 'Smith', 'jane.smith@example.com', 'Secure789', '9123456780', '456 Academic Way', dept_name, '', 'M.Tech IT']
    ]
    
    df = pd.DataFrame(data, columns=columns)
    
    import io
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    
    output.seek(0)
    response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=teacher_import_template.xlsx'
    return response

@login_required
def import_teachers_excel(request):
    if request.user.role != 'COLLEGE_ADMIN': return redirect('dashboard')
    if request.method == 'POST':
        form = ExcelImportForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['excel_file']
            try:
                df = pd.read_excel(file)
                df.columns = [str(c).strip().lower() for c in df.columns]
                
                # Column mapping
                fname_col = next((c for c in df.columns if 'first' in c), None)
                lname_col = next((c for c in df.columns if 'last' in c), None)
                email_col = next((c for c in df.columns if 'email' in c), None)
                pass_col = next((c for c in df.columns if 'pass' in c), None)
                phone_col = next((c for c in df.columns if 'phone' in c), None)
                addr_col = next((c for c in df.columns if 'address' in c), None)
                dept_col = next((c for c in df.columns if 'dept' in c or 'department' in c), None)
                spec_col = next((c for c in df.columns if 'spec' in c or 'subject' in c or 'course' in c), None)
                qual_col = next((c for c in df.columns if 'qual' in c), None)

                if not all([fname_col, email_col, pass_col]):
                    messages.error(request, "Excel must contain First Name, Email, and Password columns.")
                    return redirect('teacher_list')
                
                created_count = 0
                errors = []
                for index, row in df.iterrows():
                    try:
                        email = str(row[email_col]).strip().lower()
                        if not email or CustomUser.objects.filter(email=email).exists():
                            continue
                        
                        fname = str(row[fname_col]).strip()
                        lname = str(row[lname_col]).strip() if lname_col and pd.notna(row[lname_col]) else ""
                        password = str(row[pass_col]).strip() or 'Default@123'
                        
                        dept_name = str(row[dept_col]).strip() if dept_col and pd.notna(row[dept_col]) else ""
                        spec_name = str(row[spec_col]).strip() if spec_col and pd.notna(row[spec_col]) else ""
                        
                        phone = str(row[phone_col]).strip() if phone_col and pd.notna(row[phone_col]) else ""
                        address = str(row[addr_col]).strip() if addr_col and pd.notna(row[addr_col]) else ""
                        qualification = str(row[qual_col]).strip() if qual_col and pd.notna(row[qual_col]) else "Degree"

                        # Resolve Department & Specialization
                        department = None
                        if dept_name:
                            department = Department.objects.filter(college=request.college, name__iexact=dept_name).first()
                        
                        specialization = None
                        if department and spec_name:
                            specialization = Specialization.objects.filter(department=department, name__iexact=spec_name).first()

                        # Create User
                        user = CustomUser.objects.create_user(
                            email=email, password=password,
                            first_name=fname, last_name=lname,
                            role='TEACHER', college=request.college
                        )
                        
                        # Create Profile
                        TeacherProfile.objects.create(
                            user=user, college=request.college,
                            department=department,
                            specialization=specialization,
                            phone_number=phone,
                            address=address,
                            qualification=qualification
                        )
                        created_count += 1
                    except Exception as row_error:
                        errors.append(f"Row {index+2}: {str(row_error)}")
                
                if errors:
                    messages.warning(request, f"Processed {created_count} teachers. Errors in {len(errors)} rows.")
                    # In a real app we might log these errors
                else:
                    messages.success(request, f"Successfully imported {created_count} faculty members.")
            except Exception as e:
                messages.error(request, f"Error processing file: {str(e)}")
            return redirect('teacher_list')
    return redirect('teacher_list')


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
