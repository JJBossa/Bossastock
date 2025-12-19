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
from . import views_api
from . import views_clientes
from . import views_cuentas_cobrar
from . import views_almacenes
from . import views_compras
from . import views_busqueda_global
from . import views_exportacion_avanzada
from . import views_logs_auditoria
from . import views_notificaciones
from . import views_historial_precios
from . import views_ajustes
from . import views_devoluciones
from . import views_idioma
from . import views_reportes_programados

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
    # API para mejoras UX
    path('api/buscar-productos/', views_api.buscar_productos_api, name='buscar_productos_api'),
    # Clientes
    path('clientes/', views_clientes.listar_clientes, name='listar_clientes'),
    path('clientes/crear/', views_clientes.crear_cliente, name='crear_cliente'),
    path('clientes/<int:cliente_id>/', views_clientes.detalle_cliente, name='detalle_cliente'),
    path('clientes/<int:cliente_id>/editar/', views_clientes.editar_cliente, name='editar_cliente'),
    path('clientes/<int:cliente_id>/eliminar/', views_clientes.eliminar_cliente, name='eliminar_cliente'),
    path('api/buscar-cliente/', views_clientes.buscar_cliente_api, name='buscar_cliente_api'),
    # Cuentas por Cobrar
    path('cuentas-cobrar/', views_cuentas_cobrar.listar_cuentas_cobrar, name='listar_cuentas_cobrar'),
    path('cuentas-cobrar/crear/', views_cuentas_cobrar.crear_cuenta_cobrar, name='crear_cuenta_cobrar'),
    path('cuentas-cobrar/crear/<int:cliente_id>/', views_cuentas_cobrar.crear_cuenta_cobrar, name='crear_cuenta_cobrar_cliente'),
    path('clientes/<int:cliente_id>/cuenta/', views_cuentas_cobrar.crear_cuenta_cobrar, name='crear_cuenta_cobrar_cliente'),
    path('cuentas-cobrar/<int:cuenta_id>/', views_cuentas_cobrar.detalle_cuenta_cobrar, name='detalle_cuenta_cobrar'),
    path('cuentas-cobrar/<int:cuenta_id>/pago/', views_cuentas_cobrar.registrar_pago, name='registrar_pago'),
    # Almacenes
    path('almacenes/', views_almacenes.listar_almacenes, name='listar_almacenes'),
    path('almacenes/crear/', views_almacenes.crear_almacen, name='crear_almacen'),
    path('almacenes/<int:almacen_id>/', views_almacenes.detalle_almacen, name='detalle_almacen'),
    path('almacenes/<int:almacen_id>/editar/', views_almacenes.editar_almacen, name='editar_almacen'),
    path('almacenes/transferencia/crear/', views_almacenes.crear_transferencia, name='crear_transferencia'),
    path('almacenes/transferencia/<int:transferencia_id>/', views_almacenes.detalle_transferencia, name='detalle_transferencia'),
    path('almacenes/transferencia/<int:transferencia_id>/completar/', views_almacenes.completar_transferencia, name='completar_transferencia'),
    # Compras
    path('compras/', views_compras.listar_ordenes_compra, name='listar_ordenes_compra'),
    path('compras/crear/', views_compras.crear_orden_compra, name='crear_orden_compra'),
    path('compras/<int:orden_id>/', views_compras.detalle_orden_compra, name='detalle_orden_compra'),
    path('compras/<int:orden_id>/recibir/', views_compras.recibir_mercancia, name='recibir_mercancia'),
    # Búsqueda Global
    path('buscar/', views_busqueda_global.busqueda_global, name='busqueda_global'),
    path('api/busqueda-global/', views_busqueda_global.busqueda_global_api, name='busqueda_global_api'),
    path('historial-busquedas/', views_busqueda_global.historial_busquedas, name='historial_busquedas'),
    # Exportación Avanzada
    path('exportacion-avanzada/', views_exportacion_avanzada.exportacion_avanzada, name='exportacion_avanzada'),
    path('api/exportar-avanzado/', views_exportacion_avanzada.exportar_datos_avanzado, name='exportar_datos_avanzado'),
    # Logs y Auditoría
    path('logs/', views_logs_auditoria.listar_logs, name='listar_logs'),
    path('logs/<int:log_id>/', views_logs_auditoria.detalle_log, name='detalle_log'),
    path('logs/exportar/', views_logs_auditoria.exportar_logs, name='exportar_logs'),
    # Notificaciones
    path('notificaciones/', views_notificaciones.centro_notificaciones, name='centro_notificaciones'),
    path('api/notificaciones/', views_notificaciones.obtener_notificaciones_api, name='obtener_notificaciones_api'),
    path('notificaciones/<int:notificacion_id>/marcar-leida/', views_notificaciones.marcar_notificacion_leida, name='marcar_notificacion_leida'),
    path('notificaciones/marcar-todas-leidas/', views_notificaciones.marcar_todas_leidas, name='marcar_todas_leidas'),
    # Historial de Precios
    path('historial-precios/', views_historial_precios.historial_precios_general, name='historial_precios_general'),
    path('producto/<int:producto_id>/historial-precios/', views_historial_precios.historial_precios_producto, name='historial_precios_producto'),
    # Ajustes de Inventario
    path('ajustes/', views_ajustes.listar_ajustes, name='listar_ajustes'),
    path('ajustes/crear/', views_ajustes.crear_ajuste, name='crear_ajuste'),
    path('ajustes/<int:ajuste_id>/', views_ajustes.detalle_ajuste, name='detalle_ajuste'),
    path('ajustes/<int:ajuste_id>/aprobar/', views_ajustes.aprobar_ajuste, name='aprobar_ajuste'),
    path('ajustes/<int:ajuste_id>/rechazar/', views_ajustes.rechazar_ajuste, name='rechazar_ajuste'),
    # Devoluciones
    path('devoluciones/', views_devoluciones.listar_devoluciones, name='listar_devoluciones'),
    path('devoluciones/crear/', views_devoluciones.crear_devolucion, name='crear_devolucion'),
    path('devoluciones/crear/<int:venta_id>/', views_devoluciones.crear_devolucion, name='crear_devolucion_venta'),
    path('devoluciones/<int:devolucion_id>/', views_devoluciones.detalle_devolucion, name='detalle_devolucion'),
    path('devoluciones/<int:devolucion_id>/procesar/', views_devoluciones.procesar_devolucion, name='procesar_devolucion'),
    path('devoluciones/<int:devolucion_id>/rechazar/', views_devoluciones.rechazar_devolucion, name='rechazar_devolucion'),
    # Cambio de idioma
    path('cambiar-idioma/', views_idioma.cambiar_idioma, name='cambiar_idioma'),
    # Reportes Programados
    path('reportes-programados/', views_reportes_programados.listar_reportes_programados, name='listar_reportes_programados'),
    path('reportes-programados/crear/', views_reportes_programados.crear_reporte_programado, name='crear_reporte_programado'),
    path('reportes-programados/<int:reporte_id>/', views_reportes_programados.detalle_reporte_programado, name='detalle_reporte_programado'),
    path('reportes-programados/<int:reporte_id>/editar/', views_reportes_programados.editar_reporte_programado, name='editar_reporte_programado'),
    path('reportes-programados/<int:reporte_id>/eliminar/', views_reportes_programados.eliminar_reporte_programado, name='eliminar_reporte_programado'),
    path('reportes-programados/<int:reporte_id>/ejecutar/', views_reportes_programados.ejecutar_reporte_ahora, name='ejecutar_reporte_ahora'),
    # Dashboard
    path('dashboard/guardar-orden/', views_extra.guardar_orden_dashboard, name='guardar_orden_dashboard'),
]

