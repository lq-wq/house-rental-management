#!/usr/bin/env python3
"""Generate house icon file house.ico (pure Python, no external dependencies)"""
import struct

def create_house_pixels(size=32):
    """Generate house pixel data in BGRA format"""
    pixels = []
    for y in range(size):
        for x in range(size):
            nx, ny = x / size, y / size

            # Sky background
            color = (200, 220, 240, 255)

            # Ground (bottom 5%)
            if ny > 0.95:
                color = (100, 180, 100, 255)

            # House body
            house_left, house_right = 0.10, 0.90
            house_top, house_bottom = 0.35, 0.90

            if house_left <= nx <= house_right and house_top <= ny <= house_bottom:
                color = (200, 190, 170, 255)
                margin = 0.015
                if (abs(nx - house_left) < margin or abs(nx - house_right) < margin or
                    abs(ny - house_top) < margin or abs(ny - house_bottom) < margin):
                    color = (80, 60, 40, 255)

                # Door
                door_left, door_right = 0.40, 0.60
                door_top, door_bottom = 0.65, 0.90
                if door_left <= nx <= door_right and door_top <= ny <= door_bottom:
                    color = (120, 80, 50, 255)
                    if (abs(nx - door_left) < margin or abs(nx - door_right) < margin or
                        abs(ny - door_top) < margin or abs(ny - door_bottom) < margin):
                        color = (60, 40, 20, 255)
                    knob_cx, knob_cy = 0.55, 0.78
                    if ((nx - knob_cx)**2 + (ny - knob_cy)**2) < 0.003:
                        color = (255, 200, 50, 255)

                # Windows
                win_margin = 0.02
                # Left window
                win1_left, win1_right = 0.18, 0.35
                win1_top, win1_bottom = 0.42, 0.56
                if win1_left <= nx <= win1_right and win1_top <= ny <= win1_bottom:
                    color = (255, 250, 200, 255)
                    if (abs(nx - win1_left) < win_margin or abs(nx - win1_right) < win_margin or
                        abs(ny - win1_top) < win_margin or abs(ny - win1_bottom) < win_margin):
                        color = (80, 60, 40, 255)
                    cross = 0.01
                    cx = (win1_left + win1_right) / 2
                    cy = (win1_top + win1_bottom) / 2
                    if abs(nx - cx) < cross or abs(ny - cy) < cross:
                        color = (80, 60, 40, 255)

                # Right window
                win2_left, win2_right = 0.65, 0.82
                win2_top, win2_bottom = 0.42, 0.56
                if win2_left <= nx <= win2_right and win2_top <= ny <= win2_bottom:
                    color = (255, 250, 200, 255)
                    if (abs(nx - win2_left) < win_margin or abs(nx - win2_right) < win_margin or
                        abs(ny - win2_top) < win_margin or abs(ny - win2_bottom) < win_margin):
                        color = (80, 60, 40, 255)
                    cx = (win2_left + win2_right) / 2
                    cy = (win2_top + win2_bottom) / 2
                    if abs(nx - cx) < cross or abs(ny - cy) < cross:
                        color = (80, 60, 40, 255)

            # Roof
            roof_top, roof_bottom = 0.05, 0.35
            roof_left, roof_right = 0.05, 0.95
            if roof_top <= ny <= roof_bottom:
                t = (ny - roof_top) / (roof_bottom - roof_top)
                left_edge = 0.50 - (0.50 - roof_left) * t
                right_edge = 0.50 + (roof_right - 0.50) * t
                if left_edge <= nx <= right_edge:
                    color = (180, 80, 60, 255)
                    if ny - roof_top < 0.02 or abs(nx - left_edge) < 0.02 or abs(nx - right_edge) < 0.02:
                        color = (100, 40, 20, 255)

            # Chimney
            chimney_left, chimney_right = 0.72, 0.82
            chimney_top, chimney_bottom = 0.02, 0.22
            if chimney_left <= nx <= chimney_right and chimney_top <= ny <= chimney_bottom:
                color = (160, 140, 120, 255)
                if abs(nx - chimney_left) < 0.015 or abs(nx - chimney_right) < 0.015:
                    color = (100, 80, 60, 255)

            pixels.append((color[2], color[1], color[0], color[3]))  # BGRA

    return pixels


def create_ico_file(pixels, size, filepath):
    """Create ICO file from pixel data"""
    # BMP info header
    bmp_header = struct.pack('<I', 40)
    bmp_header += struct.pack('<i', size)
    bmp_header += struct.pack('<i', size * 2)
    bmp_header += struct.pack('<H', 1)
    bmp_header += struct.pack('<H', 32)
    bmp_header += struct.pack('<I', 0)
    bmp_header += struct.pack('<I', size * size * 4)
    bmp_header += struct.pack('<i', 0)
    bmp_header += struct.pack('<i', 0)
    bmp_header += struct.pack('<I', 0)
    bmp_header += struct.pack('<I', 0)

    # Pixel data - 修复：从下到上存储（bottom-up），解决图标倒立问题
    pixel_data = b''
    for y in range(size - 1, -1, -1):  # 从最下面一行开始
        for x in range(size):
            idx = y * size + x
            pixel_data += struct.pack('BBBB', *pixels[idx])

    # AND mask
    mask_row_size = ((size + 31) // 32) * 4
    and_mask = b'\x00' * (mask_row_size * size)

    image_data = bmp_header + pixel_data + and_mask

    # ICO directory entry
    w = size if size < 256 else 0
    h = size if size < 256 else 0
    entry = struct.pack('<BBBBHHII', w, h, 0, 0, 1, 32, len(image_data), 22)

    # ICO header
    ico_header = struct.pack('<HHH', 0, 1, 1)

    with open(filepath, 'wb') as f:
        f.write(ico_header)
        f.write(entry)
        f.write(image_data)

    print(f"Icon generated: {filepath} ({size}x{size})")


if __name__ == "__main__":
    pixels_32 = create_house_pixels(32)
    create_ico_file(pixels_32, 32, "house.ico")
    pixels_64 = create_house_pixels(64)
    create_ico_file(pixels_64, 64, "house_64.ico")
    print("Done - house icons created successfully")
