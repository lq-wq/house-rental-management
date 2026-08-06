#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
房屋租赁管理系统 v2.0
启动入口
"""

import sys
import os


def _resolve_module_path():
    """确保所有模块文件都能被正确找到"""
    # PyInstaller 打包后，文件在 _MEIPASS 临时目录
    base_dir = getattr(sys, '_MEIPASS', None)
    if base_dir:
        # 打包模式：_MEIPASS 就是临时目录
        if base_dir not in sys.path:
            sys.path.insert(0, base_dir)
        os.chdir(base_dir)
        return base_dir

    # 源码运行模式
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    os.chdir(script_dir)
    return script_dir


def main():
    base_dir = _resolve_module_path()

    # 设置窗口图标（提前设置，确保 GUI 窗口有图标）
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("house_rental_manager")
    except Exception:
        pass

    # 延迟导入，确保 sys.path 已经设置好
    import importlib

    # 逐个手动导入所需模块，确保它们被注册到 sys.modules
    for mod_name in ['utils', 'models', 'database', 'gui']:
        try:
            importlib.import_module(mod_name)
        except ImportError as e:
            print(f"导入模块 {mod_name} 失败: {e}")
            # 尝试直接添加文件路径
            py_file = os.path.join(base_dir, f"{mod_name}.py")
            if os.path.exists(py_file):
                import importlib.util
                spec = importlib.util.spec_from_file_location(mod_name, py_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[mod_name] = module
                    spec.loader.exec_module(module)
                    print(f"已通过文件路径加载 {mod_name}")

    # 最终导入 gui 并启动
    from gui import RentalManagementApp
    import tkinter as tk

    root = tk.Tk()

    # 设置窗口图标
    try:
        icon_path = os.path.join(base_dir, "house.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(default=icon_path)
    except Exception:
        pass

    app = RentalManagementApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
