#!/usr/bin/env python3
"""Generate house icon file house.ico (pure Python, no external dependencies)"""
import struct
import os

def create_house_icon(size=32, filepath="house.ico"):
    """Generate a simple house icon and save as .ico file"""
    # Define colors
    ROOF = (80, 60, 40, 255)
    WALL = (180, 200, 210, 255)
    DOOR = (120, 80, 60, 255)
    WINDOW = (200, 230, 255, 255)
    FRAME = (60, 60, 60, 255)
    SKY = (135, 206, 235, 255)
    CHIMNEY = (160, 140, 120, 255)

    # Generate pixel data (BGRA)
    pixels = []
    for y in range(size):
        for x in range(size):
            nx, ny = x / size, y / size

            # Roof triangle (top 0-0.4)
            roof_top = 0.05
            roof_bottom = 0.35
            roof_left = 0.05
            roof_right = 0.95
            if roof_top <= ny <= roof_bottom:
                t = (ny - roof_top) / (roof_bottom - roof_top)
                left_edge = 0.5 - (0.5 - roof_left) * t
                right_edge = 0.5 + (roof_right - 0.5) * t
                if left_edge <= nx <= right_edge:
                    pixels.append(ROOF)
                    continue

            # Chimney
            chimney_left = 0.7
            chimney_right = 0.82
            chimney_top = 0.0
            chimney_bottom = 0.18
            if chimney_top <= ny <= chimney_bottom and chimney_left <= nx <= chimney_right:
                pixels.append(CHIMNEY)
                continue

            # Walls
            wall_top = 0.35
            wall_bottom = 0.95
            wall_left = 0.05
            wall_right = 0.95
            if wall_top <= ny <= wall_bottom and wall_left <= nx <= wall_right:
                # Door
                door_left = 0.38
                door_right = 0.62
                door_top = 0.65
                door_bottom = 0.95
                if door_left <= nx <= door_right and door_top <= ny <= door_bottom:
                    pixels.append(DOOR)
                    continue

                # Window left
                win1_left = 0.12
                win1_right = 0.33
                win1_top = 0.42
                win1_bottom = 0.58
                if win1_left <= nx <= win1_right and win1_top <= ny <= win1_bottom:
                    margin = 0.02
                    if (abs(nx - win1_left) < margin or abs(nx - win1_right) < margin or
                        abs(ny - win1_top) < margin or abs(ny - win1_bottom) < margin):
                        pixels.append(FRAME)
                    else:
                        pixels.append(WINDOW)
                    continue

                # Window right
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

            # Background
            pixels.append(SKY)

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

    # Pixel data
    pixel_data = b''
    for y in range(size):
        for x in range(size):
            idx = y * size + x
            b, g, r, a = pixels[idx]
            pixel_data += struct.pack('BBBB', b, g, r, a)

    and_mask = b'\x00' * ((size + 31) // 32 * 4 * size)
    image_data = bmp_header + pixel_data + and_mask

    # ICO file header
    ico_header = struct.pack('<HHH', 0, 1, 1)

    # ICO directory entry
    w = size if size < 256 else 0
    h = size if size < 256 else 0
    entry = struct.pack('<BBBBHHII', w, h, 0, 0, 1, 32, len(image_data), 22)

    with open(filepath, 'wb') as f:
        f.write(ico_header)
        f.write(entry)
        f.write(image_data)

    print(f"Icon generated: {filepath} ({size}x{size})")


if __name__ == "__main__":
    create_house_icon(32, "house.ico")
    create_house_icon(64, "house_64.ico")
    print("Done - house icons created successfully")
