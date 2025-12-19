from django import forms
from django.core.exceptions import ValidationError
from .models import Producto, Categoria

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
    
    def clean_precio_compra(self):
        precio_compra = self.cleaned_data.get('precio_compra')
        if precio_compra is not None and precio_compra < 0:
            raise ValidationError('El precio de compra no puede ser negativo.')
        return precio_compra
    
    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        precio_compra = self.cleaned_data.get('precio_compra')
        if precio is not None and precio < 0:
            raise ValidationError('El precio de venta no puede ser negativo. Ingresa un valor mayor o igual a 0.')
        if precio is not None and precio == 0:
            raise ValidationError('El precio de venta debe ser mayor a 0. Si el producto es gratuito, ingresa 1.')
        if precio_compra and precio and precio < precio_compra:
            raise ValidationError('El precio de venta no puede ser menor al precio de compra. Revisa los valores.')
        return precio
    
    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock is not None and stock < 0:
            raise ValidationError('El stock no puede ser negativo. Ingresa 0 o un número positivo.')
        return stock
    
    def clean_stock_minimo(self):
        stock_minimo = self.cleaned_data.get('stock_minimo')
        if stock_minimo is not None and stock_minimo < 0:
            raise ValidationError('El stock mínimo no puede ser negativo. Ingresa 0 o un número positivo.')
        return stock_minimo
    
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            nombre = nombre.strip()
            if len(nombre) < 2:
                raise ValidationError('El nombre del producto debe tener al menos 2 caracteres.')
            if len(nombre) > 200:
                raise ValidationError('El nombre del producto es demasiado largo. Máximo 200 caracteres.')
        return nombre

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

