# apps/api/views/menu_views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.administracion.models import Menu
from ..serializers.menu_serializer import MenuSerializer


class MenuViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para tipos de menú
    GET /api/menus/ - Lista todos los menús activos
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MenuSerializer
    queryset = Menu.objects.filter(activo=True)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)  # JSON directo