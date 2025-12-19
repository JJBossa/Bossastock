"""
Tests extendidos para las vistas de la aplicación inventario
Cubre más funcionalidades y casos de uso
"""
import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from inventario.models import (
    Producto, Categoria, Venta, ItemVenta, Cliente, 
    CuentaPorCobrar, Almacen, OrdenCompra, Cotizacion
)
from tests.factories import ProductoFactory, CategoriaFactory, UserFactory


@pytest.mark.django_db
class TestVentasViews:
    """Tests para las vistas de ventas"""
    
    def test_punto_venta_requiere_login(self, client):
        """Test que el punto de venta requiere autenticación"""
        response = client.get(reverse('punto_venta'))
        assert response.status_code == 302
        assert '/login' in response.url
    
    def test_punto_venta_acceso_autenticado(self, client, admin_user):
        """Test que cualquier usuario autenticado puede acceder al POS"""
        client.force_login(admin_user)
        response = client.get(reverse('punto_venta'))
        assert response.status_code == 200
    
    def test_listar_ventas_requiere_login(self, client):
        """Test que listar ventas requiere autenticación"""
        response = client.get(reverse('listar_ventas'))
        assert response.status_code == 302


@pytest.mark.django_db
class TestClientesViews:
    """Tests para las vistas de clientes"""
    
    def test_listar_clientes_requiere_login(self, client):
        """Test que listar clientes requiere autenticación"""
        response = client.get(reverse('listar_clientes'))
        assert response.status_code == 302
    
    def test_listar_clientes_autenticado(self, client, admin_user):
        """Test que se puede listar clientes cuando se está autenticado"""
        client.force_login(admin_user)
        response = client.get(reverse('listar_clientes'))
        assert response.status_code == 200
    
    def test_crear_cliente_requiere_admin(self, client, normal_user):
        """Test que crear cliente requiere ser admin"""
        client.force_login(normal_user)
        response = client.get(reverse('crear_cliente'))
        # Debería redirigir o mostrar error
        assert response.status_code in [302, 403]


@pytest.mark.django_db
class TestAlmacenesViews:
    """Tests para las vistas de almacenes"""
    
    def test_listar_almacenes_requiere_login(self, client):
        """Test que listar almacenes requiere autenticación"""
        response = client.get(reverse('listar_almacenes'))
        assert response.status_code == 302
    
    def test_listar_almacenes_autenticado(self, client, admin_user):
        """Test que se puede listar almacenes cuando se está autenticado"""
        client.force_login(admin_user)
        response = client.get(reverse('listar_almacenes'))
        assert response.status_code == 200


@pytest.mark.django_db
class TestCotizacionesViews:
    """Tests para las vistas de cotizaciones"""
    
    def test_listar_cotizaciones_requiere_login(self, client):
        """Test que listar cotizaciones requiere autenticación"""
        response = client.get(reverse('listar_cotizaciones'))
        assert response.status_code == 302
    
    def test_crear_cotizacion_requiere_login(self, client):
        """Test que crear cotización requiere autenticación"""
        response = client.get(reverse('crear_cotizacion'))
        assert response.status_code == 302


@pytest.mark.django_db
class TestReportesViews:
    """Tests para las vistas de reportes"""
    
    def test_reportes_avanzados_requiere_login(self, client):
        """Test que los reportes requieren autenticación"""
        response = client.get(reverse('reportes_avanzados'))
        assert response.status_code == 302
    
    def test_reportes_avanzados_autenticado(self, client, admin_user):
        """Test que se puede acceder a reportes cuando se está autenticado"""
        client.force_login(admin_user)
        response = client.get(reverse('reportes_avanzados'))
        assert response.status_code == 200


@pytest.mark.django_db
class TestBusquedaGlobal:
    """Tests para la búsqueda global"""
    
    def test_busqueda_global_requiere_login(self, client):
        """Test que la búsqueda global requiere autenticación"""
        response = client.get(reverse('busqueda_global'))
        assert response.status_code == 302
    
    def test_busqueda_global_api_requiere_login(self, client):
        """Test que la API de búsqueda global requiere autenticación"""
        response = client.get(reverse('busqueda_global_api'), {'q': 'test'})
        assert response.status_code == 302
    
    def test_busqueda_global_api_funciona(self, client, admin_user):
        """Test que la API de búsqueda global funciona correctamente"""
        ProductoFactory(nombre='Producto Test', activo=True)
        client.force_login(admin_user)
        response = client.get(reverse('busqueda_global_api'), {'q': 'Test'})
        assert response.status_code == 200
        data = response.json()
        assert 'productos' in data


@pytest.mark.django_db
class TestExportacion:
    """Tests para las vistas de exportación"""
    
    def test_exportar_excel_requiere_login(self, client):
        """Test que exportar Excel requiere autenticación"""
        response = client.get(reverse('exportar_excel'))
        assert response.status_code == 302
    
    def test_exportar_pdf_requiere_login(self, client):
        """Test que exportar PDF requiere autenticación"""
        response = client.get(reverse('exportar_pdf'))
        assert response.status_code == 302


@pytest.mark.django_db
class TestNotificaciones:
    """Tests para las vistas de notificaciones"""
    
    def test_centro_notificaciones_requiere_login(self, client):
        """Test que el centro de notificaciones requiere autenticación"""
        response = client.get(reverse('centro_notificaciones'))
        assert response.status_code == 302
    
    def test_centro_notificaciones_autenticado(self, client, admin_user):
        """Test que se puede acceder al centro de notificaciones cuando se está autenticado"""
        client.force_login(admin_user)
        response = client.get(reverse('centro_notificaciones'))
        assert response.status_code == 200


@pytest.mark.django_db
class TestLogsAuditoria:
    """Tests para las vistas de logs de auditoría"""
    
    def test_listar_logs_requiere_login(self, client):
        """Test que listar logs requiere autenticación"""
        response = client.get(reverse('listar_logs'))
        assert response.status_code == 302
    
    def test_listar_logs_requiere_admin(self, client, normal_user):
        """Test que listar logs requiere ser admin"""
        client.force_login(normal_user)
        response = client.get(reverse('listar_logs'))
        # Debería redirigir o mostrar error
        assert response.status_code in [302, 403]

