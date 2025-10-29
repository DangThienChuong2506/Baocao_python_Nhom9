from core.map import WelcomeBanner, BackgroundScroller
import pygame, sys, random, os, math
from core.player import Player, load_image
from core.items import Item
from core.ui_game import draw_inventory, draw_monster_hp, draw_player_hp
from core.monster import Monster
# optional debug hack module - not required
try:
    from core import hack as _hack_module
except Exception:
    _hack_module = None
try:
    from core import map2 as _map2
except Exception:
    _map2 = None
try:
    from core import map3 as _map3
except Exception:
    _map3 = None
try:
    from core import login as login_mod
except Exception:
    login_mod = None
from core.boss import Demon, build_demon_animations, load_pixel_font, demon_intro_lines, demon_death_lines, Wizard, build_wizard_animations, Bringer
from core import sound as sound_mod
import settings

# Toggle to enable verbose debug logging.
DEBUG_LOGS = False



def main():
    map_transitioning = False
    allow_player_move = True
    # ...existing code...
    # Hiệu ứng chữ pixel chạy ngang khi vào game
    welcome_banner = WelcomeBanner([
        "Chào mừng bạn đến với thế giới Hero Fantasy",
        "Hãy cùng chiến đấu và hoàn thành thử thách nhé!",
        "Bạn hãy dùng Q, E, R, F để sử dụng skill của nhân vật",
        "Phím H để hồi máu"
    ], font_size=18, color=(255,255,255), speed=60)
    # Biến đếm số monster đã giết ở từng đợt
    monster_kill_count = 0
    monster_wave = 1  # 1: wave đầu (2 con), 2: wave 2 (3 con), 3: wave 3 (5 con), 4: wave demon (3 con)
    monsters_to_spawn = []  # Danh sách các monster sẽ spawn tiếp theo (dùng cho wave 2, 3)
    first_wave_cleared = False  # Đánh dấu đã giết xong 2 monster đầu
    wave_four_target = 0
    demon_animations = build_demon_animations()
    wave_lock_active = False  # Khóa cuộn map khi đang giao tranh các wave sau
    # ...existing code...
    # Hiệu ứng chữ pixel chạy ngang khi vào game
    welcome_banner = WelcomeBanner([
        "Chào mừng bạn đến với thế giới Hero Fantasy",
        "Hãy cùng chiến đấu và hoàn thành thử thách nhé!",
        "Bạn hãy dùng Q, E, R, F để sử dụng skill của nhân vật",
        "Phím H để hồi máu"
    ], font_size=18, color=(255,255,255), speed=60)
    # Biến đếm số monster đã giết ở từng đợt
    monster_kill_count = 0
    monster_wave = 1  # 1: wave đầu (2 con), 2: wave 2 (3 con), 3: wave 3 (5 con), 4: wave demon (3 con)
    monsters_to_spawn = []  # Danh sách các monster sẽ spawn tiếp theo (dùng cho wave 2, 3)
    first_wave_cleared = False  # Đánh dấu đã giết xong 2 monster đầu
    # ...existing code...
    # ...existing code...
    # ...existing code...
    # Load nút setting SAU khi đã init display
    setting_img = None
    setting_rect = None
    pygame.init()
    # initialize sound manager after pygame.init()
    try:
        sound_mod.init()
    except Exception:
        pass
    screen = pygame.display.set_mode((settings.WIDTH, settings.HEIGHT))
    pygame.display.set_caption("Fantasy Game Demo")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 22)
    demon_font = load_pixel_font(14)

    # Khởi tạo các nút action Q, E, R, F SAU khi đã khởi tạo pygame display
    action_button_names = ['ButtonQ.png', 'buttonE.png', 'buttonR.png', 'buttonF.png']  # Đúng tên file: ButtonQ.png, buttonE.png, buttonR.png, buttonF.png
    action_button_size = (60, 60)
    action_button_imgs = [load_image(f'assets/imagesbutton/{name}', size=action_button_size) for name in action_button_names]
    action_button_rects = [img.get_rect() for img in action_button_imgs]

    # Sắp xếp các nút Q, E, R, F ở góc dưới bên trái khung hình, cách đều nhau
    action_btn_spacing = 8
    action_y = settings.HEIGHT - action_button_size[1] - 8
    start_action_x = 8
    for i, rect in enumerate(action_button_rects):
        rect.x = start_action_x + i * (action_button_size[0] + action_btn_spacing)
        rect.y = action_y
    # Skill info popup state (press-and-hold to show)
    skill_info_shown = False
    skill_info_pressed = False
    skill_info_text = ""
    skill_info_button_index = None
    # Load nút setting SAU khi đã init display
    setting_img = None
    setting_rect = None
    pygame.init()
    screen = pygame.display.set_mode((settings.WIDTH, settings.HEIGHT))
    pygame.display.set_caption("Fantasy Game Demo")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 22)

    # If login module is present, prompt player to log in now (uses existing screen & font)
    username = None
    if login_mod is not None:
        try:
            username = login_mod.login_screen(screen, font)
        except Exception:
            try:
                # fallback: attempt a simple call without passing screen/font
                username = login_mod.login_screen(screen, font)
            except Exception:
                username = None
    else:
        username = None

    # Session score for this playthrough (1 per normal monster, 2 per boss)
    player_score = 0
    # Flag to ensure we persist the session score only once at game end
    score_persisted = False
    # Final rank (None or int) to display on end overlay after persisting
    final_rank = None

    GROUND_Y = 280

    # Sử dụng BackgroundScroller để cuộn nền lặp
    bg_scroller = BackgroundScroller('assets/maps/background.png', settings.WIDTH, speed=4)
    # flag to indicate background2 has been applied
    _bg2_applied = False
    # flag to indicate background3 has been applied
    _bg3_applied = False
    # guards to ensure bosses spawn only once across the session
    _wizard_spawned = False
    _demon_spawned = False
    _bringer_spawned = False
    # Count how many times background2 has been visited/applied
    bg2_visit_count = 0
    # Track which bg2 internal wave we're on (0 = not started, 1 = first wave spawned, 2 = second wave spawned, 3 = third wave spawned)
    bg2_wave_stage = 0
    # Khóa cuộn map khi đang giao tranh ở background2 (tương tự wave_lock_active)
    bg2_wave_lock = False
    # đánh dấu wizard đã bị hạ gục
    wizard_defeated = False
    # đánh dấu wave đầu map3 đã spawn skeleton
    bg3_wave_spawned = False
    # wave progression tracker for map3 skeletons (0=not started, 1=wave1 active, etc.)
    bg3_wave_stage = 0
    # Lưu offset nền trước đó để tính delta mỗi frame
    prev_bg_offset = bg_scroller.offset

    jump_height = int((320 ** 2) / (2 * 600))
    min_y = max(0, GROUND_Y - jump_height)

    player = Player((0, settings.HEIGHT // 2), "player", GROUND_Y, min_y)
    player_group = pygame.sprite.GroupSingle(player)

    # Thêm 2 quái vật (monster)
    min_x = settings.WIDTH // 2
    max_x = settings.WIDTH - 10
    monster_group = pygame.sprite.Group()
    # Wave 1: spawn 2 monster
    monster_positions = [min_x + 60, min_x + 130]
    import time
    class DelayedMonster(Monster):
        def __init__(self, *args, delay=0, from_left=True, **kwargs):
            super().__init__(*args, **kwargs)
            # Ensure target_x is retrieved from the initial pos argument so monsters will move toward the intended x
            # args[0] is the pos tuple passed when creating the DelayedMonster
            try:
                self.target_x = args[0][0]
            except Exception:
                # fallback to previously set target_pos if available
                if hasattr(self, 'target_pos'):
                    self.target_x = self.target_pos[0]
                else:
                    self.target_x = None
            self.spawn_time = time.time()
            self.delay = delay
            self._activated = False  # becomes True after delay passes
            self._entering = True   # slide into the arena before normal AI kicks in
            self.from_left = from_left
            # Đặt vị trí ngoài rìa màn hình (bắt đầu ngoài màn hình theo from_left)
            # Use centerx for smooth sliding and consistent comparisons
            try:
                if from_left:
                    self.rect.centerx = -self.rect.width // 2
                else:
                    self.rect.centerx = settings.WIDTH + self.rect.width // 2
            except Exception:
                # fallback to left coordinate if centerx assignment fails
                if from_left:
                    self.rect.x = -self.rect.width
                else:
                    self.rect.x = settings.WIDTH + self.rect.width
            # slower entry speed so monsters slide in gradually
            self.entry_speed = 2
            # Luôn set target_pos đúng vị trí đích (x, ground_y), treat target_x as centerx
            if self.target_x is not None:
                self.target_pos = (self.target_x, GROUND_Y)
            else:
                self.target_pos = (self.rect.centerx, GROUND_Y)
            # ensure vertical alignment uses bottom so ground-aligned monsters line up with GROUND_Y
            try:
                # Use ground_offset from the Monster so visuals match (rect.bottom = ground_y - ground_offset)
                target_bottom = int(self.target_pos[1] - getattr(self, 'ground_offset', 0))
                try:
                    self.rect.bottom = target_bottom
                except Exception:
                    # fallback to centery if bottom assignment fails
                    self.rect.centery = self.target_pos[1]
            except Exception:
                pass
        def update(self, dt, player):
            # Sau khi hết delay mới bắt đầu di chuyển
            if not self._activated and (time.time() - self.spawn_time) >= self.delay:
                self._activated = True

            # Nếu đang giai đoạn chạy vào sân khấu, di chuyển dần đến target_x
            if self._activated and self._entering and self.target_x is not None:
                # Ensure facing direction: from left => face right, from right => face left
                try:
                    self.facing_right = True if self.from_left else False
                except Exception:
                    pass
                # Ensure we use run animation during entry
                try:
                    if getattr(self, 'run_frames', None):
                        if self.action != 'run':
                            self.set_action('run')
                except Exception:
                    pass
                # Animate run frames while entering
                try:
                    self.anim_timer += dt
                    if self.anim_timer >= self.anim_speed:
                        self.anim_timer = 0.0
                        # guard against zero-length frames
                        if self.frames:
                            self.frame_idx = (self.frame_idx + 1) % len(self.frames)
                    self.image = self._orient_frame(self.frames[self.frame_idx])
                except Exception:
                    pass
                # Move using centerx so comparisons match Monster.update expectations
                if self.from_left:
                    self.rect.centerx = min(self.rect.centerx + self.entry_speed, self.target_x)
                else:
                    self.rect.centerx = max(self.rect.centerx - self.entry_speed, self.target_x)
                # When we've reached the target center, stop entering
                if self.rect.centerx == self.target_x:
                    self._entering = False

            # Khi chưa kích hoạt hoặc vẫn đang chạy vào, tạm dừng AI bình thường
            if (not self._activated) or self._entering:
                return

            # Khi đã vào vị trí, cho monster hoạt động như thường lệ
            super().update(dt, player)
    for i, x in enumerate(monster_positions):
        item_img = load_image('assets/imagesitems/item.png', size=(40, 40))
        monster = Monster((x, GROUND_Y), GROUND_Y, size=(80, 80), min_x=min_x, max_x=max_x, item_img=item_img)
        # mark monsters placed at game start as spawned on map 0
        try:
            monster.spawn_map = 0
        except Exception:
            pass
        monster_group.add(monster)
    # Muốn thêm nhiều monster hơn:
    # 1. Thêm vị trí x mới vào monster_positions
    # 2. (Nếu muốn mỗi monster có item khác nhau) đổi item_img cho từng monster

    def random_item_pos():
        x = random.randint(40, settings.WIDTH - 40)
        y = random.randint(min_y + 20, GROUND_Y - 20)
        return (x, y)

    # KHÔNG tạo items ngẫu nhiên khi khởi tạo game nữa
    items = pygame.sprite.Group()

    inventory = 0
    running = True
    paused = False
    # Trạng thái mở menu setting
    setting_open = False
    # Trạng thái màn hình defeat: khi player chết hiện ảnh defeat trước, chờ click để mở menu
    defeat_shown = False
    # If end overlay shown is a victory (True) or defeat (False)
    end_is_victory = False
    # Trạng thái victory: hiện khi bringer bị tiêu diệt
    bringer_defeated = False
    victory_shown = False
    victory_timer = 0.0
    # Danh sách các nút setting khác (trừ setting)
    setting_buttons = []
    setting_button_imgs = []
    setting_button_rects = []
    # Lấy danh sách file trong assets/imagessetting, trừ setting.png
    setting_dir = 'assets/imagessetting'
    for fname in os.listdir(setting_dir):
        if fname.endswith('.png') and fname != 'setting.png':
            setting_buttons.append(fname)
            img = load_image(os.path.join(setting_dir, fname), size=(40, 40))
            setting_button_imgs.append(img)
            setting_button_rects.append(img.get_rect())
    
    # Load setting_img sau khi đã init display
    # Load và scale setting.png về kích thước nhỏ hơn (28x28)
    setting_img = load_image('assets/imagessetting/setting.png', size=(28, 28))
    setting_rect = setting_img.get_rect()
    setting_rect.topright = (settings.WIDTH - 10, 10)
    # Load defeat image (shown when player dies). Will wait for a click to open the menu.
    try:
        # Load original defeat image, then scale it to a fraction of the screen while preserving aspect
        _orig_defeat = load_image('assets/imagesbutton/defeat.png')
        if _orig_defeat:
            sw, sh = settings.WIDTH, settings.HEIGHT
            max_w = int(sw * 0.5)   # at most 50% of screen width
            max_h = int(sh * 0.35)  # at most 35% of screen height
            ow, oh = _orig_defeat.get_size()
            scale = min(max_w / ow, max_h / oh, 1.0)
            new_w = max(1, int(ow * scale))
            new_h = max(1, int(oh * scale))
            defeat_img = pygame.transform.smoothscale(_orig_defeat, (new_w, new_h))
            defeat_rect = defeat_img.get_rect(center=(sw//2, sh//2))
        else:
            defeat_img = None
            defeat_rect = None
    except Exception:
        defeat_img = None
        defeat_rect = None
    # Prepare victory image (hidden until bringer dies)
    try:
        _orig_victory = load_image('assets/imagesbutton/victory.png')
        if _orig_victory:
            sw, sh = settings.WIDTH, settings.HEIGHT
            max_w = int(sw * 0.6)   # at most 60% of screen width
            max_h = int(sh * 0.5)   # at most 50% of screen height
            ow, oh = _orig_victory.get_size()
            scale = min(max_w / ow, max_h / oh, 1.0)
            new_w = max(1, int(ow * scale))
            new_h = max(1, int(oh * scale))
            victory_img = pygame.transform.smoothscale(_orig_victory, (new_w, new_h))
            victory_rect = victory_img.get_rect(center=(sw//2, sh//2 - 40))
        else:
            victory_img = None
            victory_rect = None
    except Exception:
        victory_img = None
        victory_rect = None
    # Load các button ở góc phải dưới
    button_names = ['buttonAhead.png', 'buttonleft.png', 'buttonright.png']
    button_sizes = [(40, 40), (40, 40), (40, 40)]
    button_imgs = [load_image(f'assets/imagesbutton/{name}', size=size) for name, size in zip(button_names, button_sizes)]
    button_rects = [img.get_rect() for img in button_imgs]

    # Sắp xếp: buttonAhead.png nằm trên, hai nút còn lại nằm dưới, cả 3 nút ở góc phải phía dưới màn hình
    margin = 8  # Giảm margin để nút nằm sát mép dưới hơn
    btn_spacing = 8
    # Button left và right nằm dưới cùng, button ahead nằm phía trên giữa hai nút
    left_rect = button_rects[1]
    right_rect = button_rects[2]
    ahead_rect = button_rects[0]

    # Tính vị trí cho hai nút dưới cùng
    right_rect.x = settings.WIDTH - button_sizes[2][0] - margin
    # Đẩy nút xuống sát mép dưới hơn
    right_rect.y = settings.HEIGHT - button_sizes[2][1] - margin
    left_rect.x = right_rect.x - button_sizes[1][0] - btn_spacing
    left_rect.y = settings.HEIGHT - button_sizes[1][1] - margin

    # ...vòng lặp while running...
    # Thay thế đoạn này bằng đoạn đã có trong while running:
    # for monster in monster_group:
    #     if hasattr(monster, 'update'):
    #         monster.update(dt, player)
    ahead_rect.x = left_rect.x + (right_rect.x + button_sizes[2][0] - left_rect.x - button_sizes[0][0]) // 2
    ahead_rect.y = left_rect.y - button_sizes[0][1] - btn_spacing + 8  # Đẩy nút phía trên xuống thêm

    def reset_game_state():
        nonlocal wave_lock_active, first_wave_cleared, monster_wave, monster_kill_count, wave_four_target, _wizard_spawned, _demon_spawned, _bringer_spawned, bg2_wave_lock, bg2_wave_stage, _bg2_applied, _bg3_applied, wizard_defeated, bg3_wave_spawned, bg3_wave_stage
        player_new = Player((0, settings.HEIGHT // 2), "player", GROUND_Y, min_y)
        # ensure the newly created player is placed at the left edge
        try:
            player_new.rect.left = 0
        except Exception:
            pass
        player_group_new = pygame.sprite.GroupSingle(player_new)
        monster_group_new = pygame.sprite.Group()
        for i, x in enumerate(monster_positions):
            item_img = load_image('assets/imagesitems/item.png', size=(40, 40))
            monster = Monster((x, GROUND_Y), GROUND_Y, size=(80, 80), min_x=min_x, max_x=max_x, item_img=item_img)
            # mark this monster as spawned on map 0
            try:
                monster.spawn_map = 0
            except Exception:
                pass
            monster_group_new.add(monster)
        items_new = pygame.sprite.Group()
        inventory_new = 0
        setting_open_new = False
        monster_wave = 1
        monster_kill_count = 0
        first_wave_cleared = False
        wave_lock_active = False
        wave_four_target = 0
        bg2_wave_lock = False
        bg2_wave_stage = 0
        _bg2_applied = False
        _bg3_applied = False
        wizard_defeated = False
        bg3_wave_spawned = False
        bg3_wave_stage = 0
        try:
            _wizard_spawned = False
        except Exception:
            pass
        try:
            _demon_spawned = False
        except Exception:
            pass
        try:
            _bringer_spawned = False
        except Exception:
            pass
        return player_new, player_group_new, monster_group_new, items_new, inventory_new, setting_open_new

    # Helper: spawn monsters at given positions.
    # use_delayed=True => spawn DelayedMonster that waits then slides in; otherwise use base Monster (like wave1 animation).
    def spawn_monsters(positions, count=None, delay_base=1.5, from_left=False, use_delayed=False, monster_cls=Monster, monster_kwargs=None):
        nonlocal monster_group, min_x, max_x, current_map
        spawned = []
        if count is None:
            count = len(positions)
        params_template = dict(monster_kwargs) if monster_kwargs else {}
        for i, x in enumerate(positions[:count]):
            params = dict(params_template)
            if 'item_img' not in params:
                params['item_img'] = load_image('assets/imagesitems/item.png', size=(40, 40))
            params.setdefault('size', (80, 80))
            params.setdefault('min_x', min_x)
            params.setdefault('max_x', max_x)
            spawn_map_value = params.pop('spawn_map', current_map)
            if use_delayed:
                delay = random.uniform(0, delay_base) + i * 0.5
                monster = DelayedMonster((x, GROUND_Y), GROUND_Y, delay=delay, from_left=from_left, **params)
                monster.target_x = x
                # ensure starting x is off-screen on the chosen side
                if from_left:
                    monster.rect.x = -monster.rect.width
                else:
                    monster.rect.x = settings.WIDTH + monster.rect.width
                # ...existing code...
            else:
                monster = monster_cls((x, GROUND_Y), GROUND_Y, **params)
                # Nếu spawn từ trái thì đặt lại rect.x sang ngoài trái và đặt facing phù hợp
                if from_left:
                    monster.rect.x = -monster.rect.width - random.randint(10, 60)
                    monster.facing_right = True
                else:
                    # Monster() mặc định spawn bên phải, nên không cần chỉnh
                    pass
            try:
                # ensure spawn_map attribute exists on the monster instance
                monster.spawn_map = spawn_map_value
            except Exception:
                pass
            # ...existing code...
            monster_group.add(monster)
            spawned.append(monster)
        return spawned

    # Wrapper specifically for goblin waves so goblins and other monster types (crows) remain separated
    def spawn_goblins(positions, count=None, delay_base=1.5, from_left=False, use_delayed=False, goblin_kwargs=None):
        # by default goblins use the base Monster class and standard sizes
        params = dict(goblin_kwargs) if goblin_kwargs else {}
        params.setdefault('size', (80, 80))
        params.setdefault('min_x', min_x)
        params.setdefault('max_x', max_x)
        # Reuse spawn_monsters but force monster_cls to Monster to keep goblin-specific behavior
        return spawn_monsters(positions, count=count, delay_base=delay_base, from_left=from_left, use_delayed=use_delayed, monster_cls=Monster, monster_kwargs=params)

    # Helper to spawn crow waves for background2 so wave1/2/3 behave identically
    def spawn_bg2_crows(positions, delay_step=0.25):
        # Build animation lists for monstercrow if available
        crow_base = os.path.join('assets', 'imagesmonster', 'monster', 'monstercrow')
        def _list_sorted(sub):
            p = os.path.join(crow_base, sub)
            if os.path.isdir(p):
                files = [os.path.join(p, f).replace('\\', '/') for f in sorted(os.listdir(p)) if f.lower().endswith('.png')]
                return files
            return []

        crow_idle = _list_sorted('crow_idle')
        crow_run = _list_sorted('crow_walk') or _list_sorted('crow_run')
        crow_attack = _list_sorted('crow_attack')
        crow_death = _list_sorted('crow_death1') + _list_sorted('crow_death2')
        crow_takehit = _list_sorted('crow_damage')

        crow_anims = {}
        if crow_idle:
            crow_anims['idle'] = crow_idle
        if crow_run:
            crow_anims['run'] = crow_run
        if crow_attack:
            crow_anims['attack'] = crow_attack
        if crow_death:
            crow_anims['death'] = crow_death
        if crow_takehit:
            crow_anims['takehit'] = crow_takehit

        if not any(crow_anims.values()):
            if settings.DEBUG and DEBUG_LOGS:
                print("[DEBUG] No crow animations found under assets/imagesmonster/monster/monstercrow - skipping crow spawn", flush=True)
            return

        for i, x in enumerate(positions):
            try:
                item_img = load_image('assets/imagesitems/item.png', size=(40, 40))
            except Exception:
                item_img = None
            # Use fixed ground Y for bg2 crows (do not align vertically to the player's current position)
            # Raise crows slightly so they fly a bit above the ground
            ground_y_for_crow = GROUND_Y - 7
            delay = delay_step * i
            try:
                m = DelayedMonster((x, ground_y_for_crow), ground_y_for_crow, delay=delay, from_left=False, size=(64, 64), min_x=min_x, max_x=max_x, item_img=item_img, animations=crow_anims)
                m.target_x = x
                try:
                    m.spawn_map = 2
                except Exception:
                    pass
                try:
                    if getattr(m, 'run_frames', None):
                        m.set_action('run')
                except Exception:
                    pass
                try:
                    # anchor crow to the background ground Y rather than player's vertical position
                    m.rect.bottom = ground_y_for_crow
                except Exception:
                    pass
                try:
                    m.facing_right = False
                except Exception:
                    pass
                # Do not force a locked arrival; allow DelayedMonster/MONSTER slide-in behavior to handle entry
                monster_group.add(m)
                try:
                    if settings.DEBUG and DEBUG_LOGS:
                        print(f"[DEBUG spawn_monsters] DelayedCrow spawn: player_cx={getattr(player,'rect',None) and player.rect.centerx}, target_x={x}, _locked_centerx={getattr(m,'_locked_centerx',None)} delay={delay} idle={len(getattr(m,'idle_frames',[]))} run={len(getattr(m,'run_frames',[]))}", flush=True)
                except Exception:
                    if settings.DEBUG and DEBUG_LOGS:
                        print(f"[DEBUG spawn_monsters] added DelayedCrow target_x={x} delay={delay}", flush=True)
            except Exception as _e:
                try:
                    monster = Monster((x, ground_y_for_crow), ground_y_for_crow, size=(64, 64), min_x=min_x, max_x=max_x, item_img=item_img, animations=crow_anims)
                    try:
                        monster.spawn_map = 2
                    except Exception:
                        pass
                    try:
                        if getattr(monster, 'run_frames', None):
                            monster.set_action('run')
                    except Exception:
                        pass
                    try:
                        monster.rect.bottom = ground_y_for_crow
                    except Exception:
                        pass
                    # Allow fallback monster to slide in normally (no forced locking)
                    monster_group.add(monster)
                    try:
                        if settings.DEBUG and DEBUG_LOGS:
                            print(f"[DEBUG spawn_monsters] fallback Crow spawn: player_cx={getattr(player,'rect',None) and player.rect.centerx}, x={x}, _locked_centerx={getattr(monster,'_locked_centerx',None)}", flush=True)
                    except Exception:
                        if settings.DEBUG and DEBUG_LOGS:
                            print(f"[DEBUG spawn_monsters] fallback added Crow at x={x} target_y={ground_y_for_crow}", flush=True)
                except Exception:
                    if settings.DEBUG and DEBUG_LOGS:
                        print(f"[DEBUG spawn_monsters] failed to add crow at x={x}: {_e}", flush=True)

    _skeleton_cache = {'anims': None}

    def _load_skeleton_animations():
        if _skeleton_cache['anims'] is not None:
            return _skeleton_cache['anims']
        base = os.path.join('assets', 'imagesmonster', 'monster', 'skeleton')
        if not os.path.isdir(base):
            _skeleton_cache['anims'] = {}
            return _skeleton_cache['anims']

        def _sorted_paths(subdir):
            folder = os.path.join(base, subdir)
            if not os.path.isdir(folder):
                return []
            files = [f for f in os.listdir(folder) if f.lower().endswith('.png')]
            files.sort()
            return [os.path.join(folder, f).replace('\\', '/') for f in files]

        anims = {
            'idle': _sorted_paths('skeletonIdle'),
            'run': _sorted_paths('skeletonWalk'),
            'attack': _sorted_paths('skeletonATK'),
            'death': _sorted_paths('skeletonDeath'),
            'takehit': _sorted_paths('skeletonTakehit'),
            'shield': _sorted_paths('skeletonShield'),
        }
        _skeleton_cache['anims'] = anims
        return anims

    def spawn_bg3_skeletons(count=3, wave_index=1):
        nonlocal bg3_wave_spawned, bg3_wave_stage
        anims = _load_skeleton_animations()
        if not anims or not any(anims.values()):
            return False

        try:
            count = max(1, int(count))
        except Exception:
            count = 3
        # Spread skeletons evenly across the right half of the arena so larger waves still fit onscreen.
        start_x = min_x + 40
        end_x = max_x - 40
        if count > 1 and end_x > start_x:
            step = (end_x - start_x) / (count - 1)
        else:
            step = 0
        positions = [int(start_x + step * i) for i in range(count)]

        params = {
            'animations': anims,
            'size': (90, 90),
            'asset_faces_right': True,
            'spawn_map': 3,
        }
        spawned = spawn_monsters(positions, count=count, from_left=False, use_delayed=False, monster_kwargs=params)
        if not spawned:
            return False
        for monster in spawned:
            try:
                total_states = len(getattr(monster, 'hp_bar_imgs', []))
                threshold = max(1, total_states // 2)
                monster.trigger_shield_threshold = threshold
                # Khi skeleton bật shield, miễn nhiễm trong 3 giây (one-time shield)
                monster.shield_once_duration = 3.0
                # Do we only want a one-time shield triggered by HP threshold for skeletons,
                # do NOT enable periodic shielding (leave shield_interval falsy).
                monster.shield_interval = None
                monster.shield_once_action = 'shield' if getattr(monster, 'shield_frames', None) else 'idle'
                monster._shield_triggered = False
                monster.shield_active = False
                monster.shield_active_timer = 0.0
                monster._shield_restore_action = 'idle'
            except Exception:
                continue
        bg3_wave_spawned = True
        if wave_index > bg3_wave_stage:
            bg3_wave_stage = wave_index
        return True

    def spawn_bringer_boss():
        nonlocal monster_group, _bringer_spawned, bg3_wave_stage, allow_player_move
        if _bringer_spawned:
            return False
        try:
            item_img = load_image('assets/imagesitems/item.png', size=(42, 42))
        except Exception:
            item_img = None
        target_x = max(min_x + 160, min(max_x - 160, int((min_x + max_x) / 2)))
        boss = Bringer((target_x, GROUND_Y), GROUND_Y, size=(150, 150), min_x=min_x, max_x=max_x, item_img=item_img)
        try:
            boss.spawn_map = 3
        except Exception:
            pass
        try:
            boss.rect.left = settings.WIDTH + 80
        except Exception:
            pass
        try:
            boss.target_pos = (target_x, GROUND_Y)
        except Exception:
            pass
        monster_group.add(boss)
        _bringer_spawned = True
        bg3_wave_stage = 4
        allow_player_move = False
        return True

    # Load nút itemshp.png để vẽ ở góc trên trái, bên phải thanh máu player
    # Thêm 4 nút itemshp.png kế bên nút gốc, tổng cộng 5 nút giống nhau
    itemshp_imgs = [load_image('assets/imagesbutton/itemshp.png', size=(30, 30)) for _ in range(5)]
    itemshp5_img = load_image('assets/imagesbutton/itemshp5.png', size=(30, 30))
    # Trạng thái từng nút: True = itemshp.png, False = itemshp5.png
    itemshp_states = [True for _ in range(5)]
    hp_x, hp_y, hp_w, hp_h = 20, 10, 150, 30
    itemshp_margin = 16  # khoảng cách với thanh máu
    itemshp_rects = []
    for idx, img in enumerate(itemshp_imgs):
        rect = img.get_rect()
        rect.x = hp_x + hp_w + itemshp_margin + idx * (rect.width + 6)  # 6px spacing giữa các nút
        rect.y = hp_y + (hp_h - rect.height) // 2
        itemshp_rects.append(rect)

    # Biến xác định map hiện tại (0: map đầu, 1: map giữa, 2: map cuối)
    current_map = 0
    while running:
        dt = clock.tick(settings.FPS) / 1000.0
        # Tính delta offset của background để phục vụ logic cuộn nền
        delta_offset = bg_scroller.offset - prev_bg_offset
        prev_bg_offset = bg_scroller.offset
        # Xác định map hiện tại dựa vào offset của bg_scroller
        # offset = 0: map đầu, offset = -WIDTH: map giữa, offset = -2*WIDTH: map cuối
        if _bg3_applied:
            current_map = 3
        elif _bg2_applied:
            current_map = 2
        else:
            if bg_scroller.offset <= -settings.WIDTH*1.5:
                current_map = 2
            elif bg_scroller.offset <= -settings.WIDTH*0.5:
                current_map = 1
            else:
                current_map = 0
        # Inform sound manager about current map so it can play appropriate music
        try:
            sound_mod.set_map(current_map)
        except Exception:
            pass
        if current_map >= 2 and not map_transitioning:
            allow_player_move = True
        # Cập nhật banner nếu còn hiệu ứng
        if welcome_banner and not welcome_banner.done:
            welcome_banner.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                # Debug: press C to kill all monsters (optional hack module)
                if event.key == pygame.K_c:
                    if _hack_module is not None:
                        try:
                           # Placeholder for future code
                            pass
                            pass
                            pass
                            _hack_module.handle_event(event, monster_group, player)
                        except Exception:
                            pass
                            pass
                            pass
                            pass
                if event.key == pygame.K_h:
                    # Nếu player cần hồi (hp_bar_idx > 0) và còn ít nhất 1 itemshp, bắt đầu hồi máu liên tục trong 2 giây
                    if hasattr(player, 'hp_bar_idx') and player.hp_bar_idx > 0 and any(itemshp_states):
                        # bắt đầu hồi theo thời gian (2 giây)
                        if hasattr(player, 'start_heal'):
                            player.start_heal(duration=2.0)
                        # tiêu thụ 1 item từ phải sang trái
                        for i in range(4, -1, -1):
                            if itemshp_states[i]:
                                itemshp_states[i] = False
                                break
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                # If an end overlay (defeat or victory) is currently shown, consume this click to open the menu
                if defeat_shown or bringer_defeated:
                    # Compute positions for the end overlay buttons (Restart, Leaderboard)
                    try:
                        try:
                            big_font = load_pixel_font(28)
                        except Exception:
                            big_font = pygame.font.SysFont(None, 28)
                        final_text = f"Your Score: {player_score}"
                        final_surf = big_font.render(final_text, True, (255, 215, 0))
                        # choose the correct end_rect depending on victory or defeat
                        end_rect_for_click = victory_rect if bringer_defeated and victory_rect else defeat_rect
                        # Position below the end image (or center if end_rect missing)
                        if end_rect_for_click:
                            fx = end_rect_for_click.centerx - final_surf.get_width() // 2
                            fy = end_rect_for_click.bottom + 10
                        else:
                            fx = settings.WIDTH // 2 - final_surf.get_width() // 2
                            fy = settings.HEIGHT // 2 + 60
                        # Buttons layout
                        btn_w, btn_h = 140, 40
                        spacing = 12
                        total_w = btn_w * 2 + spacing
                        bx = fx + final_surf.get_width() // 2 - total_w // 2
                        by = fy + final_surf.get_height() + 14
                        restart_rect = pygame.Rect(bx, by, btn_w, btn_h)
                        leaderboard_rect = pygame.Rect(bx + btn_w + spacing, by, btn_w, btn_h)
                    except Exception:
                        # fallback: open settings if anything goes wrong
                        defeat_shown = False
                        bringer_defeated = False
                        victory_shown = False
                        victory_timer = 0.0
                        setting_open = True
                        continue

                    # If clicked on Restart -> reset game state for a new run
                    if restart_rect.collidepoint(mouse_pos):
                        try:
                            player, player_group, monster_group, items, inventory, setting_open = reset_game_state()
                        except Exception:
                            try:
                                # best-effort fallback: recreate player only
                                player = Player((0, settings.HEIGHT // 2), "player", GROUND_Y, min_y)
                                player_group = pygame.sprite.GroupSingle(player)
                            except Exception:
                                pass
                        # Reset session score for the new run and persisted flag
                        try:
                            player_score = 0
                        except Exception:
                            pass
                        try:
                            score_persisted = False
                        except Exception:
                            pass
                        try:
                            final_rank = None
                        except Exception:
                            pass
                        defeat_shown = False
                        bringer_defeated = False
                        end_is_victory = False
                        victory_shown = False
                        victory_timer = 0.0
                        setting_open = False
                        # restart background/music to map1 (assets/maps/background.png)
                        try:
                            # Prefer resource loader so bundled EXE can find assets
                            try:
                                from core import resources as resources
                                bg_img = resources.load_image('assets/maps/background.png', size=(settings.WIDTH, settings.HEIGHT))
                            except Exception:
                                p = os.path.join('assets', 'maps', 'background.png')
                                bg_img = pygame.image.load(p).convert()
                                try:
                                    bg_img = pygame.transform.smoothscale(bg_img, (settings.WIDTH, settings.HEIGHT))
                                except Exception:
                                    bg_img = pygame.transform.scale(bg_img, (settings.WIDTH, settings.HEIGHT))
                            bg_scroller.bg_img = bg_img
                            bg_scroller.screen_width = settings.WIDTH
                            # map1 uses 3 tiles for horizontal scrolling
                            bg_scroller.num_tiles = 3
                            # Set offset so we're on map1 (one screen left)
                            try:
                                bg_scroller.offset = -settings.WIDTH
                            except Exception:
                                bg_scroller.offset = -settings.WIDTH if hasattr(settings, 'WIDTH') else -800
                            _bg2_applied = False
                            _bg3_applied = False
                            # place player at left edge
                            try:
                                player.rect.left = 0
                            except Exception:
                                pass
                            try:
                                sound_mod.restart_map(1)
                            except Exception:
                                try:
                                    sound_mod.restart_map(0)
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        continue

                    # If clicked on Leaderboard -> open leaderboard screen (if available)
                    if leaderboard_rect.collidepoint(mouse_pos):
                        try:
                            if login_mod is not None:
                                # call leaderboard screen (will block until closed)
                                login_mod.leaderboard_screen(screen, font)
                        except Exception:
                            pass
                        # Keep overlay shown after returning
                        continue

                    # If click is inside the end-overlay area (end image, final score text or buttons), consume it
                    # but do not open settings. Only open settings if the click is outside the whole overlay.
                    try:
                        # Build a bounding rect that contains the end image (if any), the final text and the buttons
                        overlay_left = fx if 'fx' in locals() else 0
                        overlay_top = fy if 'fy' in locals() else 0
                        overlay_right = bx + btn_w * 2 + spacing if 'bx' in locals() else overlay_left
                        overlay_bottom = by + btn_h if 'by' in locals() else overlay_top
                        if end_rect_for_click:
                            overlay_left = min(overlay_left, end_rect_for_click.left)
                            overlay_top = min(overlay_top, end_rect_for_click.top)
                            overlay_right = max(overlay_right, end_rect_for_click.right)
                            overlay_bottom = max(overlay_bottom, end_rect_for_click.bottom)
                        overlay_rect = pygame.Rect(overlay_left, overlay_top, max(0, overlay_right - overlay_left), max(0, overlay_bottom - overlay_top))
                        if overlay_rect.collidepoint(mouse_pos):
                            # Click inside overlay but not on Restart/Rank buttons: consume and do nothing
                            continue
                    except Exception:
                        # If anything goes wrong building the overlay area, fall back to previous behavior and open settings
                        pass

                    # Otherwise, preserve legacy behavior: open settings/menu
                    defeat_shown = False
                    bringer_defeated = False
                    victory_shown = False
                    victory_timer = 0.0
                    setting_open = True
                    # skip other click handling for this frame
                    continue
                if setting_rect.collidepoint(mouse_pos):
                    setting_open = not setting_open
                # Nếu đang mở menu setting, kiểm tra click vào các nút trong menu
                if setting_open:
                    n = len(setting_button_imgs)
                    btn_w, btn_h = 40, 40
                    spacing = 18
                    box_w = btn_w + 80
                    box_h = n*btn_h + (n-1)*spacing + 60
                    box_x = (settings.WIDTH - box_w) // 2
                    box_y = (settings.HEIGHT - box_h) // 2
                    for i, fname in enumerate(setting_buttons):
                        # Tạo rect tạm khung cho nút tương ứng giống cách vẽ
                        temp_rect = setting_button_rects[i].copy()
                        temp_rect.centerx = box_x + box_w // 2
                        temp_rect.y = box_y + 30 + i*(btn_h + spacing)
                        if temp_rect.collidepoint(mouse_pos):
                            # Xử lý từng nút theo tên file
                            if fname.lower() == 'pause.png':
                                paused = True
                            elif fname.lower() == 'play.png':
                                paused = False
                            elif fname.lower() == 'exit.png':
                                running = False
                            elif fname.lower() == 'start.png':
                                # Reset game state and also ensure we return to the initial background (map 0)
                                player, player_group, monster_group, items, inventory, setting_open = reset_game_state()
                                # Reset session score for the new run
                                try:
                                    player_score = 0
                                except Exception:
                                    pass
                                # Reset persisted flag so next run can be saved on game over
                                try:
                                    score_persisted = False
                                except Exception:
                                    pass
                                try:
                                    final_rank = None
                                except Exception:
                                    pass
                                try:
                                    # Move player to map1 instead of map0 when pressing Start.
                                    # Prepare background and spawn the map1 goblin wave.
                                    try:
                                        # Prefer the centralized resource loader so bundled EXEs can find assets
                                        try:
                                            from core import resources as resources
                                            bg_img = resources.load_image('assets/maps/background.png', size=(settings.WIDTH, settings.HEIGHT))
                                        except Exception:
                                            # fallback to direct load when resources helper not available
                                            p = os.path.join('assets', 'maps', 'background.png')
                                            bg_img = pygame.image.load(p).convert()
                                            try:
                                                bg_img = pygame.transform.smoothscale(bg_img, (settings.WIDTH, settings.HEIGHT))
                                            except Exception:
                                                bg_img = pygame.transform.scale(bg_img, (settings.WIDTH, settings.HEIGHT))
                                        bg_scroller.bg_img = bg_img
                                        bg_scroller.screen_width = settings.WIDTH
                                        # for map1, use 3 tiles so scrolling works as before
                                        bg_scroller.num_tiles = 3
                                    except Exception as _e:
                                        if settings.DEBUG and DEBUG_LOGS:
                                            print(f"[DEBUG start-button] failed to reload background: {_e}", flush=True)
                                    # set offset to map1 (one screen to the left)
                                    try:
                                        bg_scroller.offset = -settings.WIDTH
                                    except Exception:
                                        bg_scroller.offset = -settings.WIDTH if hasattr(settings, 'WIDTH') else  -800
                                    # clear background2/3 flags so map progression is reset
                                    _bg2_applied = False
                                    _bg3_applied = False
                                    bg3_wave_spawned = False
                                    # mark we're now on map 1
                                    current_map = 1
                                    prev_bg_offset = bg_scroller.offset
                                    allow_player_move = True
                                    # place player at the left edge of the screen
                                    try:
                                        player.rect.left = 0
                                    except Exception:
                                        pass
                                    # Spawn the map1 goblin wave (positions similar to earlier logic)
                                    try:
                                        monster_kill_count = 0
                                        positions = [min_x + 60, min_x + 130, min_x + 200]
                                        spawn_goblins(positions, from_left=False)
                                        monster_wave = 2
                                    except Exception:
                                        pass
                                    # Restart map music from the beginning for map 1
                                    try:
                                        sound_mod.restart_map(1)
                                    except Exception:
                                        try:
                                            sound_mod.restart_map(0)
                                        except Exception:
                                            pass
                                    if settings.DEBUG and DEBUG_LOGS:
                                        print("[DEBUG start-button] Reset to map1 with initial goblin wave", flush=True)
                                except Exception:
                                    pass
                                # Reset lại 5 cục máu về trạng thái ban đầu
                                try:
                                    itemshp_states = [True for _ in range(len(itemshp_states))]
                                except Exception:
                                    # Nếu itemshp_states chưa tồn tại, tạo mới
                                    itemshp_states = [True, True, True, True, True]
                                paused = False
                            # Đóng menu sau khi nhấn một nút
                            setting_open = False
                            break
                # Handle press (mouse down) on action buttons Q/E/R/F to show skill info while held
                try:
                    if not setting_open and not (defeat_shown or bringer_defeated):
                        # Only consider press when clicking on an action button
                        pressed_on_button = False
                        for ai, arect in enumerate(action_button_rects):
                            if arect.collidepoint(mouse_pos):
                                pressed_on_button = True
                                # Vietnamese skill descriptions provided by user
                                skill_texts = {
                                    0: "Q (Tốc Kiếm): kiếm sĩ tấn công ngay lập tức tạo sát thương tức thì cho mục tiêu (thời gian chờ skill 0.2 giây).",
                                    1: "E (Mũi Kiếm Sấm): đòn tấn công sát thương tương đối, (tiêu tốn 1 đơn vị mana, thời gian chờ skill 1.5 giây).",
                                    2: "R (Ngạo kiếm): kiếm sĩ chém từ trên xuống gây sát thương cực mạnh cho mục tiêu phía trước, dọn dẹp toàn bộ quái nhỏ đang đứng trước mặt và gây sát thương bằng 50%HP tối đa đối với boss, (thời gian chờ skill 4 giây và tiêu tốn 3 đơn vị mana).",
                                    3: "F (Vòng hộ mệnh): kiếm sĩ dùng khiên chặn sát thương, tạo vòng tròn hộ mệnh xung quanh bản thân, trong thời gian có vòng hộ mệnh Kiếm Sĩ miễn nhiễm toàn bộ hiệu ứng sát thương và hiệu ứng khống chế của mục tiêu, (Skill tiêu tốn 2 đơn vị mana, thời gian chờ skill 2 giây).",
                                }
                                # Show the popup while mouse is held down on this button
                                skill_info_pressed = True
                                skill_info_shown = True
                                skill_info_button_index = ai
                                skill_info_text = skill_texts.get(ai, "")
                                break
                        if not pressed_on_button:
                            # clicked elsewhere -> hide popup
                            skill_info_pressed = False
                            skill_info_shown = False
                            skill_info_button_index = None
                            skill_info_text = ""
                except Exception:
                    # do not allow any errors here to break input handling
                    skill_info_pressed = False
                    skill_info_shown = False
                    skill_info_button_index = None
                    skill_info_text = ""
                # (Removed direct death-start click handling.) Restart is handled via the settings menu Start button
        # Chuyển sang map 1 only when all monsters spawned on map 0 are dead and player reaches right edge
        if (first_wave_cleared and not wave_lock_active and current_map == 0 and player.rect.right >= settings.WIDTH and not map_transitioning):
            # check if any monsters that were spawned on map 0 are still alive
            any_map0_alive = any(getattr(m, 'spawn_map', None) == 0 and not getattr(m, 'is_dead', False) for m in monster_group)
            if not any_map0_alive:
                map_transitioning = True
                allow_player_move = False
                player.rect.right = settings.WIDTH  # Giữ player ở rìa phải khi chuyển map
            else:
                # Block movement to right until map0 monsters are dead
                allow_player_move = True

        # Nếu đang chuyển map thì cuộn offset liên tục cho đến khi đủ -settings.WIDTH
        if not paused:
            if map_transitioning:
                bg_scroller.offset -= 12  # tốc độ cuộn map, có thể chỉnh lại cho mượt
                if bg_scroller.offset <= -settings.WIDTH:
                    bg_scroller.offset = -settings.WIDTH
                    current_map = 1
                    # Đặt player về đầu map mới, tránh kẹt ở rìa phải
                    player.rect.left = 0
                    player.rect.y = GROUND_Y  # đảm bảo player ở đúng vị trí mặt đất
                    try:
                        # play next-map SFX
                        sound_mod.play_next_map()
                    except Exception:
                        pass
                    map_transitioning = False
                    allow_player_move = True
                    # Nếu chưa có monster wave 2 thì spawn luôn khi sang map mới
                    if monster_wave == 1:
                        monster_kill_count = 0
                        positions = [min_x + 60, min_x + 130, min_x + 200]
                        spawn_goblins(positions, from_left=False)
                        monster_wave = 2

        # (background swap moved later so wave count is up-to-date)

        # --- Bắt đầu khối lệnh trong while running ---
        keys = pygame.key.get_pressed()
        # Nếu đang pause thì bỏ qua phần update chính của game
        if not paused:
            if current_map == 2:
                player_group.update(dt, keys, can_move_left=True)
            else:
                # Chỉ cho phép đi sang trái khi đã sang map giữa (current_map >= 1)
                can_move_left = current_map >= 1 and allow_player_move
                if allow_player_move:
                    player_group.update(dt, keys, can_move_left=can_move_left)

            # (no dynamic block here; Player.update enforces right-edge clamp)

            # Truyền player vào update để quái biết vị trí player
            monster_group.update(dt, player)
            # KHÔNG cập nhật vị trí monster theo delta_offset, monster đứng yên
            # (Nếu có đoạn code monster.rect.x += int(delta_offset) thì xóa đi)
            # Chỉ cập nhật trạng thái monster bình thường
            items.update(dt)

        # Kiểm tra nếu player tấn công (attack1,2,3,R) và va chạm với monster, chỉ thực hiện khi vừa bắt đầu hoạt ảnh tấn công
        for monster in monster_group:
            # Player tấn công quái: chỉ gây sát thương nếu player đang đối mặt monster
            if player.action in ['attack1', 'attack2', 'attack3', 'attackR'] and player.frame_idx == 0:
                if player.rect.colliderect(monster.rect):
                    # Player phải hướng về phía monster
                    if (player.facing_right and player.rect.centerx < monster.rect.centerx) or (not player.facing_right and player.rect.centerx > monster.rect.centerx):
                        # If the monster currently has an active shield, skip applying any damage/effects.
                        # This ensures bosses with a visible shield (e.g., Bringer) are immune while shield_active.
                        if getattr(monster, 'shield_active', False):
                            continue

                        if player.action == 'attackR':
                            # R attack: heavy strike. For boss types (Demon, Wizard, Bringer)
                            # reduce current HP by ~50% (of remaining bars). Respect shields and invincibility.
                            if getattr(monster, 'shield_active', False) or getattr(monster, 'invincible_time', 0) > 0:
                                continue
                            is_boss_like = (
                                isinstance(monster, Demon)
                                or isinstance(monster, Wizard)
                                or isinstance(monster, Bringer)
                                or getattr(monster, 'hp_bar_style', '') in ('demon', 'wizard', 'bringer')
                            )
                            # Play takehit animation if available
                            if getattr(monster, 'takehit_frames', None):
                                try:
                                    monster.set_action('takehit')
                                except Exception:
                                    pass

                            if is_boss_like:
                                try:
                                    total_idx = len(monster.hp_bar_imgs) - 1
                                    # remaining positive HP bars (0 == full)
                                    remaining = max(0, total_idx - int(getattr(monster, 'hp_bar_idx', 0)))
                                    if remaining <= 0:
                                        # already at zero remaining -> schedule death
                                        monster._pending_death = True
                                    else:
                                        # remove roughly half of the current remaining bars
                                        remove = math.ceil(remaining * 0.5)
                                        new_remaining = max(0, remaining - remove)
                                        new_idx = total_idx - new_remaining
                                        # ensure hp_bar_idx only increases (more missing bars)
                                        monster.hp_bar_idx = min(total_idx, max(int(getattr(monster, 'hp_bar_idx', 0)), new_idx))
                                        monster.hp_bar_visible = True
                                        if monster.hp_bar_idx >= total_idx:
                                            monster._pending_death = True
                                except Exception:
                                    # fallback to full-kill behavior on error
                                    try:
                                        monster.hp_bar_idx = len(monster.hp_bar_imgs) - 1
                                        monster.hp_bar_visible = True
                                        monster._pending_death = True
                                    except Exception:
                                        pass
                            else:
                                # Non-boss: behave as before (set to death)
                                try:
                                    monster.hp_bar_idx = len(monster.hp_bar_imgs) - 1
                                    monster.hp_bar_visible = True
                                    monster._pending_death = True
                                except Exception:
                                    pass
                        elif player.action == 'attack2':
                            # Đòn E: mỗi lần dùng sẽ tăng máu monster lên 2 mức
                            monster.next_hp_bar(damage=2)
                            monster.hp_bar_visible = True
                        else:
                            monster.next_hp_bar(damage=2)  # Monster mất máu nhanh hơn

            # Sau khi vẽ máu về hpms6.png, chuyển sang death ở frame tiếp theo
            if hasattr(monster, '_pending_death') and monster._pending_death:
                if getattr(monster, 'action', None) == 'takehit' and getattr(monster, 'takehit_timer', 0) > 0:
                    continue
                monster.hp_bar_idx = len(monster.hp_bar_imgs) - 1
                del monster._pending_death
            # Monster tấn công player: chỉ gây sát thương nếu monster đang đối mặt player
            # Consider all attack variants (attack, attack1, attack2, ...). Wizard uses 'attack1'/'attack2'.
            # Prevent dead monsters from performing attack logic
            if getattr(monster, 'is_dead', False):
                continue

            if hasattr(monster, 'action') and getattr(monster, 'action', '').startswith('attack') and getattr(monster, 'frame_idx', 0) == 0:
                if monster.rect.colliderect(player.rect):
                    if (monster.facing_right and monster.rect.centerx < player.rect.centerx) or (not monster.facing_right and monster.rect.centerx > player.rect.centerx):
                        try:
                            # Bosses (Demon, Wizard, Bringer) show hurt visuals; regular monsters only change HP without the hurt overlay
                            # If the player has an active shield, player.next_hp_bar will early-return and block hurt/damage.
                            is_boss_like = (
                                isinstance(monster, Demon)
                                or isinstance(monster, Wizard)
                                or isinstance(monster, Bringer)
                                or getattr(monster, 'hp_bar_style', '') in ('wizard', 'bringer')
                            )
                            # For hits caused by Bringer, allow hurt visuals but do NOT block movement.
                            try:
                                if isinstance(monster, Bringer):
                                    player.hurt_blocks_movement = False
                                else:
                                    player.hurt_blocks_movement = True
                            except Exception:
                                # best-effort: if attribute missing, ignore
                                pass
                            if is_boss_like:
                                player.next_hp_bar(hurt=True)
                                # If attacker is Bringer, heal the boss on hit and schedule a one-time shield after 3s
                                try:
                                    if isinstance(monster, Bringer):
                                        # heal over 2 seconds (monsters interpret hp_bar_idx as missing bars)
                                        try:
                                            monster.start_heal(duration=2.0)
                                        except Exception:
                                            pass
                                        # schedule one-time shield in 3 seconds; only set if not already pending
                                        try:
                                            # set a default duration for the one-time shield
                                            monster.shield_once_duration = max(0.0, float(getattr(monster, 'shield_once_duration', 1.5))) or 1.5
                                        except Exception:
                                            monster.shield_once_duration = 1.5
                                        try:
                                            if not getattr(monster, '_pending_shield_timer', 0.0):
                                                monster._pending_shield_timer = 3.0
                                            else:
                                                # refresh the pending timer to 3s on each hit
                                                monster._pending_shield_timer = 3.0
                                        except Exception:
                                            try:
                                                monster._pending_shield_timer = 3.0
                                            except Exception:
                                                pass
                                except Exception:
                                    pass
                            else:
                                player.next_hp_bar(hurt=False)
                        except Exception:
                            player.next_hp_bar(hurt=False)

        # Kiểm tra va chạm và chỉ cho phép nhặt item sau 0.5 giây
        if not paused:
            picked_items = [item for item in items if player.rect.colliderect(item.rect) and getattr(item, 'can_pickup', lambda: True)()]
            for item in picked_items:
                items.remove(item)
            inventory += len(picked_items)

        # If player is in death state, show defeat image first (once). After the first frame showing it,
        # we keep it shown until the player clicks; clicking will open the settings/menu panel.
        if getattr(player, 'action', None) == 'death' and not defeat_shown and not setting_open:
            defeat_shown = True
            setting_open = False

        # When defeat image is shown, persist the session score once (if logged in)
        if defeat_shown and not score_persisted:
            try:
                if login_mod is not None and username and player_score > 0:
                    # Persist score
                    try:
                        login_mod.add_score(username, player_score)
                    except Exception:
                        pass
                    # Attempt to compute the player's rank in the stored leaderboard (top list)
                    try:
                        lb = login_mod.get_leaderboard()
                        r = None
                        for i, (u, d) in enumerate(lb):
                            try:
                                if u == username:
                                    r = i + 1
                                    break
                            except Exception:
                                continue
                        final_rank = r
                    except Exception:
                        final_rank = None
            except Exception:
                pass
            try:
                score_persisted = True
            except Exception:
                pass

        # Chỉ cho phép cuộn map khi đã giết 2 monster đầu tiên
        direction = 0
        # Map 0 và 1: Chỉ cho phép cuộn khi đã giết 2 monster đầu và không bị khóa
        # Map 2: Chỉ cho phép cuộn khi đã hoàn thành tất cả các wave (bg2_wave_stage >= 4)
        if current_map < 2:
            # Logic cũ cho map 0 và 1
            allow_scroll = (monster_wave > 1 or first_wave_cleared) and not wave_lock_active and monster_wave < 5
        else:
            # Map 2 (background2) cho phép cuộn, nhưng map 3 đứng yên để nền cố định.
            allow_scroll = not _bg3_applied
        
        if allow_scroll:
            if hasattr(player, 'moving_left') and player.moving_left:
                direction = -1
            elif hasattr(player, 'moving_right') and player.moving_right:
                direction = 1
            # Fallback: when wide single-tile backgrounds are active (bg2/bg3), also scroll if
            # the player is pushing against a screen edge while additional background remains.
            if direction == 0 and _bg2_applied and not _bg3_applied:
                try:
                    remaining = max(0, bg_scroller.bg_img.get_width() - bg_scroller.screen_width)
                except Exception:
                    remaining = 0
                if remaining > 0:
                    if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and player.rect.right >= settings.WIDTH and bg_scroller.offset < remaining:
                        direction = 1
                    elif (keys[pygame.K_LEFT] or keys[pygame.K_a]) and player.rect.left <= 0 and bg_scroller.offset > 0:
                        direction = -1
        else:
            if settings.DEBUG and DEBUG_LOGS and current_map == 2 and direction == 0:
                print("[DEBUG bg2] allow_scroll False", flush=True)
        # Nếu chưa đủ điều kiện, direction luôn = 0 (map đứng yên)
        bg_scroller.update(direction)
        bg_scroller.draw(screen)
        # Vẽ banner pixel chạy ngang qua
        if welcome_banner and not welcome_banner.done:
            welcome_banner.draw(screen)
        # Vẽ các thành phần game bình thường
        draw_player_hp(screen, player)
        from core.ui_game import draw_player_mana
        # Chỉ vẽ thanh mana nếu không phải Demon
        if not isinstance(player, Demon):
            draw_player_mana(screen, player)

        # Draw session score under player's HP bar
        try:
            # Pixel-style rendering: render at smaller base size then scale up for blocky/pixel look
            def _render_pixel_text_at(surf, text, base_size, scale, color, pos, center=False):
                try:
                    # choose a Unicode-capable font (fallback to system)
                    try:
                        base_f = load_pixel_font(base_size)
                    except Exception:
                        base_f = pygame.font.SysFont(None, base_size)
                    t_surf = base_f.render(text, True, color)
                    if scale and scale > 1:
                        w, h = t_surf.get_size()
                        t_surf = pygame.transform.scale(t_surf, (w * scale, h * scale))
                    if center:
                        r = t_surf.get_rect(center=pos)
                    else:
                        r = t_surf.get_rect(topleft=pos)
                    surf.blit(t_surf, r)
                    return r
                except Exception:
                    try:
                        t_surf = pygame.font.SysFont(None, base_size).render(text, True, color)
                        r = t_surf.get_rect(topleft=pos)
                        surf.blit(t_surf, r)
                        return r
                    except Exception:
                        return None

            score_text = f"Score: {player_score}"
            try:
                sx = hp_x
                sy = hp_y + hp_h + 20
            except Exception:
                sx, sy = 20, 10 + 30 + 20
            # shadow then text (use scale=1 for smaller size)
            _render_pixel_text_at(screen, score_text, 14, 1, (0, 0, 0), (sx + 1, sy + 1))
            _render_pixel_text_at(screen, score_text, 14, 1, (255, 255, 255), (sx, sy))
        except Exception:
            pass

        items.draw(screen)
        if _bg3_applied:
            try:
                any_bg3_alive = any(getattr(m, 'spawn_map', None) == 3 and not getattr(m, 'is_dead', False) for m in monster_group)
            except Exception:
                any_bg3_alive = False

            try:
                bringer_alive = any(isinstance(m, Bringer) and not getattr(m, 'is_dead', False) for m in monster_group)
            except Exception:
                bringer_alive = False

            # If the bringer has just been defeated, show victory image once
            try:
                if not bringer_alive and not bringer_defeated and _bringer_spawned:
                    bringer_defeated = True
                    # Show unified end overlay (reuse defeat overlay code) but mark as victory
                    defeat_shown = True
                    end_is_victory = True
                    try:
                        if 'sound_mod' in globals() and sound_mod is not None:
                            sound_mod.play_game_win()
                    except Exception:
                        pass
                    # do not immediately open leaderboard here; user will be able to press Rank
                    # keep victory_shown/victory_timer for backward compatibility (optional)
                    victory_shown = True
                    victory_timer = 5.0
            except Exception:
                pass

            if not any_bg3_alive:
                if bg3_wave_stage == 0 and not bg3_wave_spawned:
                    spawn_bg3_skeletons(count=3, wave_index=1)
                elif bg3_wave_stage == 1:
                    spawn_bg3_skeletons(count=5, wave_index=2)
                elif bg3_wave_stage == 2:
                    spawn_bg3_skeletons(count=7, wave_index=3)
                elif bg3_wave_stage == 3 and not _bringer_spawned:
                    spawn_bringer_boss()
                elif bg3_wave_stage == 4 and not bringer_alive:
                    bg3_wave_stage = 5
                    allow_player_move = True

        player_group.draw(screen)
        # Draw logged-in player's name above the player
        try:
            if username:
                # Prefer pixel font used elsewhere in the game
                display_name = str(username)
                # truncate to avoid very long names overflowing
                if len(display_name) > 20:
                    display_name = display_name[:17] + '...'
                # render name pixel-style using small base and scale
                def _render_pixel_name(text, pos_center):
                    try:
                        try:
                            base_f = load_pixel_font(12)
                        except Exception:
                            base_f = pygame.font.SysFont(None, 12)
                        surf = base_f.render(text, True, (255, 255, 255))
                        # keep name small: do not upscale (scale = 1)
                        shadow = base_f.render(text, True, (0, 0, 0))
                        r = surf.get_rect(center=pos_center)
                        screen.blit(shadow, (r.x + 1, r.y + 1))
                        screen.blit(surf, r)
                    except Exception:
                        try:
                            fallback = pygame.font.SysFont(None, 14)
                            s = fallback.render(text, True, (255, 255, 255))
                            r = s.get_rect(center=pos_center)
                            screen.blit(s, r)
                        except Exception:
                            pass

                if hasattr(player, 'rect'):
                    nx = player.rect.centerx
                    ny = player.rect.top - 6
                    _render_pixel_name(display_name, (nx, ny))
        except Exception:
            pass
        # (removed global red overlay - player handles its own hurt visuals)
        # Nếu đang tạm dừng, vẽ chữ PAUSED lên màn hình để người chơi biết
        if paused:
            paused_font = pygame.font.SysFont(None, 48)
            txt = paused_font.render('PAUSED', True, (255, 255, 255))
            tr = txt.get_rect(center=(settings.WIDTH//2, settings.HEIGHT//2))
            overlay = pygame.Surface((tr.width+20, tr.height+20), pygame.SRCALPHA)
            overlay.fill((0,0,0,160))
            screen.blit(overlay, (tr.x-10, tr.y-10))
            screen.blit(txt, tr)
        # Vẽ vòng sáng miễn nhiễm nếu player đang dùng F
        if hasattr(player, 'defend_invincible') and player.defend_invincible > 0:
            # Vẽ vòng sáng trắng mờ, nhỏ vừa với nhân vật
            px, py = player.rect.centerx, player.rect.centery
            radius = int(max(player.rect.width, player.rect.height) * 0.6)
            surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255,255,255,70), (radius, radius), radius)
            screen.blit(surf, (px-radius, py-radius))
        monster_group.draw(screen)
        for monster in monster_group:
            # if monster is a Demon instance, let it render its overlay
            if hasattr(monster, 'render_overlay'):
                try:
                    monster.render_overlay(screen)
                except Exception:
                    pass
            else:
                if getattr(monster, 'shield_active', False):
                    radius = int(max(monster.rect.width, monster.rect.height) * 0.7)
                    surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                    pygame.draw.circle(surf, (80, 200, 255, 90), (radius, radius), radius)
                    screen.blit(surf, (monster.rect.centerx - radius, monster.rect.centery - radius))
        for monster in list(monster_group):
            # Luôn vẽ thanh máu cho monster còn sống
            # Khi monster chuyển sang trạng thái death lần đầu, đếm kill ngay lập tức (tránh bị lọt do kill())
            if getattr(monster, 'is_dead', False) and not getattr(monster, '_counted', False):
                monster._counted = True
                monster_kill_count += 1
                # Determine points for this kill: boss types get 2, regular monsters get 1
                try:
                    pts = 2 if isinstance(monster, (Demon, Wizard, Bringer)) else 1
                except Exception:
                    pts = 1
                # Increment the session score
                try:
                    player_score += pts
                except Exception:
                    pass
                # Do NOT persist per-kill; we'll persist the total session score once when the run ends
                pass
                
                # Kiểm tra nếu là Wizard boss ở map 2 thì mở khóa bg2_wave_lock
                if getattr(monster, 'spawn_map', None) == 2 and isinstance(monster, Wizard):
                    bg2_wave_lock = False  # Mở khóa map sau khi giết Wizard
                    wizard_defeated = True
                    if settings.DEBUG and DEBUG_LOGS:
                        print("[DEBUG bg2-wave] Wizard defeated! Unlocking bg2 map scrolling", flush=True)
                
                if monster_wave == 1 and monster_kill_count == 2:
                    first_wave_cleared = True
                    wave_lock_active = True
                    monster_kill_count = 0
                    positions = [min_x + 60, min_x + 130, min_x + 200]
                    spawn_monsters(positions, from_left=False, use_delayed=False)
                    monster_wave = 2
                elif monster_wave == 2 and monster_kill_count == 3:
                    wave_lock_active = True
                    monster_kill_count = 0
                    positions = [min_x + 40, min_x + 90, min_x + 140, min_x + 190, min_x + 240]
                    spawn_goblins(positions, delay_base=2.0, from_left=False, use_delayed=False)
                    monster_wave = 3
                elif monster_wave == 3 and monster_kill_count == 5:
                    wave_lock_active = True
                    monster_kill_count = 0
                    positions = [min_x + 150]
                    wave_four_target = len(positions)
                    spawn_monsters(
                        positions,
                        from_left=False,
                        use_delayed=False,
                        monster_cls=Demon,
                        monster_kwargs={'size': (120, 120)}
                    )
                    try:
                        # mark demon as spawned so we don't double-spawn in edge cases
                        _demon_spawned = True
                    except Exception:
                        pass
                    monster_wave = 4
                elif monster_wave == 4 and wave_four_target and monster_kill_count == wave_four_target:
                    wave_lock_active = False
                    monster_kill_count = 0
                    wave_four_target = 0
                    monster_wave = 5

            if not (hasattr(monster, 'is_dead') and monster.is_dead and monster.action == 'death' and monster.frame_idx >= len(monster.frames)):
                draw_monster_hp(screen, monster)
            if hasattr(monster, 'is_dead') and monster.is_dead and monster.action == 'death' and monster.frame_idx >= len(monster.frames):
                if hasattr(monster, 'drop_item') and monster.drop_item and monster.drop_item_pos and hasattr(monster, 'item_img'):
                    item_rect = monster.item_img.get_rect(midbottom=monster.drop_item_pos)
                    item = Item(item_rect.center, monster.item_img)
                    items.add(item)
                    monster.drop_item = False
                monster_group.remove(monster)
                continue
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # hide any skill info popup when mouse released
                try:
                    skill_info_pressed = False
                    skill_info_shown = False
                    skill_info_button_index = None
                    skill_info_text = ""
                except Exception:
                    pass
            if event.type == pygame.MOUSEMOTION:
                # if user drags pointer outside the pressed button while holding, hide the popup
                try:
                    if skill_info_pressed and skill_info_button_index is not None:
                        if not action_button_rects[skill_info_button_index].collidepoint(event.pos):
                            skill_info_pressed = False
                            skill_info_shown = False
                            skill_info_button_index = None
                            skill_info_text = ""
                except Exception:
                    pass
        # If we're on background2 and it's been applied, and all bg2 monsters are dead, spawn the next bg2 wave
        # Handle bg2 internal waves if background2 has been applied
        if _bg2_applied:
            try:
                any_bg2_alive = any(getattr(m, 'spawn_map', None) == 2 and not getattr(m, 'is_dead', False) for m in monster_group)
            except Exception:
                any_bg2_alive = False

            if not any_bg2_alive:
                # Advance internal bg2 waves: 1 -> 2 -> 3 -> wizard(4)
                if bg2_wave_stage == 0:
                    bg2_wave_stage = 1
                    bg2_wave_lock = True  # Khóa map khi spawn wave đầu tiên
                elif bg2_wave_stage == 1:
                    # spawn second bg2 wave (4 crows)
                    try:
                        positions = [min_x + 40, min_x + 100, min_x + 160, min_x + 220]
                        if settings.DEBUG and DEBUG_LOGS:
                            print("[DEBUG bg2-wave] spawning 4 crows (wave 2)", flush=True)
                        spawn_bg2_crows(positions, delay_step=0.25)
                        bg2_wave_stage = 2
                        bg2_wave_lock = True  # Tiếp tục khóa map
                    except Exception as _e:
                        if settings.DEBUG and DEBUG_LOGS:
                            print(f"[DEBUG bg2-wave] failed spawning wave 2: {_e}", flush=True)
                elif bg2_wave_stage == 2:
                    # spawn third bg2 wave (6 crows)
                    try:
                        positions = [min_x + 40, min_x + 100, min_x + 160, min_x + 220, min_x + 280, min_x + 340]
                        if settings.DEBUG and DEBUG_LOGS:
                            print("[DEBUG bg2-wave] spawning 6 crows (wave 3)", flush=True)
                        spawn_bg2_crows(positions, delay_step=0.2)
                        bg2_wave_stage = 3
                        bg2_wave_lock = True  # Tiếp tục khóa map
                    except Exception as _e:
                        if settings.DEBUG and DEBUG_LOGS:
                            print(f"[DEBUG bg2-wave] failed spawning wave 3: {_e}", flush=True)
                elif bg2_wave_stage == 3:
                    # After the third crow wave cleared, spawn the Wizard boss as the 4th bg2 wave
                    if _wizard_spawned:
                        try:
                            bg2_wave_stage = 4
                            bg2_wave_lock = False  # Mở khóa sau khi giết Wizard
                        except Exception:
                            pass
                    else:
                        try:
                            # prepare wizard spawn parameters
                            try:
                                item_img = load_image('assets/imagesitems/item.png', size=(40, 40))
                            except Exception:
                                item_img = None
                            try:
                                p_w, p_h = player.rect.size
                                scale = 2.0
                                wiz_w = max(120, int(p_w * scale))
                                wiz_h = max(120, int(p_h * scale))
                                wiz_size = (wiz_w, wiz_h)
                            except Exception:
                                wiz_size = (180, 180)
                            try:
                                margin = 40
                                wiz_x = max(wiz_size[0] // 2 + 10, settings.WIDTH - wiz_size[0] // 2 - margin)
                            except Exception:
                                wiz_x = settings.WIDTH - 180 // 2 - 40

                            # spawn Wizard: start off-screen right and slide in to wiz_target_x on ground
                            try:
                                # prefer the previously computed wiz_x if available; otherwise use 60% width
                                wiz_target_x = wiz_x if 'wiz_x' in locals() else int(settings.WIDTH * 0.6)
                                spawn_from_right_x = settings.WIDTH + 100
                                # Use the wiz_size computed earlier
                                wiz_anims = build_wizard_animations()
                                wizard = Wizard((wiz_target_x, GROUND_Y), GROUND_Y, size=wiz_size, min_x=50, max_x=settings.WIDTH-50, item_img=item_img, animations=wiz_anims)

                                # Place the wizard off-screen to the right and ensure it's grounded
                                try:
                                    wizard.rect.left = spawn_from_right_x
                                except Exception:
                                    pass
                                try:
                                    # Anchor wizard bottom using wizard.ground_offset so artwork aligns consistently
                                    target_bottom = int(GROUND_Y - getattr(wizard, 'ground_offset', 0))
                                    wizard.rect.bottom = target_bottom
                                except Exception:
                                    try:
                                        wizard.rect.bottom = GROUND_Y
                                    except Exception:
                                        pass

                                # Slide-in target and entry flags (update will move toward target_x)
                                wizard.target_x = wiz_target_x
                                wizard._entering = True
                                wizard.from_left = False
                                wizard.entry_speed = 2
                                try:
                                    wizard.spawn_map = 2
                                except Exception:
                                    pass

                                monster_group.add(wizard)
                                try:
                                    if settings.DEBUG and DEBUG_LOGS:
                                        print(f"[DEBUG bg2-wave] Wizard spawn-from-right: start_x={spawn_from_right_x} target_x={wiz_target_x} size={wiz_size}", flush=True)
                                except Exception:
                                    pass

                                bg2_wave_stage = 4
                                _bg2_applied = True
                                bg2_wave_lock = True  # Khóa map khi Wizard spawn
                                try:
                                    _wizard_spawned = True
                                except Exception:
                                    pass
                            except Exception as _e:
                                try:
                                    if settings.DEBUG and DEBUG_LOGS:
                                        print(f"[DEBUG bg2-wave] failed to spawn wizard: {_e}", flush=True)
                                except Exception:
                                    pass
                        except Exception as _e:
                            try:
                                if settings.DEBUG and DEBUG_LOGS:
                                    print(f"[DEBUG bg2-wave] failed to spawn wizard delayed: {_e}", flush=True)
                            except Exception:
                                pass
                            try:
                                bg2_wave_stage = 3
                            except Exception:
                                pass
        # After handling monster deaths and wave progression, attempt background2 swap
        if not _bg2_applied and monster_wave >= 5 and player.rect.right >= settings.WIDTH:
            if _map2 is not None:
                try:
                    bg2 = _map2.load_bg(settings.WIDTH)
                    if bg2 is not None:
                        # Ensure background2 fully covers the screen: scale to (WIDTH, HEIGHT)
                        try:
                            bg2 = pygame.transform.smoothscale(bg2, (settings.WIDTH, settings.HEIGHT))
                        except Exception:
                            try:
                                bg2 = pygame.transform.scale(bg2, (settings.WIDTH, settings.HEIGHT))
                            except Exception:
                                pass
                        bg_scroller.bg_img = bg2
                        bg_scroller.screen_width = settings.WIDTH
                        # bg2 is full-screen, render as single tile to avoid tiling artifacts
                        bg_scroller.num_tiles = 1
                        # ensure offset is reset so we are not mid-scroll
                        try:
                           bg_scroller.offset = 0
                        except Exception:
                           pass
                        # Debug print to terminal so we can verify the swap occurred and size
                        try:
                           path = _map2._find_background_path()
                        except Exception:
                           pass
                        try:
                           w, h = bg2.get_size()
                           pass
                        except Exception:
                           pass
                        # place player at left edge of the new background so they can walk in
                        try:
                            player.rect.left = 0
                            allow_player_move = True
                        except Exception:
                            pass
                        # Spawn crow monsters that slide in from the right when background2 is applied
                        try:
                            # Build animation lists for monstercrow if available
                            crow_base = os.path.join('assets', 'imagesmonster', 'monster', 'monstercrow')
                            def _list_sorted(sub):
                                p = os.path.join(crow_base, sub)
                                if os.path.isdir(p):
                                    files = [os.path.join(p, f).replace('\\', '/') for f in sorted(os.listdir(p)) if f.lower().endswith('.png')]
                                    return files
                                return []

                            crow_idle = _list_sorted('crow_idle')
                            crow_run = _list_sorted('crow_walk') or _list_sorted('crow_run')
                            crow_attack = _list_sorted('crow_attack')
                            crow_death = _list_sorted('crow_death1') + _list_sorted('crow_death2')
                            crow_takehit = _list_sorted('crow_damage')

                            crow_anims = {}
                            if crow_idle:
                                crow_anims['idle'] = crow_idle
                            if crow_run:
                                crow_anims['run'] = crow_run
                            if crow_attack:
                                crow_anims['attack'] = crow_attack
                            if crow_death:
                                crow_anims['death'] = crow_death
                            if crow_takehit:
                                crow_anims['takehit'] = crow_takehit

                            # Only spawn if we found at least one animation frame
                            if any(crow_anims.values()):
                                # Decide how many crows to spawn based on how many times bg2 has been visited
                                bg2_visit_count += 1
                                if bg2_visit_count == 1:
                                    # Increase initial bg2 crow wave from 3 to 4
                                    crow_count = 3
                                elif bg2_visit_count == 2:
                                    crow_count = 4
                                else:
                                    crow_count = 6
                                # Generate spawn x positions spaced across the area
                                spacing = 60
                                start_x = min_x + 40
                                positions = [start_x + i * spacing for i in range(crow_count)]
                                # ...existing code...
                                # ...existing code...
                                spawn_bg2_crows(positions, delay_step=0.2)
                                bg2_wave_stage = 3
                                bg2_wave_lock = True  # Khóa map ngay khi spawn crow wave đầu
                            else:
                                pass
                        except Exception as _e:
                            pass
                        # Mark that we've spawned the first internal bg2 wave so the wave-checker won't immediately chain more
                        try:
                            bg2_wave_stage = 1
                            bg2_wave_lock = True  # Khóa map khi bắt đầu vào background2
                            pass
                        except Exception:
                            pass
                        _bg2_applied = True
                        try:
                            sound_mod.play_next_map()
                        except Exception:
                            pass
                        if settings.DEBUG and DEBUG_LOGS:
                            try:
                                print(f"[DEBUG bg2] applied background2 width={bg_scroller.bg_img.get_width()} num_tiles={bg_scroller.num_tiles}", flush=True)
                            except Exception:
                                pass
                except Exception:
                    _bg2_applied = False
        # After wizard defeated, allow transition to background3 when reaching right edge
        if wizard_defeated and _bg2_applied and not _bg3_applied and player.rect.right >= settings.WIDTH:
            if _map3 is not None:
                try:
                    bg3 = _map3.load_bg(settings.WIDTH)
                    if bg3 is not None:
                        try:
                            bg_scroller.bg_img = bg3
                            bg_scroller.screen_width = settings.WIDTH
                            bg_scroller.num_tiles = 1
                            bg_scroller.offset = 0
                        except Exception:
                            pass
                        try:
                            player.rect.left = 0
                        except Exception:
                            pass
                        allow_player_move = True
                        _bg3_applied = True
                        try:
                            sound_mod.play_next_map()
                        except Exception:
                            pass
                        if not bg3_wave_spawned:
                            try:
                                bg3_wave_spawned = spawn_bg3_skeletons()
                            except Exception:
                                bg3_wave_spawned = False
                        if settings.DEBUG and DEBUG_LOGS:
                            try:
                                print(f"[DEBUG bg3] applied background3 width={bg_scroller.bg_img.get_width()} num_tiles={bg_scroller.num_tiles}", flush=True)
                            except Exception:
                                pass
                except Exception:
                    _bg3_applied = False
        player_group.draw(screen)
        monster_group.draw(screen)
        items.draw(screen)
        draw_inventory(screen, font, inventory)
        # No HUD block message shown
        # Vẽ 5 nút: nếu itemshp_states[i] True thì itemshp.png, False thì itemshp5.png
        for i, rect in enumerate(itemshp_rects):
            if itemshp_states[i]:
                screen.blit(itemshp_imgs[i], rect)
            else:
                screen.blit(itemshp5_img, rect)
        # Vẽ nút setting ở góc phải trên
        screen.blit(setting_img, setting_rect)
        # Vẽ các button di chuyển ở góc phải dưới
        for img, rect in zip(button_imgs, button_rects):
            screen.blit(img, rect)
        # Vẽ các nút chức năng Q, E, R, F ở phía bên phải, ngang hàng với các nút di chuyển
        # Lấy cooldown từng chiêu từ player
        cooldowns = [0, 0, 0, 0]
        if hasattr(player, 'attack_cooldown'):
            cooldowns[0] = max(player.attack_cooldown, 0)  # Q
        if hasattr(player, 'cooldown_e'):
            cooldowns[1] = max(player.cooldown_e, 0)        # E
        if hasattr(player, 'cooldown_r'):
            cooldowns[2] = max(player.cooldown_r, 0)        # R
        if hasattr(player, 'cooldown_f'):
            cooldowns[3] = max(player.cooldown_f, 0)        # F

        for i, (img, rect) in enumerate(zip(action_button_imgs, action_button_rects)):
            cd = cooldowns[i]
            if cd > 0.05:
                # Tạo bản xám của nút
                gray_img = img.copy()
                gray_img.fill((120,120,120,180), special_flags=pygame.BLEND_RGBA_MULT)
                screen.blit(gray_img, rect)
                # Hiển thị số giây còn lại (làm tròn xuống)
                sec = int(cd+0.99)
                font_cool = pygame.font.SysFont(None, 32)
                text = font_cool.render(str(sec), True, (255,255,0))
                text_rect = text.get_rect(center=rect.center)
                screen.blit(text, text_rect)
            else:
                screen.blit(img, rect)
            # Draw skill info popup if requested (simple wrapped text box)
            # Only show while pressed (press-and-hold UX)
            if skill_info_pressed and skill_info_button_index is not None and skill_info_text:
                try:
                    # choose pixel font if available
                    try:
                        info_font = load_pixel_font(16)
                    except Exception:
                        info_font = pygame.font.SysFont(None, 16)

                    # basic word-wrapping
                    def wrap_text(text, font, max_w):
                        words = text.split(' ')
                        lines = []
                        cur = ''
                        for w in words:
                            test = (cur + ' ' + w).strip()
                            if font.size(test)[0] <= max_w:
                                cur = test
                            else:
                                if cur:
                                    lines.append(cur)
                                cur = w
                        if cur:
                            lines.append(cur)
                        return lines

                    anchor_rect = action_button_rects[skill_info_button_index]
                    max_w = min(360, settings.WIDTH - 40)
                    lines = wrap_text(skill_info_text, info_font, max_w - 24)
                    line_h = info_font.get_linesize()
                    box_w = max((info_font.size(ln)[0] for ln in lines), default=200) + 24
                    box_h = line_h * len(lines) + 20
                    # position above the button if possible, otherwise above center
                    bx = anchor_rect.centerx - box_w // 2
                    by = anchor_rect.top - box_h - 8
                    if by < 8:
                        by = anchor_rect.bottom + 8
                    # clamp to screen
                    bx = max(8, min(bx, settings.WIDTH - box_w - 8))
                    s = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
                    pygame.draw.rect(s, (10, 10, 10, 220), (0, 0, box_w, box_h), border_radius=8)
                    pygame.draw.rect(s, (200, 200, 200, 30), (0, 0, box_w, box_h), 2, border_radius=8)
                    screen.blit(s, (bx, by))
                    # render lines
                    ox = bx + 12
                    oy = by + 10
                    for ln in lines:
                        try:
                            surf = info_font.render(ln, True, (255, 255, 255))
                        except Exception:
                            surf = pygame.font.SysFont(None, 16).render(ln, True, (255, 255, 255))
                        screen.blit(surf, (ox, oy))
                        oy += line_h
                except Exception:
                    # be resilient - do nothing on render error
                    pass
        # If the bringer was defeated, always show the victory overlay
        if bringer_defeated:
            if victory_img:
                try:
                    screen.blit(victory_img, victory_rect)
                except Exception:
                    pass
        # Otherwise, if a defeat overlay is requested (player death), render the defeat image
        elif defeat_shown:
            if defeat_img:
                try:
                    screen.blit(defeat_img, defeat_rect)
                except Exception:
                    pass
            # Ensure end_rect is defined for the shared final-score/buttons rendering below
            try:
                end_rect = defeat_rect
            except Exception:
                end_rect = None

        # Shared final session score + buttons for both defeat and bringer victory
        if (defeat_shown or bringer_defeated):
            # determine which end rect to use (victory prefers victory_rect)
            try:
                if bringer_defeated and victory_rect:
                    end_rect = victory_rect
                elif defeat_shown and defeat_rect:
                    end_rect = defeat_rect
            except Exception:
                end_rect = end_rect if 'end_rect' in locals() else None
            try:
                try:
                    big_font = load_pixel_font(28)
                except Exception:
                    big_font = pygame.font.SysFont(None, 28)
                final_text = f"Your Score: {player_score}"
                # Append rank info when available
                try:
                    if final_rank is not None:
                        display_text = f"{final_text} (Top #{final_rank})"
                    else:
                        display_text = final_text
                except Exception:
                    display_text = final_text
                # render at smaller base size then scale for pixel look
                try:
                    base = big_font.render(display_text, True, (255, 215, 0))
                    w, h = base.get_size()
                    # render at base size (no extra upscale) for smaller final score text
                    scaled = base
                    shadow = big_font.render(display_text, True, (0, 0, 0))
                except Exception:
                    try:
                        base = pygame.font.SysFont(None, 28).render(display_text, True, (255, 215, 0))
                        w, h = base.get_size()
                        scaled = base
                        shadow = pygame.font.SysFont(None, 28).render(display_text, True, (0, 0, 0))
                    except Exception:
                        scaled = None
                        shadow = None
                # Place below the end image (or center if end_rect missing)
                if scaled:
                    if end_rect:
                        fx = end_rect.centerx - scaled.get_width() // 2
                        fy = end_rect.bottom + 10
                    else:
                        fx = settings.WIDTH // 2 - scaled.get_width() // 2
                        fy = settings.HEIGHT // 2 + 60
                    # Background box for readability
                    try:
                        box = pygame.Surface((scaled.get_width() + 20, scaled.get_height() + 12), pygame.SRCALPHA)
                        pygame.draw.rect(box, (0, 0, 0, 180), (0, 0, box.get_width(), box.get_height()), border_radius=8)
                        screen.blit(box, (fx - 10, fy - 6))
                    except Exception:
                        pass
                    try:
                        screen.blit(shadow, (fx + 1, fy + 1))
                        screen.blit(scaled, (fx, fy))
                    except Exception:
                        pass
                # Draw interactive buttons: Restart and Leaderboard
                try:
                    btn_w, btn_h = 140, 40
                    spacing = 12
                    total_w = btn_w * 2 + spacing
                    # use 'scaled' which holds the final score surface
                    bx = fx + (scaled.get_width() // 2) - total_w // 2 if scaled else fx - total_w // 2
                    by = fy + (scaled.get_height() if scaled else 0) + 14
                    # button backgrounds
                    btn_surf = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
                    pygame.draw.rect(btn_surf, (40, 40, 40, 220), (0, 0, btn_w, btn_h), border_radius=8)
                    pygame.draw.rect(btn_surf, (200, 200, 200, 20), (0, 0, btn_w, btn_h), 2, border_radius=8)
                    screen.blit(btn_surf, (bx, by))
                    screen.blit(btn_surf, (bx + btn_w + spacing, by))
                    # button labels
                    try:
                        btn_font = load_pixel_font(18)
                    except Exception:
                        btn_font = pygame.font.SysFont(None, 18)
                    # Use brown text for buttons and rename 'Leaderboard' -> 'Rank'
                    brown_col = (109, 54, 28)
                    restart_txt = btn_font.render('Restart', True, brown_col)
                    leader_txt = btn_font.render('Rank', True, brown_col)
                    # shadows (keep black for contrast)
                    restart_shadow = btn_font.render('Restart', True, (0, 0, 0))
                    leader_shadow = btn_font.render('Rank', True, (0, 0, 0))
                    rx = bx + (btn_w - restart_txt.get_width()) // 2
                    ry = by + (btn_h - restart_txt.get_height()) // 2
                    lx = bx + btn_w + spacing + (btn_w - leader_txt.get_width()) // 2
                    ly = by + (btn_h - leader_txt.get_height()) // 2
                    screen.blit(restart_shadow, (rx + 1, ry + 1))
                    screen.blit(restart_txt, (rx, ry))
                    screen.blit(leader_shadow, (lx + 1, ly + 1))
                    screen.blit(leader_txt, (lx, ly))
                except Exception:
                    pass
            except Exception:
                pass
        # Nếu bringer bị tiêu diệt thì hiện victory image trong vài giây
        if victory_shown and victory_img:
            try:
                screen.blit(victory_img, victory_rect)
            except Exception:
                pass
            try:
                victory_timer = max(0.0, victory_timer - dt)
                if victory_timer <= 0:
                    victory_shown = False
            except Exception:
                pass

        # Nếu setting_open, vẽ khung setting và các nút lên trên cùng
        if setting_open:
            n = len(setting_button_imgs)
            btn_w, btn_h = 40, 40
            spacing = 18
            box_w = btn_w + 80  # to ra
            box_h = n*btn_h + (n-1)*spacing + 60  # to ra
            box_x = (settings.WIDTH - box_w) // 2
            box_y = (settings.HEIGHT - box_h) // 2
            s = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            pygame.draw.rect(s, (60, 60, 60, 220), (0, 0, box_w, box_h), border_radius=22)
            screen.blit(s, (box_x, box_y))
            for i, (img, rect) in enumerate(zip(setting_button_imgs, setting_button_rects)):
                rect.centerx = box_x + box_w // 2
                rect.y = box_y + 30 + i*(btn_h + spacing)
                screen.blit(img, rect)
        pygame.display.flip()

    pygame.quit()
    sys.exit()
