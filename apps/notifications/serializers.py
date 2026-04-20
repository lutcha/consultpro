from rest_framework import serializers

from apps.users.models import User

from .models import ActivityLog, Notification


class ActivityLogUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'avatar']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id',
            'user',
            'type',
            'title',
            'message',
            'action_label',
            'action_url',
            'read',
            'created_at',
        ]


class ActivityLogSerializer(serializers.ModelSerializer):
    user = ActivityLogUserSerializer(read_only=True)

    class Meta:
        model = ActivityLog
        fields = [
            'id',
            'user',
            'type',
            'description',
            'metadata',
            'created_at',
        ]
