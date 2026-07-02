from django.contrib import admin

from ExerciseSet.models import ExerciseSet, ExerciseSetProgress


@admin.register(ExerciseSet)
class ExerciseSetAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'sublevel', 'order', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'sublevel', 'created_at', 'updated_at')
    search_fields = ('title', 'description', 'sublevel__nome')
    ordering = ('order', 'created_at')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ('sublevel',)


@admin.register(ExerciseSetProgress)
class ExerciseSetProgressAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'exercise_set', 'status', 'completed_at', 'created_at', 'updated_at')
    list_filter = ('status', 'completed_at', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'exercise_set__title')
    ordering = ('created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ('user', 'exercise_set')
