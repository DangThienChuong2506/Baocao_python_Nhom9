Chuong — Nhiệm vụ

- Tập trung code chính trong `main.py`.
- Điều khiển logic trò chơi và xử lý sự kiện.
- Phụ trách `core/game.py` để quản lý trạng thái, chuyển map, xử lý thua/thắng.
- Cấu hình thông số game trong `settings.py` (WIDTH, HEIGHT, FPS, phím điều khiển, tốc độ).
- Tổng hợp, kiểm thử toàn bộ code và đóng gói sản phẩm (.exe).

Các file liên quan:
- `main.py`
- `core/game.py`
- `settings.py`
- tài nguyên: `assets/maps/` và `core/resources.py`

Ghi chú:
- Đảm bảo game loop, xử lý input và chuyển trạng thái hoạt động ổn định.
- Chuẩn bị script build (pyinstaller) và hướng dẫn đóng gói trong README nếu cần.
