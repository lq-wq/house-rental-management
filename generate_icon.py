#!/usr/bin/env python3
"""生成房子图标文件 house.ico（纯 Python，无需外部依赖）"""
import struct
import os

def create_house_icon(size=32, filepath="house.ico"):
    """生成一个简单的房子图标，保存为 .ico 文件"""
    # 定义颜色
    ROOF = (80, 60, 40, 255)          # 屋顶棕色
    WALL = (180, 200, 210, 255)        # 墙壁灰色
    DOOR = (120, 80, 60, 255)          # 门棕色
    WINDOW = (200, 230, 255, 255)      # 窗户浅蓝
    FRAME = (60, 60, 60, 255)          # 边框深灰
    SKY = (135, 206, 235, 255)         # 天空蓝
    CHIMNEY = (160, 140, 120, 255)     # 烟囱

    # 生成像素数据 (BGRA)
    pixels = []
    for y in range(size):
        for x in range(size):
            # 归一化坐标
            nx, ny = x / size, y / size

            # 屋顶三角形 (顶部 0-0.4)
            roof_top = 0.05
            roof_bottom = 0.35
            roof_left = 0.05
            roof_right = 0.95
            # 三角形: 顶部中心 (0.5, roof_top), 左下 (roof_left, roof_bottom), 右下 (roof_right, roof_bottom)
            if roof_top <= ny <= roof_bottom:
                # 检查是否在三角形内
                t = (ny - roof_top) / (roof_bottom - roof_top)
                left_edge = 0.5 - (0.5 - roof_left) * t
                right_edge = 0.5 + (roof_right - 0.5) * t
                if left_edge <= nx <= right_edge:
                    pixels.append(ROOF)
                    continue

            # 烟囱 (屋顶上方)
            chimney_left = 0.7
            chimney_right = 0.82
            chimney_top = 0.0
            chimney_bottom = 0.18
            if chimney_top <= ny <= chimney_bottom and chimney_left <= nx <= chimney_right:
                pixels.append(CHIMNEY)
                continue

            # 墙壁主体 (0.35-0.95)
            wall_top = 0.35
            wall_bottom = 0.95
            wall_left = 0.05
            wall_right = 0.95
            if wall_top <= ny <= wall_bottom and wall_left <= nx <= wall_right:
                # 门 (底部中间)
                door_left = 0.38
                door_right = 0.62
                door_top = 0.65
                door_bottom = 0.95
                if door_left <= nx <= door_right and door_top <= ny <= door_bottom:
                    pixels.append(DOOR)
                    continue

                # 窗户 (左侧)
                win1_left = 0.12
                win1_right = 0.33
                win1_top = 0.42
                win1_bottom = 0.58
                if win1_left <= nx <= win1_right and win1_top <= ny <= win1_bottom:
                    # 窗框
                    margin = 0.02
                    if (abs(nx - win1_left) < margin or abs(nx - win1_right) < margin or
                        abs(ny - win1_top) < margin or abs(ny - win1_bottom) < margin):
                        pixels.append(FRAME)
                    else:
                        pixels.append(WINDOW)
                    continue

                # 窗户 (右侧)
                win2_left = 0.67
                win2_right = 0.88
                win2_top = 0.42
                win2_bottom = 0.58
                if win2_left <= nx <= win2_right and win2_top <= ny <= win2_bottom:
                    margin = 0.02
                    if (abs(nx - win2_left) < margin or abs(nx - win2_right) < margin or
                        abs(ny - win2_top) < margin or abs(ny - win2_bottom) < margin):
                        pixels.append(FRAME)
                    else:
                        pixels.append(WINDOW)
                    continue

                pixels.append(WALL)
                continue

            # 背景 (天空)
            pixels.append(SKY)

    # 编码为 ICO 文件
    # BMP 信息头
    bmp_header = struct.pack('<I', 40)  # 头部大小
    bmp_header += struct.pack('<i', size)  # 宽度
    bmp_header += struct.pack('<i', size * 2)  # 高度 (x2 for ICO)
    bmp_header += struct.pack('<H', 1)  # 色彩平面数
    bmp_header += struct.pack('<H', 32)  # 每像素位数
    bmp_header += struct.pack('<I', 0)  # 压缩方式
    bmp_header += struct.pack('<I', size * size * 4)  # 图像数据大小
    bmp_header += struct.pack('<i', 0)  # 水平分辨率
    bmp_header += struct.pack('<i', 0)  # 垂直分辨率
    bmp_header += struct.pack('<I', 0)  # 使用的颜色数
    bmp_header += struct.pack('<I', 0)  # 重要颜色数

    # 像素数据 (BMP 是 bottom-up, ICO 是 top-down)
    # 对于 ICO，高度是 size*2，像素数据直接按 top-down 排列
    # ICO 格式：像素数据从左上角开始逐行
    pixel_data = b''
    for y in range(size):
        for x in range(size):
            idx = y * size + x
            b, g, r, a = pixels[idx]
            pixel_data += struct.pack('BBBB', b, g, r, a)

    # AND 掩码 (不需要，32位色)
    and_mask = b'\x00' * ((size + 31) // 32 * 4 * size)

    image_data = bmp_header + pixel_data + and_mask

    # ICO 文件头
    ico_header = struct.pack('<HHH', 0, 1, 1)  # reserved, type=1(ico), count=1

    # ICO 目录项
    w = size if size < 256 else 0
    h = size if size < 256 else 0
    entry = struct.pack('<BBBBHHII', w, h, 0, 0, 1, 32, len(image_data), 22)

    # 写入文件
    with open(filepath, 'wb') as f:
        f.write(ico_header)
        f.write(entry)
        f.write(image_data)

    print(f"图标已生成: {filepath} ({size}x{size})")


if __name__ == "__main__":
    # 生成 32x32 和 64x64 两个尺寸
    create_house_icon(32, "house.ico")
    create_house_icon(64, "house_64.ico")
