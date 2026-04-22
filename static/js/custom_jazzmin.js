//En el passwor del login del modulo admin, poner mostrar/ocultar contaseña
document.addEventListener("DOMContentLoaded", function () {
    // Eliminar el icono de candado sin perder el espacio
    const lockIcon = document.querySelector('.input-group-append .input-group-text .fas.fa-lock');
    if (lockIcon) {
        lockIcon.style.visibility = 'hidden';  // Ocultar el icono de candado, pero mantener el espacio
    }

    // Mostrar/ocultar contraseña
    const passwordFields = document.querySelectorAll("input[type='password']");
    passwordFields.forEach((field) => {
        const toggleBtn = document.createElement("span");
        toggleBtn.classList.add("fas", "fa-lock");  // Usar el icono de FontAwesome
        toggleBtn.style.cursor = "pointer";
        toggleBtn.style.position = "absolute";  // Posicionar el icono dentro del campo
        toggleBtn.style.right = "10px";         // Alineado a la derecha
        toggleBtn.style.top = "50%";            // Centrado verticalmente
        toggleBtn.style.transform = "translateY(-50%)";  // Ajusta el centrado vertical
        toggleBtn.style.zIndex = "9999";        // Asegura que el icono esté por encima del campo
        toggleBtn.style.fontSize = "18px";      // Ajusta el tamaño del icono

        // Tooltip dinámico basado en el estado de la contraseña
        toggleBtn.title = "Mostrar contraseña"; // Inicialmente muestra "Mostrar contraseña"

        toggleBtn.addEventListener("click", function () {
            const isPassword = field.getAttribute("type") === "password";
            field.setAttribute("type", isPassword ? "text" : "password");
            toggleBtn.classList.toggle("fa-lock");
            toggleBtn.classList.toggle("fa-lock-open");

            // Cambiar el texto del tooltip
            toggleBtn.title = isPassword ? "Ocultar contraseña" : "Mostrar contraseña";
        });

        // Asegurar que el campo tenga suficiente espacio para el icono
        field.style.paddingRight = "40px";  // Asegura que haya suficiente espacio a la derecha para el icono

        field.parentNode.style.position = "relative";  // Hacer que el contenedor del campo tenga posición relativa
        field.parentNode.appendChild(toggleBtn);  // Insertar el icono de mostrar/ocultar dentro del campo
    });
});

