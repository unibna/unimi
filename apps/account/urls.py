from django.urls import path, re_path

from . import views


urlpatterns = [
    path('account/register', views.UserCreateAPI.as_view(), name='api-account-create'),
    path('account/login', views.UserLoginAPI.as_view(), name='api-account-login'),
    path('account/', views.UserAPI.as_view(), name='api-account'),
    path('account/<int:account_id>', views.UserAPI.as_view(), name='api-account'),

    # employee info
    path('employee', views.EmployeeAPI.as_view(), name='api-employee-get'),
    path('employee/<employee_id>', views.EmployeeAPI.as_view(), name='api-employee-get'),
]
