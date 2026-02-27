# 🚀 Quick Start - QR Code Feature

## ⏱️ 5 Phút Để Chạy Tính Năng

### 📋 Bước 1: Cài Đặt (1 phút)

```bash
pip install qrcode[pil]==7.4.2
mkdir -p static/qr_codes
```

### 🚀 Bước 2: Chạy Server (30 giây)

```bash
python app.py
```

Bạn sẽ thấy:
```
 * Running on http://127.0.0.1:5000
```

### 👥 Bước 3: Test Khách Hàng (2 phút)

**3a. Đặt một order:**

1. Mở browser: `http://localhost:5000`
2. Đăng nhập (hoặc register account mới)
3. Thêm 2-3 món ăn vào cart
4. Click "Checkout"
5. Điền:
   - Phone: 0912345678
   - Address: Quận 1, TP.HCM
   - Table: Table 1
   - Payment: Pay at Restaurant
6. Click "Place Order"

**3b. Xem mã QR:**

- Bạn sẽ thấy trang "Order Success"
- 📱 **Mã QR sẽ hiển thị ở giữa trang**
- Lưu lại mã QR này

### 👨‍💼 Bước 4: Test Nhân Viên (1.5 phút)

**4a. Đăng nhập Admin:**

1. Đăng xuất (corner menu)
2. Đăng nhập bằng tài khoản **admin**
   - Username: admin
   - Password: (password của admin)

**4b. Vào trang quét QR:**

1. Menu → "Quản Lý"
2. Tìm link "Scan QR Code" 
   (hoặc vào: `http://localhost:5000/scan_qr`)

**4c. Thử quét:**

Cách 1 - Dùng camera:
- Cho phép truy cập camera
- Quét mã QR (có thể dùng điện thoại khác để hiển thị)

Cách 2 - Input thủ công:
- Scroll xuống "Or enter QR code data manually:"
- Copy từ trang success: `ORDER#{order_id}#RESTAURANT`
  Ví dụ: `ORDER#1#RESTAURANT`
- Paste vào input
- Click "Search Order"

**4d. Xem kết quả:**

✅ Bạn sẽ thấy:
- Order ID
- Tên khách hàng
- Số điện thoại
- Địa chỉ
- Danh sách món ăn
- Giá tiền
- Trạng thái thanh toán
- ...và nhiều thông tin khác

---

## 🎯 Test URLs

| Tính Năng | URL |
|-----------|-----|
| Order Success (QR hiển thị) | http://localhost:5000/order_success |
| Scan QR (Quét mã) | http://localhost:5000/scan_qr |
| View QR (Xem & in) | http://localhost:5000/admin/orders/qr_viewer |

---

## 🔄 Test QR Code Viewer (Optional)

Để xem & in mã QR:

1. Vào: `http://localhost:5000/admin/orders/qr_viewer`
2. Nhập Order ID (ví dụ: 1)
3. Click "Search"
4. Bạn sẽ thấy:
   - Hình ảnh QR code
   - Thông tin order chi tiết
   - Nút Print (🖨️) - In QR
   - Nút Download (⬇️) - Tải QR

---

## ✅ Checklist Test

- [ ] Cài đặt qrcode library
- [ ] Tạo folder static/qr_codes
- [ ] Server chạy (python app.py)
- [ ] Đăng nhập customer
- [ ] Đặt hàng & xem QR
- [ ] Đăng nhập admin
- [ ] Vào /scan_qr
- [ ] Quét/input QR code
- [ ] Xem order details hiển thị
- [ ] Vào /admin/orders/qr_viewer
- [ ] Tìm & xem QR code

---

## 🐛 Nếu Gặp Lỗi

### ❌ Camera không hoạt động
```
→ Sử dụng input thủ công (ô "Or enter QR code data manually:")
→ Copy: ORDER#123#RESTAURANT (thay 123 = order id của bạn)
```

### ❌ QR Code không hiển thị
```bash
→ Kiểm tra folder tồn tại: 
  - Windows: Kiểm tra folder C:\...\static\qr_codes
  - Linux/Mac: ls -la static/qr_codes
```

### ❌ Lỗi "Module qrcode not found"
```bash
→ pip install qrcode[pil]==7.4.2
→ python app.py
```

### ❌ Không tìm thấy order
```
→ Kiểm tra Order ID chính xác
→ Kiểm tra mã QR format: ORDER#123#RESTAURANT
→ Thử tìm bằng admin order list
```

---

## 💡 Tips

1. **Để test quét QR camera**:
   - Dùng 2 thiết bị: 1 hiển thị QR, 1 quét
   - Hoặc sử dụng "Or enter QR code data manually:"

2. **Mã QR format**:
   - `ORDER#{order_id}#RESTAURANT`
   - Ví dụ: `ORDER#1#RESTAURANT`, `ORDER#25#RESTAURANT`

3. **Tìm Order ID**:
   - Admin → Orders Management
   - Hoặc xem trong order success page
   - Hoặc check database

4. **Test Order Details**:
   - Vào `/admin/orders/qr_viewer`
   - Nhập Order ID
   - Click Search
   - Xem thông tin chi tiết + in QR

---

## 🎓 Tiếp Theo

Sau khi test thành công:

1. Xem `GUIDE_QR_CODE.md` để hiểu chi tiết
2. Xem `QR_CODE_FEATURE.md` cho kỹ thuật
3. Customize nếu cần (kích thước QR, folder, etc.)
4. Deploy lên production

---

## ⏱️ Timeline

```
0:00 - 0:30  Cài đặt libraries
0:30 - 1:00  Tạo folder & start server
1:00 - 3:00  Test customer (đặt hàng)
3:00 - 4:00  Test admin (quét QR)
4:00 - 4:30  Test view QR
4:30 - 5:00  Buffer / troubleshoot
```

---

## 🎉 Success!

Nếu bạn thấy:
✅ Mã QR trên order success page  
✅ Quét/input QR → hiển thị order details  
✅ In & tải QR code thành công  

**→ Tính năng QR Code đã hoạt động hoàn hảo!** 🚀

---

## 📞 Cần Giúp?

- Kiểm tra `INSTALLATION_QR.md` (Troubleshooting)
- Kiểm tra logs: `python app.py` (console)
- Kiểm tra database: admin → orders

---

**Thời gian**: ~5 phút ⏰  
**Độ khó**: ⭐⭐ (Dễ)  
**Success Rate**: 99% ✅
