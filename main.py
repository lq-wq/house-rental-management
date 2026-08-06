#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
房屋租赁管理系统 v2.0
启动入口
"""

import sys
import os


def main():
    # 获取基础路径（PyInstaller 打包后为临时目录，源码运行时为脚本所在目录）
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

    # 将 base_dir 添加到 sys.path 的开头，确保能找到模块
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)

    # 切换工作目录到 base_dir
    os.chdir(base_dir)

    # 设置窗口图标（在导入 gui 之前完成）
    try:
        icon_path = os.path.join(base_dir, "house.ico")
        if os.path.exists(icon_path):
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("house_rental_manager")
    except Exception:
        pass

    # 导入 gui 模块并启动
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
