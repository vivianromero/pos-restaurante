// Auto-ocultar mensajes de error después de 5 segundos
document.addEventListener('DOMContentLoaded', function() {
    const errorMessage = document.getElementById('errorMessage');
    if (errorMessage) {
        setTimeout(function() {
            errorMessage.style.transition = 'opacity 0.5s ease';
            errorMessage.style.opacity = '0';
            setTimeout(function() {
                if (errorMessage && errorMessage.parentNode) {
                    errorMessage.remove();
                }
            }, 500);
        }, 5000);
    }
});

// Validación del formulario antes de enviar
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', function(event) {
        const username = document.getElementById('username');
        const password = document.getElementById('password');

        if (!username.value.trim()) {
            event.preventDefault();
            mostrarError('Por favor ingresa tu usuario');
            username.focus();
            return false;
        }

        if (!password.value.trim()) {
            event.preventDefault();
            mostrarError('Por favor ingresa tu contraseña');
            password.focus();
            return false;
        }

        // Mostrar loading en el botón
        const loginBtn = document.getElementById('loginBtn');
        if (loginBtn) {
            loginBtn.innerHTML = '⏳ Ingresando...';
            loginBtn.disabled = true;
        }

        return true;
    });
}

function mostrarError(mensaje) {
    // Eliminar error anterior si existe
    const errorExistente = document.querySelector('.error-message');
    if (errorExistente && !errorExistente.id) {
        errorExistente.remove();
    }

    // Crear nuevo mensaje de error
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `❌ ${mensaje}`;

    // Insertar después del logo
    const logo = document.querySelector('.logo');
    if (logo && logo.parentNode) {
        logo.parentNode.insertBefore(errorDiv, logo.nextSibling);
    }

    // Auto-ocultar después de 3 segundos
    setTimeout(function() {
        errorDiv.style.transition = 'opacity 0.5s ease';
        errorDiv.style.opacity = '0';
        setTimeout(function() {
            if (errorDiv && errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 500);
    }, 3000);
}

// Agregar efecto de focus a los inputs
const inputs = document.querySelectorAll('input');
inputs.forEach(input => {
    input.addEventListener('focus', function() {
        this.parentElement.classList.add('focused');
    });

    input.addEventListener('blur', function() {
        this.parentElement.classList.remove('focused');
    });
});


// Mostrar/Ocultar contraseña
document.addEventListener('DOMContentLoaded', function() {
    const togglePassword = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('password');

    if (togglePassword && passwordInput) {

        togglePassword.addEventListener('click', function() {

            // Cambiar el tipo de input entre password y text
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                togglePassword.innerHTML = '🔓';
                togglePassword.title = 'Ocultar contraseña';
            } else {
                passwordInput.type = 'password';
                togglePassword.innerHTML = '🔒';
                togglePassword.title = 'Mostrar contraseña';
            }
        });
    } else {
        console.log('No se encontró el botón togglePassword');
    }

    // Auto-ocultar mensajes de error después de 5 segundos
    const errorMessage = document.getElementById('errorMessage');
    if (errorMessage) {
        setTimeout(function() {
            errorMessage.style.transition = 'opacity 0.5s ease';
            errorMessage.style.opacity = '0';
            setTimeout(function() {
                if (errorMessage && errorMessage.parentNode) {
                    errorMessage.remove();
                }
            }, 500);
        }, 5000);
    }

    // Validación del formulario antes de enviar
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            const username = document.getElementById('username');
            const password = document.getElementById('password');

            if (!username.value.trim()) {
                event.preventDefault();
                mostrarError('Por favor ingresa tu usuario');
                username.focus();
                return false;
            }

            if (!password.value.trim()) {
                event.preventDefault();
                mostrarError('Por favor ingresa tu contraseña');
                password.focus();
                return false;
            }

            // Mostrar loading en el botón
            const loginBtn = document.getElementById('loginBtn');
            if (loginBtn) {
                loginBtn.innerHTML = '⏳ Ingresando...';
                loginBtn.disabled = true;
            }

            return true;
        });
    }
});

function mostrarError(mensaje) {
    // Eliminar error anterior si existe
    const errorExistente = document.querySelector('.error-message');
    if (errorExistente && !errorExistente.id) {
        errorExistente.remove();
    }

    // Crear nuevo mensaje de error
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `❌ ${mensaje}`;

    // Insertar después del logo
    const logo = document.querySelector('.logo');
    if (logo && logo.parentNode) {
        logo.parentNode.insertBefore(errorDiv, logo.nextSibling);
    }

    // Auto-ocultar después de 3 segundos
    setTimeout(function() {
        errorDiv.style.transition = 'opacity 0.5s ease';
        errorDiv.style.opacity = '0';
        setTimeout(function() {
            if (errorDiv && errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 500);
    }, 3000);
}
