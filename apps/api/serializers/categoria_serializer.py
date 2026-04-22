# apps/api/serializers/categoria_serializer.py
from rest_framework import serializers
from apps.administracion.models import Categoria


class CategoriaSerializer(serializers.ModelSerializer):
    """Serializador para categorías"""

    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'icono', 'orden', 'activo', 'nombre_completo']

    def get_nombre_completo(self, obj):
        """Devuelve el nombre con el icono incluido"""
        return f"{obj.icono} {obj.nombre}"