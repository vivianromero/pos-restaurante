from datetime import date

from apps.administracion.models import ConfiguracionDiaria
from django.db import transaction

def get_fecha_operacion_actual() -> date:
    """
    Obtiene la fecha de operación actual desde ConfiguracionDiaria
    con caché para evitar consultas repetidas a la BD
    """

    fecha = ConfiguracionDiaria.get_fecha_operacion()
    return fecha


def cambiar_fecha_operacion(nueva_fecha: date) -> ConfiguracionDiaria:
    """
    Cambia la fecha de operación, manteniendo un solo registro en la tabla
    """
    with transaction.atomic():
        config = ConfiguracionDiaria.objects.select_for_update().first()

        if config:
            config.fecha_operacion = nueva_fecha
            config.save()
            return config
        return ConfiguracionDiaria.objects.create(fecha_operacion=nueva_fecha)
