# apps/core/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from .decorators import es_mesero
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash, logout

from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from apps.administracion import GRUPOS_PERMITIDOS, GruposUsuarios


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    authentication_form = AuthenticationForm

    def get_success_url(self):
        return reverse_lazy('mesero')

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)

            if user is not None:
                # Verificar grupos permitidos
                grupos_permitidos = GRUPOS_PERMITIDOS[:]
                grupos_permitidos.remove(GruposUsuarios.CHOICE_GRUPOSUSUARIOS[GruposUsuarios.ADMINISTRADOR])
                if user.groups.filter(name__in=grupos_permitidos).exists() or user.is_superuser:
                    login(request, user)
                    return redirect(self.get_success_url())
                else:
                    messages.error(request, '❌ Acceso denegado. Tu usuario no tiene permisos para acceder al sistema.')
            else:
                messages.error(request, '❌ Usuario o contraseña incorrectosssssssss')
        return render(request, self.template_name, {'form': form})

@method_decorator(es_mesero, name='dispatch')
class MeseroView(TemplateView):
    template_name = 'pos/mesero.html'

@method_decorator(es_mesero, name='dispatch')
class CambiarPasswordView(TemplateView):
    template_name = 'registration/cambiar_password.html'

def custom_logout(request):
    logout(request)
    return redirect('/login/')


@login_required
def cambiar_password(request):
    """Vista para que los usuarios cambien su contraseña"""

    # Limpiar mensajes existentes al entrar a la página
    storage = messages.get_messages(request)
    storage.used = True

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, '¡Tu contraseña ha sido cambiada exitosamente!')
            return redirect('/mesero/?password_changed=success')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'registration/cambiar_password.html', {'form': form})
