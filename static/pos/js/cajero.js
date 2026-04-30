// static/pos/js/cajero.js

// ============================================
// VARIABLES GLOBALES
// ============================================
let flatpickrInstance = null;
let ordenesPendientes = 0;
let interval = null;

// ============================================
// INICIALIZACIÓN
// ============================================

document.addEventListener('DOMContentLoaded', async function() {
    await cargarConfiguracion();
    await cargarFechaOperacion();
    iniciarAutoRefresh();
    cargarPendientes();

    const modal = document.getElementById('pagoModal');
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

    // =============================
    // 🔁 RECALCULAR
    // =============================
    function recalcularTodo() {

        const importeBase = parseFloat(
            document.getElementById('pagoImporteTotal')
            .textContent.replace('$', '').replace(',', '')
        ) || 0;

        let descuento = parseFloat(
            document.getElementById('pagoDescuentoPorcentaje').value
        ) || 0;

        const montoDescuento = (importeBase * descuento) / 100;
        const totalFinal = importeBase - montoDescuento;
        console.log("Total Final:", totalFinal);
        toast("Total Final:", totalFinal);

        // TOTAL
        const totalSpan = document.getElementById('pagoTotalAPagar');
        totalSpan.textContent = formatearPrecio(totalFinal);
        totalSpan.style.color = totalFinal < 0 ? '#dc3545' : '#16a34a';

        // DEVOLUCIÓN
        const formaPago = document.getElementById('pagoFormaPago').value;
        const monto = parseFloat(
            document.getElementById('pagoMontoEntregado').value
        ) || 0;

        const devolucionSpan = document.getElementById('pagoDevolucion');

        if (formaPago === 'efectivo') {
            const devolucion = monto - totalFinal;
            devolucionSpan.textContent = formatearPrecio(devolucion);
            devolucionSpan.style.color = devolucion < 0 ? '#dc3545' : '#16a34a';
        } else {
            devolucionSpan.textContent = formatearPrecio(0);
        }
    }

    // =============================
    // 🔌 BIND INPUTS
    // =============================
    function bindInput(id, config) {
        const el = document.getElementById(id);
        if (!el) return;

        el.addEventListener('input', function() {
            this.value = validarNumeroInput(this.value, config);
            recalcularTodo();
        });

        el.addEventListener('blur', function() {
            let num = parseFloat(this.value);
            this.value = !isNaN(num) ? num.toFixed(config.decimales || 2) : '';
        });
    }

    // =============================
    // 🎯 APLICAR A INPUTS
    // =============================
    bindInput('pagoDescuentoPorcentaje', { min: 0, max: 100, decimales: 2 });
    bindInput('pagoMontoEntregado', { min: 0, decimales: 2 });
    bindInput('pagoPropina', { min: 0, decimales: 2 });

    // Cambio forma de pago
    const formaPagoSelect = document.getElementById('pagoFormaPago');
    if (formaPagoSelect) {
        formaPagoSelect.addEventListener('change', function() {
            controlarVisibilidadPago();
            recalcularTodo();
        });
    }

});

function iniciarAutoRefresh(tiempo=30000) {  // tiempo en milisegundos
    if (interval) clearInterval(interval);
    interval = setInterval(() => {
        cargarPendientes();
    }, tiempo);
}

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
    console.log("📝 Actualizando modal con orden:", orden);

    const itemsContainer = document.getElementById('modalItemsList');
    const modalNumeroOrden = document.getElementById('modalNumeroOrden');
    const modalMesa = document.getElementById('modalMesa');
    const modalMesero = document.getElementById('modalMesero');
    const pagoImporteTotal = document.getElementById('pagoImporteTotal');
    const pagoDescuentoPorcentaje = document.getElementById('pagoDescuentoPorcentaje');
    const pagoTotalAPagar = document.getElementById('pagoTotalAPagar');

    if (modalNumeroOrden) modalNumeroOrden.innerText = orden.numero_orden || '?';
    if (modalMesa) modalMesa.innerText = orden.mesa_info?.numero || orden.mesa?.numero || '?';
    if (modalMesero) modalMesero.innerText = orden.usuario || '-';
    if (pagoImporteTotal) pagoImporteTotal.innerText = formatearPrecio(orden.importe_total) || '-';
    if (pagoTotalAPagar) pagoTotalAPagar.innerText = formatearPrecio(orden.total_apagar) || '-';
    if (pagoDescuentoPorcentaje) pagoDescuentoPorcentaje.value = orden.porc_descuento

    // Calcular totales
    const subtotal = orden.items ? orden.items.reduce((sum, item) => sum + (item.precio_unitario * item.cantidad), 0) : 0;
    const descuento = subtotal * (orden.porc_descuento || 0) / 100;
    const totalConDescuento = subtotal - descuento;
    const totalFinal = totalConDescuento + (orden.propina || 0);

    const modalSubtotal = document.getElementById('modalSubtotal');
    const modalDescuentoPorc = document.getElementById('modalDescuentoPorc');
    const modalDescuento = document.getElementById('modalDescuento');
    const modalPropina = document.getElementById('modalPropina');
    const modalTotal = document.getElementById('modalTotal');

    if (modalSubtotal) modalSubtotal.innerText = formatearPrecio(subtotal);
    if (modalDescuentoPorc) modalDescuentoPorc.innerText = orden.porc_descuento || 0;
    if (modalDescuento) modalDescuento.innerText = `-${formatearPrecio(descuento)}`;
    if (modalPropina) modalPropina.innerText = formatearPrecio(orden.propina || 0);
    if (modalTotal) modalTotal.innerText = formatearPrecio(totalFinal);

    // Actualizar inputs
    const descuentoInput = document.getElementById('descuentoInput');
    const propinaInput = document.getElementById('propinaInput');

    if (descuentoInput) descuentoInput.value = orden.porc_descuento || 0;
    if (propinaInput) propinaInput.value = orden.propina || 0;

}

async function verDetalleOrden(ordenId) {
    try {

        const orden = await abrirOrdenExistente(ordenId);
        if (!orden) return;

        ordenSeleccionada = orden;
        actualizarModalConOrden(orden);

        // ✅ Mostrar el modal correctamente
        const modal = document.getElementById('pagoModal');
        if (modal) {
            modal.style.display = 'flex';
        } else {
            console.error("❌ Modal no encontrado");
        }

    } catch (error) {
        console.error('❌ Error en verDetalleOrden:', error);
        toast("❌ Error al cargar detalle de la orden: " + error.message, "error");
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

            await cargarFechaOperacion();
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

function cerrarModal() {
    const modal = document.getElementById('pagoModal');

    if (modal) {

        cerrarOrden(ordenSeleccionada.id);
        modal.style.display = 'none';

        // ---- limpiar inputs ----
        document.getElementById('pagoDescuentoPorcentaje').value = '0.00';
        document.getElementById('pagoMontoEntregado').value = '0.00';
        document.getElementById('pagoPropina').value = '0.00';

        // ---- reset selects ----
        document.getElementById('pagoFormaPago').value = 'efectivo';

        // ---- reset totales ----
        document.getElementById('pagoTotalAPagar').textContent = '$0.00';
        document.getElementById('pagoDevolucion').textContent = '$0.00';

        // colores por defecto
        document.getElementById('pagoDevolucion').style.color = '#28a745';
        document.getElementById('pagoTotalAPagar').style.color = '#000';

        // ---- limpiar datos visuales ----
        document.getElementById('modalNumeroOrden').textContent = '';
        document.getElementById('modalMesa').textContent = '';
        document.getElementById('modalMesero').textContent = '';
        document.getElementById('pagoImporteTotal').textContent = '$0.00';
    }

    ordenSeleccionada = null;
}

function controlarVisibilidadPago() {
    const formaPago = document.getElementById('pagoFormaPago').value;
    const montoEntregadoGroup = document.getElementById('pagoMontoEntregadoGroup');
    const devolucionDiv = document.getElementById('pagoDevoluciondiv');

    if (formaPago === 'transferencia') {
        // Ocultar campos de efectivo
        if (montoEntregadoGroup) montoEntregadoGroup.style.display = 'none';
        if (devolucionDiv) devolucionDiv.style.display = 'none';

        // Limpiar valores de efectivo
        const montoEntregado = document.getElementById('pagoMontoEntregado');
        if (montoEntregado) montoEntregado.value = 0;

        // Restablecer texto de devolución
    } else {
        // Mostrar campos de efectivo
        if (montoEntregadoGroup) montoEntregadoGroup.style.display = 'block';
        if (devolucionDiv) devolucionDiv.style.display = 'block';
    }
}