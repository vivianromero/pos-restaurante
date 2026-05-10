# -*- mode: python ; coding: utf-8 -*-

import os
import shutil

def post_build(): #copiar templates y staticfiles para backend
    dist_dir = os.path.join(os.getcwd(), 'dist', 'backend')
    internal_dir = os.path.join(dist_dir, '_internal')

    # mover templates
    src_templates = os.path.join(internal_dir, 'templates')
    dst_templates = os.path.join(dist_dir, 'templates')
    if os.path.exists(src_templates):
        shutil.move(src_templates, dst_templates)

    # mover staticfiles
    src_static = os.path.join(internal_dir, 'staticfiles')
    dst_static = os.path.join(dist_dir, 'staticfiles')
    if os.path.exists(src_static):
        shutil.move(src_static, dst_static)

    # mover libpython
    src_libpython = os.path.join(internal_dir, 'libpython3.12.so.1.0')
    dst_libpython = os.path.join(dist_dir, 'libpython3.12.so.1.0')
    if os.path.exists(src_libpython):
        shutil.copy2(src_libpython, dst_libpython)

from PyInstaller.utils.hooks import (
    collect_all,
    collect_submodules,
    collect_data_files
)

project_root = '/home/fujilinux/Vivian/OtrosProyectos/pos_system'

# ============================================================
# RECOLECTAR LIBRERÍAS DJANGO
# ============================================================

packages = ['django', 'jazzmin', 'rest_framework', 'corsheaders', 'django_filters']

all_datas = []
all_binaries = []
all_hiddenimports = []

for pkg in packages:
    datas, binaries, hidden = collect_all(pkg)
    all_datas += datas
    all_binaries += binaries
    all_hiddenimports += hidden

# 🔥 CLAVE: asegurar templates de jazzmin y admin
all_datas += collect_data_files('jazzmin', include_py_files=True)
all_datas += collect_data_files('django.contrib.admin', include_py_files=True)

# ============================================================
# COPIAR DIRECTORIOS PROYECTO
# ============================================================

def add_tree(src_dir, dest_prefix):
    collected = []
    if os.path.exists(src_dir):
        for root, _, files in os.walk(src_dir):
            for f in files:
                src = os.path.join(root, f)

                rel_dir = os.path.relpath(root, src_dir)
                dest_dir = os.path.join(dest_prefix, rel_dir)

                collected.append((src, dest_dir))

    return collected

print("\n=== COPIANDO TEMPLATES ===")
templates_path = os.path.join(project_root, 'templates')
all_datas += add_tree(templates_path, 'templates')

print("=== COPIANDO STATICFILES ===")
static_path = os.path.join(project_root, 'staticfiles')
if os.path.exists(static_path):
    all_datas += add_tree(static_path, 'staticfiles')
else:
    print("⚠️ Ejecuta collectstatic")

# ============================================================
# HIDDEN IMPORTS
# ============================================================

hiddenimports = all_hiddenimports + [
    'apps.core.middleware',
    'apps.administracion',
    'apps.ordenes',
    'apps.caja',
    'apps.core',
    'apps.api',
    'apps.api.urls',
    'config.settings',
    'config.urls',
    'config.wsgi',
    'config.asgi',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django.template.loaders.app_directories',
    'django.template.loaders.filesystem',

    'PIL',
    'PIL.Image',
]

# Submódulos
for app in [
    'apps.administracion',
    'apps.ordenes',
    'apps.caja',
    'apps.core',
    'apps.api'
]:
    try:
        hiddenimports += collect_submodules(app)
    except:
        pass

# ============================================================
# BUILD
# ============================================================

a = Analysis(
    ['mainapp.py'],
    pathex=[project_root],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=hiddenimports,
    excludes=['tkinter', 'numpy', 'pytest', 'setuptools', 'distutils'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='backend',
    debug=False,
    strip=False,
    upx=False,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='backend',
)

post_build()