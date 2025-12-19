"""
Validadores personalizados para el sistema de inventario
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .constants import (
    PRECIO_MINIMO, PRECIO_MAXIMO,
    STOCK_MINIMO_DEFAULT, NOMBRE_PRODUCTO_MAX_LENGTH
)


def validate_precio_positivo(value):
    """Valida que el precio sea positivo"""
    if value < PRECIO_MINIMO:
        raise ValidationError(
            _('El precio debe ser mayor o igual a %(min)s'),
            params={'min': PRECIO_MINIMO},
        )
    if value > PRECIO_MAXIMO:
        raise ValidationError(
            _('El precio no puede ser mayor a %(max)s'),
            params={'max': PRECIO_MAXIMO},
        )


def validate_stock_positivo(value):
    """Valida que el stock sea positivo"""
    if value < 0:
        raise ValidationError(
            _('El stock no puede ser negativo'),
        )


def validate_nombre_producto(value):
    """Valida el nombre del producto"""
    if not value or len(value.strip()) == 0:
        raise ValidationError(
            _('El nombre del producto no puede estar vacío'),
        )
    if len(value) > NOMBRE_PRODUCTO_MAX_LENGTH:
        raise ValidationError(
            _('El nombre del producto no puede tener más de %(max)s caracteres'),
            params={'max': NOMBRE_PRODUCTO_MAX_LENGTH},
        )
    # Validar que no tenga solo espacios
    if value.strip() != value:
        raise ValidationError(
            _('El nombre del producto no puede comenzar o terminar con espacios'),
        )


def validate_precio_promo_menor_precio(precio_promo, precio):
    """Valida que el precio promocional sea menor al precio normal"""
    if precio_promo and precio and precio_promo >= precio:
        raise ValidationError(
            _('El precio promocional debe ser menor al precio de venta'),
        )


def validate_precio_compra_menor_precio(precio_compra, precio):
    """Valida que el precio de compra sea menor al precio de venta (opcional)"""
    if precio_compra and precio and precio_compra >= precio:
        raise ValidationError(
            _('El precio de compra debe ser menor al precio de venta para tener ganancia'),
        )


def validate_sku_unico(value, instance=None):
    """Valida que el SKU sea único (si se proporciona)"""
    from .models import Producto
    
    if not value:
        return  # SKU es opcional
    
    # Buscar productos con el mismo SKU, excluyendo el actual si es una actualización
    queryset = Producto.objects.filter(sku=value)
    if instance and instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    
    if queryset.exists():
        raise ValidationError(
            _('Ya existe un producto con el SKU "%(sku)s"'),
            params={'sku': value},
        )

