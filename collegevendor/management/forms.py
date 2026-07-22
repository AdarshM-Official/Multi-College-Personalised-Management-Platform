from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from .models import StudentProfile, TeacherProfile, Department, Specialization, Assignment, Attendance, HODProfile, TimeTable, ExamNotification, AcademicClass, InternalMarkCategory, Subject, DepartmentEvent, CollegeEnquiry
from accounts.models import CustomUser
from colleges.models import College

DISTRICT_CHOICES = [
    ('', 'Select District'),
    ('Alappuzha', 'Alappuzha'), ('Ernakulam', 'Ernakulam'), ('Idukki', 'Idukki'),
    ('Kannur', 'Kannur'), ('Kasaragod', 'Kasaragod'), ('Kollam', 'Kollam'),
    ('Kottayam', 'Kottayam'), ('Kozhikode', 'Kozhikode'), ('Malappuram', 'Malappuram'),
    ('Palakkad', 'Palakkad'), ('Pathanamthitta', 'Pathanamthitta'), ('Thiruvananthapuram', 'Thiruvananthapuram'),
    ('Thrissur', 'Thrissur'), ('Wayanad', 'Wayanad'),
]

class CollegeSettingsForm(forms.ModelForm):
    district = forms.ChoiceField(choices=DISTRICT_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}), required=False)
    university_affiliation = forms.MultipleChoiceField(
        choices=[
            ('University of Kerala', 'University of Kerala'),
            ('MG University', 'MG University'),
            ('Calicut University', 'Calicut University'),
            ('Kannur University', 'Kannur University'),
            ('KTU', 'KTU'),
            ('CUSAT', 'CUSAT'),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = College
        fields = [
            'name', 'established_year', 'logo', 'address', 'district', 
            'website', 'theme_color', 'university_affiliation', 
            'contact_email', 'phone_number', 'description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'established_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'theme_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.university_affiliation:
            self.initial['university_affiliation'] = [x.strip() for x in self.instance.university_affiliation.split(',')]

class StudentForm(forms.Form):
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    profile_photo = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    
    university_reg_number = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'University Reg. No'}))
    roll_number = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Class Roll No'}))
    phone_number = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    father_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    mother_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    
    ug_marklist = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    plus_two_marklist = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    last_passout_year = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year of last completion'}))

    department = forms.ModelChoiceField(queryset=Department.objects.none(), widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_department'}))
    specialization = forms.ModelChoiceField(queryset=Specialization.objects.none(), required=False, label="Specialization", widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_specialization'}))
    academic_class = forms.ModelChoiceField(queryset=AcademicClass.objects.none(), required=False, label="Academic Class", widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_academic_class'}))

    def __init__(self, *args, **kwargs):
        college = kwargs.pop('college', None)
        user_role = kwargs.pop('user_role', None)
        user_dept = kwargs.pop('user_dept', None)
        super().__init__(*args, **kwargs)
        if college:
            if user_role == 'HOD' and user_dept:
                self.fields['department'].queryset = Department.objects.filter(id=user_dept.id)
                self.fields['department'].initial = user_dept
                self.fields['specialization'].queryset = Specialization.objects.filter(department=user_dept)
                self.fields['academic_class'].queryset = AcademicClass.objects.filter(department=user_dept)
            else:
                self.fields['department'].queryset = Department.objects.filter(college=college)
                self.fields['specialization'].queryset = Specialization.objects.filter(college=college)
                self.fields['academic_class'].queryset = AcademicClass.objects.filter(college=college)

class StudentEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = StudentProfile
        fields = ['profile_photo', 'phone_number', 'address', 'father_name', 'mother_name', 'date_of_birth', 'academic_class', 'university_reg_number', 'roll_number', 'last_passout_year', 'department', 'specialization']
        widgets = {
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'father_name': forms.TextInput(attrs={'class': 'form-control'}),
            'mother_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'academic_class': forms.Select(attrs={'class': 'form-select'}),
            'university_reg_number': forms.TextInput(attrs={'class': 'form-control'}),
            'roll_number': forms.TextInput(attrs={'class': 'form-control'}),
            'last_passout_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'specialization': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        college = kwargs.pop('college', None)
        user_role = kwargs.pop('user_role', None)
        user_dept = kwargs.pop('user_dept', None)
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            
        if college:
            if user_role == 'HOD' and user_dept:
                self.fields['department'].queryset = Department.objects.filter(id=user_dept.id)
                self.fields['department'].initial = user_dept
                self.fields['specialization'].queryset = Specialization.objects.filter(department=user_dept)
                self.fields['academic_class'].queryset = AcademicClass.objects.filter(department=user_dept)
            else:
                self.fields['department'].queryset = Department.objects.filter(college=college)
                self.fields['specialization'].queryset = Specialization.objects.filter(college=college)
                self.fields['academic_class'].queryset = AcademicClass.objects.filter(college=college)

class UserEditForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['email'].initial = self.instance.email

class TeacherForm(forms.Form):
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    qualification = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    department = forms.ModelChoiceField(queryset=Department.objects.none(), widget=forms.Select(attrs={'class': 'form-select'}))
    specialization = forms.ModelChoiceField(queryset=Specialization.objects.none(), required=False, widget=forms.Select(attrs={'class': 'form-select'}))

    def __init__(self, *args, **kwargs):
        college = kwargs.pop('college', None)
        super().__init__(*args, **kwargs)
        if college:
            self.fields['department'].queryset = Department.objects.filter(college=college)
            self.fields['specialization'].queryset = Specialization.objects.filter(college=college)

class TeacherEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = TeacherProfile
        fields = ['phone_number', 'address', 'qualification', 'profile_photo']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'deadline', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'deadline': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }

class DepartmentForm(forms.ModelForm):
    DEGREE_CHOICES = [
        ('BA', 'Bachelor of Arts (BA) – humanities, languages, social sciences'),
        ('BSc', 'Bachelor of Science (BSc) – science subjects'),
        ('BCom', 'Bachelor of Commerce (BCom) – accounting, finance, commerce'),
        ('BBA', 'Bachelor of Business Administration (BBA) – management & business'),
        ('BCA', 'Bachelor of Computer Applications (BCA) – computer science & IT'),
        ('BArch', 'Bachelor of Architecture (BArch) – architecture'),
        ('BSc Agriculture', 'Bachelor of Agriculture (BSc Agriculture) – agriculture'),
        ('BVSc', 'Bachelor of Veterinary Science (BVSc) – veterinary'),
        ('MA', 'Master of Arts (MA) – humanities, languages, social sciences'),
        ('MSc', 'Master of Science (MSc) – science & research subjects'),
        ('MCom', 'Master of Commerce (MCom) – finance, accounting, business'),
        ('MBA', 'Master of Business Administration (MBA) – management & business'),
        ('MCA', 'Master of Computer Applications (MCA) – computer & IT'),
        ('MArch', 'Master of Architecture (MArch) – architecture'),
        ('MSc Agriculture', 'Master of Agriculture (MSc Agriculture) – agriculture'),
        ('Other', 'Other (Custom Degree Type)'),
    ]
    
    name = forms.ChoiceField(choices=DEGREE_CHOICES, widget=forms.Select(attrs={'class': 'form-select', 'id': 'degree-select'}), label="Degree Type")
    custom_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control d-none', 'placeholder': 'Enter your degree type', 'id': 'custom-degree-input'}), label="Custom Degree Name")

    specializations_list = forms.CharField(
        required=False, 
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g. Physics, Chemistry (Comma separated)', 'class': 'form-control'}),
        help_text="Enter initial courses/specializations separated by commas."
    )

    class Meta:
        model = Department
        fields = ['category', 'description']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class SpecializationForm(forms.ModelForm):
    class Meta:
        model = Specialization
        fields = ['department', 'name']
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        college = kwargs.pop('college', None)
        super().__init__(*args, **kwargs)
        if college:
            self.fields['department'].queryset = Department.objects.filter(college=college)

class ExcelImportForm(forms.Form):
    excel_file = forms.FileField(label="Select Excel File", widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx, .xls'}))

class HODForm(forms.Form):
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    profile_photo = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    department = forms.ModelChoiceField(queryset=Department.objects.none(), widget=forms.Select(attrs={'class': 'form-select'}))

    def __init__(self, *args, **kwargs):
        college = kwargs.pop('college', None)
        super().__init__(*args, **kwargs)
        if college:
            self.fields['department'].queryset = Department.objects.filter(college=college)

class HODEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = HODProfile
        fields = ['profile_photo', 'phone_number']
        widgets = {
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

class TimeTableForm(forms.ModelForm):
    class Meta:
        model = TimeTable
        fields = ['title', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }

class ExamNotificationForm(forms.ModelForm):
    class Meta:
        model = ExamNotification
        fields = ['title', 'description', 'exam_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'exam_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class DepartmentEventForm(forms.ModelForm):
    class Meta:
        model = DepartmentEvent
        fields = ['title', 'description', 'event_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Annual Tech Fest'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Event details and guidelines...'}),
            'event_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class AcademicClassForm(forms.ModelForm):
    class Meta:
        model = AcademicClass
        fields = ['name', 'number_of_periods']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., S1 B.Tech CS'}),
            'number_of_periods': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '15'}),
        }

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['academic_class', 'name', 'code']
        widgets = {
            'academic_class': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Engineering Mathematics'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., MAT101'}),
        }
    
    def __init__(self, *args, **kwargs):
        department = kwargs.pop('department', None)
        super().__init__(*args, **kwargs)
        if department:
            self.fields['academic_class'].queryset = AcademicClass.objects.filter(department=department)
            self.fields['academic_class'].empty_label = "Select Class/Semester"

class InternalMarkCategoryForm(forms.ModelForm):
    class Meta:
        model = InternalMarkCategory
        fields = ['name', 'max_marks']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Attendance'}),
            'max_marks': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '1000'}),
        }

class CollegeEnquiryForm(forms.ModelForm):
    class Meta:
        model = CollegeEnquiry
        fields = ['name', 'email', 'phone_number', 'course_interested', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Full Name', 'required': 'true'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com', 'required': 'true'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., +91 9876543210', 'required': 'true'}),
            'course_interested': forms.Select(attrs={'class': 'form-select', 'required': 'true'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Details of your enquiry/application...', 'required': 'true'}),
        }

    def __init__(self, *args, **kwargs):
        college = kwargs.pop('college', None)
        super().__init__(*args, **kwargs)
        if college:
            self.fields['course_interested'].queryset = Specialization.objects.filter(college=college)
            self.fields['course_interested'].empty_label = "Select Program / Course"

from colleges.models import CollegeEvent, CollegeEventImage

class CollegeEventForm(forms.ModelForm):
    class Meta:
        model = CollegeEvent
        fields = ['title', 'description', 'event_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Annual Sports Day'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Provide details about the event...'}),
            'event_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class CollegeEventImageForm(forms.Form):
    images = forms.ImageField(widget=MultipleFileInput(attrs={'class': 'form-control', 'multiple': True}), required=False)
