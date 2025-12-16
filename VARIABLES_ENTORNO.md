# Variables de Entorno Requeridas

Este documento describe las variables de entorno necesarias para configurar la aplicación en Render.

## Variables Requeridas

### SECRET_KEY
- **Descripción**: Clave secreta de Django para firmar cookies y otros elementos sensibles
- **Valor por defecto**: Se usa una clave por defecto (NO recomendado para producción)
- **Cómo generar una nueva**:
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
- **Ejemplo**: `django-insecure-abcdefghijklmnopqrstuvwxyz1234567890`

### DEBUG
- **Descripción**: Activa/desactiva el modo debug de Django
- **Valor por defecto**: `False`
- **Valores permitidos**: `True` o `False` (como string)
- **Recomendación**: Siempre usar `False` en producción
- **Ejemplo**: `False`

### ALLOWED_HOSTS
- **Descripción**: Lista de hosts permitidos separados por comas
- **Valor por defecto**: `localhost,127.0.0.1`
- **Formato**: Lista separada por comas sin espacios extra
- **Ejemplo**: `tu-app.onrender.com,www.tu-app.onrender.com`
- **Nota**: Render proporcionará una URL como `tu-app-xxxx.onrender.com`. Asegúrate de incluirla aquí.

### DATABASE_URL
- **Descripción**: URL de conexión a la base de datos PostgreSQL
- **Valor por defecto**: None (usa SQLite localmente)
- **Formato**: `postgresql://user:password@host:port/dbname`
- **Ejemplo**: `postgresql://user:pass@dpg-xxxxx-a.render.com:5432/dbname`
- **Nota**: Render proporciona esta variable automáticamente si configuras la base de datos como dependencia del servicio web, o puedes copiarla manualmente desde el panel de la base de datos.

## Configuración en Render

1. Ve a tu servicio web en Render
2. Navega a la sección "Environment"
3. Agrega cada variable con su valor correspondiente
4. Guarda los cambios

## Notas Importantes

- **NUNCA** commitees valores reales de estas variables al repositorio
- Usa el archivo `.gitignore` para asegurarte de que `.env` no se suba al repositorio
- En producción, siempre usa una `SECRET_KEY` única y segura
- `DEBUG=False` es esencial para seguridad en producción

