from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.users.models import User, Certification


class CommaSeparatedWidget(forms.TextInput):
    """Renders a JSONField list as comma-separated text for easy editing."""
    def format_value(self, value):
        if isinstance(value, list):
            return ', '.join(str(v) for v in value)
        return value or ''

    def value_from_datadict(self, data, files, name):
        raw = super().value_from_datadict(data, files, name)
        if raw is None:
            return []
        return [item.strip() for item in raw.split(',') if item.strip()]


class UserAdminForm(forms.ModelForm):
    skills = forms.CharField(
        widget=CommaSeparatedWidget(attrs={'style': 'width:500px', 'placeholder': 'ex: Saúde Pública, Gestão de Projectos, M&E'}),
        required=False,
        help_text='Separados por vírgula',
    )
    languages = forms.CharField(
        widget=CommaSeparatedWidget(attrs={'style': 'width:500px', 'placeholder': 'ex: Português, Inglês, Francês'}),
        required=False,
        help_text='Separados por vírgula',
    )

    class Meta:
        model = User
        fields = '__all__'

    def clean_skills(self):
        val = self.cleaned_data.get('skills', '')
        if isinstance(val, list):
            return val
        return [s.strip() for s in val.split(',') if s.strip()]

    def clean_languages(self):
        val = self.cleaned_data.get('languages', '')
        if isinstance(val, list):
            return val
        return [s.strip() for s in val.split(',') if s.strip()]


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    form = UserAdminForm
    list_display = ['email', 'get_full_name', 'role', 'availability', 'is_active', 'date_joined']
    list_filter = ['role', 'availability', 'is_active', 'is_staff']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-date_joined']
    readonly_fields = ['date_joined', 'last_login']

    fieldsets = (
        ('Identificação', {
            'fields': ('email', 'username', 'first_name', 'last_name', 'password')
        }),
        ('Perfil', {
            'fields': ('role', 'availability', 'bio', 'avatar', 'skills', 'languages')
        }),
        ('Permissões', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        ('Datas', {
            'fields': ('date_joined', 'last_login'),
            'classes': ('collapse',),
        }),
    )

    add_fieldsets = (
        ('Identificação', {
            'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2')
        }),
        ('Perfil', {
            'fields': ('role', 'availability', 'skills', 'languages')
        }),
    )

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return self.fieldsets

    def get_form(self, request, obj=None, **kwargs):
        if not obj:
            kwargs['fields'] = [
                'email', 'username', 'first_name', 'last_name',
                'password1', 'password2', 'role', 'availability', 'skills', 'languages'
            ]
        return super().get_form(request, obj, **kwargs)


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ['name', 'issuer', 'user', 'issued_date', 'verified']
    list_filter = ['verified']
    search_fields = ['name', 'issuer', 'user__email']
