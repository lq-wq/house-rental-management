#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
房屋租赁管理系统 v2.0
启动入口
"""

import sys
import os


def main():
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)

    # 尝试设置应用图标（GUI 窗口图标）
    try:
        import ctypes
        icon_path = os.path.join(base_dir, "house.ico")
        if os.path.exists(icon_path):
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("house_rental_manager")
    except Exception:
        pass

    os.chdir(base_dir)

    from gui import RentalManagementApp
    import tkinter as tk

    root = tk.Tk()
    # 设置窗口图标
    try:
        icon_path = os.path.join(base_dir, "house.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except Exception:
        pass

    app = RentalManagementApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
