from django import forms
from .models import Factura, ItemFactura, Proveedor

class FacturaForm(forms.ModelForm):
    class Meta:
        model = Factura
        fields = ['archivo', 'proveedor', 'fecha_emision', 'numero_factura', 'notas']
        widgets = {
            'archivo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png',
            }),
            'proveedor': forms.Select(attrs={
                'class': 'form-select',
            }),
            'fecha_emision': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'numero_factura': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de factura (se detecta automáticamente)'
            }),
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas adicionales (opcional)'
            }),
        }
        labels = {
            'archivo': 'Archivo de Factura (PDF o Imagen)',
            'proveedor': 'Proveedor',
            'fecha_emision': 'Fecha de Emisión',
            'numero_factura': 'Número de Factura',
            'notas': 'Notas',
        }

class ItemFacturaForm(forms.ModelForm):
    class Meta:
        model = ItemFactura
        fields = ['producto', 'nombre_producto', 'cantidad', 'precio_unitario']
        widgets = {
            'producto': forms.Select(attrs={
                'class': 'form-select',
            }),
            'nombre_producto': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
            }),
        }

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'rut', 'contacto', 'telefono', 'email', 'direccion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
            }),
            'rut': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'contacto': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
            }),
        }

