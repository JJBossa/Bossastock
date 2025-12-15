from django.contrib import admin
from django.utils.html import format_html
from .models import Producto, Categoria, HistorialCambio, Factura, ItemFactura, Proveedor

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
    list_display = ('nombre', 'sku', 'categoria', 'precio', 'stock', 'stock_bajo_indicator', 'fecha_actualizacion', 'imagen_preview')
    list_filter = ('categoria', 'activo', 'fecha_creacion', 'stock')
    search_fields = ('nombre', 'sku', 'descripcion')
    ordering = ('nombre',)
    readonly_fields = ('imagen_preview', 'fecha_creacion', 'fecha_actualizacion', 'sku')
    fieldsets = (
        ('Información del Producto', {
            'fields': ('nombre', 'sku', 'descripcion', 'categoria', 'activo')
        }),
        ('Precio y Stock', {
            'fields': ('precio', 'stock', 'stock_minimo')
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
