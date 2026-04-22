document.addEventListener("DOMContentLoaded", function() {
    const menuSelect = document.getElementById("id_menu");
    const productoSelect = document.getElementById("id_producto");
    const precioInput = document.getElementById("id_precio");

    if (!menuSelect) {
        console.log("No se encontró #id_menu en el DOM");
        return;
    }

    // Obtener el ID del MenuProduct que se está editando (soporta UUID)
    function getMenuProductId() {
        const match = window.location.pathname.match(/\/menuproduct\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\/change\//);
        console.log("Pathname:", window.location.pathname);
        console.log("Match UUID:", match);
        return match ? match[1] : null;
    }

    const menuProductId = getMenuProductId();
    console.log("MenuProduct ID en edición:", menuProductId);

    function cargarProductos(menuId) {
        console.log("cargarProductos llamado con menuId:", menuId);

        if (!menuId || menuId === '' || menuId === 'None') {
            console.log("Menú vacío, deshabilitando campos");
            productoSelect.innerHTML = '<option value="">---------</option>';
            productoSelect.style.backgroundColor = "#f5f5f5";
            precioInput.style.backgroundColor = "#f5f5f5";
            productoSelect.disabled = true;
            precioInput.disabled = true;
            return;
        }

        productoSelect.innerHTML = '<option value="">Cargando productos...</option>';
        productoSelect.disabled = true;
        precioInput.disabled = true;

        // Construir URL con menuproduct_id si existe (edición)
        let url = `/admin/administracion/menuproduct/productos-por-menu/?menu_id=${menuId}`;
        if (menuProductId) {
            url += `&menuproduct_id=${menuProductId}`;
        }

        console.log("Fetching URL:", url);

        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log("Productos recibidos:", data.productos);
                console.log("Producto actual ID desde backend:", data.producto_actual_id);

                productoSelect.innerHTML = '<option value="">---------</option>';

                if (data.productos.length === 0) {
                    productoSelect.innerHTML = '<option value="">No hay productos disponibles</option>';
                    productoSelect.disabled = true;
                    precioInput.disabled = true;
                } else {
                    let productoEncontrado = false;

                    data.productos.forEach(producto => {
                        const option = document.createElement('option');
                        option.value = producto.id;
                        option.textContent = producto.nombre;
                        productoSelect.appendChild(option);

                        // Si este producto es el actual, marcarlo como seleccionado
                        if (data.producto_actual_id && producto.id == data.producto_actual_id) {
                            option.selected = true;
                            productoEncontrado = true;
                            console.log("Producto actual seleccionado:", producto.nombre);
                        }
                    });

                    productoSelect.disabled = false;
                    precioInput.disabled = false;
                    productoSelect.style.backgroundColor = "white";
                    precioInput.style.backgroundColor = "white";

                    // Si no se encontró el producto actual en la lista (no debería pasar)
                    if (menuProductId && !productoEncontrado) {
                        console.warn("No se encontró el producto actual en la lista de productos");
                    }

                    // Disparar evento change para asegurar que Django registre el valor
                    productoSelect.dispatchEvent(new Event('change'));
                }
            })
            .catch(error => {
                console.error('Error al cargar productos:', error);
                productoSelect.innerHTML = '<option value="">Error al cargar productos</option>';
                productoSelect.disabled = true;
                precioInput.disabled = true;
            });
    }

    function handleMenuChange() {
        console.log("handleMenuChange - Nuevo valor del menú:", menuSelect.value);
        cargarProductos(menuSelect.value);
        // Limpiar el precio cuando cambia el menú
        if (precioInput) {
            precioInput.value = '';
        }
    }

    // Inicializar
    const valorInicialMenu = menuSelect.value;
    console.log("Valor inicial del menú:", valorInicialMenu);

    if (valorInicialMenu && valorInicialMenu !== '' && valorInicialMenu !== 'None') {
        cargarProductos(valorInicialMenu);
    } else {
        console.log("No hay menú seleccionado inicialmente");
        productoSelect.disabled = true;
        precioInput.disabled = true;
        productoSelect.style.backgroundColor = "#f5f5f5";
        precioInput.style.backgroundColor = "#f5f5f5";
    }

    // Escuchar cambios en el select de menú
    if (window.jQuery) {
        jQuery(menuSelect).on("select2:select", function(e) {
            console.log("Select2 select event - ID:", e.params.data.id);
            handleMenuChange();
        });
        jQuery(menuSelect).on("select2:unselect", function(e) {
            console.log("Select2 unselect event");
            handleMenuChange();
        });
    } else {
        menuSelect.addEventListener("change", function(e) {
            console.log("Change event - Valor:", e.target.value);
            handleMenuChange();
        });
    }
});