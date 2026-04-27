// static/pos/js/orden.js

document.addEventListener('DOMContentLoaded', async function() {
    await cargarCategoriasAPI();
    await cargarMesasAPI();

    await cargarConfiguracion();
    await actualizarBotonEnvio();
    await cargarFechaOperacion();

    document.getElementById('enviarOrdenBtn')?.addEventListener('click', enviarOrden);
    document.getElementById('cambiarMesaBtn')?.addEventListener('click', cambiarMesa);

    document.querySelectorAll('.main-tab').forEach(tab => {
        tab.addEventListener('click', () => cambiarTab(tab.dataset.tab));
    });
});

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
            renderProductosrenderProductos();
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
    if (!menuProduct) {
        console.error("menuProduct es undefined");
        return;
    }

    const existente = ordenActual.find(i => i.menu_product_id === menuProduct.id);

    if (existente) {
        existente.cantidad++;
    } else {
        ordenActual.push({
            menu_product_id: menuProduct.id,
            nombre: menuProduct.producto_nombre || menuProduct.nombre,
            precio: parseFloat(menuProduct.precio),
            cantidad: 1
        });
    }

    actualizarUI();
    toast(`+1 ${menuProduct.producto_nombre || menuProduct.nombre}`);

    if (document.getElementById('tabMenu').classList.contains('active')) {
        renderProductos();
    }

    if (ordenIdActual) {
        guardarCambiosOrden();
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

async function cambiarMesa() {
    if (ordenActual.length > 0 && !ordenIdActual) {
        const confirmar = await window.mostrarModal({
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


async function enviarOrden() {

    // Caso 1: Orden ya existe y está en estado SERVIDA (3)
    if (ordenIdActual && ordenEstadoActual === 3) {
        await enviarACaja();
        return;
    }

    // Caso 2: Orden ya existe pero no está servida
    if (ordenIdActual) {
        toast('Esta orden ya fue procesada', tipo='warning');
        return;
    }

    // Caso 3: Orden nueva (sin ID)
    if (ordenActual.length === 0) {
        toast('Debe agregar productos a la orden', tipo='warning');
        return;
    }

    await crearNuevaOrden();
}

async function crearNuevaOrden() {

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

        if (response.ok && data.success) {
            ordenIdActual = data.data.id;
            ordenNumeroActual = data.data.numero_orden;
            ordenEstadoActual = data.data.estado;

            if (configuracionSystem.modulo_cocina_activo) {
                toast(`Orden #${data.data.numero_orden} enviada a cocina`);
                btn.innerHTML = '⏳ En cocina...';
                btn.disabled = true;
                setTimeout(() => {
                    limpiarYVolverMesas();
                }, 1500);
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
            toast(`${data.error || data.errors || 'No se pudo crear la orden'}`, tipo='error');
            btn.innerHTML = textoOriginal;
            btn.disabled = false;
        }

    } catch (error) {
        console.error("Error de red:", error);
        toast('Error al enviar la orden', tipo='error');
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
            toast("Cambios guardados");
            ordenEstadoActual = data.data.estado;
            actualizarUI();
            return true;
        } else {
            toast(`Error: ${data.error || 'No se pudieron guardar los cambios'}`, tipo='error');
            return false;
        }

    } catch (error) {
        toast("Error al guardar los cambios", tipo='error');
        return false;
    }
}

async function enviarACaja() {

    if (!ordenIdActual) {
        toast('No hay orden activa', tipo='warning');
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

        if (response.ok && data.success) {
            toast(`💰 Orden #${ordenNumeroActual} enviada a caja`);

            setTimeout(() => {
                limpiarYVolverMesas();
            }, 1500);
        } else {
            toast(`${data.error || 'Error al enviar a caja'}`, tipo='error');
            btn.innerHTML = '💰 Cobrar orden';
            btn.disabled = false;
        }

    } catch (error) {
        console.error("Error:", error);
        toast('Error al enviar a caja', tipo='error');
        btn.innerHTML = '💰 Cobrar orden';
        btn.disabled = false;
    }
}

function limpiarYVolverMesas() {

    //REINICIAR TODAS LAS VARIABLES
    ordenActual = [];
    mesaSeleccionada = null;
    ordenIdActual = null;
    ordenNumeroActual = null;
    ordenEstadoActual = null;

    actualizarUI();

    document.getElementById('menuScreen').classList.remove('active');
    document.getElementById('mesasScreen').classList.add('active');
    cargarMesasAPI();

    setTimeout(() => {
        if (typeof reconectarBotonEnviar === 'function') {
            reconectarBotonEnviar();
        }
    }, 100);
}

function reconectarBotonEnviar() {
    const btn = document.getElementById('enviarOrdenBtn');
    if (!btn) {
        return;
    }

    // HABILITAR EL BOTÓN
    btn.disabled = false;

    // Eliminar eventos anteriores
    const newBtn = btn.cloneNode(true);
    btn.parentNode.replaceChild(newBtn, btn);

    // Asignar evento
    newBtn.onclick = function() {
        enviarOrden();
    };

}

async function cargarMenusAPI() {
    try {
        const response = await fetch('/api/menus/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin'
        });

        if (!response.ok) throw new Error(`Error ${response.status}`);

        const data = await response.json();

        // Extraer menús
        let menus = Array.isArray(data) ? data : (data.results || []);
        menusDisponibles = menus;

        if (menusDisponibles.length > 0 && !menuSeleccionado) {
            menuSeleccionado = menusDisponibles[0].id;
        }

        mostrarSelectorMenu();

        // ✅ Cargar productos DESPUÉS de tener el menú seleccionado
        await cargarProductosAPI();

    } catch (error) {
        console.error("Error cargando menús:", error);
        menusDisponibles = [
            { id: '1', nombre: 'Desayuno' },
            { id: '2', nombre: 'Almuerzo' },
            { id: '3', nombre: 'Cena' }
        ];
        menuSeleccionado = '1';
        mostrarSelectorMenu();
        await cargarProductosAPI();
    }
}

async function cargarProductosAPI() {
    try {
        mostrarLoading('productosContainer', 'Cargando productos');

        let url = '/api/menu-productos/';
        const params = new URLSearchParams();

        if (menuSeleccionado) params.append('menu', menuSeleccionado);
        if (categoriaActiva > 0) params.append('categoria', categoriaActiva);

        if (params.toString()) url += `?${params.toString()}`;

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
        // ✅ Extraer productos (manejar paginación)
        if (data && data.results) {
            productos = data.results;
        } else if (Array.isArray(data)) {
            productos = data;
        } else {
            productos = [];
        }
        // ✅ Renderizar productos SOLO después de tener los datos
        renderProductos();

    } catch (error) {
        console.error("Error cargando productos:", error);
        const container = document.getElementById('productosContainer');
        if (container) {
            container.innerHTML = `
                <div class="error-container">
                    <p>❌ Error al cargar productos</p>
                    <button class="retry-btn" onclick="cargarProductosAPI()">Reintentar</button>
                </div>
            `;
        }
    }
}

async function cargarMesasAPI() {
    try {
        mostrarLoading('mesasGrid', 'mesas');

        const response = await fetch('/api/mesas/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin'
        });

        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                window.location.href = '/login/';
                return;
            }
            throw new Error(`Error ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            renderMesas(data.data);
        } else {
            throw new Error('Error en la respuesta');
        }

    } catch (error) {
        mostrarErrorMesas();
    }
}

async function cargarCategoriasAPI() {
    try {
        const response = await fetch('/api/categorias/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin'
        });

        if (!response.ok) throw new Error(`Error ${response.status}`);

        const data = await response.json();

        const categoriasData = Array.isArray(data) ? data : (data.results || []);
        categorias = [
            { id: 0, nombre: 'Todos', icono: '📋', nombre_completo: '📋 Todos' },
            ...categoriasData
        ];

        renderCategorias();

    } catch (error) {
        categorias = [
            { id: 0, nombre: 'Todos', icono: '📋', nombre_completo: '📋 Todos' }
        ];
        renderCategorias();
    }
}

function renderCategorias() {
    const container = document.getElementById('categoriasTabs');

    if (!categorias || categorias.length === 0) {
        container.innerHTML = '<div class="categoria-tab">Cargando...</div>';
        return;
    }

    container.innerHTML = categorias.map(c => `
        <div class="categoria-tab ${c.id === categoriaActiva ? 'active' : ''}" data-id="${c.id}">
            ${c.nombre_completo || c.nombre}
        </div>
    `).join('');

    document.querySelectorAll('.categoria-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            categoriaActiva = parseInt(tab.dataset.id);
            renderCategorias();
            cargarProductosAPI();
        });
    });
}

function actualizarBotonEnvio() {
    const btn = document.getElementById('enviarOrdenBtn');
    if (!btn) return;

    // Siempre habilitar al actualizar
    btn.disabled = false;

    if (configuracionSystem.modulo_cocina_activo === true) {
        btn.innerHTML = '👨‍🍳 Enviar a cocina';
        btn.classList.remove('btn-caja');
        btn.classList.add('btn-cocina');
    } else {
        btn.innerHTML = '💰 Cobrar directamente';
        btn.classList.remove('btn-cocina');
        btn.classList.add('btn-caja');
    }
}

function actualizarUI() {
    const totalItems = ordenActual.reduce((s, i) => s + i.cantidad, 0);
    const totalPrecio = ordenActual.reduce((s, i) => s + (i.precio * i.cantidad), 0);

    document.getElementById('totalHeader').innerText = formatearPrecio(totalPrecio);
    document.getElementById('tabOrdenCount').innerText = `(${totalItems})`;

    actualizarEstadoOrden();
}

function actualizarEstadoOrden() {
    const estadoSpan = document.getElementById('ordenEstado');
    if (!estadoSpan) return;

    // Si no hay orden creada (sin ID)
    if (!ordenIdActual) {
        estadoSpan.innerHTML = '🛒 Orden';
        return;
    }

    // Mostrar estado según el valor numérico
    const estados = {
        1: '⏳ Pendiente',
        2: '🍳 En preparación',
        3: '✅ Servida',
        4: '💰 Pendiente pago',
        5: '✔️ Pagada'
    };

    const estadoTexto = estados[ordenEstadoActual] || '📋 Orden';
    estadoSpan.innerHTML = `🛒 ${estadoTexto}`;
}

function actualizarAmbosTabs() {

    // Actualizar header siempre
    actualizarUI();

    // Actualizar datos internos sin importar qué tab está visible
    // Actualizar datos internos sin importar qué tab está visible
    // Los tabs se actualizarán cuando el usuario cambie a ellos

    // Si el tab Orden está visible, actualizarlo
    if (document.getElementById('tabOrden').classList.contains('active')) {
        renderOrdenLista();
    }

    // Si el tab Menú está visible, actualizarlo
    if (document.getElementById('tabMenu').classList.contains('active')) {
        renderProductos();
    }
}
ci
window.reconectarBotonEnviar = reconectarBotonEnviar
window.enviarOrden = enviarOrden;