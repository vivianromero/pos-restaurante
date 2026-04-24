# apps/core/urls_names.py

"""
Centralización de nombres de URLs para usar en decoradores y vistas
"""

# ============================================
# URLs del Admin de Django
# ============================================
ADMIN_INDEX = 'admin_index'           # Panel de admin
ADMIN_LOGIN = 'admin_login'           # Login del admin
ADMIN_LOGOUT = 'admin_logout'         # Logout del admin
ADMIN_PASSWORD_CHANGE = 'admin_password_change'
ADMIN_PASSWORD_CHANGE_DONE = 'admin_password_change_done'

# ============================================
# URLs de la App (meseros)
# ============================================
LOGIN = 'login'                       # Login de meseros
LOGOUT = 'logout'                     # Logout de meseros
CAMBIO_PASSWORD = 'cambiar_password'  # Cambiar contraseña
HOME = 'home'                         # Página de inicio

# ============================================
# URLs del POS
# ============================================
MESERO = 'mesero'                     # Pantalla del mesero
PUNTO_VENTA = 'punto_venta'           # Punto de venta
COCINA = 'cocina'                     # Pantalla de cocina