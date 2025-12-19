from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count, F, Avg
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from .models import Producto, MovimientoStock
from .utils import es_admin_bossa, registrar_cambio

@login_required
@transaction.atomic
def registrar_movimiento_stock(request, producto_id):
    """Registra un movimiento de stock (entrada/salida)"""
    if not es_admin_bossa(request.user):
        return JsonResponse({'error': 'No tienes permisos'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    producto = get_object_or_404(Producto, id=producto_id)
    tipo = request.POST.get('tipo')  # 'entrada' o 'salida'
    cantidad = request.POST.get('cantidad', '0')
    motivo = request.POST.get('motivo', 'otro')
    notas = request.POST.get('notas', '')
    
    try:
        cantidad = int(cantidad)
        if cantidad <= 0:
            return JsonResponse({'error': 'La cantidad debe ser mayor a 0'}, status=400)
        
        stock_anterior = producto.stock
        
        if tipo == 'entrada':
            stock_nuevo = producto.stock + cantidad
        elif tipo == 'salida':
            if producto.stock < cantidad:
                return JsonResponse({'error': f'Stock insuficiente. Disponible: {producto.stock}'}, status=400)
            stock_nuevo = producto.stock - cantidad
        else:
            return JsonResponse({'error': 'Tipo de movimiento inválido'}, status=400)
        
        producto.stock = stock_nuevo
        producto.save()
        
        # Registrar movimiento
        movimiento = MovimientoStock.objects.create(
            producto=producto,
            tipo=tipo,
            cantidad=cantidad,
            motivo=motivo,
            stock_anterior=stock_anterior,
            stock_nuevo=stock_nuevo,
            usuario=request.user,
            notas=notas
        )
        
        # Registrar en historial
        registrar_cambio(
            producto,
            request.user,
            'stock',
            'stock',
            stock_anterior,
            stock_nuevo,
            f'Movimiento: {movimiento.get_tipo_display()} - {movimiento.get_motivo_display()}'
        )
        
        return JsonResponse({
            'success': True,
            'stock': producto.stock,
            'stock_bajo': producto.stock_bajo,
            'mensaje': f'Movimiento registrado: {stock_anterior} → {stock_nuevo}'
        })
    except ValueError:
        return JsonResponse({'error': 'Cantidad inválida'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)

@login_required
def listar_movimientos(request):
    """Lista todos los movimientos de stock"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('inicio')
    
    movimientos = MovimientoStock.objects.select_related('producto', 'usuario').all()
    
    # Filtros
    producto_id = request.GET.get('producto', '')
    tipo = request.GET.get('tipo', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    
    if producto_id:
        movimientos = movimientos.filter(producto_id=producto_id)
    if tipo:
        movimientos = movimientos.filter(tipo=tipo)
    if fecha_desde:
        movimientos = movimientos.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        movimientos = movimientos.filter(fecha__lte=fecha_hasta)
    
    # Paginación
    paginator = Paginator(movimientos, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_entradas = movimientos.filter(tipo='entrada').aggregate(Sum('cantidad'))['cantidad__sum'] or 0
    total_salidas = movimientos.filter(tipo='salida').aggregate(Sum('cantidad'))['cantidad__sum'] or 0
    
    context = {
        'movimientos': page_obj,
        'productos': Producto.objects.filter(activo=True).order_by('nombre'),
        'producto_id': producto_id,
        'tipo': tipo,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'total_entradas': total_entradas,
        'total_salidas': total_salidas,
        'es_admin': True,
    }
    
    return render(request, 'inventario/movimientos_stock.html', context)

