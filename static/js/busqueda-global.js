/**
 * Funcionalidad de búsqueda global mejorada
 * Atajo Ctrl+K para búsqueda rápida
 */

(function() {
    'use strict';

    // Modal de búsqueda rápida
    let searchModal = null;
    let searchInput = null;
    let resultsContainer = null;
    let searchTimeout = null;

    // Crear modal de búsqueda rápida
    function createSearchModal() {
        const modalHTML = `
            <div class="modal fade" id="searchModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="bi bi-search"></i> Búsqueda Global
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <input type="text" 
                                       class="form-control form-control-lg" 
                                       id="quickSearchInput" 
                                       placeholder="Buscar productos, clientes, ventas, cotizaciones..."
                                       autocomplete="off">
                                <small class="text-muted">Escribe para buscar en todos los módulos</small>
                            </div>
                            <div id="quickSearchResults" class="mt-3">
                                <p class="text-muted text-center">Escribe para comenzar a buscar...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Agregar modal al body si no existe
        if (!document.getElementById('searchModal')) {
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        }
        
        searchModal = new bootstrap.Modal(document.getElementById('searchModal'));
        searchInput = document.getElementById('quickSearchInput');
        resultsContainer = document.getElementById('quickSearchResults');
        
        // Event listeners
        searchInput.addEventListener('input', handleSearchInput);
        searchInput.addEventListener('keydown', handleSearchKeydown);
        
        // Focus al abrir
        document.getElementById('searchModal').addEventListener('shown.bs.modal', function() {
            searchInput.focus();
        });
    }

    // Manejar input de búsqueda
    function handleSearchInput(e) {
        const query = e.target.value.trim();
        
        // Limpiar timeout anterior
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }
        
        if (query.length < 2) {
            resultsContainer.innerHTML = '<p class="text-muted text-center">Escribe al menos 2 caracteres...</p>';
            return;
        }
        
        // Debounce: esperar 300ms antes de buscar
        searchTimeout = setTimeout(() => {
            performSearch(query);
        }, 300);
    }

    // Realizar búsqueda
    function performSearch(query) {
        resultsContainer.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div><p class="mt-2">Buscando...</p></div>';
        
        fetch(`/api/busqueda-global/?q=${encodeURIComponent(query)}&tipo=todos`)
            .then(response => response.json())
            .then(data => {
                displayResults(data.resultados || []);
            })
            .catch(error => {
                console.error('Error en búsqueda:', error);
                resultsContainer.innerHTML = '<div class="alert alert-danger">Error al realizar la búsqueda</div>';
            });
    }

    // Mostrar resultados
    function displayResults(resultados) {
        if (resultados.length === 0) {
            resultsContainer.innerHTML = '<p class="text-muted text-center">No se encontraron resultados</p>';
            return;
        }
        
        let html = '<div class="list-group">';
        
        resultados.forEach(item => {
            const iconClass = getIconForType(item.tipo);
            html += `
                <a href="${item.url}" class="list-group-item list-group-item-action">
                    <div class="d-flex align-items-center">
                        <i class="${iconClass} me-3 fs-4"></i>
                        <div class="flex-grow-1">
                            <h6 class="mb-1">${item.texto}</h6>
                            <small class="text-muted">${item.subtitulo || ''}</small>
                        </div>
                        <i class="bi bi-arrow-right"></i>
                    </div>
                </a>
            `;
        });
        
        html += '</div>';
        resultsContainer.innerHTML = html;
    }

    // Obtener icono según tipo
    function getIconForType(tipo) {
        const icons = {
            'producto': 'bi bi-box-seam text-primary',
            'cliente': 'bi bi-person text-success',
            'venta': 'bi bi-receipt text-info',
            'cotizacion': 'bi bi-file-earmark-text text-warning'
        };
        return icons[tipo] || 'bi bi-circle';
    }

    // Manejar teclas en búsqueda
    function handleSearchKeydown(e) {
        // Enter: ir al primer resultado
        if (e.key === 'Enter') {
            const firstResult = resultsContainer.querySelector('a');
            if (firstResult) {
                window.location.href = firstResult.href;
            }
        }
        // Escape: cerrar modal
        if (e.key === 'Escape') {
            searchModal.hide();
        }
    }

    // Atajo Ctrl+K
    document.addEventListener('keydown', function(e) {
        // Ctrl+K o Cmd+K (Mac)
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            
            // No abrir si estamos en un input o textarea
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
            
            // Crear modal si no existe
            if (!searchModal) {
                createSearchModal();
            }
            
            // Abrir modal
            searchModal.show();
        }
    });

    // Inicializar al cargar
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createSearchModal);
    } else {
        createSearchModal();
    }
})();

