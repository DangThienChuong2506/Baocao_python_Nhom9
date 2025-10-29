Kiet — Nhiệm vụ

- Lập trình phần nhập tên người chơi trước khi vào game.
- Xây dựng và quản lý dữ liệu trong `data/users.json` để lưu tên, điểm và cấp độ.
- Thực hiện chức năng đọc–ghi file JSON, đảm bảo lưu và tải lại tiến trình chơi ổn định.

Các file liên quan:
- `core/login.py`
- `data/users.json`

Ghi chú:
- Khi đóng gói thành EXE, thay đổi đường dẫn lưu trữ nếu cần (ví dụ lưu vào `%APPDATA%` thay vì ghi đè trong thư mục cài đặt).
- Kiểm tra concurrency (nếu nhiều tiến trình ghi file cùng lúc) và xử lý lỗi IO.
