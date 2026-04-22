from django.contrib import admin
from .models import Order, OrderItem

# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     list_display = ("numero_orden", "usuario", "fecha_operacion", "estado", "cancelada")
#     list_filter = ("estado", "cancelada", "fecha_operacion")
#     search_fields = ("numero_orden", "usuario__username")
#     date_hierarchy = "fecha_operacion"
#
#     def get_readonly_fields(self, request, obj=None):
#         # Si el usuario es Administrador, todos los campos son solo lectura
#         if request.user.groups.filter(name="Administrador").exists():
#             return [f.name for f in self.model._meta.fields]
#         return super().get_readonly_fields(request, obj)
#
#     def has_add_permission(self, request):
#         if request.user.groups.filter(name="Administrador").exists():
#             return False
#         return super().has_add_permission(request)
#
#     def has_change_permission(self, request, obj=None):
#         if request.user.groups.filter(name="Administrador").exists():
#             # Permite entrar al detalle, pero sin editar
#             return True
#         return super().has_change_permission(request, obj)
#
#     def has_delete_permission(self, request, obj=None):
#         if request.user.groups.filter(name="Administrador").exists():
#             return False
#         return super().has_delete_permission(request, obj)
#
#     def get_actions(self, request):
#         actions = super().get_actions(request)
#         if request.user.groups.filter(name="Administrador").exists():
#             if "delete_selected" in actions:
#                 del actions["delete_selected"]
#         return actions
#
#
# @admin.register(OrderItem)
# class OrderItemAdmin(admin.ModelAdmin):
#     list_display = ("order", "menu_product", "cantidad", "precio_unitario", "subtotal")
#     list_filter = ("menu_product",)
#     search_fields = ("order__numero_orden", "menu_product__producto__nombre")
#
#     def get_readonly_fields(self, request, obj=None):
#         if request.user.groups.filter(name="Administrador").exists():
#             return [f.name for f in self.model._meta.fields]
#         return super().get_readonly_fields(request, obj)
#
#     def has_add_permission(self, request):
#         if request.user.groups.filter(name="Administrador").exists():
#             return False
#         return super().has_add_permission(request)
#
#     def has_change_permission(self, request, obj=None):
#         if request.user.groups.filter(name="Administrador").exists():
#             return True
#         return super().has_change_permission(request, obj)
#
#     def has_delete_permission(self, request, obj=None):
#         if request.user.groups.filter(name="Administrador").exists():
#             return False
#         return super().has_delete_permission(request, obj)
#
#     def get_actions(self, request):
#         actions = super().get_actions(request)
#         if request.user.groups.filter(name="Administrador").exists():
#             if "delete_selected" in actions:
#                 del actions["delete_selected"]
#         return actions
