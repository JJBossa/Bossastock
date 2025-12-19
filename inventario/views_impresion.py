from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Q
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.graphics.barcode import code128
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
import io
import os
import pytz
from .models import Producto, Categoria, Venta, ItemVenta
from .utils import es_admin_bossa
from django.contrib import messages

@login_required
def imprimir_etiquetas(request):
    """Vista para seleccionar productos e imprimir etiquetas"""
    if not es_admin_bossa(request.user):
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('inicio')
    
    productos = Producto.objects.filter(activo=True).order_by('nombre')
    
    # Filtros
    categoria_id = request.GET.get('categoria', '')
    query = request.GET.get('q', '')
    
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) |
            Q(sku__icontains=query)
        )
    
    categorias = Categoria.objects.all().order_by('nombre')
    
    context = {
        'productos': productos,
        'categorias': categorias,
        'categoria_id': categoria_id,
        'query': query,
        'es_admin': True,
    }
    
    return render(request, 'inventario/imprimir_etiquetas.html', context)

@login_required
def generar_etiquetas_pdf(request):
    """Genera PDF con etiquetas de productos"""
    if not es_admin_bossa(request.user):
        return HttpResponse('No autorizado', status=403)
    
    producto_ids = request.GET.getlist('producto_id')
    if not producto_ids:
        return HttpResponse('No se seleccionaron productos', status=400)
    
    productos = Producto.objects.filter(id__in=producto_ids, activo=True)
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=(4*inch, 2*inch), 
                           rightMargin=0.2*inch, leftMargin=0.2*inch,
                           topMargin=0.2*inch, bottomMargin=0.2*inch)
    elements = []
    
    styles = getSampleStyleSheet()
    
    for producto in productos:
        # Nombre del producto
        nombre_style = ParagraphStyle(
            'Nombre',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            leading=12,
            alignment=0
        )
        nombre = Paragraph(producto.nombre[:30], nombre_style)
        
        # Precio
        precio_text = f"${producto.precio:,.0f}"
        if producto.precio_promo:
            precio_text = f"${producto.precio_promo:,.0f} (Promo)"
        
        precio_style = ParagraphStyle(
            'Precio',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.black,
            leading=16,
            alignment=0,
            fontName='Helvetica-Bold'
        )
        precio = Paragraph(precio_text, precio_style)
        
        # Código de barras
        if producto.sku:
            try:
                barcode = code128.Code128(producto.sku, barWidth=0.8*mm, barHeight=15*mm)
                elements.append(barcode)
            except:
                pass
        
        elements.append(nombre)
        elements.append(precio)
        elements.append(Spacer(1, 0.1*inch))
        elements.append(PageBreak())
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="etiquetas.pdf"'
    return response

@login_required
def imprimir_lista_precios(request):
    """Vista para generar lista de precios"""
    productos = Producto.objects.filter(activo=True).order_by('nombre')
    
    # Filtros
    categoria_id = request.GET.get('categoria', '')
    incluir_precio_compra = request.GET.get('precio_compra', '') == '1'
    solo_con_stock = request.GET.get('solo_stock', '') == '1'
    
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    if solo_con_stock:
        productos = productos.filter(stock__gt=0)
    
    categorias = Categoria.objects.all().order_by('nombre')
    
    context = {
        'productos': productos,
        'categorias': categorias,
        'categoria_id': categoria_id,
        'incluir_precio_compra': incluir_precio_compra,
        'solo_con_stock': solo_con_stock,
        'es_admin': es_admin_bossa(request.user),
    }
    
    return render(request, 'inventario/imprimir_lista_precios.html', context)

@login_required
def generar_lista_precios_pdf(request):
    """Genera PDF con lista de precios"""
    categoria_id = request.GET.get('categoria', '')
    incluir_precio_compra = request.GET.get('precio_compra', '') == '1'
    solo_con_stock = request.GET.get('solo_stock', '') == '1'
    es_admin = es_admin_bossa(request.user)
    
    productos = Producto.objects.filter(activo=True).order_by('nombre')
    
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
        categoria = Categoria.objects.get(id=categoria_id)
        titulo = f"Lista de Precios - {categoria.nombre}"
    else:
        titulo = "Lista de Precios - Todos los Productos"
    
    if solo_con_stock:
        productos = productos.filter(stock__gt=0)
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=20,
        alignment=1
    )
    
    # Título
    elements.append(Paragraph(titulo, title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Tabla
    headers = ['Producto', 'Categoría', 'Precio Venta']
    if incluir_precio_compra and es_admin:
        headers.append('Precio Compra')
        headers.append('Margen %')
    if es_admin:
        headers.append('Stock')
    
    data = [headers]
    
    for producto in productos:
        row = [
            producto.nombre[:40],
            producto.categoria.nombre[:20] if producto.categoria else '-',
            f"${producto.precio:,.0f}"
        ]
        if incluir_precio_compra and es_admin:
            precio_compra = f"${producto.precio_compra:,.0f}" if producto.precio_compra else '-'
            margen = f"{producto.margen_ganancia:.1f}%" if producto.margen_ganancia else '-'
            row.extend([precio_compra, margen])
        if es_admin:
            row.append(str(producto.stock))
        data.append(row)
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.beige]),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="lista_precios.pdf"'
    return response

@login_required
def imprimir_ticket_venta(request, venta_id):
    """Genera ticket de venta - por defecto térmica 58mm, o A4 si se especifica tipo=a4"""
    tipo = request.GET.get('tipo', 'termica')  # 'termica' o 'a4'
    
    if tipo == 'a4':
        return imprimir_ticket_venta_a4(request, venta_id)
    else:
        return imprimir_ticket_venta_termica(request, venta_id)

@login_required
def imprimir_ticket_venta_termica(request, venta_id):
    """Genera ticket de venta para impresión térmica 58mm"""
    venta = get_object_or_404(Venta, id=venta_id)
    
    # Permitir acceso al usuario que hizo la venta o al admin
    if not es_admin_bossa(request.user) and venta.usuario != request.user:
        messages.error(request, 'No tienes permisos para ver este ticket.')
        return redirect('listar_ventas')
    
    items = venta.items.all()
    
    buffer = io.BytesIO()
    # Formato optimizado para impresora térmica 58mm (ancho 80mm estándar, alto variable)
    doc = SimpleDocTemplate(buffer, pagesize=(80*mm, 250*mm),
                          rightMargin=3*mm, leftMargin=3*mm,
                          topMargin=4*mm, bottomMargin=4*mm)
    elements = []
    
    styles = getSampleStyleSheet()
    
    # Estilos optimizados para impresora térmica 58mm
    style_header = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.black,
        alignment=1,  # Center
        fontName='Helvetica-Bold',
        leading=13
    )
    
    style_normal = ParagraphStyle(
        'NormalTicket',
        parent=styles['Normal'],
        fontSize=7,
        leading=9,
        alignment=0,  # Left
    )
    
    style_center = ParagraphStyle(
        'CenterTicket',
        parent=styles['Normal'],
        fontSize=7,
        leading=9,
        alignment=1,  # Center
    )
    
    style_bold = ParagraphStyle(
        'BoldTicket',
        parent=styles['Normal'],
        fontSize=7,
        leading=9,
        alignment=0,
        fontName='Helvetica-Bold'
    )
    
    style_total = ParagraphStyle(
        'TotalTicket',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        alignment=2,  # Right
        fontName='Helvetica-Bold'
    )
    
    # ===== ENCABEZADO DEL NEGOCIO =====
    elements.append(Paragraph("BOTILLERÍA LA PREVIA", style_header))
    elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph("Lautaro 948", style_center))
    elements.append(Paragraph("Santa Juana, Bio Bio, Chile", style_center))
    elements.append(Paragraph("Tel: +56956499437", style_center))
    elements.append(Spacer(1, 3*mm))
    elements.append(Paragraph("-" * 32, style_center))
    elements.append(Spacer(1, 3*mm))
    
    # ===== INFORMACIÓN DE LA VENTA =====
    # Convertir fecha a zona horaria de Chile
    fecha_chile = timezone.localtime(venta.fecha)
    
    elements.append(Paragraph("TICKET DE VENTA", style_header))
    elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph(f"Venta #: {venta.numero_venta}", style_normal))
    elements.append(Paragraph(f"Fecha: {fecha_chile.strftime('%d/%m/%Y')}", style_normal))
    elements.append(Paragraph(f"Hora: {fecha_chile.strftime('%H:%M')}", style_normal))
    if venta.usuario:
        elements.append(Paragraph(f"Vendedor: {venta.usuario.username}", style_normal))
    elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph("-" * 32, style_center))
    elements.append(Spacer(1, 2*mm))
    
    # ===== PRODUCTOS =====
    if items.exists():
        # Tabla de productos
        data = [['Cant.', 'Producto', 'Precio', 'Total']]
        for item in items:
            # Truncar nombre si es muy largo
            nombre = item.nombre_producto[:25] + '...' if len(item.nombre_producto) > 25 else item.nombre_producto
            data.append([
                str(item.cantidad),
                nombre,
                f"${item.precio_unitario:,.0f}",
                f"${item.subtotal:,.0f}"
            ])
        
        # Tabla optimizada para impresora térmica 58mm
        table = Table(data, colWidths=[8*mm, 32*mm, 18*mm, 18*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 4),
            ('TOPPADDING', (0,0), (-1,0), 4),
            ('ALIGN', (0,0), (0,-1), 'CENTER'), # Cantidad centrada
            ('ALIGN', (1,0), (1,-1), 'LEFT'),   # Producto a la izquierda
            ('ALIGN', (2,0), (-1,-1), 'RIGHT'), # Precio y Total a la derecha
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTSIZE', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.25, colors.black), # Borde para la tabla
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No hay productos en esta venta.", style_center))
    
    elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph("-" * 32, style_center))
    elements.append(Spacer(1, 2*mm))
    
    # ===== TOTALES Y PAGO =====
    elements.append(Paragraph(f"Subtotal: ${venta.subtotal:,.0f}", style_total))
    if venta.descuento > 0:
        elements.append(Paragraph(f"Descuento: -${venta.descuento:,.0f}", style_total))
    elements.append(Paragraph(f"TOTAL: ${venta.total:,.0f}", style_total))
    elements.append(Spacer(1, 3*mm))
    
    elements.append(Paragraph(f"Método de Pago: {venta.get_metodo_pago_display()}", style_normal))
    if venta.metodo_pago in ['efectivo', 'mixto']:
        elements.append(Paragraph(f"Monto Recibido: ${venta.monto_recibido:,.0f}", style_normal))
        elements.append(Paragraph(f"Cambio: ${venta.cambio:,.0f}", style_normal))
    
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph("¡Gracias por su compra!", style_center))
    elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph("--- STOCKEX ---", style_center))
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="ticket_termico_{venta.numero_venta}.pdf"'
    return response

@login_required
def imprimir_ticket_venta_a4(request, venta_id):
    """Genera ticket de venta en formato A4 con formato similar a cotizaciones"""
    venta = get_object_or_404(Venta, id=venta_id)
    
    # Permitir acceso al usuario que hizo la venta o al admin
    if not es_admin_bossa(request.user) and venta.usuario != request.user:
        messages.error(request, 'No tienes permisos para ver este ticket.')
        return redirect('listar_ventas')
    
    items = venta.items.all()
    
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
    elements.append(Paragraph("TICKET DE VENTA", title_style))
    elements.append(Spacer(1, 10*mm))
    
    # Información de la venta
    fecha_chile = timezone.localtime(venta.fecha)
    info_data = [
        ['Número de Venta:', venta.numero_venta],
        ['Fecha:', fecha_chile.strftime('%d/%m/%Y')],
        ['Hora:', fecha_chile.strftime('%H:%M')],
        ['Método de Pago:', venta.get_metodo_pago_display()],
    ]
    if venta.usuario:
        info_data.append(['Vendedor:', venta.usuario.username])
    
    info_table = Table(info_data, colWidths=[60*mm, None])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(info_table)
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
        ['Subtotal:', f"${venta.subtotal:,.0f}"],
    ]
    if venta.descuento > 0:
        totales_data.append(['Descuento:', f"-${venta.descuento:,.0f}"])
    totales_data.append(['<b>TOTAL:</b>', f"<b>${venta.total:,.0f}</b>"])
    
    if venta.metodo_pago in ['efectivo', 'mixto']:
        totales_data.append(['Monto Recibido:', f"${venta.monto_recibido:,.0f}"])
        totales_data.append(['Cambio:', f"${venta.cambio:,.0f}"])
    
    totales_table = Table(totales_data, colWidths=[None, 50*mm])
    totales_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('FONTSIZE', (-1, -2), (-1, -2), 14),
        ('FONTNAME', (-1, -2), (-1, -2), 'Helvetica-Bold'),
    ]))
    elements.append(totales_table)
    
    if venta.notas:
        elements.append(Spacer(1, 10*mm))
        elements.append(Paragraph("<b>NOTAS:</b>", styles['Normal']))
        elements.append(Paragraph(venta.notas, styles['Normal']))
    
    elements.append(Spacer(1, 15*mm))
    elements.append(Paragraph("¡Gracias por su compra!", 
                              ParagraphStyle('Footer', parent=styles['Normal'], fontSize=11, alignment=1)))
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
    response['Content-Disposition'] = f'inline; filename="ticket_a4_{venta.numero_venta}.pdf"'
    return response

