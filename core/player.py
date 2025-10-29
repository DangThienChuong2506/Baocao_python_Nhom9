import pygame
try:
	from core import sound as sound_mod
except Exception:
	sound_mod = None

try:
	from core import resources as resources
except Exception:
	resources = None


def load_image(path, size=None):
	# Use core.resources to resolve paths so bundled EXE can find assets
	try:
		if resources is not None:
			return resources.load_image(path, size=size)
	except Exception:
		pass
	# fallback: direct load
	img = pygame.image.load(path).convert_alpha()
	if size and img.get_size() != size:
		img = pygame.transform.smoothscale(img, size)
	return img


class Player(pygame.sprite.Sprite):
	def __init__(self, pos=(0, 0), frames_dir=None, ground_y=400, min_y=0):
		super().__init__()

		# load simple frame lists (best-effort; missing assets will raise at runtime)
		self.idle_frames = [load_image(f'assets/imagesplayer/idle/IDLE 1.{i}.png') for i in range(7)]
		self.jump_frames = [load_image(f'assets/imagesplayer/jump/JUMP 1.{i}.png') for i in range(5)]
		self.walk_frames = [load_image(f'assets/imagesplayer/walk/WALK 1.{i}.png') for i in range(8)]
		self.attack1_frames = [load_image(f'assets/imagesplayer/attack1/ATTACK 1.{i}.png') for i in range(6)]
		self.attack2_frames = [load_image(f'assets/imagesplayer/attack2/ATTACK 2.{i}.png') for i in range(5)]
		self.attack3_frames = [load_image(f'assets/imagesplayer/attack3/ATTACK 3.{i}.png') for i in range(6)]
		self.defend_frames = [load_image(f'assets/imagesplayer/defend/DEFEND{i+1}.png') for i in range(6)]

		# visual / rect
		self.frames = self.idle_frames
		self.frame_idx = 0
		self.image = self.frames[self.frame_idx]
		self.rect = self.image.get_rect()
		# stick to bottom-left by default
		self.ground_y = ground_y
		self.rect.bottomleft = (pos[0], ground_y)

		# hp / mana (0..5 where 0 is full health)
		self.hp_bar_idx = 0
		self.mana_bar_idx = 0

		# timers / cooldowns
		self.mana_regen_timer = 0.0
		self.invincible_time = 0.0
		self.invincible_duration = 0.7
		self.defend_invincible = 0.0
		self.attack_cooldown = 0.0
		self.attack_cooldown_time = 0.2
		self.cooldown_e = 0.0
		self.cooldown_f = 0.0
		self.cooldown_r = 0.0
		self.attack_post_delay = 0.0

		# movement / physics
		self.anim_timer = 0.0
		self.anim_speed = 1 / 8
		self.min_y = min_y
		self.is_jumping = False
		self.velocity_y = 0.0
		self.gravity = 0.3
		self.jump_power = -18
		self.action = 'idle'
		self.facing_right = True

		# Healing-over-time state
		self.healing = False
		self.heal_total_time = 0.0
		self.heal_time_remaining = 0.0
		self._heal_remaining_bars = 0
		self._heal_interval = 0.0
		self._heal_interval_timer = 0.0
		# Hurt state (when taking damage)
		self.hurt = False
		self.hurt_time = 0.0
		self.hurt_duration = 0.5
		self.hurt_frames = None  # lazy-loaded list of hurt frames
		# Whether the hurt state should block player movement. Some attacks (e.g., Bringer special)
		# should still show hurt visuals but not disable movement; set to True by default.
		self.hurt_blocks_movement = True
		# Shield state (activated by pressing F)
		self.shield_active = False
		self.shield_timer = 0.0
		self.shield_duration = 1.5

	def set_death(self):
		self.action = 'death'
		self.death_frames = [load_image(f'assets/imagesplayer/death/DEATH{i}.png') for i in range(1, 13)]
		self.frames = self.death_frames
		self.anim_speed = 1 / 8
		self.frame_idx = 0
		# Play game-lose sound (one-shot) when player dies
		try:
			if 'sound_mod' in globals() and sound_mod is not None:
				sound_mod.play_game_lose()
		except Exception:
			pass

	def start_heal(self, duration=2.0):
		"""Start a healing-over-time that will evenly restore missing HP bars over `duration` seconds.

		The API: hp_bar_idx is number of missing bars (0..5). start_heal will schedule restoring those bars.
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

	def update(self, dt, keys, can_move_left=True, block_right=False):
		# movement flags used by world scrolling
		# Accept both arrow keys and WASD (A/D) so players can use either control scheme.
		self.moving_left = (bool(keys[pygame.K_LEFT]) or bool(keys[pygame.K_a])) and can_move_left
		self.moving_right = (bool(keys[pygame.K_RIGHT]) or bool(keys[pygame.K_d]))
		# allow external code to block right movement (e.g., when map progression blocked)
		if block_right:
			self.moving_right = False
		# remember original x so we can prevent horizontal movement while hurt
		orig_x = self.rect.x

		# mana regen
		if self.mana_bar_idx > 0:
			self.mana_regen_timer += dt
			if self.mana_regen_timer >= 1.5:
				self.mana_bar_idx = max(0, self.mana_bar_idx - 1)
				self.mana_regen_timer = 0.0
		else:
			self.mana_regen_timer = 0.0

		# cooldowns / invincibility
		for attr in ('defend_invincible', 'cooldown_e', 'cooldown_f', 'cooldown_r', 'attack_cooldown', 'attack_post_delay', 'invincible_time'):
			val = getattr(self, attr, 0.0)
			if val > 0:
				setattr(self, attr, max(0.0, val - dt))

		# healing over time
		if self.healing:
			self.heal_time_remaining = max(0.0, self.heal_time_remaining - dt)
			self._heal_interval_timer -= dt
			while self._heal_remaining_bars > 0 and self._heal_interval_timer <= 0:
				# restore one bar
				if self.hp_bar_idx > 0:
					self.hp_bar_idx = max(0, self.hp_bar_idx - 1)
				self._heal_remaining_bars -= 1
				if self._heal_remaining_bars > 0:
					self._heal_interval_timer += self._heal_interval
			if self._heal_remaining_bars <= 0 or self.heal_time_remaining <= 0:
				self.healing = False

		# hurt animation handling
		if self.hurt:
			self.hurt_time = max(0.0, self.hurt_time - dt)
			# If we have explicit hurt frames, use them
			if self.hurt_frames:
				# map hurt progress to frame index
				total = len(self.hurt_frames)
				if total > 0:
					idx = int((1.0 - (self.hurt_time / self.hurt_duration)) * total)
					idx = min(total - 1, max(0, idx))
					frame_img = self.hurt_frames[idx]
					if not self.facing_right:
						frame_img = pygame.transform.flip(frame_img, True, False)
					self.image = frame_img
			else:
				# fallback: tint current frame red by drawing a semi-transparent red overlay
				frame_img = self.frames[self.frame_idx]
				if not self.facing_right:
					frame_img = pygame.transform.flip(frame_img, True, False)
				surf = frame_img.copy()
				overlay = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
				overlay.fill((200, 30, 30, 200))
				surf.blit(overlay, (0, 0))
				self.image = surf
			if self.hurt_time <= 0:
				self.hurt = False

		# death handling: play death animation and gravity
		if self.hp_bar_idx >= 5 and getattr(self, 'action', None) != 'death':
			self.set_death()

		if getattr(self, 'action', None) == 'death':
			if self.rect.bottom < self.ground_y:
				self.velocity_y += self.gravity
				self.rect.y += self.velocity_y
				if self.rect.bottom >= self.ground_y:
					self.rect.bottom = self.ground_y
					self.velocity_y = 0.0
			self.anim_timer += dt
			if self.anim_timer >= self.anim_speed:
				self.anim_timer = 0.0
				if self.frame_idx < len(self.frames) - 1:
					self.frame_idx += 1
			frame_img = self.frames[self.frame_idx]
			if not self.facing_right:
				frame_img = pygame.transform.flip(frame_img, True, False)
			self.image = frame_img
			return

		# input / action handling
		# If player is hurt, optionally disable horizontal movement but still allow action input
		skip_movement = False
		if getattr(self, 'hurt', False) and getattr(self, 'hurt_blocks_movement', True):
			# Don't return early — we must still run gravity/jump physics below so player can fall while hurt.
			# But we want to allow actions (attacks/skills) while hurt; only block horizontal movement.
			skip_movement = True

		# Process action/state transitions even when hurt (so player can still attack),
		# but avoid initiating walk actions when movement is blocked.
		if self.action in ['attack1', 'attack2', 'attack3', 'attackR']:
			if self.frame_idx == len(self.frames) - 1:
				if not (keys[pygame.K_q] or keys[pygame.K_e] or keys[pygame.K_r]):
					if self.attack_post_delay <= 0:
						self.attack_post_delay = 0.3
					self.set_action('idle')
		elif self.action == 'defend':
			if not hasattr(self, '_defend_timer'):
				self._defend_timer = 0.3
			else:
				self._defend_timer -= dt
			if self._defend_timer <= 0 and not keys[pygame.K_f]:
				self.set_action('idle')
				self._defend_timer = 0.3
		else:
			if self.attack_post_delay > 0:
				if keys[pygame.K_f]:
					self.set_action('defend')
				elif not self.is_jumping and (keys[pygame.K_UP] or keys[pygame.K_SPACE] or keys[pygame.K_w]):
					if self.rect.bottom >= self.ground_y:
						self.is_jumping = True
						self.velocity_y = self.jump_power
						self.set_action('jump')
						try:
							if 'sound_mod' in globals() and sound_mod is not None:
								sound_mod.play_jump()
						except Exception:
							pass
				elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
					self.facing_right = False
					if not self.is_jumping and not skip_movement:
						self.set_action('walk')
				elif (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and not block_right:
					self.facing_right = True
					if not self.is_jumping and not skip_movement:
						self.set_action('walk')
				elif not self.is_jumping:
					self.set_action('idle')
			else:
				if keys[pygame.K_f] and self.cooldown_f <= 0 and self.mana_bar_idx <= 3:
					# Activate defend and shield
					self.set_action('defend')
					self.cooldown_f = 2.0
					self.mana_bar_idx = min(self.mana_bar_idx + 2, 5)
					try:
						if sound_mod is not None:
							sound_mod.play_skill('F')
					except Exception:
						pass
					try:
						self.shield_active = True
						self.shield_timer = float(getattr(self, 'shield_duration', 1.5))
						# also set defend invincibility so next_hp_bar respects it
						self.defend_invincible = float(getattr(self, 'shield_duration', 1.5))
					except Exception:
						self.shield_active = True
						self.shield_timer = 1.5
						self.defend_invincible = 1.5
				elif keys[pygame.K_q] and self.attack_cooldown <= 0:
					self.set_action('attack1')
					self.attack_cooldown = self.attack_cooldown_time
					try:
						if sound_mod is not None:
							sound_mod.play_skill('Q')
					except Exception:
						pass
				elif keys[pygame.K_e] and self.cooldown_e <= 0 and self.mana_bar_idx <= 4:
					self.set_action('attack2')
					self.cooldown_e = 1.5
					self.mana_bar_idx = min(self.mana_bar_idx + 1, 5)
					try:
						if sound_mod is not None:
							sound_mod.play_skill('E')
					except Exception:
						pass
				elif keys[pygame.K_r] and self.cooldown_r <= 0 and self.mana_bar_idx <= 2:
					self.set_action('attackR')
					self.cooldown_r = 4.0
					self.mana_bar_idx = min(self.mana_bar_idx + 3, 5)
					try:
						if sound_mod is not None:
							sound_mod.play_skill('R')
					except Exception:
						pass
				elif not self.is_jumping and (keys[pygame.K_UP] or keys[pygame.K_SPACE] or keys[pygame.K_w]):
					if self.rect.bottom >= self.ground_y:
						self.is_jumping = True
						self.velocity_y = self.jump_power
						self.set_action('jump')
						try:
							if 'sound_mod' in globals() and sound_mod is not None:
								sound_mod.play_jump()
						except Exception:
							pass
				elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
					self.facing_right = False
					if not self.is_jumping and not skip_movement:
						self.set_action('walk')
				elif (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and not block_right:
					self.facing_right = True
					if not self.is_jumping and not skip_movement:
						self.set_action('walk')
				elif not self.is_jumping:
					self.set_action('idle')

		# horizontal movement (skip if hurt)
			if not skip_movement and self.action not in ['attack1', 'attack2', 'attack3']:
				move_speed = 3
				# horizontal movement: support A/D as well as arrow keys
				if keys[pygame.K_LEFT] or keys[pygame.K_a]:
					self.rect.x -= move_speed
				if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and not block_right:
					self.rect.x += move_speed
			# left edge clamp (existing)
			if self.rect.left < 0:
				self.rect.left = 0
			# right edge clamp: don't allow leaving the screen
			try:
				import settings as _s
				if self.rect.right > _s.WIDTH:
					self.rect.right = _s.WIDTH
			except Exception:
				pass

		# jumping / gravity
		if self.is_jumping:
			self.velocity_y += self.gravity
			self.rect.y += self.velocity_y
			import settings
			min_top = int(settings.HEIGHT / 3)
			if self.rect.top < min_top:
				self.rect.top = min_top
				if self.velocity_y < 0:
					self.velocity_y = 0
			if self.rect.bottom >= self.ground_y:
				self.rect.bottom = self.ground_y
				self.is_jumping = False
				self.velocity_y = 0
				self.set_action('idle')
		else:
			self.rect.bottom = self.ground_y

		# animation
		self.anim_timer += dt
		if self.anim_timer >= self.anim_speed:
			self.anim_timer = 0.0
			self.frame_idx = (self.frame_idx + 1) % len(self.frames)

		frame_img = self.frames[self.frame_idx]
		if not self.facing_right:
			frame_img = pygame.transform.flip(frame_img, True, False)
		# Only overwrite the current image if we're not showing the hurt effect
		if not getattr(self, 'hurt', False):
			self.image = frame_img

		# decrement shield timer
		if getattr(self, 'shield_active', False):
			try:
				self.shield_timer = max(0.0, self.shield_timer - dt)
				if self.shield_timer <= 0:
					self.shield_active = False
			except Exception:
				self.shield_active = False

		# If hurt and hurt_blocks_movement is True, restore original x to prevent horizontal movement
		# while still allowing gravity. If hurt_blocks_movement is False (e.g., hit by Bringer), allow movement.
		if getattr(self, 'hurt', False) and getattr(self, 'hurt_blocks_movement', True):
			try:
				self.rect.x = orig_x
			except Exception:
				pass

		# If hurt animation finished this frame, reset movement-blocking to default
		if not getattr(self, 'hurt', False):
			try:
				# Ensure future hits default to blocking movement unless explicitly changed by attacker
				self.hurt_blocks_movement = True
			except Exception:
				pass

	def set_action(self, action):
		if self.action != action:
			prev_action = self.action
			self.action = action
			self.frame_idx = 0
			# stop walking sound if we were walking and are leaving it
			try:
				if prev_action == 'walk' and 'sound_mod' in globals() and sound_mod is not None:
					sound_mod.play_walk_stop()
			except Exception:
				pass
			if action == 'idle':
				self.frames = self.idle_frames
				self.anim_speed = 1 / 10
			elif action == 'walk':
				self.frames = self.walk_frames
				self.anim_speed = 1 / 10
				try:
					if 'sound_mod' in globals() and sound_mod is not None:
						sound_mod.play_walk_start()
				except Exception:
					pass
			elif action == 'jump':
				self.frames = self.jump_frames
				self.anim_speed = 1 / 10
			elif action == 'attack1':
				self.frames = self.attack1_frames
				self.anim_speed = 1 / 10
			elif action == 'attack2':
				self.frames = self.attack2_frames
				self.anim_speed = 1 / 10
			elif action == 'attack3':
				self.frames = self.attack3_frames
				self.anim_speed = 1 / 10
			elif action == 'attackR':
				self.frames = self.attack3_frames
				self.anim_speed = 1 / 10
			elif action == 'defend':
				self.frames = self.defend_frames
				self.anim_speed = 1 / 8
				self.defend_invincible = 3.0

	def next_hp_bar(self, hurt=True):
		"""Called when player takes damage: increment hp_bar_idx up to 5 and set invincibility.

		If hurt is True, also trigger the visual hurt effect. If False, only apply HP change and invincibility.
		"""
		# If shield is active, block damage and hurt visuals entirely
		if getattr(self, 'shield_active', False):
			return
		# Otherwise consider normal invincibility sources
		was_invincible = (self.invincible_time > 0) or (self.defend_invincible > 0)
		# If attacker is not supposed to trigger hurt visuals and player is invincible, skip
		if was_invincible and not hurt:
			return

		# If not currently invincible, apply HP change and start invincibility
		applied_damage = False
		if not was_invincible and self.hp_bar_idx < 5:
			self.hp_bar_idx += 1
			self.invincible_time = self.invincible_duration
			applied_damage = True

		# If this hit should show hurt visuals, trigger them (visual only if invincible)
		if hurt:
			# trigger hurt visual effect
			self.hurt = True
			self.hurt_time = self.hurt_duration
			# lazy-load hurt_frames from assets/imagesplayer/hurt if available
			if self.hurt_frames is None:
				try:
					import os
					hurt_dir = 'assets/imagesplayer/hurt'
					files = sorted([f for f in os.listdir(hurt_dir) if f.lower().endswith('.png')])
					if files:
						self.hurt_frames = [load_image(os.path.join(hurt_dir, f)) for f in files]
					else:
						self.hurt_frames = []
				except Exception:
					# no hurt frames; will fallback to tint overlay
					self.hurt_frames = []
			# Immediately set the image for this frame so the effect is visible
			try:
				if self.hurt_frames:
					img = self.hurt_frames[0]
					if not self.facing_right:
						img = pygame.transform.flip(img, True, False)
					self.image = img
				else:
					frame_img = self.frames[self.frame_idx]
					if not self.facing_right:
						frame_img = pygame.transform.flip(frame_img, True, False)
					surf = frame_img.copy()
					overlay = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
					overlay.fill((200, 30, 30, 120))
					surf.blit(overlay, (0, 0))
					self.image = surf
			except Exception:
				pass

