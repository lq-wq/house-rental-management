# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置文件
"""
import os
import sys
import glob

# 获取当前目录（spec 文件所在目录，也是项目根目录）
ROOT_DIR = os.getcwd()

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[ROOT_DIR],
    binaries=[],
    datas=[
        ('house.ico', '.'),
    ],
    hiddenimports=[
        'gui', 'database', 'models', 'utils',
        'sqlite3', 'csv', 'shutil',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

# 添加所有 .py 文件（确保模块不会遗漏）
for py_file in glob.glob(os.path.join(ROOT_DIR, '*.py')):
    basename = os.path.basename(py_file)
    if basename not in ('main.py', 'build.spec', 'generate_icon.py'):
        a.datas.append((basename, py_file, 'DATA'))

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='房屋租赁管理系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='house.ico',
)
