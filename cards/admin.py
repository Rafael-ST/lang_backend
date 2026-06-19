from django.contrib import admin

from cards.models import Card


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('english_name', 'international_name', 'categoria', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'categoria', 'created_at', 'updated_at')
    search_fields = ('english_name', 'international_name', 'categoria__nome')
    ordering = ('english_name',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ('categoria',)
