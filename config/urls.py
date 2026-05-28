from django.urls import path, include

urlpatterns = [
    path('api/', include('identity.urls', namespace='identity')),
    path('api/mock/', include('business_mock.urls', namespace='business_mock')),
]