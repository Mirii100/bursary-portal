from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Application, Payment
from .notifications import send_bursary_notification

@receiver(post_save, sender=Application)
def application_status_changed(sender, instance, created, **kwargs):
    """
    Triggers notifications when an application is created or its status changes.
    """
    if created:
        # Initial submission
        subject = "Bursary Application Received"
        message = f"Hello {instance.student.get_full_name()}, your application for the {instance.academic_year} academic year has been successfully submitted and is pending review."
        send_bursary_notification(instance.student, subject, message)
    else:
        # Check if status has changed (simplified, for a better way use django-model-utils or similar)
        # For this prototype, we'll notify for key transitions
        if instance.status == 'recommended':
            subject = "Application Recommended"
            message = f"Great news! Your application ID {instance.id} has been recommended by the committee for final approval."
            send_bursary_notification(instance.student, subject, message)
        elif instance.status == 'rejected':
            subject = "Application Status Update"
            message = f"We regret to inform you that your application ID {instance.id} was not approved. You can view the reason on the dashboard."
            send_bursary_notification(instance.student, subject, message)

@receiver(post_save, sender=Payment)
def payment_disbursed(sender, instance, created, **kwargs):
    """
    Triggers notification when a payment record is created (funds disbursed).
    """
    if created:
        application = instance.application
        subject = "Funds Disbursed!"
        message = f"Success! Your bursary of KES {instance.amount_awarded} has been disbursed. Payment Reference: {instance.payment_reference}. Please check with your school for fee confirmation."
        send_bursary_notification(application.student, subject, message)
