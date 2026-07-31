from django.contrib import admin

from subniveis.models import SubNivel


@admin.register(SubNivel)
class SubNivelAdmin(admin.ModelAdmin):
    list_display = ('nome', 'subnivel', 'ordem', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'subnivel', 'created_at', 'updated_at')
    search_fields = ('nome', 'description', 'subnivel__nome')
    ordering = ('ordem', 'nome')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ('subnivel',)
