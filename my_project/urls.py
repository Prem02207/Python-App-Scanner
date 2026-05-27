from django.contrib import admin
from django.urls import path, include  # 'include' import karna zaroori hai

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('scraper_app.urls')), # Yahan 'scraper_app.urls' likhein
]