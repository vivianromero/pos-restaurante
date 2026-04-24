from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db import transaction
from django.db.models import Sum, F
from django_choices_field import IntegerChoicesField

from ..administracion.models import IdModels, MenuProduct, Table
from ..core.utils import get_fecha_operacion_actual


class EstadoOrden(models.IntegerChoices):
    PENDIENTE = 1, 'Pendiente'           # Enviado a cocina, esperando preparación
    PROCESANDO = 2, 'Procesando'          # En preparación
    SERVIDA = 3, 'Servida'                # Listo para servir (comida en mesa)
    PENDIENTEPAGO = 4, 'Pendiente de Pago' # Comida servida, esperando pago
    PAGADA = 5, 'Pagada'                  # Pagado

class FormaPagoOrden(models.IntegerChoices):
    EFECTIVO = 1, 'Efectivo'
    TARJETA = 2, 'Tarjeta'

class Order(IdModels):
    numero_orden = models.CharField(max_length=50, unique=True, editable=False, db_index=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, db_index=True)
    mesa = models.ForeignKey(Table, related_name="order_table", on_delete=models.PROTECT)  # varias mesas en una orden
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_operacion = models.DateField(db_index=True)
    estado = IntegerChoicesField(choices_enum=EstadoOrden, verbose_name="Estado", default=EstadoOrden.PENDIENTEPAGO)
    cancelada = models.BooleanField(default=False, db_index=True)
    motivo_cancelacion = models.TextField(blank=True, null=True)
    forma_pago = IntegerChoicesField(choices_enum=FormaPagoOrden, verbose_name='Forma de Pago', default=FormaPagoOrden.EFECTIVO)
    efectivo_entregado = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Efectivo entregado', default=0.00)
    propina = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Propina Recibida', default=0.00)
    importe_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, editable=False)
    porc_descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name='% Descuento')

    class Meta:
        indexes = [
            models.Index(fields=["fecha_operacion", "estado", "cancelada"]),
            models.Index(fields=["fecha_operacion", "usuario", "estado"]),
            models.Index(fields=["fecha_operacion", "usuario"]),
            models.Index(fields=["fecha_operacion", "numero_orden"]),
            models.Index(fields=["fecha_operacion", "usuario", "cancelada"]),
            models.Index(fields=["fecha_operacion", "usuario", "mesa"]),
        ]

    def __str__(self):
        return f"Orden #{self.id} - Mesa {self.mesa.numero} - {self.usuario.username}"

    def calcula_cambio(self):
        """
        Calcula el cambio a devolver al cliente si la forma de pago es efectivo.
        """
        if self.forma_pago == FormaPagoOrden.EFECTIVO:
            total = self.importe_total()
            cambio = self.efectivo_entregado - total
            return cambio if cambio >= 0 else Decimal("0.00")
        return Decimal("0.00")


    def calcular_total(self):
        """Calcula el total basado en los items y descuentos"""
        total = self.items.aggregate(
            total=Sum(F('cantidad') * F('precio_unitario'))
        )['total'] or Decimal('0')

        self.importe_total = total * (Decimal('1') - Decimal(self.porc_descuento) / Decimal('100'))
        return self.importe_total

    def generar_numero_orden(self):
        mesa_numero = self.mesa.numero
        fecha_operacion = get_fecha_operacion_actual()
        fecha_str = fecha_operacion.strftime('%Y%m%d')
        with transaction.atomic():
            consecutivo = Order.objects.select_for_update().filter(
                fecha_operacion=fecha_operacion
            ).count() + 1
        return f"{mesa_numero:03d}-{fecha_str.replace('-', '')}-{consecutivo:04d}"

    def save(self, *args, **kwargs):

        # obj = Order.objects.filter(pk=self.pk).first()
        if not self.numero_orden:
            self.numero_orden = self.generar_numero_orden()

        # if obj and obj.porc_descuento != self.porc_descuento:
        self.calcular_total()

        super().save(*args, **kwargs)


class OrderItem(IdModels):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", db_index=True)
    menu_product = models.ForeignKey(MenuProduct, on_delete=models.PROTECT, db_index=True)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, editable=False, default=0.00)
    # usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    @classmethod
    def bulk_create_with_subtotal(cls, items):
        """Método para crear múltiples items calculando el subtotal"""
        for item in items:
            item.subtotal = item.cantidad * item.precio_unitario
        return cls.objects.bulk_create(items)

    def save(self, *args, **kwargs):
        # Si no se ha fijado precio, tomarlo del producto del menú
        if not self.precio_unitario:
            self.precio_unitario = self.menu_product.precio
        # Calcular subtotal
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cantidad} x {self.menu_product.nombre} (Orden {self.order.numero_orden})"
