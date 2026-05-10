from django.apps import AppConfig
from django.core.management import call_command
import threading, logging

logger = logging.getLogger(__name__)

class CoreConfig(AppConfig):
    name = "apps.core"
    verbose_name = "CoreConfig"

    def ready(self):
        def run_migrations():
            try:
                call_command("migrate", interactive=False)
                # call_command("collectstatic", interactive=False, verbosity=0)
                logger.info("[POS System] Migraciones/estáticos completados")
            except Exception as e:
                logger.error(f"[POS System] Error en migraciones/estáticos: {e}")

        # Lanzar en un hilo aparte, fuera del contexto async
        threading.Thread(target=run_migrations).start()





