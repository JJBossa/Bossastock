"""
Tests extendidos para los modelos de la aplicación inventario
Cubre más casos de uso y validaciones
"""
import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from inventario.models import (
    Producto, Categoria, Venta, ItemVenta, Cliente, 
    CuentaPorCobrar, Almacen, OrdenCompra, Cotizacion,
    Transferencia, ItemTransferencia, StockAlmacen
)


@pytest.mark.django_db
class TestCliente:
    """Tests para el modelo Cliente"""
    
    def test_crear_cliente(self):
        """Test que se puede crear un cliente"""
        cliente = Cliente.objects.create(
            nombre='Cliente Test',
            rut='12345678-9',
            email='test@example.com',
            telefono='+56912345678'
        )
        assert cliente.nombre == 'Cliente Test'
        assert cliente.activo is True
    
    def test_cliente_str(self):
        """Test el método __str__ del cliente"""
        cliente = Cliente.objects.create(nombre='Cliente Test')
        assert str(cliente) == 'Cliente Test'


@pytest.mark.django_db
class TestAlmacen:
    """Tests para el modelo Almacen"""
    
    def test_crear_almacen(self):
        """Test que se puede crear un almacén"""
        almacen = Almacen.objects.create(
            nombre='Almacén Test',
            codigo='ALM-001',
            direccion='Dirección Test'
        )
        assert almacen.nombre == 'Almacén Test'
        assert almacen.activo is True
    
    def test_almacen_str(self):
        """Test el método __str__ del almacén"""
        almacen = Almacen.objects.create(nombre='Almacén Test', codigo='ALM-001')
        assert str(almacen) == 'Almacén Test (ALM-001)'


@pytest.mark.django_db
class TestCuentaPorCobrar:
    """Tests para el modelo CuentaPorCobrar"""
    
    def test_crear_cuenta_por_cobrar(self, admin_user):
        """Test que se puede crear una cuenta por cobrar"""
        cliente = Cliente.objects.create(nombre='Cliente Test')
        cuenta = CuentaPorCobrar.objects.create(
            cliente=cliente,
            monto_total=100000,
            monto_pagado=0,
            fecha_emision=timezone.now().date(),
            fecha_vencimiento=(timezone.now() + timedelta(days=30)).date(),
            estado='pendiente'
        )
        assert cuenta.monto_total == 100000
        assert cuenta.monto_pendiente == 100000
        assert cuenta.estado == 'pendiente'
    
    def test_cuenta_por_cobrar_monto_pendiente(self, admin_user):
        """Test el cálculo de monto pendiente"""
        cliente = Cliente.objects.create(nombre='Cliente Test')
        cuenta = CuentaPorCobrar.objects.create(
            cliente=cliente,
            monto_total=100000,
            monto_pagado=30000,
            fecha_emision=timezone.now().date(),
            fecha_vencimiento=(timezone.now() + timedelta(days=30)).date(),
            estado='parcial'
        )
        assert cuenta.monto_pendiente == 70000
    
    def test_cuenta_vencida(self, admin_user):
        """Test la propiedad cuenta_vencida"""
        cliente = Cliente.objects.create(nombre='Cliente Test')
        cuenta = CuentaPorCobrar.objects.create(
            cliente=cliente,
            monto_total=100000,
            monto_pagado=0,
            fecha_emision=(timezone.now() - timedelta(days=60)).date(),
            fecha_vencimiento=(timezone.now() - timedelta(days=30)).date(),
            estado='pendiente'
        )
        assert cuenta.cuenta_vencida is True


@pytest.mark.django_db
class TestCotizacion:
    """Tests para el modelo Cotizacion"""
    
    def test_crear_cotizacion(self, admin_user):
        """Test que se puede crear una cotización"""
        cotizacion = Cotizacion.objects.create(
            usuario=admin_user,
            cliente_nombre='Cliente Test',
            subtotal=100000,
            total=100000,
            fecha_vencimiento=(timezone.now() + timedelta(days=7)).date()
        )
        assert cotizacion.numero_cotizacion is not None
        assert cotizacion.total == 100000
        assert cotizacion.estado == 'pendiente'
    
    def test_cotizacion_genera_numero_automatico(self, admin_user):
        """Test que se genera número de cotización automático"""
        cotizacion = Cotizacion.objects.create(
            usuario=admin_user,
            cliente_nombre='Cliente Test',
            subtotal=100000,
            total=100000
        )
        assert cotizacion.numero_cotizacion.startswith('COT-')


@pytest.mark.django_db
class TestTransferencia:
    """Tests para el modelo Transferencia"""
    
    def test_crear_transferencia(self, admin_user):
        """Test que se puede crear una transferencia"""
        almacen_origen = Almacen.objects.create(nombre='Origen', codigo='ORI-001')
        almacen_destino = Almacen.objects.create(nombre='Destino', codigo='DES-001')
        
        transferencia = Transferencia.objects.create(
            almacen_origen=almacen_origen,
            almacen_destino=almacen_destino,
            usuario=admin_user,
            estado='pendiente'
        )
        assert transferencia.numero_transferencia is not None
        assert transferencia.estado == 'pendiente'
    
    def test_transferencia_genera_numero_automatico(self, admin_user):
        """Test que se genera número de transferencia automático"""
        almacen_origen = Almacen.objects.create(nombre='Origen', codigo='ORI-001')
        almacen_destino = Almacen.objects.create(nombre='Destino', codigo='DES-001')
        
        transferencia = Transferencia.objects.create(
            almacen_origen=almacen_origen,
            almacen_destino=almacen_destino,
            usuario=admin_user
        )
        assert transferencia.numero_transferencia.startswith('TRF-')


@pytest.mark.django_db
class TestStockAlmacen:
    """Tests para el modelo StockAlmacen"""
    
    def test_crear_stock_almacen(self):
        """Test que se puede crear un stock por almacén"""
        categoria = Categoria.objects.create(nombre='Test')
        producto = Producto.objects.create(
            nombre='Producto Test',
            categoria=categoria,
            precio=10000,
            stock=50
        )
        almacen = Almacen.objects.create(nombre='Almacén Test', codigo='ALM-001')
        
        stock = StockAlmacen.objects.create(
            producto=producto,
            almacen=almacen,
            cantidad=30,
            stock_minimo=10
        )
        assert stock.cantidad == 30
        assert stock.stock_bajo is False
    
    def test_stock_almacen_stock_bajo(self):
        """Test la propiedad stock_bajo"""
        categoria = Categoria.objects.create(nombre='Test')
        producto = Producto.objects.create(
            nombre='Producto Test',
            categoria=categoria,
            precio=10000
        )
        almacen = Almacen.objects.create(nombre='Almacén Test', codigo='ALM-001')
        
        stock = StockAlmacen.objects.create(
            producto=producto,
            almacen=almacen,
            cantidad=5,
            stock_minimo=10
        )
        assert stock.stock_bajo is True

