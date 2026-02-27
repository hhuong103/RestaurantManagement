## Hướng Dẫn Cài Đặt QR Code Feature

### Bước 1: Cập Nhật Dependencies

Chạy lệnh sau để cài đặt thư viện QR code:

```bash
pip install -r requirements.txt
```

hoặc cài đặt riêng:

```bash
pip install qrcode[pil]==7.4.2
```

### Bước 2: Tạo Thư Mục QR Code

Tạo thư mục để lưu trữ các file QR code:

```bash
mkdir -p static/qr_codes
```

### Bước 3: Khởi Động Ứng Dụng

```bash
python app.py
```

Hệ thống sẽ tự động:
- Thêm các cột mới `qr_code` và `qr_code_image` vào bảng `orders`
- Kích hoạt tính năng QR code

### Bước 4: Đăng Nhập Admin

1. Vào trang login
2. Đăng nhập bằng tài khoản admin
3. Vào menu "Quản Lý"
4. Tìm link "Scan QR Code" (hoặc vào trực tiếp `/scan_qr`)

### Kiểm Tra Cài Đặt

Để kiểm tra xem QR code feature đã hoạt động:

1. **Đặt một order mới** như khách hàng thông thường
2. **Kiểm tra trang order success** - bạn sẽ thấy mã QR
3. **Vào trang scan QR** (admin) và thử quét hoặc input thủ công

### Troubleshooting

#### Lỗi: ModuleNotFoundError: No module named 'qrcode'

**Giải pháp:**
```bash
pip install qrcode[pil]==7.4.2
```

#### Lỗi: Permission denied cho folder qr_codes

**Giải pháp:**
```bash
chmod -R 755 static/qr_codes
```

hoặc tạo folder trong Windows:
- Mở File Explorer
- Vào thư mục `static`
- Tạo folder mới tên `qr_codes`

#### Camera không hoạt động

- Đảm bảo sử dụng HTTPS hoặc localhost
- Cho phép truy cập camera trong trình duyệt
- Thử sử dụng input thủ công

#### QR Code không hiển thị trên trang success

- Kiểm tra console (F12) có error không
- Kiểm tra file `static/qr_codes/` có file QR không
- Restart server: `python app.py`

### Cấu Hình Optional

#### Thay Đổi Kích Thước QR Code

Mở file `model/order_model.py`, tìm hàm `generate_qr_code()`:

```python
# Thay đổi các tham số:
qr = qrcode.QRCode(
    version=1,      # 1-40, version cao hơn = QR lớn hơn
    error_correction=qrcode.constants.ERROR_CORRECT_L,  # L/M/Q/H
    box_size=10,    # Kích thước pixel mỗi ô
    border=4,       # Kích thước border
)
```

#### Thay Đổi Thư Mục Lưu QR

Mở file `model/order_model.py`, tìm dòng:

```python
qr_folder = "static/qr_codes"  # Thay đổi đường dẫn
```

### Bảo Mật

- Chỉ admin mới được phép quét QR
- QR code format: `ORDER#{order_id}#RESTAURANT`
- Có thể mã hóa thêm nếu cần (xem phần security docs)

### Tài Liệu Thêm

Xem file `QR_CODE_FEATURE.md` để hiểu chi tiết về tính năng.

---

**Liên hệ support nếu gặp vấn đề!**
