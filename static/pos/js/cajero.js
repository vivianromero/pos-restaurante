// static/pos/js/cajero.js

// ============================================
// VARIABLES GLOBALES
// ============================================
let flatpickrInstance = null;
let ordenesPendientes = 0;

// ============================================
// INICIALIZACIÓN
// ============================================

document.addEventListener('DOMContentLoaded', async function() {
    await cargarConfiguracion();
    await cargarFechaOperacion();
    cargarPendientes();

    const efectivoInput = document.getElementById('efectivoInput');
    if (efectivoInput) {
        efectivoInput.addEventListener('input', function() {
            const total = ordenSeleccionada?.importe_total || 0;
            const efectivo = parseFloat(this.value) || 0;
            const cambio = efectivo - total;
            const cambioInfo = document.getElementById('cambioInfo');

            if (cambioInfo) {
                if (cambio >= 0) {
                    cambioInfo.innerHTML = `💵 Cambio: ${formatearPrecio(cambio)}`;
                    cambioInfo.style.color = '#2e7d32';
                } else {
                    cambioInfo.innerHTML = `⚠️ Faltante: ${formatearPrecio(-cambio)}`;
                    cambioInfo.style.color = '#f44336';
                }
            }
        });
    }

    const formaPagoSelect = document.getElementById('formaPagoSelect');
    const efectivoSection = document.getElementById('efectivoSection');

    if (formaPagoSelect && efectivoSection) {
        formaPagoSelect.addEventListener('change', function() {
            efectivoSection.style.display = this.value === '1' ? 'flex' : 'none';
        });
    }

    const modal = document.getElementById('ordenModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) cerrarModal();
        });
    }

    const confirmModal = document.getElementById('confirmModal');
    if (confirmModal) {
        confirmModal.addEventListener('click', function(e) {
            if (e.target === confirmModal) cerrarConfirmModal();
        });
    }
});


async function cargarPendientes() {
    try {
        mostrarLoading('ordenesGrid', 'órdenes pendientes');

        const params = new URLSearchParams();
        params.append('estado_label', 'pendientepago');
        params.append('include_items', 'true');

        if (fecha_operacion) {
            params.append('fecha', fecha_operacion);
        }

        const url = `/api/ordenes/?${params.toString()}`;
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin'
        });

        if (!response.ok) throw new Error(`Error ${response.status}`);

        const data = await response.json();

        renderOrdenes(data);
        cargarResumen();

    } catch (error) {
        console.error('❌ Error:', error);
        mostrarError();
    }
}

async function cargarResumen() {
    try {
        const response = await fetch('/api/cajero/resumen/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin'
        });

        if (!response.ok) throw new Error(`Error ${response.status}`);

        const data = await response.json();

        document.getElementById('pendientesCount').innerText = data.cantidad || 0;
        document.getElementById('totalPendiente').innerText = formatearPrecio(data.total_pendiente || 0);

    } catch (error) {
        console.error('Error cargando resumen:', error);
    }
}

// ============================================
// FUNCIONES DE RENDERIZADO
// ============================================

function renderOrdenes(data) {
    const container = document.getElementById('ordenesGrid');

    // Determinar si es respuesta paginada o array directo
    let ordenes = [];
    let total = 0;

    if (data && data.results) {
        // Respuesta paginada (con paginación)
        ordenes = data.results;
        total = data.count || 0;
    } else if (Array.isArray(data)) {
        // Respuesta directa (sin paginación)
        ordenes = data;
        total = data.length;
    } else {
        console.error("Formato de respuesta no reconocido:", data);
        ordenes = [];
        total = 0;
    }

    if (!ordenes || ordenes.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="icon">💰</div>
                <p>No hay órdenes pendientes de pago</p>
                <small>Todas las órdenes han sido pagadas</small>
            </div>
        `;
        return;
    }

    container.innerHTML = ordenes.map(orden => `
        <div class="orden-card" onclick="verDetalleOrden('${orden.id}')">
            <div class="orden-header">
                <span class="orden-numero">Orden #${orden.numero_orden}</span>
                <span class="orden-mesa">Mesa ${orden.mesa_info?.numero || orden.mesa?.numero || '?'}</span>
            </div>
            <div class="orden-body">
                <ul class="orden-items">
                    ${(orden.items || []).map(item => `
                        <li>
                            <span class="item-nombre">${item.producto_nombre}</span>
                            <span class="item-cantidad">x${item.cantidad}</span>
                            <span class="item-precio">${formatearPrecio(item.precio_unitario * item.cantidad)}</span>
                        </li>
                    `).join('')}
                </ul>
            </div>
            <div class="orden-footer">
                <span class="orden-total">Total: ${formatearPrecio(orden.importe_total)}</span>
                <span class="orden-pendiente">💰 Pendiente</span>
            </div>
        </div>
    `).join('');
}

function actualizarModalConOrden(orden) {
    const itemsContainer = document.getElementById('modalItemsList');

    if (itemsContainer) {
        itemsContainer.innerHTML = orden.items.map(item => `
            <li>
                <span class="item-nombre">${item.producto_nombre} x${item.cantidad}</span>
                <span class="item-precio">${formatearPrecio(item.precio_unitario * item.cantidad)}</span>
            </li>
        `).join('');
    }

    document.getElementById('modalNumeroOrden').innerText = orden.numero_orden;
    document.getElementById('modalMesa').innerText = orden.mesa_info?.numero || '?';
    document.getElementById('modalMesero').innerText = orden.usuario || '-';

    const subtotal = orden.items.reduce((sum, item) => sum + (item.precio_unitario * item.cantidad), 0);
    const descuento = subtotal * (orden.porc_descuento || 0) / 100;
    const totalConDescuento = subtotal - descuento;
    const totalFinal = totalConDescuento + (orden.propina || 0);

    document.getElementById('modalSubtotal').innerText = formatearPrecio(subtotal);
    document.getElementById('modalDescuentoPorc').innerText = orden.porc_descuento || 0;
    document.getElementById('modalDescuento').innerText = `-${formatearPrecio(descuento)}`;
    document.getElementById('modalPropina').innerText = formatearPrecio(orden.propina || 0);
    document.getElementById('modalTotal').innerText = formatearPrecio(totalFinal);

    document.getElementById('descuentoInput').value = orden.porc_descuento || 0;
    document.getElementById('propinaInput').value = orden.propina || 0;
    document.getElementById('efectivoInput').value = orden.importe_total || 0;
}

async function verDetalleOrden(ordenId) {
    try {
        const response = await fetch(`/api/cajero/${ordenId}/`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin'
        });

        if (!response.ok) throw new Error(`Error ${response.status}`);

        const orden = await response.json();

        ordenSeleccionada = orden;
        actualizarModalConOrden(orden);

        mostrarModal();

    } catch (error) {
        console.error('Error:', error);
        toast("❌ Error al cargar detalle de la orden", "error");
    }
}

function mostrarError() {
    const container = document.getElementById('ordenesGrid');
    if (container) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="icon">❌</div>
                <p>Error al cargar las órdenes</p>
                <button onclick="cargarPendientes()" style="margin-top: 10px; padding: 8px 20px; background: #1a472a; color: white; border: none; border-radius: 20px; cursor: pointer;">Reintentar</button>
            </div>
        `;
    }
}

// ============================================
// FUNCIONES PARA MODAL DE FECHA
// ============================================

async function abrirFechaModal() {
    // Primero verificar si se puede cambiar la fecha
    const puedeCambiar = await verificarPuedeCambiarFecha();

    if (!puedeCambiar) {
        console.log("No se puede cambiar la fecha");
        return;
    }

    // Si se puede cambiar, abrir el modal para seleccionar fecha
    const modal = document.getElementById('fechaModal');
    const fechaInput = fecha_operacion_formateada;
    const modalFechaInput = document.getElementById('fechaModalInput');

    if (modal && fechaInput) {
        // Establecer la fecha actual en el input del modal
        if (fechaInput.innerText && modalFechaInput) {
            // Convertir DD/MM/YYYY a formato para flatpickr
            const partes = fechaInput.innerText.split('/');
            if (partes.length === 3) {
                modalFechaInput.value = `${partes[2]}/${partes[1]}/${partes[0]}`;
            }
        }
        modal.style.display = 'flex';

        setTimeout(() => {
            if (modalFechaInput && !flatpickrInstance) {
                flatpickrInstance = flatpickr(modalFechaInput, {
                    dateFormat: "d/m/Y",
                    locale: "es",
                    allowInput: false,
                    onChange: function(selectedDates, dateStr) {
                        console.log("Fecha seleccionada:", dateStr);
                    }
                });
            }
            if (flatpickrInstance) {
                flatpickrInstance.open();
            }
        }, 100);
    }
}

function cerrarFechaModal() {
    const modal = document.getElementById('fechaModal');
    if (modal) {
        modal.style.display = 'none';
    }
    if (flatpickrInstance) {
        flatpickrInstance.destroy();
        flatpickrInstance = null;
    }
}

async function confirmarCambioFecha() {
    const modalFechaInput = document.getElementById('fechaModalInput');
    const fechaStr = modalFechaInput?.value;

    if (!fechaStr) {
        toast("❌ Seleccione una fecha válida", "error");
        return;
    }

    const regex = /^(\d{2})\/(\d{2})\/(\d{4})$/;
    const match = fechaStr.match(regex);

    if (!match) {
        toast("❌ Formato inválido", "error");
        return;
    }

    const dia = match[1];
    const mes = match[2];
    const año = match[3];
    const nuevaFecha = `${año}-${mes}-${dia}`;

    cerrarFechaModal();

    const confirmar = await window.mostrarModal({
        title: '📅 Cambiar fecha de operación',
        message: `¿Está seguroooo de que desea cambiar la fecha de operación a <strong>${fechaStr}</strong>?`,
        confirmText: 'Sí, cambiar fecha',
        cancelText: 'Cancelar'
    });

    if (!confirmar) return;

    enviarCambioFecha(nuevaFecha, fechaStr);
}

async function enviarCambioFecha(nuevaFecha, fechaFormateada) {
    try {
        const response = await fetch('/api/cajero/cambiar-fecha/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin',
            body: JSON.stringify({ fecha: nuevaFecha })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            toast(`✅ Fecha cambiada a ${fechaFormateada}`);
            document.getElementById('fechaOperacion').innerText = fechaFormateada;

            cargarPendientes();
            cargarResumen();
        } else {
            toast(`❌ ${data.error || 'Error al cambiar fecha'}`, "error");
        }

    } catch (error) {
        console.error("Error:", error);
        toast("❌ Error al cambiar la fecha", "error");
    }
}

// ============================================
// FUNCIONES DE PAGO
// ============================================

async function aplicarDescuento() {
    if (!ordenSeleccionada) return;

    const porcentaje = document.getElementById('descuentoInput')?.value;

    if (!porcentaje || porcentaje < 0 || porcentaje > 100) {
        toast("❌ Ingrese un porcentaje válido (0-100)", "error");
        return;
    }

    try {
        const response = await fetch(`/api/cajero/${ordenSeleccionada.id}/aplicar-descuento/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin',
            body: JSON.stringify({ porcentaje: parseFloat(porcentaje) })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            toast(`✅ Descuento del ${porcentaje}% aplicado`);
            actualizarModalConOrden(data.data);
            cargarPendientes();
        } else {
            toast(`❌ ${data.error || 'Error al aplicar descuento'}`, "error");
        }

    } catch (error) {
        console.error("Error:", error);
        toast("❌ Error al aplicar descuento", "error");
    }
}

async function registrarPago() {
    if (!ordenSeleccionada) return;

    const formaPago = document.getElementById('formaPagoSelect')?.value;
    let efectivoEntregado = document.getElementById('efectivoInput')?.value || 0;
    let propina = document.getElementById('propinaInput')?.value || 0;

    if (!formaPago) {
        toast("❌ Seleccione una forma de pago", "error");
        return;
    }

    const data = {
        forma_pago: parseInt(formaPago),
        propina: parseFloat(propina) || 0
    };

    if (data.forma_pago === 1) {
        if (!efectivoEntregado || efectivoEntregado < ordenSeleccionada.importe_total) {
            const faltante = ordenSeleccionada.importe_total - (efectivoEntregado || 0);
            toast(`❌ Efectivo insuficiente. Faltan ${formatearPrecio(faltante)}`, "error");
            return;
        }
        data.efectivo_entregado = parseFloat(efectivoEntregado);
    }

    try {
        const response = await fetch(`/api/cajero/${ordenSeleccionada.id}/registrar-pago/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin',
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok && result.success) {
            let mensaje = `✅ Orden pagada correctamente`;
            if (result.cambio && result.cambio > 0) {
                mensaje += ` - Cambio: ${formatearPrecio(result.cambio)}`;
            }
            toast(mensaje);
            cerrarModal();
            cargarPendientes();
        } else {
            toast(`❌ ${result.error || 'Error al procesar pago'}`, "error");
        }

    } catch (error) {
        console.error("Error:", error);
        toast("❌ Error al procesar pago", "error");
    }
}

// Función de confirmación mejorada
async function mostrarConfirmModal(mensaje, cambio = null, soloConfirmacion = false) {
    return new Promise((resolve) => {
        const modal = document.getElementById('confirmModal');
        if (!modal) {
            resolve(false);
            return;
        }

        document.getElementById('confirmMessage').innerHTML = mensaje.replace(/\n/g, '<br>');

        const cambioElement = document.getElementById('cambioMessage');
        if (cambio !== null) {
            cambioElement.innerHTML = `💰 Cambio: ${formatearPrecio(cambio)}`;
            cambioElement.style.display = 'block';
        } else {
            cambioElement.style.display = 'none';
        }

        // Ocultar el campo de cambio si es solo confirmación
        if (soloConfirmacion && cambioElement) {
            cambioElement.style.display = 'none';
        }

        modal.style.display = 'flex';

        const confirmBtn = document.getElementById('confirmPagoBtn');
        const handleConfirm = () => {
            modal.style.display = 'none';
            confirmBtn.removeEventListener('click', handleConfirm);
            resolve(true);
        };

        const handleCancel = () => {
            modal.style.display = 'none';
            confirmBtn.removeEventListener('click', handleCancel);
            resolve(false);
        };

        confirmBtn.removeEventListener('click', handleConfirm);
        confirmBtn.addEventListener('click', handleConfirm);

        document.querySelector('#confirmModal .btn-cancelar').onclick = handleCancel;
    });
}

async function verificarPuedeCambiarFecha() {
    try {

        const params = new URLSearchParams();

        params.append('fecha', fecha_operacion);
        params.append('estado_diferente', 'pagada');

        const url = `/api/ordenes/?${params.toString()}`;

        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin'
        });

        if (!response.ok) throw new Error('Error al verificar fecha');

        const data = await response.json();

        ordenesPendientes = data.count || 0;
        fechaActualStr = fecha_operacion_formateada;

        if (ordenesPendientes > 0) {
            // Mostrar mensaje de que no se puede cambiar
            const confirmar = await mostrarConfirmModal(
                `❌ No se puede cambiar la fecha de operación.\n\n` +
                `Hay ${ordenesPendientes} orden(es) pendiente(s) de pago en la fecha actual (${fechaActualStr}).\n\n` +
                `Debe procesar todas las órdenes pendientes antes de cambiar la fecha.`,
                null,
                true
            );
            return false;
        }
        return true;

    } catch (error) {
        toast(`❌ ${data.message}`, "error")
        return false;
    }
}
