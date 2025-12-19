"""
Context processors para traducción
"""
import logging
from django.conf import settings
from django.utils.translation import get_language
from .translations import get_translations_dict, translate

logger = logging.getLogger('inventario')


def translations(request):
    """
    Context processor que inyecta las traducciones en todos los templates
    
    Uso en template: {{ translations.Ventas }} o {{ t.Ventas }}
    """
    # Obtener idioma de la sesión primero, luego del sistema
    language = None
    
    # Intentar obtener de la sesión (prioridad 1) - probar ambas claves
    if hasattr(request, 'session') and request.session:
        language = request.session.get('django_language') or request.session.get('language')
    
    # Si no está en sesión, intentar de la cookie (prioridad 2)
    if not language and hasattr(request, 'COOKIES'):
        cookie_name = getattr(settings, 'LANGUAGE_COOKIE_NAME', 'django_language')
        language = request.COOKIES.get(cookie_name) or request.COOKIES.get('django_language') or request.COOKIES.get('language')
    
    # Si no está en cookie, usar get_language() de Django (prioridad 3)
    if not language:
        language = get_language()
    
    # Si aún no hay idioma, usar el por defecto
    if not language:
        language = 'es'
    
    # Asegurar que solo usamos el código base (ej: 'es' de 'es-es')
    if language and '-' in language:
        language = language.split('-')[0]
    
    # Normalizar a minúsculas
    language = language.lower() if language else 'es'
    
    # Validar que el idioma esté en los idiomas soportados
    idiomas_soportados = [lang[0] for lang in settings.LANGUAGES]
    if language not in idiomas_soportados:
        language = 'es'  # Fallback a español
    
    # Obtener traducciones
    translations_dict = get_translations_dict(language)
    
    return {
        'translations': translations_dict,
        't': translations_dict,  # Alias corto
        'translate': lambda text: translate(text, language),  # Función helper
        'current_language': language,  # Para debugging
    }

