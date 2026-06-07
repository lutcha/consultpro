import uuid
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = [
        ('consultant', 'Consultor'),
        ('manager', 'Gestor'),
        ('admin', 'Administrador'),
    ]
    AVAILABILITY_CHOICES = [
        ('available', 'Disponivel'),
        ('busy', 'Ocupado'),
        ('unavailable', 'Indisponivel'),
    ]

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='consultant')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    skills = models.JSONField(default=list)
    languages = models.JSONField(default=list)
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='available')
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True)
    years_experience = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']


class UserInvitation(models.Model):
    ROLE_CHOICES = User.ROLE_CHOICES
    TENANT_ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('consultant', 'Consultant'),
        ('viewer', 'Viewer'),
    ]

    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='consultant')
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='user_invitations',
    )
    tenant_role = models.CharField(max_length=20, choices=TENANT_ROLE_CHOICES, default='consultant')
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_invitations',
    )
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Invitation({self.email}, {self.role})"

    @classmethod
    def create_for(cls, email, role, invited_by, days_valid=7, tenant=None, tenant_role='consultant'):
        return cls.objects.create(
            email=email,
            role=role,
            tenant=tenant,
            tenant_role=tenant_role,
            invited_by=invited_by,
            expires_at=timezone.now() + timedelta(days=days_valid),
        )

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired


class Certification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certifications')
    name = models.CharField(max_length=200)
    issuer = models.CharField(max_length=200)
    issued_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    document = models.FileField(upload_to='certifications/', null=True, blank=True)
    verified = models.BooleanField(default=False)


class ConsultantProfile(models.Model):
    """Extended profile for consultants with professional details."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='consultant_profile'
    )
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='USD')
    specializations = models.JSONField(default=list)
    education = models.TextField(blank=True)
    linkedin_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    cv_document = models.FileField(upload_to='consultants/cv/', null=True, blank=True)
    is_available_for_hire = models.BooleanField(default=True)
    total_projects_completed = models.PositiveIntegerField(default=0)
    total_proposals_won = models.PositiveIntegerField(default=0)
    performance_rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=0,
        help_text='Rating from 0.00 to 5.00'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-performance_rating', '-total_projects_completed']

    def __str__(self):
        return f"Consultant Profile: {self.user.get_full_name() or self.user.username}"
