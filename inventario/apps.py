from django.apps import AppConfig


class InventarioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventario'
    
    def ready(self):
        """Importa las señales cuando la app está lista"""
        import inventario.signals