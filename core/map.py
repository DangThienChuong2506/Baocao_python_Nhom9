# Note: barrier images and draw_barriers feature removed.
# Các lớp và hàm khác vẫn giữ nguyên.
import os
import pygame
import settings
import time

class BackgroundScroller:
	def __init__(self, img_path, screen_width, speed=2):
		import pygame
		# Resolve image path via resources so packaged builds can find assets
		try:
			from core import resources as resources
			self.bg_img = pygame.image.load(resources.resource_path(img_path)).convert()
		except Exception:
			self.bg_img = pygame.image.load(img_path).convert()
		self.bg_img = pygame.transform.scale(self.bg_img, (screen_width, self.bg_img.get_height()))
		self.screen_width = screen_width
		self.speed = speed
		self.offset = 0
		self.num_tiles = 3  # Số lượng background nối nhau

	def update(self, direction):
		# direction: -1 (sang trái), 1 (sang phải), 0 (đứng yên)
		self.offset += direction * self.speed
		if self.num_tiles <= 1:
			width = self.bg_img.get_width()
			if width <= 0:
				self.offset = 0
				return
			max_offset = max(0, width - self.screen_width)
			if self.offset < 0:
				self.offset = 0
			elif self.offset > max_offset:
				self.offset = max_offset
			return
		width = self.bg_img.get_width()
		if width <= 0:
			return
		# Giữ offset trong phạm vi [-width, width) để tránh trôi quá xa
		if self.offset >= width:
			self.offset -= width
		elif self.offset <= -width:
			self.offset += width

	def draw(self, screen):
		if self.num_tiles <= 1:
			width = self.bg_img.get_width()
			if width <= 0:
				return
			x = -int(self.offset)
			screen.blit(self.bg_img, (x, 0))
			# Nếu ảnh nhỏ hơn màn hình, lấp đầy phần còn lại để tránh hở
			if width < self.screen_width:
				# lặp lại ảnh về bên phải cho đủ chiều rộng màn hình
				repeat_x = x + width
				while repeat_x < self.screen_width:
					screen.blit(self.bg_img, (repeat_x, 0))
					repeat_x += width
			return
		width = self.bg_img.get_width()
		if width <= 0:
			return
		effective_offset = self.offset % width
		start_x = -effective_offset
		x = start_x
		# Vẽ liên tiếp các tile để phủ kín màn hình theo chiều ngang
		while x < self.screen_width:
			screen.blit(self.bg_img, (x, 0))
			x += width
		# Vẽ thêm một tile về bên trái để tránh hở khi offset nhỏ
		screen.blit(self.bg_img, (start_x - width, 0))


# Sử dụng font pixel nhỏ (VD: 'PressStart2P' nếu có, fallback Consolas)
class WelcomeBanner:
	def __init__(self, lines, font_size=18, color=(255,255,255), speed=60):
		pygame.font.init()
		self.lines = lines  # list các dòng
		try:
			self.font = pygame.font.Font("assets/fonts/PressStart2P.ttf", font_size)
		except:
			self.font = pygame.font.SysFont('Consolas', font_size, bold=True)
		self.color = color
		self.speed = speed
		self.start_time = time.time()
		self.done = False
		self.char_interval = 0.035
		# support arbitrary number of lines: track how many chars shown for each line
		self.chars_shown = [0 for _ in lines]
		self.last_update = time.time()
		self.fade_in = True
		self.alpha = 0
		self.fade_speed = 10
		# current line index being typed (0..len(lines)-1). When it reaches len(lines) we start the done timer.
		self.current_line = 0

	def update(self):
		now = time.time()
		# Hiệu ứng xuất hiện từng ký tự cho từng dòng, tiến tới các dòng tiếp theo tuần tự
		if self.current_line < len(self.lines):
			# reveal characters for the current line
			cur = self.current_line
			if self.chars_shown[cur] < len(self.lines[cur]):
				if now - self.last_update > self.char_interval:
					self.chars_shown[cur] += 1
					self.last_update = now
			else:
				# finished current line, wait a short delay then advance to next line
				if not hasattr(self, 'line_done_time') or self.line_done_time is None:
					self.line_done_time = now
				elif now - self.line_done_time > 0.6:
					# advance to next line
					self.current_line += 1
					self.line_done_time = None
					self.last_update = now
		else:
			# all lines shown: start done countdown
			if not hasattr(self, 'done_timer'):
				self.done_timer = now
			elif now - self.done_timer > 2.5:
				self.done = True
		# Hiệu ứng fade in
		if self.fade_in and self.alpha < 255:
			self.alpha += self.fade_speed
			if self.alpha > 255:
				self.alpha = 255

	def draw(self, screen):
		if self.done:
			return
		x_center = settings.WIDTH // 2
		line_h = self.font.get_height()
		spacing = 10
		offset_y = -60  # Dời lên trên 60px để tránh che thanh máu

		def draw_text_with_outline(surf, text, font, color, pos, alpha):
			outline_color = (0,0,0)
			for dx in [-1,0,1]:
				for dy in [-1,0,1]:
					if dx != 0 or dy != 0:
						outline = font.render(text, True, outline_color)
						outline.set_alpha(alpha)
						rect = outline.get_rect(center=(pos[0]+dx, pos[1]+dy))
						surf.blit(outline, rect)
			main = font.render(text, True, color)
			main.set_alpha(alpha)
			rect = main.get_rect(center=pos)
			surf.blit(main, rect)

		# Draw all previous fully-shown lines and the current partially-typed line
		total_lines = len(self.lines)
		# compute total height to vertically center the block
		total_h = total_lines * line_h + max(0, total_lines - 1) * spacing
		start_y = settings.HEIGHT // 2 - total_h // 2 + offset_y
		for i in range(total_lines):
			if i < self.current_line:
				text_to_show = self.lines[i]
			elif i == self.current_line and self.current_line < total_lines:
				text_to_show = self.lines[i][:self.chars_shown[i]]
			else:
				text_to_show = ""
			y = start_y + i * (line_h + spacing)
			if text_to_show:
				draw_text_with_outline(screen, text_to_show, self.font, self.color, (x_center, y + line_h // 2), self.alpha)
