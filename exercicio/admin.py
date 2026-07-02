from django.contrib import admin

from exercicio.models import Exercise


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('id', 'card', 'type', 'difficulty', 'order', 'is_active', 'created_at', 'updated_at')
    list_filter = ('type', 'difficulty', 'is_active', 'created_at', 'updated_at')
    search_fields = ('card__english_name', 'card__international_name', 'type')
    ordering = ('order', 'id')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ('card',)
