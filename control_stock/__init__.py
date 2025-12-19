# Inicializar Celery cuando Django arranque (opcional)
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Celery no está instalado, continuar sin él
    celery_app = None
    __all__ = ()

