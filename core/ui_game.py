import os
import pygame
try:
    from core import resources as resources
except Exception:
    resources = None


def draw_monster_hp(screen, monster, hp_img_path='assets/hp/hpmonster/hpms1.png', width=45, height=6, y_offset=5):
    """Vẽ thanh máu lên trên đầu monster."""
    # Nếu là demon (hp_bar_style == 'demon') và đã chết, không vẽ thanh HP boss
    if getattr(monster, 'hp_bar_style', '') == 'demon' and getattr(monster, 'is_dead', False):
        return
    # Allow monsters to control whether their hp bar should be drawn
    if hasattr(monster, 'should_draw_hp') and not monster.should_draw_hp():
        return
    if hasattr(monster, 'hp_bar_imgs') and getattr(monster, 'hp_bar_visible', False):
        idx = min(getattr(monster, 'hp_bar_idx', 0), len(monster.hp_bar_imgs) - 1)
        base_img = monster.hp_bar_imgs[idx]
        target_size = getattr(monster, 'hp_bar_target_size', None)
        if target_size:
            cache = getattr(monster, '_hp_bar_cache', {})
            cache_key = (idx, target_size)
            if cache_key in cache:
                hp_img = cache[cache_key]
            else:
                tw, th = target_size
                w, h = base_img.get_size()
                if w and h:
                    scale = 1.0
                    if tw:
                        scale = tw / w
                    if th:
                        height_after = h * scale
                        if height_after > th:
                            scale = th / h
                    new_size = (max(1, int(round(w * scale))), max(1, int(round(h * scale))))
                    if new_size != (w, h):
                        hp_img = pygame.transform.smoothscale(base_img, new_size)
                    else:
                        hp_img = base_img
                else:
                    hp_img = base_img
                cache[cache_key] = hp_img
                setattr(monster, '_hp_bar_cache', cache)
        else:
            hp_img = base_img
        width, height = hp_img.get_size()
    else:
        try:
            if resources is not None:
                hp_img = resources.load_image(hp_img_path)
            else:
                hp_img = pygame.image.load(hp_img_path)
            hp_img = pygame.transform.smoothscale(hp_img, (width, height))
        except Exception:
            hp_img = pygame.Surface((width, height), pygame.SRCALPHA)
    # Tính vị trí vẽ: căn giữa trên đầu monster
    bar_offset = getattr(monster, 'hp_bar_offset', y_offset)
    x_offset = getattr(monster, 'hp_bar_x_offset', 0)
    x = monster.rect.centerx + x_offset - width // 2
    y = monster.rect.top - bar_offset - height
    screen.blit(hp_img, (x, y))
    # Boss mana HUD removed: Demon and Wizard no longer show a mana bar under HP.
    # (Previously we loaded and rendered assets/mana/manaboss images here.)

def draw_player_hp(screen, player, width=150, height=30, x=20, y=10):
    """
    Vẽ thanh máu player ở góc trên bên trái màn hình.
    """
    hp_imgs = []
    for i in range(6):
        p = f'assets/hp/hpplayer/hpplayer{i+1}.png'
        try:
            if resources is not None:
                hp_imgs.append(resources.load_image(p))
            else:
                hp_imgs.append(pygame.image.load(p).convert_alpha())
        except Exception:
            # placeholder transparent surface
            hp_imgs.append(pygame.Surface((1, 1), pygame.SRCALPHA))
    hp_img = pygame.transform.smoothscale(hp_imgs[getattr(player, 'hp_bar_idx', 0)], (width, height))
    screen.blit(hp_img, (x, y))

def draw_player_mana(screen, player, width=120, height=20, x=16, y=8):
    """
    Vẽ thanh mana player nhỏ hơn, căn giữa dưới thanh máu.
    """
    mana_imgs = []
    for i in range(6):
        p = f'assets/mana/manaplayer/mnplayer{i+1}.png'
        try:
            if resources is not None:
                mana_imgs.append(resources.load_image(p))
            else:
                mana_imgs.append(pygame.image.load(p).convert_alpha())
        except Exception:
            mana_imgs.append(pygame.Surface((1, 1), pygame.SRCALPHA))
    mana_img = pygame.transform.smoothscale(mana_imgs[getattr(player, 'mana_bar_idx', 0)], (width, height))
    # Lấy lại vị trí thanh máu để căn giữa
    hp_width = 160
    hp_x = 20
    hp_y = 10
    x = hp_x + (hp_width - width) // 2
    y = hp_y + 24 + 4  # 4px cách dưới thanh máu
    screen.blit(mana_img, (x, y))

def draw_inventory(screen, font, inventory):
    pass  # Không vẽ gì lên HUD nữa
