"""
Vistas para búsqueda global mejorada
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from .models import (
    Producto, Cliente, Venta, Cotizacion, 
    HistorialBusqueda, LogAccion
)
from .utils import normalizar_texto, logger, es_admin_bossa
import json

def get_client_ip(request):
    """Obtiene la IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@login_required
def busqueda_global(request):
    """Vista principal de búsqueda global"""
    query = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', 'todos')  # todos, productos, clientes, ventas, cotizaciones
    
    resultados = {
        'productos': [],
        'clientes': [],
        'ventas': [],
        'cotizaciones': [],
        'total': 0
    }
    
    if query and len(query) >= 2:
        # Buscar en todos los módulos
        if tipo == 'todos' or tipo == 'productos':
            productos = Producto.objects.filter(
                activo=True
            ).filter(
                Q(nombre__icontains=query) |
                Q(sku__icontains=query) |
                Q(descripcion__icontains=query)
            ).select_related('categoria')[:10]
            
            resultados['productos'] = [
                {
                    'id': p.id,
                    'nombre': p.nombre,
                    'sku': p.sku or '',
                    'precio': float(p.precio_promo or p.precio),
                    'stock': p.stock,
                    'categoria': p.categoria.nombre if p.categoria else '',
                    'url': f'/producto/{p.id}/',
                    'tipo': 'producto'
                }
                for p in productos
            ]
        
        if tipo == 'todos' or tipo == 'clientes':
            clientes = Cliente.objects.filter(
                activo=True
            ).filter(
                Q(nombre__icontains=query) |
                Q(rut__icontains=query) |
                Q(email__icontains=query) |
                Q(telefono__icontains=query)
            )[:10]
            
            resultados['clientes'] = [
                {
                    'id': c.id,
                    'nombre': c.nombre,
                    'rut': c.rut or '',
                    'email': c.email or '',
                    'telefono': c.telefono or '',
                    'url': f'/clientes/{c.id}/',
                    'tipo': 'cliente'
                }
                for c in clientes
            ]
        
        if tipo == 'todos' or tipo == 'ventas':
            ventas = Venta.objects.filter(
                cancelada=False
            ).filter(
                Q(numero_venta__icontains=query) |
                Q(cliente__nombre__icontains=query) |
                Q(notas__icontains=query)
            ).select_related('cliente', 'usuario')[:10]
            
            resultados['ventas'] = [
                {
                    'id': v.id,
                    'numero_venta': v.numero_venta,
                    'cliente': v.cliente.nombre if v.cliente else 'Cliente General',
                    'total': float(v.total),
                    'fecha': v.fecha.strftime('%d/%m/%Y %H:%M'),
                    'url': f'/ventas/{v.id}/',
                    'tipo': 'venta'
                }
                for v in ventas
            ]
        
        if tipo == 'todos' or tipo == 'cotizaciones':
            cotizaciones = Cotizacion.objects.filter(
                Q(numero_cotizacion__icontains=query) |
                Q(cliente__nombre__icontains=query) |
                Q(cliente_nombre__icontains=query) |
                Q(notas__icontains=query)
            ).select_related('cliente')[:10]
            
            resultados['cotizaciones'] = [
                {
                    'id': c.id,
                    'numero_cotizacion': c.numero_cotizacion,
                    'cliente': c.cliente.nombre if c.cliente else c.cliente_nombre or 'Cliente General',
                    'total': float(c.total),
                    'fecha': c.fecha_creacion.strftime('%d/%m/%Y'),
                    'url': f'/cotizaciones/{c.id}/',
                    'tipo': 'cotizacion'
                }
                for c in cotizaciones
            ]
        
        # Calcular total
        resultados['total'] = (
            len(resultados['productos']) +
            len(resultados['clientes']) +
            len(resultados['ventas']) +
            len(resultados['cotizaciones'])
        )
        
        # Guardar en historial
        if resultados['total'] > 0:
            HistorialBusqueda.objects.create(
                usuario=request.user,
                query=query,
                tipo='global',
                resultados=resultados['total']
            )
            
            # Registrar en logs
            LogAccion.objects.create(
                usuario=request.user,
                tipo_accion='buscar',
                modulo='sistema',
                descripcion=f'Búsqueda global: "{query}" - {resultados["total"]} resultados',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
    
    # Obtener historial reciente del usuario
    historial_reciente = HistorialBusqueda.objects.filter(
        usuario=request.user
    ).order_by('-fecha')[:10]
    
    context = {
        'query': query,
        'tipo': tipo,
        'resultados': resultados,
        'historial_reciente': historial_reciente,
        'es_admin': es_admin_bossa(request.user)
    }
    
    return render(request, 'inventario/busqueda_global.html', context)

@login_required
def busqueda_global_api(request):
    """API para búsqueda global con autocompletado"""
    query = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', 'todos')
    
    if len(query) < 2:
        return JsonResponse({'resultados': []})
    
    resultados = []
    
    try:
        # Buscar productos
        if tipo == 'todos' or tipo == 'productos':
            productos = Producto.objects.filter(
                activo=True
            ).filter(
                Q(nombre__icontains=query) |
                Q(sku__icontains=query)
            ).select_related('categoria')[:5]
            
            for p in productos:
                resultados.append({
                    'id': p.id,
                    'texto': f"{p.nombre} ({p.sku or 'Sin SKU'})",
                    'subtitulo': f"${p.precio_promo or p.precio:,.0f} - Stock: {p.stock}",
                    'tipo': 'producto',
                    'url': f'/producto/{p.id}/',
                    'icono': 'bi-box-seam'
                })
        
        # Buscar clientes
        if tipo == 'todos' or tipo == 'clientes':
            clientes = Cliente.objects.filter(
                activo=True
            ).filter(
                Q(nombre__icontains=query) |
                Q(rut__icontains=query)
            )[:5]
            
            for c in clientes:
                resultados.append({
                    'id': c.id,
                    'texto': c.nombre,
                    'subtitulo': f"RUT: {c.rut or 'N/A'}",
                    'tipo': 'cliente',
                    'url': f'/clientes/{c.id}/',
                    'icono': 'bi-person'
                })
        
        # Buscar ventas
        if tipo == 'todos' or tipo == 'ventas':
            ventas = Venta.objects.filter(
                cancelada=False,
                numero_venta__icontains=query
            ).select_related('cliente')[:5]
            
            for v in ventas:
                resultados.append({
                    'id': v.id,
                    'texto': f"Venta #{v.numero_venta}",
                    'subtitulo': f"${v.total:,.0f} - {v.cliente.nombre if v.cliente else 'Cliente General'}",
                    'tipo': 'venta',
                    'url': f'/ventas/{v.id}/',
                    'icono': 'bi-receipt'
                })
        
        return JsonResponse({'resultados': resultados})
        
    except Exception as e:
        logger.error(f'Error en búsqueda global API: {str(e)}', extra={'user': request.user.username})
        return JsonResponse({'resultados': [], 'error': str(e)})

@login_required
def historial_busquedas(request):
    """Vista para ver el historial de búsquedas del usuario"""
    busquedas = HistorialBusqueda.objects.filter(
        usuario=request.user
    ).order_by('-fecha')[:50]
    
    context = {
        'busquedas': busquedas,
        'es_admin': es_admin_bossa(request.user)
    }
    
    return render(request, 'inventario/historial_busquedas.html', context)

