import csv
from django.http import HttpResponse
from .models import Application, Payment, AuditLog
from django.utils import timezone
from openpyxl import Workbook

def export_applications_csv(queryset, filename="bursary_list"):
    # ... (existing code)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}_{timezone.now().date()}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Student Name', 'National ID', 'School', 'Admission No', 'Amount Allocated', 'Status', 'Date Applied'])

    for app in queryset:
        writer.writerow([
            app.student.get_full_name(),
            app.student.national_id,
            app.student.student_profile.school_name,
            app.student.student_profile.admission_number,
            app.amount_requested,
            app.get_status_display(),
            app.created_at.strftime("%Y-%m-%d"),
        ])

    return response

def export_applications_excel(queryset, filename="bursary_list"):
    wb = Workbook()
    ws = wb.active
    ws.title = "Applications"

    # Header
    headers = ['Student Name', 'National ID', 'School', 'Admission No', 'Amount Allocated', 'Status', 'Date Applied']
    ws.append(headers)

    for app in queryset:
        ws.append([
            app.student.get_full_name(),
            app.student.national_id,
            app.student.student_profile.school_name,
            app.student.student_profile.admission_number,
            float(app.amount_requested),
            app.get_status_display(),
            app.created_at.strftime("%Y-%m-%d"),
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}_{timezone.now().date()}.xlsx"'
    wb.save(response)
    return response

