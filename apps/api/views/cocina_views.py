# apps/api/views/cocina_views.py
from django.db.models import Count, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.utils import get_fecha_operacion_actual
from apps.ordenes.models import Order, EstadoOrden
from ..serializers.orden_serializer import OrdenSerializer


class CocinaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para pantalla de cocina
    GET /api/cocina/pedidos/ - Obtener pedidos en estado PROCESANDO
    POST /api/cocina/pedidos/{id}/servir/ - Marcar pedido como servido
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OrdenSerializer

    def get_queryset(self):
        fecha_operacion = get_fecha_operacion_actual()

        # Mostrar pedidos en estado PENDIENTE
        return Order.objects.filter(
            estado__in=[EstadoOrden.PENDIENTE, EstadoOrden.PROCESANDO, EstadoOrden.SERVIDA],
            fecha_operacion=fecha_operacion,
            cancelada=False
        ).select_related(
            'usuario', 'mesa'
        ).prefetch_related(
            'items__menu_product__producto'
        ).order_by('fecha_creacion')

    @action(detail=True, methods=['post'], url_path='iniciar')
    def iniciar_preparacion(self, request, pk=None):
        """PENDIENTE → PROCESANDO"""
        try:
            order = Order.objects.get(id=pk)
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Pedido no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

        if order.estado != EstadoOrden.PENDIENTE:
            return Response({
                'success': False,
                'error': f'El pedido debe estar en estado Pendiente. Estado actual: {order.get_estado_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)

        order.estado = EstadoOrden.PROCESANDO
        order.save()

        return Response({
            'success': True,
            'message': f'Pedido #{order.numero_orden} en preparación'
        })

    @action(detail=True, methods=['post'], url_path='servir')
    def marcar_servido(self, request, pk=None):
        """PROCESANDO → SERVIDA"""
        try:
            order = Order.objects.get(id=pk)
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Pedido no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

        if order.estado != EstadoOrden.PROCESANDO:
            return Response({
                'success': False,
                'error': f'El pedido debe estar en estado Procesando. Estado actual: {order.get_estado_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)

        order.estado = EstadoOrden.SERVIDA
        order.save()

        return Response({
            'success': True,
            'message': f'Pedido #{order.numero_orden} servido. Listo para cobrar.'
        })

    @action(detail=False, methods=['get'], url_path='resumen')
    def resumen(self, request):
        """
        Resumen de pedidos en cocina
        GET /api/cocina/resumen/
        """
        fecha_operacion = get_fecha_operacion_actual()

        resumen = Order.objects.filter(
            fecha_operacion=fecha_operacion,
            cancelada=False,
            estado__in=[EstadoOrden.PENDIENTE, EstadoOrden.PROCESANDO, EstadoOrden.SERVIDA]
        ).aggregate(
            pendiente=Count('id', filter=Q(estado=EstadoOrden.PENDIENTE)),
            procesando=Count('id', filter=Q(estado=EstadoOrden.PROCESANDO)),
            servidas=Count('id', filter=Q(estado=EstadoOrden.SERVIDA))
        )

        return Response({
            'success': True,
            'pendientes': resumen['pendiente'],
            'procesando': resumen['procesando'],
            'servidas': resumen['servidas'],
            'fecha_operacion': fecha_operacion,
            'fecha_operacion_formateada': fecha_operacion.strftime('%d/%m/%Y')
        })