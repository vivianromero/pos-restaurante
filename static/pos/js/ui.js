// static/pos/js/ui.js

// Toast notification
function toast(msg, duracion = 3000) {
    const t = document.createElement('div');
    t.className = 'toast';
    t.innerText = msg;
    document.body.appendChild(t);

    setTimeout(() => {
        t.classList.add('hide');
        setTimeout(() => t.remove(), 500);
    }, duracion);
}

// Mostrar loading en mesas
function mostrarLoadingMesas() {
    const container = document.getElementById('mesasGrid');
    if (container) {
        container.innerHTML = `
            <div class="loading-container">
                <div class="spinner"></div>
                <p>Cargando mesas...</p>
            </div>
        `;
    }
}

function mostrarLoading() {

    // Mostrar loading en el grid de mesas
    const mesasGrid = document.getElementById('mesasGrid');
    if (mesasGrid) {
        mesasGrid.innerHTML = `
            <div class="loading-container">
                <div class="spinner"></div>
                <p>Cargando...</p>
            </div>
        `;
    }

    // También puedes mostrar loading en otros contenedores si es necesario
    const productosContainer = document.getElementById('productosContainer');
    if (productosContainer) {
        productosContainer.innerHTML = `
            <div class="loading-container">
                <div class="spinner"></div>
                <p>Cargando productos...</p>
            </div>
        `;
    }
}

function ocultarLoading() {
    console.log("🔄 Ocultando loading...");
    // No es necesario hacer nada específico, el contenido se reemplazará al renderizar
}

// Mostrar error en mesas
function mostrarErrorMesas() {
    const container = document.getElementById('mesasGrid');
    if (container) {
        container.innerHTML = `
            <div class="error-container">
                <p>❌ Error al cargar las mesas</p>
                <button class="retry-btn" onclick="cargarMesasAPI()">Reintentar</button>
            </div>
        `;
    }
}

// Actualizar UI de la orden
function actualizarUI() {
    const totalItems = ordenActual.reduce((s, i) => s + i.cantidad, 0);
    const totalPrecio = ordenActual.reduce((s, i) => s + (i.precio * i.cantidad), 0);

    document.getElementById('totalHeader').innerText = formatearPrecio(totalPrecio);
    document.getElementById('tabOrdenCount').innerText = `(${totalItems})`;
}

function actualizarAmbosTabs() {

    // Actualizar header siempre
    actualizarUI();

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

// ui.js

function mostrarModal(opciones) {
    return new Promise((resolve) => {
        const modal = document.getElementById('customModal');
        const title = document.getElementById('modalTitle');
        const message = document.getElementById('modalMessage');
        const confirmBtn = document.getElementById('modalConfirmBtn');
        const cancelBtn = document.getElementById('modalCancelBtn');

        // Configurar contenido
        title.textContent = opciones.title || 'Confirmar';
        message.textContent = opciones.message || '¿Estás seguro?';

        // Configurar botón de confirmación
        confirmBtn.textContent = opciones.confirmText || 'Aceptar';
        if (opciones.danger) {
            confirmBtn.classList.add('danger');
        } else {
            confirmBtn.classList.remove('danger');
        }

        // Configurar botón de cancelación (opcional)
        if (opciones.showCancel === false) {
            cancelBtn.style.display = 'none';
        } else {
            cancelBtn.style.display = 'block';
            cancelBtn.textContent = opciones.cancelText || 'Cancelar';
        }

        // Mostrar modal
        modal.style.display = 'flex';

        // Manejar eventos
        const handleConfirm = () => {
            limpiar();
            resolve(true);
        };

        const handleCancel = () => {
            limpiar();
            resolve(false);
        };

        const handleOutsideClick = (e) => {
            if (e.target === modal) {
                limpiar();
                resolve(false);
            }
        };

        const limpiar = () => {
            modal.style.display = 'none';
            confirmBtn.removeEventListener('click', handleConfirm);
            cancelBtn.removeEventListener('click', handleCancel);
            modal.removeEventListener('click', handleOutsideClick);
        };

        confirmBtn.addEventListener('click', handleConfirm);
        cancelBtn.addEventListener('click', handleCancel);
        modal.addEventListener('click', handleOutsideClick);
    });
}