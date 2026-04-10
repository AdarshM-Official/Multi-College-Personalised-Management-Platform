from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from colleges.models import College

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'SUPER_ADMIN')
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    ROLES = (
        ('SUPER_ADMIN', 'Super Admin'),
        ('COLLEGE_ADMIN', 'College Admin'),
        ('TEACHER', 'Teacher'),
        ('STUDENT', 'Student'),
    )
    
    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLES, default='STUDENT')
    college = models.ForeignKey(College, on_delete=models.CASCADE, null=True, blank=True, related_name='users')
    
    # Required for custom user
    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
