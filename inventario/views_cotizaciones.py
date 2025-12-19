from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from decimal import Decimal
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
import io
from .models import Producto, Cotizacion, ItemCotizacion, Venta, ItemVenta, MovimientoStock
from .utils import es_admin_bossa, registrar_cambio

@login_required
def crear_cotizacion(request):
    """Vista para crear una nueva cotización"""
    productos = Producto.objects.filter(activo=True).order_by('nombre')
    
    if request.method == 'POST':
        try:
            import json
            items_data = json.loads(request.POST.get('items', '[]'))
            cliente_nombre = request.POST.get('cliente_nombre', '').strip()
            cliente_contacto = request.POST.get('cliente_contacto', '').strip()
            cliente_telefono = request.POST.get('cliente_telefono', '').strip()
            cliente_email = request.POST.get('cliente_email', '').strip()
            fecha_vencimiento = request.POST.get('fecha_vencimiento', '')
            subtotal = Decimal(request.POST.get('subtotal', '0'))
            descuento = Decimal(request.POST.get('descuento', '0'))
            total = Decimal(request.POST.get('total', '0'))
            notas = request.POST.get('notas', '')
            
            if not cliente_nombre:
                return JsonResponse({'error': 'El nombre del cliente es requerido'}, status=400)
            
            if not items_data:
                return JsonResponse({'error': 'Debe agregar al menos un producto'}, status=400)
            
            if not fecha_vencimiento:
                return JsonResponse({'error': 'La fecha de vencimiento es requerida'}, status=400)
            
            # Crear cotización
            cotizacion = Cotizacion.objects.create(
                usuario=request.user,
                cliente_nombre=cliente_nombre,
                cliente_contacto=cliente_contacto or None,
                cliente_telefono=cliente_telefono or None,
                cliente_email=cliente_email or None,
                fecha_vencimiento=fecha_vencimiento,
                subtotal=subtotal,
                descuento=descuento,
                total=total,
                notas=notas or None
            )
            
            # Crear items
            for item_data in items_data:
                producto_id = item_data.get('producto_id')
                cantidad = int(item_data.get('cantidad', 1))
                precio_unitario = Decimal(item_data.get('precio', '0'))
                
                producto = None
                if producto_id:
                    try:
                        producto = Producto.objects.get(id=producto_id)
                    except Producto.DoesNotExist:
                        pass
                
                ItemCotizacion.objects.create(
                    cotizacion=cotizacion,
                    producto=producto,
                    nombre_producto=item_data.get('nombre', 'Producto'),
                    cantidad=cantidad,
                    precio_unitario=precio_unitario
                )
            
            # Recalcular total
            cotizacion.subtotal = sum(item.subtotal for item in cotizacion.items.all())
            cotizacion.total = cotizacion.subtotal - cotizacion.descuento
            cotizacion.save()
            
            return JsonResponse({
                'success': True,
                'cotizacion_id': cotizacion.id,
                'numero_cotizacion': cotizacion.numero_cotizacion,
                'mensaje': f'Cotización #{cotizacion.numero_cotizacion} creada exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Error al crear cotización: {str(e)}'}, status=500)
    
    # Calcular fecha de vencimiento por defecto (7 días)
    fecha_vencimiento_default = (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    
    context = {
        'productos': productos,
        'fecha_vencimiento_default': fecha_vencimiento_default,
        'es_admin': es_admin_bossa(request.user),
    }
    
    return render(request, 'inventario/crear_cotizacion.html', context)

@login_required
def listar_cotizaciones(request):
    """Lista todas las cotizaciones - Usuarios normales solo ven las suyas"""
    if es_admin_bossa(request.user):
        cotizaciones = Cotizacion.objects.select_related('usuario').prefetch_related('items').all()
    else:
        cotizaciones = Cotizacion.objects.select_related('usuario').prefetch_related('items').filter(usuario=request.user)
    
    # Filtros
    estado = request.GET.get('estado', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    numero_cotizacion = request.GET.get('numero_cotizacion', '')
    cliente = request.GET.get('cliente', '')
    
    if estado:
        cotizaciones = cotizaciones.filter(estado=estado)
    if fecha_desde:
        cotizaciones = cotizaciones.filter(fecha_creacion__gte=fecha_desde)
    if fecha_hasta:
        cotizaciones = cotizaciones.filter(fecha_creacion__lte=fecha_hasta)
    if numero_cotizacion:
        cotizaciones = cotizaciones.filter(numero_cotizacion__icontains=numero_cotizacion)
    if cliente:
        cotizaciones = cotizaciones.filter(cliente_nombre__icontains=cliente)
    
    # Estadísticas
    total_cotizaciones = cotizaciones.aggregate(Sum('total'))['total__sum'] or 0
    total_cotizaciones_count = cotizaciones.count()
    
    # Paginación
    paginator = Paginator(cotizaciones, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'cotizaciones': page_obj,
        'estado': estado,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'numero_cotizacion': numero_cotizacion,
        'cliente': cliente,
        'total_cotizaciones': total_cotizaciones,
        'total_cotizaciones_count': total_cotizaciones_count,
        'es_admin': es_admin_bossa(request.user),
    }
    
    return render(request, 'inventario/listar_cotizaciones.html', context)

@login_required
def detalle_cotizacion(request, cotizacion_id):
    """Detalle de una cotización"""
    if es_admin_bossa(request.user):
        cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    else:
        cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id, usuario=request.user)
    
    items = cotizacion.items.select_related('producto').all()
    
    context = {
        'cotizacion': cotizacion,
        'items': items,
        'es_admin': es_admin_bossa(request.user),
    }
    
    return render(request, 'inventario/detalle_cotizacion.html', context)

@login_required
def imprimir_cotizacion(request, cotizacion_id):
    """Genera PDF de cotización - por defecto térmica 58mm, o A4 si se especifica tipo=a4"""
    tipo = request.GET.get('tipo', 'termica')  # 'termica' o 'a4'
    
    if tipo == 'a4':
        return imprimir_cotizacion_a4(request, cotizacion_id)
    else:
        return imprimir_cotizacion_termica(request, cotizacion_id)

@login_required
def imprimir_cotizacion_termica(request, cotizacion_id):
    """Genera PDF de cotización para impresión térmica 58mm"""
    if es_admin_bossa(request.user):
        cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    else:
        cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id, usuario=request.user)
    
    items = cotizacion.items.all()
    
    buffer = io.BytesIO()
    # Formato para impresora térmica 58mm (ancho estándar 80mm, alto variable)
    doc = SimpleDocTemplate(buffer, pagesize=(80*mm, 300*mm),
                          rightMargin=3*mm, leftMargin=3*mm,
                          topMargin=5*mm, bottomMargin=5*mm)
    elements = []
    
    styles = getSampleStyleSheet()
    
    # Estilos optimizados para impresora térmica 58mm
    header_business_style = ParagraphStyle(
        'BusinessHeader',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.black,
        alignment=1,  # Center
        fontName='Helvetica-Bold',
        leading=13,
        spaceAfter=4
    )
    
    header_address_style = ParagraphStyle(
        'AddressHeader',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.black,
        alignment=1,  # Center
        leading=9,
        spaceAfter=2
    )
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        alignment=1,
        fontName='Helvetica-Bold',
        spaceAfter=6
    )
    
    style_normal = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=7,
        leading=9,
        alignment=0,  # Left
    )
    
    style_center = ParagraphStyle(
        'Center',
        parent=styles['Normal'],
        fontSize=7,
        leading=9,
        alignment=1,  # Center
    )
    
    style_bold = ParagraphStyle(
        'Bold',
        parent=styles['Normal'],
        fontSize=7,
        leading=9,
        alignment=0,
        fontName='Helvetica-Bold'
    )
    
    # ===== ENCABEZADO DEL NEGOCIO =====
    elements.append(Paragraph("BOTILLERÍA LA PREVIA", header_business_style))
    elements.append(Paragraph("Lautaro 948", header_address_style))
    elements.append(Paragraph("Santa Juana, Bio Bio, Chile", header_address_style))
    elements.append(Paragraph("Tel: +56956499437", header_address_style))
    elements.append(Spacer(1, 3*mm))
    elements.append(Paragraph("-" * 32, style_center))
    elements.append(Spacer(1, 3*mm))
    
    # Encabezado
    elements.append(Paragraph("COTIZACIÓN", title_style))
    elements.append(Spacer(1, 3*mm))
    
    # Información de la cotización (formato compacto)
    elements.append(Paragraph(f"<b>N°:</b> {cotizacion.numero_cotizacion}", style_normal))
    elements.append(Paragraph(f"<b>Fecha:</b> {cotizacion.fecha_creacion.strftime('%d/%m/%Y')}", style_normal))
    elements.append(Paragraph(f"<b>Válida hasta:</b> {cotizacion.fecha_vencimiento.strftime('%d/%m/%Y')}", style_normal))
    elements.append(Paragraph(f"<b>Estado:</b> {cotizacion.get_estado_display()}", style_normal))
    if cotizacion.usuario:
        elements.append(Paragraph(f"<b>Vendedor:</b> {cotizacion.usuario.username}", style_normal))
    elements.append(Spacer(1, 3*mm))
    elements.append(Paragraph("-" * 32, style_center))
    elements.append(Spacer(1, 3*mm))
    
    # Información del cliente (formato compacto)
    elements.append(Paragraph("<b>CLIENTE:</b>", style_bold))
    elements.append(Paragraph(cotizacion.cliente_nombre, style_normal))
    if cotizacion.cliente_contacto:
        elements.append(Paragraph(f"Contacto: {cotizacion.cliente_contacto}", style_normal))
    if cotizacion.cliente_telefono:
        elements.append(Paragraph(f"Tel: {cotizacion.cliente_telefono}", style_normal))
    if cotizacion.cliente_email:
        elements.append(Paragraph(f"Email: {cotizacion.cliente_email}", style_normal))
    elements.append(Spacer(1, 3*mm))
    elements.append(Paragraph("-" * 32, style_center))
    elements.append(Spacer(1, 3*mm))
    
    # Items (tabla compacta para 58mm)
    elements.append(Paragraph("<b>PRODUCTOS:</b>", style_bold))
    if items.exists():
        # Tabla optimizada para impresora térmica
        data = [['Cant.', 'Producto', 'Precio', 'Total']]
        for item in items:
            # Truncar nombre si es muy largo para que quepa en 58mm
            nombre = item.nombre_producto[:18] + '...' if len(item.nombre_producto) > 18 else item.nombre_producto
            data.append([
                str(item.cantidad),
                nombre,
                f"${item.precio_unitario:,.0f}",
                f"${item.subtotal:,.0f}"
            ])
        
        table = Table(data, colWidths=[8*mm, 30*mm, 18*mm, 18*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 4),
            ('TOPPADDING', (0,0), (-1,0), 4),
            ('ALIGN', (0,0), (0,-1), 'CENTER'),  # Cantidad centrada
            ('ALIGN', (1,0), (1,-1), 'LEFT'),     # Producto a la izquierda
            ('ALIGN', (2,0), (-1,-1), 'RIGHT'),   # Precio y Total a la derecha
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTSIZE', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.25, colors.black),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No hay productos", style_center))
    
    elements.append(Spacer(1, 3*mm))
    elements.append(Paragraph("-" * 32, style_center))
    elements.append(Spacer(1, 3*mm))
    
    # Totales (formato compacto)
    elements.append(Paragraph(f"Subtotal: ${cotizacion.subtotal:,.0f}", ParagraphStyle('Total', parent=styles['Normal'], fontSize=7, alignment=2, fontName='Helvetica-Bold')))
    if cotizacion.descuento > 0:
        elements.append(Paragraph(f"Descuento: -${cotizacion.descuento:,.0f}", ParagraphStyle('Total', parent=styles['Normal'], fontSize=7, alignment=2)))
    elements.append(Paragraph(f"<b>TOTAL: ${cotizacion.total:,.0f}</b>", ParagraphStyle('Total', parent=styles['Normal'], fontSize=8, alignment=2, fontName='Helvetica-Bold')))
    
    if cotizacion.notas:
        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph("-" * 32, style_center))
        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph("<b>NOTAS:</b>", style_bold))
        # Dividir notas en líneas más cortas para que quepa en 58mm
        notas_lineas = cotizacion.notas.split('\n')
        for linea in notas_lineas:
            if len(linea) > 30:
                # Dividir líneas muy largas
                palabras = linea.split()
                linea_actual = ""
                for palabra in palabras:
                    if len(linea_actual + palabra) > 30:
                        if linea_actual:
                            elements.append(Paragraph(linea_actual, style_normal))
                        linea_actual = palabra + " "
                    else:
                        linea_actual += palabra + " "
                if linea_actual:
                    elements.append(Paragraph(linea_actual, style_normal))
            else:
                elements.append(Paragraph(linea, style_normal))
    
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph("-" * 32, style_center))
    elements.append(Spacer(1, 3*mm))
    elements.append(Paragraph("Válida hasta: " + cotizacion.fecha_vencimiento.strftime('%d/%m/%Y'), style_center))
    elements.append(Paragraph("Gracias por su interés", style_center))
    elements.append(Spacer(1, 5*mm))
    
    # ===== DATOS DE CONTACTO AL FINAL =====
    elements.append(Paragraph("-" * 32, style_center))
    elements.append(Spacer(1, 3*mm))
    elements.append(Paragraph("<b>CONTACTO</b>", ParagraphStyle('ContactHeader', parent=styles['Normal'], fontSize=8, alignment=1, fontName='Helvetica-Bold')))
    elements.append(Paragraph("BOTILLERÍA LA PREVIA", header_address_style))
    elements.append(Paragraph("Lautaro 948, Santa Juana", header_address_style))
    elements.append(Paragraph("Bio Bio, Chile", header_address_style))
    elements.append(Paragraph("Tel: +56956499437", header_address_style))
    elements.append(Spacer(1, 3*mm))
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="cotizacion_termica_{cotizacion.numero_cotizacion}.pdf"'
    return response

@login_required
def imprimir_cotizacion_a4(request, cotizacion_id):
    """Genera PDF de cotización en formato A4"""
    if es_admin_bossa(request.user):
        cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    else:
        cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id, usuario=request.user)
    
    items = cotizacion.items.all()
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=20*mm, leftMargin=20*mm,
                           topMargin=20*mm, bottomMargin=20*mm)
    elements = []
    
    styles = getSampleStyleSheet()
    
    # Estilos para formato A4
    header_business_style = ParagraphStyle(
        'BusinessHeader',
        parent=styles['Normal'],
        fontSize=16,
        textColor=colors.black,
        alignment=1,  # Center
        fontName='Helvetica-Bold',
        leading=18,
        spaceAfter=6
    )
    
    header_address_style = ParagraphStyle(
        'AddressHeader',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.black,
        alignment=1,  # Center
        leading=13,
        spaceAfter=3
    )
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        alignment=1,
        fontName='Helvetica-Bold',
        spaceAfter=20
    )
    
    # ===== ENCABEZADO DEL NEGOCIO =====
    elements.append(Paragraph("BOTILLERÍA LA PREVIA", header_business_style))
    elements.append(Paragraph("Lautaro 948", header_address_style))
    elements.append(Paragraph("Santa Juana, Bio Bio, Chile", header_address_style))
    elements.append(Paragraph("Tel: +56956499437", header_address_style))
    elements.append(Spacer(1, 8*mm))
    elements.append(Paragraph("-" * 50, ParagraphStyle('Divider', parent=styles['Normal'], fontSize=10, alignment=1)))
    elements.append(Spacer(1, 8*mm))
    
    # Encabezado
    elements.append(Paragraph("COTIZACIÓN", title_style))
    elements.append(Spacer(1, 10*mm))
    
    # Información de la cotización
    info_data = [
        ['Número:', cotizacion.numero_cotizacion],
        ['Fecha:', cotizacion.fecha_creacion.strftime('%d/%m/%Y')],
        ['Válida hasta:', cotizacion.fecha_vencimiento.strftime('%d/%m/%Y')],
        ['Estado:', cotizacion.get_estado_display()],
    ]
    if cotizacion.usuario:
        info_data.append(['Vendedor:', cotizacion.usuario.get_full_name() or cotizacion.usuario.username])
    
    info_table = Table(info_data, colWidths=[60*mm, None])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10*mm))
    
    # Información del cliente
    elements.append(Paragraph("<b>DATOS DEL CLIENTE</b>", styles['Heading2']))
    cliente_data = [
        ['Nombre:', cotizacion.cliente_nombre],
    ]
    if cotizacion.cliente_contacto:
        cliente_data.append(['Contacto:', cotizacion.cliente_contacto])
    if cotizacion.cliente_telefono:
        cliente_data.append(['Teléfono:', cotizacion.cliente_telefono])
    if cotizacion.cliente_email:
        cliente_data.append(['Email:', cotizacion.cliente_email])
    
    cliente_table = Table(cliente_data, colWidths=[60*mm, None])
    cliente_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(cliente_table)
    elements.append(Spacer(1, 10*mm))
    
    # Items - formato similar al de cotizaciones (tabla con columnas)
    elements.append(Paragraph("<b>PRODUCTOS</b>", styles['Heading2']))
    items_data = [['Cantidad', 'Producto', 'Precio Unit.', 'Subtotal']]
    for item in items:
        items_data.append([
            str(item.cantidad),
            item.nombre_producto,
            f"${item.precio_unitario:,.0f}",
            f"${item.subtotal:,.0f}"
        ])
    
    items_table = Table(items_data, colWidths=[40*mm, None, 50*mm, 50*mm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Cantidad centrada
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),     # Producto a la izquierda
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),   # Precio y Total a la derecha
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 10*mm))
    
    # Totales
    totales_data = [
        ['Subtotal:', f"${cotizacion.subtotal:,.0f}"],
    ]
    if cotizacion.descuento > 0:
        totales_data.append(['Descuento:', f"-${cotizacion.descuento:,.0f}"])
    totales_data.append(['<b>TOTAL:</b>', f"<b>${cotizacion.total:,.0f}</b>"])
    
    totales_table = Table(totales_data, colWidths=[None, 50*mm])
    totales_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('FONTSIZE', (-1, -1), (-1, -1), 14),
        ('FONTNAME', (-1, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(totales_table)
    
    if cotizacion.notas:
        elements.append(Spacer(1, 10*mm))
        elements.append(Paragraph("<b>NOTAS:</b>", styles['Normal']))
        elements.append(Paragraph(cotizacion.notas, styles['Normal']))
    
    elements.append(Spacer(1, 15*mm))
    elements.append(Paragraph("Gracias por su interés. Esta cotización es válida hasta la fecha indicada.", 
                              ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, alignment=1, textColor=colors.grey)))
    elements.append(Spacer(1, 10*mm))
    
    # ===== DATOS DE CONTACTO AL FINAL =====
    elements.append(Paragraph("-" * 50, ParagraphStyle('Divider', parent=styles['Normal'], fontSize=10, alignment=1)))
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph("<b>CONTACTO</b>", ParagraphStyle('ContactHeader', parent=styles['Normal'], fontSize=11, alignment=1, fontName='Helvetica-Bold')))
    elements.append(Paragraph("BOTILLERÍA LA PREVIA", header_address_style))
    elements.append(Paragraph("Lautaro 948, Santa Juana, Bio Bio, Chile", header_address_style))
    elements.append(Paragraph("Teléfono: +56956499437", header_address_style))
    elements.append(Spacer(1, 5*mm))
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="cotizacion_a4_{cotizacion.numero_cotizacion}.pdf"'
    return response

@login_required
@transaction.atomic
def convertir_cotizacion_en_venta(request, cotizacion_id):
    """Convierte una cotización en una venta"""
    if es_admin_bossa(request.user):
        cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    else:
        cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id, usuario=request.user)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    if cotizacion.convertida_en_venta:
        return JsonResponse({'error': 'Esta cotización ya fue convertida en venta'}, status=400)
    
    try:
        # Crear venta
        venta = Venta.objects.create(
            usuario=request.user,
            subtotal=cotizacion.subtotal,
            descuento=cotizacion.descuento,
            total=cotizacion.total,
            metodo_pago='efectivo',  # Por defecto, se puede cambiar después
            notas=f'Convertida desde cotización {cotizacion.numero_cotizacion}'
        )
        
        # Crear items de venta y descontar stock
        for item_cot in cotizacion.items.all():
            if item_cot.producto:
                # Verificar stock
                if item_cot.producto.stock < item_cot.cantidad:
                    venta.delete()
                    return JsonResponse({
                        'error': f'Stock insuficiente para {item_cot.nombre_producto}. Disponible: {item_cot.producto.stock}'
                    }, status=400)
                
                stock_anterior = item_cot.producto.stock
                item_cot.producto.stock -= item_cot.cantidad
                item_cot.producto.save()
                
                ItemVenta.objects.create(
                    venta=venta,
                    producto=item_cot.producto,
                    nombre_producto=item_cot.nombre_producto,
                    cantidad=item_cot.cantidad,
                    precio_unitario=item_cot.precio_unitario,
                    stock_anterior=stock_anterior,
                    stock_despues=item_cot.producto.stock
                )
            else:
                # Producto eliminado, crear item sin producto
                ItemVenta.objects.create(
                    venta=venta,
                    producto=None,
                    nombre_producto=item_cot.nombre_producto,
                    cantidad=item_cot.cantidad,
                    precio_unitario=item_cot.precio_unitario,
                    stock_anterior=0,
                    stock_despues=0
                )
        
        # Marcar cotización como aprobada y vinculada
        cotizacion.estado = 'aprobada'
        cotizacion.convertida_en_venta = venta
        cotizacion.save()
        
        return JsonResponse({
            'success': True,
            'venta_id': venta.id,
            'numero_venta': venta.numero_venta,
            'mensaje': f'Cotización convertida en venta #{venta.numero_venta}'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Error al convertir cotización: {str(e)}'}, status=500)

