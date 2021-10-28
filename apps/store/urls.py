from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()


urlpatterns = [
    path('create', views.StoreCreateAPI.as_view(), name='store-api-create'),
    path('list', views.StoreListAPI.as_view(), name='store-api-list'),
    path('get/<int:pk>', views.StoreRetrieveUpdateAPI.as_view(), name='store-api-get'),
    path('update/<int:pk>', views.StoreRetrieveUpdateAPI.as_view(), name='store-api-update'),
    
    # related employee
    path('join/<int:pk>', views.JoinStoreAPI.as_view(), name='store-api-join'),
    path('employee/list', views.StoreEmployeeListAPI.as_view(), name='store-api-employee-list'),
]
urlpatterns += router.urls
