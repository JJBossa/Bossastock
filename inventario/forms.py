from django import forms
from django.core.exceptions import ValidationError
from typing import Optional
from .models import Producto, Categoria
from .validators import (
    validate_precio_positivo, validate_stock_positivo,
    validate_nombre_producto, validate_precio_promo_menor_precio,
    validate_precio_compra_menor_precio, validate_sku_unico
)
from .constants import PRECIO_MINIMO, PRECIO_MAXIMO

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'sku', 'descripcion', 'categoria', 'precio_compra', 'precio', 'precio_promo', 'stock', 'stock_minimo', 'imagen', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Nombre del producto',
                'data-bs-toggle': 'tooltip',
                'data-bs-placement': 'top',
                'title': 'Ingresa el nombre completo del producto. Ejemplo: "Coca Cola 500ml"'
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'SKU/Código (se genera automáticamente si se deja vacío)'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción del producto',
                'rows': 3
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
            'precio_compra': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Precio de compra (opcional)',
                'min': '0',
                'step': '1',
                'data-bs-toggle': 'tooltip',
                'data-bs-placement': 'top',
                'title': 'Precio al que compraste el producto. Se usa para calcular el margen de ganancia.'
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Precio de venta',
                'min': '0',
                'step': '1',
                'data-bs-toggle': 'tooltip',
                'data-bs-placement': 'top',
                'title': 'Precio de venta al público. Solo números enteros (sin decimales).'
            }),
            'precio_promo': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Precio promocional (opcional)',
                'min': '0',
                'step': '1'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Stock',
                'min': '0',
                'step': '1',
                'data-bs-toggle': 'tooltip',
                'data-bs-placement': 'top',
                'title': 'Cantidad actual en inventario. Debe ser 0 o mayor.'
            }),
            'stock_minimo': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Stock mínimo',
                'min': '0',
                'step': '1',
                'data-bs-toggle': 'tooltip',
                'data-bs-placement': 'top',
                'title': 'Cantidad mínima antes de recibir alerta de stock bajo. Recomendado: 10 unidades.'
            }),
            'imagen': forms.FileInput(attrs={
                'class': 'form-control form-control-lg',
                'accept': 'image/*'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'nombre': 'Nombre del Producto',
            'sku': 'SKU/Código de Barras',
            'descripcion': 'Descripción',
            'categoria': 'Categoría',
            'precio_compra': 'Precio de Compra',
            'precio': 'Precio de Venta',
            'precio_promo': 'Precio Promo',
            'stock': 'Stock',
            'stock_minimo': 'Stock Mínimo',
            'imagen': 'Imagen del Producto',
            'activo': 'Producto Activo',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['imagen'].required = False
        self.fields['sku'].required = False
        self.fields['descripcion'].required = False
        self.fields['categoria'].required = False
        self.fields['precio_compra'].required = False
        self.fields['precio_promo'].required = False
        self.fields['categoria'].queryset = Categoria.objects.all().order_by('nombre')
    
    def clean_precio_compra(self) -> Optional[float]:
        """Valida el precio de compra"""
        precio_compra = self.cleaned_data.get('precio_compra')
        if precio_compra is not None:
            validate_precio_positivo(precio_compra)
        return precio_compra
    
    def clean_precio(self) -> float:
        """Valida el precio de venta"""
        precio = self.cleaned_data.get('precio')
        precio_compra = self.cleaned_data.get('precio_compra')
        
        if precio is not None:
            validate_precio_positivo(precio)
            if precio == 0:
                raise ValidationError('El precio de venta debe ser mayor a 0. Si el producto es gratuito, ingresa 1.')
            if precio_compra:
                validate_precio_compra_menor_precio(precio_compra, precio)
        
        return precio
    
    def clean_precio_promo(self) -> Optional[float]:
        """Valida el precio promocional"""
        precio_promo = self.cleaned_data.get('precio_promo')
        precio = self.cleaned_data.get('precio')
        
        if precio_promo is not None:
            validate_precio_positivo(precio_promo)
            if precio:
                validate_precio_promo_menor_precio(precio_promo, precio)
        
        return precio_promo
    
    def clean_stock(self) -> int:
        """Valida el stock"""
        stock = self.cleaned_data.get('stock')
        if stock is not None:
            validate_stock_positivo(stock)
        return stock or 0
    
    def clean_stock_minimo(self) -> int:
        """Valida el stock mínimo"""
        stock_minimo = self.cleaned_data.get('stock_minimo')
        if stock_minimo is not None:
            validate_stock_positivo(stock_minimo)
        return stock_minimo or 0
    
    def clean_nombre(self) -> str:
        """Valida el nombre del producto"""
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            validate_nombre_producto(nombre)
            nombre = nombre.strip()
        return nombre
    
    def clean_sku(self) -> Optional[str]:
        """Valida el SKU"""
        sku = self.cleaned_data.get('sku')
        if sku:
            sku = sku.strip().upper()
            validate_sku_unico(sku, self.instance)
        return sku
    
    def clean(self) -> dict:
        """Validación cruzada de campos"""
        cleaned_data = super().clean()
        precio_compra = cleaned_data.get('precio_compra')
        precio = cleaned_data.get('precio')
        precio_promo = cleaned_data.get('precio_promo')
        
        # Validar relaciones entre precios
        if precio_compra and precio and precio_compra >= precio:
            raise ValidationError({
                'precio_compra': 'El precio de compra debe ser menor al precio de venta para tener ganancia.'
            })
        
        if precio_promo and precio and precio_promo >= precio:
            raise ValidationError({
                'precio_promo': 'El precio promocional debe ser menor al precio de venta.'
            })
        
        return cleaned_data

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion', 'color']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Nombre de la categoría'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción de la categoría',
                'rows': 3
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'type': 'color',
                'style': 'height: 50px;'
            }),
        }

