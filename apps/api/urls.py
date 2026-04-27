# apps/api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (MesaViewSet, CategoriaViewSet, MenuViewSet, MenuProductViewSet,
                    ConfiguracionSystemViewSet, OrdenViewSet, CocinaViewSet, CajeroViewSet)

router = DefaultRouter()
router.register(r'mesas', MesaViewSet, basename='mesa')
router.register(r'menus', MenuViewSet, basename='menu')
router.register(r'categorias', CategoriaViewSet, basename='categoria')
router.register(r'menu-productos', MenuProductViewSet, basename='menu-producto')
router.register(r'config-system', ConfiguracionSystemViewSet, basename='config-system')
router.register(r'ordenes', OrdenViewSet, basename='orden')
router.register(r'cocina', CocinaViewSet, basename='cocina')
router.register(r'cajero', CajeroViewSet, basename='cajero')

urlpatterns = [
    path('', include(router.urls)),
]
