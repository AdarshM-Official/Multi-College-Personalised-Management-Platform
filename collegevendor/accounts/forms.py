from django import forms
from colleges.models import College
from .models import CustomUser

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

class CollegeRegistrationForm(forms.Form):
    # College details
    college_name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    registration_number = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. REG-2024-001'}))
    
    district = forms.ChoiceField(choices=DISTRICT_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    university_affiliation = forms.MultipleChoiceField(
        choices=UNIVERSITY_CHOICES, 
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text="Select all academic bodies your institution is affiliated with."
    )

    website = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.college.edu'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))
    theme_color = forms.CharField(max_length=7, initial='#3b82f6', widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}))
    verification_document = forms.FileField(widget=forms.FileInput(attrs={'class': 'form-control'}))
    
    # Admin user details
    admin_email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'admin@college.edu'}))
    admin_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))

    def clean_admin_email(self):
        email = self.cleaned_data.get('admin_email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("User with this email already exists.")
        return email
