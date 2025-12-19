"""
Tareas asíncronas con Celery
"""
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger('inventario')


@shared_task(bind=True, max_retries=3)
def procesar_factura_ocr_async(self, factura_id):
    """
    Procesa una factura con OCR de forma asíncrona
    
    Args:
        factura_id: ID de la factura a procesar
    """
    from .models import Factura
    from .utils_ocr import procesar_factura_ocr
    
    try:
        factura = Factura.objects.get(id=factura_id)
        logger.info(f'Iniciando procesamiento OCR asíncrono de factura {factura_id}')
        
        # Procesar OCR
        procesar_factura_ocr(factura)
        
        logger.info(f'Factura {factura_id} procesada exitosamente')
        return {'status': 'success', 'factura_id': factura_id}
        
    except Factura.DoesNotExist:
        logger.error(f'Factura {factura_id} no encontrada')
        return {'status': 'error', 'message': 'Factura no encontrada'}
    except Exception as exc:
        logger.error(f'Error procesando factura {factura_id}: {str(exc)}')
        # Reintentar hasta 3 veces
        raise self.retry(exc=exc, countdown=60)  # Reintentar después de 60 segundos


@shared_task
def generar_reporte_async(reporte_id, formato='pdf'):
    """
    Genera un reporte de forma asíncrona
    
    Args:
        reporte_id: ID del reporte programado
        formato: Formato del reporte ('pdf', 'excel', 'csv')
    """
    from .models import ReporteProgramado
    
    try:
        reporte = ReporteProgramado.objects.get(id=reporte_id)
        logger.info(f'Generando reporte {reporte_id} en formato {formato}')
        
        # Aquí iría la lógica de generación del reporte
        # Por ahora solo registramos
        reporte.ultima_ejecucion = timezone.now()
        reporte.save()
        
        logger.info(f'Reporte {reporte_id} generado exitosamente')
        return {'status': 'success', 'reporte_id': reporte_id}
        
    except ReporteProgramado.DoesNotExist:
        logger.error(f'Reporte {reporte_id} no encontrado')
        return {'status': 'error', 'message': 'Reporte no encontrado'}
    except Exception as exc:
        logger.error(f'Error generando reporte {reporte_id}: {str(exc)}')
        return {'status': 'error', 'message': str(exc)}


@shared_task
def enviar_notificacion_stock_bajo():
    """
    Envía notificaciones por email cuando hay productos con stock bajo
    Se ejecuta periódicamente (configurar en celery beat)
    """
    from .models import Producto, NotificacionStock
    from django.db.models import F
    
    try:
        # Productos con stock bajo
        productos_bajo_stock = Producto.objects.filter(
            activo=True,
            stock__lte=F('stock_minimo')
        ).select_related('categoria')
        
        if not productos_bajo_stock.exists():
            logger.info('No hay productos con stock bajo')
            return {'status': 'success', 'productos': 0}
        
        # Crear notificaciones
        notificaciones_creadas = 0
        for producto in productos_bajo_stock:
            # Verificar si ya existe una notificación reciente (últimas 24 horas)
            hace_24h = timezone.now() - timedelta(hours=24)
            existe = NotificacionStock.objects.filter(
                producto=producto,
                fecha_creacion__gte=hace_24h,
                enviada=False
            ).exists()
            
            if not existe:
                NotificacionStock.objects.create(
                    producto=producto,
                    tipo='stock_bajo',
                    mensaje=f'El producto {producto.nombre} tiene stock bajo ({producto.stock} unidades)'
                )
                notificaciones_creadas += 1
        
        logger.info(f'Creadas {notificaciones_creadas} notificaciones de stock bajo')
        return {'status': 'success', 'notificaciones': notificaciones_creadas}
        
    except Exception as exc:
        logger.error(f'Error en notificaciones de stock bajo: {str(exc)}')
        return {'status': 'error', 'message': str(exc)}


@shared_task
def limpiar_logs_antiguos(dias=30):
    """
    Limpia logs antiguos de la base de datos
    
    Args:
        dias: Días de antigüedad para considerar un log como antiguo
    """
    from .models import LogAccion, HistorialCambio
    
    try:
        fecha_limite = timezone.now() - timedelta(days=dias)
        
        # Eliminar logs antiguos
        logs_eliminados = LogAccion.objects.filter(fecha__lt=fecha_limite).delete()[0]
        historial_eliminado = HistorialCambio.objects.filter(fecha__lt=fecha_limite).delete()[0]
        
        logger.info(f'Limpiados {logs_eliminados} logs y {historial_eliminado} registros de historial')
        return {
            'status': 'success',
            'logs_eliminados': logs_eliminados,
            'historial_eliminado': historial_eliminado
        }
        
    except Exception as exc:
        logger.error(f'Error limpiando logs: {str(exc)}')
        return {'status': 'error', 'message': str(exc)}


@shared_task
def enviar_reporte_por_email(reporte_id, email_destino):
    """
    Envía un reporte generado por email
    
    Args:
        reporte_id: ID del reporte
        email_destino: Email destino
    """
    from .models import ReporteProgramado
    
    try:
        reporte = ReporteProgramado.objects.get(id=reporte_id)
        
        # Aquí iría la lógica de generación y envío del reporte
        # Por ahora solo simulamos
        subject = f'Reporte: {reporte.nombre}'
        message = f'Adjunto encontrarás el reporte: {reporte.nombre}'
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email_destino],
            fail_silently=False,
        )
        
        logger.info(f'Reporte {reporte_id} enviado a {email_destino}')
        return {'status': 'success', 'email': email_destino}
        
    except Exception as exc:
        logger.error(f'Error enviando reporte {reporte_id}: {str(exc)}')
        return {'status': 'error', 'message': str(exc)}

