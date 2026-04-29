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
//    toLocaleString 'en-US' para que funcione en otros dispositivos, siempre el mismo formato
    return `$${parseFloat(precio).toLocaleString('en-US', {
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

function validarNumeroInput(valor, { min = 0, max = Infinity, decimales = 2 } = {}) {

        if (valor === null || valor === undefined) return '';

        valor = String(valor);

        // coma a punto
        valor = valor.replace(',', '.');

        // solo números y punto
        valor = valor.replace(/[^0-9.]/g, '');

        // evitar múltiples puntos
        const partes = valor.split('.');
        if (partes.length > 2) {
            valor = partes[0] + '.' + partes[1];
        }

        // 🔥 CLAVE: permitir estado intermedio "12."
        if (valor.endsWith('.')) {
            return valor;
        }

        // si empieza con punto ".5" → convertir a "0.5"
        if (valor.startsWith('.')) {
            valor = '0' + valor;
        }

        const num = parseFloat(valor);

        if (isNaN(num)) return '';

        let resultado = num;

        if (resultado < min) resultado = min;
        if (resultado > max) resultado = max;

        // 🔥 mantener decimales SOLO si ya es número completo
        if (valor.includes('.')) {
            const [entero, decimal] = valor.split('.');
            return `${entero}.${decimal.slice(0, decimales)}`;
        }

        return String(resultado);
    }

window.getCSRFToken = getCSRFToken;
window.formatearPrecio = formatearPrecio;
window.formatearNumeroOrden = formatearNumeroOrden;
window.cerrarSesion = cerrarSesion;
window.toast = toast;
