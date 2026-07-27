from django.contrib import admin

from exercicio.models import Exercise, ExerciseAttempt


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('id', 'exercise_set', 'card', 'type', 'skill', 'difficulty', 'order', 'is_active', 'created_at', 'updated_at')
    list_filter = ('skill', 'type', 'difficulty', 'is_active', 'exercise_set', 'created_at', 'updated_at')
    search_fields = ('card__english_name', 'card__international_name', 'exercise_set__title', 'type', 'skill')
    ordering = ('order', 'id')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ('exercise_set', 'card', 'pair_cards')


@admin.register(ExerciseAttempt)
class ExerciseAttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'exercise_set', 'exercise', 'is_correct', 'created_at', 'updated_at')
    list_filter = ('is_correct', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'exercise_set__title', 'exercise__type')
    ordering = ('created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ('user', 'exercise_set', 'exercise')
