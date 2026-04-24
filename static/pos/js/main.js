// static/pos/js/main.js

// Exponer funciones necesarias globalmente


document.addEventListener('DOMContentLoaded', function() {
    console.log('Funciones disponibles:', {
        cargarMesasAPI: typeof cargarMesasAPI,
        cargarCategoriasAPI: typeof cargarCategoriasAPI,
        renderProductos: typeof renderProductos,
        renderOrdenLista: typeof renderOrdenLista,
        actualizarAmbosTabs: typeof actualizarAmbosTabs,
        cargarConfiguracion: typeof cargarConfiguracion
    });

    cargarMesasAPI();
    cargarCategoriasAPI();
    cargarConfiguracion();

    document.getElementById('enviarOrdenBtn')?.addEventListener('click', enviarOrden);
    document.getElementById('cambiarMesaBtn')?.addEventListener('click', cambiarMesa);

    document.querySelectorAll('.main-tab').forEach(tab => {
        tab.addEventListener('click', () => cambiarTab(tab.dataset.tab));
    });
});


