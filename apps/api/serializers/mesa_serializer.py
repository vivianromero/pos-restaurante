# apps/api/serializers/mesa_serializer.py
from rest_framework import serializers
from apps.administracion.models import Table
from apps.ordenes.models import Order, EstadoOrden
from apps.core.utils import get_fecha_operacion_actual

class MesaSerializer(serializers.ModelSerializer):
    """Serializador para mesas"""

    estado = serializers.SerializerMethodField()
    numero_orden = serializers.SerializerMethodField()

    class Meta:
        model = Table
        fields = ['id', 'numero', 'activa', 'estado', 'numero_orden']

    def get_estado(self, obj):
        # Obtener usuario actual de la request
        request = self.context.get('request')
        usuario_actual = request.user if request else None

        # Buscar orden activa (no pagada ni cancelada)
        orden_activa = Order.objects.filter(
            mesa=obj,
            cancelada=False,
            fecha_operacion=get_fecha_operacion_actual()
        ).exclude(
            estado__in=[EstadoOrden.PAGADA]
        ).first()

        if orden_activa:
            es_mi_mesa = usuario_actual and orden_activa.usuario == usuario_actual

            return {
                'ocupada': True,
                'es_mi_mesa': es_mi_mesa,
                'order_id': str(orden_activa.id),
                'numero_orden': orden_activa.numero_orden,
                'estado_orden': orden_activa.get_estado_display(),
                'usuario_orden': orden_activa.usuario.username
            }

        return {
            'ocupada': False,
            'es_mi_mesa': False,
            'order_id': None,
            'numero_orden': None,
            'estado_orden': None,
            'usuario_orden': None
        }

    def get_numero_orden(self, obj):
        """Devuelve el número de orden si la mesa está ocupada"""
        orden_activa = Order.objects.filter(
            mesa=obj,
            cancelada=False,
            fecha_operacion=get_fecha_operacion_actual()
        ).exclude(
            estado=EstadoOrden.PAGADA
        ).first()

        if orden_activa:
            return orden_activa.numero_orden
        return None

