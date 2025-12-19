"""
Vistas para sistema de notificaciones en tiempo real
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count, F
from django.utils import timezone
from datetime import timedelta
from .models import NotificacionUsuario, CuentaPorCobrar, OrdenCompra, Producto
from .utils import es_admin_bossa, logger

@login_required
def centro_notificaciones(request):
    """Centro de notificaciones del usuario"""
    notificaciones = NotificacionUsuario.objects.filter(
        usuario=request.user
    ).order_by('-fecha', 'leida')[:50]
    
    no_leidas = notificaciones.filter(leida=False).count()
    
    context = {
        'notificaciones': notificaciones,
        'no_leidas': no_leidas,
        'es_admin': es_admin_bossa(request.user)
    }
    
    return render(request, 'inventario/centro_notificaciones.html', context)

@login_required
def marcar_notificacion_leida(request, notificacion_id):
    """Marca una notificación como leída"""
    try:
        notificacion = NotificacionUsuario.objects.get(
            id=notificacion_id,
            usuario=request.user
        )
        notificacion.leida = True
        notificacion.save()
        return JsonResponse({'success': True})
    except NotificacionUsuario.DoesNotExist:
        return JsonResponse({'error': 'Notificación no encontrada'}, status=404)

@login_required
def marcar_todas_leidas(request):
    """Marca todas las notificaciones como leídas"""
    NotificacionUsuario.objects.filter(
        usuario=request.user,
        leida=False
    ).update(leida=True)
    
    return JsonResponse({'success': True})

@login_required
def obtener_notificaciones_api(request):
    """API para obtener notificaciones no leídas (para polling)"""
    notificaciones = NotificacionUsuario.objects.filter(
        usuario=request.user,
        leida=False
    ).order_by('-fecha')[:10]
    
    datos = [
        {
            'id': n.id,
            'tipo': n.tipo,
            'titulo': n.titulo,
            'mensaje': n.mensaje,
            'fecha': n.fecha.isoformat(),
            'url': n.url_relacionada or ''
        }
        for n in notificaciones
    ]
    
    return JsonResponse({
        'notificaciones': datos,
        'total': notificaciones.count()
    })

def crear_notificaciones_automaticas():
    """Crea notificaciones automáticas para eventos del sistema"""
    from django.contrib.auth.models import User
    
    # Notificaciones de cuentas por cobrar vencidas
    cuentas_vencidas = CuentaPorCobrar.objects.filter(
        estado__in=['pendiente', 'parcial'],
        fecha_vencimiento__lt=timezone.now().date()
    )
    
    for cuenta in cuentas_vencidas:
        if cuenta.cliente:
            # Buscar usuarios admin para notificar
            admins = User.objects.filter(username='bossa')
            for admin in admins:
                NotificacionUsuario.objects.get_or_create(
                    usuario=admin,
                    tipo='cuenta_vencida',
                    titulo=f'Cuenta por Cobrar Vencida',
                    mensaje=f'La cuenta #{cuenta.id} del cliente {cuenta.cliente.nombre} está vencida',
                    url_relacionada=f'/cuentas-cobrar/{cuenta.id}/',
                    defaults={
                        'leida': False,
                        'datos_adicionales': {'cuenta_id': cuenta.id}
                    }
                )
    
    # Notificaciones de stock bajo
    productos_bajo_stock = Producto.objects.filter(
        activo=True,
        stock__lte=F('stock_minimo'),
        stock__gt=0
    )
    
    for producto in productos_bajo_stock:
        admins = User.objects.filter(username='bossa')
        for admin in admins:
            NotificacionUsuario.objects.get_or_create(
                usuario=admin,
                tipo='stock_bajo',
                titulo=f'Stock Bajo: {producto.nombre}',
                mensaje=f'El producto {producto.nombre} tiene stock bajo ({producto.stock} unidades)',
                url_relacionada=f'/producto/{producto.id}/',
                defaults={
                    'leida': False,
                    'datos_adicionales': {'producto_id': producto.id}
                }
            )
    
    # Notificaciones de órdenes de compra pendientes
    ordenes_pendientes = OrdenCompra.objects.filter(
        estado__in=['pendiente', 'parcial']
    )
    
    for orden in ordenes_pendientes:
        admins = User.objects.filter(username='bossa')
        for admin in admins:
            NotificacionUsuario.objects.get_or_create(
                usuario=admin,
                tipo='orden_pendiente',
                titulo=f'Orden de Compra Pendiente',
                mensaje=f'La orden #{orden.numero_orden} está pendiente',
                url_relacionada=f'/compras/{orden.id}/',
                defaults={
                    'leida': False,
                    'datos_adicionales': {'orden_id': orden.id}
                }
            )

