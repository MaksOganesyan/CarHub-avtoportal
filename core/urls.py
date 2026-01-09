from django.urls import path, include  # ← исправлено
from django.contrib.auth import views as auth_views
from . import views
from rest_framework.routers import DefaultRouter
from .api import CarViewSet

router = DefaultRouter()
router.register(r'cars', CarViewSet)

app_name = 'core'

urlpatterns = [
    path('', views.CarListView.as_view(), name='car_list'),
    path('car/<int:pk>/', views.CarDetailView.as_view(), name='car_detail'),
    path('car/add/', views.CarCreateView.as_view(), name='car_create'),
    path('car/<int:pk>/edit/', views.CarUpdateView.as_view(), name='car_update'),
    path('car/<int:pk>/delete/', views.CarDeleteView.as_view(), name='car_delete'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('api/', include(router.urls)),  # теперь include известен
]
