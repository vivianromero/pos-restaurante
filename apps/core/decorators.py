# apps/core/decorators.py
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator

from apps.administracion import GruposUsuarios
from .urls_names import ADMIN_LOGIN, LOGIN


def es_administrador(view_func=None, redirect_field_name=REDIRECT_FIELD_NAME,
                     login_url=None):
    """
    Decorador para verificar que el usuario sea administrador
    """
    if login_url is None:
        login_url = reverse_lazy(ADMIN_LOGIN)

    actual_decorator = user_passes_test(
        lambda u: not isinstance(u, AnonymousUser) and (
                    u.is_superuser or u.groups.filter(name=GruposUsuarios.CHOICE_GRUPOSUSUARIOS[GruposUsuarios.ADMINISTRADOR]).exists()),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator


def es_cocina(view_func=None, redirect_field_name=REDIRECT_FIELD_NAME,
              login_url=None):
    """
    Decorador para verificar que el usuario sea específicamente PROCESO_DE_ORDENES
    (usuario autenticado que pertenece al grupo PROCESO_DE_ORDENES)
    """
    if login_url is None:
        login_url = reverse_lazy(LOGIN)

    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.groups.filter(
            name=GruposUsuarios.CHOICE_GRUPOSUSUARIOS[GruposUsuarios.PROCESO_DE_ORDENES]
        ).exists(),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )

    if view_func:
        return actual_decorator(view_func)
    return actual_decorator


def es_mesero(view_func=None, redirect_field_name=REDIRECT_FIELD_NAME,
              login_url=None):
    """
    Decorador para verificar que el usuario sea específicamente mesero
    (usuario autenticado que pertenece al grupo MESERO)
    """
    if login_url is None:
        login_url = reverse_lazy(LOGIN)

    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.groups.filter(
            name=GruposUsuarios.CHOICE_GRUPOSUSUARIOS[GruposUsuarios.MESEROS]
        ).exists(),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )

    if view_func:
        return actual_decorator(view_func)
    return actual_decorator


# Versión como class decorator para usar con as_view()
def mesero_required(view_class):
    """
    Decorador para clases basadas en vista (TemplateView, ListView, etc.)
    """
    return method_decorator(es_mesero, name='dispatch')(view_class)


def admin_required(view_class):
    """
    Decorador para clases basadas en vista (TemplateView, ListView, etc.)
    """
    return method_decorator(es_administrador, name='dispatch')(view_class)


