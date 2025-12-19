/**
 * Mejoras para el Punto de Venta (POS)
 * Atajos de teclado, modo rápido, y mejoras de UX
 */

(function() {
    'use strict';

    // Modo rápido (solo código de barras)
    let modoRapido = false;
    
    // Atajos de teclado para POS
    document.addEventListener('keydown', function(e) {
        // Solo en la página de POS
        if (!window.location.pathname.includes('/pos/')) {
            return;
        }
        
        const target = e.target;
        const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA';
        
        // Modo rápido: F1 para activar/desactivar
        if (e.key === 'F1') {
            e.preventDefault();
            toggleModoRapido();
            return;
        }
        
        // Si estamos en modo rápido y no es el input de código
        if (modoRapido && !target.id.includes('codigo-barras')) {
            if (e.key.length === 1 || e.key === 'Enter') {
                e.preventDefault();
                const codigoInput = document.getElementById('codigo-barras');
                if (codigoInput) {
                    codigoInput.focus();
                    if (e.key !== 'Enter') {
                        codigoInput.value = e.key;
                    }
                }
            }
        }
        
        // Atajos cuando no estamos escribiendo
        if (!isInput) {
            // F2: Limpiar carrito
            if (e.key === 'F2') {
                e.preventDefault();
                if (confirm('¿Limpiar carrito?')) {
                    limpiarCarrito();
                }
            }
            
            // F3: Procesar venta
            if (e.key === 'F3') {
                e.preventDefault();
                procesarVenta();
            }
            
            // F4: Focus en búsqueda de productos
            if (e.key === 'F4') {
                e.preventDefault();
                const searchInput = document.querySelector('input[type="text"][placeholder*="Buscar"]');
                if (searchInput) {
                    searchInput.focus();
                }
            }
            
            // F5: Focus en descuento
            if (e.key === 'F5') {
                e.preventDefault();
                const descuentoInput = document.getElementById('descuento');
                if (descuentoInput) {
                    descuentoInput.focus();
                    descuentoInput.select();
                }
            }
            
            // F6: Cambiar tipo de descuento
            if (e.key === 'F6') {
                e.preventDefault();
                toggleTipoDescuento();
            }
            
            // F7: Focus en monto recibido
            if (e.key === 'F7') {
                e.preventDefault();
                const montoInput = document.getElementById('monto-recibido');
                if (montoInput) {
                    montoInput.focus();
                    montoInput.select();
                }
            }
            
            // Escape: Limpiar input de código
            if (e.key === 'Escape') {
                const codigoInput = document.getElementById('codigo-barras');
                if (codigoInput) {
                    codigoInput.value = '';
                    codigoInput.focus();
                }
            }
        }
        
        // Atajos numéricos para métodos de pago
        if (e.ctrlKey && !isInput) {
            if (e.key === '1') {
                e.preventDefault();
                document.getElementById('metodo-pago').value = 'efectivo';
                calcularCambio();
            } else if (e.key === '2') {
                e.preventDefault();
                document.getElementById('metodo-pago').value = 'tarjeta';
                calcularCambio();
            } else if (e.key === '3') {
                e.preventDefault();
                document.getElementById('metodo-pago').value = 'transferencia';
                calcularCambio();
            }
        }
    });
    
    // Toggle modo rápido
    function toggleModoRapido() {
        modoRapido = !modoRapido;
        const codigoInput = document.getElementById('codigo-barras');
        
        if (modoRapido) {
            // Mostrar indicador visual
            showNotification('Modo Rápido Activado - Presiona F1 para desactivar', 'info');
            if (codigoInput) {
                codigoInput.focus();
            }
            // Ocultar sección de productos
            const productosSection = document.querySelector('.productos-section');
            if (productosSection) {
                productosSection.style.display = 'none';
            }
        } else {
            showNotification('Modo Rápido Desactivado', 'info');
            if (codigoInput) {
                codigoInput.blur();
            }
            // Mostrar sección de productos
            const productosSection = document.querySelector('.productos-section');
            if (productosSection) {
                productosSection.style.display = 'block';
            }
        }
    }
    
    // Toggle tipo de descuento
    function toggleTipoDescuento() {
        const fijoRadio = document.getElementById('descuento-fijo');
        const porcentajeRadio = document.getElementById('descuento-porcentaje');
        
        if (fijoRadio && porcentajeRadio) {
            if (fijoRadio.checked) {
                porcentajeRadio.checked = true;
            } else {
                fijoRadio.checked = true;
            }
            calcularTotal();
        }
    }
    
    // Mostrar notificación
    function showNotification(mensaje, tipo = 'info') {
        // Crear elemento de notificación
        const notification = document.createElement('div');
        notification.className = `alert alert-${tipo} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${mensaje}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remover después de 3 segundos
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    // Mejoras en el input de código de barras
    const codigoInput = document.getElementById('codigo-barras');
    if (codigoInput) {
        // Auto-focus al cargar
        codigoInput.focus();
        
        // Auto-buscar al presionar Enter
        codigoInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const codigo = this.value.trim();
                if (codigo) {
                    buscarProductoPorCodigo(codigo);
                    this.value = '';
                }
            }
        });
        
        // Limpiar después de buscar
        codigoInput.addEventListener('blur', function() {
            if (!modoRapido) {
                // No limpiar en modo rápido
            }
        });
    }
    
    // Función para buscar producto (debe existir en el template)
    function buscarProductoPorCodigo(codigo) {
        // Esta función debe estar definida en el template de POS
        if (typeof window.buscarProductoPorCodigo === 'function') {
            window.buscarProductoPorCodigo(codigo);
        }
    }
    
    // Mostrar ayuda de atajos
    function mostrarAyudaAtajos() {
        const ayuda = `
            <div class="modal fade" id="ayudaAtajosModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Atajos de Teclado - POS</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <table class="table">
                                <tr>
                                    <td><kbd>F1</kbd></td>
                                    <td>Activar/Desactivar Modo Rápido</td>
                                </tr>
                                <tr>
                                    <td><kbd>F2</kbd></td>
                                    <td>Limpiar Carrito</td>
                                </tr>
                                <tr>
                                    <td><kbd>F3</kbd></td>
                                    <td>Procesar Venta</td>
                                </tr>
                                <tr>
                                    <td><kbd>F4</kbd></td>
                                    <td>Buscar Producto</td>
                                </tr>
                                <tr>
                                    <td><kbd>F5</kbd></td>
                                    <td>Focus en Descuento</td>
                                </tr>
                                <tr>
                                    <td><kbd>F6</kbd></td>
                                    <td>Cambiar Tipo Descuento</td>
                                </tr>
                                <tr>
                                    <td><kbd>F7</kbd></td>
                                    <td>Focus en Monto Recibido</td>
                                </tr>
                                <tr>
                                    <td><kbd>Ctrl</kbd> + <kbd>1</kbd></td>
                                    <td>Método: Efectivo</td>
                                </tr>
                                <tr>
                                    <td><kbd>Ctrl</kbd> + <kbd>2</kbd></td>
                                    <td>Método: Tarjeta</td>
                                </tr>
                                <tr>
                                    <td><kbd>Ctrl</kbd> + <kbd>3</kbd></td>
                                    <td>Método: Transferencia</td>
                                </tr>
                                <tr>
                                    <td><kbd>Esc</kbd></td>
                                    <td>Limpiar Input Código</td>
                                </tr>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        if (!document.getElementById('ayudaAtajosModal')) {
            document.body.insertAdjacentHTML('beforeend', ayuda);
        }
        
        const modal = new bootstrap.Modal(document.getElementById('ayudaAtajosModal'));
        modal.show();
    }
    
    // Agregar botón de ayuda si estamos en POS
    if (window.location.pathname.includes('/pos/')) {
        // Crear botón flotante de ayuda
        const ayudaBtn = document.createElement('button');
        ayudaBtn.className = 'btn btn-info position-fixed';
        ayudaBtn.style.cssText = 'bottom: 20px; right: 20px; z-index: 1000; border-radius: 50%; width: 50px; height: 50px;';
        ayudaBtn.innerHTML = '<i class="bi bi-question-circle"></i>';
        ayudaBtn.title = 'Ayuda - Atajos de Teclado (F1)';
        ayudaBtn.onclick = mostrarAyudaAtajos;
        document.body.appendChild(ayudaBtn);
        
        // Atajo F1 para ayuda también
        document.addEventListener('keydown', function(e) {
            if (e.key === 'F1' && e.shiftKey) {
                e.preventDefault();
                mostrarAyudaAtajos();
            }
        });
    }
})();

