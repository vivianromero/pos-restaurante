function mostrarLoading(id, cargando="datos") {

    // Mostrar loading en el grid
    const gridGrid = document.getElementById(id);
    if (gridGrid) {
        gridGrid.innerHTML = `
            <div class="loading-container">
                <div class="spinner"></div>
                <p>Cargando ${cargando}...</p>
            </div>
        `;
    }
}

function mostrarModal(opciones) {
    return new Promise((resolve) => {
        const modal = document.getElementById('customModal');
        const title = document.getElementById('modalTitle');
        const message = document.getElementById('modalMessage');
        const confirmBtn = document.getElementById('modalConfirmBtn');
        const cancelBtn = document.getElementById('modalCancelBtn');

        // Configurar contenido
        title.textContent = opciones.title || 'Confirmar';
        message.innerHTML = opciones.message || '¿Estás seguro?';  // ✅ Cambiar a innerHTML

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

async function cargarFechaOperacion() {
    try {
        const response = await fetch('/api/cajero/fecha-actual/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin'
        });

        if (!response.ok) throw new Error(`Error ${response.status}`);

        const data = await response.json();
        fecha_operacion_formateada = data.fecha_operacion_formateada
        fecha_operacion = data.fecha_operacion
        if (data.fecha_operacion_formateada) {
            document.getElementById('fechaOperacion').innerText = data.fecha_operacion_formateada;
        } else if (data.fecha_operacion) {
            const [year, month, day] = data.fecha_operacion.split('-');
            document.getElementById('fechaOperacion').innerText = `${day}/${month}/${year}`;
        }

    } catch (error) {
        console.error('Error:', error);
        document.getElementById('fechaOperacion').innerText = '--/--/----';
    }
}

async function cargarConfiguracion() {
    try {
        const response = await fetch('/api/config-system/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin'
        });

        if (!response.ok) throw new Error(`Error ${response.status}`);

        const data = await response.json();

        // La API devuelve un array, tomamos el primer elemento
        if (Array.isArray(data) && data.length > 0) {
            configuracionSystem = data[0];
        } else if (data.id) {
            configuracionSystem = data;
        }

    } catch (error) {
        // Usar valores por defecto
        configuracionSystem = {
            modulo_cocina_activo: false,
            modulo_caja_activo: true
        };
    }
}