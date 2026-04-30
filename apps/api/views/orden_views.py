# apps/api/views/orden_views.py
import logging

from django.core.exceptions import ValidationError
from django.db import transaction
from django_filters import rest_framework as filters
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.administracion.models import ConfiguracionSystem, Table, MenuProduct
from apps.core.utils import get_fecha_operacion_actual
from apps.ordenes.models import Order, OrderItem, EstadoOrden
from ..serializers.orden_serializer import OrdenSerializer, OrdenCreateSerializer
from django.utils import timezone

logger = logging.getLogger(__name__)


# Configuración personalizada de paginación
class OrdenPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 100


class OrdenFilter(filters.FilterSet):
    """Filtros para Orden usando django-filter"""

    # Filtros exactos
    id = filters.UUIDFilter(field_name='id')
    numero_orden = filters.CharFilter(field_name='numero_orden', lookup_expr='icontains')
    fecha = filters.DateFilter(field_name='fecha_operacion')
    fecha_desde = filters.DateFilter(field_name='fecha_operacion', lookup_expr='gte')
    fecha_hasta = filters.DateFilter(field_name='fecha_operacion', lookup_expr='lte')
    usuario_id = filters.NumberFilter(field_name='usuario__id')
    usuario = filters.CharFilter(field_name='usuario__username', lookup_expr='icontains')
    mesa = filters.NumberFilter(field_name='mesa__numero')
    mesa_id = filters.UUIDFilter(field_name='mesa__id')
    cancelada = filters.BooleanFilter(field_name='cancelada')
    total_min = filters.NumberFilter(field_name='importe_total', lookup_expr='gte')
    total_max = filters.NumberFilter(field_name='importe_total', lookup_expr='lte')

    # Filtro especial para estado
    estado = filters.NumberFilter(field_name='estado')
    estado_label = filters.CharFilter(method='filter_estado_nombre')

    def filter_estado_nombre(self, queryset, name, value):
        """Filtrar por nombre de estado"""
        estado_map = {
            'pendiente': EstadoOrden.PENDIENTE,
            'procesando': EstadoOrden.PROCESANDO,
            'servida': EstadoOrden.SERVIDA,
            'pendientepago': EstadoOrden.PENDIENTEPAGO,
            'pagada': EstadoOrden.PAGADA,
        }
        estado_lower = value.lower()
        if estado_lower in estado_map:
            return queryset.filter(estado=estado_map[estado_lower].value)
        return queryset

    class Meta:
        model = Order
        fields = [
            'id', 'numero_orden', 'fecha', 'fecha_desde', 'fecha_hasta',
            'usuario_id', 'usuario', 'mesa', 'mesa_id', 'cancelada',
            'estado', 'total_min', 'total_max'
        ]

    def filter_queryset(self, queryset):
        """Aplicar filtros personalizados"""
        queryset = super().filter_queryset(queryset)

        # Excluir canceladas por defecto si no se especifica
        cancelada_param = self.request.query_params.get('cancelada')
        if cancelada_param is None:
            queryset = queryset.filter(cancelada=False)

        # Filtro estado_diferente
        estado_diferente = self.request.query_params.get('estado_diferente')
        if estado_diferente:
            estado_map = {
                'pendiente': EstadoOrden.PENDIENTE,
                'procesando': EstadoOrden.PROCESANDO,
                'servida': EstadoOrden.SERVIDA,
                'pendientepago': EstadoOrden.PENDIENTEPAGO,
                'pagada': EstadoOrden.PAGADA,
            }
            if estado_diferente.lower() in estado_map:
                queryset = queryset.exclude(estado=estado_map[estado_diferente.lower()])
            else:
                raise ValidationError(f'Estado diferente inválido. Opciones: {list(estado_map.keys())}')

        return queryset


class OrdenViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrdenSerializer
    queryset = Order.objects.all().select_related('mesa', 'usuario')
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = OrdenFilter
    pagination_class = OrdenPagination

    def get_queryset(self):
        """Optimizar queryset base"""
        queryset = super().get_queryset()

        # Prefetch condicional basado en parámetro
        include_items = self.request.query_params.get('include_items', 'false').lower() == 'true'
        if include_items:
            queryset = queryset.prefetch_related(
                'items__menu_product__producto'
            )

        return queryset

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
        - estado_label: pendiente/procesando/servida/pendientepago/pagada
        - estado_diferente: excluir por nombre de estado
        - mesa: número de mesa
        - mesa_id: ID de mesa
        - numero_orden: número de orden
        - cancelada: true/false (por defecto false)
        - total_min: monto mínimo
        - total_max: monto máximo

        Parámetros de control:
        - include_items: true/false - incluir productos de la orden
        - limit: número máximo de resultados
        - offset: desplazamiento para paginación
        - ordenar: campo para ordenar (ej: -fecha_creacion)
        """
        try:
            # Obtener queryset con filtros aplicados automáticamente
            queryset = self.filter_queryset(self.get_queryset())

            # Ordenamiento
            ordenar_por = request.query_params.get('ordenar', '-fecha_creacion')

            # Validar campo de ordenamiento para evitar inyección SQL
            allowed_fields = ['fecha_creacion', '-fecha_creacion', 'numero_orden',
                              '-numero_orden', 'importe_total', '-importe_total',
                              'fecha_operacion', '-fecha_operacion', 'mesa__numero']

            if ordenar_por not in allowed_fields and not ordenar_por.lstrip('-') in allowed_fields:
                ordenar_por = '-fecha_creacion'

            queryset = queryset.order_by(ordenar_por)

            # Paginación automática
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            # Fallback para cuando no hay paginación (útil para exportaciones)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e.detail[0] if hasattr(e, 'detail') else e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error en list de órdenes: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Error al procesar la solicitud'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

        with transaction.atomic():
            order = Order.objects.create(
                usuario=usuario,
                mesa=mesa,
                fecha_operacion=get_fecha_operacion_actual(),
                estado=estado_inicial
            )

            menu_product_ids = [item['menu_product_id'] for item in items_data]
            menu_products = MenuProduct.objects.filter(id__in=menu_product_ids).in_bulk()

            order_items = [
                OrderItem(
                    order=order,
                    menu_product=menu_products[mp_id],
                    cantidad=item_data.get('cantidad', 1),
                    precio_unitario=menu_products[mp_id].precio
                )
                for item_data in items_data
                if (mp_id := item_data['menu_product_id']) in menu_products
            ]
            if order_items:
                OrderItem.objects.bulk_create(order_items)
                # Recalcular subtotales
                for item in order_items:
                    item.subtotal = item.cantidad * item.precio_unitario
                OrderItem.objects.bulk_update(order_items, ['subtotal'])

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
                'error': 'Debe tener al menos un producto'
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

    @action(detail=True, methods=['post'], url_path='abrir-orden')
    def abrir_orden(self, request, pk=None):
        with transaction.atomic():
            order = self.get_queryset().select_for_update().get(pk=pk)

            # Si está bloqueada por otro usuario
            if order.locked_by and order.locked_by != request.user:
                return Response(
                    {"error": f"Orden en uso por {order.locked_by.username}"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Bloquear por el usuario actual
            order.locked_by = request.user
            order.locked_at = timezone.now()
            order.save()

            # 🔑 Devolver los datos completos de la orden
            serializer = self.get_serializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='cerrar-orden')
    def cerrar_orden(self, request, pk=None):
        with transaction.atomic():
            order = self.get_queryset().select_for_update().get(pk=pk)

            # Solo quien la abrió puede cerrarla
            if order.locked_by and order.locked_by != request.user:
                return Response(
                    {"error": f"No puedes cerrar la orden, está bloqueada por {order.locked_by.username}"},
                    status=status.HTTP_403_FORBIDDEN
                )

            order.locked_by = None
            order.locked_at = None
            order.save()
            return Response({"ok": "Orden cerrada y desbloqueada"})
