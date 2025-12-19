/**
 * Dashboard personalizable con drag & drop
 */
(function() {
    let isPersonalizando = false;
    let sortableInstance = null;

    function initSortable() {
        const container = document.getElementById('dashboard-widgets');
        if (!container) return;

        // Usar SortableJS si está disponible, sino usar HTML5 drag & drop nativo
        if (typeof Sortable !== 'undefined') {
            sortableInstance = new Sortable(container, {
                animation: 150,
                handle: '.dashboard-widget',
                ghostClass: 'sortable-ghost',
                chosenClass: 'sortable-chosen',
                dragClass: 'sortable-drag',
                onEnd: function(evt) {
                    guardarOrden();
                }
            });
        } else {
            // Fallback a HTML5 drag & drop nativo
            initNativeDragDrop(container);
        }
    }

    function initNativeDragDrop(container) {
        const widgets = container.querySelectorAll('.dashboard-widget');
        let draggedElement = null;

        widgets.forEach(widget => {
            widget.draggable = true;
            
            widget.addEventListener('dragstart', function(e) {
                draggedElement = this;
                this.style.opacity = '0.5';
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('text/html', this.innerHTML);
            });

            widget.addEventListener('dragend', function(e) {
                this.style.opacity = '1';
                widgets.forEach(w => {
                    w.classList.remove('drag-over');
                });
            });

            widget.addEventListener('dragover', function(e) {
                if (e.preventDefault) {
                    e.preventDefault();
                }
                e.dataTransfer.dropEffect = 'move';
                this.classList.add('drag-over');
                return false;
            });

            widget.addEventListener('dragleave', function(e) {
                this.classList.remove('drag-over');
            });

            widget.addEventListener('drop', function(e) {
                if (e.stopPropagation) {
                    e.stopPropagation();
                }

                if (draggedElement !== this) {
                    const allWidgets = Array.from(container.querySelectorAll('.dashboard-widget'));
                    const draggedIndex = allWidgets.indexOf(draggedElement);
                    const targetIndex = allWidgets.indexOf(this);

                    if (draggedIndex < targetIndex) {
                        container.insertBefore(draggedElement, this.nextSibling);
                    } else {
                        container.insertBefore(draggedElement, this);
                    }
                    
                    guardarOrden();
                }

                this.classList.remove('drag-over');
                return false;
            });
        });
    }

    function guardarOrden() {
        const widgets = document.querySelectorAll('#dashboard-widgets .dashboard-widget');
        const orden = Array.from(widgets).map(w => w.getAttribute('data-widget-id'));
        
        // Guardar en localStorage
        localStorage.setItem('dashboard_widgets_order', JSON.stringify(orden));
        
        // Opcional: Guardar en servidor
        fetch('/dashboard/guardar-orden/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ orden: orden })
        }).catch(err => console.log('Error al guardar orden:', err));
    }

    function cargarOrden() {
        const ordenGuardado = localStorage.getItem('dashboard_widgets_order');
        if (!ordenGuardado) return;

        try {
            const orden = JSON.parse(ordenGuardado);
            const container = document.getElementById('dashboard-widgets');
            if (!container) return;

            const widgets = Array.from(container.querySelectorAll('.dashboard-widget'));
            const widgetMap = new Map(widgets.map(w => [w.getAttribute('data-widget-id'), w]));

            orden.forEach(widgetId => {
                const widget = widgetMap.get(widgetId);
                if (widget) {
                    container.appendChild(widget);
                }
            });
        } catch (e) {
            console.error('Error al cargar orden:', e);
        }
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    window.togglePersonalizacion = function() {
        isPersonalizando = !isPersonalizando;
        const widgets = document.querySelectorAll('.dashboard-widget');
        const btnPersonalizar = document.getElementById('btn-personalizar-dashboard');
        
        widgets.forEach(widget => {
            const btnOcultar = widget.querySelector('button[onclick*="ocultarWidget"]');
            if (btnOcultar) {
                if (isPersonalizando) {
                    btnOcultar.classList.remove('d-none');
                    widget.style.cursor = 'move';
                    widget.classList.add('personalizando');
                } else {
                    btnOcultar.classList.add('d-none');
                    widget.style.cursor = 'default';
                    widget.classList.remove('personalizando');
                }
            }
        });

        if (btnPersonalizar) {
            if (isPersonalizando) {
                btnPersonalizar.classList.remove('btn-outline-primary');
                btnPersonalizar.classList.add('btn-primary');
                btnPersonalizar.innerHTML = '<i class="bi bi-check-circle"></i> Guardar';
            } else {
                btnPersonalizar.classList.remove('btn-primary');
                btnPersonalizar.classList.add('btn-outline-primary');
                btnPersonalizar.innerHTML = '<i class="bi bi-layout-three-columns"></i> Personalizar';
            }
        }
    };

    window.ocultarWidget = function(widgetId) {
        const widget = document.querySelector(`[data-widget-id="${widgetId}"]`);
        if (widget) {
            widget.style.display = 'none';
            const ordenGuardado = localStorage.getItem('dashboard_widgets_hidden') || '[]';
            const hidden = JSON.parse(ordenGuardado);
            if (!hidden.includes(widgetId)) {
                hidden.push(widgetId);
                localStorage.setItem('dashboard_widgets_hidden', JSON.stringify(hidden));
            }
        }
    };

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            cargarOrden();
            initSortable();
        });
    } else {
        cargarOrden();
        initSortable();
    }
})();

