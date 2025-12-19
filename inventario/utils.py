"""
Utilidades compartidas para la aplicación inventario
"""
import unicodedata
import logging
from typing import Optional, List, Dict, Any
from django.db import transaction
from django.core.cache import cache
from django.contrib.auth.models import User
from .models import HistorialCambio, Producto, Categoria
from .constants import CACHE_TIMEOUT_LARGO

# Logger con formato estructurado
logger = logging.getLogger('inventario')


def es_admin_bossa(user: User) -> bool:
    """
    Verifica si el usuario es el admin bossa o tiene permisos de administrador
    
    MANTIENE COMPATIBILIDAD HACIA ATRÁS:
    - Si el usuario es 'bossa', retorna True
    - Si el usuario está en el grupo 'Administrador', retorna True
    - Si el usuario es superuser, retorna True
    
    Args:
        user: Usuario de Django
        
    Returns:
        bool: True si es admin, False en caso contrario
    """
    if not user or not user.is_authenticated:
        return False
    
    # Compatibilidad: usuario 'bossa' siempre es admin
    if user.username == 'bossa':
        return True
    
    # Verificar si es superuser
    if user.is_superuser:
        return True
    
    # Verificar si está en el grupo Administrador
    if user.groups.filter(name='Administrador').exists():
        return True
    
    return False


def tiene_permiso(user: User, permiso_codename: str, model_class=None) -> bool:
    """
    Verifica si un usuario tiene un permiso específico
    
    Args:
        user: Usuario de Django
        permiso_codename: Código del permiso (ej: 'add_producto', 'change_venta')
        model_class: Clase del modelo (opcional, para verificar content type)
        
    Returns:
        bool: True si tiene el permiso, False en caso contrario
    """
    if not user or not user.is_authenticated:
        return False
    
    # Superuser y admin bossa tienen todos los permisos
    if es_admin_bossa(user):
        return True
    
    # Verificar permiso directamente
    if model_class:
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(model_class)
        permiso = f"{ct.app_label}.{permiso_codename}"
        return user.has_perm(permiso)
    
    # Verificar permiso genérico
    return user.has_perm(permiso_codename)


def es_vendedor(user: User) -> bool:
    """Verifica si el usuario es vendedor"""
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name='Vendedor').exists() or es_admin_bossa(user)


def es_almacenero(user: User) -> bool:
    """Verifica si el usuario es almacenero"""
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name='Almacenero').exists() or es_admin_bossa(user)


def normalizar_texto(texto: Optional[str]) -> str:
    """
    Normaliza texto removiendo tildes y convirtiendo a minúsculas
    Útil para búsquedas insensibles a acentos
    
    Args:
        texto: Texto a normalizar
        
    Returns:
        str: Texto normalizado
    """
    if not texto:
        return ''
    # Normalizar a NFD (descomponer caracteres) y remover diacríticos
    texto_normalizado = unicodedata.normalize('NFD', texto.lower())
    # Filtrar solo caracteres que no son diacríticos
    texto_sin_tildes = ''.join(
        char for char in texto_normalizado 
        if unicodedata.category(char) != 'Mn'
    )
    return texto_sin_tildes


@transaction.atomic
def registrar_cambio(
    producto: Producto,
    usuario: Optional[User],
    tipo_cambio: str,
    campo_modificado: Optional[str] = None,
    valor_anterior: Optional[Any] = None,
    valor_nuevo: Optional[Any] = None,
    descripcion: Optional[str] = None
) -> HistorialCambio:
    """
    Registra un cambio en el historial de un producto con logging estructurado
    
    Args:
        producto: Instancia del modelo Producto
        usuario: Usuario que realizó el cambio
        tipo_cambio: Tipo de cambio ('crear', 'editar', 'eliminar', 'stock')
        campo_modificado: Nombre del campo modificado (opcional)
        valor_anterior: Valor anterior del campo (opcional)
        valor_nuevo: Valor nuevo del campo (opcional)
        descripcion: Descripción adicional del cambio (opcional)
        
    Returns:
        HistorialCambio: Instancia creada del historial
    """
    historial = HistorialCambio.objects.create(
        producto=producto,
        usuario=usuario,
        tipo_cambio=tipo_cambio,
        campo_modificado=campo_modificado,
        valor_anterior=str(valor_anterior) if valor_anterior is not None else None,
        valor_nuevo=str(valor_nuevo) if valor_nuevo is not None else None,
        descripcion=descripcion
    )
    
    # Logging estructurado
    logger.info(
        'Cambio registrado en historial',
        extra={
            'producto_id': producto.id,
            'producto_nombre': producto.nombre,
            'usuario': usuario.username if usuario else None,
            'tipo_cambio': tipo_cambio,
            'campo_modificado': campo_modificado,
            'historial_id': historial.id,
        }
    )
    
    return historial


def calcular_margen_ganancia(precio_venta: float, precio_compra: Optional[float]) -> Optional[float]:
    """
    Calcula el margen de ganancia en porcentaje
    
    Args:
        precio_venta: Precio de venta del producto
        precio_compra: Precio de compra del producto
        
    Returns:
        float: Margen de ganancia en porcentaje, o None si no se puede calcular
    """
    if precio_compra and precio_compra > 0:
        return ((precio_venta - precio_compra) / precio_compra) * 100
    return None


def calcular_ganancia_unitaria(precio_venta: float, precio_compra: Optional[float]) -> Optional[float]:
    """
    Calcula la ganancia por unidad
    
    Args:
        precio_venta: Precio de venta del producto
        precio_compra: Precio de compra del producto
        
    Returns:
        float: Ganancia unitaria, o None si no se puede calcular
    """
    if precio_compra:
        return precio_venta - precio_compra
    return None


def get_categorias_cached() -> List[Dict[str, Any]]:
    """
    Obtiene categorías desde caché o base de datos
    
    Returns:
        List[Dict]: Lista de categorías con sus datos
    """
    categorias = cache.get('categorias_list')
    if categorias is None:
        categorias = list(
            Categoria.objects.all()
            .order_by('nombre')
            .values('id', 'nombre', 'color', 'descripcion')
        )
        cache.set('categorias_list', categorias, CACHE_TIMEOUT_LARGO)
        logger.debug(f'Categorías cacheadas: {len(categorias)} categorías')
    return categorias


def invalidar_cache_categorias() -> None:
    """
    Invalida el caché de categorías
    
    Returns:
        None
    """
    cache.delete('categorias_list')
    logger.debug('Cache de categorías invalidado')

