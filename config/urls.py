from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Подключаем все наши кастомные эндпоинты под префиксом api/v1/
    path('api/v1/', include('identity.urls', namespace='identity')),
]