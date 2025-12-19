from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Factura, ItemFactura, Proveedor, Producto, HistorialCambio, Categoria
from .forms_facturas import FacturaForm, ItemFacturaForm, ProveedorForm
from .utils_ocr import extraer_texto_ocr, extraer_items_factura
from .utils import es_admin_bossa, registrar_cambio
from django.conf import settings

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
            factura.save()  # Guardar primero para tener el archivo disponible

            # =====================
            # PROCESAR OCR (ASÍNCRONO CON CELERY SI ESTÁ DISPONIBLE)
            # =====================
            texto_extraido = ""
            usar_celery = not getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)
            
            try:
                # Intentar usar Celery si está disponible
                if usar_celery:
                    try:
                        from .tasks import procesar_factura_ocr_async
                        # Procesar de forma asíncrona
                        task = procesar_factura_ocr_async.delay(factura.id)
                        messages.info(
                            request,
                            f'Factura subida exitosamente. El procesamiento OCR está en curso. '
                            f'ID de tarea: {task.id}. La factura se actualizará automáticamente cuando termine.'
                        )
                        # No esperamos el resultado, se procesará en background
                        texto_extraido = ""  # Se procesará después
                    except Exception as celery_error:
                        # Si Celery falla, procesar de forma síncrona
                        usar_celery = False
                        messages.warning(
                            request,
                            f'Celery no disponible ({str(celery_error)}). Procesando OCR de forma síncrona...'
                        )
                
                # Procesar de forma síncrona si Celery no está disponible o falló
                if not usar_celery:
                    ruta_imagen = factura.archivo.path
                    
                    # Verificar que el archivo existe
                    import os
                    if not os.path.exists(ruta_imagen):
                        messages.error(request, f'El archivo no se encontró en: {ruta_imagen}')
                    else:
                        texto_extraido = extraer_texto_ocr(ruta_imagen)
                        factura.texto_extraido = texto_extraido
                        factura.save()
                        
                        # Debug: mostrar longitud del texto extraído
                        if texto_extraido:
                            messages.success(
                                request, 
                                f'OCR completado exitosamente. Se extrajeron {len(texto_extraido)} caracteres de texto.'
                            )
                        else:
                            messages.warning(
                                request,
                                'OCR completado pero no se extrajo texto. '
                                'Verifica que la imagen sea legible y tenga buena calidad.'
                            )
                        
            except Exception as e:
                import traceback
                error_detalle = traceback.format_exc()
                messages.error(
                    request, 
                    f'Error al procesar OCR: {str(e)}. '
                    'Verifica la consola del servidor para más detalles.'
                )
                print(f"Error detallado en OCR:\n{error_detalle}")

            # =====================
            # EXTRAER ITEMS DE LA FACTURA
            # =====================
            items_detectados = []
            if texto_extraido:
                try:
                    items_detectados = extraer_items_factura(texto_extraido)
                except Exception as e:
                    messages.warning(
                        request, 
                        f'Error al extraer items automáticamente: {str(e)}. '
                        'Puedes agregarlos manualmente.'
                    )

            # Crear items detectados en la base de datos
            for item in items_detectados:
                try:
                    ItemFactura.objects.create(
                        factura=factura,
                        nombre_producto=item['nombre'],
                        cantidad=item['cantidad'],
                        precio_unitario=item['precio'],
                        subtotal=item['cantidad'] * item['precio']
                    )
                except Exception as e:
                    messages.warning(
                        request, 
                        f'Error al guardar item "{item.get("nombre", "desconocido")}": {str(e)}'
                    )

            # Mensajes de resultado
            if not items_detectados:
                messages.info(
                    request,
                    'Factura subida correctamente. No se detectaron items automáticamente. '
                    'Puedes agregarlos manualmente en la siguiente pantalla.'
                )
            else:
                messages.success(
                    request,
                    f'Factura procesada exitosamente. Se detectaron {len(items_detectados)} item(s).'
                )

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
            # Procesar creación de productos y actualización de stock
            productos_creados = 0
            items_actualizados = 0
            
            for item in items:
                # Verificar si se debe crear un nuevo producto
                crear_producto = request.POST.get(f'crear_producto_{item.id}', '') == 'on'
                
                if crear_producto and not item.producto:
                    # Crear nuevo producto desde el item
                    try:
                        # Obtener categoría por defecto o primera disponible
                        categoria = Categoria.objects.first()
                        
                        nuevo_producto = Producto.objects.create(
                            nombre=item.nombre_producto,
                            precio=item.precio_unitario,
                            stock=item.cantidad,
                            categoria=categoria,
                            activo=True
                        )
                        
                        item.producto = nuevo_producto
                        item.save()
                        
                        # Registrar creación
                        registrar_cambio(
                            nuevo_producto,
                            request.user,
                            'crear',
                            descripcion=f'Producto creado desde factura {factura.numero_factura or factura.id}'
                        )
                        
                        productos_creados += 1
                        items_actualizados += 1
                        
                    except Exception as e:
                        messages.error(request, f'Error al crear producto {item.nombre_producto}: {str(e)}')
                
                elif item.producto and not item.stock_actualizado:
                    # Actualizar stock de producto existente
                    stock_anterior = item.producto.stock
                    item.producto.stock += item.cantidad
                    
                    # Actualizar precio si es diferente
                    if item.producto.precio != item.precio_unitario:
                        item.producto.precio = item.precio_unitario
                    
                    item.producto.save()
                    
                    # Registrar cambio
                    registrar_cambio(
                        item.producto,
                        request.user,
                        'stock',
                        'stock',
                        stock_anterior,
                        item.producto.stock,
                        f'Actualizado desde factura {factura.numero_factura or factura.id}'
                    )
                    
                    item.stock_actualizado = True
                    item.save()
                    items_actualizados += 1
            
            factura.estado = 'procesada'
            factura.procesado_por = request.user
            factura.save()
            
            mensaje = f'Factura procesada exitosamente. '
            if productos_creados > 0:
                mensaje += f'Se crearon {productos_creados} producto(s) nuevo(s). '
            if items_actualizados > 0:
                mensaje += f'Stock actualizado para {items_actualizados} item(s).'
            
            messages.success(request, mensaje)
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
            precio_str = request.POST.get('precio_nuevo', '0').replace('.', '').replace(',', '').replace('$', '').strip()
            try:
                precio = int(precio_str) if precio_str else 0
            except:
                precio = 0
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


@login_required
def buscar_producto_codigo_barras(request):
    """
    API endpoint para buscar producto por código de barras (SKU).
    Usado por el escáner de códigos de barras.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    codigo = request.POST.get('codigo', '').strip()
    
    if not codigo:
        return JsonResponse({'error': 'Código de barras requerido'}, status=400)
    
    try:
        # Buscar por SKU (código de barras)
        producto = Producto.objects.get(sku=codigo, activo=True)
        return JsonResponse({
            'encontrado': True,
            'producto': {
                'id': producto.id,
                'nombre': producto.nombre,
                'precio': float(producto.precio),
                'stock': producto.stock,
                'categoria': producto.categoria.nombre if producto.categoria else None,
            }
        })
    except Producto.DoesNotExist:
        return JsonResponse({
            'encontrado': False,
            'mensaje': f'Producto con código {codigo} no encontrado'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
