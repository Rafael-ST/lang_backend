from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static


from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


urlpatterns = [
    path('exercise-builder/login/', TemplateView.as_view(template_name='exercicio/exercise_builder_login.html'), name='exercise-builder-login'),
    path('exercise-builder/', TemplateView.as_view(template_name='exercicio/exercise_builder.html'), name='exercise-builder'),
    path('admin/', admin.site.urls),
    path('api/v1/', include('authentication.urls')),
    path('api/v1/', include('categorias.urls')),
    path('api/v1/', include('cards.urls')),
    path('api/v1/', include('perfil.urls')),
    path('api/v1/', include('niveis.urls')),
    path('api/v1/', include('subniveis.urls')),
    path('api/v1/', include('exercicio.urls')),
    path('api/v1/', include('ExerciseSet.urls')),
    
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
