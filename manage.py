# !/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
# import os
# import sys
# from dotenv import load_dotenv
#
# print("=== INICIO manage.py ===")
# print("ARGV:", sys.argv)
#
# # ============================================================
# # ENV
# # ============================================================
#
# if os.path.exists("/etc/pos-system/pos-system.env"):
#     load_dotenv("/etc/pos-system/pos-system.env")
# else:
#     load_dotenv(".env")
#
# # ============================================================
# # DJANGO SETTINGS
# # ============================================================
#
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
#
# # ============================================================
# # MAIN
# # ============================================================
#
# def main():
#     from django.core.management import execute_from_command_line
#
#     execute_from_command_line(sys.argv)
#
#
# if __name__ == "__main__":
#     main()

# def main():
#     os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
#
#     try:
#         from django.core.management import execute_from_command_line
#     except ImportError as exc:
#         raise ImportError("Couldn't import Django") from exc
#
#     # 🚀 Forzar configuración SOLO si ejecutas runserver
#     if 'runserver' in sys.argv:
#         # Evitar duplicar argumentos
#         has_addr = any(':' in arg for arg in sys.argv)
#
#         if not has_addr:
#             # Escuchar en toda la red (correcto para producción local)
#             sys.argv.insert(sys.argv.index('runserver') + 1, '0.0.0.0:8090')
#
#         # Evitar autoreload en PyInstaller
#         if getattr(sys, 'frozen', False) and '--noreload' not in sys.argv:
#             sys.argv.insert(sys.argv.index('runserver') + 1, '--noreload')
#
#     execute_from_command_line(sys.argv)
#
# if __name__ == '__main__':
#     main()

