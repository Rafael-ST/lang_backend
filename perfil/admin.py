from django.contrib import admin
from .models import Perfil


class PerfilAdmin(admin.ModelAdmin):
    list_display = ('user', 'pontos')
    search_fields = ('user__username',)

admin.site.register(Perfil, PerfilAdmin)

# Register your models here.
