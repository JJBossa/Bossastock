# Estructura del Proyecto - Control de Stock

## Organización de Archivos

### 📁 Estructura Principal

```
proyecto_boti/
├── control_stock/              # Configuración del proyecto Django
│   ├── __init__.py
│   ├── settings.py            # Configuración principal
│   ├── urls.py                # URLs principales
│   ├── wsgi.py
│   └── asgi.py
│
├── inventario/                 # Aplicación principal
│   ├── models.py              # Modelos de datos (Producto, Categoria, HistorialCambio)
│   ├── views.py               # Vistas principales
│   ├── views_extra.py         # Vistas adicionales (dashboard, exportar, etc.)
│   ├── forms.py               # Formularios
│   ├── urls.py                # URLs de la aplicación
│   ├── admin.py               # Configuración del admin
│   ├── management/
│   │   └── commands/          # Comandos personalizados
│   │       ├── importar_productos.py
│   │       ├── crear_categorias.py
│   │       └── eliminar_imagenes.py
│   └── migrations/            # Migraciones de base de datos
│
├── templates/                  # Templates HTML (solo HTML, sin CSS inline)
│   ├── base.html              # Template base
│   └── inventario/
│       ├── login.html
│       ├── inicio.html
│       ├── agregar_producto.html
│       ├── editar_producto.html
│       ├── eliminar_producto.html
│       ├── detalle_producto.html
│       └── dashboard.html
│
├── static/                     # Archivos estáticos (CSS, JS, imágenes)
│   ├── css/
│   │   └── main.css           # Estilos principales (TODO el CSS aquí)
│   └── js/                     # JavaScript (si se necesita)
│
├── media/                      # Archivos subidos por usuarios
│   └── productos/              # Imágenes de productos
│
├── manage.py
├── requirements.txt
├── README.md
└── db.sqlite3                  # Base de datos (no versionar)
```

## 📋 Reglas de Organización

### ✅ Templates (templates/)
- **Solo HTML**: Los templates deben contener únicamente HTML
- **Sin CSS inline**: No usar `<style>` tags dentro de los templates
- **Sin JavaScript inline**: Usar archivos JS externos cuando sea posible
- **Clases CSS**: Usar clases CSS definidas en `static/css/main.css`
- **Tags Django**: Usar `{% load static %}` para cargar archivos estáticos

### ✅ CSS (static/css/)
- **Todo el CSS en archivos separados**: Todos los estilos en `static/css/main.css`
- **Variables CSS**: Usar `:root` para variables globales
- **Clases reutilizables**: Crear clases que se puedan usar en múltiples templates
- **Responsive**: Incluir media queries para diseño responsive

### ✅ JavaScript (static/js/)
- **Archivos separados**: Si se necesita JS, crear archivos en `static/js/`
- **Cargar en base.html**: Usar `{% block extra_js %}` para JS específico de páginas

### ✅ Modelos (inventario/models.py)
- **Un archivo por aplicación**: Todos los modelos de la app en un solo archivo
- **Modelos relacionados juntos**: Mantener modelos relacionados cerca

### ✅ Vistas (inventario/views.py)
- **Vistas principales**: En `views.py`
- **Vistas adicionales**: Funcionalidades extra en `views_extra.py`
- **Separación lógica**: Agrupar vistas relacionadas

### ✅ Formularios (inventario/forms.py)
- **Un archivo**: Todos los formularios en `forms.py`
- **Formularios relacionados**: Agrupar formularios del mismo modelo

## 🎨 Convenciones de Nombres

### CSS
- **Clases**: Usar kebab-case (ej: `.card-producto`, `.search-container`)
- **Variables**: Usar `--` prefix (ej: `--primary-color`)
- **IDs**: Evitar cuando sea posible, preferir clases

### Templates
- **Nombres descriptivos**: `agregar_producto.html`, `editar_producto.html`
- **Snake_case**: Usar guiones bajos para nombres de archivos

### Python
- **Snake_case**: Para funciones y variables
- **PascalCase**: Para clases
- **Nombres descriptivos**: Evitar abreviaciones

## 📝 Notas Importantes

1. **No mezclar estilos**: CSS siempre en archivos separados, nunca inline
2. **Cargar static**: Siempre usar `{% load static %}` antes de usar `{% static %}`
3. **Organización lógica**: Mantener archivos relacionados juntos
4. **Comentarios**: Agregar comentarios en CSS y código complejo
5. **Versionar**: No versionar `db.sqlite3`, `__pycache__/`, `media/`

