"""
Vistas para el historial de precios de productos
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import Producto, HistorialPrecio
from .utils import es_admin_bossa, logger


@login_required
def historial_precios_producto(request, producto_id):
    """Muestra el historial de precios de un producto específico"""
    producto = get_object_or_404(Producto, id=producto_id)
    historial = HistorialPrecio.objects.filter(producto=producto).select_related('usuario').order_by('-fecha')
    
    # Filtros
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    
    if fecha_desde:
        historial = historial.filter(fecha__date__gte=fecha_desde)
    if fecha_hasta:
        historial = historial.filter(fecha__date__lte=fecha_hasta)
    
    # Paginación
    paginator = Paginator(historial, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    if historial.exists():
        primer_precio = historial.last()
        ultimo_precio = historial.first()
        cambio_total = float(ultimo_precio.precio_nuevo) - float(primer_precio.precio_anterior if primer_precio.precio_anterior > 0 else primer_precio.precio_nuevo)
        porcentaje_cambio_total = ((float(ultimo_precio.precio_nuevo) - float(primer_precio.precio_anterior if primer_precio.precio_anterior > 0 else primer_precio.precio_nuevo)) / float(primer_precio.precio_anterior if primer_precio.precio_anterior > 0 else primer_precio.precio_nuevo)) * 100 if primer_precio.precio_anterior > 0 or primer_precio.precio_nuevo > 0 else 0
    else:
        cambio_total = 0
        porcentaje_cambio_total = 0
    
    context = {
        'producto': producto,
        'page_obj': page_obj,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'cambio_total': cambio_total,
        'porcentaje_cambio_total': porcentaje_cambio_total,
        'es_admin': es_admin_bossa(request.user),
    }
    return render(request, 'inventario/historial_precios.html', context)


@login_required
def historial_precios_general(request):
    """Muestra el historial de precios de todos los productos (solo admin)"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('inicio')
    
    historial = HistorialPrecio.objects.all().select_related('producto', 'usuario').order_by('-fecha')
    
    # Filtros
    producto_id = request.GET.get('producto_id', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    busqueda = request.GET.get('q', '')
    
    if producto_id:
        historial = historial.filter(producto_id=producto_id)
    if fecha_desde:
        historial = historial.filter(fecha__date__gte=fecha_desde)
    if fecha_hasta:
        historial = historial.filter(fecha__date__lte=fecha_hasta)
    if busqueda:
        historial = historial.filter(
            Q(producto__nombre__icontains=busqueda) |
            Q(producto__sku__icontains=busqueda) |
            Q(motivo__icontains=busqueda)
        )
    
    # Paginación
    paginator = Paginator(historial, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Productos para el filtro
    productos = Producto.objects.filter(activo=True).order_by('nombre')[:100]
    
    context = {
        'page_obj': page_obj,
        'productos': productos,
        'producto_id': producto_id,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'busqueda': busqueda,
        'es_admin': True,
    }
    return render(request, 'inventario/historial_precios_general.html', context)

