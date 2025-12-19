from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, F, Sum, Count, Avg, Max, Min
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta, datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
import json
import pytz
from .models import (
    Producto, MovimientoStock, Categoria, Venta, ItemVenta,
    Cliente, CuentaPorCobrar, Almacen, OrdenCompra
)
from .utils import es_admin_bossa

@login_required
def reportes_avanzados(request):
    """Dashboard de reportes avanzados con gráficos y análisis"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('inicio')
    
    # Obtener fechas personalizadas o usar período predefinido
    fecha_desde_str = request.GET.get('fecha_desde', '')
    fecha_hasta_str = request.GET.get('fecha_hasta', '')
    dias = request.GET.get('dias', '')
    
    # Si hay fechas personalizadas, usarlas
    if fecha_desde_str and fecha_hasta_str:
        try:
            fecha_desde = datetime.strptime(fecha_desde_str, '%Y-%m-%d').date()
            fecha_hasta = datetime.strptime(fecha_hasta_str, '%Y-%m-%d').date()
            if fecha_desde > fecha_hasta:
                fecha_desde, fecha_hasta = fecha_hasta, fecha_desde
            dias = 'personalizado'  # Indicar que es rango personalizado
        except:
            # Si hay error, usar período por defecto
            dias = int(dias) if dias else 30
            fecha_desde = timezone.now().date() - timedelta(days=dias)
            fecha_hasta = timezone.now().date()
    else:
        # Usar período predefinido
        dias = int(dias) if dias else 30
        fecha_desde = timezone.now().date() - timedelta(days=dias)
        fecha_hasta = timezone.now().date()
    
    # ========== ANÁLISIS DE VENTAS ==========
    ventas_periodo = Venta.objects.filter(
        fecha__date__gte=fecha_desde,
        fecha__date__lte=fecha_hasta,
        cancelada=False
    )
    
    total_ventas_periodo = ventas_periodo.aggregate(Sum('total'))['total__sum'] or 0
    cantidad_ventas = ventas_periodo.count()
    promedio_venta = total_ventas_periodo / cantidad_ventas if cantidad_ventas > 0 else 0
    
    # Ventas por día (para gráfico)
    ventas_por_dia = {}
    for venta in ventas_periodo:
        fecha_str = venta.fecha.date().strftime('%d/%m/%Y')
        if fecha_str not in ventas_por_dia:
            ventas_por_dia[fecha_str] = {'total': 0, 'cantidad': 0}
        ventas_por_dia[fecha_str]['total'] += float(venta.total)
        ventas_por_dia[fecha_str]['cantidad'] += 1
    
    # Ordenar fechas
    fechas_ordenadas = sorted(ventas_por_dia.keys(), key=lambda x: datetime.strptime(x, '%d/%m/%Y'))
    
    # Ventas por método de pago
    ventas_por_metodo = ventas_periodo.values('metodo_pago').annotate(
        total=Sum('total'),
        cantidad=Count('id')
    )
    
    # Ventas a crédito vs contado
    ventas_credito = ventas_periodo.filter(es_credito=True).aggregate(
        total=Sum('total'), cantidad=Count('id')
    )
    ventas_contado = ventas_periodo.filter(es_credito=False).aggregate(
        total=Sum('total'), cantidad=Count('id')
    )
    
    # ========== ANÁLISIS DE PRODUCTOS ==========
    # Productos más vendidos
    productos_mas_vendidos = ItemVenta.objects.filter(
        venta__fecha__date__gte=fecha_desde,
        venta__fecha__date__lte=fecha_hasta,
        venta__cancelada=False
    ).values('producto__nombre', 'producto__id').annotate(
        total_vendido=Sum('cantidad'),
        total_ingresos=Sum(F('cantidad') * F('precio_unitario'))
    ).order_by('-total_vendido')[:10]
    
    # Productos con mayor rotación
    productos_rotacion = []
    for producto in Producto.objects.filter(activo=True):
        movimientos = MovimientoStock.objects.filter(
            producto=producto,
            fecha__date__gte=fecha_desde,
            fecha__date__lte=fecha_hasta
        )
        entradas = movimientos.filter(tipo='entrada').aggregate(Sum('cantidad'))['cantidad__sum'] or 0
        salidas = movimientos.filter(tipo='salida').aggregate(Sum('cantidad'))['cantidad__sum'] or 0
        if entradas > 0 or salidas > 0:
            productos_rotacion.append({
                'producto': producto,
                'entradas': entradas,
                'salidas': salidas,
                'rotacion': salidas / max(producto.stock, 1) if producto.stock > 0 else 0
            })
    productos_rotacion.sort(key=lambda x: x['rotacion'], reverse=True)
    productos_rotacion = productos_rotacion[:10]
    
    # Productos más rentables
    productos_rentables = []
    for producto in Producto.objects.filter(activo=True, precio_compra__isnull=False):
        if producto.ganancia_unitaria:
            ganancia_total = producto.ganancia_unitaria * producto.stock
            productos_rentables.append({
                'producto': producto,
                'ganancia_total': ganancia_total,
                'margen': producto.margen_ganancia
            })
    productos_rentables.sort(key=lambda x: x['ganancia_total'], reverse=True)
    productos_rentables = productos_rentables[:10]
    
    # Productos sin movimiento
    productos_sin_movimiento = Producto.objects.filter(
        activo=True
    ).exclude(
        id__in=MovimientoStock.objects.filter(
            fecha__date__gte=fecha_desde,
            fecha__date__lte=fecha_hasta
        ).values_list('producto_id', flat=True)
    )[:10]
    
    # ========== ANÁLISIS DE CLIENTES ==========
    # Top clientes por compras
    top_clientes_raw = Venta.objects.filter(
        fecha__date__gte=fecha_desde,
        fecha__date__lte=fecha_hasta,
        cancelada=False,
        cliente__isnull=False
    ).values('cliente__nombre', 'cliente__id').annotate(
        total_compras=Sum('total'),
        cantidad_ventas=Count('id')
    ).order_by('-total_compras')[:10]
    
    # Calcular promedio para cada cliente
    top_clientes = []
    for cliente in top_clientes_raw:
        promedio = float(cliente['total_compras']) / cliente['cantidad_ventas'] if cliente['cantidad_ventas'] > 0 else 0
        cliente_dict = dict(cliente)
        cliente_dict['promedio'] = promedio
        top_clientes.append(cliente_dict)
    
    # Clientes con saldo pendiente
    clientes_saldo = Cliente.objects.filter(
        activo=True
    ).annotate(
        saldo=Sum('cuentas_por_cobrar__monto_total') - Sum('cuentas_por_cobrar__monto_pagado')
    ).filter(saldo__gt=0).order_by('-saldo')[:10]
    
    # ========== ANÁLISIS DE CUENTAS POR COBRAR ==========
    cuentas_pendientes = CuentaPorCobrar.objects.filter(
        estado__in=['pendiente', 'parcial']
    )
    total_pendiente = cuentas_pendientes.aggregate(
        total=Sum('monto_total') - Sum('monto_pagado')
    )['total'] or 0
    
    cuentas_vencidas = cuentas_pendientes.filter(
        fecha_vencimiento__lt=timezone.now().date()
    )
    total_vencido = cuentas_vencidas.aggregate(
        total=Sum('monto_total') - Sum('monto_pagado')
    )['total'] or 0
    
    # ========== ANÁLISIS DE INVENTARIO ==========
    total_productos = Producto.objects.filter(activo=True).count()
    productos_con_margen = Producto.objects.filter(
        activo=True,
        precio_compra__isnull=False
    ).count()
    valor_inventario_total = sum(p.valor_inventario for p in Producto.objects.filter(activo=True))
    ganancia_potencial_total = sum(
        (p.ganancia_unitaria * p.stock) for p in Producto.objects.filter(
            activo=True,
            precio_compra__isnull=False
        ) if p.ganancia_unitaria
    )
    
    # Productos por categoría
    productos_por_categoria = Categoria.objects.annotate(
        cantidad=Count('producto', filter=Q(producto__activo=True)),
        valor_total=Sum(F('producto__precio') * F('producto__stock'), filter=Q(producto__activo=True))
    ).filter(cantidad__gt=0).order_by('-cantidad')[:10]
    
    # ========== ANÁLISIS DE ALMACENES ==========
    almacenes_info = []
    for almacen in Almacen.objects.filter(activo=True):
        from .models import StockAlmacen
        stock_items = StockAlmacen.objects.filter(almacen=almacen)
        almacenes_info.append({
            'almacen': almacen,
            'productos_count': stock_items.count(),
            'stock_bajo_count': stock_items.filter(cantidad__lte=F('stock_minimo')).count()
        })
    
    # ========== ANÁLISIS DE COMPRAS ==========
    ordenes_periodo = OrdenCompra.objects.filter(
        fecha_creacion__date__gte=fecha_desde,
        fecha_creacion__date__lte=fecha_hasta
    )
    total_compras = ordenes_periodo.aggregate(Sum('total'))['total__sum'] or 0
    ordenes_pendientes = ordenes_periodo.filter(estado__in=['pendiente', 'parcial']).count()
    
    # Normalizar dias para el template
    if isinstance(dias, str) and dias == 'personalizado':
        dias_template = 'personalizado'
    elif isinstance(dias, int):
        dias_template = dias
    else:
        try:
            dias_template = int(dias) if dias else 30
        except:
            dias_template = 30
    
    context = {
        'dias': dias_template,
        'fecha_desde': fecha_desde.strftime('%Y-%m-%d'),
        'fecha_hasta': fecha_hasta.strftime('%Y-%m-%d'),
        'fecha_desde_display': fecha_desde.strftime('%d/%m/%Y'),
        'fecha_hasta_display': fecha_hasta.strftime('%d/%m/%Y'),
        # Ventas
        'total_ventas_periodo': total_ventas_periodo,
        'cantidad_ventas': cantidad_ventas,
        'promedio_venta': promedio_venta,
        'ventas_por_metodo': list(ventas_por_metodo),
        'ventas_credito': ventas_credito,
        'ventas_contado': ventas_contado,
        'fechas_ordenadas': json.dumps(fechas_ordenadas),
        'ventas_por_dia_total': json.dumps([ventas_por_dia.get(f, {}).get('total', 0) for f in fechas_ordenadas]),
        'ventas_por_dia_cantidad': json.dumps([ventas_por_dia.get(f, {}).get('cantidad', 0) for f in fechas_ordenadas]),
        # Productos
        'productos_mas_vendidos': productos_mas_vendidos,
        'productos_rotacion': productos_rotacion,
        'productos_rentables': productos_rentables,
        'productos_sin_movimiento': productos_sin_movimiento,
        'productos_por_categoria': productos_por_categoria,
        # Inventario
        'total_productos': total_productos,
        'productos_con_margen': productos_con_margen,
        'valor_inventario_total': valor_inventario_total,
        'ganancia_potencial_total': ganancia_potencial_total,
        # Clientes
        'top_clientes': list(top_clientes),
        'clientes_saldo': clientes_saldo,
        # Cuentas por cobrar
        'total_pendiente': total_pendiente,
        'total_vencido': total_vencido,
        'cuentas_vencidas_count': cuentas_vencidas.count(),
        # Almacenes
        'almacenes_info': almacenes_info,
        # Compras
        'total_compras': total_compras,
        'ordenes_pendientes': ordenes_pendientes,
        'es_admin': True,
    }
    
    return render(request, 'inventario/reportes_avanzados.html', context)

@login_required
def dashboard_usuario_normal(request):
    """Dashboard simplificado para usuarios normales"""
    # Estadísticas básicas
    total_productos = Producto.objects.filter(activo=True).count()
    categorias_count = Categoria.objects.count()
    
    # Productos recientes
    productos_recientes = Producto.objects.filter(activo=True).order_by('-fecha_creacion')[:5]
    
    # Productos favoritos del usuario
    from .models import ProductoFavorito
    favoritos = ProductoFavorito.objects.filter(usuario=request.user).select_related('producto')[:5]
    
    context = {
        'total_productos': total_productos,
        'categorias_count': categorias_count,
        'productos_recientes': productos_recientes,
        'favoritos': favoritos,
    }
    
    return render(request, 'inventario/dashboard_usuario.html', context)

@login_required
def graficos_ventas(request):
    """Dashboard con gráficos de ventas para el admin - DEPRECADO: usar reportes_avanzados"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('inicio')
    
    # Redirigir a reportes avanzados
    messages.info(request, 'Los gráficos de ventas ahora están integrados en Reportes Avanzados.')
    return redirect('reportes_avanzados')
