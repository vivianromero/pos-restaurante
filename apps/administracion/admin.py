from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.http import HttpResponse
from django.http import JsonResponse
from django.urls import path
from django.utils.html import format_html

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import ConfiguracionDiaria, Product, Table, Menu, MenuProduct, Categoria
from .models import ConfiguracionSystem
from .models import CustomUser
from ..ordenes.models import Order, OrderItem

@admin.register(ConfiguracionSystem)
class ConfiguracionSystemAdmin(admin.ModelAdmin):
    """Configuración del sistema en el admin de Django"""

    fieldsets = (
        ('🍳 Módulo de Cocina', {
            'fields': ('modulo_cocina_activo', 'pantalla_cocina_ip', 'pantalla_cocina_puerto'),
            'description': 'Configuración del flujo de pedidos a cocina'
        }),
        ('🖨️ Impresión', {
            'fields': ('impresion_automatica', 'impresora_nombre', 'copias_ticket'),
            'description': 'Configuración de impresión de tickets',
            'classes': ('collapse',)
        }),
        ('📋 Información', {
            'fields': ('actualizado_por', 'fecha_actualizacion'),
            'classes': ('collapse',),
            'description': 'Información de auditoría (se llena automáticamente)'
        }),
    )

    list_display = [
        'modulo_cocina_activo',
        'pantalla_cocina_ip',
        'impresion_automatica',
        'actualizado_por',
        'fecha_actualizacion'
    ]

    readonly_fields = ['actualizado_por', 'fecha_actualizacion']  # 👈 Solo lectura

    def save_model(self, request, obj, form, change):
        """Guarda el modelo asignando automáticamente el usuario actual"""
        if change:
            # Solo actualizar actualizado_por si es una modificación
            obj.actualizado_por = request.user
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        # Solo permitir una única configuración
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

class ReadOnlyGroupAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# Re‑registrar el modelo Group con esta configuración
admin.site.unregister(Group)
admin.site.register(Group, ReadOnlyGroupAdmin)


# Formulario de edición de usuario con un solo grupo
class SingleGroupUserChangeForm(CustomUserChangeForm):
    single_group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label="Rol",
        empty_label="Sin rol"
    )

    class Meta(CustomUserChangeForm.Meta):
        model = CustomUser
        fields = "__all__"
        exclude = ('groups',)

    def __init__(self, *args, **kwargs):
        # Eliminar 'groups' de los argumentos iniciales si existe
        if 'initial' in kwargs and 'groups' in kwargs['initial']:
            del kwargs['initial']['groups']

        # Llamar al super primero
        super().__init__(*args, **kwargs)

        # Ahora eliminar el campo groups del formulario si existe
        if 'groups' in self.fields:
            del self.fields['groups']

        # Configurar el valor inicial para single_group
        if self.instance and self.instance.pk:
            first_group = self.instance.groups.first()
            if first_group:
                self.fields['single_group'].initial = first_group

    def clean_single_group(self):
        group = self.cleaned_data.get('single_group')
        return group

    def save(self, commit=True):
        instance = super().save(commit=False)

        if commit:
            instance.save()
            # Guardar la relación many-to-many después
            selected_group = self.cleaned_data.get('single_group')
            if selected_group:
                instance.groups.set([selected_group])
            else:
                instance.groups.clear()

            # Esto es importante para otros campos many-to-many
            self.save_m2m()

        return instance


# Formulario de creación de usuario con un solo grupo
class SingleGroupUserCreationForm(CustomUserCreationForm):
    single_group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label="Rol",
        empty_label="Sin rol"
    )

    class Meta(CustomUserCreationForm.Meta):
        model = CustomUser
        fields = "__all__"
        exclude = ('groups',)

    def __init__(self, *args, **kwargs):
        # Eliminar 'groups' de los argumentos iniciales si existe
        if 'initial' in kwargs and 'groups' in kwargs['initial']:
            del kwargs['initial']['groups']

        # Llamar al super primero
        super().__init__(*args, **kwargs)

        # Ahora eliminar el campo groups del formulario si existe
        if 'groups' in self.fields:
            del self.fields['groups']

    def clean_single_group(self):
        group = self.cleaned_data.get('single_group')
        return group

    def save(self, commit=True):
        instance = super().save(commit=False)

        if commit:
            instance.save()
            # Guardar la relación many-to-many después
            selected_group = self.cleaned_data.get('single_group')
            if selected_group:
                instance.groups.set([selected_group])
            else:
                instance.groups.clear()

            # Esto es importante para otros campos many-to-many
            self.save_m2m()

        return instance


# Si el problema persiste, podemos crear formularios completamente nuevos
# sin heredar de CustomUserChangeForm
class DirectSingleGroupUserChangeForm(forms.ModelForm):
    single_group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label="Rol",
        empty_label="Sin rol"
    )

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        required=False,
        help_text="Raw passwords are not stored, so there is no way to see this user's password, but you can change the password using <a href=\"../password/\">this form</a>."
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'password', 'first_name', 'last_name', 'email',
                  'is_active', 'is_staff')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Si el usuario ya existe, mostrar su grupo actual
            first_group = self.instance.groups.first()
            if first_group:
                self.fields['single_group'].initial = first_group

    def clean_password(self):
        return self.initial.get('password', '')

    def save(self, commit=True):
        instance = super().save(commit=False)

        if commit:
            instance.save()
            selected_group = self.cleaned_data.get('single_group')
            if selected_group:
                instance.groups.set([selected_group])
            else:
                instance.groups.clear()
            self.save_m2m()

        return instance


class DirectSingleGroupUserCreationForm(forms.ModelForm):
    single_group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label="Rol",
        empty_label="Sin rol"
    )

    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email',
                  'is_active', 'is_staff')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.set_password(self.cleaned_data["password1"])

        if commit:
            instance.save()
            selected_group = self.cleaned_data.get('single_group')
            if selected_group:
                instance.groups.set([selected_group])
            else:
                instance.groups.clear()
            self.save_m2m()

        return instance


class CustomUserAdmin(UserAdmin):
    # Elegir qué versión usar - descomentar la que funcione
    # Opción 1: Usar los formularios modificados (puede seguir dando error)
    # add_form = SingleGroupUserCreationForm
    # form = SingleGroupUserChangeForm

    # Opción 2: Usar formularios completamente nuevos (recomendado)
    add_form = DirectSingleGroupUserCreationForm
    form = DirectSingleGroupUserChangeForm

    model = CustomUser

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj is None:  # solo en creación
            form.base_fields['is_staff'].initial = True
        return form

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(is_superuser=False)

    # Para edición de usuarios existentes
    fieldsets = (
        ("General", {
            "fields": ("username", "password"),
            "classes": ("tab-general",),
        }),
        ("Información personal", {
            "fields": ("first_name", "last_name", "email"),
            "classes": ("tab-info",),
        }),
        ("Permisos", {
            "fields": ("is_active", "is_staff"),
            "classes": ("tab-permisos",),
        }),
        ("Rol", {
            "fields": ("single_group",),
            "classes": ("tab-grupo",),
        }),
    )

    # Para creación de usuarios nuevos
    add_fieldsets = (
        ("General", {
            "fields": ("username", "password1", "password2"),
            "classes": ("tab-general",),
        }),
        ("Información personal", {
            "fields": ("first_name", "last_name", "email"),
            "classes": ("tab-info",),
        }),
        ("Permisos", {
            "fields": ("is_active", "is_staff"),
            "classes": ("tab-permisos",),
        }),
        ("Grupo", {
            "fields": ("single_group",),
            "classes": ("tab-grupo",),
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        selected_group = form.cleaned_data.get('single_group')
        if selected_group:
            obj.groups.set([selected_group])
        else:
            obj.groups.clear()

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return self.fieldsets


admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(ConfiguracionDiaria)
class ConfiguracionDiariaAdmin(admin.ModelAdmin):
    # Mostrar solo la fecha en la lista
    list_display = ("fecha_operacion",)

    # Evitar que se creen nuevos registros desde el admin
    def has_add_permission(self, request):
        return False

    # Evitar que se eliminen registros desde el admin
    def has_delete_permission(self, request, obj=None):
        return False

    # Evitar que se editen registros desde el admin
    def has_change_permission(self, request, obj=None):
        # Permitir solo visualizar (read-only)
        return False

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    # El primer campo es el link (no puede ser editable)
    list_display = ('icono', 'nombre', 'orden', 'activo')

    # Los campos editables (no incluir el primero de list_display)
    list_editable = ('orden', 'activo')

    # Los campos que funcionan como enlace (el primero por defecto)
    list_display_links = ('icono',)  # Opcional: 'icono' será clickeable

    search_fields = ('nombre',)

    fieldsets = (
        ('Información', {
            'fields': ('nombre', 'icono', 'orden', 'activo')
        }),
    )

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('categoria', 'nombre', 'disponible', 'imagen_preview')
    list_filter = ('categoria', 'disponible',)
    search_fields = ('nombre',)
    readonly_fields = ('imagen_preview_real',)

    fieldsets = (
        ('Información básica', {
            'fields': ('categoria', 'nombre', 'descripcion', 'disponible',)
        }),
        ('Imagen y visualización', {
            'fields': ('imagen', 'imagen_preview_real')
        }),
    )

    def imagen_preview(self, obj):
        if obj.imagen:
            return format_html(
                '<div style="width:80px; height:80px; display:flex; align-items:center; justify-content:center; border:1px solid #ccc; overflow:hidden;">'
                '<img src="{}" style="max-width:100%; max-height:100%; object-fit:cover;" />'
                '</div>',
                obj.imagen.url
            )
            # return format_html('<img src="{}" style="max-height:150px;"/>', obj.imagen.url)  # noqa: UP031
        return "No hay imagen"

    def imagen_preview_real(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" style="max-height:150px;"/>', obj.imagen.url)  # noqa: UP031
        return "No hay imagen"
    imagen_preview.short_description = "Vista previa"
    imagen_preview_real.short_description = "Vista previa"

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("numero", "activa")
    list_filter = ("activa",)

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo")
    list_filter = ("activo",)


@admin.register(MenuProduct)
class MenuProductAdmin(admin.ModelAdmin):
    list_display = ("menu", "categoria_personalizada",  "producto", "precio")
    list_filter = ("menu__nombre", "producto__categoria__nombre", "producto__nombre")
    search_fields = ("producto__nombre", "producto__categoria__nombre", "menu__nombre")

    ordering = ['menu__nombre', 'producto__categoria__orden', 'producto__nombre']

    def categoria_personalizada(self, obj):
        return obj.producto.categoria

    categoria_personalizada.short_description = "Categoría del producto"
    categoria_personalizada.admin_order_field = "producto__categoria__nombre"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('productos-por-menu/',
                 self.admin_site.admin_view(self.productos_por_menu),
                 name='menuproduct-productos-por-menu'),
        ]
        return custom_urls + urls

    def productos_por_menu(self, request):
        menu_id = request.GET.get('menu_id')
        menuproduct_id = request.GET.get('menuproduct_id')
        productos = []
        producto_actual_id = None

        if menu_id and menu_id != 'None':
            try:
                # Si estamos editando, obtener el producto actual
                if menuproduct_id and menuproduct_id != 'None':
                    try:
                        menuproduct = MenuProduct.objects.get(pk=menuproduct_id)
                        producto_actual_id = str(menuproduct.producto_id)
                    except MenuProduct.DoesNotExist:
                        pass

                # Obtener productos ya usados en este menú
                usados = MenuProduct.objects.filter(menu_id=menu_id)

                # Si estamos editando, excluir el registro actual
                if menuproduct_id and menuproduct_id != 'None':
                    usados = usados.exclude(pk=menuproduct_id)

                usados_ids = usados.values_list('producto_id', flat=True)

                # Filtrar productos disponibles y no usados
                qs = Product.objects.filter(disponible=True)
                if usados_ids:
                    qs = qs.exclude(id__in=usados_ids)

                productos = list(qs.values('id', 'nombre'))
            except Exception as e:
                print(f"Error: {e}")

        return JsonResponse({
            'productos': productos,
            'producto_actual_id': producto_actual_id
        })

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        return form

    class Media:
        js = ("js/menuproduct_admin.js",)

class CustomAdminSite(admin.AdminSite):
    site_header = "Panel de Administración POS"
    site_title = "POS Admin"
    index_title = "Dashboard"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("dashboard/", self.admin_view(self.dashboard_view), name="dashboard"),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        config = ConfiguracionDiaria.objects.first()
        fecha_operacion = config.fecha_operacion if config else None

        ordenes_hoy = Order.objects.filter(fecha_operacion=fecha_operacion).count()
        ventas_hoy = OrderItem.objects.filter(order__fecha_operacion=fecha_operacion).aggregate(
            total=Sum("subtotal")
        )["total"] or 0
        mesas_activas = Table.objects.filter(activa=True).count()
        productos_disponibles = Product.objects.filter(disponible=True).count()

        html = f"""
        <h1>Dashboard del Administrador</h1>
        <p><strong>Fecha de operación:</strong> {fecha_operacion}</p>
        <ul>
            <li>Órdenes del día: {ordenes_hoy}</li>
            <li>Ventas totales del día: ${ventas_hoy:.2f}</li>
            <li>Mesas activas: {mesas_activas}</li>
            <li>Productos disponibles: {productos_disponibles}</li>
        </ul>
        """
        return HttpResponse(html)


# Reemplazar el admin por el personalizado
admin_site = CustomAdminSite(name="custom_admin")


