from .models import Application, AuditLog
from django.conf import settings

class ScreeningService:
    """
    Automated Eligibility & Screening Engine.
    Filters out invalid applications before they reach the Committee.
    """
    
    # Configuration - In a real app, these could be in the database
    MAX_INCOME_THRESHOLD = 150000  # KES
    REQUIRED_CONSTITUENCY = "Central" # Example
    
    @staticmethod
    def screen_application(application):
        """
        Runs a suite of automated checks.
        Returns (is_passed, reason)
        """
        student = application.student
        profile = getattr(student, 'student_profile', None)
        docs = getattr(application, 'document_bundle', None)

        if not profile:
            return False, "Student profile is incomplete."

        # 1. Constituency Check (Crucial for Bursaries)
        if student.constituency and student.constituency.lower() != ScreeningService.REQUIRED_CONSTITUENCY.lower():
            return False, f"This bursary is only for residents of {ScreeningService.REQUIRED_CONSTITUENCY} Constituency."

        # 2. Income Check (Auto-filter high earners)
        if profile.guardian_income > ScreeningService.MAX_INCOME_THRESHOLD:
            return False, "Guardian income exceeds the maximum threshold for this financial aid."

        # 3. Document Integrity Check
        if not docs or not docs.student_id_card or not docs.fee_structure:
            return False, "Mandatory documents (ID Card or Fee Structure) are missing or corrupted."

        # 4. Automated Vulnerability Scoring (The "Smart" Difference)
        # Higher score = More needy
        score = 0
        
        # Income Factor (Max 40 points)
        if profile.guardian_income < 20000: score += 40
        elif profile.guardian_income < 50000: score += 25
        elif profile.guardian_income < 80000: score += 10
        
        # Household Size Factor (Max 30 points)
        if profile.household_size > 6: score += 30
        elif profile.household_size > 4: score += 15
        else: score += 5
        
        # Document Presence Bonus (Max 30 points)
        if docs.admission_letter: score += 30 # First-time applicants get priority
        else: score += 15 # Continuing students

        application.score = score
        application.save()

        return True, "Passed automated screening."

def apply_auto_screening(application):
    """
    Main entry point for screening.
    """
    passed, reason = ScreeningService.screen_application(application)
    
    if not passed:
        application.status = 'rejected'
        application.admin_comments = f"AUTO-REJECTION: {reason}"
        application.save()
        
        # Log the auto-rejection
        AuditLog.objects.create(
            user=None, # System action
            action="System Auto-Rejection",
            details=f"App ID {application.id} rejected: {reason}"
        )
        return False, reason
    
    return True, "Application is eligible for review."
