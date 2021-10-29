from django import urls
from django.urls import path, re_path
from django.conf.urls import url
from rest_framework import routers
from rest_framework.routers import SimpleRouter

from . import views


router = SimpleRouter()

urlpatterns = [
    path('create', views.UserCreateAPI.as_view(), name='api-account-create'),
    path('login', views.UserLoginAPI.as_view(), name='api-account-login'),
    path('<int:account_id>/get', views.UserAPI.as_view(), name='api-account-get'),
    path('<int:account_id>/update', views.UserAPI.as_view(), name='api-account-update'),
]
urlpatterns += router.urls
