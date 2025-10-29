import os
import pygame
from core.monster import Monster
try:
    import settings as _settings
    DEBUG = bool(getattr(_settings, 'DEBUG', False))
except Exception:
    DEBUG = False

try:
    from core import resources as resources
except Exception:
    resources = None

DEBUG_LOGS = False


def load_pixel_font(size):
    candidates = [
        'assets/fonts/PressStart2P.ttf',
        'assets/fonts/press-start-2p.ttf',
        'assets/fonts/pixel.ttf',
        'assets/fonts/PixelFont.ttf',
    ]
    for path in candidates:
        try:
            check = resources.resource_path(path) if resources is not None else path
            if os.path.exists(check):
                try:
                    return pygame.font.Font(check, size)
                except Exception:
                    continue
        except Exception:
            # fallback to direct path check
            try:
                if os.path.exists(path):
                    try:
                        return pygame.font.Font(path, size)
                    except Exception:
                        continue
            except Exception:
                continue
    return pygame.font.SysFont('Consolas', size, bold=True)


def build_demon_animations():
    # Prefer new location assets/imagesmonster/boss/demon but fall back to legacy path
    legacy_base = os.path.join('assets', 'imagesmonster', 'demon')
    new_base = os.path.join('assets', 'imagesmonster', 'boss', 'demon')
    base = new_base if os.path.isdir(new_base) else legacy_base

    def frame_paths(subfolder):
        folder = os.path.join(base, subfolder)
        try:
            resource_folder = resources.resource_path(folder) if resources is not None else folder
            if not os.path.isdir(resource_folder):
                return []
            def sort_key(name):
                digits = ''.join(ch for ch in name if ch.isdigit())
                return int(digits) if digits else 0
            filenames = sorted(
                (fname for fname in os.listdir(resource_folder) if fname.lower().endswith('.png')),
                key=sort_key
            )
            # return relative-style paths as before so other code can pass them through resource_path
            return [os.path.join(folder, fname).replace('\\', '/') for fname in filenames]
        except Exception:
            return []

    return {
        'idle': frame_paths('demon_idle'),
        'run': frame_paths('demon_walk'),
        'attack': frame_paths('demon_cleave'),
        'takehit': frame_paths('demon_take_hit'),
        'death': frame_paths('demon_death'),
    }


def build_bringer_animations():
    """Load animation frame paths for the Bringer boss."""
    base = os.path.join('assets', 'imagesmonster', 'boss', 'bringer')
    if not os.path.isdir(base):
        return {
            'idle': [],
            'run': [],
            'attack': [],
            'attack2': [],
            'takehit': [],
            'death': [],
            'fallback': [],
        }

    def frame_paths(subfolder):
        folder = os.path.join(base, subfolder)
        try:
            resource_folder = resources.resource_path(folder) if resources is not None else folder
            if not os.path.isdir(resource_folder):
                return []
            files = [f for f in os.listdir(resource_folder) if f.lower().endswith('.png')]
        except Exception:
            return []
        # sort numerically when filenames include indexes (e.g., frame0.png)
        def sort_key(name):
            digits = ''.join(ch for ch in name if ch.isdigit())
            return int(digits) if digits else name.lower()
        files.sort(key=sort_key)
        return [os.path.join(folder, f).replace('\\', '/') for f in files]

    anims = {
        'idle': frame_paths('bringerIdle'),
        'run': frame_paths('bringerRun') or frame_paths('bringerWalk'),
        'walk': frame_paths('bringerWalk'),
        'attack': frame_paths('bringerATK'),
        'attack2': frame_paths('bringerATK2'),
        'takehit': frame_paths('bringerHurt'),
        'death': frame_paths('bringerDeath'),
        'fallback': frame_paths('bringerFallback'),
    }
    # remove empty lists for optional animations to keep dictionary lean
    anims = {k: v for k, v in anims.items() if v}
    return anims

# Two-line speech for demon
demon_intro_lines = [
    "Lại một kẻ không biết lượng sức",
    "Muốn rời khỏi đây ngươi phải bước qua xác của ta"
]

demon_death_lines = [
    "Ngươi nghĩ đánh bại được ta?",
    "Ngươi hãy chuẩn bị chết đi..."
]


def _load_boss_hp_paths():
    hp_dir = os.path.join('assets', 'hp', 'hpboss')
    try:
        resource_hp_dir = resources.resource_path(hp_dir) if resources is not None else hp_dir
        if os.path.isdir(resource_hp_dir):
            files = [f for f in os.listdir(resource_hp_dir) if f.lower().endswith('.png')]
            if files:
                def sort_key(name):
                    digits = ''.join(ch for ch in name if ch.isdigit())
                    return int(digits) if digits else name.lower()
                files.sort(key=sort_key)
                return [os.path.join(hp_dir, f).replace('\\', '/') for f in files]
    except Exception:
        pass
    return [f'assets/hp/hpboss/hpboss{i}.png' for i in range(1, 7)]


class Demon(Monster):
    """Specialized Monster for the demon boss with sensible defaults."""
    def __init__(self, pos, ground_y, size=None, min_x=None, max_x=None, item_img=None, **kwargs):
        # Prepare default demon-specific kwargs
        animations = build_demon_animations()
        if size is None:
            inferred_size = None
            for key in ('run', 'idle', 'attack', 'takehit'):
                frames = animations.get(key)
                if frames:
                    try:
                        surface = pygame.image.load(frames[0])
                        inferred_size = surface.get_size()
                        break
                    except Exception:
                        continue
            size = inferred_size or (120, 120)
        hp_bar_paths = _load_boss_hp_paths()
        defaults = {
            'animations': animations,
            'asset_faces_right': False,
            'ground_offset': 20,
            'takehit_on_damage': True,
            'hp_bar_paths': hp_bar_paths,
            'hp_bar_size': (130, 18),
            'hp_bar_always_visible': True,
            'hp_bar_offset': -6,
            # Increase demon shield cooldown so shields reappear less frequently
            # (was 1.5s). Adjust this value if you want a different recovery time.
            'shield_interval': 3.5,
            'shield_duration': 1.0,
        }
        # Merge with caller overrides
        merged = dict(defaults)
        # ensure wizard animations are passed to the Monster base so correct frames load immediately
        try:
            merged['animations'] = animations
        except Exception:
            pass
        merged.update(kwargs)
        super().__init__(pos, ground_y, size=size, min_x=min_x, max_x=max_x, item_img=item_img, **merged)
        # Mark this as demon for game logic
        self.hp_bar_style = 'demon'
        # Speech timers (seconds)
        self.speech_intro_timer = 3.5
        self.speech_death_timer = 0.0
        self._death_timer_started = False
        # font for rendering speech
        try:
            self.font = load_pixel_font(14)
        except Exception:
            self.font = pygame.font.SysFont(None, 14)
        try:
            self.facing_right = False
        except Exception:
            pass
        try:
            self.invincible_duration = max(0.35, float(getattr(self, 'invincible_duration', 0.2)))
        except Exception:
            self.invincible_duration = 0.35

    def should_draw_hp(self):
        # don't draw the boss hp bar after death
        return not self.is_dead

    def render_overlay(self, screen):
        """Render demon-specific overlays: shield aura and speech box. (No mana bar)"""
        # Shield aura (if active)
        if getattr(self, 'shield_active', False):
            radius = int(max(self.rect.width, self.rect.height) * 0.7)
            surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (80, 200, 255, 90), (radius, radius), radius)
            screen.blit(surf, (self.rect.centerx - radius, self.rect.centery - radius))

        # Speech box: intro or death lines
        lines = None
        if getattr(self, 'speech_intro_timer', 0) > 0 and not getattr(self, 'is_dead', False):
            lines = [
                "Lại một kẻ không biết lượng sức",
                "Muốn rời khỏi đây ngươi phải bước qua xác của ta"
            ]
        elif getattr(self, 'speech_death_timer', 0) > 0:
            lines = [
                "Ngươi nghĩ đánh bại được ta là dễ dàng sao?",
                "Ngươi hãy chuẩn bị chết đi..."
            ]
        if lines:
            rendered = [self.font.render(line, True, (255, 255, 255)) for line in lines]
            pad_x, pad_y = 18, 12
            line_gap = 6
            box_w = max(surf_line.get_width() for surf_line in rendered) + pad_x * 2
            box_h = sum(surf_line.get_height() for surf_line in rendered) + pad_y * 2 + line_gap * (len(rendered) - 1)
            box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            box_surf.fill((70, 70, 70, 210))
            y_cursor = pad_y
            for surf_line in rendered:
                x_line = (box_w - surf_line.get_width()) // 2
                box_surf.blit(surf_line, (x_line, y_cursor))
                y_cursor += surf_line.get_height() + line_gap
            x = self.rect.centerx - box_w // 2
            y = self.rect.top - 40 - box_h
            screen.blit(box_surf, (x, y))

    def update(self, dt, player=None):
        # Call base update first (handles AI, shield, death flag, etc.)
        super().update(dt, player)
        # If demon just died, start death speech timer once
        if self.is_dead and not self._death_timer_started:
            self.speech_intro_timer = 0.0
            self.speech_death_timer = 3.5
            self._death_timer_started = True
        # Decrease speech timers
        if getattr(self, 'speech_intro_timer', 0) > 0:
            self.speech_intro_timer = max(0.0, self.speech_intro_timer - dt)
        if getattr(self, 'speech_death_timer', 0) > 0:
            self.speech_death_timer = max(0.0, self.speech_death_timer - dt)
            # decrement post-attack timer if set
            try:
                if getattr(self, '_post_attack_timer', 0.0) > 0.0:
                    self._post_attack_timer = max(0.0, getattr(self, '_post_attack_timer', 0.0) - dt)
            except Exception:
                pass

    def next_hp_bar(self, damage=1):
        try:
            super().next_hp_bar(damage=1)
        except Exception:
            try:
                super().next_hp_bar(damage)
            except Exception:
                pass
class Bringer(Monster):
    """Boss that appears on map 3 after skeleton waves are cleared."""

    def __init__(self, pos, ground_y, size=None, min_x=None, max_x=None, item_img=None, **kwargs):
        animations = kwargs.pop('animations', None) or build_bringer_animations()
        if size is None:
            inferred_size = None
            for key in ('run', 'walk', 'idle', 'attack', 'attack2'):
                frames = animations.get(key)
                if frames:
                    try:
                        surface = pygame.image.load(frames[0])
                        inferred_size = surface.get_size()
                        break
                    except Exception:
                        continue
            size = inferred_size or (140, 140)
        hp_bar_paths = _load_boss_hp_paths()
        defaults = {
            'animations': animations,
            'asset_faces_right': True,
            'ground_offset': 9,
            'takehit_on_damage': True,
            'hp_bar_paths': hp_bar_paths,
            'hp_bar_size': (130, 18),
            'hp_bar_always_visible': True,
            'hp_bar_offset': -32,
            'hp_bar_x_offset': -4,
            'shield_interval': None,
            'shield_duration': 0.0,
        }
        merged = dict(defaults)
        merged.update(kwargs)
        super().__init__(pos, ground_y, size=size, min_x=min_x, max_x=max_x, item_img=item_img, **merged)
        self.hp_bar_style = 'bringer'
        # ensure secondary animations map to expected attributes
        try:
            if 'attack2' in animations and animations['attack2']:
                from core import monster as monster_mod
                self.attack2_frames = [monster_mod.load_image(p, size) for p in animations['attack2']]
                # if primary attack frames missing, use attack2 as default
                if not getattr(self, 'attack_frames', None):
                    self.attack_frames = list(getattr(self, 'attack2_frames', []))
        except Exception:
            pass

        
        # Track attack combo state: count of completed normal attacks. After
        # 3 completed normal attacks, the next attack will use attack2_frames.
        self._bringer_completed_attacks = 0
        # Whether we've handled the current attack's finish (to avoid double-counting)
        self._bringer_attack_finish_handled = False
        try:
            from core import monster as monster_mod
            if 'walk' in animations and animations['walk']:
                self.walk_frames = [monster_mod.load_image(p, size) for p in animations['walk']]
            elif getattr(self, 'run_frames', None):
                self.walk_frames = list(self.run_frames)
        except Exception:
            pass
        try:
            if getattr(self, 'run_frames', None):
                self.frames = self.run_frames
            elif getattr(self, 'walk_frames', None):
                self.frames = self.walk_frames
        except Exception:
            pass
        try:
            self.speed = max(2, getattr(self, 'speed', 2))
        except Exception:
            self.speed = 2
        # Boss attacks hit harder but less frequently than standard monsters
        try:
            # Make Bringer attacks a bit slower by default (increase cooldown)
            self.attack_cooldown_time = max(1.8, float(getattr(self, 'attack_cooldown_time', 1.8)))
        except Exception:
            self.attack_cooldown_time = 1.8
        # Ensure boss arrives from the right, facing the player by default
        try:
            self.facing_right = False
        except Exception:
            pass
        try:
            self.invincible_duration = max(0.35, float(getattr(self, 'invincible_duration', 0.2)))
        except Exception:
            self.invincible_duration = 0.35
        # Encourage run animation while approaching the arena center
        try:
            if getattr(self, 'run_frames', None):
                self.frames = self.run_frames
                self.action = 'run'
                self.anim_speed = 1/10
                self.frame_idx = 0
        except Exception:
            pass
        # Track whether Bringer should prefer run animation (spawn/chase) or walk animation (patrol)
        self._bringer_force_run = True
        # Speech timers and state for Bringer boss
        try:
            self.font = load_pixel_font(14)
        except Exception:
            self.font = pygame.font.SysFont(None, 14)
        # Intro speech: use absolute timestamps (ms) so we don't need dt in update
        now = pygame.time.get_ticks()
        # durations in milliseconds for the two intro lines
        self._speech_intro_start = now
        self._speech_intro_durations = (4000, 3500)
        # Death speech will be started when the boss dies (timestamp stored in _speech_death_start)
        self._speech_death_start = 0
        self._speech_death_duration = 5000
        self._death_speech_started = False

    def should_draw_hp(self):
        return not getattr(self, 'is_dead', False)

    def render_overlay(self, screen):
        """Render Bringer-specific speech overlay: two intro lines in sequence, and a death line."""
        lines = None
        # Determine which lines to show based on timestamps
        try:
            now = pygame.time.get_ticks()
        except Exception:
            now = 0

        # Intro sequence (first then second) while alive
        if not getattr(self, 'is_dead', False) and getattr(self, '_speech_intro_start', 0):
            try:
                d1, d2 = getattr(self, '_speech_intro_durations', (4000, 3500))
                elapsed = max(0, now - int(getattr(self, '_speech_intro_start', 0)))
                if elapsed < d1:
                    lines = ["Ngươi có thể đánh bại được hai thuộc hạ của ta thật là không phải kẻ tầm thường"]
                elif elapsed < d1 + d2:
                    lines = ["Ngươi sẽ phải xuống địa ngục tại đây"]
                else:
                    lines = None
            except Exception:
                lines = None

        # If boss died, ensure death speech start timestamp is set and show death line while within duration
        if getattr(self, 'is_dead', False):
            try:
                if not getattr(self, '_death_speech_started', False):
                    self._death_speech_started = True
                    self._speech_death_start = now
                if getattr(self, '_speech_death_start', 0):
                    elapsed_d = max(0, now - int(getattr(self, '_speech_death_start', 0)))
                    if elapsed_d < int(getattr(self, '_speech_death_duration', 5000)):
                        lines = ["Ta đã thật sự thua loài người các ngươi sao, ta sẽ trở lại, loài người hãy đợi đấy"]
                    else:
                        lines = None
            except Exception:
                pass

        if lines:
            try:
                # Helper: wrap a long text into multiple lines that fit max_width
                def _wrap_text(text, font, max_width):
                    words = text.split()
                    lines_out = []
                    cur = ''
                    for w in words:
                        test = (cur + ' ' + w).strip() if cur else w
                        try:
                            if font.size(test)[0] <= max_width:
                                cur = test
                            else:
                                if cur:
                                    lines_out.append(cur)
                                # if single word longer than max_width, force-break the word
                                if font.size(w)[0] > max_width:
                                    # break the word into chunks
                                    chunk = ''
                                    for ch in w:
                                        if font.size(chunk + ch)[0] <= max_width:
                                            chunk += ch
                                        else:
                                            if chunk:
                                                lines_out.append(chunk)
                                            chunk = ch
                                    if chunk:
                                        cur = chunk
                                    else:
                                        cur = ''
                                else:
                                    cur = w
                        except Exception:
                            # on error fall back to no wrapping
                            return [text]
                    if cur:
                        lines_out.append(cur)
                    return lines_out

                # decide a sensible max width for the speech box (60% of screen or up to 700px)
                try:
                    max_w = min(700, int(screen.get_width() * 0.6))
                except Exception:
                    max_w = 500

                wrapped_lines = []
                for t in lines:
                    wrapped_lines.extend(_wrap_text(t, self.font, max_w))

                rendered = [self.font.render(line, True, (255, 255, 255)) for line in wrapped_lines]
                pad_x, pad_y = 18, 12
                line_gap = 6
                box_w = max(s.get_width() for s in rendered) + pad_x * 2
                box_h = sum(s.get_height() for s in rendered) + pad_y * 2 + line_gap * (len(rendered) - 1)
                box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
                # semi-opaque dark background to ensure readability
                box_surf.fill((30, 30, 30, 220))
                y_cursor = pad_y
                for surf_line in rendered:
                    x_line = (box_w - surf_line.get_width()) // 2
                    box_surf.blit(surf_line, (x_line, y_cursor))
                    y_cursor += surf_line.get_height() + line_gap
                x = self.rect.centerx - box_w // 2
                y = self.rect.top - 40 - box_h
                screen.blit(box_surf, (x, y))
            except Exception:
                pass

    def next_hp_bar(self, damage=1):
        try:
            super().next_hp_bar(damage=1)
        except Exception:
            try:
                super().next_hp_bar(damage)
            except Exception:
                pass

    def set_action(self, action, player=None, attack_range=40):
        # Remap "walk" requests to "run" so base movement logic stays intact.
        remapped = action
        if action == 'walk':
            remapped = 'run'

        is_new_attack = remapped == 'attack' and getattr(self, 'action', None) != 'attack'
        use_attack2 = False
        if is_new_attack and getattr(self, 'attack2_frames', None):
            # Use completed-attack counter: after 3 completed normal attacks,
            # the next attack will be attack2. We update this counter when the
            # attack animation finishes in update().
            completed = getattr(self, '_bringer_completed_attacks', 0)
            if completed >= 3:
                use_attack2 = True

        # Avoid calling base set_action for attack to prevent base-class repositioning
        # which moves the monster's centerx near the player. Bringer should face
        # the player but keep its own x position when starting an attack.
        if remapped == 'attack' and is_new_attack:
            # set basic attack state without triggering Monster's reposition logic
            try:
                self.action = 'attack'
                self.frame_idx = 0
                self.anim_timer = 0.0
            except Exception:
                pass

            # decide frames (may be attack or attack2)
            if use_attack2 and getattr(self, 'attack2_frames', None):
                self.frames = self.attack2_frames
                # slower attack animation for special attack
                self.anim_speed = 1/9
            else:
                if getattr(self, 'attack_frames', None):
                    self.frames = self.attack_frames
                    # slower normal attack animation
                    self.anim_speed = 1/9

            # face player if provided but do NOT change self.rect.centerx
            if player is not None:
                try:
                    self.facing_right = self.rect.centerx < player.rect.centerx
                except Exception:
                    pass

            try:
                if self.frames:
                    self.image = self._orient_frame(self.frames[self.frame_idx])
            except Exception:
                pass
        else:
            # non-attack actions: use base behavior
            try:
                super().set_action(remapped, player=player, attack_range=attack_range)
            except Exception:
                try:
                    super().set_action(remapped, None, attack_range)
                except Exception:
                    pass
        if remapped == 'run':
            if getattr(self, '_bringer_force_run', False) and getattr(self, 'run_frames', None):
                if self.frames is not self.run_frames:
                    self.frames = self.run_frames
                self.anim_speed = 1/10
            elif getattr(self, 'walk_frames', None):
                if self.frames is not self.walk_frames:
                    self.frames = self.walk_frames
                self.anim_speed = 1/12
            try:
                self.image = self._orient_frame(self.frames[self.frame_idx])
            except Exception:
                pass

    def update(self, dt, player=None):
        target_data = getattr(self, 'target_pos', None)
        if isinstance(target_data, (tuple, list)) and target_data:
            target_x = target_data[0]
        else:
            target_x = self.rect.centerx
        entering = self.rect.centerx > target_x
        chasing = False
        if player is not None and not getattr(player, 'is_dead', False):
            distance = abs(self.rect.centerx - player.rect.centerx)
            chasing = distance < 220
        self._bringer_force_run = entering or chasing
        super().update(dt, player)

        # Ensure Bringer uses its dedicated death animation and is removed after it finishes.
        # If HP bars reached the final index but some external flow didn't set is_dead yet,
        # force the death action, clear shields/heals and mark for removal so the death
        # animation from assets/imagesmonster/boss/bringer/bringerDeath plays then the
        # sprite is killed (Monster.update will handle frame progression and kill()).
        try:
            total_idx = len(getattr(self, 'hp_bar_imgs', [])) - 1
            if total_idx >= 0 and int(getattr(self, 'hp_bar_idx', 0)) >= total_idx and not getattr(self, 'is_dead', False):
                try:
                    self.set_action('death')
                except Exception:
                    pass
                try:
                    self.is_dead = True
                except Exception:
                    pass
                try:
                    self.drop_item = True
                    self.drop_item_pos = self.rect.midbottom
                except Exception:
                    pass
                # Turn off any active healing/shield so the boss doesn't re-enter alive states
                try:
                    self.healing = False
                except Exception:
                    pass
                try:
                    self._one_time_shield_active = False
                    self.shield_active = False
                    self.shield_active_timer = 0.0
                except Exception:
                    pass
                try:
                    # start death speech timestamp for overlay if needed
                    self._death_speech_started = True
                    self._speech_death_start = pygame.time.get_ticks()
                except Exception:
                    pass
        except Exception:
            pass
        if self.action == 'run':
            if self._bringer_force_run and getattr(self, 'run_frames', None):
                if self.frames is not self.run_frames:
                    self.frames = self.run_frames
                    self.anim_speed = 1/10
            elif getattr(self, 'walk_frames', None):
                if self.frames is not self.walk_frames:
                    self.frames = self.walk_frames
                    self.anim_speed = 1/12
            try:
                self.image = self._orient_frame(self.frames[self.frame_idx])
            except Exception:
                pass

        # Detect finishing of an attack animation and update completed-attack counter
        try:
            if getattr(self, 'action', None) == 'attack' and getattr(self, 'frames', None):
                last_idx = max(0, len(self.frames) - 1)
                if getattr(self, 'frame_idx', 0) >= last_idx:
                    if not getattr(self, '_bringer_attack_finish_handled', False):
                        try:
                            just_frames = getattr(self, 'frames', None)
                            played_attack2 = just_frames is getattr(self, 'attack2_frames', None)
                        except Exception:
                            played_attack2 = False
                        try:
                            if played_attack2:
                                # after special attack, reset counter
                                self._bringer_completed_attacks = 0
                            else:
                                # increment completed normal attacks (cap at 3)
                                self._bringer_completed_attacks = min(3, getattr(self, '_bringer_completed_attacks', 0) + 1)
                        except Exception:
                            try:
                                self._bringer_completed_attacks = getattr(self, '_bringer_completed_attacks', 0) + 1
                            except Exception:
                                pass
                        try:
                            self._bringer_attack_finish_handled = True
                        except Exception:
                            pass
                        try:
                            # Return to idle and impose cooldown so AI re-evaluates
                            self.set_action('idle')
                        except Exception:
                            pass
                        try:
                            self.attack_cooldown = float(getattr(self, 'attack_cooldown_time', 1.4))
                        except Exception:
                            self.attack_cooldown = 1.4
                else:
                    try:
                        self._bringer_attack_finish_handled = False
                    except Exception:
                        pass
        except Exception:
            pass




def build_wizard_animations():
    """Build animation paths for the Wizard boss.

    Expecting folders under assets/imagesmonster/boss/wizard like:
      WizardIdle, WizardRun, WizardAttack1, WizardAttack2, WizardDeath, WizardTakehit, WizardJump
    Returns dict compatible with Monster animations parameter.
    """
    import os
    legacy_base = os.path.join('assets', 'imagesmonster', 'wizard')
    new_base = os.path.join('assets', 'imagesmonster', 'boss', 'wizard')
    base = new_base if os.path.isdir(new_base) else legacy_base

    def _list_sorted(sub):
        p = os.path.join(base, sub)
        if not os.path.isdir(p):
            return []
        files = [f for f in sorted(os.listdir(p)) if f.lower().endswith('.png')]
        return [os.path.join(p, f).replace('\\', '/') for f in files]

    anims = {}
    # map expected subfolders to animation keys
    idle = _list_sorted('WizardIdle') or _list_sorted('wizard_idle') or _list_sorted('Idle')
    run = _list_sorted('WizardRun') or _list_sorted('wizard_run') or _list_sorted('Run')
    # Prefer WizardAttack1 as attack1, and WizardAttack2 as attack2; fall back to generic Attack for attack1
    attack1 = _list_sorted('WizardAttack1') or _list_sorted('WizardAttack') or _list_sorted('wizard_attack') or _list_sorted('Attack')
    attack2 = _list_sorted('WizardAttack2') or _list_sorted('wizard_attack2') or _list_sorted('Attack2')
    takehit = _list_sorted('WizardTakehit') or _list_sorted('wizard_takehit') or _list_sorted('Takehit')
    death = _list_sorted('WizardDeath') or _list_sorted('WizardDie') or _list_sorted('Death')

    if idle:
        anims['idle'] = idle
    if run:
        anims['run'] = run
    if attack1:
        anims['attack1'] = attack1
    if attack2:
        anims['attack2'] = attack2
    if takehit:
        anims['takehit'] = takehit
    if death:
        anims['death'] = death
    return anims


class Wizard(Monster):
    def __init__(self, pos, ground_y, size=(120, 120), min_x=None, max_x=None, item_img=None, **kwargs):
        animations = build_wizard_animations()
        hp_bar_paths = _load_boss_hp_paths()
        defaults = {
            # Assume wizard assets face to the right; let Monster._orient_frame handle flips
            'asset_faces_right': True,
            # align wizard to the ground: some wizard art sits above the feet, apply negative offset so
            # rect.bottom aligns to the visible ground. Tweak this if sprites are still floating.
            # Make wizard sit slightly lower visually; increase magnitude if still floating.
            # Nudged up 1px from -36 to -35 to slightly raise the sprite.
            'ground_offset': -34,
            'takehit_on_damage': True,
            'hp_bar_paths': hp_bar_paths,
            'hp_bar_size': (120, 16),
            'hp_bar_always_visible': True,
            'hp_bar_offset': -6,
            # wizard does not use shield behavior
        }
        merged = dict(defaults)
        merged.update(kwargs)
        super().__init__(pos, ground_y, size=size, min_x=min_x, max_x=max_x, item_img=item_img, **merged)
        self.hp_bar_style = 'wizard'
        # Make wizard lose HP more slowly: increase invincibility window and clamp damage per hit
        try:
            # bosses should be harder to burst down
            self.invincible_duration = max(getattr(self, 'invincible_duration', 0.2), 0.6)
        except Exception:
            self.invincible_duration = 0.6
        # Ensure attack1_frames and attack2_frames exist on the instance.
        # Monster.__init__ may populate generic 'attack_frames' but not 'attack1_frames'/'attack2_frames'.
        try:
            from core import monster as monster_mod
            # Populate named frames from provided animations so Wizard uses its own assets
            try:
                if 'idle' in animations and animations['idle']:
                    try:
                        self.idle_frames = [monster_mod.load_image(p, size) for p in animations['idle']]
                    except Exception:
                        pass
                if 'run' in animations and animations['run']:
                    try:
                        self.run_frames = [monster_mod.load_image(p, size) for p in animations['run']]
                    except Exception:
                        pass
                # Load attack1 and attack2 frames separately if present
                if 'attack1' in animations and animations['attack1']:
                    try:
                        self.attack1_frames = [monster_mod.load_image(p, size) for p in animations['attack1']]
                    except Exception:
                        pass
                if 'attack2' in animations and animations['attack2']:
                    try:
                        self.attack2_frames = [monster_mod.load_image(p, size) for p in animations['attack2']]
                    except Exception:
                        pass
                # Fallback: if only generic 'attack' key present (older assets), map it to attack1
                if 'attack' in animations and animations['attack'] and not getattr(self, 'attack1_frames', None):
                    try:
                        self.attack1_frames = [monster_mod.load_image(p, size) for p in animations['attack']]
                    except Exception:
                        pass
            except Exception:
                pass
                # Ensure legacy `attack_frames` exists for compatibility with Monster.set_action
                # Prefer attack1_frames (new assets) as the default attack animation.
                try:
                    if getattr(self, 'attack1_frames', None):
                        self.attack_frames = self.attack1_frames
                    elif getattr(self, 'attack2_frames', None):
                        self.attack_frames = self.attack2_frames
                    else:
                        # fall back to any existing attack_frames or empty list
                        self.attack_frames = list(getattr(self, 'attack_frames', []) or [])
                except Exception:
                    self.attack_frames = list(getattr(self, 'attack_frames', []) or [])
        except Exception:
            # Best-effort: ensure attributes exist
            if not hasattr(self, 'attack_frames'):
                self.attack_frames = []
        # Debug: report how many frames were loaded for each key animation
        try:
            ai = len(getattr(self, 'idle_frames', []))
            a1 = len(getattr(self, 'attack1_frames', []))
            a2 = len(getattr(self, 'attack2_frames', []))
            rf = len(getattr(self, 'run_frames', []))
            if DEBUG and DEBUG_LOGS:
                print(f"[DEBUG wizard_init] idle={ai} run={rf} attack1={a1} attack2={a2} asset_faces_right={getattr(self,'asset_faces_right',None)} facing_right={getattr(self,'facing_right',None)} size={getattr(self,'rect',None) and getattr(self,'rect').size}", flush=True)
        except Exception:
            pass
        # optional speech or FX timers
        try:
            self.font = load_pixel_font(12)
        except Exception:
            import pygame
            self.font = pygame.font.SysFont(None, 12)
        # Intro speech shown when wizard xuất hiện
        self.speech_intro_timer = 6.0
        self.speech_intro_text = (
            "Ta không ngờ rằng ngay cả Demon cũng bị ngươi đánh bại, ngươi sẽ phải để mạng lại nơi này"
        )
        self.speech_death_timer = 0.0
        self.speech_death_text = (
            "Ta mà lại thất bại trước kẻ như ngươi sao, ngươi hãy chờ đến địa ngục tiếp theo đi"
        )
        self._death_speech_started = False
        # Ensure wizard starts in idle state (use WizardIdle frames) and is grounded
        try:
            # set frames and initial image explicitly to avoid fallback to Monster defaults
            try:
                self.frames = getattr(self, 'idle_frames', self.frames)
                self.frame_idx = 0
                self.image = self._orient_frame(self.frames[self.frame_idx])
            except Exception:
                pass
            self.set_action('idle')
        except Exception:
            pass
        # Map current mana (0..max_mana) to mana_bar_idx used by the HUD (0..steps-1)
        # NOTE: HUD images are ordered manaboss1..N where manaboss1 should represent FULL mana.
        try:
            steps = max(1, int(getattr(self, 'mana_bar_steps', 6)))
            max_m = float(getattr(self, 'max_mana', 100))
            cur = float(getattr(self, 'mana', 0))
            prop = 0.0
            if max_m > 0:
                prop = max(0.0, min(1.0, cur / max_m))
            # convert to index where 0 == full (manaboss1) and steps-1 == empty (manabossN)
            idx_forward = int(round(prop * (steps - 1)))
            idx = (steps - 1) - idx_forward
            idx = max(0, min(steps - 1, idx))
            self.mana_bar_idx = idx
        except Exception:
            pass
        try:
            # align bottom to ground using ground_offset so visible feet line up with the environment
            self.ground_y = ground_y
            # Monster/Player convention: rect.bottom should equal ground_y - ground_offset
            try:
                target_bottom = int(ground_y - getattr(self, 'ground_offset', 0))
                # prefer bottomleft when an explicit x was provided in pos
                try:
                    self.rect.bottomleft = (pos[0], target_bottom)
                except Exception:
                    self.rect.bottom = target_bottom
            except Exception:
                # fallback to raw ground_y if something goes wrong
                try:
                    self.rect.bottom = ground_y
                except Exception:
                    pass
        except Exception:
            pass
        # Do not manually flip frames here; use Monster._orient_frame() which flips
        # frames at draw/update time based on `self.facing_right` and `self.asset_faces_right`.
        # death state tracking
        self._death_animation_started = False
        # attack state: support attack1/attack2 chaining
        self._attack_finish_handled = False
        # how many consecutive attack1s have been performed
        self._attack1_streak = 0
        self._attack1_max = 3
        # Wizard-specific attack tuning
        # how close the player must be for the wizard to trigger its attack routine
        self.attack_range = 80
        # how far the wizard can 'see' the player and engage (larger than attack_range)
        self.vision_range = 260
        # cooldown between consecutive attack attempts (seconds)
        self.attack_cooldown_time = 1.6
        self.attack_cooldown = 0.0
        # Animation smoothing: target duration (seconds) for attack animations
        self.attack_anim_duration = 0.9
        # Reposition smoothing when starting an attack: total time and runtime fields
        self._attack_reposition_time_total = 0.08
        self._attack_reposition_timer = 0.0
        self._attack_reposition_start_centerx = None
        self._attack_reposition_target_centerx = None
        # Minimum distance (px) tolerance to be considered 'in position' for attacks
        self.reposition_threshold = 8
        # Instead of teleporting, walk toward attack position
        self._attack_walk_target = None
        self._attack_walk_speed = 3
        # Mana system for Wizard
        try:
            self.mana = 100
            self.max_mana = 100
            self.mana_recharge_rate = 20.0  # mana per second
            self.mana_recharge_enabled = True
        except Exception:
            self.mana = 100
            self.max_mana = 100
            self.mana_recharge_rate = 20.0
            self.mana_recharge_enabled = True
        # Start full so HUD shows manaboss1 (full image is index 0 after our inverted mapping)
        try:
            self.mana = float(self.max_mana)
        except Exception:
            self.mana = 100.0
        # mana bar index used by HUD drawing (0..N-1). Default to 0 and 6 steps.
        self.mana_bar_idx = 0
        self.mana_bar_steps = 6
        # Preload boss mana images (assets/mana/manaboss) so HUD uses the exact files
        try:
            mana_dir = os.path.join('assets', 'mana', 'manaboss')
            imgs = []
            names = []
            # Try to load manaboss1..6 in order explicitly if they exist
            for i in range(1, 7):
                p = os.path.join(mana_dir, f'manaboss{i}.png')
                if os.path.exists(p):
                    try:
                        imgs.append(pygame.image.load(p).convert_alpha())
                        names.append(f'manaboss{i}.png')
                    except Exception:
                        continue
            # If explicit set not found, fallback to reading directory and sorting by numeric suffix
            if not imgs and os.path.isdir(mana_dir):
                files = [f for f in os.listdir(mana_dir) if f.lower().endswith('.png')]
                def _sort_key(fn):
                    import re
                    m = re.search(r'(\d+)(?=\.png$)', fn, re.IGNORECASE)
                    if m:
                        return int(m.group(1))
                    return fn.lower()
                files.sort(key=_sort_key)
                for fname in files:
                    p = os.path.join(mana_dir, fname)
                    try:
                        imgs.append(pygame.image.load(p).convert_alpha())
                        names.append(fname)
                    except Exception:
                        continue
            if imgs:
                self._mana_imgs = imgs
                self._mana_img_names = names
                self.mana_bar_steps = len(imgs)
            else:
                self._mana_imgs = []
                self._mana_img_names = []
        except Exception:
            self._mana_imgs = []
            self._mana_img_names = []
        # stepwise regen timer (boss mana uses discrete images manaboss1..N)
        self._mana_regen_timer = 0.0
        # seconds per step: match player default (1.5s per mana step)
        # Có thể override bằng settings.MANA_REGEN_INTERVAL (nếu importable)
        try:
            import settings as _settings
            self.mana_regen_interval = float(getattr(_settings, 'MANA_REGEN_INTERVAL', 1.5))
        except Exception:
            self.mana_regen_interval = 1.5
        # legacy fields (kept for compatibility but not used by HUD)
        self.mana_img = None
        self.mana_img_size = (80, 12)
    def render_overlay(self, screen):
        # Wizard overlay: (no shield aura)
        # Draw mana overlay above the boss (if image present)
        try:
            if getattr(self, 'mana_img', None) is not None:
                percent = 0.0
                try:
                    percent = max(0.0, min(1.0, float(self.mana) / float(self.max_mana)))
                except Exception:
                    percent = 0.0
                full_w = self.mana_img.get_width()
                h = self.mana_img.get_height()
                clip_w = int(full_w * percent)
                x = self.rect.centerx - full_w // 2
                y = self.rect.top - 8 - h
                if clip_w > 0:
                    try:
                        part = self.mana_img.subsurface((0, 0, clip_w, h))
                        screen.blit(part, (x, y))
                    except Exception:
                        temp = self.mana_img.copy()
                        temp.set_alpha(int(255 * percent))
                        screen.blit(temp, (x, y))
                else:
                    try:
                        bg = pygame.Surface((full_w, h), pygame.SRCALPHA)
                        bg.fill((40, 40, 40, 180))
                        screen.blit(bg, (x, y))
                    except Exception:
                        pass
        except Exception:
            pass
        # Show intro speech in rectangular box while timer active
        if getattr(self, 'speech_intro_timer', 0.0) > 0.0:
            try:
                lines = []
                text = self.speech_intro_text
                # simple manual wrap to roughly two lines
                if len(text) > 55:
                    split_idx = text.rfind(' ', 0, len(text)//2 + 12)
                    if split_idx == -1:
                        split_idx = len(text)//2
                    lines.append(text[:split_idx].strip())
                    lines.append(text[split_idx:].strip())
                else:
                    lines.append(text)
                font = getattr(self, 'font', None) or load_pixel_font(12)
                rendered = [font.render(line, True, (255, 255, 255)) for line in lines]
                pad_x, pad_y = 18, 10
                line_gap = 6
                box_w = max(surf_line.get_width() for surf_line in rendered) + pad_x * 2
                box_h = sum(surf_line.get_height() for surf_line in rendered) + pad_y * 2 + line_gap * (len(rendered) - 1)
                box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
                box_surf.fill((50, 50, 70, 210))
                y_cursor = pad_y
                for surf_line in rendered:
                    x_line = (box_w - surf_line.get_width()) // 2
                    box_surf.blit(surf_line, (x_line, y_cursor))
                    y_cursor += surf_line.get_height() + line_gap
                box_x = self.rect.centerx - box_w // 2
                box_y = self.rect.top - box_h - 16
                screen.blit(box_surf, (box_x, box_y))
            except Exception:
                pass
        elif getattr(self, 'speech_death_timer', 0.0) > 0.0:
            try:
                lines = []
                text = self.speech_death_text
                if len(text) > 55:
                    split_idx = text.rfind(' ', 0, len(text)//2 + 12)
                    if split_idx == -1:
                        split_idx = len(text)//2
                    lines.append(text[:split_idx].strip())
                    lines.append(text[split_idx:].strip())
                else:
                    lines.append(text)
                font = getattr(self, 'font', None) or load_pixel_font(12)
                rendered = [font.render(line, True, (255, 255, 255)) for line in lines]
                pad_x, pad_y = 18, 10
                line_gap = 6
                box_w = max(surf_line.get_width() for surf_line in rendered) + pad_x * 2
                box_h = sum(surf_line.get_height() for surf_line in rendered) + pad_y * 2 + line_gap * (len(rendered) - 1)
                box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
                box_surf.fill((50, 50, 70, 210))
                y_cursor = pad_y
                for surf_line in rendered:
                    x_line = (box_w - surf_line.get_width()) // 2
                    box_surf.blit(surf_line, (x_line, y_cursor))
                    y_cursor += surf_line.get_height() + line_gap
                box_x = self.rect.centerx - box_w // 2
                box_y = self.rect.top - box_h - 16
                screen.blit(box_surf, (box_x, box_y))
            except Exception:
                pass

    def set_action(self, action, player=None, attack_range=40):
        # If shield is active, ignore takehit so shield properly blocks damage animation
        # no shield behavior for wizard; delegate takehit to base

        # Attack handling: base code calls set_action('attack') so dispatch to
        # attack1/attack2 frames here. This keeps compatibility while allowing
        # wizard-specific effects (heal/shield) only on attack2.
        if action == 'attack':
            # if already attacking, don't restart
            try:
                if getattr(self, 'action', None) == 'attack':
                    return
            except Exception:
                pass

            # Decide which attack variant to use. Default to attack1_frames when
            # present, and use attack2_frames after _attack1_max consecutive attack1s.
            try:
                use_attack2 = False
                if getattr(self, '_attack1_max', 0) and getattr(self, '_attack1_streak', 0) >= getattr(self, '_attack1_max', 0):
                    # Only use attack2 if we actually have attack2 frames
                    if getattr(self, 'attack2_frames', None):
                        use_attack2 = True

                if use_attack2:
                    chosen_frames = getattr(self, 'attack2_frames', None) or getattr(self, 'attack_frames', None)
                    chosen_name = 'attack2'
                else:
                    chosen_frames = getattr(self, 'attack1_frames', None) or getattr(self, 'attack_frames', None)
                    chosen_name = 'attack1'

                if not chosen_frames:
                    # fallback to base behavior which will set attack_frames if available
                    super().set_action('attack', player, attack_range)
                    return

                # set animation frames and metadata
                self.action = 'attack'
                self.frames = chosen_frames
                if DEBUG and DEBUG_LOGS:
                    try:
                        print(f"[DEBUG Wizard] set_action attack -> {chosen_name} frames={len(getattr(self, chosen_name + '_frames', self.frames))} streak={getattr(self,'_attack1_streak',None)}", flush=True)
                    except Exception:
                        pass
                # finalize animation state
                try:
                    self.frame_idx = 0
                    self.anim_speed = getattr(self, 'attack_anim_duration', 0.9) / max(1, len(self.frames))
                except Exception:
                    self.anim_speed = 1 / 10
                self.anim_timer = 0.0

                # face player if provided
                if player is not None:
                    try:
                        self.facing_right = self.rect.centerx < player.rect.centerx
                    except Exception:
                        pass

                # Apply Wizard-specific effect on attack2: heal-over-time.
                # attack1 does NOT trigger heal.
                try:
                    if chosen_name == 'attack2':
                        if hasattr(self, 'start_heal'):
                            try:
                                self.start_heal(duration=2.0)
                            except Exception:
                                pass
                except Exception:
                    pass

                return
            except Exception:
                try:
                    super().set_action('attack', player, attack_range)
                except Exception:
                    pass
                return

        # non-attack actions -> delegate to base
        try:
            super().set_action(action, player, attack_range)
        except Exception:
            try:
                super().set_action(action, None, attack_range)
            except Exception:
                pass
        # If run action, tune animation speed to match run frames
        if action == 'run':
            try:
                if getattr(self, 'run_frames', None):
                    desired_run_cycle = 0.55
                    frame_count = max(1, len(self.run_frames))
                    self.anim_speed = desired_run_cycle / frame_count
                    self.run_anim_speed = self.anim_speed
                else:
                    self.anim_speed = getattr(self, 'run_anim_speed', 1/14)
            except Exception:
                pass

    def update(self, dt, player=None):
        # Recharge mana over time (before other logic)
        try:
            if getattr(self, 'mana_recharge_enabled', False) and getattr(self, 'mana', 0) < getattr(self, 'max_mana', 100):
                self.mana = min(self.max_mana, self.mana + self.mana_recharge_rate * dt)
        except Exception:
            pass
        """Delegate update to Monster so Wizard AI matches Demon/Monster behavior.
        Keep run animation tuning after update so visuals match movement.
        """
        try:
            super().update(dt, player)
        except Exception:
            try:
                super().update(dt, None)
            except Exception:
                pass
        if getattr(self, 'is_dead', False) and not getattr(self, '_death_speech_started', False):
            try:
                self.speech_intro_timer = 0.0
                self.speech_death_timer = 5.0
                self._death_speech_started = True
            except Exception:
                pass
        # If the player is dead, cancel any scheduled attacks and stop attacking
        try:
            if player is not None and getattr(player, 'action', None) == 'death':
                try:
                    # cancel attack cooldowns
                    self.attack_cooldown = 0.0
                except Exception:
                    pass
                try:
                    if getattr(self, 'action', None) in ('attack',):
                        self.set_action('idle')
                except Exception:
                    pass
                # don't run further attack scheduling/logic
                return
        except Exception:
            pass
        # Debug: print status when player near so we can see why attacks aren't firing
        # ...existing code...
        # If currently running, ensure run anim speed matches tuned value
        try:
            if getattr(self, 'action', None) == 'run' and getattr(self, 'run_frames', None):
                desired_run_cycle = 0.55
                frame_count = max(1, len(self.run_frames))
                self.anim_speed = desired_run_cycle / frame_count
        except Exception:
            pass
        # Detect finishing Attack (reset handled flag)
        try:
            if getattr(self, 'action', None) == 'attack' and getattr(self, 'frames', None):
                last_idx = max(0, len(self.frames) - 1)
                if getattr(self, 'frame_idx', 0) >= last_idx:
                    if not getattr(self, '_attack_finish_handled', False):
                        try:
                            if DEBUG and DEBUG_LOGS:
                                print(f"[DEBUG Wizard] attack finished action={getattr(self,'action',None)} frame_idx={getattr(self,'frame_idx',None)} last_idx={last_idx} streak={getattr(self,'_attack1_streak',None)}", flush=True)
                        except Exception:
                            pass
                        try:
                            # mark handled to avoid repeating this block
                            self._attack_finish_handled = True
                        except Exception:
                            pass
                        # Update attack streaks and schedule next behavior:
                        try:
                            # Determine which attack variant just played
                            just_frames = getattr(self, 'frames', None)
                            played_attack1 = just_frames is getattr(self, 'attack1_frames', None)
                            played_attack2 = just_frames is getattr(self, 'attack2_frames', None)
                        except Exception:
                            played_attack1 = False
                            played_attack2 = False
                        try:
                            if played_attack1:
                                # increment streak but cap at max
                                try:
                                    self._attack1_streak = min(getattr(self, '_attack1_max', 3), getattr(self, '_attack1_streak', 0) + 1)
                                except Exception:
                                    self._attack1_streak = getattr(self, '_attack1_streak', 0) + 1
                            elif played_attack2:
                                # after attack2, reset streak so next attacks start with attack1
                                try:
                                    self._attack1_streak = 0
                                except Exception:
                                    self._attack1_streak = 0
                        except Exception:
                            pass
                        try:
                            # Return to idle and set attack cooldown so AI re-evaluates and triggers next attack
                            try:
                                self.set_action('idle')
                            except Exception:
                                pass
                            # impose cooldown before next attack
                            try:
                                self.attack_cooldown = float(getattr(self, 'attack_cooldown_time', 1.6))
                            except Exception:
                                self.attack_cooldown = 1.6
                        except Exception:
                            pass
                else:
                    try:
                        self._attack_finish_handled = False
                    except Exception:
                        pass
        except Exception:
            pass

        # Stepwise mana-bar regeneration: decrement mana_bar_idx (toward 0 == full) over time
        try:
            if getattr(self, 'mana_recharge_enabled', False) and getattr(self, 'mana_bar_idx', 0) > 0:
                # accumulate timer
                self._mana_regen_timer = getattr(self, '_mana_regen_timer', 0.0) + dt
                interval = float(getattr(self, 'mana_regen_interval', 1.2))
                steps = max(1, int(getattr(self, 'mana_bar_steps', 6)))
                mana_imgs = getattr(self, '_mana_imgs', [])
                # reduce index by whole steps passed
                while self._mana_regen_timer >= interval and self.mana_bar_idx > 0:
                    self._mana_regen_timer -= interval
                    try:
                        if len(mana_imgs) >= 3:
                            self.mana_bar_idx = max(0, int(self.mana_bar_idx) - 1)
                        elif len(mana_imgs) == 2:
                            self.mana_bar_idx = max(0, int(self.mana_bar_idx) - 1)
                        else:
                            self.mana_bar_idx = 0
                    except Exception:
                        self.mana_bar_idx = max(0, getattr(self, 'mana_bar_idx', 0) - 1)
                # sync float mana to the discrete index for any other logic
                try:
                    forward_idx = (steps - 1) - int(getattr(self, 'mana_bar_idx', 0))
                    prop = float(forward_idx) / float(max(1, steps - 1))
                    self.mana = prop * float(getattr(self, 'max_mana', 100))
                except Exception:
                    pass
        except Exception:
            pass

        # Mana no longer auto-triggers attacks. Attack selection is separate from mana HUD.
        try:
            if getattr(self, 'speech_intro_timer', 0.0) > 0.0:
                self.speech_intro_timer = max(0.0, self.speech_intro_timer - dt)
        except Exception:
            pass
        try:
            if getattr(self, 'speech_death_timer', 0.0) > 0.0:
                self.speech_death_timer = max(0.0, self.speech_death_timer - dt)
        except Exception:
            pass

    def next_hp_bar(self, damage=1):
        """Wizard-specific HP loss: clamp incoming damage to 1 bar and respect shields/invincibility.

        This overrides Monster.next_hp_bar so the wizard loses health more slowly.
        """
        # Wizard no longer has a shield; respect invincibility only
        try:
            # Always treat damage as at most 1 for the wizard
            super().next_hp_bar(damage=1)
        except Exception:
            try:
                super().next_hp_bar(damage)
            except Exception:
                pass

