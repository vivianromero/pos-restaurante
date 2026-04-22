from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from decimal import Decimal
from .models import OrderItem

@receiver([post_save, post_delete], sender=OrderItem)
def actualizar_importe_total(sender, instance, **kwargs):
    """
    Recalcula el importe total de la orden cada vez que se guarda o elimina un OrderItem.
    """
    order = instance.order
    order.importe_total = order.calcular_total()
    order.save(update_fields=["importe_total"])
