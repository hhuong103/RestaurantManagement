# ----- Giai đoạn 1: Build môi trường -----
# Sử dụng một image đầy đủ để cài đặt các gói phụ thuộc
FROM python:3.10 as builder

# Đặt thư mục làm việc
WORKDIR /usr/src/app

# Cập nhật pip
RUN python -m pip install --upgrade pip

# Tạo một môi trường ảo riêng trong giai đoạn build
RUN python -m venv /opt/venv

# Kích hoạt môi trường ảo để các gói được cài vào đó
ENV PATH="/opt/venv/bin:$PATH"

# Sao chép file requirements và cài đặt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ----- Giai đoạn 2: Tạo image cuối cùng -----
# Sử dụng một image python "slim" nhẹ hơn nhiều
FROM python:3.10-slim

# Tạo một người dùng không phải root để chạy ứng dụng (tăng cường bảo mật)
RUN addgroup --system app && adduser --system --group app

# Đặt thư mục làm việc
WORKDIR /home/app

# Sao chép môi trường ảo đã được cài đặt từ giai đoạn "builder"
COPY --from=builder /opt/venv /opt/venv

# Sao chép toàn bộ mã nguồn ứng dụng
COPY . .

# Xử lý file database: Sao chép file SQLite vào image
# LƯU Ý: Dữ liệu sẽ bị mất nếu container bị xóa. Xem cách xử lý tốt hơn ở Bước 5.

# Cấp quyền sở hữu cho người dùng "app"
RUN chown -R app:app ./
USER app

# Kích hoạt môi trường ảo cho image cuối cùng
ENV PATH="/opt/venv/bin:$PATH"

# Mở cổng mà Gunicorn sẽ chạy
EXPOSE 8000

# Lệnh để khởi động ứng dụng
# THAY THẾ 'app.main:app' cho đúng với ứng dụng của bạn
# Cấu trúc là: TÊN_MODULE:TÊN_BIẾN_ỨNG_DỤNG
# Ví dụ: nếu file chính là app.py và biến là app = Flask(__name__), thì dùng 'app:app'
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]