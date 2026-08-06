# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置文件
"""

import sys
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[str(ROOT_DIR)],                    # 确保能找到当前目录下的模块
    binaries=[],
    datas=[
        ('house.ico', '.'),                    # 打包图标文件
    ],
    hiddenimports=[
        'gui', 'database', 'models', 'utils',  # 显式声明所有模块
        'sqlite3', 'csv', 'shutil',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

# 添加所有 .py 文件到打包列表（确保不会遗漏）
for py_file in ROOT_DIR.glob('*.py'):
    if py_file.name != 'main.py' and py_file.name != 'build.spec' and py_file.name != 'generate_icon.py':
        a.datas.append((py_file.name, str(py_file), 'DATA'))

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
    console=False,                # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='house.ico',             # 设置图标
)
