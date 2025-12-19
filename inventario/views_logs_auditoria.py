"""
Vistas para historial y auditoría mejorada
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import timedelta
import json
import csv
from .models import LogAccion
from .utils import es_admin_bossa, logger

@login_required
def listar_logs(request):
    """Lista todos los logs de acciones del sistema"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('inicio')
    
    # Filtros
    modulo = request.GET.get('modulo', '')
    tipo_accion = request.GET.get('tipo_accion', '')
    usuario_id = request.GET.get('usuario', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    busqueda = request.GET.get('q', '')
    
    logs = LogAccion.objects.all().select_related('usuario').order_by('-fecha')
    
    # Aplicar filtros
    if modulo:
        logs = logs.filter(modulo=modulo)
    if tipo_accion:
        logs = logs.filter(tipo_accion=tipo_accion)
    if usuario_id:
        logs = logs.filter(usuario_id=usuario_id)
    if fecha_desde:
        logs = logs.filter(fecha__date__gte=fecha_desde)
    if fecha_hasta:
        logs = logs.filter(fecha__date__lte=fecha_hasta)
    if busqueda:
        logs = logs.filter(
            Q(descripcion__icontains=busqueda) |
            Q(objeto_tipo__icontains=busqueda)
        )
    
    # Paginación
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_logs = logs.count()
    logs_hoy = logs.filter(fecha__date=timezone.now().date()).count()
    logs_semana = logs.filter(fecha__date__gte=timezone.now().date() - timedelta(days=7)).count()
    
    # Obtener módulos y tipos únicos para filtros
    modulos = LogAccion.MODULO_CHOICES
    tipos_accion = LogAccion.TIPO_ACCION
    
    context = {
        'page_obj': page_obj,
        'total_logs': total_logs,
        'logs_hoy': logs_hoy,
        'logs_semana': logs_semana,
        'modulos': modulos,
        'tipos_accion': tipos_accion,
        'filtros': {
            'modulo': modulo,
            'tipo_accion': tipo_accion,
            'usuario_id': usuario_id,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'busqueda': busqueda,
        },
        'es_admin': True
    }
    
    return render(request, 'inventario/listar_logs.html', context)

@login_required
def detalle_log(request, log_id):
    """Detalle de un log específico con comparación de datos"""
    if not es_admin_bossa(request.user):
        return redirect('inicio')
    
    log = LogAccion.objects.get(id=log_id)
    
    context = {
        'log': log,
        'es_admin': True
    }
    
    return render(request, 'inventario/detalle_log.html', context)

@login_required
def exportar_logs(request):
    """Exporta logs a CSV"""
    if not es_admin_bossa(request.user):
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    logs = LogAccion.objects.all().select_related('usuario').order_by('-fecha')[:1000]
    
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="logs_auditoria.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Fecha', 'Usuario', 'Tipo Acción', 'Módulo', 'Descripción', 'Objeto ID', 'IP', 'User Agent'])
    
    for log in logs:
        writer.writerow([
            log.fecha.strftime('%Y-%m-%d %H:%M:%S'),
            log.usuario.username if log.usuario else 'Sistema',
            log.get_tipo_accion_display(),
            log.get_modulo_display(),
            log.descripcion,
            log.objeto_id or '',
            log.ip_address or '',
            (log.user_agent or '')[:100]
        ])
    
    return response

