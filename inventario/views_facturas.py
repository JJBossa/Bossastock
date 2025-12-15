from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.core.paginator import Paginator
from .models import Factura, ItemFactura, Proveedor, Producto, HistorialCambio
from .forms_facturas import FacturaForm, ItemFacturaForm, ProveedorForm
from .utils_ocr import (
    procesar_imagen_ocr, 
    extraer_fecha, 
    extraer_numero_factura, 
    extraer_total,
    extraer_items_factura
)
from .views import es_admin_bossa, registrar_cambio

@login_required
def listar_facturas(request):
    """Lista todas las facturas"""
    facturas = Factura.objects.all().order_by('-fecha_subida')
    
    # Filtros
    estado = request.GET.get('estado', '')
    if estado:
        facturas = facturas.filter(estado=estado)
    
    proveedor_id = request.GET.get('proveedor', '')
    if proveedor_id:
        facturas = facturas.filter(proveedor_id=proveedor_id)
    
    # Paginación
    paginator = Paginator(facturas, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    proveedores = Proveedor.objects.all().order_by('nombre')
    
    context = {
        'facturas': page_obj,
        'proveedores': proveedores,
        'estado_filtro': estado,
        'proveedor_filtro': proveedor_id,
        'es_admin': es_admin_bossa(request.user),
    }
    
    return render(request, 'inventario/listar_facturas.html', context)

@login_required
def subir_factura(request):
    """Vista para subir una nueva factura"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('inicio')
    
    if request.method == 'POST':
        form = FacturaForm(request.POST, request.FILES)
        if form.is_valid():
            factura = form.save(commit=False)
            
            # Procesar OCR
            texto_extraido = procesar_imagen_ocr(factura.archivo)
            factura.texto_extraido = texto_extraido
            
            # Extraer información automáticamente
            if not factura.numero_factura:
                factura.numero_factura = extraer_numero_factura(texto_extraido)
            
            if not factura.fecha_emision:
                factura.fecha_emision = extraer_fecha(texto_extraido)
            
            if not factura.total:
                factura.total = extraer_total(texto_extraido) or 0
            
            factura.save()
            
            # Extraer items de la factura
            productos = Producto.objects.filter(activo=True)
            items_detectados = extraer_items_factura(texto_extraido, productos)
            
            # Crear items
            for item_data in items_detectados:
                ItemFactura.objects.create(
                    factura=factura,
                    producto=item_data.get('producto'),
                    nombre_producto=item_data['nombre_producto'],
                    cantidad=item_data['cantidad'],
                    precio_unitario=item_data['precio_unitario'],
                    subtotal=item_data['subtotal'],
                    producto_coincidencia=item_data['producto_coincidencia']
                )
            
            # Si no se detectaron items, mostrar advertencia
            if len(items_detectados) == 0:
                messages.warning(request, 'Factura subida pero no se detectaron items automáticamente. Puedes agregarlos manualmente.')
            else:
                messages.success(request, f'Factura subida y procesada exitosamente. Se detectaron {len(items_detectados)} items.')
            
            return redirect('editar_factura', factura_id=factura.id)
    else:
        form = FacturaForm()
    
    return render(request, 'inventario/subir_factura.html', {
        'form': form,
        'es_admin': True,
    })

@login_required
def editar_factura(request, factura_id):
    """Vista para editar y confirmar items de una factura"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('inicio')
    
    factura = get_object_or_404(Factura, id=factura_id)
    items = factura.items.all()
    productos = Producto.objects.filter(activo=True).order_by('nombre')
    
    if request.method == 'POST':
        if 'confirmar' in request.POST:
            # Procesar actualización de stock
            items_actualizados = 0
            
            for item in items:
                if item.producto and not item.stock_actualizado:
                    # Actualizar stock
                    stock_anterior = item.producto.stock
                    item.producto.stock += item.cantidad
                    item.producto.save()
                    
                    # Registrar cambio
                    registrar_cambio(
                        item.producto,
                        request.user,
                        'stock',
                        'stock',
                        stock_anterior,
                        item.producto.stock,
                        f'Actualizado desde factura {factura.numero_factura}'
                    )
                    
                    item.stock_actualizado = True
                    item.save()
                    items_actualizados += 1
            
            factura.estado = 'procesada'
            factura.procesado_por = request.user
            factura.save()
            
            messages.success(request, f'Factura procesada. Stock actualizado para {items_actualizados} productos.')
            return redirect('detalle_factura', factura_id=factura.id)
        
        elif 'guardar_items' in request.POST:
            # Guardar cambios en items
            for item in items:
                producto_id = request.POST.get(f'producto_{item.id}')
                nombre_producto = request.POST.get(f'nombre_producto_{item.id}')
                cantidad = request.POST.get(f'cantidad_{item.id}')
                precio = request.POST.get(f'precio_{item.id}')
                
                if producto_id:
                    item.producto_id = producto_id if producto_id != '' else None
                if nombre_producto:
                    item.nombre_producto = nombre_producto
                if cantidad:
                    try:
                        item.cantidad = int(cantidad)
                    except:
                        pass
                if precio:
                    try:
                        precio_limpio = str(precio).replace('.', '').replace(',', '').replace('$', '').strip()
                        item.precio_unitario = int(precio_limpio) if precio_limpio else 0
                    except:
                        pass
                
                item.save()
            
            # Recalcular total
            factura.total = items.aggregate(total=Sum('subtotal'))['total'] or 0
            factura.save()
            
            messages.success(request, 'Items actualizados correctamente.')
            return redirect('editar_factura', factura_id=factura.id)
        
        elif 'agregar_item' in request.POST:
            # Agregar nuevo item
            nombre = request.POST.get('nombre_nuevo')
            cantidad = int(request.POST.get('cantidad_nuevo', 1))
            precio = int(request.POST.get('precio_nuevo', 0).replace('.', '').replace(',', ''))
            producto_id = request.POST.get('producto_nuevo')
            
            ItemFactura.objects.create(
                factura=factura,
                producto_id=producto_id if producto_id else None,
                nombre_producto=nombre,
                cantidad=cantidad,
                precio_unitario=precio,
                subtotal=cantidad * precio
            )
            
            messages.success(request, 'Item agregado correctamente.')
            return redirect('editar_factura', factura_id=factura.id)
    
    context = {
        'factura': factura,
        'items': items,
        'productos': productos,
        'es_admin': True,
    }
    
    return render(request, 'inventario/editar_factura.html', context)

@login_required
def detalle_factura(request, factura_id):
    """Vista de detalle de una factura"""
    factura = get_object_or_404(Factura, id=factura_id)
    items = factura.items.all()
    
    context = {
        'factura': factura,
        'items': items,
        'es_admin': es_admin_bossa(request.user),
    }
    
    return render(request, 'inventario/detalle_factura.html', context)

@login_required
def eliminar_factura(request, factura_id):
    """Elimina una factura"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('inicio')
    
    factura = get_object_or_404(Factura, id=factura_id)
    
    if request.method == 'POST':
        # Eliminar archivo
        if factura.archivo:
            try:
                import os
                from django.conf import settings
                file_path = settings.MEDIA_ROOT / factura.archivo.name
                if file_path.exists():
                    os.remove(file_path)
            except:
                pass
        
        factura.delete()
        messages.success(request, 'Factura eliminada exitosamente.')
        return redirect('listar_facturas')
    
    return render(request, 'inventario/eliminar_factura.html', {
        'factura': factura,
        'es_admin': True,
    })

@login_required
def gestionar_proveedores(request):
    """Gestionar proveedores"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('inicio')
    
    proveedores = Proveedor.objects.all().order_by('nombre')
    
    if request.method == 'POST':
        if 'agregar' in request.POST:
            form = ProveedorForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Proveedor agregado exitosamente.')
                return redirect('gestionar_proveedores')
        elif 'editar' in request.POST:
            proveedor_id = request.POST.get('proveedor_id')
            proveedor = get_object_or_404(Proveedor, id=proveedor_id)
            form = ProveedorForm(request.POST, instance=proveedor)
            if form.is_valid():
                form.save()
                messages.success(request, 'Proveedor actualizado exitosamente.')
                return redirect('gestionar_proveedores')
        elif 'eliminar' in request.POST:
            proveedor_id = request.POST.get('proveedor_id')
            proveedor = get_object_or_404(Proveedor, id=proveedor_id)
            proveedor.delete()
            messages.success(request, 'Proveedor eliminado exitosamente.')
            return redirect('gestionar_proveedores')
    else:
        form = ProveedorForm()
    
    return render(request, 'inventario/gestionar_proveedores.html', {
        'proveedores': proveedores,
        'form': form,
        'es_admin': True,
    })

