from django.db import models
from django.utils.text import slugify

class College(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    logo = models.ImageField(upload_to='college_logos/', null=True, blank=True)
    theme_color = models.CharField(max_length=7, default='#3b82f6')
    address = models.TextField()
    contact_email = models.EmailField()
    phone_number = models.CharField(max_length=15, blank=True)
    district = models.CharField(max_length=100, blank=True)
    university_affiliation = models.CharField(max_length=500, blank=True, help_text="Comma-separated list of affiliated universities.")
    description = models.TextField(blank=True, help_text="Briefly describe your institution.")
    established_year = models.PositiveIntegerField(null=True, blank=True)
    
    # Verification Details
    registration_number = models.CharField(max_length=100, unique=True, null=True)
    website = models.URLField(null=True, blank=True)
    verification_document = models.FileField(upload_to='verification_docs/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class CollegeImage(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='college_gallery/')
    caption = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.college.name}"

class CollegeAchievement(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='achievements')
    title = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.college.name}"
