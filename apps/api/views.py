# from rest_framework import viewsets, status
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from django.db import transaction
# from django.utils import timezone
# from decimal import Decimal
#
# from apps.administracion.models import Table, MenuProduct
# from apps.ordenes.models import Order, OrderItem, EstadoOrden
# from .serializers import TableSerializer, MenuProductSerializer, OrderSerializer
#
#
# class TableViewSet(viewsets.ReadOnlyModelViewSet):
#     """
#     ViewSet para listar mesas (solo lectura)
#     GET /api/mesas/ - Lista todas las mesas activas
#     GET /api/mesas/{id}/ - Detalle de una mesa
#     """
#     permission_classes = [IsAuthenticated]
#     serializer_class = TableSerializer
#     queryset = Table.objects.all()
#
#
# class MenuProductViewSet(viewsets.ReadOnlyModelViewSet):
#     """
#     ViewSet para listar productos del menú (solo lectura)
#     GET /api/productos/ - Lista todos los productos
#     GET /api/productos/?disponible=true - Filtra solo productos disponibles
#     GET /api/productos/{id}/ - Detalle de un producto
#     """
#     permission_classes = [IsAuthenticated]
#     serializer_class = MenuProductSerializer
#
#     def get_queryset(self):
#         queryset = MenuProduct.objects.select_related('producto', 'menu').all()
#
#         # Filtrar por disponibilidad
#         disponible = self.request.query_params.get('disponible', None)
#         if disponible is not None:
#             if disponible.lower() == 'true':
#                 queryset = queryset.filter(producto__disponible=True)
#             elif disponible.lower() == 'false':
#                 queryset = queryset.filter(producto__disponible=False)
#
#         return queryset
#
#
# class OrderViewSet(viewsets.ModelViewSet):
#     """
#     ViewSet para gestionar órdenes
#     GET /api/ordenes/ - Lista todas las órdenes
#     GET /api/ordenes/?estado=1 - Filtra por estado
#     POST /api/ordenes/ - Crea una nueva orden
#     PUT /api/ordenes/{id}/ - Actualiza una orden completa
#     PATCH /api/ordenes/{id}/ - Actualiza una orden parcialmente
#     DELETE /api/ordenes/{id}/ - Elimina una orden
#     POST /api/ordenes/{id}/update_status/ - Cambia el estado de la orden
#     POST /api/ordenes/{id}/add_items/ - Agrega items a una orden existente
#     """
#     permission_classes = [IsAuthenticated]
#     serializer_class = OrderSerializer
#
#     def get_queryset(self):
#         queryset = Order.objects.filter(cancelada=False)
#
#         # Filtrar por estado
#         estado = self.request.query_params.get('estado', None)
#         if estado is not None:
#             try:
#                 estado_int = int(estado)
#                 queryset = queryset.filter(estado=estado_int)
#             except ValueError:
#                 pass
#
#         # Filtrar por mesa
#         mesa_id = self.request.query_params.get('mesa', None)
#         if mesa_id:
#             queryset = queryset.filter(mesas__id=mesa_id)
#
#         # Optimizar consultas
#         queryset = queryset.prefetch_related('items', 'items__menu_product', 'items__menu_product__producto', 'mesas')
#
#         return queryset
#
#     @transaction.atomic
#     def create(self, request, *args, **kwargs):
#         """
#         Crear una nueva orden
#         Ejemplo de body:
#         {
#             "mesas": ["uuid_mesa_1", "uuid_mesa_2"],
#             "items": [
#                 {"menu_product_id": "uuid_producto_1", "cantidad": 2},
#                 {"menu_product_id": "uuid_producto_2", "cantidad": 1}
#             ]
#         }
#         """
#         mesa_ids = request.data.get('mesas', [])
#         items_data = request.data.get('items', [])
#
#         # Validar que hay al menos una mesa
#         if not mesa_ids:
#             return Response(
#                 {'error': 'Debe seleccionar al menos una mesa'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         # Validar que las mesas existen y están activas
#         mesas = Table.objects.filter(id__in=mesa_ids, activa=True)
#         if len(mesas) != len(mesa_ids):
#             return Response(
#                 {'error': 'Una o más mesas no existen o están inactivas'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         # Verificar que las mesas no tengan una orden activa
#         for mesa in mesas:
#             orden_activa = Order.objects.filter(
#                 mesas=mesa,
#                 cancelada=False
#             ).exclude(estado=EstadoOrden.PAGADA).exists()
#
#             if orden_activa:
#                 return Response(
#                     {'error': f'La mesa {mesa.numero} ya tiene una orden activa'},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
#
#         # Crear la orden
#         order = Order.objects.create(
#             usuario=request.user,
#             fecha_operacion=timezone.localdate(),
#             estado=EstadoOrden.PENDIENTEPAGO
#         )
#         order.mesas.set(mesas)
#
#         # Agregar items a la orden
#         if items_data:
#             for item_data in items_data:
#                 menu_product_id = item_data.get('menu_product_id')
#                 cantidad = item_data.get('cantidad', 1)
#
#                 if not menu_product_id:
#                     continue
#
#                 try:
#                     menu_product = MenuProduct.objects.select_related('producto').get(id=menu_product_id)
#                     OrderItem.objects.create(
#                         order=order,
#                         menu_product=menu_product,
#                         cantidad=cantidad,
#                         precio_unitario=menu_product.precio
#                     )
#                 except MenuProduct.DoesNotExist:
#                     return Response(
#                         {'error': f'Producto con ID {menu_product_id} no existe'},
#                         status=status.HTTP_400_BAD_REQUEST
#                     )
#
#         # Calcular el total
#         order.calcular_total()
#         order.save()
#
#         # Recargar la orden con todos sus datos
#         order = Order.objects.prefetch_related('items', 'items__menu_product', 'items__menu_product__producto',
#                                                'mesas').get(id=order.id)
#         serializer = self.get_serializer(order)
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
#
#     @action(detail=True, methods=['post'])
#     def update_status(self, request, pk=None):
#         """
#         Cambiar el estado de una orden
#         Ejemplo de body:
#         {
#             "estado": 2
#         }
#         Estados: 1=Pendiente, 2=Procesando, 3=Servida, 4=Pagada
#         """
#         order = self.get_object()
#         nuevo_estado = request.data.get('estado')
#
#         # Validar que el estado sea válido
#         estados_validos = [e.value for e in EstadoOrden]
#         if nuevo_estado not in estados_validos:
#             return Response(
#                 {'error': f'Estado inválido. Opciones: {estados_validos}'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         # Si ya está pagada, no se puede cambiar
#         if order.estado == EstadoOrden.PAGADA:
#             return Response(
#                 {'error': 'No se puede cambiar el estado de una orden pagada'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         order.estado = nuevo_estado
#         order.save()
#
#         return Response({
#             'status': 'ok',
#             'order_id': str(order.id),
#             'nuevo_estado': order.get_estado_display(),
#             'estado_valor': order.estado
#         })
#
#     @action(detail=True, methods=['post'])
#     def add_items(self, request, pk=None):
#         """
#         Agregar items a una orden existente
#         Ejemplo de body:
#         {
#             "items": [
#                 {"menu_product_id": "uuid_producto_1", "cantidad": 2},
#                 {"menu_product_id": "uuid_producto_2", "cantidad": 1}
#             ]
#         }
#         """
#         order = self.get_object()
#
#         # Validar que la orden no esté pagada
#         if order.estado == EstadoOrden.PAGADA:
#             return Response(
#                 {'error': 'No se pueden agregar items a una orden pagada'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         items_data = request.data.get('items', [])
#
#         if not items_data:
#             return Response(
#                 {'error': 'Debe enviar al menos un item'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         # Agregar cada item
#         items_agregados = []
#         for item_data in items_data:
#             menu_product_id = item_data.get('menu_product_id')
#             cantidad = item_data.get('cantidad', 1)
#
#             if not menu_product_id:
#                 continue
#
#             try:
#                 menu_product = MenuProduct.objects.select_related('producto').get(id=menu_product_id)
#
#                 # Verificar si el producto ya existe en la orden
#                 existing_item = order.items.filter(menu_product=menu_product).first()
#
#                 if existing_item:
#                     # Si ya existe, aumentar la cantidad
#                     existing_item.cantidad += cantidad
#                     existing_item.save()
#                     items_agregados.append(existing_item)
#                 else:
#                     # Si no existe, crear nuevo item
#                     new_item = OrderItem.objects.create(
#                         order=order,
#                         menu_product=menu_product,
#                         cantidad=cantidad,
#                         precio_unitario=menu_product.precio
#                     )
#                     items_agregados.append(new_item)
#
#             except MenuProduct.DoesNotExist:
#                 return Response(
#                     {'error': f'Producto con ID {menu_product_id} no existe'},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
#
#         # Recalcular el total de la orden
#         order.calcular_total()
#         order.save()
#
#         # Recargar la orden actualizada
#         order = Order.objects.prefetch_related('items', 'items__menu_product', 'items__menu_product__producto',
#                                                'mesas').get(id=order.id)
#         serializer = self.get_serializer(order)
#
#         return Response({
#             'status': 'ok',
#             'message': f'Se agregaron {len(items_agregados)} item(s) a la orden',
#             'orden': serializer.data
#         })
#
#     @action(detail=True, methods=['post'])
#     def remove_item(self, request, pk=None):
#         """
#         Eliminar un item de la orden
#         Ejemplo de body:
#         {
#             "item_id": "uuid_item"
#         }
#         """
#         order = self.get_object()
#         item_id = request.data.get('item_id')
#
#         if not item_id:
#             return Response(
#                 {'error': 'Debe especificar el item_id'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         try:
#             item = order.items.get(id=item_id)
#             item.delete()
#
#             # Recalcular total
#             order.calcular_total()
#             order.save()
#
#             # Recargar la orden
#             order = Order.objects.prefetch_related('items', 'items__menu_product', 'items__menu_product__producto',
#                                                    'mesas').get(id=order.id)
#             serializer = self.get_serializer(order)
#
#             return Response({
#                 'status': 'ok',
#                 'message': 'Item eliminado correctamente',
#                 'orden': serializer.data
#             })
#         except OrderItem.DoesNotExist:
#             return Response(
#                 {'error': 'El item no existe en esta orden'},
#                 status=status.HTTP_404_NOT_FOUND
#             )
#
#     @action(detail=True, methods=['post'])
#     def update_item_quantity(self, request, pk=None):
#         """
#         Actualizar la cantidad de un item
#         Ejemplo de body:
#         {
#             "item_id": "uuid_item",
#             "cantidad": 3
#         }
#         """
#         order = self.get_object()
#         item_id = request.data.get('item_id')
#         nueva_cantidad = request.data.get('cantidad')
#
#         if not item_id:
#             return Response(
#                 {'error': 'Debe especificar el item_id'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         if nueva_cantidad is None:
#             return Response(
#                 {'error': 'Debe especificar la nueva cantidad'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         try:
#             nueva_cantidad = int(nueva_cantidad)
#             if nueva_cantidad < 1:
#                 return Response(
#                     {'error': 'La cantidad debe ser mayor a 0'},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
#         except ValueError:
#             return Response(
#                 {'error': 'La cantidad debe ser un número entero'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         try:
#             item = order.items.get(id=item_id)
#             item.cantidad = nueva_cantidad
#             item.save()
#
#             # Recalcular total
#             order.calcular_total()
#             order.save()
#
#             # Recargar la orden
#             order = Order.objects.prefetch_related('items', 'items__menu_product', 'items__menu_product__producto',
#                                                    'mesas').get(id=order.id)
#             serializer = self.get_serializer(order)
#
#             return Response({
#                 'status': 'ok',
#                 'message': 'Cantidad actualizada correctamente',
#                 'orden': serializer.data
#             })
#         except OrderItem.DoesNotExist:
#             return Response(
#                 {'error': 'El item no existe en esta orden'},
#                 status=status.HTTP_404_NOT_FOUND
#             )


