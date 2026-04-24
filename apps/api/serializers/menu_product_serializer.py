# apps/api/serializers/menu_product_serializer.py
from rest_framework import serializers

from apps.administracion.models import MenuProduct


class MenuProductSerializer(serializers.ModelSerializer):
    """
    Serializador para productos del menú (MenuProduct)
    Incluye información anidada del producto y categoría
    """

    # Datos del producto
    producto_id = serializers.UUIDField(source='producto.id', read_only=True)
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    producto_descripcion = serializers.CharField(source='producto.descripcion', read_only=True)
    producto_disponible = serializers.BooleanField(source='producto.disponible', read_only=True)

    # Datos de la categoría (a través del producto)
    categoria_id = serializers.UUIDField(source='producto.categoria.id', read_only=True)
    categoria_nombre = serializers.CharField(source='producto.categoria.nombre', read_only=True)
    categoria_icono = serializers.CharField(source='producto.categoria.icono', read_only=True)

    # Datos del menú
    menu_id = serializers.UUIDField(source='menu.id', read_only=True)
    menu_nombre = serializers.CharField(source='menu.nombre', read_only=True)

    # URL de la imagen
    imagen_url = serializers.SerializerMethodField()

    # Precio formateado (opcional)
    precio_formateado = serializers.SerializerMethodField()

    class Meta:
        model = MenuProduct
        fields = [
            'id',
            'producto_id',
            'producto_nombre',
            'producto_descripcion',
            'producto_disponible',
            'precio',
            'precio_formateado',
            'categoria_id',
            'categoria_nombre',
            'categoria_icono',
            'menu_id',
            'menu_nombre',
            'imagen_url'
        ]

    def get_imagen_url(self, obj):
        """
        Devuelve la URL completa de la imagen del producto
        """
        if obj.producto.imagen and obj.producto.imagen.name:
            return f'/media/{obj.producto.imagen.name}'
        return None

    def get_precio_formateado(self, obj):
        """
        Devuelve el precio formateado como moneda
        """
        return f"${obj.precio:,.2f}"