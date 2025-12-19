from django.contrib import admin
from django.utils.html import format_html
from .models import Producto, Categoria, HistorialCambio, Factura, ItemFactura, Proveedor, ProductoFavorito, MovimientoStock, Venta, ItemVenta, Cotizacion, ItemCotizacion, NotificacionStock

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'color_preview', 'producto_count', 'fecha_creacion')
    search_fields = ('nombre',)
    ordering = ('nombre',)
    
    def color_preview(self, obj):
        return format_html(
            '<div style="width: 30px; height: 30px; background-color: {}; border-radius: 5px;"></div>',
            obj.color
        )
    color_preview.short_description = "Color"
    
    def producto_count(self, obj):
        return obj.producto_set.count()
    producto_count.short_description = "Productos"

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'sku', 'categoria', 'precio_compra', 'precio', 'precio_promo', 'margen_display', 'stock', 'stock_bajo_indicator', 'fecha_actualizacion', 'imagen_preview')
    list_filter = ('categoria', 'activo', 'fecha_creacion', 'stock')
    search_fields = ('nombre', 'sku', 'descripcion')
    ordering = ('nombre',)
    readonly_fields = ('imagen_preview', 'fecha_creacion', 'fecha_actualizacion', 'sku', 'margen_display')
    fieldsets = (
        ('Información del Producto', {
            'fields': ('nombre', 'sku', 'descripcion', 'categoria', 'activo')
        }),
        ('Precio y Stock', {
            'fields': ('precio_compra', 'precio', 'precio_promo', 'margen_display', 'stock', 'stock_minimo')
        }),
        ('Imagen', {
            'fields': ('imagen', 'imagen_preview')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def imagen_preview(self, obj):
        if obj.imagen:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px; border-radius: 5px;" />',
                obj.imagen.url
            )
        return "Sin imagen"
    imagen_preview.short_description = "Vista Previa"
    
    def stock_bajo_indicator(self, obj):
        if obj.stock_bajo:
            return format_html('<span style="color: red;">⚠ Stock Bajo</span>')
        return "✓"
    stock_bajo_indicator.short_description = "Estado"
    
    def margen_display(self, obj):
        if obj.margen_ganancia is not None:
            color = 'green' if obj.margen_ganancia > 30 else 'orange' if obj.margen_ganancia > 10 else 'red'
            return format_html('<span style="color: {};"><strong>{:.1f}%</strong></span>', color, obj.margen_ganancia)
        return "-"
    margen_display.short_description = "Margen %"

@admin.register(HistorialCambio)
class HistorialCambioAdmin(admin.ModelAdmin):
    list_display = ('producto', 'tipo_cambio', 'usuario', 'fecha', 'campo_modificado')
    list_filter = ('tipo_cambio', 'fecha')
    search_fields = ('producto__nombre', 'usuario__username')
    readonly_fields = ('producto', 'usuario', 'tipo_cambio', 'campo_modificado', 'valor_anterior', 'valor_nuevo', 'fecha', 'descripcion')
    ordering = ('-fecha',)

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'telefono', 'email', 'fecha_creacion')
    search_fields = ('nombre', 'rut', 'email')
    ordering = ('nombre',)

class ItemFacturaInline(admin.TabularInline):
    model = ItemFactura
    extra = 0
    readonly_fields = ('subtotal', 'producto_coincidencia', 'stock_actualizado')
    fields = ('producto', 'nombre_producto', 'cantidad', 'precio_unitario', 'subtotal', 'producto_coincidencia', 'stock_actualizado')

@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ('numero_factura', 'proveedor', 'fecha_emision', 'total', 'estado', 'fecha_subida')
    list_filter = ('estado', 'fecha_emision', 'fecha_subida')
    search_fields = ('numero_factura', 'proveedor__nombre')
    readonly_fields = ('texto_extraido', 'fecha_subida', 'procesado_por')
    inlines = [ItemFacturaInline]
    ordering = ('-fecha_subida',)
    fieldsets = (
        ('Información de Factura', {
            'fields': ('numero_factura', 'proveedor', 'fecha_emision', 'total', 'estado')
        }),
        ('Archivo', {
            'fields': ('archivo',)
        }),
        ('Procesamiento', {
            'fields': ('texto_extraido', 'procesado_por', 'fecha_subida'),
            'classes': ('collapse',)
        }),
        ('Notas', {
            'fields': ('notas',)
        }),
    )

@admin.register(ItemFactura)
class ItemFacturaAdmin(admin.ModelAdmin):
    list_display = ('factura', 'producto', 'nombre_producto', 'cantidad', 'precio_unitario', 'subtotal', 'stock_actualizado')
    list_filter = ('stock_actualizado', 'producto_coincidencia')
    search_fields = ('nombre_producto', 'factura__numero_factura')
    readonly_fields = ('subtotal',)

@admin.register(ProductoFavorito)
class ProductoFavoritoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'producto', 'fecha_agregado')
    list_filter = ('fecha_agregado',)
    search_fields = ('usuario__username', 'producto__nombre')
    ordering = ('-fecha_agregado',)

@admin.register(MovimientoStock)
class MovimientoStockAdmin(admin.ModelAdmin):
    list_display = ('producto', 'tipo', 'cantidad', 'motivo', 'stock_anterior', 'stock_nuevo', 'usuario', 'fecha')
    list_filter = ('tipo', 'motivo', 'fecha')
    search_fields = ('producto__nombre', 'usuario__username', 'notas')
    readonly_fields = ('stock_anterior', 'stock_nuevo', 'fecha')
    ordering = ('-fecha',)
    date_hierarchy = 'fecha'

class ItemVentaInline(admin.TabularInline):
    model = ItemVenta
    extra = 0
    readonly_fields = ('subtotal', 'stock_anterior', 'stock_despues')
    fields = ('producto', 'nombre_producto', 'cantidad', 'precio_unitario', 'subtotal', 'stock_anterior', 'stock_despues')

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('numero_venta', 'fecha', 'usuario', 'total', 'metodo_pago', 'cancelada', 'items_count')
    list_filter = ('metodo_pago', 'cancelada', 'fecha')
    search_fields = ('numero_venta', 'usuario__username')
    readonly_fields = ('numero_venta', 'fecha', 'subtotal', 'total', 'cambio')
    inlines = [ItemVentaInline]
    ordering = ('-fecha',)
    date_hierarchy = 'fecha'
    
    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = "Items"

@admin.register(ItemVenta)
class ItemVentaAdmin(admin.ModelAdmin):
    list_display = ('venta', 'producto', 'nombre_producto', 'cantidad', 'precio_unitario', 'subtotal')
    list_filter = ('venta__fecha',)
    search_fields = ('nombre_producto', 'venta__numero_venta')
    readonly_fields = ('subtotal',)

class ItemCotizacionInline(admin.TabularInline):
    model = ItemCotizacion
    extra = 0
    readonly_fields = ('subtotal',)
    fields = ('producto', 'nombre_producto', 'cantidad', 'precio_unitario', 'subtotal')

@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ('numero_cotizacion', 'cliente_nombre', 'fecha_creacion', 'fecha_vencimiento', 'total', 'estado', 'usuario', 'convertida_en_venta')
    list_filter = ('estado', 'fecha_creacion', 'fecha_vencimiento')
    search_fields = ('numero_cotizacion', 'cliente_nombre', 'cliente_email')
    readonly_fields = ('numero_cotizacion', 'fecha_creacion', 'subtotal', 'total')
    inlines = [ItemCotizacionInline]
    ordering = ('-fecha_creacion',)
    date_hierarchy = 'fecha_creacion'

@admin.register(ItemCotizacion)
class ItemCotizacionAdmin(admin.ModelAdmin):
    list_display = ('cotizacion', 'producto', 'nombre_producto', 'cantidad', 'precio_unitario', 'subtotal')
    list_filter = ('cotizacion__fecha_creacion',)
    search_fields = ('nombre_producto', 'cotizacion__numero_cotizacion')
    readonly_fields = ('subtotal',)

@admin.register(NotificacionStock)
class NotificacionStockAdmin(admin.ModelAdmin):
    list_display = ('producto', 'stock_actual', 'stock_anterior', 'fecha', 'vista', 'notificada')
    list_filter = ('vista', 'notificada', 'fecha')
    search_fields = ('producto__nombre',)
    readonly_fields = ('fecha',)
    date_hierarchy = 'fecha'
    
    def mark_as_viewed(self, request, queryset):
        queryset.update(vista=True)
    mark_as_viewed.short_description = "Marcar como vistas"
    
    actions = [mark_as_viewed]
