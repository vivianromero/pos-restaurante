# apps/api/views/cajero_views.py
from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.decorators import es_cajero
from apps.core.utils import get_fecha_operacion_actual, cambiar_fecha_operacion
from apps.ordenes.models import Order, EstadoOrden, FormaPagoOrden
from ..serializers.orden_serializer import OrdenSerializer


class CajeroViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para cajero
    GET /api/cajero/pendientes/ - Órdenes pendientes de pago
    GET /api/cajero/pendientes/{id}/ - Detalle de orden
    POST /api/cajero/pendientes/{id}/aplicar-descuento/ - Aplicar descuento
    POST /api/cajero/pendientes/{id}/registrar-pago/ - Registrar pago
    POST /api/cajero/pendientes/{id}/agregar-propina/ - Agregar propina (solo después de pagada)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OrdenSerializer

    def get_queryset(self):
        fecha_operacion = get_fecha_operacion_actual()

        # Órdenes pendientes de pago (PENDIENTEPAGO = 4)
        return Order.objects.filter(
            estado=EstadoOrden.PENDIENTEPAGO,
            fecha_operacion=fecha_operacion,
            cancelada=False
        ).select_related(
            'usuario', 'mesa'
        ).prefetch_related(
            'items__menu_product__producto'
        ).order_by('mesa__numero')


    @method_decorator(es_cajero, name='dispatch')
    @action(detail=False, methods=['post'], url_path='cambiar-fecha')
    def cambiar_fecha_operacion(self, request):
        """
        Cambiar la fecha de operación (solo cajeros)
        POST /api/cajero/cambiar-fecha/
        Body: {"fecha": "2024-12-25"}
        """

        fecha_str = request.data.get('fecha')

        if not fecha_str:
            return Response({
                'success': False,
                'error': 'Debe proporcionar una fecha en formato YYYY-MM-DD'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            nueva_fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({
                'success': False,
                'error': 'Formato de fecha inválido. Use YYYY-MM-DD'
            }, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Obtener fecha actual
            fecha_actual = get_fecha_operacion_actual()

            # Si la fecha es la misma, no hacer nada
            if fecha_actual == nueva_fecha:
                return Response({
                    'success': True,
                    'message': 'La fecha ya está configurada',
                    'fecha_operacion': nueva_fecha.isoformat()
                })

            # Verificar si hay órdenes pendientes (no pagadas)
            ordenes_pendientes = Order.objects.select_for_update().filter(
                fecha_operacion=fecha_actual,
                cancelada=False
            ).exclude(
                estado=EstadoOrden.PAGADA
            ).count()

            if ordenes_pendientes > 0:
                return Response({
                    'success': False,
                    'error': f'No se puede cambiar la fecha. Hay {ordenes_pendientes} órdenes pendientes de pago en la fecha actual ({fecha_actual.strftime("%d/%m/%Y")}).',
                    'ordenes_pendientes': ordenes_pendientes,
                    'fecha_actual': fecha_actual.isoformat()
                }, status=status.HTTP_400_BAD_REQUEST)

            # Cambiar fecha de operación
            config = cambiar_fecha_operacion(nueva_fecha)

            return Response({
                'success': True,
                'message': f'Fecha de operación cambiada de {fecha_actual.strftime("%d/%m/%Y")} a {nueva_fecha.strftime("%d/%m/%Y")}',
                'fecha_anterior': fecha_actual.isoformat(),
                'fecha_operacion': nueva_fecha.isoformat()
            })

    @action(detail=False, methods=['get'], url_path='fecha-actual')
    def fecha_actual(self, request):
        """
        Obtener la fecha de operación actual
        GET /api/cajero/fecha-actual/
        """
        fecha_operacion = get_fecha_operacion_actual()
        res = {
            'success': True,
            'fecha_operacion': fecha_operacion.isoformat(),
            'fecha_operacion_formateada': fecha_operacion.strftime('%d/%m/%Y')
        }

        return Response(res)

    @method_decorator(es_cajero, name='dispatch')
    @action(detail=True, methods=['post'], url_path='guardar-pago')
    def guardar_pago(self, request, pk=None):
        with transaction.atomic():
            order = self.get_queryset().select_for_update().get(pk=pk)

            try:
                monto_entregado = float(request.data.get('monto_entregado', 0))
                propina = float(request.data.get('propina', 0))
                metodo_pago = request.data.get('metodo_pago')
                descuento = float(request.data.get('descuento', 0))
                accion = request.data.get('accion', None)
            except (TypeError, ValueError):
                return Response(
                    {"error": "Datos de pago inválidos"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            #Validaciones obligatorias
            if not metodo_pago:
                return Response(
                    {"error": "Debe especificar un método de pago"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if descuento > 100 or descuento < 0:
                return Response(
                    {"error": "El % a descontar es incorrecto"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            order.porc_descuento = descuento

            if metodo_pago == "efectivo":
                if monto_entregado < 0:
                    return Response(
                        {"error": "El monto entregado debe ser mayor a 0"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if monto_entregado > 0 and monto_entregado < order.total_apagar:
                    return Response(
                        {"error": "El monto entregado no cubre el total a pagar"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            if propina < 0:
                return Response(
                    {"error": "La propina no puede ser negativa"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            order.propina = propina
            order.metodo_pago = FormaPagoOrden.EFECTIVO if metodo_pago == 'efectivo' else FormaPagoOrden.TARJETA
            if accion and accion == "pagar":
                order.estado = EstadoOrden.PAGADA
            order.save()

            serializer = self.get_serializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
