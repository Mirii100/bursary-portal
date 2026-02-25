from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StudentProfile, Application, ApplicationDocument, Payment, AuditLog, Testimony, DevelopmentProject, BoardMember, BursaryCycle, DownloadableDocument

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'role', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role', 'national_id', 'phone', 'constituency', 'profile_photo')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role', 'national_id', 'phone', 'constituency')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(StudentProfile)
admin.site.register(Application)
admin.site.register(ApplicationDocument)
admin.site.register(Payment)
admin.site.register(AuditLog)
admin.site.register(Testimony)
admin.site.register(DevelopmentProject)
admin.site.register(BoardMember)
admin.site.register(BursaryCycle)
admin.site.register(DownloadableDocument)
