from rest_framework import serializers
from apps.administracion.models import Table, MenuProduct
from apps.ordenes.models import Order, OrderItem, EstadoOrden


# class TableSerializer(serializers.ModelSerializer):
#     """
#     Serializador para el modelo Table (Mesas)
#     Incluye información adicional sobre si la mesa está ocupada
#     """
#     estado = serializers.SerializerMethodField()
#
#     class Meta:
#         model = Table
#         fields = ['id', 'numero', 'activa', 'estado']
#
#     def get_estado(self, obj):
#         """
#         Determina si la mesa está ocupada y devuelve información de la orden activa
#         """
#         from apps.ordenes.models import Order, EstadoOrden
#
#         # Buscar una orden activa (no pagada ni cancelada) para esta mesa
#         orden_activa = Order.objects.filter(
#             mesa=obj,
#             cancelada=False
#         ).exclude(
#             estado__in=[EstadoOrden.PAGADA]
#         ).first()
#
#         if orden_activa:
#             return {
#                 'ocupada': True,
#                 'order_id': str(orden_activa.id),
#                 'estado_orden': orden_activa.get_estado_display(),
#                 'estado_valor': orden_activa.estado,
#                 'numero_orden': orden_activa.numero_orden,
#                 'usuario_orden': orden_activa.usuario
#             }
#
#         return {
#             'ocupada': False,
#             'order_id': None,
#             'estado_orden': None,
#             'estado_valor': None,
#             'numero_orden': None,
#             'usuario_orden':None
#         }
#
#
# class MenuProductSerializer(serializers.ModelSerializer):
#     """
#     Serializador para el modelo MenuProduct (Productos en el menú)
#     Incluye información del producto relacionado
#     """
#     producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
#     producto_descripcion = serializers.CharField(source='producto.descripcion', read_only=True)
#     disponible = serializers.BooleanField(source='producto.disponible', read_only=True)
#     menu_nombre = serializers.CharField(source='menu.nombre', read_only=True)
#
#     class Meta:
#         model = MenuProduct
#         fields = [
#             'id',
#             'producto_nombre',
#             'producto_descripcion',
#             'precio',
#             'disponible',
#             'menu_nombre'
#         ]
#
#
# class OrderItemSerializer(serializers.ModelSerializer):
#     """
#     Serializador para el modelo OrderItem (Items de la orden)
#     Incluye información del producto
#     """
#     producto_nombre = serializers.CharField(source='menu_product.producto.nombre', read_only=True)
#     producto_id = serializers.UUIDField(source='menu_product.producto.id', read_only=True)
#     menu_product_id = serializers.UUIDField(source='menu_product.id', read_only=True)
#     precio_unitario_formateado = serializers.SerializerMethodField()
#     subtotal_formateado = serializers.SerializerMethodField()
#
#     class Meta:
#         model = OrderItem
#         fields = [
#             'id',
#             'menu_product_id',
#             'producto_id',
#             'producto_nombre',
#             'cantidad',
#             'precio_unitario',
#             'precio_unitario_formateado',
#             'subtotal',
#             'subtotal_formateado'
#         ]
#
#     def get_precio_unitario_formateado(self, obj):
#         """Formatea el precio unitario como moneda"""
#         return f"${obj.precio_unitario:,.2f}"
#
#     def get_subtotal_formateado(self, obj):
#         """Formatea el subtotal como moneda"""
#         return f"${obj.subtotal:,.2f}"
#
#
# class OrderSerializer(serializers.ModelSerializer):
#     """
#     Serializador para el modelo Order (Órdenes)
#     Incluye información relacionada (items, mesas, estados)
#     """
#     items = OrderItemSerializer(many=True, read_only=True)
#     mesas_info = TableSerializer(source='mesas', many=True, read_only=True)
#     estado_label = serializers.CharField(source='get_estado_display', read_only=True)
#     forma_pago_label = serializers.CharField(source='get_forma_pago_display', read_only=True)
#     importe_total_formateado = serializers.SerializerMethodField()
#     fecha_creacion_formateada = serializers.SerializerMethodField()
#     cambio = serializers.DecimalField(source='calcula_cambio', read_only=True, max_digits=10, decimal_places=2)
#
#     class Meta:
#         model = Order
#         fields = [
#             'id',
#             'numero_orden',
#             'usuario',
#             'mesas',
#             'mesas_info',
#             'fecha_creacion',
#             'fecha_creacion_formateada',
#             'fecha_operacion',
#             'estado',
#             'estado_label',
#             'cancelada',
#             'motivo_cancelacion',
#             'forma_pago',
#             'forma_pago_label',
#             'efectivo_entregado',
#             'propina',
#             'importe_total',
#             'importe_total_formateado',
#             'porc_descuento',
#             'cambio',
#             'items'
#         ]
#         read_only_fields = ['numero_orden', 'importe_total']
#
#     def get_importe_total_formateado(self, obj):
#         """Formatea el importe total como moneda"""
#         return f"${obj.importe_total:,.2f}"
#
#     def get_fecha_creacion_formateada(self, obj):
#         """Formatea la fecha de creación"""
#         if obj.fecha_creacion:
#             return obj.fecha_creacion.strftime("%d/%m/%Y %H:%M:%S")
#         return None
#
#
# class OrderCreateSerializer(serializers.ModelSerializer):
#     """
#     Serializador específico para CREAR órdenes
#     Permite enviar mesas e items en la misma petición
#     """
#     mesas = serializers.ListField(child=serializers.UUIDField(), write_only=True)
#     items = serializers.ListField(child=serializers.DictField(), write_only=True, required=False)
#
#     class Meta:
#         model = Order
#         fields = ['mesas', 'items', 'forma_pago', 'propina', 'porc_descuento']
#
#     def validate_mesas(self, value):
#         """Validar que las mesas existan y estén activas"""
#         from apps.administracion.models import Table
#
#         if not value:
#             raise serializers.ValidationError("Debe seleccionar al menos una mesa")
#
#         mesas = Table.objects.filter(id__in=value, activa=True)
#         if len(mesas) != len(value):
#             raise serializers.ValidationError("Una o más mesas no existen o están inactivas")
#
#         # Verificar que las mesas no tengan órdenes activas
#         from apps.ordenes.models import Order, EstadoOrden
#
#         for mesa in mesas:
#             orden_activa = Order.objects.filter(
#                 mesas=mesa,
#                 cancelada=False
#             ).exclude(estado__in=[EstadoOrden.PAGADA]).exists()
#
#             if orden_activa:
#                 raise serializers.ValidationError(f"La mesa {mesa.numero} ya tiene una orden activa")
#
#         return value
#
#     def validate_items(self, value):
#         """Validar que los items existan"""
#         from apps.administracion.models import MenuProduct
#
#         if not value:
#             return value
#
#         for item in value:
#             menu_product_id = item.get('menu_product_id')
#             cantidad = item.get('cantidad', 1)
#
#             if not menu_product_id:
#                 raise serializers.ValidationError("Cada item debe tener menu_product_id")
#
#             if cantidad < 1:
#                 raise serializers.ValidationError("La cantidad debe ser mayor a 0")
#
#             try:
#                 MenuProduct.objects.get(id=menu_product_id)
#             except MenuProduct.DoesNotExist:
#                 raise serializers.ValidationError(f"Producto con ID {menu_product_id} no existe")
#
#         return value
#
#
# class OrderItemCreateSerializer(serializers.ModelSerializer):
#     """
#     Serializador para crear/actualizar items de una orden
#     """
#
#     class Meta:
#         model = OrderItem
#         fields = ['id', 'menu_product', 'cantidad']
#
#     def validate_cantidad(self, value):
#         if value < 1:
#             raise serializers.ValidationError("La cantidad debe ser mayor a 0")
#         return value
#
#
# class OrderUpdateStatusSerializer(serializers.Serializer):
#     """
#     Serializador para actualizar el estado de una orden
#     """
#     estado = serializers.IntegerField()
#
#     def validate_estado(self, value):
#         from apps.ordenes.models import EstadoOrden
#
#         estados_validos = [e.value for e in EstadoOrden]
#         if value not in estados_validos:
#             raise serializers.ValidationError(f"Estado inválido. Opciones: {estados_validos}")
#         return value
#
#
# class OrderAddItemsSerializer(serializers.Serializer):
#     """
#     Serializador para agregar items a una orden existente
#     """
#     items = serializers.ListField(child=serializers.DictField())
#
#     def validate_items(self, value):
#         from apps.administracion.models import MenuProduct
#
#         if not value:
#             raise serializers.ValidationError("Debe enviar al menos un item")
#
#         for item in value:
#             menu_product_id = item.get('menu_product_id')
#             cantidad = item.get('cantidad', 1)
#
#             if not menu_product_id:
#                 raise serializers.ValidationError("Cada item debe tener menu_product_id")
#
#             if cantidad < 1:
#                 raise serializers.ValidationError("La cantidad debe ser mayor a 0")
#
#             try:
#                 MenuProduct.objects.get(id=menu_product_id)
#             except MenuProduct.DoesNotExist:
#                 raise serializers.ValidationError(f"Producto con ID {menu_product_id} no existe")
#
#         return value
#
#
# class OrderItemQuantitySerializer(serializers.Serializer):
#     """
#     Serializador para actualizar la cantidad de un item
#     """
#     item_id = serializers.UUIDField()
#     cantidad = serializers.IntegerField()
#
#     def validate_cantidad(self, value):
#         if value < 1:
#             raise serializers.ValidationError("La cantidad debe ser mayor a 0")
#         return value
#
#
# class OrderRemoveItemSerializer(serializers.Serializer):
#     """
#     Serializador para eliminar un item de una orden
#     """
#     item_id = serializers.UUIDField()