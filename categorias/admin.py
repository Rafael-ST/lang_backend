from django.contrib import admin

from categorias.models import Categoria


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('nome',)
    ordering = ('nome',)
    readonly_fields = ('id', 'created_at', 'updated_at')
