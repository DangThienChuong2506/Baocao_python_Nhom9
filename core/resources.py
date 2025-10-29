import os
import sys
import pygame

# Đóng gói file exe tránh lỗi đường dẫn khi dùng PyInstaller

# Base directory (project root) is parent of core module
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def resource_path(rel_path):
    """Return an absolute path to a resource.

    Works both when running from source and when bundled by PyInstaller
    (uses sys._MEIPASS if available).
    Accepts forward-slash paths and normalizes them to the platform.
    """
    if not rel_path:
        return rel_path
    # normalize separators
    rel = rel_path.replace('/', os.sep)
    base = getattr(sys, '_MEIPASS', None) or BASE_DIR
    return os.path.join(base, rel)


def load_image(rel_path, size=None, convert_alpha=True):
    """Load an image by relative path (under project assets) and optionally scale it.

    rel_path: path like 'assets/imagesplayer/idle/IDLE 1.0.png'
    """
    p = resource_path(rel_path)
    surf = pygame.image.load(p)
    try:
        if convert_alpha:
            surf = surf.convert_alpha()
        else:
            surf = surf.convert()
    except Exception:
        # If convert fails (e.g., no video), keep original
        pass
    if size and surf.get_size() != size:
        try:
            surf = pygame.transform.smoothscale(surf, size)
        except Exception:
            try:
                surf = pygame.transform.scale(surf, size)
            except Exception:
                pass
    return surf


def resource_exists(rel_path):
    return os.path.exists(resource_path(rel_path))
