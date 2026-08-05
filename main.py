#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
房屋租赁管理系统
启动入口
"""

import sys
import os


def main():
    # 确保当前目录在路径中（支持 PyInstaller 打包）
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)

    # 切换工作目录到程序所在目录，确保数据库文件在正确位置
    os.chdir(base_dir)

    from gui import RentalManagementApp
    import tkinter as tk

    root = tk.Tk()
    app = RentalManagementApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
