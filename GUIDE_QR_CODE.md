# QR Code Feature - Hướng Dẫn Toàn Diện

## 📱 Tính Năng Mới: Quản Lý Order Bằng Mã QR

Hệ thống quản lý nhà hàng của bạn giờ có thể tạo và quét mã QR code để quản lý order!

---

## 🚀 Cài Đặt Nhanh

### Yêu Cầu
- Python 3.7+
- pip (Python package manager)

### Bước 1: Cài Đặt Thư Viện
```bash
pip install qrcode[pil]==7.4.2
```

hoặc (nếu đã có requirements.txt):
```bash
pip install -r requirements.txt
```

### Bước 2: Tạo Thư Mục
```bash
mkdir -p static/qr_codes
```

### Bước 3: Khởi Động Lại
```bash
python app.py
```

✅ Xong! Tính năng đã sẵn sàng sử dụng.

---

## 👥 Hướng Dẫn Cho Khách Hàng

### Đặt Hàng Và Nhận QR Code

**Bước 1: Thêm Món Ăn Vào Giỏ**
1. Vào trang chủ
2. Chọn các món ăn thích hợp
3. Click "Add to Cart"

**Bước 2: Thanh Toán**
1. Vào giỏ hàng (`/cart`)
2. Chọn các món muốn đặt
3. Click "Checkout"

**Bước 3: Điền Thông Tin**
1. Điền số điện thoại
2. Điền địa chỉ (nếu giao hàng)
3. Chọn bàn dự trữ (nếu ăn tại chỗ)
4. Chọn phương thức thanh toán
5. Click "Place Order"

**Bước 4: Nhận QR Code**
- Bạn sẽ được chuyển đến trang thành công
- **Mã QR sẽ được hiển thị trên trang này**
- Có thể:
  - 📸 Chụp ảnh
  - 🖨️ In ra
  - 📱 Lưu trên điện thoại

### Sử Dụng QR Code Tại Nhà Hàng

1. **Khi đến nhà hàng**, đưa mã QR cho nhân viên
2. Nhân viên sẽ quét mã QR
3. Nhân viên sẽ thấy:
   - Thông tin chi tiết order của bạn
   - Danh sách món ăn
   - Giá tiền
   - Trạng thái thanh toán
4. Nhân viên sẽ xử lý order của bạn

**💡 Lưu ý**: Lưu lại mã QR cho đến khi thanh toán xong!

---

## 👨‍💼 Hướng Dẫn Cho Nhân Viên (Admin)

### Quét QR Code Của Khách

#### Cách 1: Sử Dụng Camera

**Bước 1: Vào Trang Quét QR**
1. Đăng nhập tài khoản admin
2. Vào Menu → "Quản Lý"
3. Click "Scan QR Code"
   (hoặc vào trực tiếp: `/scan_qr`)

**Bước 2: Quét Mã QR**
1. Cho phép truy cập camera khi được hỏi
2. Hướng camera vào mã QR của khách
3. Hệ thống sẽ tự động nhận diện
4. Thông tin order sẽ hiển thị ngay

#### Cách 2: Input Thủ Công

Nếu camera không hoạt động:
1. Yêu cầu khách cho biết mã QR
2. Copy mã QR vào ô "Or enter QR code data manually:"
3. Click "Search Order"
4. Thông tin order sẽ hiển thị

### Xem Thông Tin Order Chi Tiết

Khi quét thành công, bạn sẽ thấy:

| Thông Tin | Chi Tiết |
|-----------|----------|
| **Order ID** | Mã order duy nhất |
| **Tên khách** | Tên của khách hàng |
| **Số điện thoại** | Liên hệ khách |
| **Địa chỉ** | Địa chỉ giao hàng |
| **Bàn dự trữ** | Bàn mà khách đặt |
| **Danh sách món** | Tất cả thực đơn |
| **Giá từng món** | Chi tiết giá |
| **Tổng giá** | Tổng tiền cần thanh toán |
| **Trạng thái thanh toán** | Đã thanh toán / Chưa thanh toán |
| **Thời gian đặt** | Khi nào khách đặt |

### Xem & In QR Code Của Order

**Bước 1: Vào Trang Xem QR**
1. Menu → "Quản Lý"
2. Click "View QR Code"
   (hoặc vào: `/admin/orders/qr_viewer`)

**Bước 2: Tìm Order**
1. Nhập Order ID
2. Click "Search"

**Bước 3: Hành Động Với QR**
- 🖨️ **Print QR**: In mã QR
- ⬇️ **Download**: Tải file QR về
- 📋 **Xem chi tiết**: Thông tin order đầy đủ

---

## 📊 Admin Dashboard - QR Code Management

### Vị Trí Menu

```
Admin Menu
  ├── Scan QR Code (Quét mã QR của khách)
  ├── View QR Code (Xem & in QR)
  └── Orders Management
      ├── List Orders (Xem danh sách)
      └── Mỗi order có QR code
```

### Các Tính Năng

1. **Scan QR Code**
   - Quét camera hoặc input thủ công
   - Xem thông tin order
   - Dễ dàng tìm các thông tin chi tiết

2. **View QR Code**
   - Tìm order bằng Order ID
   - Xem hình ảnh QR code
   - In hoặc tải QR về

3. **Order List**
   - Xem tất cả order
   - Mỗi order có QR code
   - Quản lý status

---

## 🔧 Cấu Hình & Tùy Chỉnh

### Thay Đổi Định Dạng QR

Mở file: `model/order_model.py`

Tìm hàm `generate_qr_code()`:

```python
qr = qrcode.QRCode(
    version=1,                              # Tăng lên nếu cần QR lớn hơn
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,   # Kích thước pixel
    border=4,      # Kích thước viền
)
```

### Thay Đổi Thư Mục Lưu QR

```python
qr_folder = "static/qr_codes"  # Thay đổi đường dẫn
```

### Mã QR Format

Hiện tại mã QR chứa:
```
ORDER#{order_id}#RESTAURANT
```

Ví dụ: `ORDER#123#RESTAURANT`

---

## 🐛 Xử Lý Sự Cố

### ❌ Camera Không Hoạt Động

**Nguyên nhân**: Thiếu HTTPS, không cho phép truy cập

**Giải pháp**:
1. Dùng localhost thay vì IP
2. Cho phép truy cập camera trong browser
3. Sử dụng input thủ công

### ❌ Module qrcode Not Found

**Lỗi**: `ModuleNotFoundError: No module named 'qrcode'`

**Giải pháp**:
```bash
pip install qrcode[pil]==7.4.2
```

### ❌ QR Code Không Hiển Thị

**Nguyên nhân**: Folder không tồn tại hoặc không có quyền

**Giải pháp**:
```bash
mkdir -p static/qr_codes
chmod 755 static/qr_codes
```

### ❌ Không Tìm Thấy Order

**Nguyên nhân**: Mã QR sai, order không tồn tại

**Giải pháp**:
1. Kiểm tra mã QR có đúng không
2. Kiểm tra order đã được lưu vào database
3. Thử tìm kiếm theo Order ID

### ❌ QR Code Bị Mờ/Không Quét Được

**Giải pháp**:
1. Đảm bảo QR code in rõ ràng
2. Không xoay QR code
3. Hướng camera từ từ vào QR

---

## 📱 Hỗ Trợ Thiết Bị

| Thiết Bị | Hỗ Trợ |
|----------|--------|
| **Smartphone iOS** | ✅ Đầy đủ |
| **Smartphone Android** | ✅ Đầy đủ |
| **Desktop/Laptop** | ✅ Đầy đủ |
| **Tablet** | ✅ Đầy đủ |

### Trình Duyệt Hỗ Trợ

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**Yêu cầu**: Được phép truy cập camera

---

## 🔐 Bảo Mật

✅ **Tính Năng Bảo Mật**
- Chỉ admin mới được phép quét QR
- Session-based authentication
- QR code lưu trữ an toàn trong database

**Khuyến Nghị**:
- Thường xuyên cập nhật password
- Không chia sẻ tài khoản admin
- Sử dụng HTTPS trên production

---

## 📈 Thống Kê & Analytics

### Dữ Liệu QR Code Lưu Trữ

```
Database: orders table
Cột qr_code: Mã QR text (ORDER#123#RESTAURANT)
Cột qr_code_image: Hình ảnh QR (PNG base64)
```

### Có Thể Phát Triển

- 📊 Thống kê số lần quét
- 📈 Tracking orders
- 🔔 Notification cho khách
- 📧 Email QR code

---

## 📚 Tài Liệu Kỹ Thuật

Xem chi tiết tại:
- `QR_CODE_FEATURE.md` - Mô tả tính năng
- `INSTALLATION_QR.md` - Hướng dẫn cài đặt

---

## 🆘 Hỗ Trợ & Liên Hệ

Nếu gặp vấn đề:
1. Kiểm tra hướng dẫn troubleshooting trên
2. Xem logs: `python app.py` (console output)
3. Kiểm tra database có dữ liệu không

---

## 📋 Checklist Cài Đặt

- [ ] Cài đặt qrcode: `pip install qrcode[pil]`
- [ ] Tạo folder: `mkdir -p static/qr_codes`
- [ ] Khởi động server: `python app.py`
- [ ] Test đặt hàng: Đặt order 1 cái
- [ ] Test quét QR: Vào admin → Scan QR
- [ ] Test xem QR: Admin → View QR Code

---

## 🎉 Xong!

Bạn đã sẵn sàng sử dụng tính năng QR code!

**Bắt đầu**:
1. Đặt một order thử
2. Vào trang success xem QR
3. Login admin quét thử
4. Xem thông tin order

**Hãy tận dụng tính năng này để cải thiện trải nghiệm khách hàng!** 🚀

---

**Phiên bản**: 1.0  
**Cập nhật cuối**: 2025-01-09  
**Tác giả**: Restaurant Management System
