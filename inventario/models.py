from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
import os
import uuid

def upload_to_productos(instance, filename):
    """Función para organizar las imágenes por nombre de producto"""
    ext = filename.split('.')[-1]
    nombre_limpio = instance.nombre.lower().replace(' ', '_').replace('/', '_')
    nombre_limpio = ''.join(c for c in nombre_limpio if c.isalnum() or c in ('_', '-'))
    return f'productos/{nombre_limpio}.{ext}'

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Categoría")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    color = models.CharField(max_length=7, default='#667eea', help_text="Color en formato hexadecimal (ej: #667eea)")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Producto")
    sku = models.CharField(
        max_length=50, 
        unique=True, 
        blank=True, 
        null=True,
        verbose_name="SKU/Código de Barras",
        help_text="Código único del producto (opcional)"
    )
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    categoria = models.ForeignKey(
        Categoria, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Categoría"
    )
    precio = models.DecimalField(
        max_digits=10, 
        decimal_places=0, 
        validators=[MinValueValidator(0)],
        verbose_name="Precio Unidad"
    )
    precio_promo = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        blank=True,
        null=True,
        verbose_name="Precio Promo",
        help_text="Precio promocional (opcional)"
    )
    stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Stock"
    )
    stock_minimo = models.IntegerField(
        default=10,
        validators=[MinValueValidator(0)],
        verbose_name="Stock Mínimo",
        help_text="Alerta cuando el stock esté por debajo de este valor"
    )
    imagen = models.ImageField(
        upload_to=upload_to_productos,
        blank=True,
        null=True,
        verbose_name="Imagen del Producto",
        help_text="Sube una imagen del producto (opcional)"
    )
    activo = models.BooleanField(default=True, verbose_name="Activo", help_text="Producto visible en el catálogo")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} - ${self.precio:,}"

    def save(self, *args, **kwargs):
        # Generar SKU automático si no se proporciona
        if not self.sku:
            # Generar SKU basado en nombre y UUID corto
            nombre_base = self.nombre[:10].upper().replace(' ', '').replace('/', '')
            self.sku = f"{nombre_base}-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def stock_bajo(self):
        """Indica si el stock está por debajo del mínimo"""
        return self.stock <= self.stock_minimo

    @property
    def valor_inventario(self):
        """Calcula el valor total del inventario de este producto"""
        return self.precio * self.stock

class HistorialCambio(models.Model):
    TIPO_CAMBIO = [
        ('crear', 'Creación'),
        ('editar', 'Edición'),
        ('eliminar', 'Eliminación'),
        ('stock', 'Cambio de Stock'),
    ]
    
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='historial')
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    tipo_cambio = models.CharField(max_length=20, choices=TIPO_CAMBIO)
    campo_modificado = models.CharField(max_length=100, blank=True, null=True)
    valor_anterior = models.TextField(blank=True, null=True)
    valor_nuevo = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Historial de Cambio"
        verbose_name_plural = "Historial de Cambios"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.tipo_cambio} - {self.producto.nombre} - {self.fecha}"

def upload_to_facturas(instance, filename):
    """Función para organizar las facturas por fecha"""
    ext = filename.split('.')[-1]
    fecha_str = instance.fecha_emision.strftime('%Y-%m-%d') if instance.fecha_emision else 'sin-fecha'
    nombre_limpio = f"{fecha_str}_{str(uuid.uuid4())[:8]}.{ext}"
    return f'facturas/{nombre_limpio}'

class Proveedor(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Proveedor")
    rut = models.CharField(max_length=20, blank=True, null=True, verbose_name="RUT")
    contacto = models.CharField(max_length=200, blank=True, null=True, verbose_name="Contacto")
    telefono = models.CharField(max_length=50, blank=True, null=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    direccion = models.TextField(blank=True, null=True, verbose_name="Dirección")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Factura(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('procesada', 'Procesada'),
        ('rechazada', 'Rechazada'),
    ]
    
    numero_factura = models.CharField(max_length=100, blank=True, null=True, verbose_name="Número de Factura")
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Proveedor")
    archivo = models.FileField(upload_to=upload_to_facturas, verbose_name="Archivo de Factura")
    fecha_emision = models.DateField(blank=True, null=True, verbose_name="Fecha de Emisión")
    fecha_subida = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Subida")
    total = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Total")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name="Estado")
    texto_extraido = models.TextField(blank=True, null=True, verbose_name="Texto Extraído (OCR)")
    procesado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Procesado por")
    notas = models.TextField(blank=True, null=True, verbose_name="Notas")

    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"Factura {self.numero_factura or 'N/A'} - {self.fecha_emision or 'Sin fecha'}"

class ItemFactura(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='items', verbose_name="Factura")
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Producto")
    nombre_producto = models.CharField(max_length=200, verbose_name="Nombre del Producto (texto extraído)")
    cantidad = models.IntegerField(default=1, validators=[MinValueValidator(1)], verbose_name="Cantidad")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Precio Unitario")
    subtotal = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Subtotal")
    producto_coincidencia = models.BooleanField(default=False, verbose_name="Producto Coincidió Automáticamente")
    stock_actualizado = models.BooleanField(default=False, verbose_name="Stock Actualizado")

    class Meta:
        verbose_name = "Item de Factura"
        verbose_name_plural = "Items de Factura"
        ordering = ['id']

    def __str__(self):
        return f"{self.nombre_producto} - {self.cantidad} x ${self.precio_unitario}"

    def save(self, *args, **kwargs):
        # Calcular subtotal automáticamente
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
