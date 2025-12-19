"""
Utilidades compartidas para la aplicación inventario
"""
import unicodedata
import logging
from django.db import transaction
from django.core.cache import cache
from .models import HistorialCambio

# Logger
logger = logging.getLogger('inventario')


def es_admin_bossa(user):
    """
    Verifica si el usuario es el admin bossa
    
    Args:
        user: Usuario de Django
        
    Returns:
        bool: True si es el admin bossa, False en caso contrario
    """
    return user.is_authenticated and user.username == 'bossa'


def normalizar_texto(texto):
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
def registrar_cambio(producto, usuario, tipo_cambio, campo_modificado=None, 
                     valor_anterior=None, valor_nuevo=None, descripcion=None):
    """
    Registra un cambio en el historial de un producto
    
    Args:
        producto: Instancia del modelo Producto
        usuario: Usuario que realizó el cambio
        tipo_cambio: Tipo de cambio ('crear', 'editar', 'eliminar', 'stock')
        campo_modificado: Nombre del campo modificado (opcional)
        valor_anterior: Valor anterior del campo (opcional)
        valor_nuevo: Valor nuevo del campo (opcional)
        descripcion: Descripción adicional del cambio (opcional)
    """
    HistorialCambio.objects.create(
        producto=producto,
        usuario=usuario,
        tipo_cambio=tipo_cambio,
        campo_modificado=campo_modificado,
        valor_anterior=str(valor_anterior) if valor_anterior is not None else None,
        valor_nuevo=str(valor_nuevo) if valor_nuevo is not None else None,
        descripcion=descripcion
    )


def calcular_margen_ganancia(precio_venta, precio_compra):
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


def calcular_ganancia_unitaria(precio_venta, precio_compra):
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


def get_categorias_cached():
    """
    Obtiene categorías desde caché o base de datos
    
    Returns:
        QuerySet: Categorías ordenadas por nombre
    """
    categorias = cache.get('categorias_list')
    if categorias is None:
        from .models import Categoria
        categorias = list(Categoria.objects.all().order_by('nombre').values('id', 'nombre', 'color', 'descripcion'))
        cache.set('categorias_list', categorias, 3600)  # Cache por 1 hora
    return categorias


def invalidar_cache_categorias():
    """Invalida el caché de categorías"""
    cache.delete('categorias_list')

