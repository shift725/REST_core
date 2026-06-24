import uuid_utils.compat as uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class UUIDv7Mixin(models.Model):
    """所有 Model 繼承此類別即可使用 UUIDv7 主鍵"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)

    class Meta:
        abstract = True


class CustomUser(UUIDv7Mixin, AbstractUser):
    """自訂使用者模型，增加額外欄位"""

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(
        max_length=20,
        choices=[
            ('admin', '管理員'),
            ('staff', '員工'),
            ('member', '會員'),
        ],
        default='member',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 使用 email 作為登入帳號
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
