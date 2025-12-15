from django.urls import path
from . import views
from . import views_extra
from . import views_facturas

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('agregar-producto/', views.agregar_producto, name='agregar_producto'),
    path('editar-producto/<int:producto_id>/', views.editar_producto, name='editar_producto'),
    path('eliminar-producto/<int:producto_id>/', views.eliminar_producto, name='eliminar_producto'),
    path('dashboard/', views_extra.dashboard, name='dashboard'),
    path('producto/<int:producto_id>/', views_extra.detalle_producto, name='detalle_producto'),
    path('exportar/excel/', views_extra.exportar_excel, name='exportar_excel'),
    path('exportar/pdf/', views_extra.exportar_pdf, name='exportar_pdf'),
    path('exportar/csv/', views_extra.exportar_csv, name='exportar_csv'),
    # Facturas
    path('facturas/', views_facturas.listar_facturas, name='listar_facturas'),
    path('facturas/subir/', views_facturas.subir_factura, name='subir_factura'),
    path('facturas/<int:factura_id>/', views_facturas.detalle_factura, name='detalle_factura'),
    path('facturas/<int:factura_id>/editar/', views_facturas.editar_factura, name='editar_factura'),
    path('facturas/<int:factura_id>/eliminar/', views_facturas.eliminar_factura, name='eliminar_factura'),
    path('proveedores/', views_facturas.gestionar_proveedores, name='gestionar_proveedores'),
]

