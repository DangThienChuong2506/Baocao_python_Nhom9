# 🔒 Cơ chế chặn Player ở các Map

## Tổng quan
Game sử dụng cơ chế chặn player để bắt buộc người chơi phải hoàn thành tất cả wave quái trước khi có thể chuyển map.

## Biến điều khiển chính

### Map 0 & 1 (Background1):
```python
first_wave_cleared = False      # Đã giết 2 quái đầu chưa?
wave_lock_active = False        # Đang khóa map khi giao tranh
monster_wave = 1                # Wave hiện tại (1-5)
```

### Map 2 (Background2):
```python
bg2_wave_stage = 0              # Stage của wave bg2 (0-4)
bg2_wave_lock = False           # Khóa cuộn map ở bg2
_bg2_applied = False            # Đã áp dụng background2 chưa
```

---

## Cơ chế Map 0 (Background1)

### 📌 Điều kiện cuộn map:
```python
allow_scroll = (monster_wave > 1 or first_wave_cleared) and not wave_lock_active and monster_wave < 5
```

### 🔄 Timeline hoạt động:

#### **Wave 1: BẮT ĐẦU GAME**
- Spawn: 2 Goblins
- Trạng thái: `first_wave_cleared = False`, `wave_lock_active = False`
- **Background: ĐỨNG YÊN** ❌
- Player: Bị nhốt trong màn hình

#### **Wave 2: Giết xong Wave 1**
- Spawn: 3 Goblins
- Trạng thái: `first_wave_cleared = True`, `wave_lock_active = True`
- **Background: VẪN ĐỨNG YÊN** ❌
- Player: Vẫn bị nhốt

#### **Wave 3: Giết xong Wave 2**
- Spawn: 5 Goblins
- Trạng thái: `wave_lock_active = True`
- **Background: VẪN ĐỨNG YÊN** ❌

#### **Wave 4: Giết xong Wave 3**
- Spawn: Demon Boss
- Trạng thái: `wave_lock_active = True`
- **Background: VẪN ĐỨNG YÊN** ❌

#### **Wave 5: Giết xong Demon**
- Trạng thái: `wave_lock_active = False`, `monster_wave = 5`
- **Background: ĐƯỢC CUỘN** ✅
- Player: Có thể tiến đến cửa chuyển map

---

## Cơ chế Map 2 (Background2)

### 📌 Điều kiện cuộn map:
```python
allow_scroll = (bg2_wave_stage >= 4) and not bg2_wave_lock
```

### 🔄 Timeline hoạt động:

#### **Stage 0: Vừa vào Background2**
- Spawn: Wave 1 (3 Crows)
- Trạng thái: `bg2_wave_stage = 1`, `bg2_wave_lock = True`
- **Background: ĐỨNG YÊN** ❌
- Player: Bị nhốt, phải giết hết crows

#### **Stage 1: Giết xong Wave 1**
- Spawn: Wave 2 (4 Crows)
- Trạng thái: `bg2_wave_stage = 2`, `bg2_wave_lock = True`
- **Background: VẪN ĐỨNG YÊN** ❌

#### **Stage 2: Giết xong Wave 2**
- Spawn: Wave 3 (6 Crows)
- Trạng thái: `bg2_wave_stage = 3`, `bg2_wave_lock = True`
- **Background: VẪN ĐỨNG YÊN** ❌

#### **Stage 3: Giết xong Wave 3**
- Spawn: Wizard Boss
- Trạng thái: `bg2_wave_stage = 4`, `bg2_wave_lock = True`
- **Background: VẪN ĐỨNG YÊN** ❌

#### **Stage 4: Giết xong Wizard**
- Trạng thái: `bg2_wave_stage = 4`, `bg2_wave_lock = False`
- **Background: ĐƯỢC CUỘN** ✅
- Player: Tự do di chuyển

---

## Code quan trọng

### 1. Logic cuộn map (game.py, dòng ~744)
```python
direction = 0
if current_map < 2:
    # Map 0 và 1
    allow_scroll = (monster_wave > 1 or first_wave_cleared) and not wave_lock_active and monster_wave < 5
else:
    # Map 2
    allow_scroll = (bg2_wave_stage >= 4) and not bg2_wave_lock

if allow_scroll:
    if player.moving_left:
        direction = -1
    elif player.moving_right:
        direction = 1

bg_scroller.update(direction)  # direction = 0 → map đứng yên!
```

### 2. Xử lý khi Wizard chết (game.py, dòng ~814)
```python
if getattr(monster, 'is_dead', False) and not getattr(monster, '_counted', False):
    monster._counted = True
    
    # Kiểm tra nếu là Wizard boss ở map 2
    if getattr(monster, 'spawn_map', None) == 2 and isinstance(monster, Wizard):
        bg2_wave_lock = False  # MỞ KHÓA!
        print("[DEBUG] Wizard defeated! Unlocking bg2 map scrolling")
```

### 3. Spawn wave tự động (game.py, dòng ~851)
```python
if _bg2_applied:
    any_bg2_alive = any(
        getattr(m, 'spawn_map', None) == 2 
        and not getattr(m, 'is_dead', False) 
        for m in monster_group
    )
    
    if not any_bg2_alive:
        # Tất cả quái map 2 đã chết → spawn wave tiếp theo
        if bg2_wave_stage == 1:
            spawn_bg2_crows(positions_wave2)
            bg2_wave_stage = 2
            bg2_wave_lock = True  # Khóa tiếp!
```

---

## 🎯 Kết luận

| Map | Điều kiện mở khóa | Số Wave | Boss cuối |
|-----|------------------|---------|-----------|
| **Map 0** | Giết Demon Boss | 4 waves | Demon |
| **Map 2** | Giết Wizard Boss | 4 waves | Wizard |

**Nguyên tắc chung**: 
- ❌ Chưa giết hết wave → `direction = 0` → Background đứng yên
- ✅ Giết hết boss cuối → Mở khóa → Background cuộn được
- 🔒 Player bị "nhốt" trong màn hình cho đến khi hoàn thành nhiệm vụ

**Các cơ chế chặn song song:**
1. **Chặn cuộn background**: `direction = 0`
2. **Chặn đi sang trái**: `can_move_left = False` (ở map 0)
3. **Chặn đi qua rìa phải**: `player.rect.right = WIDTH` (clamp)
