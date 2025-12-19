from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core import serializers
from django.core.management import call_command
from django.conf import settings
from io import StringIO
import json
import os
from datetime import datetime
from pathlib import Path
from .utils import es_admin_bossa

@login_required
def crear_backup(request):
    """Crea un backup de la base de datos desde la interfaz web"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('inicio')
    
    if request.method == 'POST':
        try:
            BASE_DIR = Path(__file__).resolve().parent.parent.parent
            backup_dir = BASE_DIR / 'backups'
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = backup_dir / f'backup_{timestamp}.json'
            
            # Exportar datos
            from inventario.models import Producto, Categoria, Proveedor, Factura, ItemFactura, MovimientoStock
            
            datos = {}
            datos['categorias'] = serializers.serialize('json', Categoria.objects.all())
            datos['productos'] = serializers.serialize('json', Producto.objects.all())
            datos['proveedores'] = serializers.serialize('json', Proveedor.objects.all())
            datos['facturas'] = serializers.serialize('json', Factura.objects.all())
            datos['items_factura'] = serializers.serialize('json', ItemFactura.objects.all())
            datos['movimientos_stock'] = serializers.serialize('json', MovimientoStock.objects.all())
            datos['metadata'] = {
                'fecha_backup': datetime.now().isoformat(),
                'usuario': request.user.username,
                'total_productos': Producto.objects.count(),
                'total_categorias': Categoria.objects.count(),
            }
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=2, ensure_ascii=False)
            
            file_size = backup_file.stat().st_size / 1024  # KB
            
            messages.success(request, f'Backup creado exitosamente: {backup_file.name} ({file_size:.2f} KB)')
            return redirect('gestionar_backups')
        except Exception as e:
            messages.error(request, f'Error al crear backup: {str(e)}')
            return redirect('gestionar_backups')
    
    return redirect('gestionar_backups')

@login_required
def gestionar_backups(request):
    """Gestiona los backups creados"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('inicio')
    
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    backup_dir = BASE_DIR / 'backups'
    backup_dir.mkdir(exist_ok=True)
    
    backups = []
    for file in sorted(backup_dir.glob('backup_*.json'), reverse=True):
        stat = file.stat()
        backups.append({
            'nombre': file.name,
            'ruta': str(file),
            'tamaño': stat.st_size / 1024,  # KB
            'fecha': datetime.fromtimestamp(stat.st_mtime)
        })
    
    context = {
        'backups': backups,
        'es_admin': True,
    }
    
    return render(request, 'inventario/gestionar_backups.html', context)

@login_required
def descargar_backup(request, nombre_archivo):
    """Descarga un archivo de backup"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('inicio')
    
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    backup_file = BASE_DIR / 'backups' / nombre_archivo
    
    if not backup_file.exists():
        messages.error(request, 'El archivo de backup no existe.')
        return redirect('gestionar_backups')
    
    with open(backup_file, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        return response

@login_required
def eliminar_backup(request, nombre_archivo):
    """Elimina un archivo de backup"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('inicio')
    
    if request.method == 'POST':
        BASE_DIR = Path(__file__).resolve().parent.parent.parent
        backup_file = BASE_DIR / 'backups' / nombre_archivo
        
        if backup_file.exists():
            backup_file.unlink()
            messages.success(request, f'Backup "{nombre_archivo}" eliminado exitosamente.')
        else:
            messages.error(request, 'El archivo de backup no existe.')
    
    return redirect('gestionar_backups')

