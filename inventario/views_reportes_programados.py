"""
Vistas para reportes programados por email
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q
from .models import ReporteProgramado
from .utils import es_admin_bossa, logger


@login_required
def listar_reportes_programados(request):
    """Lista todos los reportes programados"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('inicio')
    
    reportes = ReporteProgramado.objects.all().select_related('creado_por').order_by('nombre')
    
    # Filtros
    activo = request.GET.get('activo', '')
    tipo = request.GET.get('tipo', '')
    
    if activo == 'si':
        reportes = reportes.filter(activo=True)
    elif activo == 'no':
        reportes = reportes.filter(activo=False)
    
    if tipo:
        reportes = reportes.filter(tipo_reporte=tipo)
    
    # Paginación
    paginator = Paginator(reportes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'activo': activo,
        'tipo': tipo,
        'es_admin': True,
    }
    return render(request, 'inventario/listar_reportes_programados.html', context)


@login_required
def crear_reporte_programado(request):
    """Crear un nuevo reporte programado"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('inicio')
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        tipo_reporte = request.POST.get('tipo_reporte')
        formato = request.POST.get('formato', 'pdf')
        frecuencia = request.POST.get('frecuencia')
        hora_envio = request.POST.get('hora_envio', '09:00')
        destinatarios = request.POST.get('destinatarios', '').strip()
        
        dia_semana = request.POST.get('dia_semana')
        dia_mes = request.POST.get('dia_mes')
        
        try:
            reporte = ReporteProgramado.objects.create(
                nombre=nombre,
                tipo_reporte=tipo_reporte,
                formato=formato,
                frecuencia=frecuencia,
                hora_envio=hora_envio,
                destinatarios=destinatarios,
                dia_semana=int(dia_semana) if dia_semana else None,
                dia_mes=int(dia_mes) if dia_mes else None,
                creado_por=request.user,
                activo=True
            )
            
            messages.success(request, f'Reporte programado "{reporte.nombre}" creado exitosamente.')
            return redirect('detalle_reporte_programado', reporte_id=reporte.id)
            
        except Exception as e:
            logger.error(f'Error al crear reporte programado: {str(e)}')
            messages.error(request, f'Error al crear reporte programado: {str(e)}')
    
    context = {
        'es_admin': True,
    }
    return render(request, 'inventario/crear_reporte_programado.html', context)


@login_required
def detalle_reporte_programado(request, reporte_id):
    """Detalle de un reporte programado"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('inicio')
    
    reporte = get_object_or_404(ReporteProgramado.objects.select_related('creado_por'), id=reporte_id)
    
    context = {
        'reporte': reporte,
        'es_admin': True,
    }
    return render(request, 'inventario/detalle_reporte_programado.html', context)


@login_required
def editar_reporte_programado(request, reporte_id):
    """Editar un reporte programado"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('inicio')
    
    reporte = get_object_or_404(ReporteProgramado, id=reporte_id)
    
    if request.method == 'POST':
        reporte.nombre = request.POST.get('nombre', '').strip()
        reporte.tipo_reporte = request.POST.get('tipo_reporte')
        reporte.formato = request.POST.get('formato', 'pdf')
        reporte.frecuencia = request.POST.get('frecuencia')
        reporte.hora_envio = request.POST.get('hora_envio', '09:00')
        reporte.destinatarios = request.POST.get('destinatarios', '').strip()
        reporte.activo = request.POST.get('activo') == 'on'
        
        dia_semana = request.POST.get('dia_semana')
        dia_mes = request.POST.get('dia_mes')
        reporte.dia_semana = int(dia_semana) if dia_semana else None
        reporte.dia_mes = int(dia_mes) if dia_mes else None
        
        # Recalcular próximo envío
        reporte.proximo_envio = reporte.calcular_proximo_envio()
        
        try:
            reporte.save()
            messages.success(request, f'Reporte programado "{reporte.nombre}" actualizado exitosamente.')
            return redirect('detalle_reporte_programado', reporte_id=reporte.id)
        except Exception as e:
            logger.error(f'Error al actualizar reporte programado: {str(e)}')
            messages.error(request, f'Error al actualizar reporte programado: {str(e)}')
    
    context = {
        'reporte': reporte,
        'es_admin': True,
    }
    return render(request, 'inventario/editar_reporte_programado.html', context)


@login_required
def eliminar_reporte_programado(request, reporte_id):
    """Eliminar un reporte programado"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('inicio')
    
    reporte = get_object_or_404(ReporteProgramado, id=reporte_id)
    
    if request.method == 'POST':
        nombre = reporte.nombre
        reporte.delete()
        messages.success(request, f'Reporte programado "{nombre}" eliminado exitosamente.')
        return redirect('listar_reportes_programados')
    
    context = {
        'reporte': reporte,
        'es_admin': True,
    }
    return render(request, 'inventario/eliminar_reporte_programado.html', context)


@login_required
def ejecutar_reporte_ahora(request, reporte_id):
    """Ejecutar un reporte programado inmediatamente"""
    if not es_admin_bossa(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('inicio')
    
    reporte = get_object_or_404(ReporteProgramado, id=reporte_id)
    
    try:
        # Aquí se ejecutaría la lógica de generación y envío del reporte
        # Por ahora solo simulamos
        from django.core.mail import send_mail
        from django.conf import settings
        
        destinatarios = [email.strip() for email in reporte.destinatarios.split(',') if email.strip()]
        
        # Generar reporte (simulado)
        mensaje = f"Reporte {reporte.get_tipo_reporte_display()} generado automáticamente."
        
        # Enviar email
        send_mail(
            subject=f'STOCKEX - {reporte.nombre}',
            message=mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@stockex.com',
            recipient_list=destinatarios,
            fail_silently=False,
        )
        
        # Actualizar último envío
        reporte.ultimo_envio = timezone.now()
        reporte.proximo_envio = reporte.calcular_proximo_envio()
        reporte.save()
        
        messages.success(request, f'Reporte "{reporte.nombre}" ejecutado y enviado exitosamente.')
        
    except Exception as e:
        logger.error(f'Error al ejecutar reporte programado: {str(e)}')
        messages.error(request, f'Error al ejecutar reporte: {str(e)}')
    
    return redirect('detalle_reporte_programado', reporte_id=reporte.id)

