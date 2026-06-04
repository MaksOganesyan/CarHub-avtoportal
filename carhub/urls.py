from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),  # OAUTH2 / social login
    path('', include('core.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# django-debug-toolbar URLs (только в DEBUG — для демонстрации оптимизации запросов)
if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

# Django Silk URLs (подключаются, когда silk добавлен в INSTALLED_APPS)
if settings.DEBUG and 'silk' in settings.INSTALLED_APPS:
    try:
        urlpatterns = [
            path('silk/', include('silk.urls', namespace='silk')),
        ] + urlpatterns
    except ImportError:
        pass
