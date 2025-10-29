import json
import os
import pygame
import sys
import settings

# Data file path relative to project root
DATA_DIR = 'data'
DATA_FILE = os.path.join(DATA_DIR, 'users.json')


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_users():
    _ensure_data_dir()
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def save_users(users):
    _ensure_data_dir()
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4, ensure_ascii=False)


def add_score(username, score):
    users = load_users()
    if username not in users:
        users[username] = {"score": 0}
    try:
        users[username]["score"] = int(users[username].get("score", 0)) + int(score)
    except Exception:
        users[username]["score"] = users[username].get("score", 0) + score
    # After updating, keep only the top 5 users by score in persistent storage.
    try:
        # Sort items by score (desc). Convert score to int for reliable comparison.
        sorted_items = sorted(users.items(), key=lambda x: int(x[1].get('score', 0)), reverse=True)
        top_items = sorted_items[:5]
        # Rebuild users dict containing only the top 5 entries
        users = {k: v for k, v in top_items}
    except Exception:
        # If sorting/trimming fails for any reason, fall back to saving all users.
        pass

    save_users(users)


def get_leaderboard():
    users = load_users()
    return sorted(users.items(), key=lambda x: x[1].get('score', 0), reverse=True)


def login_screen(screen, font, width=None, height=None):
    """Show a simple login screen using the provided `screen` and `font`.

    Returns the username string (trimmed). This function does not call pygame.init()
    and expects an existing display surface.
    """
    if width is None or height is None:
        try:
            width, height = screen.get_size()
        except Exception:
            width, height = 640, 480

    # Improved UI: centered panel with input box and Start button
    username = ""
    # debug: mark login_screen entry (only when global DEBUG is enabled)
    try:
        if getattr(settings, 'DEBUG', False):
            print("[DEBUG] login_screen entered", flush=True)
    except Exception:
        pass
    active = True
    clock = pygame.time.Clock()
    cursor_on = True
    cursor_timer = 0.0
    cursor_blink = 0.5
    btn_hover = False

    # Prepare fonts with a bit more hierarchy
    # Prefer project pixel font if available
    try:
        from core.boss import load_pixel_font as _load_pixel
    except Exception:
        _load_pixel = None
    # Helper: pick a Unicode-capable font from common system fonts (prefer Windows fonts)
    def _unicode_font(sz):
        # Common fonts that usually contain Vietnamese glyphs
        candidates = ['Segoe UI', 'Tahoma', 'Arial', 'DejaVu Sans', 'Noto Sans', 'Liberation Sans', 'Times New Roman']
        try:
            for name in candidates:
                path = pygame.font.match_font(name)
                if path:
                    try:
                        return pygame.font.Font(path, sz)
                    except Exception:
                        continue
        except Exception:
            pass
        # Fallback to default system font
        try:
            return pygame.font.SysFont(None, sz)
        except Exception:
            return font

    try:
        # Prefer Unicode-capable system font for UI text so Vietnamese diacritics render correctly.
        title_font = _unicode_font(22)
        input_font = _unicode_font(20)
        # Increase the small hint font slightly so the caption under the input is easier to read
        small_font = _unicode_font(14)
        # If a pixel font is intentionally provided by the project and desired for stylistic reasons,
        # keep it available as _load_pixel but don't use it for rendering Vietnamese text.
    except Exception:
        # ultimate fallback to provided font
        title_font = font
        input_font = font
        small_font = font

    # start button default size (will be positioned inside the loop after panel computed)
    start_btn_w, start_btn_h = 140, 44
    start_btn_rect = pygame.Rect(0, 0, start_btn_w, start_btn_h)

    while active:
        dt = clock.tick(60) / 1000.0
        cursor_timer += dt
        if cursor_timer >= cursor_blink:
            cursor_timer = 0.0
            cursor_on = not cursor_on

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN and username.strip():
                    return username.strip()
                elif e.key == pygame.K_BACKSPACE:
                    username = username[:-1]
                elif e.key == pygame.K_ESCAPE:
                    # allow cancel/back-out by returning None
                    return None
                else:
                    if len(username) < 24 and len(e.unicode) == 1 and e.unicode.isprintable():
                        username += e.unicode
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos
                if start_btn_rect.collidepoint(mx, my) and username.strip():
                    return username.strip()

        # Draw background dim
        # No background dim: the panel will cover the whole window so we don't draw a dark overlay
        try:
            if getattr(settings, 'DEBUG', False):
                print("[DEBUG] login_screen drawing frame", flush=True)
        except Exception:
            pass

        # Compute panel geometry (inset framed panel so edges look clean)
        parchment = (235, 212, 177)
        screen.fill(parchment)
        inset = max(12, min(width, height) // 40)
        panel_x = inset
        panel_y = inset
        panel_w = max(100, width - inset * 2)
        panel_h = max(100, height - inset * 2)
        panel_color = parchment
        border_color = (128, 60, 28)
        inner_shadow = (188, 120, 70)

        # Panel: prefer a themed image `assets/imageslogin/Login.png` when available
        panel_image = None
        try:
            from core import resources as resources
            panel_image = resources.load_image('assets/imageslogin/Login.png', size=(panel_w, panel_h))
        except Exception:
            try:
                p = os.path.join('assets', 'imageslogin', 'Login.png')
                if os.path.exists(p):
                    panel_image = pygame.image.load(p).convert_alpha()
                    try:
                        panel_image = pygame.transform.smoothscale(panel_image, (panel_w, panel_h))
                    except Exception:
                        panel_image = pygame.transform.scale(panel_image, (panel_w, panel_h))
            except Exception:
                panel_image = None

        if panel_image is not None:
            # draw the themed panel image
            try:
                screen.blit(panel_image, (panel_x, panel_y))
            except Exception:
                # fallback to simple panel if blit fails
                panel_image = None

        if panel_image is None:
            # fallback panel rendering using the warm beige/brown palette from the provided artwork
            panel_color = (235, 212, 177)  # light parchment beige
            border_color = (128, 60, 28)   # dark brown border
            inner_shadow = (188, 120, 70)
            pygame.draw.rect(screen, panel_color, (panel_x, panel_y, panel_w, panel_h), border_radius=12)
            pygame.draw.rect(screen, border_color, (panel_x, panel_y, panel_w, panel_h), 4, border_radius=12)
            # subtle inner shadow line to suggest depth
            try:
                pygame.draw.rect(screen, inner_shadow, (panel_x + 8, panel_y + 8, panel_w - 16, panel_h - 16), 2, border_radius=10)
            except Exception:
                pass

        # Title
        # Render title with pixelized effect: render small and scale up to get pixel style
        def _render_pixel_text(target_surf, text, base_font, base_size, scale, color, pos, align='center'):
            """
            Render text using a Unicode-capable base font then scale up to get a pixelated look.
            pos: a (x,y) tuple whose meaning depends on align:
              - 'center': pos is the center
              - 'midleft': pos is the midleft
              - 'topleft': pos is the top-left
            Returns the blitted rect or None.
            """
            try:
                # base_font may be a Font object already
                if isinstance(base_font, pygame.font.Font):
                    f = base_font
                else:
                    f = _unicode_font(base_size)
                surf = f.render(text, True, color)
                if scale and scale > 1:
                    w, h = surf.get_size()
                    surf = pygame.transform.scale(surf, (int(w * scale), int(h * scale)))
                if align == 'center':
                    rect = surf.get_rect(center=pos)
                elif align == 'midleft':
                    rect = surf.get_rect(midleft=pos)
                else:
                    rect = surf.get_rect(topleft=pos)
                target_surf.blit(surf, rect)
                return rect
            except Exception:
                try:
                    surf = base_font.render(text, True, color)
                    if align == 'center':
                        rect = surf.get_rect(center=pos)
                    elif align == 'midleft':
                        rect = surf.get_rect(midleft=pos)
                    else:
                        rect = surf.get_rect(topleft=pos)
                    target_surf.blit(surf, rect)
                    return rect
                except Exception:
                    return None

        # Draw big English title at the top (branding) then the Vietnamese title below it
        # so the large title sits above all other controls.
        try:
            big_font = _unicode_font(36)
        except Exception:
            big_font = title_font
        title_color = (109, 54, 28)
        # place the big title near the top inside the panel
        big_title_pos = (panel_x + panel_w // 2, panel_y + max(28, inset * 2))
        _render_pixel_text(screen, "HERO FANTASY", big_font, 28, 1.0, title_color, big_title_pos, align='center')

    # (Vietnamese title will be positioned closer to the input box below)

        # Input box (parchment style) - centered below the English title
        input_box_w = min(900, panel_w - 160)
        input_box_h = max(40, int(panel_h * 0.07))
        input_box_x = panel_x + (panel_w - input_box_w) // 2
        # Place the input box centered vertically in the panel (so it's visually central)
        # Titles remain at the top; this centers the input within the remaining space.
        input_box_y = panel_y + (panel_h // 2) - (input_box_h // 2)
        input_box_rect = pygame.Rect(input_box_x, input_box_y, input_box_w, input_box_h)

        # Render the Vietnamese title close above the input box
        try:
            # Move the Vietnamese title a bit higher above the input box
            # so it sits visibly above the input (increase gap).
            title_gap = max(20, inset + 8)
            title_center = (panel_x + panel_w // 2, input_box_y - title_gap)
            _render_pixel_text(screen, "Nhập tên người chơi", title_font, 18, 1, title_color, title_center, align='center')
        except Exception:
            pass

        input_fill = (244, 232, 203)  # pale parchment
        input_border = (115, 55, 28)  # brown border
        pygame.draw.rect(screen, input_fill, input_box_rect, border_radius=8)
        pygame.draw.rect(screen, input_border, input_box_rect, 3, border_radius=8)

        # Render username with ellipsis if too long
        display_name = username
        max_chars = 22
        if len(display_name) > max_chars:
            display_name = display_name[-max_chars:]
            display_name = '...' + display_name[3:]

        # Render input text with pixelized effect
        try:
            # render at smaller base size then scale 2x for pixel look
            # render input text using midleft so cursor aligns at the right of the text
            name_rect = _render_pixel_text(screen, display_name, input_font, 16, 1, (72, 36, 20), (input_box_x + 10, input_box_y + input_box_h // 2), align='midleft')
            if name_rect is None:
                # fallback: normal render
                name_surf = input_font.render(display_name, True, (12, 12, 12))
                name_rect = name_surf.get_rect(midleft=(input_box_x + 10, input_box_y + input_box_h // 2))
                screen.blit(name_surf, name_rect)
        except Exception:
            try:
                name_surf = input_font.render(display_name, True, (12, 12, 12))
                name_rect = name_surf.get_rect(midleft=(input_box_x + 10, input_box_y + input_box_h // 2))
                screen.blit(name_surf, name_rect)
            except Exception:
                name_rect = None

        # blinking cursor
        if cursor_on and (pygame.time.get_ticks() // 300) % 2 == 0 and name_rect is not None:
            cx = name_rect.right + 4
            cy1 = input_box_y + 10
            cy2 = input_box_y + input_box_h - 10
            pygame.draw.line(screen, (12, 12, 12), (cx, cy1), (cx, cy2), 2)

        # helper hint
        # Hint under input (styled brown, slightly larger and nudged down for readability)
        hint_y = input_box_y + input_box_h + max(18, inset)
        _render_pixel_text(screen, "Tên hiển thị (tối đa 24 ký tự)", small_font, 14, 1, (109, 54, 28), (panel_x + panel_w // 2, hint_y), align='center')

        # Start button (parchment + wooden button style)
        # Place the button at the bottom of the panel so it's always reachable
        # but inset a little from the panel edge.
        bottom_inset = max(12, inset * 2)
        start_btn_rect.midbottom = (panel_x + panel_w // 2, panel_y + panel_h - bottom_inset)
        mx, my = pygame.mouse.get_pos()
        btn_hover = start_btn_rect.collidepoint(mx, my)
        btn_base = (141, 78, 46)      # wooden brown
        btn_hover_col = (169, 96, 54) # lighter on hover
        btn_disabled = (200, 184, 165)
        if not username.strip():
            btn_color = btn_disabled
        else:
            btn_color = btn_hover_col if btn_hover else btn_base

        # Shadow (pixel-like) behind the button
        try:
            shadow_rect = start_btn_rect.move(4, 4)
            pygame.draw.rect(screen, (72, 36, 20), shadow_rect, border_radius=8)
        except Exception:
            pass

        pygame.draw.rect(screen, btn_color, start_btn_rect, border_radius=8)
        pygame.draw.rect(screen, (98, 48, 26), start_btn_rect, 3, border_radius=8)
        # Start button label rendered pixel-style (golden text)
        _render_pixel_text(screen, "Bắt đầu", title_font, 18, 1, (109, 54, 28), start_btn_rect.center, align='center')

        pygame.display.flip()

    return None


def leaderboard_screen(screen, font):
    leaderboard = get_leaderboard()
    running = True
    clock = pygame.time.Clock()
    width, height = screen.get_size()
    # Choose a Unicode-capable font for rendering leaderboard text (so Vietnamese displays correctly)
    def _unicode_font_local(sz):
        candidates = ['Segoe UI', 'Tahoma', 'Arial', 'DejaVu Sans', 'Noto Sans', 'Liberation Sans', 'Times New Roman']
        try:
            for name in candidates:
                path = pygame.font.match_font(name)
                if path:
                    try:
                        return pygame.font.Font(path, sz)
                    except Exception:
                        continue
        except Exception:
            pass
        try:
            return pygame.font.SysFont(None, sz)
        except Exception:
            return font

    title_font = _unicode_font_local(28)
    line_font = _unicode_font_local(16)
    hint_font = _unicode_font_local(14)

    # Local helper for pixel rendering similar to the login screen helper
    def _render_pixel_text_local(target_surf, text, base_font, base_size, scale, color, topleft):
        try:
            f = base_font if isinstance(base_font, pygame.font.Font) else _unicode_font_local(base_size)
            surf = f.render(text, True, color)
            if scale and scale > 1:
                w, h = surf.get_size()
                surf = pygame.transform.scale(surf, (w * scale, h * scale))
            rect = surf.get_rect(topleft=topleft)
            target_surf.blit(surf, rect)
            return rect
        except Exception:
            try:
                surf = font.render(text, True, color)
                rect = surf.get_rect(topleft=topleft)
                target_surf.blit(surf, rect)
                return rect
            except Exception:
                return None

    # Only show the top 5 scores. If fewer than 5 users exist, show them all.
    # Users ranked lower than 5th are not displayed.
    top_entries = leaderboard
    if len(top_entries) > 5:
        top_entries = top_entries[:5]

    while running:
        # Draw a parchment-style full-window panel (no black margins)
        screen.fill((235, 212, 177))  # fill with parchment color as base

        # Make the panel occupy the entire window (edge-to-edge)
        panel_x = 0
        panel_y = 0
        panel_w = width
        panel_h = height

        # Parchment palette (match image 2)
        panel_color = (235, 212, 177)  # light parchment beige
        border_color = (128, 60, 28)   # dark brown border
        inner_shadow = (188, 120, 70)

        # Draw main panel and border
        try:
            pygame.draw.rect(screen, panel_color, (panel_x, panel_y, panel_w, panel_h), border_radius=12)
            pygame.draw.rect(screen, border_color, (panel_x, panel_y, panel_w, panel_h), 4, border_radius=12)
            pygame.draw.rect(screen, inner_shadow, (panel_x + 8, panel_y + 8, panel_w - 16, panel_h - 16), 2, border_radius=10)
        except Exception:
            # fallback simple panel
            pygame.draw.rect(screen, panel_color, (panel_x, panel_y, panel_w, panel_h))

        # Text colors (brown tones matching panel art)
        title_color = (109, 54, 28)
        line_color = (72, 36, 20)
        hint_color = (109, 54, 28)

        # Centered title near top of panel
        try:
            title_surf = title_font.render("BẢNG XẾP HẠNG", True, title_color)
            title_rect = title_surf.get_rect(center=(panel_x + panel_w // 2, panel_y + 34))
            screen.blit(title_surf, title_rect)
        except Exception:
            _render_pixel_text_local(screen, "BẢNG XẾP HẠNG", title_font, 20, 1, title_color, (panel_x + 20, panel_y + 20))

        # Entries - distribute vertically to use the larger panel space
        start_y = panel_y + 110
        # compute a comfortable spacing that adapts to the panel height
        entries_count = max(1, len(top_entries))
        available_space = panel_h - 160
        line_spacing = max(36, available_space // (entries_count + 1))
        y = start_y
        for i, (user, data) in enumerate(top_entries):
            line_text = f"{i+1}. {user} - {data.get('score',0)}"
            try:
                # center lines horizontally within the panel
                line_surf = line_font.render(line_text, True, line_color)
                line_rect = line_surf.get_rect(center=(panel_x + panel_w // 2, y))
                screen.blit(line_surf, line_rect)
            except Exception:
                _render_pixel_text_local(screen, line_text, line_font, 12, 1, line_color, (panel_x + 40, y))
            y += line_spacing

        # Hint at bottom of panel
        try:
            hint_surf = hint_font.render("Nhấn ESC để quay lại", True, hint_color)
            hint_rect = hint_surf.get_rect(center=(panel_x + panel_w // 2, panel_y + panel_h - 28))
            screen.blit(hint_surf, hint_rect)
        except Exception:
            _render_pixel_text_local(screen, "Nhấn ESC để quay lại", hint_font, 12, 1, hint_color, (panel_x + 40, panel_y + panel_h - 44))

        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                running = False
        clock.tick(30)


def get_user_score(username):
    users = load_users()
    return users.get(username, {}).get('score', 0)
