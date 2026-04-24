# apps/api/views/orden_views.py
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.administracion.models import ConfiguracionSystem, Table, MenuProduct
from apps.core.utils import get_fecha_operacion_actual
from apps.ordenes.models import Order, OrderItem, EstadoOrden
from ..serializers.orden_serializer import OrdenSerializer, OrdenCreateSerializer


class OrdenViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrdenSerializer

    def get_queryset(self):
        return Order.objects.filter(cancelada=False).select_related(
            'usuario', 'mesa'
        ).prefetch_related(
            'items__menu_product__producto'
        )

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Crear una nueva orden
        """
        serializer = OrdenCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        try:
            mesa = Table.objects.select_for_update().get(
                id=validated_data['mesa'],
                activa=True
            )
        except Table.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Mesa no encontrada o inactiva'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verificar si la mesa ya tiene una orden activa
        orden_activa = Order.objects.filter(
            mesa=mesa,
            cancelada=False,
            estado__in=[EstadoOrden.PROCESANDO, EstadoOrden.PENDIENTEPAGO, EstadoOrden.SERVIDA]
        ).exists()

        if orden_activa:
            return Response({
                'success': False,
                'error': 'La mesa ya tiene una orden activa'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Crear orden en una transacción
        order = self._crear_orden(request.user, mesa, validated_data['items'])

        # Serializar respuesta
        response_serializer = self.get_serializer(order)

        return Response({
            'success': True,
            'message': 'Orden creada correctamente',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)


    def _crear_orden(self, usuario, mesa, items_data):
        """Método auxiliar para crear la orden y sus items"""
        config = ConfiguracionSystem.objects.get_cached_data()

        estado_inicial = EstadoOrden.PENDIENTE if config.modulo_cocina_activo else EstadoOrden.PENDIENTEPAGO

        order = Order.objects.create(
            usuario=usuario,
            mesa=mesa,
            fecha_operacion=get_fecha_operacion_actual(),
            estado=estado_inicial
        )

        menu_product_ids = [item['menu_product_id'] for item in items_data]
        menu_products = {
            str(mp.id): mp for mp in MenuProduct.objects.filter(id__in=menu_product_ids)
        }

        order_items = []
        for item_data in items_data:
            mp_id = item_data['menu_product_id']
            if mp_id not in menu_products:
                raise ValidationError(f'Producto con ID {mp_id} no existe')

            menu_product = menu_products[mp_id]
            order_items.append(OrderItem(
                order=order,
                menu_product=menu_product,
                cantidad=item_data.get('cantidad', 1),
                precio_unitario=menu_product.precio
            ))

        if order_items:
            OrderItem.bulk_create_with_subtotal(order_items)

        # order.calcular_total()
        order.save()

        return order

    @action(detail=True, methods=['post'], url_path='actualizar-items')
    def actualizar_items(self, request, pk=None):
        """
        Actualizar los items de una orden existente
        POST /api/ordenes/{id}/actualizar-items/
        Body: {"items": [{"menu_product_id": "...", "cantidad": 2}, ...]}
        """
        try:
            order = self.get_object()
        except Exception:
            return Response({
                'success': False,
                'error': 'Orden no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)

        # Validar que la orden no esté pagada ni cancelada
        if order.estado == EstadoOrden.PAGADA:
            return Response({
                'success': False,
                'error': 'No se puede modificar una orden pagada'
            }, status=status.HTTP_400_BAD_REQUEST)

        if order.cancelada:
            return Response({
                'success': False,
                'error': 'No se puede modificar una orden cancelada'
            }, status=status.HTTP_400_BAD_REQUEST)

        items_data = request.data.get('items', [])

        if not items_data:
            return Response({
                'success': False,
                'error': 'Debe enviar al menos un item'
            }, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Eliminar items existentes
            order.items.all().delete()

            # Crear nuevos items
            order_items = []
            for item_data in items_data:
                menu_product_id = item_data.get('menu_product_id')
                cantidad = item_data.get('cantidad', 1)

                try:
                    menu_product = MenuProduct.objects.get(id=menu_product_id)
                    subtotal = cantidad * menu_product.precio

                    order_items.append(OrderItem(
                        order=order,
                        menu_product=menu_product,
                        cantidad=cantidad,
                        precio_unitario=menu_product.precio,
                        subtotal=subtotal
                    ))
                except MenuProduct.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': f'Producto con ID {menu_product_id} no existe'
                    }, status=status.HTTP_400_BAD_REQUEST)

            if order_items:
                OrderItem.objects.bulk_create(order_items)

            # Recalcular total
            order.calcular_total()
            order.save()

        # Recargar la orden actualizada
        order = Order.objects.prefetch_related(
            'items__menu_product__producto'
        ).get(id=order.id)

        serializer = self.get_serializer(order)

        return Response({
            'success': True,
            'message': 'Orden actualizada correctamente',
            'data': serializer.data
        })

    @action(detail=True, methods=['post'], url_path='enviar-caja')
    def enviar_caja(self, request, pk=None):
        """
        Enviar orden a caja
        POST /api/ordenes/{id}/enviar-caja/
        """
        try:
            order = self.get_object()
        except Exception:
            return Response({
                'success': False,
                'error': 'Orden no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)

        # Verificar que la orden está en estado SERVIDA (3)
        if order.estado != EstadoOrden.SERVIDA:
            return Response({
                'success': False,
                'error': f'Solo se pueden enviar a caja órdenes en estado Servida. Estado actual: {order.get_estado_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Cambiar estado a PENDIENTEPAGO (4)
        order.estado = EstadoOrden.PENDIENTEPAGO
        order.save()

        return Response({
            'success': True,
            'message': f'Orden #{order.numero_orden} enviada a caja',
            'estado': order.estado,
            'estado_label': order.get_estado_display()
        })