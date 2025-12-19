# Guía de Usuario - STOCKEX

## Índice
1. [Inicio de Sesión](#inicio-de-sesión)
2. [Dashboard](#dashboard)
3. [Gestión de Productos](#gestión-de-productos)
4. [Punto de Venta (POS)](#punto-de-venta-pos)
5. [Ventas](#ventas)
6. [Clientes](#clientes)
7. [Cotizaciones](#cotizaciones)
8. [Almacenes](#almacenes)
9. [Compras](#compras)
10. [Reportes](#reportes)
11. [Búsqueda Global](#búsqueda-global)
12. [Notificaciones](#notificaciones)

---

## Inicio de Sesión

1. Accede a la URL del sistema (por defecto: `http://localhost:8000`)
2. Ingresa tu nombre de usuario y contraseña
3. Haz clic en "Iniciar Sesión"

**Nota:** Si eres administrador, verás un panel adicional con más opciones.

---

## Dashboard

El dashboard muestra:
- **Estadísticas generales**: Total de productos, ventas del día, stock bajo
- **Gráficos interactivos**: Ventas por período, productos más vendidos
- **Accesos rápidos**: Enlaces a las funciones más usadas

### Accesos Rápidos
- **Punto de Venta**: Acceso directo al sistema de ventas
- **Agregar Producto**: Crear nuevos productos rápidamente
- **Reportes**: Ver análisis y estadísticas

---

## Gestión de Productos

### Ver Productos
- En la página principal verás todos los productos activos
- Usa la barra de búsqueda para filtrar por nombre, SKU o descripción
- Los filtros avanzados permiten buscar por categoría, precio, stock

### Agregar Producto
1. Haz clic en "Agregar Producto" (solo administradores)
2. Completa el formulario:
   - Nombre del producto (obligatorio)
   - SKU (se genera automáticamente si no se proporciona)
   - Categoría
   - Precio de venta
   - Precio de compra (opcional)
   - Stock inicial
   - Stock mínimo
   - Descripción
   - Imagen (opcional)
3. Haz clic en "Guardar"

### Editar Producto
1. Busca el producto que deseas editar
2. Haz clic en el producto para ver sus detalles
3. Haz clic en "Editar"
4. Modifica los campos necesarios
5. Guarda los cambios

### Actualizar Stock Rápido
1. En la lista de productos, haz clic en el botón de actualizar stock
2. Ingresa la nueva cantidad
3. Selecciona el tipo de movimiento (entrada/salida)
4. Confirma

---

## Punto de Venta (POS)

### Realizar una Venta
1. Accede al Punto de Venta desde el menú
2. Busca productos usando:
   - Barra de búsqueda (nombre o SKU)
   - Escaneo de código de barras (presiona `F`)
   - Selección manual
3. Agrega productos al carrito
4. Selecciona el cliente (opcional)
5. Aplica descuentos si es necesario:
   - Descuento fijo ($)
   - Descuento porcentual (%)
6. Selecciona método de pago
7. Ingresa el monto recibido
8. Haz clic en "Procesar Venta"

### Atajos de Teclado
- **F1**: Buscar producto
- **F2**: Procesar venta
- **F3**: Limpiar carrito
- **F**: Búsqueda rápida por código de barras
- **Ctrl+K**: Búsqueda global

### Venta a Crédito
1. Selecciona un cliente
2. Marca la casilla "Venta a Crédito"
3. Se creará automáticamente una cuenta por cobrar

---

## Ventas

### Ver Historial de Ventas
1. Accede a "Ventas" desde el menú
2. Usa los filtros para buscar ventas específicas:
   - Número de venta
   - Método de pago
   - Rango de fechas
3. Haz clic en una venta para ver sus detalles

### Detalle de Venta
- Información completa de la venta
- Lista de productos vendidos
- Opción de imprimir ticket
- Opción de cancelar venta (solo si no está cancelada)

### Imprimir Ticket
1. En el detalle de venta, haz clic en "Imprimir"
2. Selecciona el formato:
   - **Térmica**: Para impresoras de 58mm
   - **A4**: Formato estándar

---

## Clientes

### Listar Clientes
1. Accede a "Clientes" desde el menú
2. Verás la lista de todos los clientes activos
3. Usa la búsqueda para filtrar

### Crear Cliente
1. Haz clic en "Crear Cliente"
2. Completa el formulario:
   - Nombre (obligatorio)
   - RUT (opcional)
   - Email
   - Teléfono
   - Dirección
3. Guarda

### Ver Detalle de Cliente
- Información completa del cliente
- Historial de ventas
- Cuentas por cobrar
- Opción de crear cuenta por cobrar directamente

---

## Cotizaciones

### Crear Cotización
1. Accede a "Cotizaciones" → "Crear Cotización"
2. Selecciona un cliente (opcional)
3. Agrega productos al carrito
4. Aplica descuentos si es necesario
5. Establece fecha de vencimiento
6. Guarda la cotización

### Convertir Cotización en Venta
1. Abre el detalle de la cotización
2. Haz clic en "Convertir en Venta"
3. Se creará una venta con los productos de la cotización

### Imprimir Cotización
1. En el detalle de cotización, haz clic en "Imprimir"
2. Se generará un PDF con la cotización

---

## Almacenes

### Listar Almacenes
1. Accede a "Almacenes" desde el menú
2. Verás todos los almacenes del sistema

### Crear Almacén
1. Haz clic en "Crear Almacén"
2. Completa:
   - Nombre
   - Código
   - Dirección
   - Teléfono
   - Responsable
3. Guarda

### Transferencias entre Almacenes
1. Accede a "Almacenes" → "Crear Transferencia"
2. Selecciona almacén origen y destino
3. Agrega productos a transferir
4. Confirma la transferencia
5. Cuando los productos lleguen, completa la transferencia

---

## Compras

### Crear Orden de Compra
1. Accede a "Compras" → "Crear Orden"
2. Selecciona el proveedor
3. Agrega productos a comprar
4. Establece fecha esperada de recepción
5. Guarda la orden

### Recibir Mercancía
1. Abre el detalle de la orden de compra
2. Haz clic en "Recibir Mercancía"
3. Selecciona el almacén de destino
4. Confirma las cantidades recibidas
5. El stock se actualizará automáticamente

---

## Reportes

### Reportes Avanzados
1. Accede a "Reportes" desde el menú
2. Selecciona el período:
   - Últimos 7 días
   - Últimos 30 días
   - Últimos 90 días
   - Último año
   - Rango personalizado
3. Visualiza:
   - Ventas en el tiempo
   - Ventas por método de pago
   - Productos más vendidos
   - Top clientes
   - Estado de cuentas por cobrar
   - Stock por almacén

### Exportar Datos
1. Accede a "Exportación Avanzada"
2. Selecciona:
   - Tipo de datos (productos, ventas, clientes, etc.)
   - Formato (Excel, PDF, CSV)
   - Rango de fechas (opcional)
3. Haz clic en "Generar Exportación"

---

## Búsqueda Global

### Búsqueda Rápida
- Presiona **Ctrl+K** desde cualquier página
- Escribe lo que buscas
- El sistema buscará en:
  - Productos
  - Clientes
  - Ventas
  - Cotizaciones

### Historial de Búsquedas
- Accede a "Historial de Búsquedas" para ver tus búsquedas recientes

---

## Notificaciones

### Centro de Notificaciones
1. Accede a "Notificaciones" desde el menú
2. Verás todas tus notificaciones:
   - Stock bajo
   - Cuentas por cobrar vencidas
   - Órdenes de compra pendientes
   - Mensajes del sistema

### Marcar como Leída
- Haz clic en "Marcar Leída" en cada notificación
- O usa "Marcar Todas como Leídas" para limpiar todas

---

## Consejos y Trucos

1. **Búsqueda Rápida**: Usa `Ctrl+K` para buscar en todo el sistema
2. **Atajos de Teclado**: En el POS, usa F1, F2, F3 para acciones rápidas
3. **Favoritos**: Marca productos frecuentes como favoritos para acceso rápido
4. **Exportación**: Exporta datos regularmente para respaldos
5. **Notificaciones**: Revisa regularmente las notificaciones para estar al día

---

## Soporte

Si tienes problemas o preguntas:
1. Revisa esta guía
2. Consulta la documentación técnica
3. Revisa los logs del sistema (solo administradores)

