# apps/ordenes/filters.py
# apps/ordenes/filters.py
from django.core.exceptions import ValidationError
from django_filters import rest_framework as filters
from rest_framework.exceptions import ValidationError
from django.apps import apps


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Asignar el modelo real después de que Django esté listo
        if self._meta.model is None:
            self._meta.model = apps.get_model('ordenes', 'Order')

    def filter_estado_nombre(self, queryset, name, value):
        """Filtrar por nombre de estado"""
        # Importación local para evitar circular import
        from apps.ordenes.models import EstadoOrden

        estado_map = {
            'pendiente': EstadoOrden.PENDIENTE,
            'procesando': EstadoOrden.PROCESANDO,
            'servida': EstadoOrden.SERVIDA,
            'pendientepago': EstadoOrden.PENDIENTEPAGO,
            'pagada': EstadoOrden.PAGADA,
        }
        estado_lower = value.lower()
        if estado_lower in estado_map:
            return queryset.filter(estado=estado_map[estado_lower])
        return queryset

    def filter_queryset(self, queryset):
        """Aplicar filtros personalizados"""
        # Importación local para evitar circular import
        from apps.ordenes.models import EstadoOrden

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

    class Meta:
        model = None  # No asignar aquí, se asignará en __init__
        fields = [
            'id', 'numero_orden', 'fecha', 'fecha_desde', 'fecha_hasta',
            'usuario_id', 'usuario', 'mesa', 'mesa_id', 'cancelada',
            'estado', 'total_min', 'total_max'
        ]

# from django.core.exceptions import ValidationError
# from django_filters import rest_framework as filters
# from rest_framework.exceptions import ValidationError
#
# from apps.ordenes.models import Order, EstadoOrden
#
# class OrdenFilter(filters.FilterSet):
#     """Filtros para Orden usando django-filter"""
#
#     # Filtros exactos
#     id = filters.UUIDFilter(field_name='id')
#     numero_orden = filters.CharFilter(field_name='numero_orden', lookup_expr='icontains')
#     fecha = filters.DateFilter(field_name='fecha_operacion')
#     fecha_desde = filters.DateFilter(field_name='fecha_operacion', lookup_expr='gte')
#     fecha_hasta = filters.DateFilter(field_name='fecha_operacion', lookup_expr='lte')
#     usuario_id = filters.NumberFilter(field_name='usuario__id')
#     usuario = filters.CharFilter(field_name='usuario__username', lookup_expr='icontains')
#     mesa = filters.NumberFilter(field_name='mesa__numero')
#     mesa_id = filters.UUIDFilter(field_name='mesa__id')
#     cancelada = filters.BooleanFilter(field_name='cancelada')
#     total_min = filters.NumberFilter(field_name='importe_total', lookup_expr='gte')
#     total_max = filters.NumberFilter(field_name='importe_total', lookup_expr='lte')
#
#     # Filtro especial para estado
#     estado = filters.NumberFilter(field_name='estado')
#     estado_label = filters.CharFilter(method='filter_estado_nombre')
#
#     def filter_estado_nombre(self, queryset, name, value):
#         """Filtrar por nombre de estado"""
#         estado_map = {
#             'pendiente': EstadoOrden.PENDIENTE,
#             'procesando': EstadoOrden.PROCESANDO,
#             'servida': EstadoOrden.SERVIDA,
#             'pendientepago': EstadoOrden.PENDIENTEPAGO,
#             'pagada': EstadoOrden.PAGADA,
#         }
#         estado_lower = value.lower()
#         if estado_lower in estado_map:
#             return queryset.filter(estado=estado_map[estado_lower].value)
#         return queryset
#
#     class Meta:
#         model = Order
#         fields = [
#             'id', 'numero_orden', 'fecha', 'fecha_desde', 'fecha_hasta',
#             'usuario_id', 'usuario', 'mesa', 'mesa_id', 'cancelada',
#             'estado', 'total_min', 'total_max'
#         ]
#
#     def filter_queryset(self, queryset):
#         """Aplicar filtros personalizados"""
#         queryset = super().filter_queryset(queryset)
#
#         # Excluir canceladas por defecto si no se especifica
#         cancelada_param = self.request.query_params.get('cancelada')
#         if cancelada_param is None:
#             queryset = queryset.filter(cancelada=False)
#
#         # Filtro estado_diferente
#         estado_diferente = self.request.query_params.get('estado_diferente')
#         if estado_diferente:
#             estado_map = {
#                 'pendiente': EstadoOrden.PENDIENTE,
#                 'procesando': EstadoOrden.PROCESANDO,
#                 'servida': EstadoOrden.SERVIDA,
#                 'pendientepago': EstadoOrden.PENDIENTEPAGO,
#                 'pagada': EstadoOrden.PAGADA,
#             }
#             if estado_diferente.lower() in estado_map:
#                 queryset = queryset.exclude(estado=estado_map[estado_diferente.lower()])
#             else:
#                 raise ValidationError(f'Estado diferente inválido. Opciones: {list(estado_map.keys())}')
#
#         return queryset