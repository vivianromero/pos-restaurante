# apps/api/views/categoria_views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.administracion.models import Categoria
from ..serializers.categoria_serializer import CategoriaSerializer


class CategoriaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para categorías
    GET /api/categorias/ - Lista todas las categorías activas ordenadas
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CategoriaSerializer

    def get_queryset(self):
        return Categoria.objects.filter(activo=True).order_by('orden')