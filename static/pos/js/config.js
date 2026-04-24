// static/pos/js/config.js

// ============================================
// VARIABLES GLOBALES
// ============================================

// Variables de orden
let nextOrdenNumero = 1;
let mesaSeleccionada = null;
let ordenActual = [];
let categoriaActiva = 0;
let ordenNumeroActual = null;
let ordenIdActual = null;
let ordenEstadoActual = null;

// Variables de datos
let mesas = [];
let productos = [];
let menuSeleccionado = null;
let menusDisponibles = [];
let categorias = [];

// Configuración del sistema
let configuracionSystem = {
    modulo_cocina_activo: false,
    modulo_caja_activo: true,
    pantalla_cocina_ip: null,
    pantalla_cocina_puerto: 8000,
    impresion_automatica: false,
    impresora_nombre: null,
    copias_ticket: 1
};