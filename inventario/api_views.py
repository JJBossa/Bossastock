"""
Vistas API usando Django REST Framework
Estos endpoints están en paralelo con los existentes, NO los reemplazan
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, F
from django_filters.rest_framework import DjangoFilterBackend
from typing import Optional

from .models import (
    Producto, Categoria, Venta, ItemVenta,
    Cotizacion, ItemCotizacion, MovimientoStock,
    NotificacionStock, Proveedor
)
from .serializers import (
    ProductoSerializer, ProductoListSerializer, CategoriaSerializer,
    VentaSerializer, CotizacionSerializer, MovimientoStockSerializer,
    NotificacionStockSerializer, ProveedorSerializer
)
from .utils import es_admin_bossa, normalizar_texto
from .permissions import IsAdminOrReadOnly, IsOwnerOrAdmin, IsAdminBossa


class ProductoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar productos
    
    Permite:
    - list: Listar productos (GET /api/v1/productos/)
    - retrieve: Obtener un producto (GET /api/v1/productos/{id}/)
    - create: Crear producto (POST /api/v1/productos/) - Solo admin bossa
    - update: Actualizar producto (PUT /api/v1/productos/{id}/) - Solo admin bossa
    - destroy: Eliminar producto (DELETE /api/v1/productos/{id}/) - Solo admin bossa
    
    Filtros:
    - ?search=nombre - Búsqueda en nombre y SKU
    - ?categoria=id - Filtrar por categoría
    - ?stock_bajo=true - Solo productos con stock bajo
    - ?activo=true - Solo productos activos
    """
    queryset = Producto.objects.all().select_related('categoria')
    permission_classes = [IsAdminOrReadOnly]  # Usar permiso personalizado
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['categoria', 'activo']
    search_fields = ['nombre', 'sku', 'descripcion']
    ordering_fields = ['nombre', 'precio', 'stock', 'fecha_creacion']
    ordering = ['nombre']
    
    def get_serializer_class(self):
        """Usar serializer simplificado para list, completo para detail"""
        if self.action == 'list':
            return ProductoListSerializer
        return ProductoSerializer
    
    def get_queryset(self):
        """Filtrar productos según parámetros"""
        queryset = super().get_queryset()
        
        # Filtrar por stock bajo
        stock_bajo = self.request.query_params.get('stock_bajo', None)
        if stock_bajo == 'true':
            queryset = queryset.filter(stock__lte=F('stock_minimo'))
        
        # Filtrar solo activos por defecto (si no se especifica)
        activo = self.request.query_params.get('activo', 'true')
        if activo == 'true':
            queryset = queryset.filter(activo=True)
        
        return queryset
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminBossa])
    def actualizar_stock(self, request, pk: Optional[int] = None) -> Response:
        """
        Endpoint para actualizar stock de un producto.
        Solo administradores pueden usar este endpoint.
        """
        producto = self.get_object()
        cantidad = request.data.get('cantidad')
        tipo = request.data.get('tipo', 'ajuste')  # entrada, salida, ajuste
        
        if cantidad is None:
            return Response(
                {'error': 'Cantidad requerida'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cantidad = int(cantidad)
            stock_anterior = producto.stock
            
            if tipo == 'entrada':
                producto.stock += cantidad
            elif tipo == 'salida':
                producto.stock = max(0, producto.stock - cantidad)
            else:  # ajuste
                producto.stock = cantidad
            
            producto.save()
            
            return Response({
                'success': True,
                'stock_anterior': stock_anterior,
                'stock_nuevo': producto.stock,
                'producto': ProductoSerializer(producto).data
            })
        except ValueError:
            return Response(
                {'error': 'Cantidad debe ser un número'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class CategoriaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar categorías"""
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsAdminOrReadOnly]  # Usar permiso personalizado
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['nombre', 'fecha_creacion']
    ordering = ['nombre']


class VentaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar ventas (solo lectura)
    Para crear ventas, usar el endpoint existente /pos/procesar-venta/
    """
    queryset = Venta.objects.all().select_related('usuario').prefetch_related('items')
    serializer_class = VentaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['metodo_pago', 'cancelada', 'usuario']
    ordering_fields = ['fecha', 'total']
    ordering = ['-fecha']
    
    def get_queryset(self):
        """Filtrar ventas según usuario"""
        queryset = super().get_queryset()
        
        # Si no es admin, solo ver sus propias ventas
        if not es_admin_bossa(self.request.user):
            queryset = queryset.filter(usuario=self.request.user)
        
        return queryset
    
    def get_permissions(self):
        """Usar permiso personalizado para objetos"""
        return [IsAuthenticated(), IsOwnerOrAdmin()]


class CotizacionViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar cotizaciones"""
    queryset = Cotizacion.objects.all().select_related('usuario').prefetch_related('items')
    serializer_class = CotizacionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['estado', 'usuario']
    ordering_fields = ['fecha_creacion', 'total']
    ordering = ['-fecha_creacion']
    
    def get_queryset(self):
        """Filtrar cotizaciones según usuario"""
        queryset = super().get_queryset()
        
        # Si no es admin, solo ver sus propias cotizaciones
        if not es_admin_bossa(self.request.user):
            queryset = queryset.filter(usuario=self.request.user)
        
        return queryset
    
    def get_permissions(self):
        """Permisos: todos pueden crear, solo owner/admin puede editar/eliminar"""
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """Asignar usuario actual al crear cotización"""
        serializer.save(usuario=self.request.user)


class MovimientoStockViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para consultar movimientos de stock (solo lectura)"""
    queryset = MovimientoStock.objects.all().select_related('producto', 'usuario')
    serializer_class = MovimientoStockSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['tipo', 'motivo', 'producto']
    ordering_fields = ['fecha']
    ordering = ['-fecha']


class NotificacionStockViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para consultar notificaciones de stock bajo"""
    queryset = NotificacionStock.objects.all().select_related('producto')
    serializer_class = NotificacionStockSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['vista', 'notificada']
    ordering_fields = ['fecha']
    ordering = ['-fecha']
    
    @action(detail=True, methods=['post'])
    def marcar_vista(self, request, pk: Optional[int] = None) -> Response:
        """Marcar notificación como vista"""
        notificacion = self.get_object()
        notificacion.vista = True
        notificacion.save()
        return Response({'success': True})


class ProveedorViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar proveedores"""
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [IsAdminOrReadOnly]  # Usar permiso personalizado
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'rut', 'email']
    ordering_fields = ['nombre', 'fecha_creacion']
    ordering = ['nombre']

