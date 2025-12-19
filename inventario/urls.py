from django.urls import path
from . import views
from . import views_extra
from . import views_facturas
from . import views_usuarios
from . import views_favoritos
from . import views_categorias
from . import views_movimientos
from . import views_backup
from . import views_reportes
from . import views_impresion
from . import views_pos
from . import views_cotizaciones

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('agregar-producto/', views.agregar_producto, name='agregar_producto'),
    path('editar-producto/<int:producto_id>/', views.editar_producto, name='editar_producto'),
    path('eliminar-producto/<int:producto_id>/', views.eliminar_producto, name='eliminar_producto'),
    path('producto/<int:producto_id>/actualizar-stock/', views.actualizar_stock_rapido, name='actualizar_stock_rapido'),
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
    # Gestión de Usuarios (Solo Admin)
    path('usuarios/', views_usuarios.listar_usuarios, name='listar_usuarios'),
    path('usuarios/crear/', views_usuarios.crear_usuario, name='crear_usuario'),
    path('usuarios/<int:user_id>/editar/', views_usuarios.editar_usuario, name='editar_usuario'),
    path('usuarios/<int:user_id>/resetear-password/', views_usuarios.resetear_password, name='resetear_password'),
    path('usuarios/<int:user_id>/eliminar/', views_usuarios.eliminar_usuario, name='eliminar_usuario'),
    # Favoritos
    path('producto/<int:producto_id>/favorito/', views_favoritos.toggle_favorito, name='toggle_favorito'),
    path('favoritos/', views_favoritos.mis_favoritos, name='mis_favoritos'),
    # Código de barras
    path('api/buscar-codigo-barras/', views_facturas.buscar_producto_codigo_barras, name='buscar_codigo_barras'),
    # Categorías
    path('categorias/', views_categorias.gestionar_categorias, name='gestionar_categorias'),
    path('categorias/<int:categoria_id>/ajax/', views_categorias.editar_categoria_ajax, name='editar_categoria_ajax'),
    # Movimientos de Stock
    path('producto/<int:producto_id>/movimiento/', views_movimientos.registrar_movimiento_stock, name='registrar_movimiento_stock'),
    path('movimientos/', views_movimientos.listar_movimientos, name='listar_movimientos'),
    # Backup
    path('backup/crear/', views_backup.crear_backup, name='crear_backup'),
    path('backup/', views_backup.gestionar_backups, name='gestionar_backups'),
    path('backup/<str:nombre_archivo>/descargar/', views_backup.descargar_backup, name='descargar_backup'),
    path('backup/<str:nombre_archivo>/eliminar/', views_backup.eliminar_backup, name='eliminar_backup'),
    # Reportes
    path('reportes/', views_reportes.reportes_avanzados, name='reportes_avanzados'),
    path('graficos-ventas/', views_reportes.graficos_ventas, name='graficos_ventas'),
    path('dashboard-usuario/', views_reportes.dashboard_usuario_normal, name='dashboard_usuario'),
    # Impresión
    path('imprimir/etiquetas/', views_impresion.imprimir_etiquetas, name='imprimir_etiquetas'),
    path('imprimir/etiquetas/pdf/', views_impresion.generar_etiquetas_pdf, name='generar_etiquetas_pdf'),
    path('imprimir/lista-precios/', views_impresion.imprimir_lista_precios, name='imprimir_lista_precios'),
    path('imprimir/lista-precios/pdf/', views_impresion.generar_lista_precios_pdf, name='generar_lista_precios_pdf'),
    # Punto de Venta (POS)
    path('pos/', views_pos.punto_venta, name='punto_venta'),
    path('pos/buscar-producto/', views_pos.buscar_producto_pos, name='buscar_producto_pos'),
    path('pos/procesar-venta/', views_pos.procesar_venta, name='procesar_venta'),
    path('ventas/', views_pos.listar_ventas, name='listar_ventas'),
    path('ventas/limpiar-historial/', views_pos.limpiar_historial_ventas, name='limpiar_historial_ventas'),
    path('ventas/<int:venta_id>/', views_pos.detalle_venta, name='detalle_venta'),
    path('ventas/<int:venta_id>/cancelar/', views_pos.cancelar_venta, name='cancelar_venta'),
    path('ventas/<int:venta_id>/ticket/', views_impresion.imprimir_ticket_venta, name='imprimir_ticket_venta'),
    # Cotizaciones
    path('cotizaciones/', views_cotizaciones.listar_cotizaciones, name='listar_cotizaciones'),
    path('cotizaciones/crear/', views_cotizaciones.crear_cotizacion, name='crear_cotizacion'),
    path('cotizaciones/<int:cotizacion_id>/', views_cotizaciones.detalle_cotizacion, name='detalle_cotizacion'),
    path('cotizaciones/<int:cotizacion_id>/imprimir/', views_cotizaciones.imprimir_cotizacion, name='imprimir_cotizacion'),
    path('cotizaciones/<int:cotizacion_id>/convertir/', views_cotizaciones.convertir_cotizacion_en_venta, name='convertir_cotizacion_en_venta'),
]

