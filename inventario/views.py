from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q, F, Sum, Count
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import CharField
from django.db.models.functions import Lower, Replace
from django.core.exceptions import ValidationError
from datetime import timedelta
from .models import Producto, Categoria, HistorialCambio, ProductoFavorito, MovimientoStock
from .forms import ProductoForm, CategoriaForm
from .utils import es_admin_bossa, normalizar_texto, registrar_cambio, logger, get_categorias_cached

def login_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('inicio')
    else:
        form = AuthenticationForm()
    
    return render(request, 'inventario/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

# registrar_cambio ahora está en utils.py

@login_required
def agregar_producto(request):
    """Vista para agregar un nuevo producto (solo para bossa)"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('inicio')
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save()
            registrar_cambio(producto, request.user, 'crear', descripcion=f'Producto creado: {producto.nombre}')
            messages.success(request, f'Producto "{producto.nombre}" agregado exitosamente.')
            return redirect('inicio')
    else:
        form = ProductoForm()
    
    return render(request, 'inventario/agregar_producto.html', {
        'form': form,
        'es_admin': True,
    })

@login_required
def editar_producto(request, producto_id):
    """Vista para editar un producto existente (solo para bossa)"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('inicio')
    
    producto = get_object_or_404(Producto, id=producto_id)
    producto_original = Producto.objects.get(id=producto_id)
    
    if request.method == 'POST':
        # Verificar si se quiere eliminar la imagen
        if 'eliminar_imagen' in request.POST:
            if producto.imagen:
                try:
                    import os
                    from django.conf import settings
                    old_image_path = settings.MEDIA_ROOT / producto.imagen.name
                    if old_image_path.exists():
                        os.remove(old_image_path)
                    producto.imagen = None
                    producto.save()
                    registrar_cambio(producto, request.user, 'editar', 'imagen', 'Imagen eliminada', 'Sin imagen')
                    messages.success(request, 'Imagen eliminada exitosamente.')
                except Exception as e:
                    messages.error(request, f'Error al eliminar la imagen: {str(e)}')
            else:
                messages.warning(request, 'El producto no tiene imagen para eliminar.')
            return redirect('editar_producto', producto_id=producto.id)
        
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            # Registrar cambios en campos
            cambios = []
            if producto_original.nombre != form.cleaned_data['nombre']:
                registrar_cambio(producto, request.user, 'editar', 'nombre', producto_original.nombre, form.cleaned_data['nombre'])
            if producto_original.precio != form.cleaned_data['precio']:
                registrar_cambio(producto, request.user, 'editar', 'precio', producto_original.precio, form.cleaned_data['precio'])
            if producto_original.stock != form.cleaned_data['stock']:
                registrar_cambio(producto, request.user, 'stock', 'stock', producto_original.stock, form.cleaned_data['stock'])
            
            # Si se sube una nueva imagen, eliminar la anterior si existe
            if 'imagen' in request.FILES and producto.imagen:
                try:
                    import os
                    from django.conf import settings
                    old_image_path = settings.MEDIA_ROOT / producto.imagen.name
                    if old_image_path.exists():
                        os.remove(old_image_path)
                except:
                    pass
            
            producto = form.save()
            messages.success(request, f'Producto "{producto.nombre}" actualizado exitosamente.')
            return redirect('inicio')
    else:
        form = ProductoForm(instance=producto)
    
    return render(request, 'inventario/editar_producto.html', {
        'form': form,
        'producto': producto,
        'es_admin': True,
    })

@login_required
def eliminar_producto(request, producto_id):
    """Vista para eliminar un producto (solo para bossa)"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('inicio')
    
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        nombre_producto = producto.nombre
        # Eliminar imagen si existe
        if producto.imagen:
            try:
                import os
                from django.conf import settings
                image_path = settings.MEDIA_ROOT / producto.imagen.name
                if image_path.exists():
                    os.remove(image_path)
            except:
                pass
        
        # Registrar eliminación antes de borrar
        registrar_cambio(producto, request.user, 'eliminar', descripcion=f'Producto eliminado: {nombre_producto}')
        producto.delete()
        messages.success(request, f'Producto "{nombre_producto}" eliminado exitosamente.')
        return redirect('inicio')
    
    return render(request, 'inventario/eliminar_producto.html', {
        'producto': producto,
        'es_admin': True,
    })

@login_required
def inicio(request):
    # Optimización: usar select_related para evitar N+1 queries
    productos = Producto.objects.filter(activo=True).select_related('categoria')
    query = request.GET.get('q', '')
    orden = request.GET.get('orden', 'nombre_asc')
    categoria_id = request.GET.get('categoria', '')
    precio_min = request.GET.get('precio_min', '')
    precio_max = request.GET.get('precio_max', '')
    stock_bajo = request.GET.get('stock_bajo', '')
    con_imagen = request.GET.get('con_imagen', '')
    vista = request.GET.get('vista', 'grid')  # grid o lista
    
    # Filtros avanzados
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    
    if precio_min:
        try:
            productos = productos.filter(precio__gte=float(precio_min))
        except (ValueError, TypeError):
            logger.warning(f'Precio mínimo inválido: {precio_min}', extra={'user': request.user.username})
            pass
    
    if precio_max:
        try:
            productos = productos.filter(precio__lte=float(precio_max))
        except (ValueError, TypeError):
            logger.warning(f'Precio máximo inválido: {precio_max}', extra={'user': request.user.username})
            pass
    
    if stock_bajo == '1':
        productos = productos.filter(stock__lte=F('stock_minimo'))
    
    if con_imagen == '1':
        productos = productos.exclude(imagen__isnull=True).exclude(imagen='')
    elif con_imagen == '0':
        productos = productos.filter(Q(imagen__isnull=True) | Q(imagen=''))
    
    # Búsqueda optimizada - usar queries de base de datos en lugar de iteración en memoria
    if query:
        query_normalizado = normalizar_texto(query)
        
        # Búsqueda directa en DB (mucho más rápida que iterar en memoria)
        # Buscar en nombre, SKU y descripción
        q_objects = Q()
        
        # Para búsqueda insensible a tildes, necesitamos una estrategia híbrida
        # Primero intentar búsqueda directa (rápida)
        q_objects |= Q(nombre__icontains=query)
        q_objects |= Q(sku__icontains=query)
        q_objects |= Q(descripcion__icontains=query)
        
        # Si la búsqueda contiene caracteres con tilde, también buscar sin tilde
        # Ejemplo: buscar "cafe" también encuentra "café"
        productos_filtrados = productos.filter(q_objects)
        
        # Si no hay resultados con búsqueda directa, intentar búsqueda normalizada
        # Solo si la búsqueda directa no dio resultados
        if not productos_filtrados.exists() and query != query_normalizado:
            # Búsqueda adicional normalizada (más lenta, solo si es necesario)
            productos_ids = []
            productos_temp = productos.only('id', 'nombre', 'sku', 'descripcion')
            
            for producto in productos_temp:
                nombre_norm = normalizar_texto(producto.nombre)
                sku_norm = normalizar_texto(producto.sku or '')
                descripcion_norm = normalizar_texto(producto.descripcion or '')
                
                if (query_normalizado in nombre_norm or 
                    query_normalizado in sku_norm or 
                    query_normalizado in descripcion_norm):
                    productos_ids.append(producto.id)
            
            if productos_ids:
                productos = productos.filter(id__in=productos_ids)
            else:
                productos = productos.none()
        else:
            productos = productos_filtrados
        
        logger.info(f'Búsqueda realizada: "{query}" - {productos.count()} resultados', 
                   extra={'user': request.user.username})
    
    # Ordenamiento
    if orden == 'nombre_asc':
        productos = productos.order_by('nombre')
    elif orden == 'nombre_desc':
        productos = productos.order_by('-nombre')
    elif orden == 'precio_asc':
        productos = productos.order_by('precio')
    elif orden == 'precio_desc':
        productos = productos.order_by('-precio')
    elif orden == 'stock_asc':
        productos = productos.order_by('stock')
    elif orden == 'stock_desc':
        productos = productos.order_by('-stock')
    elif orden == 'fecha_desc':
        productos = productos.order_by('-fecha_creacion')
    
    # Paginación
    paginator = Paginator(productos, 24)  # 24 productos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener categorías para el filtro (desde caché)
    categorias_data = get_categorias_cached()
    # Convertir a objetos Categoria para compatibilidad con template
    categorias = Categoria.objects.filter(id__in=[c['id'] for c in categorias_data]).order_by('nombre')
    
    # Estadísticas rápidas
    total_productos = Producto.objects.filter(activo=True).count()
    productos_stock_bajo_count = Producto.objects.filter(activo=True, stock__lte=F('stock_minimo')).count()
    
    # Obtener IDs de productos favoritos del usuario
    favoritos_ids = set()
    if request.user.is_authenticated:
        favoritos_ids = set(ProductoFavorito.objects.filter(
            usuario=request.user
        ).values_list('producto_id', flat=True))
    
    context = {
        'productos': page_obj,
        'query': query,
        'orden': orden,
        'categoria_id': categoria_id,
        'precio_min': precio_min,
        'precio_max': precio_max,
        'stock_bajo': stock_bajo,
        'con_imagen': con_imagen,
        'vista': vista,
        'categorias': categorias,
        'total_productos': total_productos,
        'productos_stock_bajo_count': productos_stock_bajo_count,
        'es_admin': es_admin_bossa(request.user),
        'favoritos_ids': favoritos_ids,  # IDs de productos favoritos
    }
    
    return render(request, 'inventario/inicio.html', context)

@login_required
def actualizar_stock_rapido(request, producto_id):
    """Vista AJAX para actualizar stock rápidamente con botones +/-"""
    if not es_admin_bossa(request.user):
        return JsonResponse({'error': 'No tienes permisos'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    producto = get_object_or_404(Producto, id=producto_id)
    accion = request.POST.get('accion')  # 'sumar', 'restar', o 'set'
    cantidad = request.POST.get('cantidad', '0')
    
    try:
        cantidad = int(cantidad)
        stock_anterior = producto.stock
        
        if accion == 'sumar':
            nuevo_stock = producto.stock + cantidad
        elif accion == 'restar':
            nuevo_stock = max(0, producto.stock - cantidad)  # No permitir negativo
        elif accion == 'set':
            nuevo_stock = max(0, cantidad)  # No permitir negativo
        else:
            return JsonResponse({'error': 'Acción no válida'}, status=400)
        
        producto.stock = nuevo_stock
        producto.save()
        
        # Registrar movimiento de stock
        tipo_movimiento = 'entrada' if accion == 'sumar' else 'salida' if accion == 'restar' else 'ajuste'
        MovimientoStock.objects.create(
            producto=producto,
            tipo=tipo_movimiento,
            cantidad=abs(nuevo_stock - stock_anterior),
            motivo='ajuste_inventario' if accion == 'set' else 'otro',
            stock_anterior=stock_anterior,
            stock_nuevo=nuevo_stock,
            usuario=request.user,
            notas=f'Actualización rápida: {accion} {cantidad if accion != "set" else ""}'
        )
        
        # Registrar cambio
        registrar_cambio(
            producto, 
            request.user, 
            'stock', 
            'stock', 
            stock_anterior, 
            nuevo_stock,
            f'Stock actualizado rápidamente: {accion} {cantidad if accion != "set" else ""}'
        )
        
        return JsonResponse({
            'success': True,
            'stock': producto.stock,
            'stock_bajo': producto.stock_bajo,
            'mensaje': f'Stock actualizado: {stock_anterior} → {nuevo_stock}'
        })
    except ValueError:
        return JsonResponse({'error': 'Cantidad inválida. Debe ser un número.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)
