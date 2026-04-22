JAZZMIN_SETTINGS = {
    'show_ui_builder': False,
    'show_user': False,  # Esta línea controla si el usuario logueado es mostrado en las alertas
    'show_sidebar': True,
    'use_google_fonts_cdn': False, #Desactiva carga de fuentes de Google

    'site_logo': 'img/nexopos_adaptable.png',  # Ruta relativa a la carpeta de static
    # 'site_logo_classes': 'img-fluid',
    "site_logo_classes": "brand-image",
    'site_brand': 'NexoPOS',  # Nombre o logo en la parte superior
    'navigation_expanded': False,
    'hide_models': ['auth.group'],
    'welcome_sign': '¡Bienvenido al Panel de Administración!',  # Mensaje de bienvenida
    'custom_js': 'js/custom_jazzmin.js',
    'custom_css': 'css/custom_jazzmin.css',
    'login_logo': 'img/nexopos_adaptable.png',  # Ruta al logo personalizado

    # 'show_ui_builder': True,  # Oculta el UI Builder de Jazzmin si no lo necesitas

    'user_menu': [
        {'name': 'Profile', 'url': 'admin:auth_user_change', 'permissions': ['auth.change_user']},  # Puedes agregar más elementos al menú del usuario
    ],

    'changeform_format': 'collapsed',  # Colapsa formularios si es necesario

    "icons": {
            "dashboard": "fas fa-tachometer-alt",
            "administracion": "fas fa-cogs",
            "auth": "fas fa-user-cog",
            "backend": "fas fa-cogs",
    },

    "hide_models":['auth.user', 'administracion.customuser', 'administracion.configuraciondiaria',
                   'administracion.table', 'administracion.product', 'administracion.menu',
                   'administracion.menuproduct', 'administracion.product', 'auth.group',
                   'administracion.order','administracion.categoria', 'administracion.configuracionsystem'],

    "custom_links": {
        "administracion": [
            {"name": "Configuración del Sistema", "url": "admin:administracion_configuracionsystem_changelist", "icon": "fas fa-desktop"},
            {"name": "Grupos de usuarios", "url": "admin:auth_group_changelist", "icon": "fas fa-user-group"},
            {"name": "Usuarios", "url": "admin:administracion_customuser_changelist", "icon": "fas fa-user"},
            {"name": "Configuración Diaria", "url": "admin:administracion_configuraciondiaria_changelist", "icon": "fas fa-calendar-day"},
            {"name": "Mesas", "url": "admin:administracion_table_changelist", "icon": "fas fa-chair"},
            {"name": "Categorías de Productos", "url": "admin:administracion_categoria_changelist", "icon": "fas fa-tags"},
            {"name": "Productos", "url": "admin:administracion_product_changelist", "icon": "fas fa-box-open"},
            {"name": "Tipos de Menú", "url": "admin:administracion_menu_changelist", "icon": "fas fa-list-alt"},
            {"name": "Menú de Productos", "url": "admin:administracion_menuproduct_changelist", "icon": "fas fa-utensils"},
        ],
    },
}

