from django.core.management.base import BaseCommand
from inventario.models import Categoria

class Command(BaseCommand):
    help = 'Crea categorías iniciales para los productos'

    def handle(self, *args, **options):
        categorias = [
            {'nombre': 'Bebidas', 'color': '#667eea', 'descripcion': 'Bebidas en general'},
            {'nombre': 'Cervezas', 'color': '#f59e0b', 'descripcion': 'Cervezas y cervezas artesanales'},
            {'nombre': 'Vinos', 'color': '#ef4444', 'descripcion': 'Vinos tintos, blancos y rosados'},
            {'nombre': 'Licores', 'color': '#10b981', 'descripcion': 'Licores y destilados'},
            {'nombre': 'Whisky', 'color': '#8b5cf6', 'descripcion': 'Whisky y escocés'},
            {'nombre': 'Ron', 'color': '#f97316', 'descripcion': 'Ron y rones premium'},
            {'nombre': 'Vodka', 'color': '#06b6d4', 'descripcion': 'Vodka y vodka premium'},
            {'nombre': 'Tequila', 'color': '#84cc16', 'descripcion': 'Tequila y mezcal'},
            {'nombre': 'Gin', 'color': '#ec4899', 'descripcion': 'Gin y ginebra'},
            {'nombre': 'Pisco', 'color': '#14b8a6', 'descripcion': 'Pisco chileno y peruano'},
            {'nombre': 'Refrescos', 'color': '#3b82f6', 'descripcion': 'Refrescos y gaseosas'},
            {'nombre': 'Jugos', 'color': '#fbbf24', 'descripcion': 'Jugos naturales y envasados'},
            {'nombre': 'Energizantes', 'color': '#f43f5e', 'descripcion': 'Bebidas energizantes'},
        ]
        
        creadas = 0
        actualizadas = 0
        
        for cat_data in categorias:
            categoria, created = Categoria.objects.get_or_create(
                nombre=cat_data['nombre'],
                defaults={
                    'color': cat_data['color'],
                    'descripcion': cat_data['descripcion']
                }
            )
            if not created:
                categoria.color = cat_data['color']
                categoria.descripcion = cat_data['descripcion']
                categoria.save()
                actualizadas += 1
            else:
                creadas += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'[COMPLETADO] Categorias creadas!\n'
                f'  Creadas: {creadas}\n'
                f'  Actualizadas: {actualizadas}'
            )
        )

