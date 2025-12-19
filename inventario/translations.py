"""
Sistema de traducción simple para STOCKEX
Proporciona traducciones básicas sin necesidad de gettext
"""
from django.utils.translation import get_language

# Diccionario de traducciones
TRANSLATIONS = {
    'es': {
        # Navegación principal
        'Ventas': 'Ventas',
        'Menú': 'Menú',
        'Productos': 'Productos',
        'Clientes': 'Clientes',
        'Cotizaciones': 'Cotizaciones',
        'Facturas': 'Facturas',
        'Proveedores': 'Proveedores',
        'Almacenes': 'Almacenes',
        'Compras': 'Compras',
        'Reportes': 'Reportes',
        'Usuarios': 'Usuarios',
        'Dashboard': 'Dashboard',
        'Cerrar Sesión': 'Cerrar Sesión',
        'Idioma': 'Idioma',
        'Español': 'Español',
        'English': 'English',
        'Português': 'Português',
        # Acciones comunes
        'Agregar': 'Agregar',
        'Editar': 'Editar',
        'Eliminar': 'Eliminar',
        'Guardar': 'Guardar',
        'Cancelar': 'Cancelar',
        'Buscar': 'Buscar',
        'Limpiar': 'Limpiar',
        'Ver Detalles': 'Ver Detalles',
        'Volver': 'Volver',
        # Mensajes
        'Stock': 'Stock',
        'Precio': 'Precio',
        'Categoría': 'Categoría',
        'Nombre': 'Nombre',
        'Cantidad': 'Cantidad',
        'Total': 'Total',
        'Subtotal': 'Subtotal',
    },
    'en': {
        # Main navigation
        'Ventas': 'Sales',
        'Menú': 'Menu',
        'Productos': 'Products',
        'Clientes': 'Clients',
        'Cotizaciones': 'Quotes',
        'Facturas': 'Invoices',
        'Proveedores': 'Suppliers',
        'Almacenes': 'Warehouses',
        'Compras': 'Purchases',
        'Reportes': 'Reports',
        'Usuarios': 'Users',
        'Dashboard': 'Dashboard',
        'Cerrar Sesión': 'Logout',
        'Idioma': 'Language',
        'Español': 'Spanish',
        'English': 'English',
        'Português': 'Portuguese',
        # Common actions
        'Agregar': 'Add',
        'Editar': 'Edit',
        'Eliminar': 'Delete',
        'Guardar': 'Save',
        'Cancelar': 'Cancel',
        'Buscar': 'Search',
        'Limpiar': 'Clear',
        'Ver Detalles': 'View Details',
        'Volver': 'Back',
        # Messages
        'Stock': 'Stock',
        'Precio': 'Price',
        'Categoría': 'Category',
        'Nombre': 'Name',
        'Cantidad': 'Quantity',
        'Total': 'Total',
        'Subtotal': 'Subtotal',
    },
    'pt': {
        # Navegação principal
        'Ventas': 'Vendas',
        'Menú': 'Menu',
        'Productos': 'Produtos',
        'Clientes': 'Clientes',
        'Cotizaciones': 'Cotações',
        'Facturas': 'Faturas',
        'Proveedores': 'Fornecedores',
        'Almacenes': 'Armazéns',
        'Compras': 'Compras',
        'Reportes': 'Relatórios',
        'Usuarios': 'Usuários',
        'Dashboard': 'Painel',
        'Cerrar Sesión': 'Sair',
        'Idioma': 'Idioma',
        'Español': 'Espanhol',
        'English': 'Inglês',
        'Português': 'Português',
        # Ações comuns
        'Agregar': 'Adicionar',
        'Editar': 'Editar',
        'Eliminar': 'Excluir',
        'Guardar': 'Salvar',
        'Cancelar': 'Cancelar',
        'Buscar': 'Buscar',
        'Limpiar': 'Limpar',
        'Ver Detalles': 'Ver Detalhes',
        'Volver': 'Voltar',
        # Mensagens
        'Stock': 'Estoque',
        'Precio': 'Preço',
        'Categoría': 'Categoria',
        'Nombre': 'Nome',
        'Cantidad': 'Quantidade',
        'Total': 'Total',
        'Subtotal': 'Subtotal',
    },
}


def translate(text: str, language: str = None) -> str:
    """
    Traduce un texto al idioma actual o especificado
    
    Args:
        text: Texto a traducir
        language: Idioma destino (opcional, usa el idioma actual si no se especifica)
        
    Returns:
        str: Texto traducido o el texto original si no hay traducción
    """
    if language is None:
        language = get_language() or 'es'
    
    # Obtener solo el código base del idioma (ej: 'es' de 'es-es')
    lang_code = language.split('-')[0] if '-' in language else language
    
    # Obtener traducciones para el idioma
    translations = TRANSLATIONS.get(lang_code, TRANSLATIONS['es'])
    
    # Retornar traducción o texto original
    return translations.get(text, text)


def get_translations_dict(language: str = None) -> dict:
    """
    Obtiene el diccionario completo de traducciones para un idioma
    
    Args:
        language: Idioma (opcional, usa el idioma actual si no se especifica)
        
    Returns:
        dict: Diccionario de traducciones
    """
    if language is None:
        language = get_language() or 'es'
    
    lang_code = language.split('-')[0] if '-' in language else language
    return TRANSLATIONS.get(lang_code, TRANSLATIONS['es'])

