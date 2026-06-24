from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    ordering = ('email',)
    list_display = ('email', 'username', 'role', 'phone', 'is_staff', 'is_active', 'created_at')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('email', 'username', 'phone')
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_login', 'date_joined')

    fieldsets = (
        (None, {'fields': ('id', 'email', 'password')}),
        ('個人資訊', {'fields': ('username', 'first_name', 'last_name', 'phone', 'role')}),
        (
            '權限',
            {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')},
        ),
        ('時間戳', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('email', 'username', 'password1', 'password2', 'role'),
            },
        ),
    )
