from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Producto, ProductoFavorito
from .utils import es_admin_bossa

@login_required
@require_POST
def toggle_favorito(request, producto_id):
    """Agregar o quitar producto de favoritos"""
    
    producto = get_object_or_404(Producto, id=producto_id)
    
    favorito, created = ProductoFavorito.objects.get_or_create(
        usuario=request.user,
        producto=producto
    )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Si es una petición AJAX
        if not created:
            # Ya existía, lo eliminamos
            favorito.delete()
            return JsonResponse({'favorito': False, 'mensaje': 'Producto removido de favoritos'})
        else:
            # Fue creado, lo agregamos
            return JsonResponse({'favorito': True, 'mensaje': 'Producto agregado a favoritos'})
    else:
        # Si es una petición normal (POST)
        if not created:
            favorito.delete()
            messages.success(request, f'"{producto.nombre}" removido de favoritos')
        else:
            messages.success(request, f'"{producto.nombre}" agregado a favoritos')
        
        # Redirigir de donde vino
        return redirect(request.META.get('HTTP_REFERER', 'inicio'))

@login_required
def mis_favoritos(request):
    """Lista los productos favoritos del usuario"""
    favoritos = ProductoFavorito.objects.filter(usuario=request.user).select_related('producto')
    productos_favoritos = [fav.producto for fav in favoritos]
    
    # Ordenar por fecha de agregado (más recientes primero)
    productos_favoritos = sorted(productos_favoritos, 
                                  key=lambda p: ProductoFavorito.objects.get(
                                      usuario=request.user, producto=p
                                  ).fecha_agregado, 
                                  reverse=True)
    
    context = {
        'productos': productos_favoritos,
        'total_favoritos': len(productos_favoritos),
        'es_admin': es_admin_bossa(request.user),
    }
    
    return render(request, 'inventario/mis_favoritos.html', context)

