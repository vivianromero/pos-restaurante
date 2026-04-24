import uuid
from datetime import date

from PIL import Image
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db import transaction
from django.utils import timezone


class IdModels(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class DatosCacheManager(models.Manager):
    _cache = None

    def get_cached_data(self):
        return self._cache

    def clear_cache(self):
        self._cache = None

    class Meta:
        abstract = True

class CustomUser(AbstractUser):
    pass

    def __str__(self):
        return self.username

class ConfiguracionDiariaCacheManager(DatosCacheManager):

    def _obtener_datos(self):
        """Obtiene la configuración diaria desde BD"""
        fechaprocesamiento = ConfiguracionDiaria.objects.first()
        if not fechaprocesamiento:
            fechaprocesamiento = ConfiguracionDiaria.objects.create(
                fecha_operacion=timezone.localdate()
            )
            fechaprocesamiento.save()
        return fechaprocesamiento

    def get_cached_data(self):
        if self._cache is None:
            self._cache = self.get_fecha_procesamiento()
        return self._cache

    @transaction.atomic
    def get_fecha_procesamiento(self):
        fechaprocesamiento = ConfiguracionDiaria.objects.first()
        if not fechaprocesamiento:
            fechaprocesamiento = ConfiguracionDiaria.objects.create(
                fecha_operacion=timezone.localdate()
            )
        return fechaprocesamiento

class ConfiguracionDiaria(IdModels):
    fecha_operacion = models.DateField(default=timezone.localdate, db_index=True)
    objects = ConfiguracionDiariaCacheManager()

    def __str__(self):
        return f"Fecha de operación: {self.fecha_operacion}"

    @classmethod
    def get_fecha_operacion(cls) -> date:
        """Obtiene la fecha de operación actual"""
        return cls.objects.get_cached_data().fecha_operacion


class Categoria(models.Model):
    ICONOS_CATEGORIAS = [
        ('🍕', '🍕 Platos fuertes'),
        ('🥗', '🥗 Entradas'),
        ('🥤', '🥤 Bebidas'),
        ('🍰', '🍰 Postres'),
        ('🍔', '🍔 Hamburguesas'),
        ('🥩', '🥩 Carnes'),
        ('🍜', '🍜 Sopas'),
        ('🐟', '🐟 Pescados'),
        ('☕', '☕ Café'),
        ('🍺', '🍺 Cervezas'),
        ('🍷', '🍷 Vinos'),
        ('🍸', '🍸 Cocteles'),
        ('🍦', '🍦 Helados'),
        ('🥖', '🥖 Panadería'),
        ('🍳', '🍳 Desayunos'),
        ('📋', '📋 Todos'),
    ]

    nombre = models.CharField(max_length=100, verbose_name="Categoría del Producto", unique=True)
    icono = models.CharField(
        max_length=10,
        choices=ICONOS_CATEGORIAS,
        default='🍽️'
    )
    orden = models.IntegerField(default=0, unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['orden']

    def __str__(self):
        return f"{self.icono} {self.nombre}"


class Product(IdModels):
    nombre = models.CharField(max_length=250, db_index=True, unique=True, verbose_name='Producto')
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, verbose_name="Categoría del Producto")
    disponible = models.BooleanField(default=True)
    imagen = models.ImageField(
        upload_to='productos/',
        null=True,
        blank=True,
        verbose_name='Imagen del producto'
    )

    class Meta:
        indexes = [
            models.Index(fields=["nombre"]),
            models.Index(fields=["disponible"]),
        ]
        ordering = ['categoria', 'nombre']

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.imagen:
            img = Image.open(self.imagen.path)
            # Redimensionar siempre a un máximo de 800x800 px
            img.thumbnail((800, 800))
            # Optimizar y guardar en formato JPEG
            if img.mode in ("RGBA", "P"):  # convertir si es PNG con transparencia
                img = img.convert("RGB")
            img.save(self.imagen.path, format="JPEG", quality=85, optimize=True)


class Table(IdModels):
    numero = models.PositiveIntegerField(unique=True)
    activa = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["numero"]),
            models.Index(fields=["activa"]),
        ]
        ordering = ['numero']

    def __str__(self):
        return f"Mesa {self.numero}"


class Menu(IdModels):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Tipo de memú")  # único y con índice implícito
    activo = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return self.nombre

class MenuProduct(IdModels):
    menu = models.ForeignKey(Menu, on_delete=models.PROTECT, related_name="menu_products", verbose_name="Tipo de Menú")
    producto = models.ForeignKey(Product, on_delete=models.PROTECT)
    precio = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["menu", "producto"], name="unique_menu_producto")
        ]
    ordering = ['menu__nombre', 'producto__categoria__nombre', 'producto__nombre']

    def __str__(self):
        return f"{self.producto.nombre} ({self.menu.nombre})"


class ConfiguracionSystemCacheManager(DatosCacheManager):

    def get_cached_data(self):
        if self._cache is None:
            self._cache = self.obtener()
        return self._cache

    @transaction.atomic
    def obtener(self):
        """Obtiene la configuración activa (singleton)"""
        config = ConfiguracionSystem.objects.first()
        return config


class ConfiguracionSystem(models.Model):
    """Configuración general del sistema"""
    modulo_cocina_activo = models.BooleanField(
        default=False,
        verbose_name="Activar módulo de cocina",
        help_text="Si está activo, los pedidos van primero a cocina. Si no, van directamente a caja."
    )
    pantalla_cocina_ip = models.GenericIPAddressField(
        null=True, blank=True,
        verbose_name="IP de pantalla de cocina",
        help_text="IP de la tablet/pantalla que mostrará los pedidos en cocina"
    )
    pantalla_cocina_puerto = models.IntegerField(
        default=8000,
        verbose_name="Puerto de pantalla de cocina",
        help_text="Puerto donde corre la app en la pantalla de cocina"
    )
    impresion_automatica = models.BooleanField(
        default=False,
        verbose_name="Imprimir ticket automáticamente",
        help_text="Imprime el ticket automáticamente al finalizar la orden"
    )
    impresora_nombre = models.CharField(
        max_length=100,
        blank=True, null=True,
        verbose_name="Nombre de la impresora",
        help_text="Nombre de la impresora térmica configurada en el sistema"
    )
    copias_ticket = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Copias del ticket",
        help_text="Número de copias a imprimir"
    )
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True, blank=True,
        editable=False,
        verbose_name="Actualizado por"
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True,
                                               verbose_name="Fecha de actualización", editable=False)
    objects = ConfiguracionSystemCacheManager()

    class Meta:
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuraciones del Sistema"

    def __str__(self):
        return f"Sistema: Cocina={self.modulo_cocina_activo}"


    def save(self, *args, **kwargs):
        # Asegurar que siempre sea ID=1 (singleton)
        self.id = 1
        super().save(*args, **kwargs)



