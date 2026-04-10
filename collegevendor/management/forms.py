from django import forms
from .models import StudentProfile, TeacherProfile, Department, Specialization, Assignment, Attendance
from accounts.models import CustomUser
from colleges.models import College

DISTRICT_CHOICES = [
    ('', 'Select District'),
    ('Alappuzha', 'Alappuzha'), ('Ernakulam', 'Ernakulam'), ('Idukki', 'Idukki'),
    ('Kannur', 'Kannur'), ('Kasaragod', 'Kasaragod'), ('Kollam', 'Kollam'),
    ('Kottayam', 'Kottayam'), ('Kozhikode', 'Kozhikode'), ('Malappuram', 'Malappuram'),
    ('Palakkad', 'Palakkad'), ('Pathanamthitta', 'Pathanamthitta'), ('Thiruvananthapuram', 'Thiruvananthapuram'),
    ('Thrissur', 'Thrissur'), ('Wayanad', 'Wayanad')
]

UNIVERSITY_CHOICES = [
    ('Kerala University', 'University of Kerala'),
    ('MG University', 'Mahatma Gandhi University'),
    ('Calicut University', 'University of Calicut'),
    ('Kannur University', 'Kannur University'),
    ('KTU', 'APJ Abdul Kalam Technological University (KTU)'),
    ('KUFOS', 'Kerala University of Fisheries and Ocean Studies'),
    ('KAU', 'Kerala Agricultural University'),
    ('KVASU', 'Kerala Veterinary and Animal Sciences University'),
    ('KHSU', 'Kerala University of Health Sciences'),
    ('CUSAT', 'Cochin University of Science and Technology'),
    ('NUALS', 'The National University of Advanced Legal Studies (NUALS)'),
    ('Other', 'Other Academic Body')
]

class CollegeSettingsForm(forms.ModelForm):
    university_affiliation = forms.MultipleChoiceField(
        choices=UNIVERSITY_CHOICES, 
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = College
        fields = ['name', 'logo', 'district', 'university_affiliation', 'contact_email', 'phone_number', 'address', 'website', 'established_year', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'district': forms.Select(choices=DISTRICT_CHOICES, attrs={'class': 'form-select'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'established_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.university_affiliation:
            # Convert comma-separated string back to list for MultipleChoiceField
            self.initial['university_affiliation'] = [x.strip() for x in self.instance.university_affiliation.split(',')]

class StudentForm(forms.Form):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    roll_number = forms.CharField(max_length=50)
    department = forms.ModelChoiceField(queryset=Department.objects.none())
    specialization = forms.ModelChoiceField(queryset=Specialization.objects.none(), required=False)

    def __init__(self, *args, **kwargs):
        college = kwargs.pop('college', None)
        super().__init__(*args, **kwargs)
        if college:
            self.fields['department'].queryset = Department.objects.filter(college=college)
            self.fields['specialization'].queryset = Specialization.objects.filter(college=college)

class TeacherForm(forms.Form):
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    role = forms.CharField(initial='TEACHER', widget=forms.HiddenInput)
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
    profile_photo = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. +91 9876543210'}))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Residential Address'}))

    department = forms.ModelChoiceField(queryset=Department.objects.none(), widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_department'}))
    specialization = forms.ModelChoiceField(queryset=Specialization.objects.none(), required=False, widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_specialization'}))
    qualification = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. PhD, M.Tech'}))

    def __init__(self, *args, **kwargs):
        college = kwargs.pop('college', None)
        super().__init__(*args, **kwargs)
        if college:
            self.fields['department'].queryset = Department.objects.filter(college=college)
            self.fields['specialization'].queryset = Specialization.objects.filter(college=college)

class TeacherEditForm(forms.Form):
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    profile_photo = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))

    department = forms.ModelChoiceField(queryset=Department.objects.none(), widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_department'}))
    specialization = forms.ModelChoiceField(queryset=Specialization.objects.none(), required=False, widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_specialization'}))
    qualification = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. PhD, M.Tech'}))

    def __init__(self, *args, **kwargs):
        college = kwargs.pop('college', None)
        super().__init__(*args, **kwargs)
        if college:
            self.fields['department'].queryset = Department.objects.filter(college=college)
            self.fields['specialization'].queryset = Specialization.objects.filter(college=college)

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'file', 'deadline']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class DepartmentForm(forms.ModelForm):
    DEGREE_CHOICES = [
        ('Bachelor of Arts (BA)', 'Bachelor of Arts (BA) – humanities, languages, social sciences'),
        ('Bachelor of Science (BSc)', 'Bachelor of Science (BSc) – science & research subjects'),
        ('Bachelor of Commerce (BCom)', 'Bachelor of Commerce (BCom) – finance, accounting, business'),
        ('Bachelor of Business Administration (BBA)', 'Bachelor of Business Administration (BBA) – management & business'),
        ('Bachelor of Computer Applications (BCA)', 'Bachelor of Computer Applications (BCA) – computer & IT'),
        ('Bachelor of Physical Education (BPEd / BPES)', 'Bachelor of Physical Education (BPEd / BPES) – sports'),
        ('Bachelor of Architecture (BArch)', 'Bachelor of Architecture (BArch) – architecture'),
        ('Bachelor of Agriculture (BSc Agriculture)', 'Bachelor of Agriculture (BSc Agriculture) – agriculture'),
        ('Bachelor of Veterinary Science (BVSc)', 'Bachelor of Veterinary Science (BVSc) – veterinary'),
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
        fields = ['name', 'category', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Brief overview...', 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }

class SpecializationForm(forms.ModelForm):
    # This will be handled dynamically in JS for better UX, 
    # but we provide common options here as fallback.
    COURSE_CATALOGUE = {
        'BA': [
            'English', 'Malayalam', 'Hindi', 'Arabic', 'Economics', 'History', 'Political Science', 
            'Sociology', 'English Literature', 'Malayalam Literature', 'Hindi Literature', 
            'Sanskrit', 'Tamil', 'French', 'German', 'Psychology', 'Journalism & Mass Communication'
        ],
        'BSc': [
            'Physics', 'Chemistry', 'Mathematics', 'Botany', 'Zoology', 'Computer Science', 
            'Statistics', 'Electronics', 'Environmental Science', 'Psychology', 
            'Biotechnology', 'Microbiology', 'Biochemistry', 'Mathematics with Computer Science'
        ],
        'BCom': ['Finance', 'Accounting', 'Computer Applications', 'Taxation', 'Banking'],
        'BBA': ['Marketing', 'Finance', 'Human Resources', 'Supply Chain', 'International Business'],
        'BCA': ['Software Development', 'Web Technologies', 'Networking', 'Cloud Computing'],
    }
    
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'spec-name-input'}))

    class Meta:
        model = Specialization
        fields = ['department', 'name']
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select', 'id': 'spec-dept-select'}),
        }

    def __init__(self, *args, **kwargs):
        college = kwargs.pop('college', None)
        super().__init__(*args, **kwargs)
        if college:
            self.fields['department'].queryset = Department.objects.filter(college=college)
