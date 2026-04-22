// static/pos/js/mesas.js

function renderMesas(mesasData) {
    const container = document.getElementById('mesasGrid');

    if (!mesasData || mesasData.length === 0) {
        container.innerHTML = '<div class="empty-state">🍽️ No hay mesas disponibles</div>';
        return;
    }

    container.innerHTML = mesasData.map(m => {
        // Acceder correctamente a los datos del estado
        const estado = m.estado;
        const ocupada = estado.ocupada;
        const esMiMesa = estado.es_mi_mesa;

        let claseExtra = '';
        let mensaje = '';
        let puedeSeleccionar = false;

        if (!ocupada) {
            claseExtra = 'libre';
            mensaje = '🟢 Libre';
            puedeSeleccionar = true;
        } else if (esMiMesa) {
            claseExtra = 'mi-mesa';
            mensaje = `🟡 ${estado.estado_orden} - #${estado.numero_orden}`;
            puedeSeleccionar = true;
        } else {
            claseExtra = 'ocupada-otro';
            mensaje = `🔴 Ocupada por ${estado.usuario_orden}`;
            puedeSeleccionar = false;
        }

        return `
            <div class="mesa-card ${claseExtra}"
                 data-id="${m.id}"
                 data-numero="${m.numero}"
                 data-ocupada="${ocupada}"
                 data-es-mi-mesa="${esMiMesa}"
                 data-order-id="${estado.order_id || ''}"
                 data-puede-seleccionar="${puedeSeleccionar}">
                <div class="mesa-numero-grande">${m.numero}</div>
                <div class="mesa-estado">${mensaje}</div>
                ${estado.numero_orden && esMiMesa ? `<div class="mesa-orden-info">Orden: ${estado.numero_orden}</div>` : ''}
            </div>
        `;
    }).join('');

    // Evento de click
    document.querySelectorAll('.mesa-card').forEach(card => {
        card.addEventListener('click', () => {
            const puedeSeleccionar = card.dataset.puedeSeleccionar === 'true';

            if (!puedeSeleccionar) {
                toast(`⚠️ ${card.querySelector('.mesa-estado')?.innerText || 'Mesa ocupada'}`);
                return;
            }

            const mesa = {
                id: card.dataset.id,
                numero: parseInt(card.dataset.numero),
                estado: card.dataset.ocupada === 'true' ? 'ocupada' : 'libre',
                order_id: card.dataset.orderId || null
            };
            seleccionarMesa(mesa);
        });
    });
}


async function seleccionarMesa(mesa) {
    mesaSeleccionada = mesa;

    // Si la mesa está ocupada por mí, cargar la orden existente
    if (mesa.estado === 'ocupada' && mesa.order_id) {
        await cargarOrdenExistente(mesa.order_id);
        return;
    }

    // Mesa libre: nueva orden
    ordenActual = [];
    ordenIdActual = null;
    ordenNumeroActual = null;
    ordenEstadoActual = null;
    actualizarUI();

    document.getElementById('mesasScreen').classList.remove('active');
    document.getElementById('menuScreen').classList.add('active');

    document.getElementById('mesaNumero').innerText = `Mesa #${mesa.numero}`;
    document.getElementById('ordenNumero').innerText = '#---';

    renderCategorias();
    cargarMenusAPI();
    cambiarTab('menu');
    actualizarBotonEnvio();
}

async function cargarOrdenExistente(orderId) {
    try {
        console.log("=== cargarOrdenExistente ===");
        console.log("renderCategorias es función?", typeof renderCategorias);
        console.log("cargarMenusAPI es función?", typeof cargarMenusAPI);
        console.log("cambiarTab es función?", typeof cambiarTab);

        mostrarLoading();

        const url = `/api/ordenes/${orderId}/`;
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin'
        });

        if (!response.ok) {
            throw new Error(`Error ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        ordenIdActual = data.id;
        ordenNumeroActual = data.numero_orden;
        ordenEstadoActual = data.estado;

        ordenActual = data.items.map(item => ({
            menu_product_id: item.menu_product,
            nombre: item.producto_nombre,
            precio: parseFloat(item.precio_unitario),
            cantidad: item.cantidad,
            subtotal: parseFloat(item.subtotal)
        }));

        actualizarUI();

        document.getElementById('mesasScreen').classList.remove('active');
        document.getElementById('menuScreen').classList.add('active');

        document.getElementById('mesaNumero').innerText = `Mesa #${mesaSeleccionada.numero}`;
        document.getElementById('ordenNumero').innerText = `#${data.numero_orden}`;

        // Llamar con verificación
        if (typeof renderCategorias === 'function') {
            renderCategorias();
        } else {
            console.error("❌ renderCategorias no está definida");
        }

        if (typeof cargarMenusAPI === 'function') {
            await cargarMenusAPI();
        } else {
            console.error("❌ cargarMenusAPI no está definida");
        }

        if (typeof cambiarTab === 'function') {
            cambiarTab('menu');
        } else {
            console.error("❌ cambiarTab no está definida");
        }

        if (typeof actualizarBotonPorEstado === 'function') {
            actualizarBotonPorEstado();
        }

    } catch (error) {
        console.error("Error en cargarOrdenExistente:", error);
        toast('❌ Error al cargar la orden: ' + error.message);
    }
}

function actualizarBotonPorEstado() {
    const btn = document.getElementById('enviarOrdenBtn');
    if (!btn) return;

    // Orden en estado SERVIDA (3) - mostrar botón de cobrar
    if (ordenEstadoActual === 3) {
        btn.innerHTML = `💰 Cobrar orden #${ordenNumeroActual}`;
        btn.classList.remove('btn-cocina');
        btn.classList.add('btn-caja');
        btn.disabled = false;
        btn.onclick = () => enviarOrden();
    }
    // Orden en estado PROCESANDO (2) - en espera
    else if (ordenEstadoActual === 2) {
        btn.innerHTML = '⏳ En cocina...';
        btn.disabled = true;
    }
    // Orden en estado PENDIENTEPAGO (1) - ya fue a caja
    else if (ordenEstadoActual === 1) {
        btn.innerHTML = '💰 En caja...';
        btn.disabled = true;
    }
    // Orden pagada
    else if (ordenEstadoActual === 4) {
        btn.innerHTML = '✅ Orden pagada';
        btn.disabled = true;
    }
}
