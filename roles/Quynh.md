Quynh — Nhiệm vụ

- Phụ trách `core/sound.py` để quản lý âm thanh nền, hiệu ứng chiến đấu, thắng/thua.
- Quản lý tài nguyên âm thanh trong `assets/sounds/`.
- Chỉnh sửa và tối ưu dung lượng file âm thanh (convert/trim nếu cần).
- Tạo danh sách nhạc nền và hiệu ứng phù hợp cho từng map.

Các file liên quan:
- `core/sound.py`
- `assets/sounds/` (sound map, sound player, boss, win/lose)

Ghi chú:
- Sử dụng định dạng file nhẹ (ogg nếu cần) để giảm kích thước, kiểm tra loop mượt.
- Đảm bảo volume control và mute toggle trong UI.
