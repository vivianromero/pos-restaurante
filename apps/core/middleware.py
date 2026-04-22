from django.shortcuts import redirect
from django.shortcuts import render

# apps/core/middleware.py
from django.shortcuts import redirect
from django.shortcuts import render


class AdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verificar si es una URL del admin (excepto la página de login)
        if request.path.startswith('/admin/') and not request.path.startswith('/admin/login/'):
            if request.user.is_authenticated:
                # Verificar si es superusuario o pertenece al grupo Administracion
                if not (request.user.is_superuser or request.user.groups.filter(name='Administrador').exists()):
                    return render(request, '403.html', status=403)

        return self.get_response(request)