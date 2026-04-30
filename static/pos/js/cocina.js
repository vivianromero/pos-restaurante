// static/pos/js/cocina.js

let pedidoSeleccionado = null;

// Inicializar
document.addEventListener('DOMContentLoaded', async function() {
    await cargarConfiguracion();
    await cargarFechaOperacion();

    cargarPedidos();
    iniciarAutoRefresh();
});

async function cargarPedidos() {
    try {
        mostrarLoading('pedidosGrid', 'pedidos');

        const response = await fetch('/api/cocina/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin'
        });

        if (!response.ok) throw new Error(`Error ${response.status}`);

        const pedidos = await response.json();
        renderPedidos(pedidos);
        cargarResumen();


    } catch (error) {
        console.error('❌ Error:', error);
        mostrarError();
    }
}

// Cargar resumen (contadores)
async function cargarResumen() {
    try {
        const response = await fetch('/api/cocina/resumen/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin'
        });

        if (!response.ok) throw new Error(`Error ${response.status}`);

        const data = await response.json();

        document.getElementById('pendientesCount').innerText = data.pendientes || 0;
        document.getElementById('procesandoCount').innerText = data.procesando || 0;
        document.getElementById('servidasCount').innerText = data.servidas || 0;

    } catch (error) {
        console.error('Error cargando resumen:', error);
    }
}

// Renderizar pedidos con botones según estado
function renderPedidos(pedidos) {
    const container = document.getElementById('pedidosGrid');
    // ✅ Verificar que pedidos es un array
    console.log(pedidos);
     const listaPedidos = pedidos.results || pedidos;

    // ✅ Verificar que listaPedidos es un array
    if (!listaPedidos || !Array.isArray(listaPedidos) || listaPedidos.length === 0) {
        container.innerHTML = '<div class="empty-state">🍽️ No hay pedidos pendientes</div>';
        return;
    }
    container.innerHTML = listaPedidos.map(pedido => {
        // Obtener número de mesa correctamente
        const numeroMesa = pedido.mesa_info?.numero || pedido.mesa?.numero || '?';

        // Obtener nombre del usuario
        const nombreUsuario = pedido.usuario_name || pedido.usuario?.username || 'Mesero';

        // Determinar qué botón mostrar según el estado
        let botones = '';

        if (pedido.estado === 1) { // PENDIENTE
            botones = `
                <button class="btn-procesar" onclick="iniciarPreparacion('${pedido.id}')">
                    🍳 Procesar
                </button>
            `;
        } else if (pedido.estado === 2) { // PROCESANDO
            botones = `
                <button class="btn-servir" onclick="servirPedido('${pedido.id}')">
                    ✅ Servir
                </button>
            `;
        } else {
            botones = `<span class="estado-finalizado">✓ Finalizado</span>`;
        }

        return `
            <div class="pedido-card" data-id="${pedido.id}" data-estado="${pedido.estado}" onclick="abrirModalPago('${pedido.id}')">
                <div class="pedido-header">
                    <div class="pedido-header-row">
                        <div class="pedido-numero-wrapper">
                            <span class="carrito-emoji">🛒</span>
                            <span class="pedido-numero">#${pedido.numero_orden}</span>
                        </div>
                        <span class="pedido-mesa">Mesa ${numeroMesa}</span>
                    </div>
                    <div class="pedido-header-row">
                        <span class="pedido-usuario">${nombreUsuario}</span>
                        <span class="pedido-estado estado-${pedido.estado}">${pedido.estado_label || getEstadoLabel(pedido.estado)}</span>
                    </div>
                </div>
                <div class="linea-head"></div>
                <div class="pedido-body">
                    <ul class="pedido-items">
                        ${(pedido.items || []).map(item => `
                            <li>
                                <span class="item-nombre">${item.producto_nombre}</span>
                                <span class="item-cantidad">x ${item.cantidad}</span>
                                <span class="item-precio">${formatearPrecio(item.precio_unitario * item.cantidad)}</span>
                            </li>
                        `).join('')}
                    </ul>
                </div>
                <div class="pedido-footer">
                    <div class="total-wrapper">
                        <span class="total-label">TOTAL</span>
                        <span class="pedido-total">${formatearPrecio(pedido.importe_total)}</span>
                    </div>
                    <div class="acciones-wrapper">
                        ${botones}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function getEstadoLabel(estado) {
    const estados = {
        1: '⏳ Pendiente',
        2: '🍳 En preparación',
        3: '✅ Servida',
        4: '💰 Pendiente pago',
        5: '✔️ Pagada'
    };
    return estados[estado] || 'Desconocido';
}

// Iniciar preparación (PENDIENTE → PROCESANDO)
async function iniciarPreparacion(pedidoId) {
    try {
        const response = await fetch(`/api/cocina/${pedidoId}/iniciar/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin'
        });

        const data = await response.json();

        if (response.ok && data.success) {
            toast(data.message);
            cargarPedidos();  // Recargar lista
            cargarResumen();   // Actualizar contadores
        } else {
            toast(`${data.error || 'Error al iniciar preparación'}`, tipo='error');
        }

    } catch (error) {
        console.error('Error:', error);
        toast('Error al conectar con el servidor', tipo='error');
    }
}

// Marcar como servido (PROCESANDO → SERVIDA)
async function servirPedido(pedidoId) {
    try {
        const response = await fetch(`/api/cocina/${pedidoId}/servir/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin'
        });

        const data = await response.json();

        if (response.ok && data.success) {
            toast(data.message);
            cargarPedidos();  // Recargar lista
            cargarResumen();   // Actualizar contadores
        } else {
            toast(`${data.error || 'Error al marcar como servido'}`, tipo='error');
        }

    } catch (error) {
        console.error('Error:', error);
        toast('Error al conectar con el servidor', tipo='error');
    }
}

// Mostrar error
function mostrarError() {
    const container = document.getElementById('pedidosGrid');
    container.innerHTML = `
        <div class="empty-state">
            <p>❌ Error al cargar pedidos</p>
            <button onclick="cargarPedidos()" style="margin-top: 10px; padding: 8px 20px;">Reintentar</button>
        </div>
    `;
}


let intervalId = null;

function iniciarAutoRefresh(tiempo=30000) {  // tiempo en milisegundos
    if (intervalId) clearInterval(intervalId);
    intervalId = setInterval(() => {
        cargarPedidos();
    }, tiempo);
}


function detenerAutoRefresh() {
    if (intervalId) {
        clearInterval(intervalId);
        intervalId = null;
    }
}

window.addEventListener('beforeunload', function() {
    detenerAutoRefresh();
});