// Gestión de Modo Oscuro
(function() {
    // Cargar preferencia guardada
    const darkModePreference = localStorage.getItem('darkMode');
    const isDarkMode = darkModePreference === 'true';
    
    // Aplicar modo oscuro si está guardado
    if (isDarkMode) {
        enableDarkMode();
    }
    
    // Toggle del botón
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function() {
            const body = document.body;
            const isDark = body.classList.contains('dark-mode');
            
            if (isDark) {
                disableDarkMode();
            } else {
                enableDarkMode();
            }
        });
    }
    
    function enableDarkMode() {
        document.body.classList.add('dark-mode');
        document.body.classList.remove('light-mode');
        const stylesheet = document.getElementById('dark-mode-stylesheet');
        if (stylesheet) {
            stylesheet.disabled = false;
        }
        const icon = document.getElementById('dark-mode-icon');
        if (icon) {
            icon.className = 'bi bi-sun';
        }
        localStorage.setItem('darkMode', 'true');
    }
    
    function disableDarkMode() {
        document.body.classList.remove('dark-mode');
        document.body.classList.add('light-mode');
        const stylesheet = document.getElementById('dark-mode-stylesheet');
        if (stylesheet) {
            stylesheet.disabled = true;
        }
        const icon = document.getElementById('dark-mode-icon');
        if (icon) {
            icon.className = 'bi bi-moon-stars';
        }
        localStorage.setItem('darkMode', 'false');
    }
})();

// Búsqueda Rápida por Código de Barras (Atajo F)
(function() {
    document.addEventListener('keydown', function(e) {
        // Presionar F para búsqueda rápida (solo si no está escribiendo en un input)
        if (e.key === 'f' || e.key === 'F') {
            const activeElement = document.activeElement;
            const isInput = activeElement.tagName === 'INPUT' || 
                          activeElement.tagName === 'TEXTAREA' ||
                          activeElement.contentEditable === 'true';
            
            if (!isInput) {
                e.preventDefault();
                const searchInput = document.getElementById('search-input');
                if (searchInput) {
                    searchInput.focus();
                    searchInput.select();
                }
            }
        }
    });
})();

