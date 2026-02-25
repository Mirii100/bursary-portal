from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    
    # Profile & Security
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('profile/edit/', views.UserProfileUpdateView.as_view(), name='user-profile-update'),
    path('password-change/', auth_views.PasswordChangeView.as_view(template_name='bursary/password_change.html'), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='bursary/password_change_done.html'), name='password_change_done'),

    # Password Reset URLs
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('profile-setup/', views.ProfileSetupView.as_view(), name='profile-setup'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # Application
    path('apply/', views.ApplyView.as_view(), name='apply'),
    path('apply/edit/<int:pk>/', views.EditApplicationView.as_view(), name='edit-application'),
    path('download-award/<int:pk>/', views.DownloadAwardLetterView.as_view(), name='download-award'),
    
    # Committee
    path('committee/dashboard/', views.CommitteeDashboardView.as_view(), name='committee-dashboard'),
    path('committee/review/<int:pk>/', views.ReviewApplicationView.as_view(), name='review-application'),
    path('staff/application/<int:pk>/', views.StudentApplicationDetailView.as_view(), name='student-application-detail'),
    
    # New Pages
    path('about/', views.AboutView.as_view(), name='about'),
    path('gallery/', views.GalleryView.as_view(), name='gallery'),
    path('downloads/', views.DownloadsView.as_view(), name='downloads'),
    path('downloads/serve/<int:pk>/', views.DownloadFileView.as_view(), name='serve-document'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('transparency/disbursements/', views.PublicDisbursementView.as_view(), name='public-disbursements'),
    path('development/', views.DevelopmentListView.as_view(), name='development-projects'),
    path('development/new/', views.DevelopmentCreateView.as_view(), name='development-create'),
    path('development/edit/<int:pk>/', views.DevelopmentUpdateView.as_view(), name='development-update'),
    path('testimony/new/', views.TestimonyCreateView.as_view(), name='submit-testimony'),
    
    # Staff/Admin Unified Views
    path('staff/applications/', views.StaffApplicationListView.as_view(), name='staff-application-list'),
    path('staff/finances/', views.FinancialHistoryView.as_view(), name='financial-history'),
    
    # Admin
    path('admin-office/dashboard/', views.AdminDashboardView.as_view(), name='admin-dashboard'),
    path('admin-office/export/', views.ExportApplicationsView.as_view(), name='export-applications'),
    path('admin-office/export/excel/', views.ExportApplicationsExcelView.as_view(), name='export-applications-excel'),
    path('admin-office/audit-logs/', views.AuditLogListView.as_view(), name='audit-logs'),
    path('admin-office/reports/', views.ReportsView.as_view(), name='reports'),
    path('admin-office/reports/pdf/', views.PDFReportView.as_view(), name='generate-pdf-report'),
    path('admin-office/disburse/<int:pk>/', views.DisburseFundsView.as_view(), name='disburse-funds'),
    path('admin-office/bulk-disburse/', views.BulkDisburseView.as_view(), name='bulk-disburse'),
]
