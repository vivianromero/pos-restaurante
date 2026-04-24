# apps/api/views/menu_product_views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.administracion.models import MenuProduct
from ..serializers.menu_product_serializer import MenuProductSerializer


class MenuProductViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MenuProductSerializer

    def get_queryset(self):
        queryset = MenuProduct.objects.select_related(
            'producto',
            'producto__categoria',
            'menu'
        ).all()

        queryset = queryset.filter(producto__disponible=True)

        menu_id = self.request.query_params.get('menu', None)
        if menu_id:
            queryset = queryset.filter(menu_id=menu_id)

        categoria_id = self.request.query_params.get('categoria', None)
        if categoria_id:
            queryset = queryset.filter(producto__categoria_id=categoria_id)

        return queryset