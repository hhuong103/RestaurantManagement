# QR Code Feature - Restaurant Management System

## Mô Tả Tính Năng

Hệ thống đã được cập nhật với tính năng **Mã QR Code** để quản lý order tại nhà hàng. Tính năng này cho phép:

1. **Khách hàng**: Nhận mã QR sau khi đặt hàng online thành công
2. **Nhân viên**: Quét mã QR để xem thông tin chi tiết đơn hàng của khách

## Quy Trình Hoạt Động

### 1. Khách Hàng Đặt Hàng
- Khách hàng thêm món ăn vào giỏ hàng
- Điền thông tin (phone, address, bàn, phương thức thanh toán)
- Click "Place Order"
- **Kết quả**: Được chuyển đến trang thành công với mã QR

### 2. Trang Order Success
- Hiển thị mã QR code được tạo tự động
- Hiển thị Order ID
- Khách hàng có thể:
  - Chụp ảnh QR code
  - In QR code
  - Lưu QR code

### 3. Nhân Viên Quét QR
- Vào menu admin → "Scan QR Code"
- Sử dụng camera điện thoại để quét mã QR
- Hoặc nhập thủ công mã QR
- **Kết quả**: Hiển thị thông tin đầy đủ của order

## Cải Tiến Kỹ Thuật

### Database
- **Cột mới**: `qr_code`, `qr_code_image` trong bảng `orders`
- **QR Code Format**: `ORDER#{order_id}#RESTAURANT`

### Backend
- **Model**: `OrderModel`
  - `generate_qr_code(order_id)`: Tạo mã QR
  - `save_qr_code_to_order(order_id, qr_code_data, qr_filename)`: Lưu QR vào DB
  - `get_order_by_qr_code(qr_code_data)`: Lấy order từ QR code

### API Endpoints
```
GET  /scan_qr                 - Trang quét QR (admin)
POST /api/get_order_by_qr     - Lấy thông tin order từ QR
GET  /api/get_latest_order_qr - Lấy QR của order cuối
POST /api/complete_order/<id> - Hoàn thành order
```

### Frontend
- **Thư viện**: jsQR library
- **Camera**: Real-time QR scanning
- **Fallback**: Manual input nếu camera không khả dụng

## Hướng Dẫn Sử Dụng

### Cho Khách Hàng

1. Đặt hàng như bình thường
2. Sau khi order thành công, bạn sẽ thấy:
   - Mã QR code
   - Order ID
3. Lưu/in mã QR này
4. Khi đến nhà hàng, đưa mã QR cho nhân viên

### Cho Nhân Viên

1. Đăng nhập với tài khoản admin
2. Vào menu "Quản Lý" → "Scan QR Code"
3. Sử dụng camera để quét mã QR của khách
4. Xem thông tin đầy đủ:
   - Order ID
   - Tên khách hàng
   - Số điện thoại
   - Địa chỉ
   - Bàn dự trữ
   - Danh sách món ăn
   - Tổng tiền
   - Trạng thái thanh toán
5. Nếu cần, click "Mark as Completed"

## Cài Đặt & Triển Khai

### 1. Cài Đặt Thư Viện
```bash
pip install qrcode[pil]==7.4.2
```

### 2. Khởi Động Lại Server
```bash
python app.py
```

### 3. Database Migration
- Hệ thống sẽ tự động thêm các cột mới khi chạy lần đầu

## Tính Năng Chi Tiết

### Tạo QR Code
- **Tự động**: Tạo ngay khi order được lưu vào DB
- **Format**: PNG image
- **Lưu trữ**:
  - Hình ảnh: `static/qr_codes/order_{id}_qr.png`
  - Base64: Lưu trong DB
  - Text: Lưu mã QR text

### Quét QR Code
- **Camera**: HD quality real-time scanning
- **Xử lý**: Tự động nhận diện mã QR
- **Fallback**: Input thủ công nếu camera lỗi
- **Compatibility**: iOS, Android, Desktop

### Xem Order Details
Khi quét thành công, nhân viên sẽ thấy:
- ✓ Thông tin khách hàng
- ✓ Danh sách chi tiết món ăn
- ✓ Giá tiền từng món
- ✓ Tổng giá
- ✓ Bàn dự trữ
- ✓ Ghi chú (address, payment method, payment status)
- ✓ Thời gian đặt hàng

## Troubleshooting

### Camera Không Hoạt Động
- Kiểm tra quyền truy cập camera
- Sử dụng HTTPS (camera yêu cầu secure context)
- Dùng input thủ công

### QR Code Không Hiển Thị
- Kiểm tra folder `static/qr_codes/` tồn tại
- Kiểm tra database có cột `qr_code` và `qr_code_image`
- Tạo lại QR code bằng API

### Order Không Tìm Thấy
- Kiểm tra QR code đúng định dạng: `ORDER#{id}#RESTAURANT`
- Kiểm tra database có order đó không
- Thử input thủ công

## Bảo Mật

- ✓ Chỉ admin mới được phép quét QR
- ✓ QR code chứa order ID (có thể mã hóa thêm nếu cần)
- ✓ API protected bằng session
- ✓ Lưu trữ trong database an toàn

## Tương Lai

Các tính năng có thể phát triển thêm:
- Mã hóa QR code (encrypt QR data)
- SMS notification cho khách
- Multi-language support
- In QR trực tiếp từ hệ thống
- Export QR code ZIP
- Analytics tracking scans

---

**Phiên bản**: 1.0  
**Cập nhật**: 2025-01-09
