from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve

from core.views import trigger_glitchtip_error

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('core.urls')),
]

# Отдаём media-файлы (загруженные картинки автомобилей main_image и т.п.).
# Нужно для прод-контейнера (gunicorn + DEBUG=0), где обычный static() не работает.
# Также работает в dev.
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

# В проде отдаём и статику из STATIC_ROOT (собранную collectstatic).
if not settings.DEBUG:
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    ]

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
