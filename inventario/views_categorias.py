from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Categoria, Producto
from .forms import CategoriaForm
from .utils import es_admin_bossa, logger, invalidar_cache_categorias


@login_required
def gestionar_categorias(request):
    """Vista para listar, agregar y editar categorías (solo admin)"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('inicio')
    
    categorias = Categoria.objects.all().annotate(
        producto_count=models.Count('producto')
    ).order_by('nombre')
    
    # Formulario para nueva categoría
    if request.method == 'POST':
        if 'eliminar' in request.POST:
            # Eliminar categoría
            categoria_id = request.POST.get('categoria_id')
            categoria = get_object_or_404(Categoria, id=categoria_id)
            nombre = categoria.nombre
            categoria.delete()
            invalidar_cache_categorias()  # Invalidar caché al eliminar categoría
            messages.success(request, f'Categoría "{nombre}" eliminada exitosamente.')
            return redirect('gestionar_categorias')
        else:
            # Crear o editar categoría
            categoria_id = request.POST.get('categoria_id')
            if categoria_id:
                # Editar existente
                categoria = get_object_or_404(Categoria, id=categoria_id)
                form = CategoriaForm(request.POST, instance=categoria)
                if form.is_valid():
                    form.save()
                    invalidar_cache_categorias()  # Invalidar caché al modificar categoría
                    messages.success(request, f'Categoría "{categoria.nombre}" actualizada exitosamente.')
                    return redirect('gestionar_categorias')
            else:
                # Crear nueva
                form = CategoriaForm(request.POST)
                if form.is_valid():
                    categoria = form.save()
                    invalidar_cache_categorias()  # Invalidar caché al crear categoría
                    messages.success(request, f'Categoría "{categoria.nombre}" creada exitosamente.')
                    return redirect('gestionar_categorias')
    else:
        form = CategoriaForm()
    
    context = {
        'categorias': categorias,
        'form': form,
        'es_admin': True,
    }
    
    return render(request, 'inventario/gestionar_categorias.html', context)


@login_required
def editar_categoria_ajax(request, categoria_id):
    """Obtener datos de una categoría para edición via AJAX"""
    if not es_admin_bossa(request.user):
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    categoria = get_object_or_404(Categoria, id=categoria_id)
    return JsonResponse({
        'id': categoria.id,
        'nombre': categoria.nombre,
        'descripcion': categoria.descripcion or '',
        'color': categoria.color,
    })


# Importar models para Count
from django.db import models

