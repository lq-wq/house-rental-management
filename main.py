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

    os.chdir(base_dir)

    from gui import RentalManagementApp
    import tkinter as tk

    root = tk.Tk()

    # 设置窗口图标 - 优先使用 iconbitmap，其次 iconphoto
    icon_loaded = False
    try:
        icon_path = os.path.join(base_dir, "house.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(default=icon_path)
            icon_loaded = True
    except Exception:
        pass

    # 如果 iconbitmap 失败了，尝试使用 iconphoto 生成一个简单的房子图标
    if not icon_loaded:
        try:
            # 创建一个简单的 16x16 房子图标
            img = tk.PhotoImage(width=16, height=16)
            # 用像素数据画一个简单的房子
            colors = {
                's': '#87CEEB',  # sky
                'r': '#B44C3C',  # roof
                'w': '#C8BEA0',  # wall
                'd': '#8B5E3C',  # door
                'g': '#6B8E23',  # grass
            }
            # 16x16 house pixel map
            pixels = [
                "ssssrssssrsssss",
                "sssrrrsssrrrsss",
                "ssrrrrrssrrrrss",
                "srrrrrrrssrrrrs",
                "rrrrrrrrrrrrrrr",
                "sswwwwwwwwwwsss",
                "sswwwwwwwwwwsss",
                "sswwdwwwwdwwsss",
                "sswwdwwwwdwwsss",
                "sswwddddddwwsss",
                "sswwddddddwwsss",
                "sswwwwwwwwwwsss",
                "sswwwwwwwwwwsss",
                "sswwwwwwwwwwsss",
                "sssssssssssssss",
                "sssssssssssssss",
            ]
            img_string = ""
            for row in pixels:
                for ch in row:
                    img_string += "{" + colors[ch] + "} "
                img_string += " "
            img.put(img_string, to=(0, 0, 16, 16))
            root.iconphoto(True, img)
        except Exception:
            pass

    app = RentalManagementApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
