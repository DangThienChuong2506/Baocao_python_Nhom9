import pygame
import time
try:
    from core import resources as resources
except Exception:
    resources = None


def load_item_image():
    # Hàm này trả về ảnh vật phẩm từ assets/imagesitems
    try:
        if resources is not None:
            return resources.load_image('assets/imagesitems/item.png')
    except Exception:
        pass
    return pygame.image.load('assets/imagesitems/item.png').convert_alpha()

class Item(pygame.sprite.Sprite):
    def __init__(self, pos, image=None):
        super().__init__()
        # Nếu không truyền image thì tự động lấy từ assets/imagesitems
        if image is None:
            image = load_item_image()
        self.image = image
        self.rect = self.image.get_rect(center=pos)
        self.spawn_time = pygame.time.get_ticks()  # Lưu thời điểm xuất hiện

    def can_pickup(self):
        # Chỉ cho phép nhặt sau 0.5 giây
        return (pygame.time.get_ticks() - self.spawn_time) >= 500
