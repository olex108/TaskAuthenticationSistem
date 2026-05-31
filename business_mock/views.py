from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request
from identity.permissions import HasPermission


class MockAnalyticsAPIView(APIView):
    """
    Mock endpoint for business intelligence and financial reports.
    Protected by custom RBAC: requires 'mock:view_analytics' permission.
    """
    permission_classes = [HasPermission('mock:view_analytics')]

    def get(self, request: Request) -> Response:
        mock_data = {
            "report_name": "Q2 Strategic Business Performance",
            "active_clients": 1250,
            "monthly_recurring_revenue": 89400.50,
            "currency": "USD",
            "is_confidential": True
        }
        return Response(mock_data, status=status.HTTP_200_OK)


class MockDataManagementAPIView(APIView):
    """
    Mock endpoint for modifying corporate configuration settings.
    Protected by custom RBAC: requires 'mock:edit_data' permission.
    """
    permission_classes = [HasPermission('mock:edit_data')]

    def post(self, request: Request) -> Response:
        target_setting = request.data.get("setting_key")
        new_value = request.data.get("value")

        if not target_setting or not new_value:
            return Response(
                {"error": "Both setting_key and value fields are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "message": "System setting successfully modified (Mock Action Executed).",
                "updated_rule": {target_setting: new_value}
            },
            status=status.HTTP_200_OK
        )
