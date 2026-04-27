# apps/api/views/orden_views.py
from datetime import datetime

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
from decimal import Decimal


class OrdenViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrdenSerializer

    queryset = Order.objects.all()

    def list(self, request, *args, **kwargs):
        """
        Filtrar órdenes por múltiples parámetros
        GET /api/ordenes/

        Parámetros de filtro:
        - id: UUID de la orden
        - fecha: fecha exacta (YYYY-MM-DD)
        - fecha_desde: fecha inicio (YYYY-MM-DD)
        - fecha_hasta: fecha fin (YYYY-MM-DD)
        - usuario: username del usuario
        - usuario_id: ID del usuario
        - estado: valor numérico del estado
        - estado_nombre: nombre del estado
        - estado_diferente: nombre del estado diferente
        - mesa: número de mesa
        - numero_orden: número de orden
        - cancelada: true/false

        Parámetros de control:
        - include_items: true/false - incluir productos de la orden
        - limit: número máximo de resultados
        - ordenar: campo para ordenar (ej: -fecha_creacion)
        """

        # ============================================
        # DICCIONARIOS DE FILTROS
        # ============================================

        filters = {}
        range_filters = {}
        search_filters = {}
        queryset = self.get_queryset()

        # Parámetros de control
        include_items = request.query_params.get('include_items', 'false').lower() == 'true'

        # ============================================
        # FILTROS EXACTOS
        # ============================================

        # ID de la orden
        orden_id = request.query_params.get('id')
        if orden_id:
            filters['id'] = orden_id

        # Número de orden
        numero_orden = request.query_params.get('numero_orden')
        if numero_orden:
            search_filters['numero_orden__icontains'] = numero_orden

        # Fecha exacta
        fecha = request.query_params.get('fecha')
        if fecha:
            try:
                fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
                filters['fecha_operacion'] = fecha_obj
            except ValueError:
                return Response({
                    'success': False,
                    'error': 'Formato de fecha inválido. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Estado
        estado = request.query_params.get('estado')
        if estado:
            try:
                estado_int = int(estado)
                if estado_int in [e.value for e in EstadoOrden]:
                    filters['estado'] = estado_int
                else:
                    return Response({
                        'success': False,
                        'error': f'Estado inválido. Opciones: {[e.value for e in EstadoOrden]}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except ValueError:
                return Response({
                    'success': False,
                    'error': 'El estado debe ser un número'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Estado por nombre
        estado_nombre = request.query_params.get('estado_nombre')
        estado_diferente = request.query_params.get('estado_diferente')
        estado_map = {
            'pendiente': EstadoOrden.PENDIENTE,
            'procesando': EstadoOrden.PROCESANDO,
            'servida': EstadoOrden.SERVIDA,
            'pendientepago': EstadoOrden.PENDIENTEPAGO,
            'pagada': EstadoOrden.PAGADA,
        }
        if estado_nombre:
            estado_lower = estado_nombre.lower()
            if estado_lower in estado_map:
                filters['estado'] = estado_map[estado_lower]
            else:
                return Response({
                    'success': False,
                    'error': f'Estado inválido. Opciones: {list(estado_map.keys())}'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Usuario
        usuario_id = request.query_params.get('usuario_id')
        if usuario_id:
            filters['usuario_id'] = usuario_id

        usuario = request.query_params.get('usuario')
        if usuario:
            search_filters['usuario__username__icontains'] = usuario

        # Mesa
        mesa = request.query_params.get('mesa')
        if mesa:
            try:
                filters['mesa__numero'] = int(mesa)
            except ValueError:
                return Response({
                    'success': False,
                    'error': 'La mesa debe ser un número'
                }, status=status.HTTP_400_BAD_REQUEST)

        mesa_id = request.query_params.get('mesa_id')
        if mesa_id:
            filters['mesa_id'] = mesa_id

        # Cancelada
        cancelada = request.query_params.get('cancelada')
        if cancelada:
            filters['cancelada'] = cancelada.lower() == 'true'
        else:
            queryset = queryset.filter(cancelada=False)

        # ============================================
        # FILTROS DE RANGO
        # ============================================

        # Fecha desde
        fecha_desde = request.query_params.get('fecha_desde')
        if fecha_desde:
            try:
                fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                range_filters['fecha_operacion__gte'] = fecha_desde_obj
            except ValueError:
                return Response({
                    'success': False,
                    'error': 'Formato de fecha_desde inválido. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Fecha hasta
        fecha_hasta = request.query_params.get('fecha_hasta')
        if fecha_hasta:
            try:
                fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                range_filters['fecha_operacion__lte'] = fecha_hasta_obj
            except ValueError:
                return Response({
                    'success': False,
                    'error': 'Formato de fecha_hasta inválido. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Rango de total
        total_min = request.query_params.get('total_min')
        if total_min:
            try:
                range_filters['importe_total__gte'] = Decimal(total_min)
            except:
                pass

        total_max = request.query_params.get('total_max')
        if total_max:
            try:
                range_filters['importe_total__lte'] = Decimal(total_max)
            except:
                pass
        try:
            # Aplicar filtros
            if filters:
                queryset = queryset.filter(**filters)
            if range_filters:
                queryset = queryset.filter(**range_filters)
            if search_filters:
                queryset = queryset.filter(**search_filters)
            if estado_diferente:
                estado_diferente_lower = estado_diferente.lower()
                if estado_diferente_lower in estado_map:
                    queryset = queryset.exclude(estado=estado_map[estado_diferente_lower])
                else:
                    return Response({
                        'success': False,
                        'error': f'Estado diferente inválido. Opciones: {list(estado_map.keys())}'
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Incluir productos si se solicita
            if include_items:
                queryset = queryset.prefetch_related('items__menu_product__producto')

            # Ordenar
            ordenar_por = request.query_params.get('ordenar', '-fecha_creacion')
            queryset = queryset.order_by(ordenar_por)

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except ValueError as error:
            raise ValidationError(f"Error en el formato de los parámetros: {error}")
        except Exception as exc:
            raise ValidationError(exc.args[1])

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