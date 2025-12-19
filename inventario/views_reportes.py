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
from .models import Producto, MovimientoStock, Categoria, Venta, ItemVenta
from .utils import es_admin_bossa

@login_required
def reportes_avanzados(request):
    """Dashboard de reportes avanzados"""
    if not es_admin_bossa(request.user):
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('inicio')
    
    # Período de tiempo
    dias = int(request.GET.get('dias', 30))
    fecha_desde = timezone.now().date() - timedelta(days=dias)
    
    # Productos más vendidos (por ventas)
    productos_mas_vendidos = ItemVenta.objects.filter(
        venta__fecha__gte=fecha_desde,
        venta__cancelada=False
    ).values('producto__nombre', 'producto__id').annotate(
        total_vendido=Sum('cantidad')
    ).order_by('-total_vendido')[:10]
    
    # Estadísticas de ventas
    total_ventas_periodo = Venta.objects.filter(
        fecha__gte=fecha_desde,
        cancelada=False
    ).aggregate(Sum('total'))['total__sum'] or 0
    cantidad_ventas = Venta.objects.filter(
        fecha__gte=fecha_desde,
        cancelada=False
    ).count()
    
    # Productos con mayor rotación
    productos_rotacion = []
    for producto in Producto.objects.filter(activo=True):
        movimientos = MovimientoStock.objects.filter(
            producto=producto,
            fecha__gte=fecha_desde
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
    
    # Análisis de rentabilidad
    productos_rentables = []
    for producto in Producto.objects.filter(activo=True, precio_compra__isnull=False):
        if producto.ganancia_unitaria:
            ganancia_total = producto.ganancia_unitaria * producto.stock
            productos_rentables.append({
                'producto': producto,
                'ganancia_total': ganancia_total
            })
    productos_rentables.sort(key=lambda x: x['ganancia_total'], reverse=True)
    productos_rentables = productos_rentables[:10]
    
    # Productos sin movimiento
    productos_sin_movimiento = Producto.objects.filter(
        activo=True
    ).exclude(
        id__in=MovimientoStock.objects.filter(
            fecha__gte=fecha_desde
        ).values_list('producto_id', flat=True)
    )[:10]
    
    # Estadísticas generales
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
    
    # Estadísticas de ventas del período
    ventas_por_metodo = Venta.objects.filter(
        fecha__gte=fecha_desde,
        cancelada=False
    ).values('metodo_pago').annotate(
        total=Sum('total'),
        cantidad=Count('id')
    )
    
    context = {
        'dias': dias,
        'fecha_desde': fecha_desde,
        'productos_mas_vendidos': productos_mas_vendidos,
        'productos_rotacion': productos_rotacion,
        'productos_rentables': productos_rentables,
        'productos_sin_movimiento': productos_sin_movimiento,
        'total_productos': total_productos,
        'productos_con_margen': productos_con_margen,
        'valor_inventario_total': valor_inventario_total,
        'ganancia_potencial_total': ganancia_potencial_total,
        'total_ventas_periodo': total_ventas_periodo,
        'cantidad_ventas': cantidad_ventas,
        'ventas_por_metodo': ventas_por_metodo,
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
    """Dashboard con gráficos de ventas para el admin"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('inicio')
    
    ahora = timezone.now()
    
    # Obtener fechas personalizadas o usar período predefinido
    fecha_desde_str = request.GET.get('fecha_desde', '')
    fecha_hasta_str = request.GET.get('fecha_hasta', '')
    periodo = request.GET.get('periodo', 'mes')  # dia, semana, mes, semestre, año, personalizado
    
    # Si hay fechas personalizadas, usarlas
    if fecha_desde_str and fecha_hasta_str:
        try:
            fecha_desde = datetime.strptime(fecha_desde_str, '%Y-%m-%d').date()
            fecha_hasta = datetime.strptime(fecha_hasta_str, '%Y-%m-%d').date()
            periodo = 'personalizado'
            # Determinar agrupación según rango
            dias_diferencia = (fecha_hasta - fecha_desde).days
            if dias_diferencia <= 60:
                agrupar_por = 'dia'
            elif dias_diferencia <= 180:
                agrupar_por = 'semana'
            elif dias_diferencia <= 730:
                agrupar_por = 'mes'
            elif dias_diferencia <= 1460:
                agrupar_por = 'semestre'
            else:
                agrupar_por = 'año'
        except:
            fecha_desde = ahora.date() - timedelta(days=365)
            fecha_hasta = ahora.date()
            agrupar_por = 'mes'
    else:
        # Calcular fechas según período predefinido
        fecha_hasta = ahora.date()
        if periodo == 'dia':
            fecha_desde = ahora.date() - timedelta(days=30)
            agrupar_por = 'dia'
        elif periodo == 'semana':
            fecha_desde = ahora.date() - timedelta(days=84)
            agrupar_por = 'semana'
        elif periodo == 'mes':
            fecha_desde = ahora.date() - timedelta(days=365)
            agrupar_por = 'mes'
        elif periodo == 'semestre':
            fecha_desde = ahora.date() - timedelta(days=730)
            agrupar_por = 'semestre'
        else:  # año
            fecha_desde = ahora.date() - timedelta(days=1825)
            agrupar_por = 'año'
    
    # Obtener ventas del período
    ventas = Venta.objects.filter(
        fecha__date__gte=fecha_desde,
        fecha__date__lte=fecha_hasta,
        cancelada=False
    ).order_by('fecha')
    
    # Preparar datos para gráficos
    datos_ventas = {}
    datos_cantidad = {}
    
    for venta in ventas:
        fecha = venta.fecha.date()
        
        if agrupar_por == 'dia':
            clave = fecha.strftime('%d/%m/%Y')
        elif agrupar_por == 'semana':
            semana = fecha.isocalendar()[1]
            año = fecha.year
            clave = f"Sem {semana}/{año}"
        elif agrupar_por == 'mes':
            clave = fecha.strftime('%m/%Y')
        elif agrupar_por == 'semestre':
            semestre = 1 if fecha.month <= 6 else 2
            clave = f"S{semestre}/{fecha.year}"
        else:  # año
            clave = str(fecha.year)
        
        if clave not in datos_ventas:
            datos_ventas[clave] = 0
            datos_cantidad[clave] = 0
        
        datos_ventas[clave] += float(venta.total)
        datos_cantidad[clave] += 1
    
    # Ordenar por fecha
    if agrupar_por == 'dia':
        claves_ordenadas = sorted(datos_ventas.keys(), key=lambda x: datetime.strptime(x, '%d/%m/%Y'))
    elif agrupar_por == 'semana':
        claves_ordenadas = sorted(datos_ventas.keys())
    elif agrupar_por == 'mes':
        claves_ordenadas = sorted(datos_ventas.keys(), key=lambda x: datetime.strptime(x, '%m/%Y'))
    elif agrupar_por == 'semestre':
        claves_ordenadas = sorted(datos_ventas.keys())
    else:
        claves_ordenadas = sorted(datos_ventas.keys())
    
    # Estadísticas generales
    total_ventas_periodo = sum(datos_ventas.values())
    cantidad_ventas_periodo = sum(datos_cantidad.values())
    promedio_venta = total_ventas_periodo / cantidad_ventas_periodo if cantidad_ventas_periodo > 0 else 0
    
    # Ventas por método de pago
    ventas_por_metodo = Venta.objects.filter(
        fecha__date__gte=fecha_desde,
        fecha__date__lte=fecha_hasta,
        cancelada=False
    ).values('metodo_pago').annotate(
        total=Sum('total'),
        cantidad=Count('id')
    )
    
    # Top productos vendidos
    top_productos = ItemVenta.objects.filter(
        venta__fecha__date__gte=fecha_desde,
        venta__fecha__date__lte=fecha_hasta,
        venta__cancelada=False
    ).values('producto__nombre', 'producto__id').annotate(
        total_vendido=Sum('cantidad'),
        total_ingresos=Sum(F('cantidad') * F('precio_unitario'))
    ).order_by('-total_vendido')[:10]
    
    context = {
        'periodo': periodo,
        'fecha_desde': fecha_desde.strftime('%Y-%m-%d'),
        'fecha_hasta': fecha_hasta.strftime('%Y-%m-%d'),
        'labels': json.dumps(claves_ordenadas),
        'datos_ventas': json.dumps([datos_ventas.get(k, 0) for k in claves_ordenadas]),
        'datos_cantidad': json.dumps([datos_cantidad.get(k, 0) for k in claves_ordenadas]),
        'total_ventas_periodo': total_ventas_periodo,
        'cantidad_ventas_periodo': cantidad_ventas_periodo,
        'promedio_venta': promedio_venta,
        'ventas_por_metodo': list(ventas_por_metodo),
        'top_productos': list(top_productos),
        'es_admin': True,
    }
    
    return render(request, 'inventario/graficos_ventas.html', context)

