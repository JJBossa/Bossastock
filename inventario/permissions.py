"""
Permisos personalizados para la API REST
"""
from rest_framework import permissions
from .utils import es_admin_bossa


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado: Solo administradores pueden crear/editar/eliminar.
    Los demás usuarios solo pueden leer.
    """
    
    def has_permission(self, request, view):
        # Permitir lectura a todos los usuarios autenticados
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Para escritura, solo administradores
        return request.user and request.user.is_authenticated and es_admin_bossa(request.user)


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permiso personalizado: Solo el propietario o administrador puede acceder.
    """
    
    def has_object_permission(self, request, view, obj):
        # Administradores pueden hacer todo
        if es_admin_bossa(request.user):
            return True
        
        # Verificar si el objeto tiene un campo 'usuario'
        if hasattr(obj, 'usuario'):
            return obj.usuario == request.user
        
        # Verificar si el objeto tiene un campo 'user'
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Por defecto, denegar
        return False


class IsAdminBossa(permissions.BasePermission):
    """
    Permiso personalizado: Solo el administrador bossa puede acceder.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and es_admin_bossa(request.user)

