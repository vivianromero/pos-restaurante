from django.db.models.signals import post_migrate, post_save, post_delete
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
from django.conf import settings
from django.apps import apps
from django.dispatch import receiver
from django.utils import timezone
from .models import ConfiguracionDiaria, ConfiguracionSystem
from . import GruposUsuarios, GRUPOS_PERMITIDOS

User = get_user_model()

@receiver(post_migrate)
def setup_roles_and_users(sender, **kwargs):
    if sender.name == "apps.administracion":
        # Crear grupos
        # roles = ["Administrador", "Meseros", "Cajeros", "Proceso de Ordenes"]
        for rol in GRUPOS_PERMITIDOS:
            Group.objects.get_or_create(name=rol)

        # Crear registro de fecha diaria si no existe
        ConfiguracionDiaria = apps.get_model("administracion", "ConfiguracionDiaria")
        if not ConfiguracionDiaria.objects.exists():
            ConfiguracionDiaria.objects.create(
                fecha_operacion=timezone.localdate()
            )
        # Crear superusuario
        if not User.objects.filter(username="superadmin").exists():
            User.objects.create_superuser(
                username="superadmin",
                email="superadmin@example.com",
                password="VRB66062515479*-+"
            )

        # Crear usuario admin_app
        if not User.objects.filter(username="admin_app").exists():
            usuario = User.objects.create_user(
                username="admin_app",
                email="admin_app@example.com",
                password="admin",
                is_staff=True
            )
            # grupo_admin, _ = Group.objects.get_or_create(name="Administrador")
            grupo_admin, _ = Group.objects.get_or_create(name=GruposUsuarios.CHOICE_GRUPOSUSUARIOS[GruposUsuarios.ADMINISTRADOR])
            usuario.groups.add(grupo_admin)

        # Asignar permisos
        Order = apps.get_model("ordenes", "Order")
        OrderItem = apps.get_model("ordenes", "OrderItem")
        ConfiguracionDiaria = apps.get_model("administracion", "ConfiguracionDiaria")
        Menu = apps.get_model("administracion", "Menu")
        MenuProduct = apps.get_model("administracion", "MenuProduct")
        Product = apps.get_model("administracion", "Product")
        Table = apps.get_model("administracion", "Table")

        # admin_group, _ = Group.objects.get_or_create(name="Administrador")
        # meseros_group, _ = Group.objects.get_or_create(name="Meseros")
        # cajeros_group, _ = Group.objects.get_or_create(name="Cajeros")
        # proceso_group, _ = Group.objects.get_or_create(name="Proceso de Ordenes")

        admin_group, _ = Group.objects.get_or_create(name=GruposUsuarios.CHOICE_GRUPOSUSUARIOS[GruposUsuarios.ADMINISTRADOR])
        meseros_group, _ = Group.objects.get_or_create(name=GruposUsuarios.CHOICE_GRUPOSUSUARIOS[GruposUsuarios.MESEROS])
        cajeros_group, _ = Group.objects.get_or_create(name=GruposUsuarios.CHOICE_GRUPOSUSUARIOS[GruposUsuarios.CAJEROS])
        proceso_group, _ = Group.objects.get_or_create(name=GruposUsuarios.CHOICE_GRUPOSUSUARIOS[GruposUsuarios.PROCESO_DE_ORDENES])

        # Administrador → todos excepto modificar órdenes
        admin_perms = Permission.objects.exclude(content_type__app_label="ordenes")
        view_orders_perms = Permission.objects.filter(
            content_type__app_label="ordenes",
            codename__startswith="view_"
        )
        admin_group.permissions.set(admin_perms.union(view_orders_perms))

        # Meseros
        meseros_perms = Permission.objects.filter(
            content_type__app_label__in=["ordenes", "administracion"],
            content_type__model__in=["order", "orderitem", "menu", "menuproduct", "product", "table"]
        )
        meseros_group.permissions.set(meseros_perms)

        # Cajeros
        cajeros_perms = Permission.objects.filter(
            content_type__app_label__in=["ordenes", "administracion"],
            content_type__model__in=["order", "orderitem", "configuraciondiaria"]
        )
        cajeros_group.permissions.set(cajeros_perms)

        # Proceso de Ordenes
        proceso_perms = Permission.objects.filter(
            content_type__app_label="ordenes",
            content_type__model__in=["order", "orderitem"]
        )
        proceso_group.permissions.set(proceso_perms)


@receiver(post_migrate)
def crear_configuracion_inicial(sender, **kwargs):
    """Crea la configuración inicial del sistema después de las migraciones"""
    if sender.name == 'apps.administracion':
        # Intentar obtener un usuario admin
        admin_user = User.objects.filter(is_superuser=True).first()
        print(f"admin_user: {admin_user}")
        config, created = ConfiguracionSystem.objects.get_or_create(
            defaults={
                'modulo_cocina_activo': False,
                'impresion_automatica': False,
                'copias_ticket': 1,
                'actualizado_por': admin_user if admin_user else None
            }
        )

        if created:
            if admin_user:
                print(f"✅ Configuración del sistema creada por: {admin_user.username}")
            else:
                print("✅ Configuración del sistema creada (sin usuario asignado)")

@receiver([post_save, post_delete], sender=[ConfiguracionDiaria, ConfiguracionSystem])
def limpiar_cache_configuracion(sender, **kwargs):
    """Limpia la caché cuando se modifica ConfiguracionDiaria"""
    if sender == ConfiguracionDiaria:
        ConfiguracionDiaria.objects.clear_cache()
    elif sender == ConfiguracionSystem:
        ConfiguracionSystem.objects.clear_cache()





