from django.urls import path, re_path

from . import views


urlpatterns = [
    path('account/register', views.UserCreateAPI.as_view()),
    path('account/login', views.UserLoginAPI.as_view()),
    path('account/', views.UserAPI.as_view()),
    path('account/<int:account_id>', views.UserAPI.as_view()),

    # employee info
    path('employee', views.EmployeeAPI.as_view()),
    path('employee/<employee_id>', views.EmployeeAPI.as_view()),

    # customer address
    path('customer/address', views.CustomerAddressAPI.as_view()),
    path('customer/address/<int:address_id>', views.CustomerAddressAPI.as_view()),
]
