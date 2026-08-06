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

    # 确保数据目录存在（由 database.py 的 get_data_dir 自动创建）

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
