// static/pos/js/orden.js

// Función auxiliar para actualizar ambos tabs
function actualizarAmbosTabs() {

    // Actualizar header
    actualizarUI();

    // Actualizar tab Orden si está visible
    const tabOrden = document.getElementById('tabOrden');
    const tabMenu = document.getElementById('tabMenu');

    if (tabOrden && tabOrden.classList.contains('active')) {
        renderOrdenLista();
    }

    // Actualizar tab Menú si está visible
    if (tabMenu && tabMenu.classList.contains('active')) {
        if (typeof renderProductos === 'function') {
            renderProductos();
        } else {
            console.log('❌ renderProductos no es una función');
        }
    }
}


function eliminarProducto(menuProductId) {
    const index = ordenActual.findIndex(i => i.menu_product_id === menuProductId);

    if (index !== -1) {
        if (ordenActual[index].cantidad > 1) {
            ordenActual[index].cantidad--;
        } else {
            ordenActual.splice(index, 1);
        }
        actualizarAmbosTabs();
        toast(`❌ Producto removido`);
    }
}


function agregarProducto(menuProduct) {
    console.log("🚀 agregarProducto LLAMADO");
    console.log("  - Producto:", menuProduct?.producto_nombre);
    console.log("  - ordenIdActual:", ordenIdActual);

    const existente = ordenActual.find(i => i.menu_product_id === menuProduct.id);

    if (existente) {
        console.log("  - Producto existente, nueva cantidad:", existente.cantidad);
        existente.cantidad++;
    } else {
        console.log("  - Push Nuevo producto agregado");
        ordenActual.push({
            menu_product_id: menuProduct.id,
            nombre: menuProduct.producto_nombre || menuProduct.nombre,
            precio: parseFloat(menuProduct.precio),
            cantidad: 1
        });
        console.log("  - Nuevo producto agregado");
    }

    actualizarUI();
    toast(`+1 ${menuProduct.producto_nombre || menuProduct.nombre}`);

    if (document.getElementById('tabMenu').classList.contains('active')) {
        renderProductos();
    }

    // Verificar si debe guardar
    if (ordenIdActual) {
        console.log("  - ✅ Guardando cambios...");
        guardarCambiosOrden();
    } else {
        console.log("No hay ordenIdActual, no se guarda");
    }
}


function agregarMultiples(menuProduct, cantidad) {
    const existente = ordenActual.find(i => i.menu_product_id === menuProduct.id);

    if (existente) {
        existente.cantidad += cantidad;
    } else {
        ordenActual.push({
            menu_product_id: menuProduct.id,
            nombre: menuProduct.producto_nombre || menuProduct.nombre,
            precio: parseFloat(menuProduct.precio),
            cantidad: cantidad
        });
    }

    actualizarUI();
    toast(`+${cantidad} ${menuProduct.producto_nombre || menuProduct.nombre}`);

    if (document.getElementById('tabMenu').classList.contains('active')) {
        renderProductos();
    }

    // Si es una orden existente, guardar automáticamente
    if (ordenIdActual) {
        guardarCambiosOrden();
    }
}

function renderOrdenLista() {
    const container = document.getElementById('ordenLista');

    if (ordenActual.length === 0) {
        container.innerHTML = '<div class="empty-state">✨ Agrega productos desde el menú</div>';
        return;
    }

    container.innerHTML = ordenActual.map((item, idx) => `
        <div class="orden-item">
            <div class="item-info">
                <div class="item-nombre">${item.nombre}</div>
                <div class="item-precio">${formatearPrecio(item.precio)} c/u</div>
            </div>
            <div class="item-controls">
                <button class="cantidad-btn" data-action="dec" data-idx="${idx}">−</button>
                <span class="item-cantidad">${item.cantidad}</span>
                <button class="cantidad-btn" data-action="inc" data-idx="${idx}">+</button>
                <button class="cantidad-btn eliminar" data-action="del" data-idx="${idx}">🗑️</button>
            </div>
            <div class="item-subtotal">${formatearPrecio(item.precio * item.cantidad)}</div>
        </div>
    `).join('');

    // Agregar eventos - usar event delegation para evitar problemas
    container.querySelectorAll('.cantidad-btn').forEach(btn => {
        // Remover eventos anteriores para evitar duplicados
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);

        // Dentro de renderOrdenLista, en los eventos
        newBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const idx = parseInt(newBtn.dataset.idx);
            const action = newBtn.dataset.action;

            if (action === 'inc') {
                ordenActual[idx].cantidad++;
            } else if (action === 'dec') {
                if (ordenActual[idx].cantidad > 1) {
                    ordenActual[idx].cantidad--;
                } else {
                    ordenActual.splice(idx, 1);
                }
            } else if (action === 'del') {
                ordenActual.splice(idx, 1);
            }

            actualizarUI();
            renderOrdenLista();

            if (document.getElementById('tabMenu').classList.contains('active')) {
                renderProductos();
            }

            //Si es una orden existente, guardar automáticamente
            if (ordenIdActual) {
                await guardarCambiosOrden();
            }
        });
    });
}

function enviarOrden() {
    if (ordenActual.length === 0) {
        toast('⚠️ Debe agregar productos a la Orden');
        return;
    }

    const ordenData = {
        orden_numero: ordenNumeroActual,
        mesa_id: mesaSeleccionada.id,
        mesa_numero: mesaSeleccionada.numero,
        productos: ordenActual.map(p => ({
            menu_product_id: p.menu_product_id,
            nombre: p.nombre,
            cantidad: p.cantidad,
            precio: p.precio,
            subtotal: p.precio * p.cantidad
        })),
        total: ordenActual.reduce((s, i) => s + (i.precio * i.cantidad), 0),
        fecha: new Date().toISOString()
    };

    toast(`✅ Orden #${formatearNumeroOrden(ordenNumeroActual)} enviada`);

    setTimeout(() => {
        ordenActual = [];
        mesaSeleccionada = null;
        document.getElementById('menuScreen').classList.remove('active');
        document.getElementById('mesasScreen').classList.add('active');
        cargarMesasAPI();
    }, 1000);
}

async function cambiarMesa() {
    if (ordenActual.length > 0 && !ordenIdActual) {
        const confirmar = await mostrarModal({
            title: 'Cambiar de mesa',
            message: '¿Cambiar de mesa? La orden actual se perderá.',
            confirmText: 'Cambiar',
            cancelText: 'Cancelar'
        });
        if (!confirmar) return;
    }

    // Limpiar variables
    ordenActual = [];
    mesaSeleccionada = null;
    ordenIdActual = null;
    ordenNumeroActual = null;
    ordenEstadoActual = null;

    // Cambiar pantalla
    document.getElementById('menuScreen').classList.remove('active');
    document.getElementById('mesasScreen').classList.add('active');

    // Recargar mesas
    cargarMesasAPI();
}

function cambiarTab(tabId) {

    document.querySelectorAll('.main-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabId);
    });

    const tabMenu = document.getElementById('tabMenu');
    const tabOrden = document.getElementById('tabOrden');

    if (tabId === 'menu') {
        tabMenu.classList.add('active');
        tabOrden.classList.remove('active');
        renderProductos();
    } else {
        tabMenu.classList.remove('active');
        tabOrden.classList.add('active');
        renderOrdenLista();
    }
}

function cerrarSesion() {
    window.location.href = '/logout/';
}

function actualizarBotonEnvio() {
    const btn = document.getElementById('enviarOrdenBtn');
    if (!btn) return;

    if (configuracionsystem.modulo_cocina_activo) {
        btn.innerHTML = '👨‍🍳 Enviar a cocina';
        btn.classList.remove('btn-caja');
        btn.classList.add('btn-cocina');
    } else {
        btn.innerHTML = '💰 Cobrar directamente';
        btn.classList.remove('btn-cocina');
        btn.classList.add('btn-caja');
    }
}

async function enviarOrden() {
    console.log("enviarOrden llamado");
    console.log("ordenIdActual:", ordenIdActual);
    console.log("ordenEstadoActual:", ordenEstadoActual);
    console.log("modulo_cocina_activo:", configuracion?.modulo_cocina_activo);

    // Caso 1: Orden ya existe y está en estado SERVIDA (3)
    if (ordenIdActual && ordenEstadoActual === 3) {
        console.log("Caso 1: Orden servida, enviando a caja");
        await enviarACaja();
        return;
    }

    // Caso 2: Orden ya existe pero no está servida
    if (ordenIdActual) {
        console.log("Caso 2: Orden ya existe pero no está servida");
        toast('⚠️ Esta orden ya fue procesada');
        return;
    }

    // Caso 3: Orden nueva (sin ID)
    if (ordenActual.length === 0) {
        toast('⚠️ Debe agregar productos a la orden');
        return;
    }

    console.log("Caso 3: Creando nueva orden");
    await crearNuevaOrden();
}

async function crearNuevaOrden() {
    console.log("=== crearNuevaOrden ===");
    console.log("mesaSeleccionada:", mesaSeleccionada);
    console.log("ordenActual:", ordenActual);

    const btn = document.getElementById('enviarOrdenBtn');
    const textoOriginal = btn.innerHTML;
    btn.innerHTML = '⏳ Procesando...';
    btn.disabled = true;

    const ordenData = {
        mesa: mesaSeleccionada.id,
        items: ordenActual.map(item => ({
            menu_product_id: item.menu_product_id,
            cantidad: item.cantidad
        }))
    };

    console.log("Enviando datos:", ordenData);

    try {
        const response = await fetch('/api/ordenes/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin',
            body: JSON.stringify(ordenData)
        });

        const data = await response.json();
        console.log("Respuesta:", data);

        if (response.ok && data.success) {
            ordenIdActual = data.data.id;
            ordenNumeroActual = data.data.numero_orden;
            ordenEstadoActual = data.data.estado;

            console.log("Orden creada:", ordenIdActual, ordenNumeroActual, ordenEstadoActual);

            if (configuracion.modulo_cocina_activo) {
                toast(`✅ Orden #${data.data.numero_orden} enviada a cocina`);
                btn.innerHTML = '⏳ En cocina...';
                btn.disabled = true;
            } else {
                // COCINA INACTIVA: Orden creada, mostrar mensaje y volver a mesas
                toast(`💰 Orden #${data.data.numero_orden} enviada a caja`);

                // Esperar un momento y luego limpiar
                setTimeout(() => {
                    limpiarYVolverMesas();
                }, 1500);
            }
        } else {
            console.error("Error en respuesta:", data);
            toast(`❌ ${data.error || data.errors || 'No se pudo crear la orden'}`);
            btn.innerHTML = textoOriginal;
            btn.disabled = false;
        }

    } catch (error) {
        console.error("Error de red:", error);
        toast('❌ Error al enviar la orden');
        btn.innerHTML = textoOriginal;
        btn.disabled = false;
    }
}


async function guardarCambiosOrden() {
    if (!ordenIdActual) {
        return;
    }

    const itemsData = ordenActual.map(item => ({
        menu_product_id: item.menu_product_id,
        cantidad: item.cantidad
    }));

    try {
        const response = await fetch(`/api/ordenes/${ordenIdActual}/actualizar-items/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin',
            body: JSON.stringify({ items: itemsData })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            toast("✅ Cambios guardados");
            actualizarUI();
            return true;
        } else {
            toast(`❌ Error: ${data.error || 'No se pudieron guardar los cambios'}`);
            return false;
        }

    } catch (error) {
        toast("❌ Error al guardar los cambios");
        return false;
    }
}

async function enviarACaja() {
    console.log("=== enviarACaja ===");
    console.log("ordenIdActual:", ordenIdActual);

    if (!ordenIdActual) {
        toast('❌ No hay orden activa');
        return;
    }

    const btn = document.getElementById('enviarOrdenBtn');
    btn.innerHTML = '⏳ Procesando...';
    btn.disabled = true;

    try {
        const response = await fetch(`/api/ordenes/${ordenIdActual}/enviar-caja/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin'
        });

        const data = await response.json();
        console.log("Respuesta enviarACaja:", data);

        if (response.ok && data.success) {
            toast(`💰 Orden #${ordenNumeroActual} enviada a caja`);

            setTimeout(() => {
                limpiarYVolverMesas();
            }, 1500);
        } else {
            toast(`❌ ${data.error || 'Error al enviar a caja'}`);
            btn.innerHTML = '💰 Cobrar orden';
            btn.disabled = false;
        }

    } catch (error) {
        console.error("Error:", error);
        toast('❌ Error al enviar a caja');
        btn.innerHTML = '💰 Cobrar orden';
        btn.disabled = false;
    }
}

function limpiarYVolverMesas() {
    console.log("=== limpiarYVolverMesas ===");

    ordenActual = [];
    mesaSeleccionada = null;
    ordenIdActual = null;
    ordenNumeroActual = null;
    ordenEstadoActual = null;
    actualizarUI();

    document.getElementById('menuScreen').classList.remove('active');
    document.getElementById('mesasScreen').classList.add('active');
    cargarMesasAPI();
}