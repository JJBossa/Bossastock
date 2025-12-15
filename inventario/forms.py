from django import forms
from .models import Producto, Categoria

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'sku', 'descripcion', 'categoria', 'precio', 'precio_promo', 'stock', 'stock_minimo', 'imagen', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Nombre del producto'
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
            'precio': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Precio unidad',
                'min': '0',
                'step': '1'
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
                'step': '1'
            }),
            'stock_minimo': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Stock mínimo',
                'min': '0',
                'step': '1'
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
            'precio': 'Precio Unidad',
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
        self.fields['precio_promo'].required = False
        self.fields['categoria'].queryset = Categoria.objects.all().order_by('nombre')

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

