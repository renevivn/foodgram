from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from recipes.views import short_link_redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('s/<int:recipe_id>/', short_link_redirect, name='short_link'),
    path('', include('api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
