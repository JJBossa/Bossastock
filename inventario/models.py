from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum
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
        ('credito', 'Crédito'),
        ('mixto', 'Mixto'),
    ]
    
    numero_venta = models.CharField(max_length=50, unique=True, verbose_name="Número de Venta")
    cliente = models.ForeignKey('Cliente', on_delete=models.SET_NULL, null=True, blank=True, related_name='ventas', verbose_name="Cliente")
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Vendedor")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Venta")
    subtotal = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Subtotal")
    descuento = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Descuento")
    total = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Total")
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, default='efectivo', verbose_name="Método de Pago")
    monto_recibido = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Monto Recibido")
    cambio = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Cambio")
    es_credito = models.BooleanField(default=False, verbose_name="Venta a Crédito", help_text="Si es crédito, se creará una cuenta por cobrar")
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
    cliente = models.ForeignKey('Cliente', on_delete=models.SET_NULL, null=True, blank=True, related_name='cotizaciones', verbose_name="Cliente")
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Vendedor")
    # Mantener campos legacy para compatibilidad
    cliente_nombre = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nombre del Cliente (Legacy)")
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


class Cliente(models.Model):
    """Modelo para gestionar clientes"""
    TIPO_CLIENTE_CHOICES = [
        ('natural', 'Persona Natural'),
        ('empresa', 'Empresa'),
    ]
    
    nombre = models.CharField(max_length=200, verbose_name="Nombre o Razón Social")
    rut = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="RUT", help_text="RUT del cliente (opcional)")
    tipo_cliente = models.CharField(max_length=20, choices=TIPO_CLIENTE_CHOICES, default='natural', verbose_name="Tipo de Cliente")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    telefono = models.CharField(max_length=50, blank=True, null=True, verbose_name="Teléfono")
    direccion = models.TextField(blank=True, null=True, verbose_name="Dirección")
    contacto = models.CharField(max_length=200, blank=True, null=True, verbose_name="Persona de Contacto")
    limite_credito = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        default=0, 
        verbose_name="Límite de Crédito",
        help_text="Monto máximo de crédito permitido (0 = sin límite)"
    )
    activo = models.BooleanField(default=True, verbose_name="Activo", help_text="Cliente activo en el sistema")
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")
    notas = models.TextField(blank=True, null=True, verbose_name="Notas")
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['nombre']),
            models.Index(fields=['rut']),
            models.Index(fields=['activo']),
        ]
    
    def __str__(self):
        return f"{self.nombre} ({self.rut or 'Sin RUT'})"
    
    @property
    def total_compras(self):
        """Calcula el total de compras del cliente"""
        from django.db.models import Sum
        total = Venta.objects.filter(
            cliente=self,
            cancelada=False
        ).aggregate(Sum('total'))['total__sum'] or 0
        return total
    
    @property
    def cantidad_ventas(self):
        """Cuenta la cantidad de ventas del cliente"""
        return Venta.objects.filter(cliente=self, cancelada=False).count()
    
    @property
    def saldo_pendiente(self):
        """Calcula el saldo pendiente de cuentas por cobrar"""
        from django.db.models import Sum
        total = CuentaPorCobrar.objects.filter(
            cliente=self,
            estado__in=['pendiente', 'parcial']
        ).aggregate(
            saldo=Sum('monto_total') - Sum('monto_pagado')
        )['saldo'] or 0
        return max(0, total)


class CuentaPorCobrar(models.Model):
    """Modelo para gestionar cuentas por cobrar (créditos a clientes)"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('parcial', 'Pago Parcial'),
        ('pagado', 'Pagado'),
        ('vencido', 'Vencido'),
        ('cancelado', 'Cancelado'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='cuentas_por_cobrar', verbose_name="Cliente")
    venta = models.ForeignKey(Venta, on_delete=models.SET_NULL, null=True, blank=True, related_name='cuenta_por_cobrar', verbose_name="Venta Relacionada")
    numero_documento = models.CharField(max_length=50, unique=True, verbose_name="Número de Documento")
    monto_total = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Monto Total")
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Monto Pagado")
    fecha_emision = models.DateField(verbose_name="Fecha de Emisión")
    fecha_vencimiento = models.DateField(verbose_name="Fecha de Vencimiento")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name="Estado")
    notas = models.TextField(blank=True, null=True, verbose_name="Notas")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    
    class Meta:
        verbose_name = "Cuenta por Cobrar"
        verbose_name_plural = "Cuentas por Cobrar"
        ordering = ['-fecha_emision']
        indexes = [
            models.Index(fields=['cliente', 'estado']),
            models.Index(fields=['fecha_vencimiento']),
            models.Index(fields=['estado', 'fecha_vencimiento']),
        ]
    
    def __str__(self):
        return f"{self.numero_documento} - {self.cliente.nombre} - ${self.monto_total:,.0f}"
    
    @property
    def saldo_pendiente(self):
        """Calcula el saldo pendiente"""
        return max(0, self.monto_total - self.monto_pagado)
    
    @property
    def esta_vencida(self):
        """Verifica si la cuenta está vencida"""
        from django.utils import timezone
        return timezone.now().date() > self.fecha_vencimiento and self.estado in ['pendiente', 'parcial']
    
    def save(self, *args, **kwargs):
        """Actualiza el estado según el monto pagado"""
        if not self.numero_documento:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            self.numero_documento = f"CC-{timestamp}"
        
        # Actualizar estado según pagos
        if self.monto_pagado >= self.monto_total:
            self.estado = 'pagado'
        elif self.monto_pagado > 0:
            self.estado = 'parcial'
        elif self.estado == 'pagado' and self.monto_pagado < self.monto_total:
            self.estado = 'pendiente'
        
        super().save(*args, **kwargs)


class PagoCliente(models.Model):
    """Modelo para registrar pagos de clientes"""
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('cheque', 'Cheque'),
        ('tarjeta', 'Tarjeta'),
        ('otro', 'Otro'),
    ]
    
    cuenta_por_cobrar = models.ForeignKey(CuentaPorCobrar, on_delete=models.CASCADE, related_name='pagos', verbose_name="Cuenta por Cobrar")
    monto = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Monto")
    fecha_pago = models.DateField(verbose_name="Fecha de Pago")
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, default='efectivo', verbose_name="Método de Pago")
    referencia = models.CharField(max_length=200, blank=True, null=True, verbose_name="Referencia", help_text="Número de cheque, transferencia, etc.")
    notas = models.TextField(blank=True, null=True, verbose_name="Notas")
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Registrado por")
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")
    
    class Meta:
        verbose_name = "Pago de Cliente"
        verbose_name_plural = "Pagos de Clientes"
        ordering = ['-fecha_pago']
        indexes = [
            models.Index(fields=['cuenta_por_cobrar', 'fecha_pago']),
        ]
    
    def __str__(self):
        return f"Pago ${self.monto:,.0f} - {self.cuenta_por_cobrar.cliente.nombre} - {self.fecha_pago}"
    
    def save(self, *args, **kwargs):
        """Actualiza el monto pagado de la cuenta por cobrar"""
        super().save(*args, **kwargs)
        # Actualizar monto pagado de la cuenta
        cuenta = self.cuenta_por_cobrar
        from django.db.models import Sum
        cuenta.monto_pagado = cuenta.pagos.aggregate(
            total=Sum('monto')
        )['total'] or 0
        cuenta.save()


class Almacen(models.Model):
    """Modelo para gestionar múltiples almacenes/sucursales"""
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Almacén")
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código", help_text="Código único del almacén")
    direccion = models.TextField(blank=True, null=True, verbose_name="Dirección")
    telefono = models.CharField(max_length=50, blank=True, null=True, verbose_name="Teléfono")
    responsable = models.CharField(max_length=200, blank=True, null=True, verbose_name="Responsable")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    notas = models.TextField(blank=True, null=True, verbose_name="Notas")
    
    class Meta:
        verbose_name = "Almacén"
        verbose_name_plural = "Almacenes"
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['activo']),
        ]
    
    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class StockAlmacen(models.Model):
    """Modelo para gestionar stock por almacén"""
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='stock_almacenes', verbose_name="Producto")
    almacen = models.ForeignKey(Almacen, on_delete=models.CASCADE, related_name='stock_productos', verbose_name="Almacén")
    cantidad = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Cantidad")
    stock_minimo = models.IntegerField(default=10, validators=[MinValueValidator(0)], verbose_name="Stock Mínimo")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")
    
    class Meta:
        verbose_name = "Stock por Almacén"
        verbose_name_plural = "Stocks por Almacén"
        unique_together = ['producto', 'almacen']
        indexes = [
            models.Index(fields=['almacen', 'producto']),
            models.Index(fields=['cantidad']),
        ]
    
    def __str__(self):
        return f"{self.producto.nombre} - {self.almacen.nombre}: {self.cantidad}"
    
    @property
    def stock_bajo(self):
        """Indica si el stock está por debajo del mínimo"""
        return self.cantidad <= self.stock_minimo


class Transferencia(models.Model):
    """Modelo para transferencias entre almacenes"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_transito', 'En Tránsito'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]
    
    numero_transferencia = models.CharField(max_length=50, unique=True, verbose_name="Número de Transferencia")
    almacen_origen = models.ForeignKey(Almacen, on_delete=models.CASCADE, related_name='transferencias_salida', verbose_name="Almacén Origen")
    almacen_destino = models.ForeignKey(Almacen, on_delete=models.CASCADE, related_name='transferencias_entrada', verbose_name="Almacén Destino")
    fecha_solicitud = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Solicitud")
    fecha_transferencia = models.DateTimeField(blank=True, null=True, verbose_name="Fecha de Transferencia")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name="Estado")
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Usuario")
    notas = models.TextField(blank=True, null=True, verbose_name="Notas")
    
    class Meta:
        verbose_name = "Transferencia"
        verbose_name_plural = "Transferencias"
        ordering = ['-fecha_solicitud']
        indexes = [
            models.Index(fields=['almacen_origen', 'estado']),
            models.Index(fields=['almacen_destino', 'estado']),
        ]
    
    def __str__(self):
        return f"Transferencia #{self.numero_transferencia} - {self.almacen_origen} → {self.almacen_destino}"
    
    def save(self, *args, **kwargs):
        if not self.numero_transferencia:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            self.numero_transferencia = f"TRF-{timestamp}"
        super().save(*args, **kwargs)


class ItemTransferencia(models.Model):
    """Items de una transferencia"""
    transferencia = models.ForeignKey(Transferencia, on_delete=models.CASCADE, related_name='items', verbose_name="Transferencia")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, verbose_name="Producto")
    cantidad = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Cantidad")
    cantidad_enviada = models.IntegerField(default=0, verbose_name="Cantidad Enviada")
    cantidad_recibida = models.IntegerField(default=0, verbose_name="Cantidad Recibida")
    
    class Meta:
        verbose_name = "Item de Transferencia"
        verbose_name_plural = "Items de Transferencia"
    
    def __str__(self):
        return f"{self.producto.nombre} - {self.cantidad} unidades"


class OrdenCompra(models.Model):
    """Modelo para órdenes de compra a proveedores"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('parcial', 'Parcialmente Recibida'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]
    
    numero_orden = models.CharField(max_length=50, unique=True, verbose_name="Número de Orden")
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='ordenes_compra', verbose_name="Proveedor")
    fecha_orden = models.DateField(verbose_name="Fecha de Orden")
    fecha_esperada = models.DateField(verbose_name="Fecha Esperada de Recepción")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name="Estado")
    subtotal = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Subtotal")
    descuento = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Descuento")
    total = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Total")
    notas = models.TextField(blank=True, null=True, verbose_name="Notas")
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Creado por")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    
    class Meta:
        verbose_name = "Orden de Compra"
        verbose_name_plural = "Órdenes de Compra"
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['proveedor', 'estado']),
            models.Index(fields=['fecha_orden']),
        ]
    
    def __str__(self):
        return f"OC #{self.numero_orden} - {self.proveedor.nombre} - ${self.total:,.0f}"
    
    def save(self, *args, **kwargs):
        if not self.numero_orden:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            self.numero_orden = f"OC-{timestamp}"
        super().save(*args, **kwargs)


class ItemOrdenCompra(models.Model):
    """Items de una orden de compra"""
    orden = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE, related_name='items', verbose_name="Orden de Compra")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, verbose_name="Producto")
    cantidad = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Cantidad Solicitada")
    cantidad_recibida = models.IntegerField(default=0, verbose_name="Cantidad Recibida")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Precio Unitario")
    subtotal = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Subtotal")
    
    class Meta:
        verbose_name = "Item de Orden de Compra"
        verbose_name_plural = "Items de Orden de Compra"
    
    def __str__(self):
        return f"{self.producto.nombre} - {self.cantidad} x ${self.precio_unitario}"
    
    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)


class RecepcionMercancia(models.Model):
    """Modelo para recepción de mercancía de órdenes de compra"""
    orden_compra = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE, related_name='recepciones', verbose_name="Orden de Compra")
    almacen = models.ForeignKey(Almacen, on_delete=models.CASCADE, verbose_name="Almacén de Recepción")
    fecha_recepcion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Recepción")
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Recibido por")
    notas = models.TextField(blank=True, null=True, verbose_name="Notas")
    
    class Meta:
        verbose_name = "Recepción de Mercancía"
        verbose_name_plural = "Recepciones de Mercancía"
        ordering = ['-fecha_recepcion']
    
    def __str__(self):
        return f"Recepción OC #{self.orden_compra.numero_orden} - {self.fecha_recepcion.strftime('%d/%m/%Y')}"

# ========== MODELOS PARA MEJORAS ==========

class HistorialBusqueda(models.Model):
    """Modelo para guardar el historial de búsquedas del usuario"""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='busquedas')
    query = models.CharField(max_length=255, verbose_name="Búsqueda")
    tipo = models.CharField(
        max_length=20,
        choices=[
            ('producto', 'Producto'),
            ('cliente', 'Cliente'),
            ('venta', 'Venta'),
            ('cotizacion', 'Cotización'),
            ('global', 'Búsqueda Global'),
        ],
        default='global',
        verbose_name="Tipo"
    )
    resultados = models.IntegerField(default=0, verbose_name="Cantidad de Resultados")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")
    
    class Meta:
        verbose_name = "Historial de Búsqueda"
        verbose_name_plural = "Historial de Búsquedas"
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['usuario', '-fecha']),
            models.Index(fields=['query']),
        ]
    
    def __str__(self):
        return f"{self.usuario.username} - {self.query} - {self.fecha}"

class LogAccion(models.Model):
    """Modelo para logs detallados de acciones del usuario"""
    TIPO_ACCION = [
        ('crear', 'Crear'),
        ('editar', 'Editar'),
        ('eliminar', 'Eliminar'),
        ('ver', 'Ver'),
        ('exportar', 'Exportar'),
        ('imprimir', 'Imprimir'),
        ('login', 'Iniciar Sesión'),
        ('logout', 'Cerrar Sesión'),
        ('buscar', 'Buscar'),
        ('otro', 'Otro'),
    ]
    
    MODULO_CHOICES = [
        ('producto', 'Producto'),
        ('cliente', 'Cliente'),
        ('venta', 'Venta'),
        ('cotizacion', 'Cotización'),
        ('factura', 'Factura'),
        ('proveedor', 'Proveedor'),
        ('almacen', 'Almacén'),
        ('compra', 'Compra'),
        ('usuario', 'Usuario'),
        ('sistema', 'Sistema'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='acciones')
    tipo_accion = models.CharField(max_length=20, choices=TIPO_ACCION, verbose_name="Tipo de Acción")
    modulo = models.CharField(max_length=20, choices=MODULO_CHOICES, verbose_name="Módulo")
    objeto_id = models.IntegerField(null=True, blank=True, verbose_name="ID del Objeto")
    objeto_tipo = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tipo de Objeto")
    descripcion = models.TextField(verbose_name="Descripción")
    datos_anteriores = models.JSONField(null=True, blank=True, verbose_name="Datos Anteriores")
    datos_nuevos = models.JSONField(null=True, blank=True, verbose_name="Datos Nuevos")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Dirección IP")
    user_agent = models.TextField(blank=True, null=True, verbose_name="User Agent")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")
    
    class Meta:
        verbose_name = "Log de Acción"
        verbose_name_plural = "Logs de Acciones"
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['usuario', '-fecha']),
            models.Index(fields=['modulo', 'tipo_accion']),
            models.Index(fields=['-fecha']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_accion_display()} - {self.get_modulo_display()} - {self.usuario} - {self.fecha}"

class NotificacionUsuario(models.Model):
    """Modelo para notificaciones del usuario"""
    TIPO_NOTIFICACION = [
        ('stock_bajo', 'Stock Bajo'),
        ('cuenta_vencida', 'Cuenta Vencida'),
        ('orden_pendiente', 'Orden Pendiente'),
        ('sistema', 'Sistema'),
        ('info', 'Información'),
        ('warning', 'Advertencia'),
        ('error', 'Error'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones')
    tipo = models.CharField(max_length=20, choices=TIPO_NOTIFICACION, verbose_name="Tipo")
    titulo = models.CharField(max_length=200, verbose_name="Título")
    mensaje = models.TextField(verbose_name="Mensaje")
    leida = models.BooleanField(default=False, verbose_name="Leída")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")
    url_relacionada = models.CharField(max_length=500, blank=True, null=True, verbose_name="URL Relacionada")
    datos_adicionales = models.JSONField(null=True, blank=True, verbose_name="Datos Adicionales")
    
    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-fecha', 'leida']
        indexes = [
            models.Index(fields=['usuario', 'leida', '-fecha']),
        ]
    
    def __str__(self):
        return f"{self.titulo} - {self.usuario.username} - {self.fecha}"