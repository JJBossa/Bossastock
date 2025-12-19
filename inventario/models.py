from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image
import os
import uuid
import logging

logger = logging.getLogger('inventario')

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
    precio_compra = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        blank=True,
        null=True,
        verbose_name="Precio de Compra",
        help_text="Precio al que se compró el producto (para calcular margen)"
    )
    precio = models.DecimalField(
        max_digits=10, 
        decimal_places=0, 
        validators=[MinValueValidator(0)],
        verbose_name="Precio de Venta"
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
        # Guardar stock anterior para detectar cambios
        stock_anterior = None
        if self.pk:
            try:
                stock_anterior = Producto.objects.get(pk=self.pk).stock
            except Producto.DoesNotExist:
                pass
        
        # Generar SKU automático si no se proporciona
        if not self.sku:
            # Generar SKU basado en nombre y UUID corto
            nombre_base = self.nombre[:10].upper().replace(' ', '').replace('/', '')
            self.sku = f"{nombre_base}-{str(uuid.uuid4())[:8].upper()}"
        
        # Guardar primero
        super().save(*args, **kwargs)
        
        # Optimizar imagen después de guardar
        self.optimizar_imagen()
        
        # Verificar si el stock bajó por debajo del mínimo y crear notificación
        if stock_anterior is not None and self.stock <= self.stock_minimo and stock_anterior > self.stock_minimo:
            # Solo crear notificación si el stock acaba de bajar por debajo del mínimo
            NotificacionStock.objects.create(
                producto=self,
                stock_anterior=stock_anterior,
                stock_actual=self.stock
            )
            logger.info(f'Notificación de stock bajo creada para {self.nombre} (Stock: {self.stock})')
    
    def optimizar_imagen(self):
        """Optimiza la imagen del producto: redimensiona y comprime"""
        if self.imagen:
            try:
                from django.conf import settings
                img_path = os.path.join(settings.MEDIA_ROOT, self.imagen.name)
                
                if os.path.exists(img_path):
                    img = Image.open(img_path)
                    
                    # Convertir a RGB si es necesario (para JPEG)
                    if img.mode in ('RGBA', 'LA', 'P'):
                        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        if img.mode in ('RGBA', 'LA'):
                            rgb_img.paste(img, mask=img.split()[-1])
                        else:
                            rgb_img.paste(img)
                        img = rgb_img
                    
                    # Redimensionar si es muy grande (máximo 800px de ancho o alto)
                    max_size = 800
                    if img.width > max_size or img.height > max_size:
                        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                    
                    # Guardar optimizada (calidad 85 para balance tamaño/calidad)
                    img.save(img_path, 'JPEG', quality=85, optimize=True)
            except Exception as e:
                # Si hay error en la optimización, no romper el guardado
                print(f"Error al optimizar imagen: {e}")
                pass

    @property
    def stock_bajo(self):
        """Indica si el stock está por debajo del mínimo"""
        return self.stock <= self.stock_minimo

    @property
    def valor_inventario(self):
        """Calcula el valor total del inventario de este producto"""
        return self.precio * self.stock
    
    @property
    def margen_ganancia(self):
        """Calcula el margen de ganancia en porcentaje"""
        if self.precio_compra and self.precio_compra > 0:
            return ((self.precio - self.precio_compra) / self.precio_compra) * 100
        return None
    
    @property
    def ganancia_unitaria(self):
        """Calcula la ganancia por unidad"""
        if self.precio_compra:
            return self.precio - self.precio_compra
        return None

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

class MovimientoStock(models.Model):
    TIPO_MOVIMIENTO = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
        ('perdida', 'Pérdida'),
        ('devolucion', 'Devolución'),
    ]
    
    MOTIVO_CHOICES = [
        ('compra', 'Compra a Proveedor'),
        ('venta', 'Venta'),
        ('ajuste_inventario', 'Ajuste de Inventario'),
        ('perdida', 'Pérdida/Rotura'),
        ('devolucion_cliente', 'Devolución de Cliente'),
        ('devolucion_proveedor', 'Devolución a Proveedor'),
        ('transferencia', 'Transferencia'),
        ('otro', 'Otro'),
    ]
    
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField(max_length=20, choices=TIPO_MOVIMIENTO, verbose_name="Tipo de Movimiento")
    cantidad = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Cantidad")
    motivo = models.CharField(max_length=50, choices=MOTIVO_CHOICES, verbose_name="Motivo")
    stock_anterior = models.IntegerField(verbose_name="Stock Anterior")
    stock_nuevo = models.IntegerField(verbose_name="Stock Nuevo")
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Usuario")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")
    notas = models.TextField(blank=True, null=True, verbose_name="Notas")
    factura = models.ForeignKey('Factura', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Factura Relacionada")

    class Meta:
        verbose_name = "Movimiento de Stock"
        verbose_name_plural = "Movimientos de Stock"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.producto.nombre} - {self.cantidad} unidades - {self.fecha}"

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

class ProductoFavorito(models.Model):
    """Modelo para productos favoritos de usuarios"""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='productos_favoritos')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='usuarios_favoritos')
    fecha_agregado = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Agregado")

    class Meta:
        verbose_name = "Producto Favorito"
        verbose_name_plural = "Productos Favoritos"
        unique_together = ['usuario', 'producto']  # Un usuario solo puede tener un producto como favorito una vez
        ordering = ['-fecha_agregado']

    def __str__(self):
        return f"{self.usuario.username} - {self.producto.nombre}"

class Venta(models.Model):
    """Modelo para registrar ventas del punto de venta"""
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
        ('mixto', 'Mixto'),
    ]
    
    numero_venta = models.CharField(max_length=50, unique=True, verbose_name="Número de Venta")
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Vendedor")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Venta")
    subtotal = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Subtotal")
    descuento = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Descuento")
    total = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Total")
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, default='efectivo', verbose_name="Método de Pago")
    monto_recibido = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Monto Recibido")
    cambio = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Cambio")
    notas = models.TextField(blank=True, null=True, verbose_name="Notas")
    cancelada = models.BooleanField(default=False, verbose_name="Venta Cancelada")

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ['-fecha']

    def __str__(self):
        return f"Venta #{self.numero_venta} - ${self.total:,.0f} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"
    
    def save(self, *args, **kwargs):
        if not self.numero_venta:
            # Generar número de venta único
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            self.numero_venta = f"V-{timestamp}"
        super().save(*args, **kwargs)

class ItemVenta(models.Model):
    """Items de una venta"""
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='items', verbose_name="Venta")
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, verbose_name="Producto")
    nombre_producto = models.CharField(max_length=200, verbose_name="Nombre del Producto")
    cantidad = models.IntegerField(default=1, validators=[MinValueValidator(1)], verbose_name="Cantidad")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Precio Unitario")
    subtotal = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Subtotal")
    stock_anterior = models.IntegerField(default=0, verbose_name="Stock Anterior")
    stock_despues = models.IntegerField(default=0, verbose_name="Stock Después")

    class Meta:
        verbose_name = "Item de Venta"
        verbose_name_plural = "Items de Venta"
        ordering = ['id']

    def __str__(self):
        return f"{self.nombre_producto} - {self.cantidad} x ${self.precio_unitario}"

    def save(self, *args, **kwargs):
        # Calcular subtotal automáticamente
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

class Cotizacion(models.Model):
    """Modelo para cotizaciones a clientes"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('vencida', 'Vencida'),
    ]
    
    numero_cotizacion = models.CharField(max_length=50, unique=True, verbose_name="Número de Cotización")
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Vendedor")
    cliente_nombre = models.CharField(max_length=200, verbose_name="Nombre del Cliente")
    cliente_contacto = models.CharField(max_length=200, blank=True, null=True, verbose_name="Contacto")
    cliente_telefono = models.CharField(max_length=50, blank=True, null=True, verbose_name="Teléfono")
    cliente_email = models.EmailField(blank=True, null=True, verbose_name="Email")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_vencimiento = models.DateField(verbose_name="Fecha de Vencimiento")
    subtotal = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Subtotal")
    descuento = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Descuento")
    total = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Total")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name="Estado")
    notas = models.TextField(blank=True, null=True, verbose_name="Notas")
    convertida_en_venta = models.ForeignKey('Venta', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Convertida en Venta")

    class Meta:
        verbose_name = "Cotización"
        verbose_name_plural = "Cotizaciones"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Cotización #{self.numero_cotizacion} - {self.cliente_nombre} - ${self.total:,.0f}"
    
    def save(self, *args, **kwargs):
        if not self.numero_cotizacion:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            self.numero_cotizacion = f"COT-{timestamp}"
        super().save(*args, **kwargs)
    
    @property
    def esta_vencida(self):
        from django.utils import timezone
        return timezone.now().date() > self.fecha_vencimiento and self.estado == 'pendiente'

class ItemCotizacion(models.Model):
    """Items de una cotización"""
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='items', verbose_name="Cotización")
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, verbose_name="Producto")
    nombre_producto = models.CharField(max_length=200, verbose_name="Nombre del Producto")
    cantidad = models.IntegerField(default=1, validators=[MinValueValidator(1)], verbose_name="Cantidad")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Precio Unitario")
    subtotal = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Subtotal")

    class Meta:
        verbose_name = "Item de Cotización"
        verbose_name_plural = "Items de Cotización"
        ordering = ['id']

    def __str__(self):
        return f"{self.nombre_producto} - {self.cantidad} x ${self.precio_unitario}"

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)


class NotificacionStock(models.Model):
    """Modelo para notificaciones de stock bajo"""
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='notificaciones_stock', verbose_name="Producto")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")
    vista = models.BooleanField(default=False, verbose_name="Vista")
    notificada = models.BooleanField(default=False, verbose_name="Notificada")
    stock_anterior = models.IntegerField(verbose_name="Stock Anterior")
    stock_actual = models.IntegerField(verbose_name="Stock Actual")
    
    class Meta:
        verbose_name = "Notificación de Stock"
        verbose_name_plural = "Notificaciones de Stock"
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['-fecha', 'vista']),
        ]
    
    def __str__(self):
        return f"Stock bajo: {self.producto.nombre} - {self.stock_actual} unidades"