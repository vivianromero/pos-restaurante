# apps/api/serializers/mesa_serializer.py
from rest_framework import serializers
from apps.administracion.models import ConfiguracionSystem

class ConfiguracionSystemSerializer(serializers.ModelSerializer):
    """Serializador para mesas"""

    class Meta:
        model = ConfiguracionSystem
        fields = ['id', 'modulo_cocina_activo', 'pantalla_cocina_ip', 'pantalla_cocina_puerto',
                  'impresion_automatica', 'impresora_nombre', 'copias_ticket']



