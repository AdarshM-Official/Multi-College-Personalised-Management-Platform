from django.db import models
from django.conf import settings
from colleges.models import College

class TenantModel(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Department(TenantModel):
    CATEGORY_CHOICES = (('UG', 'Undergraduate'), ('PG', 'Postgraduate'))
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=2, choices=CATEGORY_CHOICES, default='UG')
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.college.name})"

class Specialization(TenantModel):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='specializations')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.department.name})"

class TeacherProfile(TenantModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teacher_profile')
    profile_photo = models.ImageField(upload_to='teachers/photos/', null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    specialization = models.ForeignKey(Specialization, on_delete=models.SET_NULL, null=True, blank=True)
    qualification = models.CharField(max_length=255)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"Teacher: {self.user.get_full_name()}"

class HODProfile(TenantModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hod_profile')
    profile_photo = models.ImageField(upload_to='hods/photos/', null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    department = models.OneToOneField(Department, on_delete=models.SET_NULL, null=True, related_name='hod_profile')

    def __str__(self):
        return f"HOD: {self.user.get_full_name()}"

class StudentProfile(TenantModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    profile_photo = models.ImageField(upload_to='students/photos/', null=True, blank=True)
    university_reg_number = models.CharField(max_length=50, blank=True)
    roll_number = models.CharField(max_length=50) # Class Roll Number
    phone_number = models.CharField(max_length=15, blank=True)
    father_name = models.CharField(max_length=100, blank=True)
    mother_name = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Marksheets
    ug_marklist = models.FileField(upload_to='students/marks/ug/', null=True, blank=True)
    plus_two_marklist = models.FileField(upload_to='students/marks/plustwo/', null=True, blank=True)
    
    last_passout_year = models.IntegerField(null=True, blank=True)
    
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    specialization = models.ForeignKey(Specialization, on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def age(self):
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None

    def __str__(self):
        return f"Student: {self.user.get_full_name()} ({self.roll_number})"

class Attendance(TenantModel):
    STATUS_CHOICES = (('PRESENT', 'Present'), ('ABSENT', 'Absent'), ('LATE', 'Late'))
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

class Assignment(TenantModel):
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='assignments/')
    deadline = models.DateTimeField()

    def __str__(self):
        return self.title

class Submission(TenantModel):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    file = models.FileField(upload_to='submissions/')
    marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

class Announcement(TenantModel):
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_global = models.BooleanField(default=False) # Global for all in college
    target_roles = models.CharField(max_length=100, default='ALL') # ALL, TEACHERS, STUDENTS

    def __str__(self):
        return self.title

class TimeTable(TenantModel):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='timetables')
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='timetables/')
    uploaded_by = models.ForeignKey('HODProfile', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.title

class ExamNotification(TenantModel):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='exam_notifications')
    title = models.CharField(max_length=255)
    description = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)
    exam_date = models.DateField(null=True, blank=True)
    posted_by = models.ForeignKey('HODProfile', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.title

class PlatformNotification(models.Model):
    """Notification sent by Super Admin to specific colleges or all."""
    college = models.ForeignKey(College, on_delete=models.CASCADE, null=True, blank=True) # NULL means all colleges
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.title
