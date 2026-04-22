from apps.administracion.models import ConfiguracionDiaria
from datetime import date

def get_fecha_operacion_actual() -> date:
    """
    Obtiene la fecha de operación actual desde ConfiguracionDiaria
    con caché para evitar consultas repetidas a la BD
    """

    fecha = ConfiguracionDiaria.get_fecha_operacion()
    return fecha