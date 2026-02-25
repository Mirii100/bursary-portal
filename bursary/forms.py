from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, StudentProfile, Application, ApplicationDocument, Testimony, DevelopmentProject

class UserRegistrationForm(UserCreationForm):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('committee', 'Committee Member'),
        ('admin', 'MP Office Admin'),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True, widget=forms.Select(attrs={'class': 'form-select'}))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address (Used for Login)'}))
    phone = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}))
    national_id = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'National ID No.'}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('role', 'first_name', 'last_name', 'email', 'phone', 'national_id')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data['phone']
        user.national_id = self.cleaned_data['national_id']
        
        # Professional Staff Permissions
        if user.role in ['admin', 'committee']:
            user.is_staff = True
            
        if commit:
            user.save()
        return user

class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'national_id', 'profile_photo']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

from .constants import KENYAN_SCHOOLS, KENYAN_COUNTIES, KENYAN_CONSTITUENCIES, SAMPLE_WARDS, SAMPLE_LOCATIONS, SAMPLE_SUBLOCATIONS

class StudentProfileForm(forms.ModelForm):
    guardian_id_copy = forms.FileField(required=True, widget=forms.FileInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = StudentProfile
        fields = [
            'school_name', 'admission_number', 
            'county', 'constituency', 'ward', 'location', 'sub_location',
            'guardian_name', 'guardian_phone', 'guardian_id_number', 'guardian_income', 'household_size',
            'guardian_id_copy'
        ]
        widgets = {
            'school_name': forms.Select(choices=[('', 'Select Your School')] + KENYAN_SCHOOLS, attrs={'class': 'form-select'}),
            'admission_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter admission number'}),
            
            # Residency Dropdowns
            'county': forms.Select(choices=[('', 'Select County')] + KENYAN_COUNTIES, attrs={'class': 'form-select'}),
            'constituency': forms.Select(choices=[('', 'Select Constituency')] + KENYAN_CONSTITUENCIES, attrs={'class': 'form-select'}),
            'ward': forms.Select(choices=[('', 'Select Ward')] + SAMPLE_WARDS, attrs={'class': 'form-select'}),
            'location': forms.Select(choices=[('', 'Select Location')] + SAMPLE_LOCATIONS, attrs={'class': 'form-select'}),
            'sub_location': forms.Select(choices=[('', 'Select Sub-Location')] + SAMPLE_SUBLOCATIONS, attrs={'class': 'form-select'}),
            
            'guardian_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name of Parent/Guardian'}),
            'guardian_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Guardian Phone Number'}),
            'guardian_id_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Guardian National ID'}),
            'guardian_income': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Monthly income'}),
            'household_size': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Number of members'}),
        }

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['academic_year', 'amount_requested']
        widgets = {
            'academic_year': forms.Select(choices=[('', 'Select Year'), ('2024/2025', '2024/2025'), ('2025/2026', '2025/2026')], attrs={'class': 'form-control'}),
            'amount_requested': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max KES 50,000'}),
        }

class ApplicationDocumentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        is_continuing = kwargs.pop('is_continuing', False)
        super().__init__(*args, **kwargs)
        if is_continuing:
            self.fields['student_id_card'].required = False
            self.fields['student_id_card'].help_text = "Reusing previously uploaded ID. Upload only if you wish to update it."

    class Meta:
        model = ApplicationDocument
        fields = ['student_id_card', 'fee_structure', 'admission_letter']
        widgets = {
            'student_id_card': forms.FileInput(attrs={'class': 'form-control'}),
            'fee_structure': forms.FileInput(attrs={'class': 'form-control'}),
            'admission_letter': forms.FileInput(attrs={'class': 'form-control'}),
        }

class CommitteeReviewForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['score', 'committee_comments']
        widgets = {
            'score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'committee_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class TestimonyForm(forms.ModelForm):
    class Meta:
        model = Testimony
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Share your experience with the bursary system...'}),
        }

class DevelopmentProjectForm(forms.ModelForm):
    class Meta:
        model = DevelopmentProject
        fields = ['title', 'description', 'image', 'estimated_cost', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'estimated_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
