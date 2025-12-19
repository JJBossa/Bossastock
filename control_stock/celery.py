"""
Configuración de Celery para tareas asíncronas
"""
import os

try:
    from celery import Celery
    
    # Establecer el módulo de configuración de Django por defecto
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'control_stock.settings')
    
    app = Celery('control_stock')
    
    # Configuración usando namespace 'CELERY'
    app.config_from_object('django.conf:settings', namespace='CELERY')
    
    # Auto-descubrir tareas en todas las apps instaladas
    app.autodiscover_tasks()
    
    
    @app.task(bind=True, ignore_result=True)
    def debug_task(self):
        """Tarea de prueba para verificar que Celery funciona"""
        print(f'Request: {self.request!r}')
        
except ImportError:
    # Celery no está instalado, crear un objeto dummy
    app = None

