import math
import os
import pygame
import settings


POSSIBLE_NAMES = ['background2.png', 'background2.jpg', 'background2.jpeg']


def _find_background_path():
    base = os.path.join('assets', 'maps')
    for name in POSSIBLE_NAMES:
        p = os.path.join(base, name)
        if os.path.isfile(p):
            return p
    return None


def _ensure_min_width(surface, min_width):
    """Repeat the surface horizontally until it reaches at least min_width."""
    width, height = surface.get_size()
    if width >= min_width:
        return surface
    repeats = math.ceil(min_width / width)
    # Create a new surface wide enough to allow scrolling.
    extended = pygame.Surface((width * repeats, height)).convert()
    extended.fill((0, 0, 0))
    for i in range(repeats):
        extended.blit(surface, (i * width, 0))
    return extended


def load_bg(screen_width):
    """Load and return a background surface scaled to match screen height with ample width."""
    path = _find_background_path()
    if not path:
        return None
    try:
        try:
            from core import resources as resources
            surf = pygame.image.load(resources.resource_path(path)).convert()
        except Exception:
            surf = pygame.image.load(path).convert()
        ow, oh = surf.get_size()
        target_height = settings.HEIGHT
        if oh <= 0:
            return surf
        scale = target_height / oh
        new_width = max(int(ow * scale), screen_width)
        surf = pygame.transform.smoothscale(surf, (new_width, target_height))
        # Ensure background wide enough so player có không gian di chuyển (>= 3 màn hình).
        min_width = screen_width * 3
        surf = _ensure_min_width(surf, min_width)
        return surf
    except Exception:
        return None
