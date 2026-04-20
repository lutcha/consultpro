from django.contrib import admin
from apps.users.models import User, Certification


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'username', 'first_name', 'last_name', 'role', 'availability']
    list_filter = ['role', 'availability']
    search_fields = ['email', 'username', 'first_name', 'last_name']


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ['name', 'issuer', 'user', 'issued_date', 'verified']
    list_filter = ['verified']
    search_fields = ['name', 'issuer']
