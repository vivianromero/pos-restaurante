# apps/api/serializers/orden_serializer.py
from rest_framework import serializers
from apps.ordenes.models import Order, OrderItem, EstadoOrden, FormaPagoOrden
from apps.administracion.models import MenuProduct, Table


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializador para items de la orden"""

    producto_nombre = serializers.CharField(source='menu_product.producto.nombre', read_only=True)
    producto_descripcion = serializers.CharField(source='menu_product.producto.descripcion', read_only=True)
    producto_precio = serializers.DecimalField(source='menu_product.precio', read_only=True, max_digits=8,
                                               decimal_places=2)
    subtotal_formateado = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'id', 'menu_product', 'cantidad', 'precio_unitario',
            'subtotal', 'subtotal_formateado', 'producto_nombre',
            'producto_descripcion', 'producto_precio'
        ]

    def get_subtotal_formateado(self, obj):
        return f"${obj.subtotal:,.2f}"


class OrdenSerializer(serializers.ModelSerializer):
    """Serializador para órdenes"""

    items = OrderItemSerializer(many=True, read_only=True)
    estado_label = serializers.CharField(source='get_estado_display', read_only=True)
    forma_pago_label = serializers.CharField(source='get_forma_pago_display', read_only=True)
    total = serializers.DecimalField(source='importe_total', read_only=True, max_digits=12, decimal_places=2)
    total_formateado = serializers.SerializerMethodField()
    mesa_info = serializers.SerializerMethodField()
    puede_cobrar = serializers.SerializerMethodField()
    puede_editar = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'numero_orden', 'mesa', 'mesa_info', 'usuario',
            'fecha_creacion', 'fecha_operacion', 'estado', 'estado_label',
            'forma_pago', 'forma_pago_label', 'importe_total', 'total',
            'total_formateado', 'items', 'cancelada', 'motivo_cancelacion',
            'efectivo_entregado', 'propina', 'porc_descuento',
            'puede_cobrar', 'puede_editar'
        ]
        read_only_fields = ['numero_orden', 'importe_total']

    def get_total_formateado(self, obj):
        return f"${obj.importe_total:,.2f}"

    def get_mesa_info(self, obj):
        """Devuelve información de la mesa"""
        return {
            'id': str(obj.mesa.id),
            'numero': obj.mesa.numero
        }

    def get_puede_cobrar(self, obj):
        """
        Indica si la orden puede ser enviada a caja
        Solo si está en estado SERVIDA (3)
        """
        return obj.estado == EstadoOrden.SERVIDA

    def get_puede_editar(self, obj):
        """
        Indica si la orden puede ser editada (agregar/quitar productos)
        Solo si no está pagada ni cancelada
        """
        return obj.estado not in [EstadoOrden.PAGADA] and not obj.cancelada


class OrdenCreateSerializer(serializers.Serializer):
    """Serializador para crear una nueva orden"""

    mesa = serializers.UUIDField()
    items = serializers.ListField(child=serializers.DictField())

    def validate_mesa(self, value):
        """Validar que la mesa exista y esté activa"""
        from apps.administracion.models import Table
        from apps.ordenes.models import Order, EstadoOrden

        try:
            mesa = Table.objects.get(id=value, activa=True)
        except Table.DoesNotExist:
            raise serializers.ValidationError("La mesa no existe o está inactiva")

        # Verificar que la mesa no tenga una orden activa
        orden_activa = Order.objects.filter(
            mesa=mesa,
            cancelada=False
        ).exclude(estado=EstadoOrden.PAGADA).exists()

        if orden_activa:
            raise serializers.ValidationError(f"La mesa {mesa.numero} ya tiene una orden activa")

        return value

    def validate_items(self, value):
        """Validar que los items existan"""
        from apps.administracion.models import MenuProduct

        if not value:
            raise serializers.ValidationError("Debe agregar al menos un producto")

        for item in value:
            menu_product_id = item.get('menu_product_id')
            cantidad = item.get('cantidad', 1)

            if not menu_product_id:
                raise serializers.ValidationError("Cada item debe tener menu_product_id")

            if cantidad < 1:
                raise serializers.ValidationError("La cantidad debe ser mayor a 0")

            try:
                MenuProduct.objects.get(id=menu_product_id)
            except MenuProduct.DoesNotExist:
                raise serializers.ValidationError(f"Producto con ID {menu_product_id} no existe")

        return value


class OrdenCambiarEstadoSerializer(serializers.Serializer):
    """Serializador para cambiar estado de una orden"""

    estado = serializers.IntegerField()

    def validate_estado(self, value):
        from apps.ordenes.models import EstadoOrden

        estados_validos = [e.value for e in EstadoOrden]
        if value not in estados_validos:
            raise serializers.ValidationError(f"Estado inválido. Opciones: {estados_validos}")
        return value

# apps/api/serializers/orden_serializer.py
# from rest_framework import serializers
# from apps.ordenes.models import Order, OrderItem, EstadoOrden
# from apps.administracion.models import MenuProduct
#
#
# class OrderItemSerializer(serializers.ModelSerializer):
#     """Serializador para items de la orden"""
#
#     producto_nombre = serializers.CharField(source='menu_product.producto.nombre', read_only=True)
#     producto_descripcion = serializers.CharField(source='menu_product.producto.descripcion', read_only=True)
#     producto_precio = serializers.DecimalField(source='menu_product.precio', read_only=True, max_digits=8,
#                                                decimal_places=2)
#     menu_product_id = serializers.UUIDField(source='menu_product.id', read_only=True)
#     subtotal_formateado = serializers.SerializerMethodField()
#
#     class Meta:
#         model = OrderItem
#         fields = [
#             'id', 'menu_product', 'menu_product_id', 'cantidad',
#             'precio_unitario', 'subtotal', 'subtotal_formateado',
#             'producto_nombre', 'producto_descripcion', 'producto_precio'
#         ]
#
#     def get_subtotal_formateado(self, obj):
#         return f"${obj.subtotal:,.2f}"
#
#
# class OrdenSerializer(serializers.ModelSerializer):
#     """Serializador para órdenes"""
#
#     items = OrderItemSerializer(many=True, read_only=True)
#     estado_label = serializers.CharField(source='get_estado_display', read_only=True)
#     total = serializers.DecimalField(source='importe_total', read_only=True, max_digits=12, decimal_places=2)
#     total_formateado = serializers.SerializerMethodField()
#     mesas_info = serializers.SerializerMethodField()
#     puede_cobrar = serializers.SerializerMethodField()
#     puede_editar = serializers.SerializerMethodField()
#
#     class Meta:
#         model = Order
#         fields = [
#             'id', 'numero_orden', 'mesa', 'mesas_info', 'usuario',
#             'fecha_creacion', 'fecha_operacion', 'estado', 'estado_label',
#             'importe_total', 'total', 'total_formateado', 'items',
#             'cancelada', 'motivo_cancelacion', 'puede_cobrar', 'puede_editar'
#         ]
#         read_only_fields = ['numero_orden', 'importe_total']
#
#     def get_total_formateado(self, obj):
#         return f"${obj.importe_total:,.2f}"
#
#     def get_mesas_info(self, obj):
#         """Devuelve información de las mesas asociadas"""
#         return [
#             {
#                 'id': str(mesa.id),
#                 'numero': mesa.numero
#             }
#             for mesa in obj.mesas.all()
#         ]
#
#     def get_puede_cobrar(self, obj):
#         """
#         Indica si la orden puede ser enviada a caja
#         Solo si está en estado SERVIDA (3)
#         """
#         return obj.estado == EstadoOrden.SERVIDA
#
#     def get_puede_editar(self, obj):
#         """
#         Indica si la orden puede ser editada (agregar/quitar productos)
#         Solo si no está pagada ni cancelada
#         """
#         return obj.estado not in [EstadoOrden.PAGADA] and not obj.cancelada
#
#
# class OrdenCreateSerializer(serializers.Serializer):
#     """Serializador para crear una nueva orden"""
#
#     mesas = serializers.ListField(child=serializers.UUIDField(), write_only=True)
#     items = serializers.ListField(child=serializers.DictField(), write_only=True)
#
#     # def validate_mesas(self, value):
#     #     """Validar que las mesas existan y estén activas"""
#     #     from apps.administracion.models import Table
#     #     from apps.ordenes.models import Order, EstadoOrden
#     #
#     #     if not value:
#     #         raise serializers.ValidationError("Debe seleccionar al menos una mesa")
#     #
#     #     mesas = Table.objects.filter(id__in=value, activa=True)
#     #     if len(mesas) != len(value):
#     #         raise serializers.ValidationError("Una o más mesas no existen o están inactivas")
#     #
#     #     # Verificar que las mesas no tengan órdenes activas
#     #     for mesa in mesas:
#     #         orden_activa = Order.objects.filter(
#     #             mesas=mesa,
#     #             cancelada=False
#     #         ).exclude(estado=EstadoOrden.PAGADA).exists()
#     #
#     #         if orden_activa:
#     #             raise serializers.ValidationError(f"La mesa {mesa.numero} ya tiene una orden activa")
#     #
#     #     return value
#
#     def validate_items(self, value):
#         """Validar que los items existan"""
#         from apps.administracion.models import MenuProduct
#
#         if not value:
#             raise serializers.ValidationError("Debe agregar al menos un producto")
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
# class OrdenCambiarEstadoSerializer(serializers.Serializer):
#     """Serializador para cambiar estado de una orden"""
#
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
# class OrdenEnviarCajaSerializer(serializers.Serializer):
#     """Serializador para enviar orden a caja"""
#
#     # No se necesitan campos adicionales, solo la validación se hace en la vista
#     pass