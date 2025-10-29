Nhu — Nhiệm vụ

- Thiết kế và lập trình giao diện trong `core/ui_game.py`.
- Bao gồm: menu, thanh máu, điểm số, nút bấm và khung thông báo.
- Xây dựng phần nhập tên người chơi (`core/login.py`): bố cục, chọn font, hiệu ứng chuyển cảnh.
- Quản lý tài nguyên UI: `assets/fonts/` và `assets/images/ui/`.

Các file liên quan:
- `core/ui_game.py`
- `core/login.py`
- `assets/fonts/` (ví dụ `PressStart2P.ttf`)
- `assets/imagesbutton/`, `assets/imagessetting/`

Ghi chú:
- Đảm bảo UI tỉ lệ tốt trên các độ phân giải (centered, anchored button).
- Sử dụng font pixel-friendly, fallback an toàn khi đóng gói.
