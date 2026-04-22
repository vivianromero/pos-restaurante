# apps/api/serializers/mesa_serializer.py
from rest_framework import serializers
from apps.administracion.models import Menu

class MenuSerializer(serializers.ModelSerializer):
    """Serializador para mesas"""

    class Meta:
        model = Menu
        fields = ['id', 'nombre', 'activo']
