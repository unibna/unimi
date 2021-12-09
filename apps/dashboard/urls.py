from django.urls import path

from apps.dashboard.employee_dashboard_views import *

urlpatterns = [
    
    path('dashboard/employee', EmployeeDashboard.as_view(), name="dashboard_employee"),
]
