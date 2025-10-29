import os
import sys
import pygame
import random
try:
	from core import resources as resources
except Exception:
	resources = None


def load_image(path, size=None):
	# Preferred: delegate to core.resources if available
	try:
		if resources is not None:
			return resources.load_image(path, size=size)
	except Exception:
		# fall through to trying to resolve path manually
		pass

	# Try to resolve an absolute path that works inside a bundled EXE
	try:
		# If resources module partially failed to import but exists, try its resource_path
		if resources is not None and hasattr(resources, 'resource_path'):
			resolved = resources.resource_path(path)
		else:
			base = getattr(sys, '_MEIPASS', None) or os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
			resolved = os.path.join(base, path.replace('/', os.sep))
		if os.path.exists(resolved):
			img = pygame.image.load(resolved).convert_alpha()
			if size and img.get_size() != size:
				img = pygame.transform.smoothscale(img, size)
			return img
	except Exception:
		pass

	# Final fallback: try loading with given relative path (may fail in EXE working dir)
	img = pygame.image.load(path).convert_alpha()
	if size and img.get_size() != size:
		img = pygame.transform.smoothscale(img, size)
	return img

# Thêm biến để lưu toạ độ và trạng thái drop item cho monster
class Monster(pygame.sprite.Sprite):
	# ...existing code...
	def __init__(
		self,
		pos,
		ground_y,
		size=None,
		min_x=None,
		max_x=None,
		item_img=None,
		animations=None,
		asset_faces_right=True,
		ground_offset=0,
		takehit_on_damage=True,
		hp_bar_paths=None,
		hp_bar_size=(45, 6),
		hp_bar_always_visible=False,
		hp_bar_offset=-1,
		hp_bar_x_offset=10,
		shield_interval=None,
		shield_duration=0.0,
	):
		super().__init__()
		# Load các hoạt ảnh từ thư mục imagesmonster theo cấu hình
		if animations is None:
			# Prefer new location assets/imagesmonster/monster/goblins then fall back to legacy
			legacy_base = os.path.join('assets', 'imagesmonster', 'goblins')
			new_base = os.path.join('assets', 'imagesmonster', 'monster', 'goblins')
			# When running from a bundled EXE the working directory is different.
			# Resolve each candidate via resources.resource_path (if available) and
			# pick the one that actually exists and contains frames.
			candidates = [new_base, legacy_base]
			base_monster_path = new_base  # default to new_base
			for cand in candidates:
				try:
					resolved = resources.resource_path(cand) if resources is not None else cand
				except Exception:
					resolved = cand
				# ensure the directory exists and has at least one png in idlemonster
				idle_dir = os.path.join(resolved, 'idlemonster')
				if os.path.isdir(idle_dir):
					pngs = [f for f in os.listdir(idle_dir) if f.lower().endswith('.png')]
					if pngs:
						base_monster_path = cand
						break
			idle_paths = [os.path.join(base_monster_path, 'idlemonster', f'I{i}.png').replace('\\', '/') for i in range(1, 5)]
			run_paths = [os.path.join(base_monster_path, 'runmonster', f'Run{i}.png').replace('\\', '/') for i in range(1, 9)]
			attack_paths = [os.path.join(base_monster_path, 'attackmonster', f'At{i}.png').replace('\\', '/') for i in range(1, 9)]
			death_paths = [os.path.join(base_monster_path, 'deathmonster', f'D{i}.png').replace('\\', '/') for i in range(1, 5)]
			takehit_paths = [os.path.join(base_monster_path, 'takehitmonster', f'Take Hit {i}.png').replace('\\', '/') for i in range(1, 5)]
		else:
			idle_paths = animations.get('idle', [])
			run_paths = animations.get('run', [])
			attack_paths = animations.get('attack', [])
			death_paths = animations.get('death', [])
			takehit_paths = animations.get('takehit', [])
		self.idle_frames = [load_image(path, size) for path in idle_paths]
		self.run_frames = [load_image(path, size) for path in run_paths]
		self.attack_frames = [load_image(path, size) for path in attack_paths]
		self.death_frames = [load_image(path, size) for path in death_paths]
		self.takehit_frames = [load_image(path, size) for path in takehit_paths]
		# Load any additional named animations provided in animations dict (e.g. 'jump')
		if animations:
			for k, paths in animations.items():
				attr = f"{k}_frames"
				# don't overwrite already loaded standard frames
				if hasattr(self, attr):
					continue
				try:
					setattr(self, attr, [load_image(p, size) for p in paths])
				except Exception:
					setattr(self, attr, [])
		self.asset_faces_right = asset_faces_right
		self.ground_offset = ground_offset
		self.takehit_on_damage = takehit_on_damage
		self.hp_bar_always_visible = hp_bar_always_visible
		self.hp_bar_target_size = hp_bar_size if hp_bar_paths else None
		# General default style for monsters; boss subclasses can override this
		self.hp_bar_style = 'default'
		# Hoạt ảnh thanh máu
		if hp_bar_paths:
			self.hp_bar_imgs = [load_image(path) for path in hp_bar_paths]
		else:
			self.hp_bar_imgs = [load_image(f'assets/hp/hpmonster/hpms{i}.png', hp_bar_size) for i in range(1, 7)]
		self.hp_bar_idx = 0
		self.hp_bar_visible = hp_bar_always_visible  # Mặc định hiện với boss, ẩn với quái thường
		self.hp_bar_offset = hp_bar_offset
		self.hp_bar_x_offset = hp_bar_x_offset
		self._hp_bar_cache = {}
		self.hp_bar_animating = False
		self.hp_bar_anim_timer = 0.0
		self.hp_bar_anim_speed = 1/15
		self.shield_interval = shield_interval
		self.shield_duration = shield_duration
		self.shield_timer = shield_interval if shield_interval else 0.0
		self.shield_active = False
		self.shield_active_timer = 0.0
		self.trigger_shield_threshold = None
		self.shield_once_duration = 0.0
		self.shield_once_action = None
		self._shield_triggered = False
		self._shield_restore_action = None

		# Healing-over-time state for monsters (bosses will use this when triggered)
		self.healing = False
		self.heal_total_time = 0.0
		self.heal_time_remaining = 0.0
		self._heal_remaining_bars = 0
		self._heal_interval = 0.0
		self._heal_interval_timer = 0.0

		self.frames = self.idle_frames
		self.frame_idx = 0
		self.image = self.frames[0]  # Idle là frame đầu tiên
		# Monster xuất hiện từ ngoài bên phải khung hình
		self.target_pos = pos  # Lưu vị trí đích
		self.rect = self.image.get_rect()
		self.rect.bottom = ground_y - self.ground_offset
		import settings
		self.rect.left = settings.WIDTH + random.randint(10, 100)  # Xuất hiện ngoài màn hình phải

		self.ground_y = ground_y

		self.anim_timer = 0.0
		self.anim_speed = 1/8
		self.action = 'run'
		self.facing_right = False
		self.idle_delay = 0  # Thời gian idle còn lại (giây)
		# Giới hạn di chuyển ngang
		self.min_x = min_x
		self.max_x = max_x
		self.speed = random.choice([1, 2, 3])
		self.move_timer = 0.0
		self.move_interval = random.uniform(1.0, 2.5)  # thời gian đổi hướng
		self.entering = False  # Không dùng entering nữa
		self.takehit_timer = 0
		self.takehit_duration = 0.5  # giây, thời gian hiệu ứng takehit giữ lại
		self.is_dead = False
		self.drop_item = False
		self.drop_item_pos = None
		self.item_img = item_img
		# Thời gian miễn nhiễm sau khi nhận sát thương
		self.invincible_time = 0.0
		self.invincible_duration = 0.2  # giây (monster nhận sát thương nhanh hơn player)
		# Thêm cooldown tấn công
		self.attack_cooldown = 0.0
		self.attack_cooldown_time = 1.5  # giây

	def _orient_frame(self, frame_img):
		if self.facing_right != self.asset_faces_right:
			return pygame.transform.flip(frame_img, True, False)
		return frame_img

	def set_action(self, action, player=None, attack_range=40):
		if self.action != action:
			self.action = action
			self.frame_idx = 0
			if action == 'idle':
				self.frames = self.idle_frames
				self.anim_speed = 1/8
			elif action == 'run':
				self.frames = self.run_frames
				self.anim_speed = 1/10
			elif action == 'jump':
				# prefer explicit jump frames if available
				self.frames = getattr(self, 'jump_frames', self.idle_frames)
				self.anim_speed = 1/12
			elif action == 'attack':
				self.frames = self.attack_frames
				self.anim_speed = 1/12
				# Chỉ random vị trí khi bắt đầu tấn công
				if player is not None:
					import random
					offset = random.randint(-20, 20)
					if self.rect.centerx < player.rect.centerx:
						self.facing_right = True
						self.rect.centerx = player.rect.centerx - attack_range + offset
					else:
						self.facing_right = False
						self.rect.centerx = player.rect.centerx + attack_range + offset
			elif action == 'takehit':
						# Only switch to takehit if we have frames for it
						if getattr(self, 'takehit_frames', None):
							self.frames = self.takehit_frames
							self.anim_speed = 1/8
							self.takehit_timer = self.takehit_duration
						else:
							# no takehit frames; fall back to idle briefly
							self.frames = self.idle_frames
							self.anim_speed = 1/10
			elif action == 'death':
				self.frames = self.death_frames
				self.anim_speed = 1/8
			elif action == 'shield':
				self.frames = getattr(self, 'shield_frames', self.idle_frames)
				self.anim_speed = 1/10
			self.anim_timer = 0.0
			if self.frames:
				self.image = self._orient_frame(self.frames[self.frame_idx])

	def next_hp_bar(self, damage=2):
		# Gọi hàm này mỗi lần bị đánh trúng
		if self.invincible_time > 0 or self.shield_active:
			return  # Đang miễn nhiễm, không trừ máu
		# Tăng nhiều máu hơn mỗi lần bị đánh (mặc định 2 đơn vị, có thể chỉnh damage)
		if self.hp_bar_idx < len(self.hp_bar_imgs) - 1:
			self.hp_bar_idx += damage
			if self.hp_bar_idx > len(self.hp_bar_imgs) - 1:
				self.hp_bar_idx = len(self.hp_bar_imgs) - 1
			self.invincible_time = self.invincible_duration
		self.hp_bar_visible = True
		# Chuyển sang hoạt ảnh bị đánh (takehit)
		if self.takehit_on_damage:
			self.set_action('takehit')


	def start_heal(self, duration=2.0):
		"""Start a heal-over-time that will evenly restore missing HP bars over `duration` seconds.

		This mirrors Player.start_heal but for monsters: hp_bar_idx counts missing bars (0 == full).
		"""
		missing = self.hp_bar_idx
		if missing <= 0:
			return
		self.heal_total_time = duration
		self.heal_time_remaining = duration
		self._heal_remaining_bars = missing
		self._heal_interval = duration / max(1, missing)
		self._heal_interval_timer = self._heal_interval
		self.healing = True

	def update(self, dt, player=None):
		if self.shield_interval:
			if self.shield_active:
				self.shield_active_timer -= dt
				if self.shield_active_timer <= 0:
					self.shield_active = False
					self.shield_timer = self.shield_interval
			else:
				self.shield_timer -= dt
				if self.shield_timer <= 0:
					self.shield_active = True
					self.shield_active_timer = self.shield_duration
					self.shield_timer = self.shield_interval
		else:
			if self.shield_active:
				self.shield_active_timer = max(0.0, self.shield_active_timer - dt)
		# Giảm thời gian miễn nhiễm sát thương
		if self.invincible_time > 0:
			self.invincible_time -= dt

		# Trigger one-time shields when dropping below a threshold (used by skeletons on map3)
		try:
			threshold = getattr(self, 'trigger_shield_threshold', None)
			if threshold is not None and not getattr(self, '_shield_triggered', False):
				if self.hp_bar_idx >= threshold:
					self._shield_triggered = True
					duration = getattr(self, 'shield_once_duration', 1.5)
					if duration <= 0:
						duration = 1.5
					self.shield_active = True
					self.shield_active_timer = duration
					self._shield_restore_action = 'idle'
					try:
						desired = getattr(self, 'shield_once_action', None)
						if desired:
							self.set_action(desired)
						elif getattr(self, 'shield_frames', None):
							self.set_action('shield')
						else:
							self.set_action('idle')
					except Exception:
						self.set_action('idle')
					self.anim_timer = 0.0
		except Exception:
			pass

		# Support for externally scheduled one-time shields (e.g., Bringer special behavior).
		# If `_pending_shield_timer` is set (>0) it counts down and, when reaches 0, activates a
		# one-time shield for `shield_once_duration` seconds without enabling periodic shielding.
		try:
			if getattr(self, '_pending_shield_timer', 0.0) > 0:
				self._pending_shield_timer = max(0.0, getattr(self, '_pending_shield_timer', 0.0) - dt)
				if getattr(self, '_pending_shield_timer', 0.0) <= 0.0:
					# activate one-time shield
					duration = float(getattr(self, 'shield_once_duration', 1.5))
					self._one_time_shield_active = True
					self._one_time_shield_timer = duration
					# mark visible shield and timer
					self.shield_active = True
					self.shield_active_timer = duration
					# Clear pending marker
					try:
						delattr(self, '_pending_shield_timer')
					except Exception:
						# fallback: set to 0
						self._pending_shield_timer = 0.0
		except Exception:
			pass

		if self.shield_active and not self.shield_interval:
			self.anim_timer += dt
			if self.anim_timer >= self.anim_speed:
				self.anim_timer = 0.0
				if self.frames:
					self.frame_idx = (self.frame_idx + 1) % len(self.frames)
			if self.frames:
				self.image = self._orient_frame(self.frames[self.frame_idx])
			if self.shield_active_timer <= 0:
				self.shield_active = False
				restore = getattr(self, '_shield_restore_action', None)
				if restore and not getattr(self, 'is_dead', False):
					self.set_action(restore)
				self._shield_restore_action = None
			else:
				return

		# If a one-time shield is active, manage its timer and clear it when done. This runs after
		# the periodic shield branch above so it only affects one-time activations.
		try:
			if getattr(self, '_one_time_shield_active', False):
				self._one_time_shield_timer = max(0.0, getattr(self, '_one_time_shield_timer', 0.0) - dt)
				# ensure shield_active reflects this one-time shield
				self.shield_active = True
				self.shield_active_timer = getattr(self, '_one_time_shield_timer', 0.0)
				if getattr(self, '_one_time_shield_timer', 0.0) <= 0.0:
					self._one_time_shield_active = False
					self.shield_active = False
					self.shield_active_timer = 0.0
					# clear restore action marker
					self._shield_restore_action = None
		except Exception:
			pass

		# Healing over time for monsters (when start_heal was called)
		if getattr(self, 'healing', False):
			try:
				self.heal_time_remaining = max(0.0, self.heal_time_remaining - dt)
				self._heal_interval_timer -= dt
				while self._heal_remaining_bars > 0 and self._heal_interval_timer <= 0:
					# restore one HP bar (hp_bar_idx represents missing bars)
					if self.hp_bar_idx > 0:
						self.hp_bar_idx = max(0, self.hp_bar_idx - 1)
					self._heal_remaining_bars -= 1
					if self._heal_remaining_bars > 0:
						self._heal_interval_timer += self._heal_interval
				if self._heal_remaining_bars <= 0 or self.heal_time_remaining <= 0:
					self.healing = False
			except Exception:
				# On error, cancel healing to avoid infinite loops
				self.healing = False
		# Nếu monster còn ở ngoài phải, chỉ cho phép di chuyển vào, nhưng vẫn update AI và hoạt ảnh bình thường
		if self.rect.centerx > self.target_pos[0]:
			# Khi xuất hiện, luôn ép action là 'run' và chỉ dùng run_frames
			if self.action != 'run':
				self.action = 'run'
				self.frames = self.run_frames
				self.anim_speed = 1/10
				self.frame_idx = 0
			appear_speed = 2
			self.rect.x -= appear_speed
			self.facing_right = False
			# Cập nhật hoạt ảnh chạy khi xuất hiện
			self.anim_timer += dt
			if self.anim_timer >= self.anim_speed:
				self.anim_timer = 0.0
				self.frame_idx = (self.frame_idx + 1) % len(self.run_frames)
			self.image = self._orient_frame(self.run_frames[self.frame_idx])
			# Khi đã đến vị trí target_pos thì đặt đúng vị trí quy định và idle 1s
			if self.rect.centerx <= self.target_pos[0]:
				self.rect.centerx = self.target_pos[0]
				self.set_action('idle')
				self.idle_delay = 1.0
			return

		# Enforce locked coordinates if flagged (used by DelayedMonster and bg2 spawns)
		# This prevents external code or rounding from nudging monsters after arrival
		try:
			if getattr(self, '_lock_on_arrival', False):
				# lock bottom (vertical) if provided
				if getattr(self, '_locked_bottom', None) is not None:
					self.rect.bottom = int(self._locked_bottom)
				# lock centerx if provided
				if getattr(self, '_locked_centerx', None) is not None:
					self.rect.centerx = int(self._locked_centerx)
				# After enforcing the locked coords for this frame, clear the flag so AI can resume
				# allow a small grace period property if present
				if getattr(self, '_lock_frames', None) is None:
					# default: only lock for 1 frame after arrival
					self._lock_on_arrival = False
				else:
					try:
						self._lock_frames -= 1
						if self._lock_frames <= 0:
							self._lock_on_arrival = False
					except Exception:
						# if _lock_frames isn't an int or something goes wrong, clear the lock
						self._lock_on_arrival = False
		except Exception:
			pass
		# Phần còn lại giữ nguyên: luôn update action, hoạt ảnh theo logic AI phía dưới
		# Nếu máu đã cạn (hpms6.png) thì chuyển sang death và chỉ chạy hoạt ảnh death
		if self.hp_bar_idx == len(self.hp_bar_imgs) - 1:
			if not self.is_dead:
				self.set_action('death')
				self.is_dead = True
				self.drop_item = True
				self.drop_item_pos = self.rect.midbottom
				# demon-specific speech timers moved to Demon subclass
			# Chỉ animate death, không update gì khác, không vẽ thanh máu nữa
			self.anim_timer += dt
			if self.anim_timer >= self.anim_speed:
				self.anim_timer = 0.0
				self.frame_idx += 1
				if self.frame_idx >= len(self.frames):
					self.kill()
				else:
					self.image = self._orient_frame(self.frames[self.frame_idx])
			return

			# Giảm cooldown tấn công
			if self.attack_cooldown > 0:
				self.attack_cooldown -= dt
		# Nếu player chết thì monster không tấn công nữa, chỉ idle hoặc di chuyển
		if player is not None and getattr(player, 'action', None) == 'death':
			# Nếu đang attack hoặc takehit thì chuyển về run để không bị đứng yên
			if self.action in ['attack', 'takehit']:
				self.set_action('run')
			# Idle delay logic: nếu đang idle và có idle_delay > 0 thì chỉ đếm thời gian, hết thì chuyển sang run
			if self.idle_delay > 0:
				self.idle_delay -= dt
				if self.idle_delay <= 0:
					self.set_action('run')
					self.move_timer = 0.0
					self.move_interval = random.uniform(1.0, 2.5)
					self.speed = random.uniform(0.5, 1.2) * random.choice([-1, 1])
					if self.rect.centerx == self.target_pos[0]:
						self.speed = random.uniform(0.5, 1.2) * random.choice([-1, 1])
						self.rect.x += int(self.speed)
				self.anim_timer += dt
				if self.anim_timer >= self.anim_speed:
					self.anim_timer = 0.0
					self.frame_idx = (self.frame_idx + 1) % len(self.frames)
				self.image = self._orient_frame(self.frames[self.frame_idx])
				return
			# Nếu không idle delay thì di chuyển run như cũ
			if self.action == 'run' and self.min_x is not None and self.max_x is not None:
				self.move_timer += dt
				if self.move_timer >= self.move_interval:
					self.move_timer = 0.0
					self.move_interval = random.uniform(1.0, 2.5)
					self.speed = random.uniform(0.5, 1.2) * random.choice([-1, 1])
					self.set_action('idle')
					self.idle_delay = 1.0
					return
				self.rect.x += self.speed
				if self.rect.right >= self.max_x:
					self.rect.right = self.max_x
					self.speed = -abs(self.speed)
				elif self.rect.left <= self.min_x:
					self.rect.left = self.min_x
					self.speed = abs(self.speed)
				self.facing_right = self.speed > 0
			self.anim_timer += dt
			if self.anim_timer >= self.anim_speed:
				self.anim_timer = 0.0
				self.frame_idx = (self.frame_idx + 1) % len(self.frames)
			self.image = self._orient_frame(self.frames[self.frame_idx])
			return
		# Idle delay logic: nếu đang idle và có idle_delay > 0 thì chỉ đếm thời gian, hết thì chuyển sang run
		if self.idle_delay > 0:
			self.idle_delay -= dt
			if self.idle_delay <= 0:
				# Sau khi idle xong, luôn random lại hướng di chuyển mới
				self.set_action('run')
				self.move_timer = 0.0
				self.move_interval = random.uniform(1.0, 2.5)
				# Luôn random lại self.speed khác 0
				self.speed = random.uniform(0.5, 1.2) * random.choice([-1, 1])
				# Nếu monster đang ở đúng target_pos và không có player gần, ép monster phải di chuyển tiếp
				if self.rect.centerx == self.target_pos[0]:
					self.speed = random.uniform(0.5, 1.2) * random.choice([-1, 1])
					# Đẩy monster ra khỏi target_pos một chút để bắt đầu di chuyển
					self.rect.x += int(self.speed)
			# Vẫn update hoạt ảnh idle
			self.anim_timer += dt
			if self.anim_timer >= self.anim_speed:
				self.anim_timer = 0.0
				self.frame_idx = (self.frame_idx + 1) % len(self.frames)
			self.image = self._orient_frame(self.frames[self.frame_idx])
			return

		# Nếu đang ở trạng thái takehit thì giữ hiệu ứng trong takehit_duration
		if self.action == 'takehit':
			self.takehit_timer -= dt
			if self.takehit_timer <= 0:
				self.set_action('run')
		else:
			# AI: Nếu player ở gần thì tấn công, nếu player ở xa thì đuổi theo
			attack_range = 40
			chase_range = 200  # Nếu player trong phạm vi này thì monster sẽ đuổi theo
			can_attack = False
			if player is not None:
				distance = abs(self.rect.centerx - player.rect.centerx)
				# Nếu player ở gần thì tấn công
				if distance < attack_range:
					# Chỉ random vị trí khi chuyển sang attack, không random liên tục
					self.set_action('attack', player, attack_range)
					can_attack = True
				# Nếu player ở xa nhưng trong phạm vi chase_range thì monster đuổi theo
				elif distance < chase_range:
					self.set_action('run')
					# Monster di chuyển về phía player, không giới hạn min_x/max_x khi chase
					speed = 2
					if self.rect.centerx < player.rect.centerx:
						self.rect.x += speed
						self.facing_right = True
					else:
						self.rect.x -= speed
						self.facing_right = False
					can_attack = False
			if not can_attack:
				# Nếu không tấn công và không đuổi theo thì di chuyển ngẫu nhiên như cũ (giới hạn min_x/max_x)
				if self.action != 'idle':
					self.set_action('run')
				if self.action == 'run' and self.min_x is not None and self.max_x is not None and (player is None or abs(self.rect.centerx - player.rect.centerx) >= chase_range):
					self.move_timer += dt
					if self.move_timer >= self.move_interval:
						self.move_timer = 0.0
						self.move_interval = random.uniform(1.0, 2.5)
						self.speed = random.uniform(0.5, 1.2) * random.choice([-1, 1])
						# Khi đổi hướng, cho idle 1s rồi mới chạy tiếp
						self.set_action('idle')
						self.idle_delay = 1.0
						return
					self.rect.x += self.speed
					if self.rect.right >= self.max_x:
						self.rect.right = self.max_x
						self.speed = -abs(self.speed)
					elif self.rect.left <= self.min_x:
						self.rect.left = self.min_x
						self.speed = abs(self.speed)
					self.facing_right = self.speed > 0
		# Không animate thanh máu nữa, chỉ đổi frame khi bị đánh

		self.anim_timer += dt
		if self.anim_timer >= self.anim_speed:
			self.anim_timer = 0.0
			self.frame_idx = (self.frame_idx + 1) % len(self.frames)
		self.image = self._orient_frame(self.frames[self.frame_idx])

		# Nếu máu đã cạn (hpms6.png) thì chuyển sang death (trừ khi còn chờ pending death)
		if (self.hp_bar_idx == len(self.hp_bar_imgs) - 1
			and not self.is_dead
			and not getattr(self, '_pending_death', False)):
			self.set_action('death')
			self.is_dead = True
			self.drop_item = True
			self.drop_item_pos = self.rect.midbottom
		# Nếu đang death, animate xong thì kill sprite
		if self.action == 'death':
			self.anim_timer += dt
			if self.anim_timer >= self.anim_speed:
				self.anim_timer = 0.0
				self.frame_idx += 1
				if self.frame_idx >= len(self.frames):
					self.kill()
				else:
					self.image = self._orient_frame(self.frames[self.frame_idx])

	# Thêm phương thức mới để resize và sắp xếp 4 hình ảnh theo chiều ngang
	def resize_and_arrange_images(self, image_paths, size, spacing=10):
		# Tải và resize từng hình ảnh
		images = [load_image(path, size) for path in image_paths]

		# Tính toán kích thước của bức tranh ghép
		total_width = sum(image.get_width() for image in images) + spacing * (len(images) - 1)
		max_height = max(image.get_height() for image in images)

		# Tạo bức tranh ghép mới
		combined_image = pygame.Surface((total_width, max_height), pygame.SRCALPHA)

		# Vẽ từng hình ảnh lên bức tranh ghép
		x_offset = 0
		for image in images:
			combined_image.blit(image, (x_offset, (max_height - image.get_height()) // 2))
			x_offset += image.get_width() + spacing

		return combined_image
