// static/pos/js/api.js

async function cargarMesasAPI() {
    try {
        mostrarLoadingMesas();

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

        menusDisponibles = Array.isArray(data) ? data : (data.data || []);

        if (menusDisponibles.length > 0 && !menuSeleccionado) {
            menuSeleccionado = menusDisponibles[0].id;
        }

        mostrarSelectorMenu();
        await cargarProductosAPI();

    } catch (error) {
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

        categorias = [
            { id: 0, nombre: 'Todos', icono: '📋', nombre_completo: '📋 Todos' },
            ...(Array.isArray(data) ? data : [])
        ];

        renderCategorias();

    } catch (error) {
        categorias = [
            { id: 0, nombre: 'Todos', icono: '📋', nombre_completo: '📋 Todos' }
        ];
        renderCategorias();
    }
}

async function cargarProductosAPI() {
    try {
        const container = document.getElementById('productosContainer');
        if (container) {
            container.innerHTML = '<div class="loading-container"><div class="spinner"></div><p>Cargando productos...</p></div>';
        }

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

        productos = Array.isArray(data) ? data : (data.data || []);
        renderProductos();

    } catch (error) {
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
            configuracionsystem = data[0];
        } else if (data.id) {
            configuracionsystem = data;
        }

        // Actualizar botón según configuración
        actualizarBotonEnvio();

    } catch (error) {
        // Usar valores por defecto
        configuracionsystem = {
            modulo_cocina_activo: false,
            modulo_caja_activo: true
        };
        actualizarBotonEnvio();
    }
}