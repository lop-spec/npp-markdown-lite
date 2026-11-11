import ctypes as C
from ctypes import wintypes as W
import struct
import zlib

def capture(hwnd, path):
    u = C.WinDLL('user32', use_last_error=True)
    g = C.WinDLL('gdi32', use_last_error=True)
    u.GetWindowRect.argtypes = [W.HWND, C.POINTER(W.RECT)]
    u.GetWindowDC.argtypes = [W.HWND]
    u.GetWindowDC.restype = W.HDC
    u.PrintWindow.argtypes = [W.HWND, W.HDC, W.UINT]
    u.ReleaseDC.argtypes = [W.HWND, W.HDC]
    g.CreateCompatibleDC.argtypes = [W.HDC]
    g.CreateCompatibleDC.restype = W.HDC
    g.CreateCompatibleBitmap.argtypes = [W.HDC, C.c_int, C.c_int]
    g.CreateCompatibleBitmap.restype = W.HBITMAP
    g.SelectObject.argtypes = [W.HDC, W.HGDIOBJ]
    g.SelectObject.restype = W.HGDIOBJ
    g.GetDIBits.argtypes = [W.HDC, W.HBITMAP, W.UINT, W.UINT, W.LPVOID, W.LPVOID, W.UINT]
    g.DeleteObject.argtypes = [W.HGDIOBJ]
    g.DeleteDC.argtypes = [W.HDC]
    rect = W.RECT()
    u.GetWindowRect(hwnd, C.byref(rect))
    width, height = rect.right - rect.left, rect.bottom - rect.top
    source = u.GetWindowDC(hwnd)
    dc = g.CreateCompatibleDC(source)
    bitmap = g.CreateCompatibleBitmap(source, width, height)
    old = g.SelectObject(dc, bitmap)
    try:
        if not u.PrintWindow(hwnd, dc, 2): raise OSError('PrintWindow failed')
        g.SelectObject(dc, old)
        info = C.create_string_buffer(struct.pack('<IiiHHIIiiII', 40, width, -height, 1, 32, 0, 0, 0, 0, 0, 0))
        data = C.create_string_buffer(width * height * 4)
        if not g.GetDIBits(dc, bitmap, 0, height, data, info, 0): raise OSError('GetDIBits failed')
        pixels = data.raw
        rgb = bytearray()
        for row in range(height):
            rgb.append(0)
            start = row * width * 4
            for x in range(width):
                b, green, r, _ = pixels[start + x * 4:start + x * 4 + 4]
                rgb.extend((r, green, b))
        def chunk(kind, value):
            return struct.pack('>I', len(value)) + kind + value + struct.pack('>I', zlib.crc32(kind + value) & 0xffffffff)
        path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(rgb)) + chunk(b'IEND', b''))
    finally:
        g.DeleteObject(bitmap)
        g.DeleteDC(dc)
        u.ReleaseDC(hwnd, source)
