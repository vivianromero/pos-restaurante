# apps/ordenes/managers.py
from django.db import models

from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Value, Count
from django.db.models.functions import Cast, Coalesce

class OrderManager(models.Manager):
    def calcular_resumen(self, params=None, request=None):
        qs = self.get_queryset()
        if params and request:
            # Importación local para evitar circular import
            from .filters import OrdenFilter
            filtro = OrdenFilter(params, queryset=qs, request=request)
            qs = filtro.qs

        resumen = qs.aggregate(
                    cantidad=(Count('id')),
                    importe=Coalesce(
                        Sum(Cast('importe_total', output_field=DecimalField(max_digits=12, decimal_places=2))),
                        Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
                    ),
                    monto_descuento=Coalesce(
                        Sum(Cast(
                            ExpressionWrapper(
                                F('importe_total') * F('porc_descuento') / Value(100.0),
                                output_field=DecimalField(max_digits=12, decimal_places=4)
                            ),
                            output_field=DecimalField(max_digits=12, decimal_places=2)
                        )),
                        Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
                    ),
                    total_porpagar=Coalesce(
                        Sum(Cast(
                            ExpressionWrapper(
                                F('importe_total') - (F('importe_total') * F('porc_descuento') / Value(100.0)),
                                output_field=DecimalField(max_digits=12, decimal_places=2)
                            ),
                            output_field=DecimalField(max_digits=12, decimal_places=2)
                        )),
                        Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
                    )
                )
        return {
            'cantidad': resumen['cantidad'] or 0,
            'importe_total': resumen['importe'] or 0,
            'monto_descuento': resumen['monto_descuento'] or 0,
            'total_pendiente': resumen['total_porpagar'] or 0,
        }