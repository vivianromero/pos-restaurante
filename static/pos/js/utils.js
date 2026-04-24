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

function formatearPrecio(precio) {
    return `$${parseFloat(precio).toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    })}`;
}

// Formatear número de orden
function formatearNumeroOrden(numero) {
    return `#${numero.toString().padStart(3, '0')}`;
}

function cerrarSesion() {
    window.location.href = '/logout/';
}

function toast(msg, tipo = 'success', duracion = 3000) {
    const oldToasts = document.querySelectorAll('.toast');
    oldToasts.forEach(toast => toast.remove());

    const colores = {
        success: '#1a472a',
        error: '#f44336',
        warning: '#ff9800',
        info: '#2196f3'
    };

    const iconos = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };

    const t = document.createElement('div');
    t.className = 'toast';
    t.innerHTML = `${iconos[tipo] || '✅'} ${msg}`;
    t.style.cssText = `
        position: fixed;
        bottom: 80px;
        left: 50%;
        transform: translateX(-50%);
        background: ${colores[tipo] || colores.success};
        color: white;
        padding: 12px 20px;
        border-radius: 30px;
        font-size: 0.9rem;
        z-index: 1000;
        white-space: nowrap;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    `;
    document.body.appendChild(t);

    setTimeout(() => {
        t.style.opacity = '0';
        t.style.transition = 'opacity 0.5s ease';
        setTimeout(() => {
            if (t && t.parentNode) {
                t.remove();
            }
        }, 500);
    }, duracion);
}

window.getCSRFToken = getCSRFToken;
window.formatearPrecio = formatearPrecio;
window.formatearNumeroOrden = formatearNumeroOrden;
window.cerrarSesion = cerrarSesion;
window.toast = toast;
