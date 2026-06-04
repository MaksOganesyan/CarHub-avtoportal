from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from core.views import trigger_glitchtip_error

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('core.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

if settings.DEBUG and 'silk' in settings.INSTALLED_APPS:
    try:
        urlpatterns = [
            path('silk/', include('silk.urls', namespace='silk')),
        ] + urlpatterns
    except ImportError:
        pass

# Для демонстрации GlitchTip (ошибки и 404 должны приходить в облачный дашборд)
urlpatterns += [
    path('trigger-glitchtip-error/', trigger_glitchtip_error, name='trigger_glitchtip_error'),
]

# Кастомный обработчик 404 (используется только когда DEBUG=False).
# Всегда шлёт capture_message в GlitchTip + отдаёт чистый templates/404.html
handler404 = 'core.views.handler404'
