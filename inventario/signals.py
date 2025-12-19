"""
Señales para capturar cambios automáticamente
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Producto, HistorialPrecio
import logging

logger = logging.getLogger('inventario')


@receiver(pre_save, sender=Producto)
def capturar_precios_anteriores(sender, instance, **kwargs):
    """Captura los precios anteriores antes de guardar"""
    if instance.pk:
        try:
            producto_anterior = Producto.objects.get(pk=instance.pk)
            instance._precio_anterior = producto_anterior.precio
            instance._precio_compra_anterior = producto_anterior.precio_compra
            instance._precio_promo_anterior = producto_anterior.precio_promo
        except Producto.DoesNotExist:
            instance._precio_anterior = None
            instance._precio_compra_anterior = None
            instance._precio_promo_anterior = None
    else:
        instance._precio_anterior = None
        instance._precio_compra_anterior = None
        instance._precio_promo_anterior = None


@receiver(post_save, sender=Producto)
def registrar_cambio_precio(sender, instance, created, **kwargs):
    """Registra cambios de precio en el historial"""
    if created:
        # Si es un producto nuevo, registrar precio inicial
        HistorialPrecio.objects.create(
            producto=instance,
            precio_anterior=0,
            precio_nuevo=instance.precio,
            precio_compra_anterior=None,
            precio_compra_nuevo=instance.precio_compra,
            precio_promo_anterior=None,
            precio_promo_nuevo=instance.precio_promo,
            motivo='Precio inicial',
            notas='Producto creado'
        )
    else:
        # Verificar si hubo cambios en los precios
        precio_cambio = False
        precio_compra_cambio = False
        precio_promo_cambio = False
        
        if hasattr(instance, '_precio_anterior'):
            if instance._precio_anterior is not None and instance._precio_anterior != instance.precio:
                precio_cambio = True
            if instance._precio_compra_anterior is not None and instance._precio_compra_anterior != (instance.precio_compra or 0):
                precio_compra_cambio = True
            if instance._precio_promo_anterior != instance.precio_promo:
                precio_promo_cambio = True
        
        if precio_cambio or precio_compra_cambio or precio_promo_cambio:
            # Obtener usuario del request si está disponible
            usuario = None
            if hasattr(instance, '_request_user'):
                usuario = instance._request_user
            
            HistorialPrecio.objects.create(
                producto=instance,
                precio_anterior=instance._precio_anterior or 0,
                precio_nuevo=instance.precio,
                precio_compra_anterior=instance._precio_compra_anterior,
                precio_compra_nuevo=instance.precio_compra,
                precio_promo_anterior=instance._precio_promo_anterior,
                precio_promo_nuevo=instance.precio_promo,
                usuario=usuario,
                motivo='Cambio de precio',
                notas=f'Precio actualizado: {"Venta" if precio_cambio else ""} {"Compra" if precio_compra_cambio else ""} {"Promo" if precio_promo_cambio else ""}'.strip()
            )
            logger.info(f'Historial de precio registrado para {instance.nombre}')

