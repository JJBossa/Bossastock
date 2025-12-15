from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q, F, Sum, Count
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import Producto, Categoria, HistorialCambio
from .forms import ProductoForm, CategoriaForm

def es_admin_bossa(user):
    """Verifica si el usuario es el admin bossa"""
    return user.is_authenticated and user.username == 'bossa'

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

def registrar_cambio(producto, usuario, tipo_cambio, campo_modificado=None, valor_anterior=None, valor_nuevo=None, descripcion=None):
    """Registra un cambio en el historial"""
    HistorialCambio.objects.create(
        producto=producto,
        usuario=usuario,
        tipo_cambio=tipo_cambio,
        campo_modificado=campo_modificado,
        valor_anterior=str(valor_anterior) if valor_anterior else None,
        valor_nuevo=str(valor_nuevo) if valor_nuevo else None,
        descripcion=descripcion
    )

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
    productos = Producto.objects.filter(activo=True)
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
        except:
            pass
    
    if precio_max:
        try:
            productos = productos.filter(precio__lte=float(precio_max))
        except:
            pass
    
    if stock_bajo == '1':
        productos = productos.filter(stock__lte=F('stock_minimo'))
    
    if con_imagen == '1':
        productos = productos.exclude(imagen__isnull=True).exclude(imagen='')
    elif con_imagen == '0':
        productos = productos.filter(imagen__isnull=True) | productos.filter(imagen='')
    
    # Búsqueda
    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) |
            Q(sku__icontains=query) |
            Q(descripcion__icontains=query)
        )
    
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
    
    # Obtener categorías para el filtro
    categorias = Categoria.objects.all().order_by('nombre')
    
    # Estadísticas rápidas
    total_productos = Producto.objects.filter(activo=True).count()
    productos_stock_bajo_count = Producto.objects.filter(activo=True, stock__lte=F('stock_minimo')).count()
    
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
    }
    
    return render(request, 'inventario/inicio.html', context)
