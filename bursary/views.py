from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView
from django.contrib import messages
from django.views.generic import CreateView, TemplateView, ListView, DetailView, UpdateView, View
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import Sum, Count, Avg
from django.template.loader import render_to_string
from django.http import HttpResponse
from .utils import export_applications_csv, export_applications_excel

from .forms import UserRegistrationForm, StudentProfileForm, ApplicationForm, ApplicationDocumentForm, CommitteeReviewForm, UserProfileUpdateForm, TestimonyForm, DevelopmentProjectForm
from .models import User, StudentProfile, Application, ApplicationDocument, AuditLog, Payment, DevelopmentProject, Testimony, BoardMember, BursaryCycle, DownloadableDocument
import uuid

class HomeView(TemplateView):
    template_name = 'bursary/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Scalable Fetching: Optimization with select_related
        context['testimonies'] = Testimony.objects.select_related('user', 'user__student_profile').order_by('-is_featured', '-created_at')[:6]
        return context

class AboutView(TemplateView):
    template_name = 'bursary/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['serving_board'] = BoardMember.objects.filter(status='serving')
        context['previous_board'] = BoardMember.objects.filter(status='previous')
        return context

class GalleryView(TemplateView):
    template_name = 'bursary/gallery.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['serving_board'] = BoardMember.objects.filter(status='serving')
        return context

class DownloadsView(ListView):
    model = DownloadableDocument
    template_name = 'bursary/downloads.html'
    context_object_name = 'documents'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Group documents by category for professional layout
        docs = DownloadableDocument.objects.all()
        context['guides'] = docs.filter(category='guide')
        context['forms'] = docs.filter(category='form')
        context['reports'] = docs.filter(category='report')
        context['policies'] = docs.filter(category='policy')
        return context

class DownloadFileView(View):
    """Increments count and serves file for preview/download."""
    def get(self, request, pk, *args, **kwargs):
        doc = get_object_or_404(DownloadableDocument, pk=pk)
        doc.download_count += 1
        doc.save()
        
        # Open file and serve
        file_handle = doc.file.open()
        response = HttpResponse(file_handle.read(), content_type='application/pdf')
        # 'inline' allows browser to preview, 'attachment' forces download
        response['Content-Disposition'] = f'inline; filename="{doc.file.name}"'
        return response

class ContactView(TemplateView):
    template_name = 'bursary/contact.html'

    def post(self, request, *args, **kwargs):
        messages.success(request, "Your message has been sent successfully! Our team will get back to you soon.")
        return redirect('contact')

class PublicDisbursementView(TemplateView):
    template_name = 'bursary/public_disbursement.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_constituency_disbursed'] = Payment.objects.aggregate(Sum('amount_awarded'))['amount_awarded__sum'] or 0
        context['total_students_helped'] = Payment.objects.count()
        context['active_cycles'] = BursaryCycle.objects.filter(is_active=True).order_by('-year')
        history = Application.objects.filter(status='paid').values('academic_year').annotate(
            total_students=Count('id'),
            total_disbursed=Sum('payment_record__amount_awarded')
        ).order_by('-academic_year')
        context['financial_history'] = history
        return context

class RegisterView(CreateView):
    template_name = 'bursary/register.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Registration successful! Welcome, {self.object.get_full_name()}. Please log in to continue.")
        return response

class ProfileSetupView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = StudentProfile
    form_class = StudentProfileForm
    template_name = 'bursary/profile_setup.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        return self.request.user.role == 'student'

    def get_object(self, queryset=None):
        profile, created = StudentProfile.objects.get_or_create(user=self.request.user, defaults={
            'guardian_income': 0,
            'household_size': 1
        })
        return profile

    def form_valid(self, form):
        messages.success(self.request, "Profile updated and compliant with current requirements!")
        return super().form_valid(form)

class UserLoginView(LoginView):
    template_name = 'bursary/login.html'
    
    def get_success_url(self):
        user = self.request.user
        if user.role == 'committee':
            return reverse_lazy('committee-dashboard')
        elif user.role == 'admin':
            return reverse_lazy('admin-dashboard')
        return reverse_lazy('dashboard')

class UserProfileView(LoginRequiredMixin, DetailView):
    template_name = 'bursary/profile.html'
    context_object_name = 'target_user'

    def get_object(self):
        return self.request.user

class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileUpdateForm
    template_name = 'bursary/profile_update.html'
    success_url = reverse_lazy('user-profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Profile updated successfully!")
        return super().form_valid(form)

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'bursary/dashboard.html'

    def get(self, request, *args, **kwargs):
        user = request.user
        if user.role == 'student':
            profile = getattr(user, 'student_profile', None)
            is_compliant = profile and all([profile.ward, profile.guardian_name, profile.guardian_id_copy])
            if not is_compliant:
                messages.info(request, "New system requirements detected. Please update your profile details to proceed.")
                return redirect('profile-setup')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.role == 'student':
            context['total_awarded'] = Payment.objects.filter(application__student=user).aggregate(Sum('amount_awarded'))['amount_awarded__sum'] or 0
            context['constituency_total'] = Payment.objects.aggregate(Sum('amount_awarded'))['amount_awarded__sum'] or 0
            context['profile_completion'] = user.profile_completion
            context['my_applications'] = user.applications.all().order_by('-created_at')
        return context

class DevelopmentListView(ListView):
    model = DevelopmentProject
    template_name = 'bursary/development_list.html'
    context_object_name = 'projects'

class DevelopmentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = DevelopmentProject
    form_class = DevelopmentProjectForm
    template_name = 'bursary/development_form.html'
    success_url = reverse_lazy('development-projects')
    raise_exception = True

    def test_func(self):
        return self.request.user.role == 'admin' or self.request.user.is_superuser

class DevelopmentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = DevelopmentProject
    form_class = DevelopmentProjectForm
    template_name = 'bursary/development_form.html'
    success_url = reverse_lazy('development-projects')
    raise_exception = True

    def test_func(self):
        return self.request.user.role == 'admin' or self.request.user.is_superuser

class TestimonyCreateView(LoginRequiredMixin, CreateView):
    model = Testimony
    form_class = TestimonyForm
    template_name = 'bursary/testimony_form.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Thank you for your testimony! It has been submitted for review.")
        return super().form_valid(form)

from .services import apply_auto_screening

class ApplyView(LoginRequiredMixin, TemplateView):
    template_name = 'bursary/apply.html'

    def get_self_context(self, request):
        is_continuing = Application.objects.filter(student=request.user).exists()
        return {
            'is_continuing': is_continuing,
            'app_form': ApplicationForm(),
            'doc_form': ApplicationDocumentForm(is_continuing=is_continuing)
        }

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_self_context(request))

    def post(self, request, *args, **kwargs):
        is_continuing = Application.objects.filter(student=request.user).exists()
        app_form = ApplicationForm(request.POST)
        doc_form = ApplicationDocumentForm(request.POST, request.FILES, is_continuing=is_continuing)

        if app_form.is_valid() and doc_form.is_valid():
            try:
                with transaction.atomic():
                    academic_year = app_form.cleaned_data['academic_year']
                    if Application.objects.filter(student=request.user, academic_year=academic_year).exists():
                        messages.error(request, f"You have already applied for the {academic_year} academic year.")
                        return render(request, self.template_name, {
                            'app_form': app_form, 
                            'doc_form': doc_form,
                            'is_continuing': is_continuing
                        })

                    application = app_form.save(commit=False)
                    application.student = request.user
                    application.save()

                    documents = doc_form.save(commit=False)
                    documents.application = application
                    
                    if is_continuing:
                        last_app = Application.objects.filter(student=request.user).exclude(pk=application.pk).order_by('-created_at').first()
                        if last_app and hasattr(last_app, 'document_bundle'):
                            last_docs = last_app.document_bundle
                            if not documents.student_id_card:
                                documents.student_id_card = last_docs.student_id_card
                            if not documents.admission_letter:
                                documents.admission_letter = last_docs.admission_letter
                    
                    documents.save()

                    passed, reason = apply_auto_screening(application)
                    
                    if not passed:
                        messages.warning(request, f"System Screening Notification: {reason}")
                        AuditLog.objects.create(user=request.user, action=f"Application auto-rejected for {academic_year}: {reason}")
                        return redirect('dashboard')

                    AuditLog.objects.create(user=request.user, action=f"Submitted application for {academic_year}")
                    messages.success(request, "Application submitted successfully! Our system has verified your initial eligibility.")
                    return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
        
        return render(request, self.template_name, {
            'app_form': app_form, 
            'doc_form': doc_form, 
            'is_continuing': is_continuing
        })

class EditApplicationView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'bursary/apply.html'
    raise_exception = True

    def test_func(self):
        application = get_object_or_404(Application, pk=self.kwargs['pk'])
        return application.student == self.request.user and application.status == 'pending'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application = get_object_or_404(Application, pk=self.kwargs['pk'])
        is_continuing = Application.objects.filter(student=self.request.user).exclude(pk=application.pk).exists()
        
        context['app_form'] = ApplicationForm(instance=application)
        context['doc_form'] = ApplicationDocumentForm(instance=application.document_bundle, is_continuing=is_continuing)
        context['is_editing'] = True
        context['is_continuing'] = is_continuing
        return context

    def post(self, request, *args, **kwargs):
        application = get_object_or_404(Application, pk=self.kwargs['pk'])
        is_continuing = Application.objects.filter(student=request.user).exclude(pk=application.pk).exists()
        
        app_form = ApplicationForm(request.POST, instance=application)
        doc_form = ApplicationDocumentForm(request.POST, request.FILES, instance=application.document_bundle, is_continuing=is_continuing)

        if app_form.is_valid() and doc_form.is_valid():
            try:
                with transaction.atomic():
                    application = app_form.save()
                    documents = doc_form.save()
                    passed, reason = apply_auto_screening(application)
                    
                    if not passed:
                        messages.warning(request, f"Application updated but failed auto-screening: {reason}")
                    else:
                        messages.success(request, "Application updated and verified successfully.")
                    
                    AuditLog.objects.create(user=request.user, action=f"Edited application ID {application.id}")
                    return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
        
        return render(request, self.template_name, {
            'app_form': app_form, 
            'doc_form': doc_form, 
            'is_editing': True, 
            'is_continuing': is_continuing
        })

class CommitteeDashboardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Application
    template_name = 'bursary/committee_dashboard.html'
    context_object_name = 'applications'
    raise_exception = True

    def test_func(self):
        return self.request.user.role in ['committee', 'admin'] or self.request.user.is_superuser

    def get_queryset(self):
        return Application.objects.filter(status='pending').order_by('-score', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_apps = Application.objects.all()
        context['total_apps'] = all_apps.count()
        context['system_auto_rejected'] = all_apps.filter(status='rejected', admin_comments__icontains='AUTO-REJECTION').count()
        return context

class ReviewApplicationView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Application
    form_class = CommitteeReviewForm
    template_name = 'bursary/review_application.html'
    success_url = reverse_lazy('committee-dashboard')
    raise_exception = True

    def test_func(self):
        return self.request.user.role in ['committee', 'admin'] or self.request.user.is_superuser

    def form_valid(self, form):
        form.instance.status = 'recommended'
        messages.success(self.request, "Application reviewed and recommended for approval.")
        AuditLog.objects.create(user=self.request.user, action=f"Reviewed application ID {form.instance.id}")
        return super().form_valid(form)

class StudentApplicationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Application
    template_name = 'bursary/student_detail.html'
    context_object_name = 'application'
    raise_exception = True

    def test_func(self):
        return self.request.user.role in ['committee', 'admin'] or self.request.user.is_superuser

class StaffApplicationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Application
    template_name = 'bursary/staff_application_list.html'
    context_object_name = 'applications'
    paginate_by = 50
    raise_exception = True

    def test_func(self):
        return self.request.user.role in ['admin', 'committee'] or self.request.user.is_superuser

    def get_queryset(self):
        return Application.objects.select_related('student', 'student__student_profile').all().order_by('-created_at')

class FinancialHistoryView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'bursary/financial_history.html'
    raise_exception = True

    def test_func(self):
        return self.request.user.role in ['admin', 'committee'] or self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        history = Application.objects.filter(status='paid').values('academic_year').annotate(
            total_students=Count('id'),
            total_disbursed=Sum('payment_record__amount_awarded')
        ).order_by('-academic_year')
        context['financial_history'] = history
        context['all_payments'] = Payment.objects.all().order_by('-date_paid')
        return context

class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Application
    template_name = 'bursary/admin_dashboard.html'
    context_object_name = 'applications'
    raise_exception = True

    def test_func(self):
        return self.request.user.role == 'admin' or self.request.user.is_superuser

    def get_queryset(self):
        return Application.objects.filter(status='recommended')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_apps = Application.objects.all()
        context['total_apps'] = all_apps.count()
        context['total_approved'] = all_apps.filter(status='approved').count()
        context['total_paid'] = all_apps.filter(status='paid').count()
        context['total_rejected'] = all_apps.filter(status='rejected').count()
        context['system_auto_rejected'] = all_apps.filter(status='rejected', admin_comments__icontains='AUTO-REJECTION').count()
        context['total_budget_used'] = Payment.objects.aggregate(total=Sum('amount_awarded'))['total'] or 0
        context['avg_score'] = all_apps.aggregate(avg=Avg('score'))['avg'] or 0
        return context

class AuditLogListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = AuditLog
    template_name = 'bursary/audit_logs.html'
    context_object_name = 'logs'
    paginate_by = 20
    ordering = ['-timestamp']
    raise_exception = True

    def test_func(self):
        return self.request.user.role == 'admin' or self.request.user.is_superuser

class ReportsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'bursary/reports.html'
    raise_exception = True

    def test_func(self):
        return self.request.user.role == 'admin' or self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_apps = Application.objects.all()
        context['total_apps'] = all_apps.count()
        approved_count = all_apps.filter(status__in=['approved', 'paid']).count()
        context['total_approved'] = approved_count
        context['total_paid'] = all_apps.filter(status='paid').count()
        context['total_budget_used'] = Payment.objects.aggregate(total=Sum('amount_awarded'))['total'] or 0
        context['avg_score'] = all_apps.aggregate(avg=Avg('score'))['avg'] or 0
        context['approval_rate'] = (approved_count / all_apps.count() * 100) if all_apps.count() > 0 else 0
        status_counts = {}
        for status, label in Application.STATUS_CHOICES:
            status_counts[label] = all_apps.filter(status=status).count()
        context['status_counts'] = status_counts
        score_ranges = [0, 0, 0, 0, 0]
        for app in all_apps:
            score = app.score
            if score <= 20: score_ranges[0] += 1
            elif score <= 40: score_ranges[1] += 1
            elif score <= 60: score_ranges[2] += 1
            elif score <= 80: score_ranges[3] += 1
            else: score_ranges[4] += 1
        context['score_distribution'] = score_ranges
        context['recent_payments'] = Payment.objects.select_related('application__student').order_by('-date_paid')[:10]
        return context

class PDFReportView(LoginRequiredMixin, UserPassesTestMixin, View):
    raise_exception = True
    def test_func(self):
        return self.request.user.role == 'admin' or self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        all_apps = Application.objects.all()
        total_apps = all_apps.count()
        total_approved = all_apps.filter(status__in=['approved', 'paid']).count()
        total_budget_used = Payment.objects.aggregate(total=Sum('amount_awarded'))['total'] or 0
        try:
            from fpdf import FPDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, "Alexia's Global Tech System Report", ln=True, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", '', 12)
            pdf.cell(100, 10, f"Total Applications: {total_apps}")
            pdf.ln(8)
            pdf.cell(100, 10, f"Total Approved/Paid: {total_approved}")
            pdf.ln(8)
            pdf.cell(100, 10, f"Total Disbursed: KES {total_budget_used}")
            pdf.ln(15)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(60, 10, "Student", 1)
            pdf.cell(40, 10, "Year", 1)
            pdf.cell(40, 10, "Status", 1)
            pdf.cell(30, 10, "Score", 1)
            pdf.ln()
            pdf.set_font("Arial", '', 9)
            for app in all_apps[:50]:
                pdf.cell(60, 10, str(app.student.get_full_name())[:30], 1)
                pdf.cell(40, 10, str(app.academic_year), 1)
                pdf.cell(40, 10, str(app.get_status_display()), 1)
                pdf.cell(30, 10, str(app.score), 1)
                pdf.ln()
            response = HttpResponse(pdf.output(), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="alexias_global_tech_report.pdf"'
            return response
        except Exception as e:
            return HttpResponse(f"Error generating PDF: {e}", status=500)

class ExportApplicationsView(LoginRequiredMixin, UserPassesTestMixin, View):
    raise_exception = True
    def test_func(self):
        return self.request.user.role == 'admin' or self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        queryset = Application.objects.filter(status__in=['recommended', 'approved', 'paid'])
        AuditLog.objects.create(user=request.user, action="Exported Application List (CSV)")
        return export_applications_csv(queryset)

class ExportApplicationsExcelView(LoginRequiredMixin, UserPassesTestMixin, View):
    raise_exception = True
    def test_func(self):
        return self.request.user.role == 'admin' or self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        queryset = Application.objects.filter(status__in=['recommended', 'approved', 'paid'])
        AuditLog.objects.create(user=request.user, action="Exported Application List (Excel)")
        return export_applications_excel(queryset)

from .mpesa import process_bursary_disbursement

class DisburseFundsView(LoginRequiredMixin, UserPassesTestMixin, View):
    raise_exception = True
    def test_func(self):
        return self.request.user.role == 'admin' or self.request.user.is_superuser

    def post(self, request, pk, *args, **kwargs):
        application = get_object_or_404(Application, pk=pk)
        if hasattr(application, 'payment_record'):
            messages.warning(request, "Funds have already been disbursed for this application.")
            return redirect('admin-dashboard')
        if application.status == 'recommended':
            with transaction.atomic():
                application.status = 'approved'
                application.save()
                success, result = process_bursary_disbursement(application)
                if success:
                    application.status = 'paid'
                    application.save()
                    AuditLog.objects.create(user=request.user, action=f"Disbursed funds (M-Pesa) for App ID {application.id}")
                    messages.success(request, f"Funds successfully disbursed to {application.student.get_full_name()} via M-Pesa. Ref: {result}")
                else:
                    messages.error(request, f"M-Pesa Disbursement failed: {result}")
        else:
            messages.warning(request, "This application is not ready for disbursement.")
        return redirect('admin-dashboard')

class BulkDisburseView(LoginRequiredMixin, UserPassesTestMixin, View):
    raise_exception = True
    def test_func(self):
        return self.request.user.role == 'admin' or self.request.user.is_superuser

    def post(self, request, *args, **kwargs):
        application_ids = request.POST.getlist('selected_applications')
        if not application_ids:
            messages.warning(request, "No applications selected for disbursement.")
            return redirect('admin-dashboard')
        success_count = 0
        fail_count = 0
        for app_id in application_ids:
            application = get_object_or_404(Application, pk=app_id)
            if hasattr(application, 'payment_record') or application.status != 'recommended':
                fail_count += 1
                continue
            try:
                with transaction.atomic():
                    application.status = 'approved'
                    application.save()
                    success, result = process_bursary_disbursement(application)
                    if success:
                        application.status = 'paid'
                        application.save()
                        AuditLog.objects.create(user=request.user, action=f"Bulk Disbursed (M-Pesa) for App ID {application.id}")
                        success_count += 1
                    else:
                        fail_count += 1
            except Exception:
                fail_count += 1
        if success_count > 0:
            messages.success(request, f"Successfully disbursed funds to {success_count} students.")
        if fail_count > 0:
            messages.error(request, f"Failed to disburse to {fail_count} applications. They may have already been paid.")
        return redirect('admin-dashboard')

class DownloadAwardLetterView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        application = get_object_or_404(Application, pk=pk, student=request.user)
        if application.status not in ['approved', 'paid']:
            messages.error(request, "Your application has not been approved yet.")
            return redirect('dashboard')
        return render(request, 'bursary/award_letter.html', {'application': application})
