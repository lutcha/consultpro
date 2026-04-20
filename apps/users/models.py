from django.contrib.auth.models import AbstractUser
from django.db import models


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


class Certification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certifications')
    name = models.CharField(max_length=200)
    issuer = models.CharField(max_length=200)
    issued_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    document = models.FileField(upload_to='certifications/', null=True, blank=True)
    verified = models.BooleanField(default=False)
