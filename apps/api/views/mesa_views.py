# apps/api/views/mesa_views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.administracion.models import Table
from ..serializers import MesaSerializer


class MesaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para mesas
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MesaSerializer
    queryset = Table.objects.filter(activa=True)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return Response({
            'success': True,
            'data': serializer.data,
            'total': queryset.count(),
            'usuario': request.user.username
        })
