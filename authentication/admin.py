from django.contrib import admin

from authentication.models import AccountDeletionRequest


@admin.register(AccountDeletionRequest)
class AccountDeletionRequestAdmin(admin.ModelAdmin):
    list_display = (
        'email',
        'status',
        'created_at',
        'confirmed_at',
        'processed_at',
    )
    list_filter = ('status', 'created_at', 'confirmed_at', 'processed_at')
    search_fields = ('email',)
    ordering = ('-created_at',)
    readonly_fields = (
        'id',
        'email',
        'reason',
        'confirmation_token_hash',
        'confirmation_expires_at',
        'confirmed_at',
        'created_at',
        'updated_at',
    )
    fieldsets = (
        ('Solicitação', {
            'fields': ('id', 'email', 'reason', 'status', 'is_active'),
        }),
        ('Confirmação', {
            'fields': (
                'confirmation_expires_at',
                'confirmed_at',
                'confirmation_token_hash',
            ),
        }),
        ('Processamento', {
            'fields': ('processed_at', 'created_at', 'updated_at'),
        }),
    )
