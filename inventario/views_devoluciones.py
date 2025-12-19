"""
Vistas para el sistema de devoluciones
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from .models import Venta, ItemVenta, Devolucion, ItemDevolucion, Cliente
from .utils import es_admin_bossa, logger


@login_required
def listar_devoluciones(request):
    """Lista todas las devoluciones"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('inicio')
    
    devoluciones = Devolucion.objects.all().select_related('venta', 'cliente', 'procesado_por').order_by('-fecha_solicitud')
    
    # Filtros
    estado = request.GET.get('estado', '')
    venta_id = request.GET.get('venta_id', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    
    if estado:
        devoluciones = devoluciones.filter(estado=estado)
    if venta_id:
        devoluciones = devoluciones.filter(venta_id=venta_id)
    if fecha_desde:
        devoluciones = devoluciones.filter(fecha_solicitud__date__gte=fecha_desde)
    if fecha_hasta:
        devoluciones = devoluciones.filter(fecha_solicitud__date__lte=fecha_hasta)
    
    # Paginación
    paginator = Paginator(devoluciones, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_devoluciones = devoluciones.count()
    pendientes = devoluciones.filter(estado='pendiente').count()
    procesadas = devoluciones.filter(estado='procesada').count()
    monto_total = sum(float(d.monto_devolver) for d in devoluciones.filter(estado='procesada'))
    
    context = {
        'page_obj': page_obj,
        'estado': estado,
        'venta_id': venta_id,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'total_devoluciones': total_devoluciones,
        'pendientes': pendientes,
        'procesadas': procesadas,
        'monto_total': monto_total,
        'es_admin': True,
    }
    return render(request, 'inventario/listar_devoluciones.html', context)


@login_required
def crear_devolucion(request, venta_id=None):
    """Crear una nueva devolución"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('inicio')
    
    venta = None
    if venta_id:
        venta = get_object_or_404(Venta.objects.select_related('cliente'), id=venta_id)
    
    if request.method == 'POST':
        venta_id_post = request.POST.get('venta_id')
        tipo_devolucion = request.POST.get('tipo_devolucion')
        metodo_reembolso = request.POST.get('metodo_reembolso')
        motivo = request.POST.get('motivo', '').strip()
        notas = request.POST.get('notas', '').strip() or None
        
        try:
            venta = get_object_or_404(Venta.objects.select_related('cliente'), id=venta_id_post)
            
            # Calcular monto a devolver
            if tipo_devolucion == 'completa':
                monto_devolver = venta.total
            else:
                # Parcial - calcular desde items seleccionados
                items_seleccionados = request.POST.getlist('items_seleccionados')
                monto_devolver = Decimal('0')
                for item_id in items_seleccionados:
                    item = get_object_or_404(ItemVenta, id=item_id, venta=venta)
                    cantidad_devolver = int(request.POST.get(f'cantidad_{item_id}', item.cantidad))
                    if cantidad_devolver > item.cantidad:
                        cantidad_devolver = item.cantidad
                    monto_devolver += item.precio_unitario * cantidad_devolver
            
            # Crear devolución
            devolucion = Devolucion.objects.create(
                venta=venta,
                cliente=venta.cliente,
                tipo_devolucion=tipo_devolucion,
                monto_devolver=monto_devolver,
                metodo_reembolso=metodo_reembolso,
                motivo=motivo,
                notas=notas,
                estado='pendiente'
            )
            
            # Crear items de devolución
            if tipo_devolucion == 'completa':
                for item_venta in venta.items.all():
                    ItemDevolucion.objects.create(
                        devolucion=devolucion,
                        item_venta=item_venta,
                        cantidad=item_venta.cantidad
                    )
            else:
                items_seleccionados = request.POST.getlist('items_seleccionados')
                for item_id in items_seleccionados:
                    item_venta = get_object_or_404(ItemVenta, id=item_id, venta=venta)
                    cantidad_devolver = int(request.POST.get(f'cantidad_{item_id}', item_venta.cantidad))
                    if cantidad_devolver > 0:
                        ItemDevolucion.objects.create(
                            devolucion=devolucion,
                            item_venta=item_venta,
                            cantidad=min(cantidad_devolver, item_venta.cantidad),
                            motivo=request.POST.get(f'motivo_{item_id}', '').strip() or None
                        )
            
            messages.success(request, f'Devolución #{devolucion.numero_devolucion} creada exitosamente. Pendiente de procesamiento.')
            return redirect('detalle_devolucion', devolucion_id=devolucion.id)
            
        except Exception as e:
            logger.error(f'Error al crear devolución: {str(e)}')
            messages.error(request, f'Error al crear devolución: {str(e)}')
    
    # Si hay venta, obtener sus items
    items_venta = []
    if venta:
        items_venta = venta.items.all().select_related('producto')
    
    # Obtener ventas recientes para selección
    ventas_recientes = Venta.objects.filter(cancelada=False).select_related('cliente').order_by('-fecha')[:50]
    
    context = {
        'venta': venta,
        'items_venta': items_venta,
        'ventas_recientes': ventas_recientes,
        'es_admin': True,
    }
    return render(request, 'inventario/crear_devolucion.html', context)


@login_required
def detalle_devolucion(request, devolucion_id):
    """Detalle de una devolución específica"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('inicio')
    
    devolucion = get_object_or_404(
        Devolucion.objects.select_related('venta', 'cliente', 'procesado_por'),
        id=devolucion_id
    )
    items = devolucion.items.all().select_related('item_venta__producto')
    
    context = {
        'devolucion': devolucion,
        'items': items,
        'es_admin': True,
    }
    return render(request, 'inventario/detalle_devolucion.html', context)


@login_required
def procesar_devolucion(request, devolucion_id):
    """Procesa una devolución: actualiza stock y maneja reembolso"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('inicio')
    
    devolucion = get_object_or_404(Devolucion, id=devolucion_id)
    
    if devolucion.estado != 'pendiente':
        messages.error(request, 'Solo se pueden procesar devoluciones pendientes.')
        return redirect('detalle_devolucion', devolucion_id=devolucion.id)
    
    try:
        devolucion.procesar(request.user)
        messages.success(request, f'Devolución #{devolucion.numero_devolucion} procesada exitosamente. Stock actualizado.')
        logger.info(f'Devolución #{devolucion.numero_devolucion} procesada por {request.user.username}')
    except Exception as e:
        logger.error(f'Error al procesar devolución: {str(e)}')
        messages.error(request, f'Error al procesar devolución: {str(e)}')
    
    return redirect('detalle_devolucion', devolucion_id=devolucion.id)


@login_required
def rechazar_devolucion(request, devolucion_id):
    """Rechaza una devolución"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('inicio')
    
    devolucion = get_object_or_404(Devolucion, id=devolucion_id)
    
    if devolucion.estado != 'pendiente':
        messages.error(request, 'Solo se pueden rechazar devoluciones pendientes.')
        return redirect('detalle_devolucion', devolucion_id=devolucion.id)
    
    motivo_rechazo = request.POST.get('motivo_rechazo', '').strip()
    
    try:
        devolucion.rechazar(request.user, motivo_rechazo)
        messages.success(request, f'Devolución #{devolucion.numero_devolucion} rechazada.')
        logger.info(f'Devolución #{devolucion.numero_devolucion} rechazada por {request.user.username}')
    except Exception as e:
        logger.error(f'Error al rechazar devolución: {str(e)}')
        messages.error(request, f'Error al rechazar devolución: {str(e)}')
    
    return redirect('detalle_devolucion', devolucion_id=devolucion.id)

