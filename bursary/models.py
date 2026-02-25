from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('committee', 'Committee Member'),
        ('admin', 'MP Office Admin'),
        ('super_admin', 'Super Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student', db_index=True)
    email = models.EmailField(unique=True)
    national_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    constituency = models.CharField(max_length=100, null=True, blank=True)
    profile_photo = models.ImageField(upload_to='profiles/', null=True, blank=True)

    def is_committee(self):
        return self.role == 'committee' or self.is_superuser

    def is_mp_admin(self):
        return self.role == 'admin' or self.is_superuser

    @property
    def profile_completion(self):
        if self.role != 'student':
            return 100
        
        fields_to_check = [
            self.first_name, self.last_name, self.email, self.phone, self.national_id, self.profile_photo
        ]
        filled = sum(1 for f in fields_to_check if f)
        total = len(fields_to_check)
        
        profile = getattr(self, 'student_profile', None)
        if profile:
            profile_fields = [
                profile.school_name, profile.admission_number, profile.county, 
                profile.constituency, profile.ward, profile.location, 
                profile.sub_location, profile.guardian_name, profile.guardian_phone,
                profile.guardian_id_number, profile.guardian_id_copy
            ]
            filled += sum(1 for f in profile_fields if f)
            total += len(profile_fields)
        else:
            total += 11
            
        return int((filled / total) * 100)

class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    school_name = models.CharField(max_length=255)
    admission_number = models.CharField(max_length=50)
    guardian_name = models.CharField(max_length=255, default="")
    guardian_phone = models.CharField(max_length=15, default="")
    guardian_id_number = models.CharField(max_length=20, default="")
    guardian_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    household_size = models.IntegerField(default=1)
    guardian_id_copy = models.FileField(upload_to='documents/guardian_ids/', null=True, blank=True)
    
    # Residency Details (Now Mandatory)
    county = models.CharField(max_length=100, default="")
    constituency = models.CharField(max_length=100, default="")
    ward = models.CharField(max_length=100, default="")
    location = models.CharField(max_length=100, default="")
    sub_location = models.CharField(max_length=100, default="")

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.school_name}"

class Application(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('recommended', 'Recommended by Committee'),
        ('approved', 'Approved for Disbursement'),
        ('rejected', 'Rejected'),
        ('paid', 'Funds Disbursed'),
    )
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    academic_year = models.CharField(max_length=20, db_index=True) # e.g., "2025/2026"
    amount_requested = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(1000), MaxValueValidator(50000)]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    score = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    committee_comments = models.TextField(blank=True, null=True)
    admin_comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'academic_year') # Smart Validation: One per year

    def __str__(self):
        return f"{self.student.username} - {self.academic_year} ({self.status})"

class ApplicationDocument(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='document_bundle')
    student_id_card = models.FileField(upload_to='documents/student_ids/', help_text="Mandatory: Valid Student ID")
    fee_structure = models.FileField(upload_to='documents/fee_structures/', help_text="Mandatory: Official Fee Structure")
    admission_letter = models.FileField(upload_to='documents/admission_letters/', null=True, blank=True, help_text="Optional: For first-time applicants")
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Payment(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='payment_record')
    amount_awarded = models.DecimalField(max_digits=12, decimal_places=2)
    payment_reference = models.CharField(max_length=100, unique=True)
    date_paid = models.DateTimeField(auto_now_add=True)

class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    details = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

class DevelopmentProject(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='development_projects/', null=True, blank=True)
    estimated_cost = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=50, choices=(('proposed', 'Proposed'), ('ongoing', 'In Progress'), ('completed', 'Completed')))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Testimony(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    is_featured = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Testimonies"

    def __str__(self):
        return f"Testimony by {self.user.username}"

class BoardMember(models.Model):
    STATUS_CHOICES = (('serving', 'Serving'), ('previous', 'Previous'))
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    photo = models.ImageField(upload_to='board/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='serving')
    period = models.CharField(max_length=100, help_text="e.g. 2022 - 2027")

    def __str__(self):
        return f"{self.name} ({self.status})"

class BursaryCycle(models.Model):
    year = models.CharField(max_length=20, default="", db_index=True)
    planned_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Cycle {self.year} (Budget: {self.planned_budget})"

class DownloadableDocument(models.Model):
    CATEGORY_CHOICES = (
        ('guide', 'Student Guide'),
        ('form', 'Official Form'),
        ('report', 'Public Report'),
        ('policy', 'Policy Document'),
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='resources/')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='guide')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    version = models.CharField(max_length=20, default="1.0")
    download_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title
