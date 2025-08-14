from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from django.utils.html import format_html

from .models import CustomUser

# Register your models here.

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('username',)
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            ),
            'classes': ('collapse',)
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'first_name',
                'last_name',
                'password1',
                'password2'
            ),
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff'),
            'classes': ('collapse',)
        }),
    )
    list_display = [
        'username',
        'email',
        'first_name',
        'last_name',
        'is_active',
        'is_staff',
        'date_joined',
        'last_login',
        'account_status'
    ]

    list_filter = [
        'is_active',
        'is_staff',
        'is_superuser',
        'date_joined',
        'last_login'
    ]

    search_fields = [
        'username',
        'email',
        'first_name',
        'last_name'
    ]

    ordering = ['-date_joined']

    def account_status(self, obj):
        """Display account status with color coding"""
        if obj.is_active:
            if obj.last_login:
                return format_html(
                    '<span style="color: green; font-weight: bold;">✓ Active</span>'
                )
            else:
                return format_html(
                    '<span style="color: orange; font-weight: bold;">⚠ Never Logged In</span>'
                )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Inactive</span>'
            )
    account_status.short_description = 'Status'
