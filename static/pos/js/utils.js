// static/pos/js/utils.js

// Obtener token CSRF
function getCSRFToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 10) === ('csrftoken' + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    return cookieValue;
}

// Formatear precio
function formatearPrecio(precio) {
    return `$${parseFloat(precio).toLocaleString()}`;
}

// Formatear número de orden
function formatearNumeroOrden(numero) {
    return `#${numero.toString().padStart(3, '0')}`;
}