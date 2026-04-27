from datetime import date

from apps.administracion.models import ConfiguracionDiaria


def get_fecha_operacion_actual() -> date:
    """
    Obtiene la fecha de operación actual desde ConfiguracionDiaria
    con caché para evitar consultas repetidas a la BD
    """

    fecha = ConfiguracionDiaria.get_fecha_operacion()
    return fecha

def cambiar_fecha_operacion(nueva_fecha: date) -> ConfiguracionDiaria:
    """
    Cambia la fecha de operación
    """
    config, created = ConfiguracionDiaria.objects.get_or_create(
        fecha_operacion=nueva_fecha
    )
    return config