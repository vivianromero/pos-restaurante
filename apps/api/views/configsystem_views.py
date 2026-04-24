# apps/api/views/categoria_views.py
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.administracion.models import ConfiguracionSystem
from ..serializers.configsystem_serializer import ConfiguracionSystemSerializer


class ConfiguracionSystemViewSet(viewsets.GenericViewSet):
    """
    API para Configuración del Sistema
    GET /api/config-system/ - Obtener la configuración del sistema
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ConfiguracionSystemSerializer

    def list(self, request):
        """GET /api/config-system/ - Obtener la configuración"""
        config = ConfiguracionSystem.objects.get_cached_data()
        serializer = self.get_serializer(config)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='actual')
    def actual(self, request):
        """GET /api/config-system/actual/ - Devuelve la configuración directamente"""
        config = ConfiguracionSystem.objects.get_cached_data()
        serializer = self.get_serializer(config)
        return Response(serializer.data)