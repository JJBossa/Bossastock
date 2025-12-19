"""
Comando para crear grupos de permisos iniciales
Ejecutar: python manage.py crear_grupos_permisos
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from inventario.models import (
    Producto, Categoria, Venta, Cliente, Almacen, 
    Proveedor, Factura, Cotizacion, AjusteInventario
)


class Command(BaseCommand):
    help = 'Crea los grupos de permisos iniciales del sistema'

    def handle(self, *args, **options):
        self.stdout.write('Creando grupos de permisos...')
        
        # Obtener content types
        producto_ct = ContentType.objects.get_for_model(Producto)
        categoria_ct = ContentType.objects.get_for_model(Categoria)
        venta_ct = ContentType.objects.get_for_model(Venta)
        cliente_ct = ContentType.objects.get_for_model(Cliente)
        almacen_ct = ContentType.objects.get_for_model(Almacen)
        proveedor_ct = ContentType.objects.get_for_model(Proveedor)
        factura_ct = ContentType.objects.get_for_model(Factura)
        cotizacion_ct = ContentType.objects.get_for_model(Cotizacion)
        ajuste_ct = ContentType.objects.get_for_model(AjusteInventario)
        
        # 1. GRUPO: Administrador
        admin_group, created = Group.objects.get_or_create(name='Administrador')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Grupo "Administrador" creado'))
        else:
            self.stdout.write('  Grupo "Administrador" ya existe')
        
        # Administrador tiene todos los permisos
        admin_permissions = Permission.objects.filter(
            content_type__in=[
                producto_ct, categoria_ct, venta_ct, cliente_ct,
                almacen_ct, proveedor_ct, factura_ct, cotizacion_ct, ajuste_ct
            ]
        )
        admin_group.permissions.set(admin_permissions)
        self.stdout.write(f'  Permisos asignados: {admin_permissions.count()}')
        
        # 2. GRUPO: Vendedor
        vendedor_group, created = Group.objects.get_or_create(name='Vendedor')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Grupo "Vendedor" creado'))
        else:
            self.stdout.write('  Grupo "Vendedor" ya existe')
        
        # Vendedor puede: ver productos, crear ventas, ver clientes, crear cotizaciones
        vendedor_permissions = Permission.objects.filter(
            content_type__in=[producto_ct, venta_ct, cliente_ct, cotizacion_ct],
            codename__in=[
                'view_producto', 'view_categoria',
                'add_venta', 'view_venta', 'change_venta',
                'view_cliente', 'add_cliente', 'change_cliente',
                'add_cotizacion', 'view_cotizacion', 'change_cotizacion',
            ]
        )
        vendedor_group.permissions.set(vendedor_permissions)
        self.stdout.write(f'  Permisos asignados: {vendedor_permissions.count()}')
        
        # 3. GRUPO: Almacenero
        almacen_group, created = Group.objects.get_or_create(name='Almacenero')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Grupo "Almacenero" creado'))
        else:
            self.stdout.write('  Grupo "Almacenero" ya existe')
        
        # Almacenero puede: gestionar productos, almacenes, ajustes, recepciones
        almacen_permissions = Permission.objects.filter(
            content_type__in=[producto_ct, almacen_ct, ajuste_ct, proveedor_ct, factura_ct],
            codename__in=[
                'view_producto', 'change_producto',  # Puede actualizar stock
                'view_categoria',
                'view_almacen', 'add_almacen', 'change_almacen',
                'view_ajusteinventario', 'add_ajusteinventario', 'change_ajusteinventario',
                'view_proveedor', 'view_factura', 'add_factura',
            ]
        )
        almacen_group.permissions.set(almacen_permissions)
        self.stdout.write(f'  Permisos asignados: {almacen_permissions.count()}')
        
        # 4. GRUPO: Contador
        contador_group, created = Group.objects.get_or_create(name='Contador')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Grupo "Contador" creado'))
        else:
            self.stdout.write('  Grupo "Contador" ya existe')
        
        # Contador puede: ver reportes, gestionar cuentas por cobrar
        contador_permissions = Permission.objects.filter(
            content_type__in=[venta_ct, cliente_ct, factura_ct],
            codename__in=[
                'view_venta', 'view_cliente', 'view_factura',
            ]
        )
        contador_group.permissions.set(contador_permissions)
        self.stdout.write(f'  Permisos asignados: {contador_permissions.count()}')
        
        # 5. GRUPO: Usuario Normal (solo lectura básica)
        usuario_group, created = Group.objects.get_or_create(name='Usuario Normal')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Grupo "Usuario Normal" creado'))
        else:
            self.stdout.write('  Grupo "Usuario Normal" ya existe')
        
        # Usuario normal solo puede ver productos y crear ventas
        usuario_permissions = Permission.objects.filter(
            content_type__in=[producto_ct, venta_ct],
            codename__in=[
                'view_producto', 'view_categoria',
                'add_venta', 'view_venta',  # Puede vender
            ]
        )
        usuario_group.permissions.set(usuario_permissions)
        self.stdout.write(f'  Permisos asignados: {usuario_permissions.count()}')
        
        self.stdout.write(self.style.SUCCESS('\n✓ Grupos de permisos creados exitosamente!'))
        self.stdout.write('\nPara asignar un usuario a un grupo:')
        self.stdout.write('  python manage.py shell')
        self.stdout.write('  >>> from django.contrib.auth.models import User, Group')
        self.stdout.write('  >>> user = User.objects.get(username="bossa")')
        self.stdout.write('  >>> group = Group.objects.get(name="Administrador")')
        self.stdout.write('  >>> user.groups.add(group)')

