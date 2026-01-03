# Automation Tool (Playwright + Python + CustomTkinter)

Đây là cấu trúc dự án mẫu cho một công cụ automation sử dụng Playwright với giao diện người dùng (UI) được xây dựng bằng CustomTkinter.

## Cấu trúc dự án

```
automation-tool/
├── app/
│   ├── core/
│   │   ├── pages/          # Page Object Model (POM) classes
│   │   └── tests/          # Test scripts / logic automation
│   └── ui/                 # Các thành phần UI (nếu cần tách nhỏ)
├── config/                 # Cấu hình (settings, env vars)
├── logs/                   # Logs file
├── reports/                # Kết quả test (html report, screenshots)
├── utils/                  # Các hàm tiện ích (logger, helpers)
├── main.py                 # Entry point (chạy UI)
├── requirements.txt        # Các thư viện cần thiết
└── .env                    # Biến môi trường
```

## Cài đặt

1.  **Tạo môi trường ảo (khuyên dùng):**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

2.  **Cài đặt thư viện:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Cài đặt trình duyệt Playwright:**
    ```bash
    playwright install
    ```

## Cấu hình

Chỉnh sửa file `.env` để thay đổi các cấu hình cơ bản:
- `BASE_URL`: Trang web cần test.
- `HEADLESS`: Chạy ẩn (True) hoặc hiện trình duyệt (False).
- `BROWSER`: Loại trình duyệt (chromium, firefox, webkit).

## Chạy ứng dụng

Chạy file `main.py` để mở giao diện điều khiển:

```bash
python main.py
```

## Phát triển thêm

- **Thêm Page mới:** Tạo file mới trong `app/core/pages/` kế thừa từ `BasePage`.
- **Thêm Test case:** Tạo function hoặc class trong `app/core/tests/` sử dụng các Page Object.
- **Mở rộng UI:** Chỉnh sửa `main.py` hoặc thêm các module trong `app/ui/`.
