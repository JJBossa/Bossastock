from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .utils import es_admin_bossa

@login_required
def listar_usuarios(request):
    """Lista todos los usuarios - Solo para admin"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('inicio')
    
    # Búsqueda
    query = request.GET.get('q', '')
    usuarios = User.objects.all().order_by('username')
    
    if query:
        usuarios = usuarios.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
    
    # Paginación
    paginator = Paginator(usuarios, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'usuarios': page_obj,
        'query': query,
        'total_usuarios': usuarios.count(),
    }
    
    return render(request, 'inventario/listar_usuarios.html', context)

@login_required
def crear_usuario(request):
    """Crear un nuevo usuario - Solo para admin"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('inicio')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        
        # Validaciones
        if not username:
            messages.error(request, 'El nombre de usuario es obligatorio.')
            return redirect('crear_usuario')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, f'El usuario "{username}" ya existe.')
            return redirect('crear_usuario')
        
        if not password:
            messages.error(request, 'La contraseña es obligatoria.')
            return redirect('crear_usuario')
        
        if password != password_confirm:
            messages.error(request, 'Las contraseñas no coinciden.')
            return redirect('crear_usuario')
        
        if len(password) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres.')
            return redirect('crear_usuario')
        
        # Crear usuario
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=is_staff,
                is_superuser=is_superuser
            )
            messages.success(request, f'Usuario "{username}" creado exitosamente.')
            return redirect('listar_usuarios')
        except Exception as e:
            messages.error(request, f'Error al crear usuario: {str(e)}')
            return redirect('crear_usuario')
    
    return render(request, 'inventario/crear_usuario.html')

@login_required
def editar_usuario(request, user_id):
    """Editar un usuario existente - Solo para admin"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('inicio')
    
    usuario = get_object_or_404(User, id=user_id)
    
    # No permitir editar al mismo usuario admin (bossa)
    if usuario.username == 'bossa' and request.user.username != 'bossa':
        messages.error(request, 'No puedes editar este usuario.')
        return redirect('listar_usuarios')
    
    if request.method == 'POST':
        usuario.username = request.POST.get('username', usuario.username)
        usuario.email = request.POST.get('email', usuario.email)
        usuario.first_name = request.POST.get('first_name', '')
        usuario.last_name = request.POST.get('last_name', '')
        usuario.is_staff = request.POST.get('is_staff') == 'on'
        usuario.is_superuser = request.POST.get('is_superuser') == 'on'
        usuario.is_active = request.POST.get('is_active') == 'on'
        
        # Verificar si el username ya existe (excepto el mismo usuario)
        if User.objects.filter(username=usuario.username).exclude(id=usuario.id).exists():
            messages.error(request, f'El usuario "{usuario.username}" ya existe.')
            return redirect('editar_usuario', user_id=user_id)
        
        usuario.save()
        messages.success(request, f'Usuario "{usuario.username}" actualizado exitosamente.')
        return redirect('listar_usuarios')
    
    context = {
        'usuario': usuario,
    }
    
    return render(request, 'inventario/editar_usuario.html', context)

@login_required
def resetear_password(request, user_id):
    """Resetear la contraseña de un usuario - Solo para admin"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('inicio')
    
    usuario = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        nueva_password = request.POST.get('nueva_password')
        confirmar_password = request.POST.get('confirmar_password')
        
        if not nueva_password:
            messages.error(request, 'La contraseña es obligatoria.')
            return redirect('resetear_password', user_id=user_id)
        
        if nueva_password != confirmar_password:
            messages.error(request, 'Las contraseñas no coinciden.')
            return redirect('resetear_password', user_id=user_id)
        
        if len(nueva_password) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres.')
            return redirect('resetear_password', user_id=user_id)
        
        usuario.set_password(nueva_password)
        usuario.save()
        messages.success(request, f'Contraseña de "{usuario.username}" actualizada exitosamente.')
        return redirect('listar_usuarios')
    
    context = {
        'usuario': usuario,
    }
    
    return render(request, 'inventario/resetear_password.html', context)

@login_required
def eliminar_usuario(request, user_id):
    """Eliminar un usuario - Solo para admin"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('inicio')
    
    usuario = get_object_or_404(User, id=user_id)
    
    # No permitir eliminar al mismo usuario admin (bossa)
    if usuario.username == 'bossa':
        messages.error(request, 'No puedes eliminar este usuario.')
        return redirect('listar_usuarios')
    
    # No permitir auto-eliminarse
    if usuario.id == request.user.id:
        messages.error(request, 'No puedes eliminar tu propio usuario.')
        return redirect('listar_usuarios')
    
    if request.method == 'POST':
        username = usuario.username
        usuario.delete()
        messages.success(request, f'Usuario "{username}" eliminado exitosamente.')
        return redirect('listar_usuarios')
    
    context = {
        'usuario': usuario,
    }
    
    return render(request, 'inventario/eliminar_usuario.html', context)

