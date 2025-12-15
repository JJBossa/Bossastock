# 🐍 Guía de Despliegue en PythonAnywhere

Esta guía te ayudará a desplegar tu proyecto Django en PythonAnywhere de forma rápida y sencilla.

## 📋 Requisitos Previos

1. Cuenta en [PythonAnywhere.com](https://www.pythonanywhere.com) (gratis)
2. Tu proyecto en GitHub, GitLab o Bitbucket
3. 15 minutos de tu tiempo

## 🎯 Pasos para Desplegar

### 1. Subir tu código a GitHub

Si aún no tienes tu código en GitHub:

```bash
# Inicializar repositorio (si no lo has hecho)
git init
git add .
git commit -m "Preparado para producción"

# Crear repositorio en GitHub y luego:
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git branch -M main
git push -u origin main
```

### 2. Crear cuenta en PythonAnywhere

1. Ve a [pythonanywhere.com](https://www.pythonanywhere.com)
2. Regístrate (plan "Beginner" es gratis)
3. Confirma tu email

### 3. Clonar tu Repositorio

1. En el dashboard de PythonAnywhere, ve a la pestaña **"Files"**
2. Abre una consola Bash (botón "Bash" en la parte superior)
3. Navega a tu directorio home y clona el repo:

```bash
cd ~
git clone https://github.com/TU_USUARIO/TU_REPO.git proyecto_boti
cd proyecto_boti
```

### 4. Crear Entorno Virtual

```bash
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Instalar Tesseract OCR

PythonAnywhere tiene Tesseract preinstalado, pero necesitas asegurarte de que esté disponible:

```bash
# Verificar que Tesseract esté instalado
tesseract --version

# Si no está, instálalo (puede requerir permisos de administrador)
# En PythonAnywhere generalmente ya está instalado
```

### 6. Configurar la Aplicación Web

1. Ve a la pestaña **"Web"** en el dashboard
2. Haz clic en **"Add a new web app"**
3. Selecciona:
   - **Domain:** `tu-usuario.pythonanywhere.com`
   - **Python Web Framework:** Django
   - **Python version:** 3.10
   - **Project path:** `/home/tu-usuario/proyecto_boti`
   - **Source code:** `/home/tu-usuario/proyecto_boti`
   - **WSGI file:** `/home/tu-usuario/proyecto_boti/control_stock/wsgi.py`

### 7. Configurar Variables de Entorno

En la pestaña **"Web"**, en la sección de tu aplicación, haz clic en **"Environment variables"** y agrega:

```
SECRET_KEY=tu-secret-key-super-segura-aqui
DEBUG=False
ALLOWED_HOSTS=tu-usuario.pythonanywhere.com
```

**Para generar un SECRET_KEY seguro:**
```bash
cd ~/proyecto_boti
source venv/bin/activate
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 8. Actualizar settings.py

PythonAnywhere necesita algunas configuraciones específicas. Edita `control_stock/settings.py`:

```python
# Al final del archivo, agrega:
if 'pythonanywhere.com' in os.environ.get('HTTP_HOST', ''):
    # Configuraciones específicas de PythonAnywhere
    STATIC_ROOT = '/home/tu-usuario/proyecto_boti/staticfiles'
    MEDIA_ROOT = '/home/tu-usuario/proyecto_boti/media'
```

### 9. Configurar Archivos Estáticos

1. En la pestaña **"Web"**, en la sección **"Static files"**, agrega:
   - **URL:** `/static/`
   - **Directory:** `/home/tu-usuario/proyecto_boti/staticfiles`

2. Para archivos media:
   - **URL:** `/media/`
   - **Directory:** `/home/tu-usuario/proyecto_boti/media`

### 10. Recolectar Archivos Estáticos

En la consola Bash:

```bash
cd ~/proyecto_boti
source venv/bin/activate
python manage.py collectstatic --noinput
```

### 11. Ejecutar Migraciones

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py crear_categorias
```

### 12. Configurar WSGI

1. En la pestaña **"Web"**, haz clic en el enlace del archivo WSGI
2. Reemplaza el contenido con:

```python
import os
import sys

# Agregar el path del proyecto
path = '/home/tu-usuario/proyecto_boti'
if path not in sys.path:
    sys.path.insert(0, path)

# Activar el entorno virtual
activate_this = '/home/tu-usuario/proyecto_boti/venv/bin/activate_this.py'
if os.path.exists(activate_this):
    exec(open(activate_this).read(), {'__file__': activate_this})

# Configurar Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'control_stock.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

**IMPORTANTE:** Reemplaza `tu-usuario` con tu nombre de usuario de PythonAnywhere.

### 13. Reiniciar la Aplicación

1. En la pestaña **"Web"**, haz clic en el botón verde **"Reload"**
2. Espera unos segundos

### 14. ¡Listo! 🎉

Tu aplicación estará disponible en: `https://tu-usuario.pythonanywhere.com`

## 🔧 Configuración Adicional

### Configurar Dominio Personalizado

1. En la pestaña **"Web"**, en "Static files"
2. Agrega tu dominio personalizado
3. Configura DNS según las instrucciones

### Programar Tareas (Cron Jobs)

Si necesitas ejecutar comandos periódicamente:

1. Ve a la pestaña **"Tasks"**
2. Crea una nueva tarea programada
3. Ejemplo: `cd /home/tu-usuario/proyecto_boti && source venv/bin/activate && python manage.py tu_comando`

## ⚠️ Notas Importantes

- **Plan Gratuito**: Tiene limitaciones (1 app web, 512MB de almacenamiento)
- **Archivos Media**: Se guardan en el sistema de archivos. Para producción real, considera usar S3
- **Tesseract**: Generalmente está preinstalado, pero verifica con `tesseract --version`
- **Consola Web**: PythonAnywhere tiene una consola Bash muy útil para administrar tu app

## 🐛 Solución de Problemas

### Error: "Module not found"
- Verifica que el entorno virtual esté activado
- Asegúrate de que todas las dependencias estén en `requirements.txt`

### Error: "Static files not found"
- Verifica que `collectstatic` se haya ejecutado
- Revisa la configuración de Static files en la pestaña Web

### Error: "Tesseract not found"
- Verifica con `tesseract --version` en la consola
- Si no está, contacta al soporte de PythonAnywhere

### La app no carga
- Revisa los logs de error en la pestaña Web → Error log
- Verifica que el WSGI esté configurado correctamente
- Asegúrate de haber hecho "Reload"

## 📞 Soporte

- PythonAnywhere tiene excelente documentación: [help.pythonanywhere.com](https://help.pythonanywhere.com)
- Revisa los logs de error en el dashboard

¡Buena suerte con tu despliegue! 🚀

