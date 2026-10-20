from django.db import models


class UserAccount(models.Model):
    """Application identity linked to a trusted Django session."""

    ROLE_USER = 'user'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = [
        (ROLE_USER, '사용자'),
        (ROLE_ADMIN, '관리자'),
    ]

    id = models.BigAutoField(primary_key=True, db_column='user_id')
    identity_key = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=150)
    email = models.EmailField(max_length=254, unique=True, null=True, blank=True)
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default=ROLE_USER)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sb_user'
        ordering = ['id']

    def __str__(self):
        return self.email or self.name
