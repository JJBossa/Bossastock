from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum, Count, F
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from datetime import timedelta
from decimal import Decimal
from .models import Producto, Venta, ItemVenta, MovimientoStock
from .utils import es_admin_bossa, registrar_cambio, logger

@login_required
def punto_venta(request):
    """Vista principal del punto de venta - Accesible para todos los usuarios"""
    
    # Obtener productos activos para búsqueda
    productos = Producto.objects.filter(activo=True).order_by('nombre')
    
    context = {
        'productos': productos,
        'es_admin': es_admin_bossa(request.user),
    }
    
    return render(request, 'inventario/punto_venta.html', context)

@login_required
def buscar_producto_pos(request):
    """API para buscar producto por código de barras en el POS - Accesible para todos"""
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    codigo = request.POST.get('codigo', '').strip()
    
    if not codigo:
        return JsonResponse({'error': 'Código requerido'}, status=400)
    
    try:
        # Buscar por SKU (código de barras)
        producto = Producto.objects.get(sku=codigo, activo=True)
        
        # Verificar stock
        if producto.stock <= 0:
            return JsonResponse({
                'encontrado': True,
                'sin_stock': True,
                'producto': {
                    'id': producto.id,
                    'nombre': producto.nombre,
                    'precio': float(producto.precio_promo or producto.precio),
                    'stock': producto.stock,
                },
                'mensaje': 'Producto sin stock disponible'
            })
        
        return JsonResponse({
            'encontrado': True,
            'producto': {
                'id': producto.id,
                'nombre': producto.nombre,
                'precio': float(producto.precio_promo or producto.precio),
                'precio_normal': float(producto.precio),
                'precio_promo': float(producto.precio_promo) if producto.precio_promo else None,
                'stock': producto.stock,
                'sku': producto.sku,
            }
        })
    except Producto.DoesNotExist:
        return JsonResponse({
            'encontrado': False,
            'mensaje': f'Producto con código {codigo} no encontrado'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@transaction.atomic
def procesar_venta(request):
    """Procesa una venta y descuenta el stock - Accesible para todos"""
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        import json
        items_data = json.loads(request.POST.get('items', '[]'))
        subtotal = Decimal(request.POST.get('subtotal', '0'))
        descuento = Decimal(request.POST.get('descuento', '0'))
        total = Decimal(request.POST.get('total', '0'))
        metodo_pago = request.POST.get('metodo_pago', 'efectivo')
        monto_recibido = Decimal(request.POST.get('monto_recibido', '0'))
        cambio = Decimal(request.POST.get('cambio', '0'))
        notas = request.POST.get('notas', '')
        
        if not items_data:
            return JsonResponse({'error': 'No hay items en la venta'}, status=400)
        
        # Crear venta
        venta = Venta.objects.create(
            usuario=request.user,
            subtotal=subtotal,
            descuento=descuento,
            total=total,
            metodo_pago=metodo_pago,
            monto_recibido=monto_recibido,
            cambio=cambio,
            notas=notas
        )
        
        # Procesar items y descontar stock
        # Usar select_for_update() para bloquear registros y evitar condiciones de carrera
        items_creados = []
        productos_actualizados = []
        
        for item_data in items_data:
            producto_id = item_data.get('producto_id')
            cantidad = int(item_data.get('cantidad', 1))
            precio_unitario = Decimal(item_data.get('precio', '0'))
            
            # Bloquear el registro del producto hasta que termine la transacción
            # Esto previene que otro usuario venda el mismo producto simultáneamente
            try:
                producto = Producto.objects.select_for_update().get(id=producto_id)
            except Producto.DoesNotExist:
                venta.delete()
                logger.error(f'Producto {producto_id} no encontrado al procesar venta', 
                           extra={'user': request.user.username, 'venta_id': venta.id})
                return JsonResponse({
                    'error': f'Producto no encontrado (ID: {producto_id})'
                }, status=400)
            
            # Verificar stock disponible ANTES de descontar
            if producto.stock < cantidad:
                venta.delete()  # Cancelar venta si no hay stock
                logger.warning(f'Stock insuficiente para {producto.nombre}. Disponible: {producto.stock}, Solicitado: {cantidad}',
                             extra={'user': request.user.username, 'producto_id': producto_id, 'venta_id': venta.id})
                return JsonResponse({
                    'error': f'Stock insuficiente para {producto.nombre}. Disponible: {producto.stock}, Solicitado: {cantidad}'
                }, status=400)
            
            stock_anterior = producto.stock
            producto.stock -= cantidad
            producto.save()
            productos_actualizados.append(producto)
            
            # Crear item de venta
            item = ItemVenta.objects.create(
                venta=venta,
                producto=producto,
                nombre_producto=producto.nombre,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                stock_anterior=stock_anterior,
                stock_despues=producto.stock
            )
            items_creados.append(item)
            
            # Registrar movimiento de stock
            MovimientoStock.objects.create(
                producto=producto,
                tipo='salida',
                cantidad=cantidad,
                motivo='venta',
                stock_anterior=stock_anterior,
                stock_nuevo=producto.stock,
                usuario=request.user,
                notas=f'Venta #{venta.numero_venta}'
            )
            
            # Registrar en historial
            registrar_cambio(
                producto,
                request.user,
                'stock',
                'stock',
                stock_anterior,
                producto.stock,
                f'Venta: {cantidad} unidades - Venta #{venta.numero_venta}'
            )
        
        logger.info(f'Venta #{venta.numero_venta} procesada exitosamente. Total: ${venta.total}',
                   extra={'user': request.user.username, 'venta_id': venta.id, 'total': float(venta.total)})
        
        return JsonResponse({
            'success': True,
            'venta_id': venta.id,
            'numero_venta': venta.numero_venta,
            'total': float(venta.total),
            'mensaje': f'Venta #{venta.numero_venta} procesada exitosamente'
        })
        
    except Producto.DoesNotExist as e:
        logger.error(f'Producto no encontrado al procesar venta: {str(e)}',
                    exc_info=True, extra={'user': request.user.username})
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)
    except ValidationError as e:
        logger.warning(f'Error de validación al procesar venta: {str(e)}',
                      extra={'user': request.user.username})
        return JsonResponse({'error': str(e)}, status=400)
    except ValueError as e:
        logger.warning(f'Error de valor al procesar venta: {str(e)}',
                      extra={'user': request.user.username})
        return JsonResponse({'error': f'Datos inválidos: {str(e)}'}, status=400)
    except Exception as e:
        logger.error(f'Error inesperado al procesar venta: {str(e)}',
                    exc_info=True, extra={'user': request.user.username})
        return JsonResponse({'error': 'Error interno del servidor. Por favor, intente nuevamente.'}, status=500)

@login_required
def listar_ventas(request):
    """Lista todas las ventas - Usuarios normales solo ven sus propias ventas"""
    
    # Usuarios normales solo ven sus propias ventas
    if es_admin_bossa(request.user):
        ventas = Venta.objects.select_related('usuario').prefetch_related('items').all()
    else:
        ventas = Venta.objects.select_related('usuario').prefetch_related('items').filter(usuario=request.user)
    
    # Filtros
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    metodo_pago = request.GET.get('metodo_pago', '')
    numero_venta = request.GET.get('numero_venta', '')
    
    if fecha_desde:
        ventas = ventas.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        ventas = ventas.filter(fecha__lte=fecha_hasta)
    if metodo_pago:
        ventas = ventas.filter(metodo_pago=metodo_pago)
    if numero_venta:
        ventas = ventas.filter(numero_venta__icontains=numero_venta)
    
    # Estadísticas
    total_ventas = ventas.aggregate(Sum('total'))['total__sum'] or 0
    total_ventas_count = ventas.count()
    
    # Paginación
    paginator = Paginator(ventas, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'ventas': page_obj,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'metodo_pago': metodo_pago,
        'numero_venta': numero_venta,
        'total_ventas': total_ventas,
        'total_ventas_count': total_ventas_count,
        'es_admin': es_admin_bossa(request.user),
    }
    
    return render(request, 'inventario/listar_ventas.html', context)

@login_required
def detalle_venta(request, venta_id):
    """Detalle de una venta - Usuarios normales solo ven sus propias ventas"""
    if es_admin_bossa(request.user):
        venta = get_object_or_404(Venta, id=venta_id)
    else:
        venta = get_object_or_404(Venta, id=venta_id, usuario=request.user)
    items = venta.items.select_related('producto').all()
    
    context = {
        'venta': venta,
        'items': items,
        'es_admin': es_admin_bossa(request.user),
    }
    
    return render(request, 'inventario/detalle_venta.html', context)

@login_required
def cancelar_venta(request, venta_id):
    """Cancela una venta y restaura el stock - Solo admin o el mismo vendedor"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Usuarios normales solo pueden cancelar sus propias ventas
        if es_admin_bossa(request.user):
            venta = get_object_or_404(Venta, id=venta_id)
        else:
            venta = get_object_or_404(Venta, id=venta_id, usuario=request.user)
        
        if venta.cancelada:
            return JsonResponse({'error': 'La venta ya está cancelada'}, status=400)
        
        # Restaurar stock de cada item
        for item in venta.items.all():
            if item.producto:
                stock_anterior = item.producto.stock
                item.producto.stock += item.cantidad
                item.producto.save()
                
                # Registrar movimiento
                MovimientoStock.objects.create(
                    producto=item.producto,
                    tipo='entrada',
                    cantidad=item.cantidad,
                    motivo='devolucion_cliente',
                    stock_anterior=stock_anterior,
                    stock_nuevo=item.producto.stock,
                    usuario=request.user,
                    notas=f'Cancelación de venta #{venta.numero_venta}'
                )
        
        venta.cancelada = True
        venta.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': f'Venta #{venta.numero_venta} cancelada exitosamente. Stock restaurado.'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Error al cancelar venta: {str(e)}'}, status=500)

@login_required
def limpiar_historial_ventas(request):
    """Elimina todas las ventas del sistema - Solo admin"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('listar_ventas')
    
    if request.method == 'POST':
        try:
            # Contar ventas antes de eliminar
            total_ventas = Venta.objects.count()
            
            # Eliminar todas las ventas (esto también eliminará los items relacionados por CASCADE)
            Venta.objects.all().delete()
            
            messages.success(request, f'Se eliminaron {total_ventas} venta(s) del historial.')
            return redirect('listar_ventas')
        except Exception as e:
            messages.error(request, f'Error al limpiar el historial: {str(e)}')
            return redirect('listar_ventas')
    
    # Si es GET, redirigir
    return redirect('listar_ventas')

