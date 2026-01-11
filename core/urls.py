from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from rest_framework.routers import DefaultRouter
from .api import CarViewSet, BrandViewSet

router = DefaultRouter()
router.register(r'cars', CarViewSet)
router.register(r'brands', BrandViewSet)

app_name = 'core'

urlpatterns = [
    path('', views.CarListView.as_view(), name='car_list'),
    path('car/<int:pk>/', views.CarDetailView.as_view(), name='car_detail'),
    path('car/add/', views.CarCreateView.as_view(), name='car_create'),
    path('car/<int:pk>/edit/', views.CarUpdateView.as_view(), name='car_update'),
    path('car/<int:pk>/delete/', views.CarDeleteView.as_view(), name='car_delete'),

    # Регистрация и логин
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # API
    path('api/', include(router.urls)),
]
