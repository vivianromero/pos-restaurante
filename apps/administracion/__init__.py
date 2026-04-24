class GruposUsuarios:
    ADMINISTRADOR = 1
    MESEROS = 2
    CAJEROS = 3
    PROCESO_DE_ORDENES = 4

    CHOICE_GRUPOSUSUARIOS = {
        1: 'Administrador',
        2: 'Meseros',
        3: 'Cajeros',
        4: 'Proceso de Ordenes',
    }

GRUPOS_PERMITIDOS = [k for k in GruposUsuarios.CHOICE_GRUPOSUSUARIOS.values()]

VALORES_POR_API_GRUPO = {
    GruposUsuarios.MESEROS: "mesero",
    GruposUsuarios.CAJEROS: "cajero",
    GruposUsuarios.PROCESO_DE_ORDENES: "cocina",
}