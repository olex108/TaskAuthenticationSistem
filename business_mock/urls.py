from django.urls import path
from business_mock.views import MockAnalyticsAPIView, MockDataManagementAPIView

app_name = 'business_mock'

urlpatterns = [
    path('business/analytics/', MockAnalyticsAPIView.as_view(), name='mock_analytics'),
    path('business/manage/', MockDataManagementAPIView.as_view(), name='mock_management'),
]
