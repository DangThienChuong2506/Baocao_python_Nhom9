import os
import pygame
try:
    from core import resources as resources
except Exception:
    resources = None


def _load_frames_from_folder(folder, size=None):
    frames = []
    try:
        if not os.path.isdir(folder):
            return frames
        # sort files to keep ordering
        files = sorted([f for f in os.listdir(folder) if f.lower().endswith('.png')])
        for fn in files:
            path = os.path.join(folder, fn)
            try:
                if resources is not None:
                    img = pygame.image.load(resources.resource_path(path)).convert_alpha()
                else:
                    img = pygame.image.load(path).convert_alpha()
                if size and img.get_size() != size:
                    img = pygame.transform.smoothscale(img, size)
                frames.append(img)
            except Exception:
                # ignore broken images
                continue
    except Exception:
        return []
    return frames


def handle_event(event, monster_group, player=None):
    """Handle debug/hack input.

    When the player presses C, set every monster to its death animation and mark it dead.
    This function is defensive: it will never raise if assets or attributes are missing.
    """
    if event.type != pygame.KEYDOWN:
        return
    if event.key != pygame.K_c:
        return

    # paths for monster death frames
    # Prefer new locations but fall back to legacy paths if not present
    goblin_legacy = os.path.join('assets', 'imagesmonster', 'goblins', 'deathmonster')
    goblin_new = os.path.join('assets', 'imagesmonster', 'monster', 'goblins', 'deathmonster')
    goblin_folder = goblin_new if os.path.isdir(goblin_new) else goblin_legacy

    demon_legacy = os.path.join('assets', 'imagesmonster', 'demon', 'demon_death')
    demon_new = os.path.join('assets', 'imagesmonster', 'boss', 'demon', 'demon_death')
    demon_folder = demon_new if os.path.isdir(demon_new) else demon_legacy

    # Try to guess a reasonable size to scale death frames to by inspecting one monster
    sample_size = None
    try:
        for m in monster_group:
            if hasattr(m, 'frames') and len(m.frames) > 0:
                sample_size = m.frames[0].get_size()
                break
    except Exception:
        sample_size = None

    goblin_frames = _load_frames_from_folder(goblin_folder, size=sample_size)
    demon_frames = _load_frames_from_folder(demon_folder, size=sample_size)

    for m in list(monster_group):
        try:
            # only affect monsters that are still alive
            if getattr(m, 'is_dead', False):
                continue

            # choose death frames based on class name or hp_bar_style
            chosen = None
            if getattr(m, '__class__', None) and m.__class__.__name__.lower().startswith('demon'):
                chosen = demon_frames or m.death_frames
            elif getattr(m, 'hp_bar_style', '') == 'demon':
                chosen = demon_frames or m.death_frames
            else:
                chosen = goblin_frames or m.death_frames

            # apply chosen frames if available
            if chosen:
                try:
                    m.death_frames = chosen
                except Exception:
                    pass

            # force-death: switch to death action and prepare for animation
            try:
                if hasattr(m, 'set_action'):
                    m.set_action('death')
                m.frame_idx = 0
                m.is_dead = True
                m.drop_item = True
                # ensure hp bar shows empty if available
                if hasattr(m, 'hp_bar_imgs'):
                    m.hp_bar_idx = len(m.hp_bar_imgs) - 1
                    m.hp_bar_visible = True
                # Note: do NOT set m._counted here. The main loop will detect is_dead and _counted==False
                # and will increment the wave kill counter so waves progress naturally.
            except Exception:
                try:
                    # fallback: try to mark dead and let the loop handle removal
                    m.is_dead = True
                except Exception:
                    pass
        except Exception:
            # never propagate
            continue
