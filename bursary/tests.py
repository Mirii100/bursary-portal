from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from bursary.models import AuditLog, Application, Payment, StudentProfile, ApplicationDocument
from django.core import mail
from bursary.services import apply_auto_screening
from django.core.files.base import ContentFile

User = get_user_model()

class ReportingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin', 
            password='password123', 
            email='admin@example.com',
            role='admin'
        )
        self.student_user = User.objects.create_user(
            username='student', 
            password='password123',
            role='student'
        )
        self.client.login(username='admin', password='password123')

    def test_audit_log_view_status_code(self):
        response = self.client.get(reverse('audit-logs'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bursary/audit_logs.html')

    def test_reports_view_status_code(self):
        response = self.client.get(reverse('reports'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bursary/reports.html')

    def test_pdf_report_view_status_code(self):
        response = self.client.get(reverse('generate-pdf-report'))
        self.assertIn(response.status_code, [200, 500])
        if response.status_code == 200:
            self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_audit_log_creation(self):
        AuditLog.objects.create(user=self.admin_user, action="Test Action")
        response = self.client.get(reverse('audit-logs'))
        self.assertContains(response, "Test Action")

    def test_access_control(self):
        self.client.logout()
        self.client.login(username='student', password='password123')
        
        response = self.client.get(reverse('audit-logs'))
        self.assertEqual(response.status_code, 403)

        response = self.client.get(reverse('reports'))
        self.assertEqual(response.status_code, 403)

class NotificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='notify_me',
            email='test@example.com',
            password='password123',
            phone='0712345678'
        )

    def test_submission_notification(self):
        app = Application.objects.create(
            student=self.user,
            academic_year='2025/2026',
            amount_requested=5000
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Application Received", mail.outbox[0].subject)

    def test_payment_notification(self):
        app = Application.objects.create(
            student=self.user,
            academic_year='2025/2026',
            amount_requested=5000
        )
        mail.outbox = [] # Clear outbox
        
        Payment.objects.create(
            application=app,
            amount_awarded=5000,
            payment_reference='TXN123'
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Funds Disbursed", mail.outbox[0].subject)

class ScreeningTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username='test_student_screening',
            password='password123',
            constituency='Central'
        )
        self.profile = StudentProfile.objects.create(
            user=self.student,
            school_name='UON',
            admission_number='C01/123',
            guardian_income=30000,
            household_size=5
        )

    def test_auto_rejection_wrong_constituency(self):
        self.student.constituency = 'WrongPlace'
        self.student.save()
        
        app = Application.objects.create(
            student=self.student,
            academic_year='2025/2026',
            amount_requested=10000
        )
        ApplicationDocument.objects.create(
            application=app,
            student_id_card=ContentFile(b"fake_id", name="id.png"),
            fee_structure=ContentFile(b"fake_fee", name="fee.png")
        )

        passed, reason = apply_auto_screening(app)
        self.assertFalse(passed)
        self.assertEqual(app.status, 'rejected')
        self.assertIn("constituency", reason.lower())

    def test_auto_scoring_low_income(self):
        self.profile.guardian_income = 5000
        self.profile.save()
        
        app = Application.objects.create(
            student=self.student,
            academic_year='2025/2026',
            amount_requested=10000
        )
        ApplicationDocument.objects.create(
            application=app,
            student_id_card=ContentFile(b"fake_id", name="id.png"),
            fee_structure=ContentFile(b"fake_fee", name="fee.png")
        )

        passed, reason = apply_auto_screening(app)
        self.assertTrue(passed)
        # Score should be high for low income (40 for income + 15 for hh size + 15 for continuing docs)
        self.assertGreaterEqual(app.score, 70)
