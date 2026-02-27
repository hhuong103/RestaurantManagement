# 🍽️ Restaurant QR Code Management - README

## Tính Năng Mới: Mã QR Code Cho Đơn Hàng

Hệ thống quản lý nhà hàng giờ hỗ trợ **QR Code Management** - một tính năng hiện đại để:

✅ **Khách hàng**: Nhận mã QR sau khi đặt hàng online  
✅ **Nhân viên**: Quét mã QR để xem chi tiết order  
✅ **Admin**: Quản lý, in, và tải QR codes  

---

## ⚡ Cài Đặt Nhanh (3 Bước)

### 1️⃣ Cài Đặt Thư Viện QR
```bash
pip install qrcode[pil]==7.4.2
```

### 2️⃣ Tạo Thư Mục
```bash
mkdir -p static/qr_codes
```

### 3️⃣ Khởi Động Server
```bash
python app.py
```

**Xong!** ✨ Tính năng đã sẵn sàng.

---

## 🎯 Quy Trình Sử Dụng

### 👤 Khách Hàng

```
Đặt Hàng → Điền Thông Tin → Thanh Toán → ✨ Nhận Mã QR
                                            ↓
                                        In / Chụp
                                            ↓
                                      Đưa cho Nhân Viên
```

### 👨‍💼 Nhân Viên (Admin)

```
Khách đến → Nhận QR → Quét Mã → Xem Chi Tiết Order → Xử Lý
                       ↑
                  (hoặc input)
```

---

## 🚀 Các Trang Mới

| Trang | URL | Quyền | Mô Tả |
|-------|-----|-------|-------|
| **Order Success** | `/order_success` | Khách | Hiển thị mã QR |
| **Scan QR** | `/scan_qr` | Admin | Quét mã QR |
| **View QR** | `/admin/orders/qr_viewer` | Admin | Xem & in QR |

---

## 🔧 Cấu Trúc Tệp

```
RestaurantManagement/
├── app.py                          (✅ Updated)
├── requirements.txt                (✅ Updated)
├── model/
│   └── order_model.py             (✅ Updated)
├── controller/
│   └── order_controller.py        (✅ Updated)
├── templates/
│   ├── order_success.html         (✅ Updated)
│   ├── scan_qr.html              (✅ New)
│   └── view_order_qr.html        (✅ New)
├── static/
│   └── qr_codes/                 (✅ New folder)
├── CHANGES_SUMMARY.md             (ℹ️ Thay đổi)
├── QR_CODE_FEATURE.md             (ℹ️ Chi tiết tính năng)
├── INSTALLATION_QR.md             (ℹ️ Cài đặt & sửa lỗi)
└── GUIDE_QR_CODE.md               (ℹ️ Hướng dẫn đầy đủ)
```

---

## 📖 Tài Liệu

Có 4 tài liệu để tham khảo:

1. **📋 CHANGES_SUMMARY.md** - Tóm tắt các thay đổi
2. **📚 QR_CODE_FEATURE.md** - Mô tả chi tiết tính năng
3. **🔧 INSTALLATION_QR.md** - Hướng dẫn cài đặt & troubleshooting  
4. **📖 GUIDE_QR_CODE.md** - Hướng dẫn toàn diện (đầy đủ nhất)

👉 **Khuyên**: Bắt đầu với `GUIDE_QR_CODE.md`

---

## ✨ Tính Năng Chính

### 1. Tạo QR Code Tự Động
- Tạo ngay khi order được lưu
- Format: `ORDER#{id}#RESTAURANT`
- Lưu ảnh PNG trong `static/qr_codes/`

### 2. Hiển Thị QR Trên Success Page
- Khách hàng thấy mã QR
- Có thể chụp ảnh / in / lưu

### 3. Quét QR Code
- Admin dùng camera quét
- Hiển thị thông tin order chi tiết
- Support fallback: input thủ công

### 4. Quản Lý QR
- Xem QR code của bất kỳ order nào
- In hoặc tải file QR
- Xem thông tin đầy đủ order

---

## 🎯 Ví Dụ Thực Tế

### Khách Hàng

```
1. Vào trang chủ → thêm 2-3 món ăn vào giỏ
2. Vào /cart → chọn các món muốn order
3. Click "Checkout" → điền số điện thoại, địa chỉ, chọn bàn
4. Click "Place Order"
5. 📱 Được chuyển đến trang success với MÃ QR
6. Chụp ảnh hoặc in mã QR
7. Tới nhà hàng → đưa mã QR cho nhân viên
```

### Nhân Viên

```
1. Đăng nhập admin account
2. Vào Menu → "Quản Lý" → "Scan QR Code"
3. Cho phép truy cập camera
4. Quét mã QR của khách
5. 📋 Xem thông tin đầy đủ:
   - Tên khách, phone, address
   - Danh sách món ăn
   - Giá tiền từng món + tổng
   - Trạng thái thanh toán
   - Bàn dự trữ
6. Xử lý order của khách
```

---

## 🐛 Troubleshooting

### ❌ "ModuleNotFoundError: qrcode"
```bash
pip install qrcode[pil]==7.4.2
```

### ❌ Camera không hoạt động
- Sử dụng `localhost` thay vì IP
- Cho phép truy cập camera trong browser
- Dùng input thủ công

### ❌ QR Code không hiển thị
```bash
mkdir -p static/qr_codes
```

### ❌ Không tìm thấy order
- Kiểm tra mã QR có đúng không
- Xác nhận order đã lưu vào database

→ Xem chi tiết trong `INSTALLATION_QR.md`

---

## 📱 Hỗ Trợ Thiết Bị

| Thiết Bị | Quét QR | Xem QR | Ghi Chú |
|----------|---------|--------|---------|
| iPhone | ✅ | ✅ | Safari 14+ |
| Android | ✅ | ✅ | Chrome 90+ |
| Desktop | ✅ | ✅ | Webcam cần thiết |

---

## 🔒 Bảo Mật

✅ Chỉ admin được phép quét QR  
✅ Session-based authentication  
✅ QR code lưu trữ an toàn  
✅ Dữ liệu được mã hóa  

---

## 🚀 API Reference

```
Endpoint 1: POST /api/get_order_by_qr
  Input: {qr_code: "ORDER#123#RESTAURANT"}
  Output: {success: true, order: {...}}

Endpoint 2: GET /api/get_latest_order_qr
  Output: {success: true, order_id: 123, qr_image: "..."}

Endpoint 3: POST /api/complete_order/<id>
  Output: {success: true, message: "..."}

Endpoint 4: GET /api/get_order_details/<id>
  Output: {success: true, order: {...}}
```

---

## 📊 Database Schema

```sql
-- Thêm 2 cột mới vào bảng orders
ALTER TABLE orders ADD COLUMN qr_code TEXT;
ALTER TABLE orders ADD COLUMN qr_code_image TEXT;
```

*(Hệ thống sẽ tự động thêm các cột này)*

---

## 📝 Các Tệp Được Cập Nhật

### Backend
- ✅ `app.py` - Thêm 6 routes mới
- ✅ `model/order_model.py` - 3 hàm QR mới
- ✅ `controller/order_controller.py` - Cập nhật store_order
- ✅ `requirements.txt` - Thêm qrcode library

### Frontend
- ✅ `templates/order_success.html` - Hiển thị QR
- ✅ `templates/scan_qr.html` - **Trang mới** - Quét QR
- ✅ `templates/view_order_qr.html` - **Trang mới** - Xem QR

### Tài Liệu
- ✅ `CHANGES_SUMMARY.md` - Tóm tắt thay đổi
- ✅ `QR_CODE_FEATURE.md` - Chi tiết tính năng
- ✅ `INSTALLATION_QR.md` - Hướng dẫn cài đặt
- ✅ `GUIDE_QR_CODE.md` - Hướng dẫn toàn diện

---

## ✅ Checklist Cài Đặt

```
□ Pip install qrcode library
□ Tạo folder static/qr_codes
□ Khởi động server python app.py
□ Đặt một order thử (customer)
□ Kiểm tra QR trên order_success
□ Login admin → quét QR
□ Test view & in QR code
□ Kiểm tra database (qr_code columns)
```

---

## 🎓 Bắt Đầu

**Cho người mới**:
1. Đọc phần **"Cài Đặt Nhanh"** ở trên
2. Đọc **`GUIDE_QR_CODE.md`** để hiểu cách sử dụng
3. Test tính năng với order thực tế

**Cho developer**:
1. Xem **`CHANGES_SUMMARY.md`** để hiểu thay đổi
2. Xem **`QR_CODE_FEATURE.md`** cho chi tiết kỹ thuật
3. Customize nếu cần

---

## 📞 Hỗ Trợ

Gặp vấn đề?
1. Kiểm tra **`INSTALLATION_QR.md`** (phần Troubleshooting)
2. Kiểm tra logs: `python app.py` (console output)
3. Kiểm tra folder `static/qr_codes/` tồn tại

---

## 🎉 Kết Luận

Bạn giờ có một hệ thống quản lý order hoàn chỉnh với QR code!

```
Khách hàng → Đặt hàng → Nhận QR → Tới nhà hàng → Đưa QR
  ↓
Nhân viên → Quét QR → Xem chi tiết → Xử lý order ✅
```

---

**Version**: 1.0  
**Last Updated**: 2025-01-09  
**Status**: ✅ Sẵn sàng sử dụng

🚀 **Happy coding!** 🍽️
