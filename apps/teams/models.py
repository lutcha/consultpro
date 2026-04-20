from django.db import models

from apps.users.models import User


class Team(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(User, related_name='teams', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name
