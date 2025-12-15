from django.core.management.base import BaseCommand
from inventario.models import Producto
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Elimina las imágenes de todos los productos que las tengan'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirma la eliminación de imágenes',
        )

    def handle(self, *args, **options):
        confirmar = options.get('confirmar')
        
        productos_con_imagen = Producto.objects.exclude(imagen__isnull=True).exclude(imagen='')
        total = productos_con_imagen.count()
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS('No hay productos con imágenes para eliminar.'))
            return
        
        self.stdout.write(f'\nSe encontraron {total} productos con imágenes.')
        
        if not confirmar:
            self.stdout.write(self.style.WARNING(
                '\nPara confirmar la eliminación, ejecuta el comando con --confirmar'
            ))
            self.stdout.write('Ejemplo: python manage.py eliminar_imagenes --confirmar')
            return
        
        eliminados = 0
        errores = 0
        
        for producto in productos_con_imagen:
            try:
                # Eliminar archivo físico si existe
                if producto.imagen:
                    file_path = settings.MEDIA_ROOT / producto.imagen.name
                    if file_path.exists():
                        os.remove(file_path)
                        self.stdout.write(f'[OK] Archivo eliminado: {producto.imagen.name}')
                
                # Limpiar campo en la base de datos
                producto.imagen = None
                producto.save()
                eliminados += 1
                
            except Exception as e:
                errores += 1
                self.stdout.write(self.style.ERROR(f'Error eliminando imagen de {producto.nombre}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\n[COMPLETADO] Proceso finalizado!\n'
            f'  Imagenes eliminadas: {eliminados}\n'
            f'  Errores: {errores}\n'
            f'  Total procesados: {total}'
        ))

