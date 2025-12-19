"""
Vistas para ajustes de inventario
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.db import transaction
from .models import Producto, AjusteInventario
from .utils import es_admin_bossa, logger


@login_required
def listar_ajustes(request):
    """Lista todos los ajustes de inventario"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('inicio')
    
    ajustes = AjusteInventario.objects.all().select_related('producto', 'solicitado_por', 'aprobado_por').order_by('-fecha_solicitud')
    
    # Filtros
    estado = request.GET.get('estado', '')
    producto_id = request.GET.get('producto_id', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    
    if estado:
        ajustes = ajustes.filter(estado=estado)
    if producto_id:
        ajustes = ajustes.filter(producto_id=producto_id)
    if fecha_desde:
        ajustes = ajustes.filter(fecha_solicitud__date__gte=fecha_desde)
    if fecha_hasta:
        ajustes = ajustes.filter(fecha_solicitud__date__lte=fecha_hasta)
    
    # Paginación
    paginator = Paginator(ajustes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_ajustes = ajustes.count()
    pendientes = ajustes.filter(estado='pendiente').count()
    aprobados = ajustes.filter(estado='aprobado').count()
    
    # Productos para el filtro
    productos = Producto.objects.filter(activo=True).order_by('nombre')[:100]
    
    context = {
        'page_obj': page_obj,
        'productos': productos,
        'estado': estado,
        'producto_id': producto_id,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'total_ajustes': total_ajustes,
        'pendientes': pendientes,
        'aprobados': aprobados,
        'es_admin': True,
    }
    return render(request, 'inventario/listar_ajustes.html', context)


@login_required
def crear_ajuste(request):
    """Crear un nuevo ajuste de inventario"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('inicio')
    
    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        tipo_ajuste = request.POST.get('tipo_ajuste')
        cantidad_nueva = request.POST.get('cantidad_nueva')
        motivo = request.POST.get('motivo', '').strip()
        notas = request.POST.get('notas', '').strip() or None
        
        try:
            producto = get_object_or_404(Producto, id=producto_id)
            cantidad_nueva = int(cantidad_nueva)
            
            if cantidad_nueva < 0:
                messages.error(request, 'La cantidad no puede ser negativa.')
                return redirect('crear_ajuste')
            
            # Crear ajuste
            ajuste = AjusteInventario.objects.create(
                producto=producto,
                tipo_ajuste=tipo_ajuste,
                cantidad_anterior=producto.stock,
                cantidad_nueva=cantidad_nueva,
                motivo=motivo,
                notas=notas,
                solicitado_por=request.user,
                estado='pendiente'
            )
            
            messages.success(request, f'Ajuste #{ajuste.numero_ajuste} creado exitosamente. Pendiente de aprobación.')
            return redirect('detalle_ajuste', ajuste_id=ajuste.id)
            
        except ValueError:
            messages.error(request, 'La cantidad debe ser un número válido.')
        except Exception as e:
            logger.error(f'Error al crear ajuste: {str(e)}')
            messages.error(request, f'Error al crear ajuste: {str(e)}')
    
    productos = Producto.objects.filter(activo=True).order_by('nombre')
    
    context = {
        'productos': productos,
        'es_admin': True,
    }
    return render(request, 'inventario/crear_ajuste.html', context)


@login_required
def detalle_ajuste(request, ajuste_id):
    """Detalle de un ajuste específico"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('inicio')
    
    ajuste = get_object_or_404(
        AjusteInventario.objects.select_related('producto', 'solicitado_por', 'aprobado_por'),
        id=ajuste_id
    )
    
    context = {
        'ajuste': ajuste,
        'es_admin': True,
    }
    return render(request, 'inventario/detalle_ajuste.html', context)


@login_required
def aprobar_ajuste(request, ajuste_id):
    """Aprueba un ajuste de inventario"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('inicio')
    
    ajuste = get_object_or_404(AjusteInventario, id=ajuste_id)
    
    if ajuste.estado != 'pendiente':
        messages.error(request, 'Solo se pueden aprobar ajustes pendientes.')
        return redirect('detalle_ajuste', ajuste_id=ajuste.id)
    
    try:
        ajuste.aprobar(request.user)
        messages.success(request, f'Ajuste #{ajuste.numero_ajuste} aprobado exitosamente. Stock actualizado.')
        logger.info(f'Ajuste #{ajuste.numero_ajuste} aprobado por {request.user.username}')
    except Exception as e:
        logger.error(f'Error al aprobar ajuste: {str(e)}')
        messages.error(request, f'Error al aprobar ajuste: {str(e)}')
    
    return redirect('detalle_ajuste', ajuste_id=ajuste.id)


@login_required
def rechazar_ajuste(request, ajuste_id):
    """Rechaza un ajuste de inventario"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('inicio')
    
    ajuste = get_object_or_404(AjusteInventario, id=ajuste_id)
    
    if ajuste.estado != 'pendiente':
        messages.error(request, 'Solo se pueden rechazar ajustes pendientes.')
        return redirect('detalle_ajuste', ajuste_id=ajuste.id)
    
    motivo_rechazo = request.POST.get('motivo_rechazo', '').strip()
    
    try:
        ajuste.rechazar(request.user, motivo_rechazo)
        messages.success(request, f'Ajuste #{ajuste.numero_ajuste} rechazado.')
        logger.info(f'Ajuste #{ajuste.numero_ajuste} rechazado por {request.user.username}')
    except Exception as e:
        logger.error(f'Error al rechazar ajuste: {str(e)}')
        messages.error(request, f'Error al rechazar ajuste: {str(e)}')
    
    return redirect('detalle_ajuste', ajuste_id=ajuste.id)

