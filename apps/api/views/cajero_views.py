# apps/api/views/cajero_views.py
from datetime import datetime
from decimal import Decimal

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
        ).order_by('fecha_creacion')

    @action(detail=True, methods=['post'], url_path='aplicar-descuento')
    def aplicar_descuento(self, request, pk=None):
        """
        Aplicar descuento a una orden
        POST /api/cajero/pendientes/{id}/aplicar-descuento/
        Body: {"porcentaje": 10}
        """
        try:
            order = Order.objects.get(id=pk)
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Orden no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)

        # Solo se puede aplicar descuento si está pendiente de pago
        if order.estado != EstadoOrden.PENDIENTEPAGO:
            return Response({
                'success': False,
                'error': f'Solo se puede aplicar descuento a órdenes pendientes de pago. Estado actual: {order.get_estado_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)

        porcentaje = request.data.get('porcentaje', 0)

        try:
            porcentaje = Decimal(str(porcentaje))
            if porcentaje < 0 or porcentaje > 100:
                raise ValueError()
        except:
            return Response({
                'success': False,
                'error': 'El porcentaje debe ser un número entre 0 y 100'
            }, status=status.HTTP_400_BAD_REQUEST)

        order.porc_descuento = porcentaje
        order.calcular_total()
        order.save()

        # Serializar respuesta
        serializer = self.get_serializer(order)

        return Response({
            'success': True,
            'message': f'Descuento del {porcentaje}% aplicado',
            'data': serializer.data
        })

    @action(detail=True, methods=['post'], url_path='registrar-pago')
    def registrar_pago(self, request, pk=None):
        """
        Registrar pago de una orden
        POST /api/cajero/pendientes/{id}/registrar-pago/
        Body: {
            "forma_pago": 1,  # 1=Efectivo, 2=Tarjeta
            "efectivo_entregado": 50000,
            "propina": 0
        }
        """
        try:
            order = Order.objects.get(id=pk)
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Orden no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)

        # Solo se puede pagar si está pendiente de pago
        if order.estado != EstadoOrden.PENDIENTEPAGO:
            return Response({
                'success': False,
                'error': f'La orden no está pendiente de pago. Estado actual: {order.get_estado_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)

        forma_pago = request.data.get('forma_pago')
        efectivo_entregado = request.data.get('efectivo_entregado', 0)
        propina = request.data.get('propina', 0)

        # Validar forma de pago
        if forma_pago not in [FormaPagoOrden.EFECTIVO, FormaPagoOrden.TARJETA]:
            return Response({
                'success': False,
                'error': 'Forma de pago inválida. Opciones: 1 (Efectivo), 2 (Tarjeta)'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validar propina
        try:
            propina = Decimal(str(propina))
            if propina < 0:
                raise ValueError()
        except:
            return Response({
                'success': False,
                'error': 'La propina debe ser un número válido'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validar efectivo
        cambio = 0
        if forma_pago == FormaPagoOrden.EFECTIVO:
            try:
                efectivo_entregado = Decimal(str(efectivo_entregado))
                if efectivo_entregado < order.importe_total:
                    return Response({
                        'success': False,
                        'error': f'El efectivo entregado (${efectivo_entregado:,.2f}) es insuficiente. Total: ${order.importe_total:,.2f}',
                        'total': float(order.importe_total),
                        'efectivo_entregado': float(efectivo_entregado),
                        'faltante': float(order.importe_total - efectivo_entregado)
                    }, status=status.HTTP_400_BAD_REQUEST)
                cambio = efectivo_entregado - order.importe_total
            except:
                return Response({
                    'success': False,
                    'error': 'El efectivo entregado debe ser un número válido'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Actualizar orden
        order.forma_pago = forma_pago
        order.propina = propina
        # if forma_pago == FormaPagoOrden.EFECTIVO:
        #     order.efectivo_entregado = efectivo_entregado
        order.estado = EstadoOrden.PAGADA
        order.save()

        serializer = self.get_serializer(order)

        return Response({
            'success': True,
            'message': f'Orden #{order.numero_orden} pagada correctamente',
            'cambio': float(cambio) if cambio > 0 else 0,
            'data': serializer.data
        })

    @action(detail=True, methods=['post'], url_path='agregar-propina')
    def agregar_propina(self, request, pk=None):
        """
        Agregar propina a una orden ya pagada
        POST /api/cajero/pendientes/{id}/agregar-propina/
        Body: {"propina": 5000}
        """
        try:
            order = Order.objects.get(id=pk)
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Orden no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)

        # Solo se puede agregar propina si está pagada
        if order.estado != EstadoOrden.PAGADA:
            return Response({
                'success': False,
                'error': f'Solo se puede agregar propina a órdenes pagadas. Estado actual: {order.get_estado_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)

        propina = request.data.get('propina', 0)

        try:
            propina = Decimal(str(propina))
            if propina < 0:
                raise ValueError()
        except:
            return Response({
                'success': False,
                'error': 'La propina debe ser un número válido'
            }, status=status.HTTP_400_BAD_REQUEST)

        order.propina = propina
        order.save()

        serializer = self.get_serializer(order)

        return Response({
            'success': True,
            'message': f'Propina de ${propina:,.2f} agregada a la orden #{order.numero_orden}',
            'data': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='resumen')
    def resumen(self, request):
        """
        Resumen de órdenes pendientes de pago
        GET /api/cajero/resumen/
        """
        fecha_operacion = get_fecha_operacion_actual()

        pendientes = Order.objects.filter(
            estado=EstadoOrden.PENDIENTEPAGO,
            fecha_operacion=fecha_operacion,
            cancelada=False
        )

        total_pendiente = pendientes.aggregate(
            total=Sum('importe_total')
        )['total'] or 0

        return Response({
            'success': True,
            'cantidad': pendientes.count(),
            'total_pendiente': float(total_pendiente),
            'total_pendiente_formateado': f"${total_pendiente:,.2f}",
            'fecha_operacion': fecha_operacion
        })

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
        ordenes_pendientes = Order.objects.filter(
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