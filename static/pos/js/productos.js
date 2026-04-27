// static/pos/js/productos.js

function renderProductos() {
    const container = document.getElementById('productosContainer');

    if (!productos || productos.length === 0) {
        container.innerHTML = '<div class="empty-state">🍽️ No hay productos en esta categoría</div>';
        return;
    }

    container.innerHTML = productos.map(p => {
        const itemEnOrden = ordenActual.find(i => i.menu_product_id === p.id);
        const cantidadActual = itemEnOrden ? itemEnOrden.cantidad : 0;

        return `
            <div class="producto-card" data-id="${p.id}">
                <div class="producto-imagen" style="background-image: url('${p.imagen_url || 'https://placehold.co/70x70/1a472a/white?text=🍽️'}');"></div>
                <div class="producto-info">
                    <div class="producto-nombre">${p.producto_nombre || p.nombre}</div>
                    <div class="producto-descripcion">${p.producto_descripcion || p.descripcion || ''}</div>
                    <div class="producto-precio">${formatearPrecio(p.precio)}</div>
                    ${cantidadActual > 0 ? `<div class="producto-cantidad-actual">📦 Lleva: ${cantidadActual}</div>` : ''}
                </div>
                <div class="producto-actions">
                    ${cantidadActual > 0 ? `<button class="btn-cantidad eliminar" data-action="eliminar">🗑️</button>` : ''}
                    <div class="btn-group">
                        <button class="btn-multiple" data-action="mas1">+1</button>
                        <button class="btn-multiple" data-action="mas5">+5</button>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    // Event delegation
    const containerElement = document.getElementById('productosContainer');
    if (containerElement) {
        containerElement.removeEventListener('click', handleProductClick);
        containerElement.addEventListener('click', handleProductClick);
    }
}

function handleProductClick(e) {

    const card = e.target.closest('.producto-card');
    if (!card) {
        return;
    }

    const menuProductId = card.dataset.id;
    const producto = productos.find(p => p.id === menuProductId);

    if (e.target.classList.contains('btn-multiple')) {
        e.stopPropagation();
        const action = e.target.getAttribute('data-action');
        if (action === 'mas1') {
            agregarProducto(producto);
        } else if (action === 'mas5') {
            agregarMultiples(producto, 5);
        }
    } else if (e.target.classList.contains('btn-cantidad')) {
        e.stopPropagation();
        eliminarProducto(menuProductId);
    } else {
        agregarProducto(producto);
    }
}

function mostrarSelectorMenu() {
    const container = document.getElementById('menuSelectorContainer');
    const selector = document.getElementById('selectorMenu');

    if (!container || !selector) return;

    if (menusDisponibles && menusDisponibles.length > 0) {
        container.style.display = 'block';
        selector.innerHTML = menusDisponibles.map(m => `
            <option value="${m.id}" ${menuSeleccionado === m.id ? 'selected' : ''}>
                📋 ${m.nombre}
            </option>
        `).join('');

        selector.onchange = (e) => {
            menuSeleccionado = e.target.value;
            categoriaActiva = 0;
            renderCategorias();
            cargarProductosAPI();
        };
    } else {
        container.style.display = 'none';
    }
}

// Exportar funciones globalmente
window.renderCategorias = renderCategorias;
window.renderProductos = renderProductos;
window.handleProductClick = handleProductClick;
