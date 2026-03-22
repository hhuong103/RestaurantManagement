import base64
from functools import wraps
import socket
import token
import os
import tempfile

from dotenv import load_dotenv

# ✅ Load .env bằng đường dẫn tuyệt đối, trước khi import ai_helper
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"), override=True)

from flask import Flask, render_template, request, session, redirect, url_for, abort, jsonify, flash, Response
from controller.menu_controller import MenuController
from controller.auth_controller import AuthController
from controller.user_controller import UserController
from controller.order_controller import OrderController

# ✅ Import AI helper SAU khi dotenv đã load
from ai_helper import analyze_food_image
from chatbot_ai import chat_with_ai, get_greeting_message

from reportlab.lib.pagesizes import letter

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os
import json
import re
import inspect
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL")  # ví dụ: http://192.168.1.10:5000

app = Flask(__name__)
app.secret_key = "CHANGE_THIS_SECRET_IN_PRODUCTION"
auth_controller = AuthController()
user_controller = UserController()
order_controller = OrderController()
menu_controller = MenuController()

def resolve_public_base_url():
    """
    Ưu tiên PUBLIC_BASE_URL (IP LAN hoặc domain).
    Nếu user đang mở bằng 127.0.0.1/localhost thì tự suy ra IP LAN để điện thoại truy cập được.
    """
    env = os.getenv("PUBLIC_BASE_URL")
    if env:
        return env.rstrip("/")

    host = request.host.split(":")[0]
    port = request.host.split(":")[1] if ":" in request.host else "5000"

    if host in ("127.0.0.1", "localhost"):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))  # chỉ để lấy IP LAN
            lan_ip = s.getsockname()[0]
        except Exception:
            lan_ip = host
        finally:
            s.close()
        return f"http://{lan_ip}:{port}"

    return request.host_url.rstrip("/")


import io

# ===== QR helpers (SVG/PNG) =====
try:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_M
    from qrcode.image.svg import SvgImage
except Exception:
    qrcode = None
    ERROR_CORRECT_M = None
    SvgImage = None


def _build_order_target_url(qr_token: str) -> str:
    """
    URL mà QR sẽ encode (điện thoại scan mở được).
    """
    base_url = resolve_public_base_url()
    return f"{base_url}/q/o/{qr_token}"


def build_qr_svg(data: str, extra_border: int = 2):
    """
    Tạo QR SVG (vector) với một chút lề trắng bổ sung.

    `extra_border` tính theo số modules trắng thêm vào mỗi cạnh, tương tự
    với tham số `border` của qrcode.QRCode.  Mặc định thêm 2 modules giúp
    browser scale hoặc đặt bên trong container không cắt mất các finder
    pattern.
    """
    if qrcode is None or SvgImage is None or ERROR_CORRECT_M is None:
        return None

    # border giá trị lớn hơn bình thường để giữ an toàn
    base_border = 4
    border = base_border + extra_border

    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=10,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(image_factory=SvgImage)
    try:
        svg_bytes = img.to_string()
    except Exception:
        return None

    svg_str = svg_bytes.decode("utf-8") if isinstance(svg_bytes, bytes) else str(svg_bytes)

    # ensure shape-rendering for crisp edges (we may call again later but
    # doing it here guarantees waveform if other callers use this helper)
    s = svg_str.lstrip()
    if s.startswith("<svg"):
        svg_str = svg_str.replace("<svg", '<svg shape-rendering="crispEdges"', 1)

    return svg_str


def build_qr_png_bytes(data: str, box_size: int = 12, border: int = 4, extra_border: int = 2):
    """
    Tạo QR PNG bytes (phục vụ route render .png).

    Các tham số giống với qrcode.QRCode, thêm `extra_border` giúp mở rộng
    thêm một vài module trắng trên mỗi cạnh. Điều này tạo ra một lớp
    an toàn để browser khi scale/resize không vô tình cắt chân "finder"
    patterns hoặc gạch ngoài.

    Giá trị mặc định `extra_border=2` đủ rộng để đảm bảo ảnh nhỏ hơn
    chiều rộng của container (340/280px) vẫn còn margin trắng dư.
    """
    if qrcode is None or ERROR_CORRECT_M is None:
        return None

    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # thêm padding bổ sung (theo modules) để tránh bị crop khi browser scale
    try:
        from PIL import Image
    except ImportError:
        Image = None

    if Image is not None and extra_border > 0:
        try:
            # convert PIL image if necessary
            if not isinstance(img, Image.Image):
                img = img.convert("RGB")
            margin_px = box_size * extra_border
            w, h = img.size
            canvas = Image.new(img.mode, (w + margin_px * 2, h + margin_px * 2), "white")
            canvas.paste(img, (margin_px, margin_px))
            img = canvas
        except Exception:
            # nếu chuyện gì đó sai thì dùng ảnh gốc
            pass

    bio = io.BytesIO()
    try:
        img.save(bio, format="PNG", optimize=True)
    except Exception:
        # fallback in case PIL object incompatible
        qr2 = qrcode.QRCode(
            version=None,
            error_correction=ERROR_CORRECT_M,
            box_size=box_size,
            border=border + extra_border,
        )
        qr2.add_data(data)
        qr2.make(fit=True)
        png2 = qr2.make_image(fill_color="black", back_color="white")
        png2.save(bio, format="PNG", optimize=True)
    return bio.getvalue()


def normalize_text(v):
    if v is None:
        return None
    if isinstance(v, (bytes, bytearray)):
        return v.decode("utf-8", errors="ignore")
    return str(v)


def normalize_qr_base64(v):
    """
    Chuẩn hóa qr_code_image để:
    - Nếu DB lưu bytes/BLOB -> convert base64 string
    - Nếu đã là 'data:image/png;base64,...' -> bỏ prefix, giữ phần base64
    - Nếu là string base64 -> giữ nguyên
    """
    if v is None:
        return None

    if isinstance(v, (bytes, bytearray)):
        return base64.b64encode(v).decode("utf-8")

    if isinstance(v, str):
        s = v.strip()
        # bỏ prefix data-url nếu có
        m = re.search(r'base64,(.*)$', s, re.DOTALL)
        if m:
            s = m.group(1).strip()
        return s

    # fallback an toàn
    return str(v)


@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%dT%H:%M'):
    if value is None:
        return ''
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except:
            return value
    else:
        dt = value
    return dt.strftime(format)

@app.context_processor
def inject_user():
    # Expose common template variables site-wide
    cart = session.get('cart', {})
    try:
        cart_count = sum(int(v.get('quantity', 0)) for v in cart.values())
    except Exception:
        cart_count = 0
    return {
        'username': session.get('username'),
        'role': session.get('role'),
        'cart_count': cart_count
    }

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Trang chủ
@app.route("/")
def show_menu():
    controller = MenuController()
    return controller.request_menu()

# Quản lý menu (Admin)
@app.route("/admin/menu/list")
@admin_required
def show_menu_list():
    controller = MenuController()
    return controller.list_menu()

@app.route("/admin/menu/create")
@admin_required
def create_menu():
    controller = MenuController()
    return controller.create_menu()

@app.route("/admin/menu/store", methods=['POST'])
@admin_required
def store_menu():
    controller = MenuController()
    return controller.store_menu()

@app.route("/menu/edit/<int:item_id>", methods=["GET", "POST"])
@admin_required
def edit_menu(item_id):
    controller = MenuController()
    return controller.edit_menu(item_id)


@app.route("/menu/delete/<int:item_id>", methods=['GET'])
@admin_required
def delete_menu(item_id):
    controller = MenuController()
    return controller.delete_menu(item_id)

# Auth
@app.route("/register", methods=["GET", "POST"])
def register():
    return auth_controller.register()

@app.route("/login", methods=["GET", "POST"])
def login():
    return auth_controller.login()

@app.route("/logout")
def logout():
    return auth_controller.logout()

@app.route("/home")
def home():
    return auth_controller.home()

# Giỏ hàng
@app.route("/cart/add/<int:item_id>", methods=["POST"])
def add_to_cart(item_id):
    quantity = request.form.get("quantity", 1, type=int)
    cart = session.get("cart", {})

    if str(item_id) in cart:
        cart[str(item_id)]["quantity"] += quantity
    else:
        menu_item = menu_controller.model.get_menu_item_by_id(item_id)
        if not menu_item:
            return "Item not found", 404
        cart[str(item_id)] = {
            "name": menu_item["name"],
            "price": menu_item["price"],
            "image": menu_item.get("image", None),
            "quantity": quantity
        }
    session["cart"] = cart
    return redirect(url_for("view_cart"))

@app.route("/cart", methods=["GET"])
def view_cart():
    cart = session.get("cart", {})
    total_price = sum(item["price"] * item["quantity"] for item in cart.values())
    return render_template("cart.html", cart=cart, total_price=total_price)

@app.route("/cart/remove/<int:item_id>", methods=["POST"])
def remove_from_cart(item_id):
    cart = session.get("cart", {})
    if str(item_id) in cart:
        del cart[str(item_id)]
    session["cart"] = cart
    return redirect(url_for("view_cart"))

@app.route("/cart/update/<int:item_id>", methods=["POST"])
def update_cart_item(item_id):
    action = request.form.get("action")
    cart = session.get("cart", {})
    if str(item_id) in cart:
        if action == "increment":
            cart[str(item_id)]["quantity"] += 1
        elif action == "decrement" and cart[str(item_id)]["quantity"] > 1:
            cart[str(item_id)]["quantity"] -= 1
        session["cart"] = cart
    return redirect(url_for("view_cart"))

# Xử lý đặt hàng
@app.route("/process_order", methods=["POST"])
def process_order():
    if "username" not in session:
        return redirect(url_for("login"))

    cart = session.get("cart", {})
    if not cart:
        flash("Cart is empty. Please add items first.", "error")
        return redirect(url_for("view_cart"))

    selected_items_json = request.form.get("selected_items_json", "[]")
    try:
        selected_items = json.loads(selected_items_json)
    except json.JSONDecodeError:
        flash("Invalid items data.", "error")
        return redirect(url_for("view_cart"))

    if not selected_items:
        flash("Please select at least one item to place an order.", "error")
        return redirect(url_for("view_cart"))

    total_quantity = 0
    subtotal = 0.0
    items_details = []
    item_descriptions = []

    for item_id in selected_items:
        key = str(item_id)
        if key in cart:
            item = cart[key]
            qty = int(item["quantity"])
            price = float(item["price"])
            total_quantity += qty
            subtotal += price * qty

            items_details.append({
                "name": item["name"],
                "quantity": qty,
                "price": price
            })
            item_descriptions.append(f"{item['name']} (x{qty})")

    items_text = ", ".join(item_descriptions)
    items_json = json.dumps(items_details, ensure_ascii=False)

    session["pending_order"] = {
        "customer_name": session.get("username"),
        "items_text": items_text,       # ✅ text đẹp (không còn [])
        "items_json": items_json,       # ✅ JSON để invoice/scan hiển thị đúng
        "items_details": items_details, # ✅ giữ list dict
        "quantity": int(total_quantity),
        "subtotal": float(subtotal),
        "service_fees": 0.0,
        "price": float(subtotal),
        "selected_items": selected_items
    }

    return redirect(url_for("order_information"))


@app.route("/order_information", methods=["GET", "POST"])
def order_information():
    if "pending_order" not in session:
        flash("No order to process. Please place an order first.", "error")
        return redirect(url_for("view_cart"))

    available_tables = order_controller.model.get_available_tables()

    if request.method == "POST":
        customer_name_form = request.form.get("customer_name")
        email = request.form.get("email")
        phone_number = request.form.get("phone_number")
        address = request.form.get("address")
        payment_method = request.form.get("payment_method")
        table_reservation = request.form.get("table_reservation")
        services = request.form.getlist("services")
        special_requests = request.form.get("special_requests")

        if not all([customer_name_form, email, phone_number, address, payment_method, table_reservation]):
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("order_information"))

        if payment_method not in ["Pay at Restaurant", "Bank Payment"]:
            flash("Invalid payment method selected.", "error")
            return redirect(url_for("order_information"))

        if table_reservation != "No Reservation":
            table_status = order_controller.model.get_available_tables()
            table_names = [t["name"] for t in table_status]
            if table_reservation not in table_names:
                flash("Selected table is no longer available. Please choose another.", "error")
                return redirect(url_for("order_information"))

        pending_order = session.get("pending_order", {})
        customer_name = pending_order.get("customer_name") or customer_name_form

        items_text = (pending_order.get("items_text") or "").strip()
        items_json = pending_order.get("items_json")
        items_details = pending_order.get("items_details", [])
        if not items_json and items_details:
            items_json = json.dumps(items_details, ensure_ascii=False)

        total_quantity = int(pending_order.get("quantity", 0))
        subtotal = float(pending_order.get("subtotal", 0))
        selected_items = pending_order.get("selected_items", [])

        # ✅ service fees
        service_prices = {
            "Home Delivery": 50000,
            "Express Service": 30000,
            "Special Packaging": 20000,
            "Chef's Special Request": 40000
        }
        service_fees = 0
        service_descriptions = []
        for s in services:
            if s in service_prices:
                service_fees += service_prices[s]
                service_descriptions.append(f"{s} (+{service_prices[s]:,.0f} VND)")

        total_price_with_services = float(subtotal) + float(service_fees)

        payment_status = "Paid" if payment_method == "Bank Payment" else "Unpaid"
        services_text = ", ".join(service_descriptions) if service_descriptions else "None"
        special_requests_text = f", Special Requests: {special_requests}" if special_requests else ""

        note = (
            f"Name: {customer_name}, Email: {email}, Phone: {phone_number}, Address: {address}, "
            f"Payment Method: {payment_method}, Payment Status: {payment_status}, "
            f"Table: {table_reservation}, Services: {services_text}{special_requests_text}, "
            f"Items: {items_text}"
        )

        # ✅ Nếu model hỗ trợ items_json/subtotal/service_fee -> lưu đẹp + invoice chuẩn
        supports_items_json = func_supports(order_controller.model.create_order, "items_json")

        create_kwargs = {
            "customer_name": customer_name,
            # items: nếu model có items_json => items lưu TEXT đẹp; nếu không => items lưu JSON như cũ
            "items": items_text if supports_items_json else (items_json or "[]"),
            "items_json": items_json,
            "quantity": total_quantity,
            "subtotal": subtotal,
            "service_fee": service_fees,
            "price": total_price_with_services,
            "status": "Pending",
            "note": note,
            "customer_phone": phone_number,
            "customer_address": address,
            "table_reservation": table_reservation
        }

        order_id = call_with_supported_kwargs(order_controller.model.create_order, create_kwargs)

        if not order_id:
            flash("Failed to place order. Selected table may be reserved.", "error")
            return redirect(url_for("order_information"))

        # ✅ Generate QR đúng 1 lần + dùng public base url để điện thoại scan mở được
        base_url = resolve_public_base_url()
        token, qr_filename, qr_image_base64 = order_controller.model.generate_qr_code(order_id, base_url=base_url)

        if token:
            call_with_supported_kwargs(
                order_controller.model.save_qr_code_to_order,
                {"order_id": order_id, "token": token, "qr_filename": qr_filename, "qr_image_base64": qr_image_base64}
            )

        session["last_order_id"] = order_id

        # Remove ordered items from cart
        cart = session.get("cart", {})
        for item_id in selected_items:
            cart.pop(str(item_id), None)
        session["cart"] = cart

        session.pop("pending_order", None)
        flash("Order placed successfully!", "success")
        return redirect(url_for("order_success"))

    pending_order = session.get("pending_order")
    return render_template("order_infor.html", order=pending_order, available_tables=available_tables)


@app.route('/order_success')
def order_success():
    # Triệt để: nếu chưa login thì redirect luôn, tránh trang trắng + API fail
    if "username" not in session:
        return redirect(url_for("login"))

    try:
        order_id = session.get("last_order_id")

        if not order_id:
            customer_name = session.get("username")
            orders = order_controller.model.get_orders_by_customer(customer_name)
            if orders:
                order_id = orders[-1]["id"]

        if not order_id:
            flash("No order found.", "error")
            return redirect(url_for("show_menu"))

        order = order_controller.model.get_order_by_id(order_id)
        if not order:
            flash("Order not found.", "error")
            return redirect(url_for("show_menu"))

        order_dict = dict(order)

        qr_token = normalize_text(order_dict.get("qr_code"))
        qr_image = order_dict.get("qr_code_image")
        qr_filename = order_dict.get("qr_filename")

        # Nếu thiếu QR hoặc thiếu ảnh -> generate lại và lưu
        if not qr_token or not qr_image:
            base_url = resolve_public_base_url()
            token_, qr_filename_, qr_image_base64 = order_controller.model.generate_qr_code(order_id, base_url=base_url)

            if token_:
                call_with_supported_kwargs(
                    order_controller.model.save_qr_code_to_order,
                    {"order_id": order_id, "token": token_, "qr_filename": qr_filename_, "qr_image_base64": qr_image_base64}
                )
                qr_token = token_
                qr_filename = qr_filename_
                qr_image = qr_image_base64

        # Chuẩn hóa base64 để template dùng ổn định
        qr_image = normalize_qr_base64(qr_image)

        # Khi có token thì luôn trình bày bằng đường dẫn động để
        # tránh dùng ảnh cũ (stored base64) bị mất góc. Url_for
        # tạo liên kết tới các route mới được tối ưu margin.
        qr_svg_url = url_for("render_order_qr_svg", token=qr_token) if qr_token else None
        qr_png_url = url_for("render_order_qr_png", token=qr_token) if qr_token else None
        if qr_svg_url or qr_png_url:
            qr_image = None  # loại bỏ ảnh lưu cũ, dùng đường dẫn ưu tiên

        return render_template(
            "order_success.html",
            initial_order_id=order_id,
            initial_qr_token=qr_token,
            initial_qr_svg_url=qr_svg_url,
            initial_qr_png_url=qr_png_url,
            initial_qr_image=qr_image,
            initial_qr_filename=qr_filename
        )

    except Exception as e:
        app.logger.exception("order_success failed")
        flash(f"Cannot load order success page: {str(e)}", "error")
        return redirect(url_for("show_menu"))
    
def call_with_supported_kwargs(func, kwargs: dict):
    """Gọi func(**kwargs) nhưng chỉ giữ các tham số mà func thật sự hỗ trợ."""
    sig = inspect.signature(func)
    filtered = {k: v for k, v in kwargs.items() if k in sig.parameters}
    return func(**filtered)

def func_supports(func, name: str) -> bool:
    try:
        return name in inspect.signature(func).parameters
    except Exception:
        return False


@app.route('/admin/orders/update_note/<int:order_id>', methods=['POST'])
@admin_required
def update_order_note(order_id):
    data = request.get_json()
    new_status = data.get('note', '')

    if new_status not in ['Paid', 'Unpaid', '']:
        return jsonify({'success': False, 'message': 'Invalid payment status'}), 400

    current_order = order_controller.model.get_order_by_id(order_id)
    if not current_order:
        return jsonify({'success': False, 'message': 'Order not found'}), 404

    note = current_order['note'] if current_order['note'] else ''
    note_parts = note.split(", ") if note else ["Phone: N/A", "Address: N/A", "Payment Method: N/A"]
    if len(note_parts) > 3:
        note_parts = note_parts[:3]
    note_parts.append(f"Payment Status: {new_status if new_status else 'Unpaid'}")
    updated_note = ", ".join(note_parts)

    if order_controller.model.update_order(order_id, note=updated_note):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Failed to update note', 'old_note': current_order['note']}), 500

# Quản lý đơn hàng (Admin)
@app.route('/admin/orders', methods=['GET'])
@admin_required
def list_orders():
    orders = order_controller.model.get_all_orders()
    return render_template("orders.html", orders=orders)

@app.route("/admin/orders/create", methods=["GET"])
@admin_required
def create_order_form():
    return order_controller.create_order_form()

@app.route("/admin/orders/edit/<int:order_id>", methods=["GET"])
@admin_required
def edit_order_form(order_id):
    return order_controller.edit_order_form(order_id)

@app.route("/admin/orders/update/<int:order_id>", methods=["POST"])
@admin_required
def update_order(order_id):
    return order_controller.update_order(order_id)

@app.route("/admin/orders/store", methods=["POST"])
@admin_required
def store_order():
    return order_controller.store_order()

@app.route("/admin/orders/delete/<int:order_id>", methods=["GET"])
@admin_required
def delete_order(order_id):
    return order_controller.delete_order(order_id)

# Quản lý bàn (Admin)
@app.route("/admin/tables", methods=["GET"])
@admin_required
def manage_tables():
    return order_controller.manage_tables()

@app.route("/admin/tables/create", methods=["GET", "POST"])
@admin_required
def create_table():
    if request.method == "POST":
        return order_controller.create_table()
    return render_template("create_table.html")

@app.route("/admin/tables/edit/<int:table_id>", methods=["GET", "POST"])
@admin_required
def edit_table(table_id):
    if request.method == "POST":
        return order_controller.update_table(table_id)
    return order_controller.edit_table(table_id)

@app.route("/admin/tables/delete/<int:table_id>", methods=["GET"])
@admin_required
def delete_table(table_id):
    return order_controller.delete_table(table_id)

@app.route("/transaction_history", methods=["GET"])
def transaction_history():
    return order_controller.transaction_history()

@app.route("/cancel_order/<int:order_id>", methods=["POST"])
def cancel_order(order_id):
    return order_controller.cancel_order(order_id)

@app.route("/approve_order/<int:order_id>", methods=["POST"])
@admin_required
def approve_order(order_id):
    return order_controller.approve_order(order_id)

@app.template_filter('format_price')
def format_price(value):
    return f"{value:,.0f} VND"

@app.route("/suggestions", methods=["GET"])
def get_suggestions():
    menu_items = menu_controller.model.get_all_menu_items()
    suggestions = [item["name"] for item in menu_items]
    suggestions.extend([
        "Cà phê", "Trà", "Nước ép", "Món chay", "Giao hàng nhanh",
        "Cà phê chất lượng cao", "Ưu đãi 50%", "Dưới 50.000 VND",
        "Cà phê sáng", "Đồ uống giải nhiệt"
    ])
    return jsonify(suggestions)

# Tạo và tải hóa đơn
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet

@app.route("/admin/orders/invoice/<int:order_id>")
@admin_required
def generate_invoice(order_id):
    order = order_controller.model.get_order_by_id(order_id)
    if not order or order["status"] != "Completed":
        flash("Order not found or not completed.", "error")
        return redirect(url_for("list_orders"))

    now = datetime.now()
    date_str = now.strftime("%d/%m/%Y %H:%M:%S")
    time_out = now.strftime("%H:%M")

    if "created_at" in order and isinstance(order["created_at"], datetime):
        time_in = order["created_at"].strftime("%H:%M")
    else:
        time_in = now.strftime("%H:%M")
        print("Warning: 'created_at' field not found in order. Using current time as fallback.")

    filename = f"invoice_{order_id}.pdf"
    filepath = os.path.join("static", filename)
    
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter

    font_name = "Times-Roman"
    try:
        pdfmetrics.registerFont(TTFont('TimesNewRoman', 'static/fonts/TimesNewRoman.ttf'))
        font_name = "TimesNewRoman"
    except Exception as e:
        print(f"Failed to register font: {e}")
        font_name = "Times-Roman"

    c.setFont(font_name, 16)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(width / 2, height - 50, "VEGETARIAN RESTAURANT")

    c.setFont(font_name, 10)
    c.drawCentredString(width / 2, height - 70, "123 Z15, Thai Nguyen city, Thai Nguyen")
    c.drawCentredString(width / 2, height - 90, "Phone: 0865.787.333")

    c.setFont(font_name, 14)
    c.drawCentredString(width / 2, height - 120, "INVOICE")

    c.setFont(font_name, 10)
    c.drawString(50, height - 150, f"Date: {date_str}")
    c.drawString(50, height - 170, f"Invoice No: {order['id']}")
    c.drawString(50, height - 190, f"Arrival Time: {time_in}")
    c.drawString(50, height - 210, f"Departure Time: {time_out}")
    c.drawString(50, height - 230, f"Table: {order['table_reservation'] or 'No Reservation'}")

    customer_name = order['customer_name']
    c.drawString(width - 200, height - 150, f"Customer: {customer_name}")

    c.setFont(font_name, 10)
    table_left = 50
    table_right = width - 50
    column_positions = {
        "item": table_left + 10,
        "unit_price": table_left + 300,
        "quantity": table_left + 400,
        "total": table_left + 500
    }

    table_top = height - 290
    c.drawString(column_positions["item"], table_top - 15, "Item")
    c.drawString(column_positions["unit_price"], table_top - 15, "Unit Price")
    c.drawString(column_positions["quantity"], table_top - 15, "Quantity")
    c.drawString(column_positions["total"], table_top - 15, "Total")

    y_position = table_top - 30
    total_quantity = 0
    items = order.get('items_json') or order['items']
    styles = getSampleStyleSheet()
    style = styles["Normal"]
    style.fontName = font_name
    style.fontSize = 10

    try:
        items_list = json.loads(items) if isinstance(items, str) and items.strip().startswith("[") else items
        for i, item in enumerate(items_list, 1):
            if isinstance(item, dict):
                name = item.get('name', 'Unknown')
                qty = item.get('quantity', 1)
                price = item.get('price', 0)
                total_price = qty * price
                total_quantity += qty

                item_width = column_positions["unit_price"] - column_positions["item"] - 10
                p = Paragraph(name, style)
                w, h = p.wrap(item_width, 100)
                p.drawOn(c, column_positions["item"], y_position - h - 5)

                c.drawString(column_positions["unit_price"], y_position - 15, f"{price:,.0f} VND")
                c.drawString(column_positions["quantity"], y_position - 15, str(qty))
                c.drawString(column_positions["total"], y_position - 15, f"{total_price:,.0f} VND")

                y_position -= max(20, h + 5)
    except Exception:
        item_width = column_positions["unit_price"] - column_positions["item"] - 10
        p = Paragraph(items, style)
        w, h = p.wrap(item_width, 100)
        p.drawOn(c, column_positions["item"], y_position - h - 5)

        c.drawString(column_positions["unit_price"], y_position - 15, f"{order['price'] / order['quantity']:,.0f} VND")
        c.drawString(column_positions["quantity"], y_position - 15, str(order['quantity']))
        c.drawString(column_positions["total"], y_position - 15, f"{order['price']:,.0f} VND")
        total_quantity = order['quantity']
        y_position -= max(20, h + 5)

    c.drawString(column_positions["item"], y_position - 15, "Subtotal")
    c.drawString(column_positions["quantity"], y_position - 15, str(total_quantity))
    c.drawString(column_positions["total"], y_position - 15, f"{order['price']:,.0f} VND")
    y_position -= 20

    y_position -= 30
    c.setFont(font_name, 12)
    c.drawString(350, y_position, f"Total Amount: {order['price']:,.0f} VND")

    y_position -= 30
    c.setFont(font_name, 10)
    c.drawCentredString(width / 2, y_position, "Thank you – See you again")

    c.save()

    return redirect(url_for("static", filename=filename))

@app.route("/search")
def search():
    controller = MenuController()
    return controller.search()

@app.route('/api/menu_suggestions')
def menu_suggestions():
    """API để lấy gợi ý tên món ăn"""
    controller = MenuController()
    items = controller.model.get_all_menu_items()
    suggestions = [item['name'] for item in items]
    return jsonify(suggestions)

@app.route('/api/analyze_food_image', methods=['POST'])
def analyze_food_image_api():
    """API để phân tích hình ảnh món ăn và tự động tạo tên + mô tả"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image file provided'}), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Validate file extension
        allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
        file_ext = image_file.filename.rsplit('.', 1)[-1].lower()
        if file_ext not in allowed_extensions:
            return jsonify({'success': False, 'error': 'Invalid image format'}), 400
        
        # Save image temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as tmp_file:
            image_file.save(tmp_file.name)
            temp_path = tmp_file.name
        
        try:
            # Analyze image with AI (include original filename so fallback can guess correctly)
            result = analyze_food_image(temp_path, original_filename=image_file.filename)
            
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return jsonify(result)
        except Exception as e:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({'success': False, 'error': str(e)}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

@app.route('/category/<category>')
def category(category):
    template_name = f'category_{category}.html'
    return render_template(template_name, category=category)

@app.route('/about_us')
def about_us():
    return render_template('about_us.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/admin/users', methods=['GET'])
@admin_required
def user_list():
    return user_controller.list_users()

@app.route('/users/create', methods=['GET'])
def create_user_form():
    return user_controller.create_user_form()

@app.route('/users/create', methods=['POST'])
def store_user():
    return user_controller.store_user()

@app.route("/users/edit/<int:user_id>", methods=["GET"])
def edit_user_form(user_id):
    return user_controller.edit_user_form(user_id)

@app.route('/users/delete/<int:user_id>', methods=['GET'])
@admin_required
def delete_user(user_id):
    return user_controller.delete_user(user_id)

@app.route('/users/update/<int:user_id>', methods=['POST'])
@admin_required
def update_user(user_id):
    return user_controller.update_user(user_id)

@app.route("/admin/dashboard")
@admin_required
def dashboard():
    from datetime import datetime
    current_month = datetime.now().strftime('%m')
    current_year = datetime.now().strftime('%Y')

    total_revenue = order_controller.model.get_monthly_revenue(current_month, current_year)
    monthly_revenue_data = order_controller.model.get_revenue_per_month(year=current_year)
    customer_counts = order_controller.model.get_customer_counts_per_month(year=current_year)
    daily_revenue_data = order_controller.model.get_revenue_per_day(month=current_month, year=current_year)

    orders = order_controller.model.get_all_orders()
    user_count = len(user_controller.model.get_all_users())
    order_count = len(orders)

    return render_template(
        "dashboard.html",
        username=session.get("username", "Admin"),
        total_revenue=total_revenue,
        user_count=user_count,
        order_count=order_count,
        orders=orders,
        monthly_revenue_data=monthly_revenue_data,
        customer_counts=customer_counts,
        daily_revenue_data=daily_revenue_data,
        selected_month=current_month,
        selected_year=current_year
    )

from model.menu_model import MenuModel

# ... existing code ...

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%dT%H:%M'):
    """
    Parse datetime string/object từ SQLite rồi format ra chuỗi mong muốn.
    Mặc định trả về format phù hợp input datetime-local: YYYY-MM-DDTHH:MM
    """
    if value is None or value == '':
        return ''

    # Nếu là datetime object
    if isinstance(value, datetime):
        return value.strftime(format)

    # Nếu là string
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return ''
        # SQLite có thể lưu 'YYYY-MM-DD HH:MM:SS' hoặc có .microseconds
        try:
            dt = datetime.fromisoformat(s.replace('Z', '+00:00'))
            return dt.strftime(format)
        except Exception:
            # fallback phổ biến
            for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
                try:
                    dt = datetime.strptime(s, fmt)
                    return dt.strftime(format)
                except Exception:
                    pass
            # Nếu không parse được thì trả nguyên văn
            return s

    return str(value)

# Chatbot route (legacy)
@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")

# ===== AI-POWERED ORDERING CHATBOT =====
@app.route("/ai-chat")
def ai_chat():
    """Render the AI ordering chatbot page."""
    return render_template("ai_chat.html")


@app.route("/api/ai-chat/send", methods=["POST"])
def ai_chat_send():
    """Process a message through the AI ordering agent."""
    try:
        user_message = (request.json or {}).get("message", "").strip()

        # Initialize conversation history if needed
        if "ai_chat_history" not in session:
            session["ai_chat_history"] = []

        # Handle init request → return greeting
        if user_message == "__INIT__":
            session["ai_chat_history"] = []
            greeting = get_greeting_message(session.get("username"))
            session["ai_chat_history"] = [
                {"role": "model", "parts": [greeting["message"]]}
            ]
            session.modified = True
            cart = session.get("cart", {})
            cart_count = sum(int(v.get("quantity", 0)) for v in cart.values())
            greeting["cart_count"] = cart_count
            return jsonify(greeting)

        if not user_message:
            return jsonify({"message": "Please type a message.", "action": None, "suggestions": []})

        # Fetch current data
        menu_items = menu_controller.model.get_menu() or []
        available_tables = order_controller.model.get_available_tables() or []
        cart = session.get("cart", {})
        username = session.get("username")

        # Add user message to history
        history = session.get("ai_chat_history", [])
        history.append({"role": "user", "parts": [user_message]})

        # Call AI
        ai_response = chat_with_ai(
            conversation_history=history,
            user_message=user_message,
            menu_items=menu_items,
            tables=available_tables,
            cart=cart,
            username=username
        )

        # Execute action if present
        action = ai_response.get("action")
        action_data = ai_response.get("action_data") or {}

        if action == "add_to_cart":
            item_id = action_data.get("item_id")
            qty = int(action_data.get("quantity", 1))
            if item_id:
                menu_item = menu_controller.model.get_menu_item_by_id(int(item_id))
                if menu_item:
                    key = str(item_id)
                    if key in cart:
                        cart[key]["quantity"] = int(cart[key].get("quantity", 0)) + qty
                    else:
                        cart[key] = {
                            "name": menu_item["name"],
                            "price": menu_item["price"],
                            "image": menu_item.get("image"),
                            "quantity": qty
                        }
                    session["cart"] = cart

        elif action == "remove_from_cart":
            item_id = action_data.get("item_id")
            if item_id:
                cart.pop(str(item_id), None)
                session["cart"] = cart

        elif action == "clear_cart":
            session["cart"] = {}
            cart = {}

        elif action == "place_order":
            if cart:
                ai_response["redirect"] = url_for("view_cart")
            else:
                ai_response["message"] += "<br><br>⚠️ Your cart is empty. Add some items first!"
                ai_response["action"] = None

        # Store model response in history
        history.append({"role": "model", "parts": [ai_response.get("message", "")]})

        # Keep history manageable
        if len(history) > 60:
            history = history[-60:]
        session["ai_chat_history"] = history
        session.modified = True

        # Add cart count to response
        cart = session.get("cart", {})
        ai_response["cart_count"] = sum(int(v.get("quantity", 0)) for v in cart.values())

        return jsonify(ai_response)

    except Exception as e:
        app.logger.exception("ai_chat_send failed")
        return jsonify({
            "message": "Sorry, something went wrong on the server. Please try again! 🙏",
            "action": None,
            "action_data": None,
            "suggestions": ["🍽️ View menu", "🛒 Show cart", "🔄 Try again"],
            "items_to_show": None,
            "cart_count": sum(int(v.get("quantity", 0)) for v in session.get("cart", {}).values())
        }), 200


@app.route("/api/ai-chat/reset", methods=["POST"])
def ai_chat_reset():
    """Reset the AI chat conversation."""
    session.pop("ai_chat_history", None)
    return jsonify({"success": True})


@app.route("/api/ai-chat/add-to-cart", methods=["POST"])
def ai_chat_add_to_cart():
    """Direct add-to-cart from product card buttons — no AI roundtrip needed."""
    try:
        data = request.json or {}
        item_id = data.get("item_id")
        qty = int(data.get("quantity", 1))

        if not item_id:
            return jsonify({"success": False, "message": "Missing item_id"})

        menu_item = menu_controller.model.get_menu_item_by_id(int(item_id))
        if not menu_item:
            return jsonify({"success": False, "message": "Item not found"})

        cart = session.get("cart", {})
        key = str(item_id)
        if key in cart:
            cart[key]["quantity"] = int(cart[key].get("quantity", 0)) + qty
        else:
            cart[key] = {
                "name": menu_item["name"],
                "price": menu_item["price"],
                "image": menu_item.get("image"),
                "quantity": qty
            }
        session["cart"] = cart
        session.modified = True

        cart_count = sum(int(v.get("quantity", 0)) for v in cart.values())
        cart_total = sum(float(v.get("price", 0)) * int(v.get("quantity", 0)) for v in cart.values())

        return jsonify({
            "success": True,
            "message": f"Added {qty}x {menu_item['name']} to cart!",
            "cart_count": cart_count,
            "cart_total": cart_total,
            "cart": {k: v for k, v in cart.items()}
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/api/ai-chat/cart-summary", methods=["GET"])
def ai_chat_cart_summary():
    """Get current cart summary for the AI chat interface."""
    cart = session.get("cart", {})
    items = []
    total = 0
    for k, v in cart.items():
        qty = int(v.get("quantity", 0))
        price = float(v.get("price", 0))
        items.append({
            "id": k,
            "name": v.get("name"),
            "price": price,
            "quantity": qty,
            "image": v.get("image"),
            "subtotal": price * qty
        })
        total += price * qty

    return jsonify({
        "success": True,
        "items": items,
        "total": total,
        "count": sum(int(v.get("quantity", 0)) for v in cart.values())
    })

@app.route("/chatbot/send", methods=["POST"])
def chatbot_send():
    user_message = request.json.get("message", "").strip()
    # normalize when passing to handler
    response_text = handle_chatbot_message(user_message.lower())

    # If a numbered menu was emitted previously, expose quick-reply buttons
    buttons = []
    last_menu = session.get('chat_last_menu') or {}
    if last_menu:
        # load menu items for labels
        menu_model = MenuModel()
        menu_items = {it['id']: it for it in (menu_model.get_menu() or [])}
        # preserve numeric order
        for key in sorted(last_menu.keys(), key=lambda x: int(x)):
            item_id = last_menu.get(key)
            it = menu_items.get(item_id)
            if it:
                buttons.append({"label": f"{key}. {it['name']}", "value": key})

    cart_count = sum(int(v.get('quantity', 0)) for v in session.get('cart', {}).values())
    return jsonify({"response": response_text, "buttons": buttons, "cart_count": cart_count})

def handle_chatbot_message(message):
    """Xử lý tin nhắn từ chatbot.

    Chức năng mở rộng:
    - Trả lời các câu hỏi thông tin (địa chỉ, giờ mở cửa, thanh toán...)
    - Gợi ý món theo đánh giá / từ khóa
    - Thêm món vào `session['cart']` khi người dùng yêu cầu đặt/mua
    - Hiển thị tóm tắt giỏ hàng
    """
    # basic restaurant info
    restaurant_info = {
        "name": "Nhà Hàng ABC",
        "address": "123 Đường ABC, Quận 1, TP.HCM",
        "phone": "0123-456-789",
        "hours": "7:00 - 22:00 hàng ngày",
        "payment": ["Tiền mặt", "Chuyển khoản", "Ví điện tử (MoMo, ZaloPay)"],
        "parking": "Có chỗ đậu xe miễn phí",
        "events": "Hiện tại không có chương trình khuyến mãi đặc biệt."
    }

    text = (message or "").strip().lower()

    # quick helpers
    def summarize_cart():
        cart = session.get("cart", {})
        if not cart:
            return "Giỏ hàng của bạn đang trống. Bạn có muốn thêm món không?"
        lines = []
        total = 0
        count = 0
        for k, v in cart.items():
            qty = int(v.get("quantity", 1))
            price = float(v.get("price", 0))
            lines.append(f"{v.get('name')} x{qty} — {price:,.0f} VND")
            total += price * qty
            count += qty
        lines.append(f"Tổng {count} món — {total:,.0f} VND. <a href=\"{url_for('view_cart')}\">Xem giỏ hàng</a>")
        return "<br>".join(lines)

    # load menu
    menu_model = MenuModel()
    menu_items = menu_model.get_menu() or []

    # If user replies with numbers and we previously stored a menu mapping
    nums = re.findall(r"\d+", text)
    last_menu = session.get('chat_last_menu')
    if nums and last_menu:
        added = []
        cart = session.get('cart', {})
        for n in nums:
            key = str(n)
            if key in last_menu:
                item_id = last_menu[key]
                # find item in menu_items
                item = next((it for it in menu_items if it['id'] == item_id), None)
                if not item:
                    continue
                dict_key = str(item_id)
                if dict_key in cart:
                    cart[dict_key]['quantity'] = int(cart[dict_key].get('quantity', 0)) + 1
                else:
                    cart[dict_key] = {'name': item['name'], 'price': item['price'], 'image': item.get('image'), 'quantity': 1}
                added.append(item['name'])
        session['cart'] = cart
        if not added:
            return "Tôi không tìm thấy số tương ứng trong danh sách trước đó. Vui lòng yêu cầu 'Gợi ý' để tôi gửi lại menu có đánh số."
        # clear the menu mapping so it doesn't persist indefinitely
        session.pop('chat_last_menu', None)
        return f"Đã thêm vào giỏ: {', '.join(added)}. Bạn có muốn thêm nữa không? (Gõ số hoặc 'Xem giỏ hàng')"

    # any non-numeric or unrelated query should clear previous mapping
    session.pop('chat_last_menu', None)

    # helper: find item by fuzzy substring match; return (id, item)
    def find_menu_item_by_text(q):
        q = q.strip().lower()
        if not q:
            return None
        # exact name match first
        for it in menu_items:
            if it['name'].strip().lower() == q:
                return (it['id'], it)
        # contains match
        best = None
        for it in menu_items:
            name = it['name'].strip().lower()
            if q in name:
                # prefer longer q match
                return (it['id'], it)
            # split words match
            words = q.split()
            if all(w in name for w in words):
                return (it['id'], it)
        # last resort: fuzzy by token overlap
        for it in menu_items:
            name = it['name'].strip().lower()
            for w in q.split():
                if w and w in name:
                    best = (it['id'], it)
                    break
            if best:
                return best
        return None

    # Intent: view cart
    if any(p in text for p in ["xem giỏ", "giỏ hàng", "xem giỏ hàng", "cart"]):
        return summarize_cart()

    # Intent: add/order item (patterns like 'đặt 2 phở bò', 'thêm phở bò', 'mua phở')
    if any(p in text for p in ["đặt", "mua", "thêm", "order", "cho tôi 1", "cho tôi"]):
        # try to extract quantity
        qty = 1
        m = re.search(r"(\d+)\s*(?:x|cái|suất|phần)?", text)
        if m:
            try:
                qty = max(1, int(m.group(1)))
            except Exception:
                qty = 1

        # try to isolate candidate item name by removing verbs and numbers
        candidate = re.sub(r"\b(đặt|mua|thêm|giúp|cho tôi|order|xem|gợi ý)\b", "", text)
        candidate = re.sub(r"\d+", "", candidate).strip()

        # if no obvious candidate, respond with top suggestions
        if not candidate:
            top = menu_model.get_top_rated(5)
            names = ", ".join([f"{it['name']} ({it['price']:,} VND)" for it in top])
            return f"Bạn muốn đặt món nào? Gợi ý: {names}. Ví dụ: 'Đặt 2 Phở Bò'"

        found = find_menu_item_by_text(candidate)
        if not found:
            # try splitting candidate into words and re-match progressively
            parts = candidate.split()
            found = None
            for i in range(len(parts)):
                frag = " ".join(parts[i:])
                found = find_menu_item_by_text(frag)
                if found:
                    break

        if not found:
            return "Xin lỗi, tôi không tìm thấy món theo tên đó. Bạn thử gõ đúng tên món hoặc nhập 'gợi ý' để xem đề xuất."

        item_id, item = found
        # add to session cart
        cart = session.get('cart', {})
        key = str(item_id)
        if key in cart:
            cart[key]['quantity'] = int(cart[key].get('quantity', 0)) + qty
        else:
            cart[key] = {
                'name': item['name'],
                'price': item['price'],
                'image': item.get('image'),
                'quantity': qty
            }
        session['cart'] = cart
        total_qty = sum(int(v.get('quantity', 0)) for v in cart.values())
        return f"Đã thêm {qty} x {item['name']} ({item['price']:,.0f} VND) vào giỏ. Tổng món trong giỏ: {total_qty}. <a href=\"{url_for('view_cart')}\">Xem giỏ</a>"

    # Menu exploration / suggestions – only when user explicitly asks to list or recommend
    list_intent_words = ["gợi ý", "đề xuất", "đưa ra", "liệt kê", "kể", "đưa"]
    menu_words = ["menu", "món", "món ăn", "đồ uống", "thực đơn", "bán chạy"]
    wants_list = any(li in text for li in list_intent_words) and any(mw in text for mw in menu_words)
    if wants_list:
        # vegetarian filter
        if "chay" in text:
            veg = [it for it in menu_items if "chay" in (it.get('description') or "").lower()]
            if veg:
                veg.sort(key=lambda x: x.get('rating', 0), reverse=True)
                return "Gợi ý món chay: " + ", ".join([f"{it['name']} ({it['price']:,.0f} VND)" for it in veg[:6]])
            return "Hiện tại chưa có mục rõ ràng cho món chay, bạn muốn tôi lọc theo từ khóa nào?"

        # generic top rated list
        top = menu_model.get_top_rated(12)
        if top:
            mapping = {}
            lines = []
            for idx, it in enumerate(top, start=1):
                mapping[str(idx)] = it['id']
                lines.append(f"{idx}. {it['name']} — {it['price']:,.0f} VND")
            session['chat_last_menu'] = mapping
            list_html = "<br>".join(lines)
            return (
                "Dưới đây là các món gợi ý (hãy trả lời bằng số tương ứng để tôi thêm món vào giỏ):<br>"
                + list_html
                + "<br>Ví dụ: '1,3' hoặc '2 4' để thêm các món tương ứng."
            )

    # fallback information intents
    if "địa chỉ" in text or "địa điểm" in text:
        return f"Địa chỉ: {restaurant_info['address']}"
    if "giờ" in text or "mở cửa" in text:
        return f"Giờ mở cửa: {restaurant_info['hours']}"
    if "số điện thoại" in text or "liên hệ" in text:
        return f"Số điện thoại: {restaurant_info['phone']}"
    if "thanh toán" in text or "ví" in text:
        return "Phương thức thanh toán: " + ", ".join(restaurant_info['payment'])

    # default
    return "Xin chào! Tôi có thể gợi ý món và giúp bạn đặt hàng."

# QR Code Routes
@app.route('/scan_qr')
def scan_qr():
    """Trang quét QR cho nhân viên"""
    if "username" not in session or session.get("role") != "admin":
        flash("You do not have permission to access this page.", "error")
        return redirect(url_for("show_menu"))
    return render_template('scan_qr.html')


@app.route("/qr/render/<token>.svg")
def render_order_qr_svg(token):
    target_url = _build_order_target_url(token)
    svg = build_qr_svg(target_url)
    if not svg:
        return "QR SVG generator not available. Please install qrcode.", 500

    # Ép SVG nét vuông (tránh anti-alias gây cảm giác sứt cạnh)
    s = svg.lstrip()
    if s.startswith("<svg"):
        svg = svg.replace("<svg", '<svg shape-rendering="crispEdges"', 1)

    resp = Response(svg)
    resp.headers["Content-Type"] = "image/svg+xml; charset=utf-8"
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/qr/render/<token>.png")
def render_order_qr_png(token):
    """Trả về mã QR ở định dạng PNG.

    Hàm sẽ thêm một lề trắng rộng hơn nhằm tránh tình trạng browser scale
    gián tiếp cắt mất một cạnh của mã. Tham số `extra_border` truyền vào
    helper để đảm bảo margin lớn hơn bình thường.
    """
    target_url = _build_order_target_url(token)
    # dùng border lớn hơn và thêm padding an toàn
    png = build_qr_png_bytes(target_url, box_size=12, border=6, extra_border=2)
    if not png:
        return "QR PNG generator not available. Please install qrcode.", 500

    resp = Response(png)
    resp.headers["Content-Type"] = "image/png"
    resp.headers["Cache-Control"] = "no-store"
    return resp

@app.route("/qr/full/<token>")
def qr_fullscreen_view(token):
    token = normalize_text(token)
    if not token:
        return "Missing token", 400

    svg_url = url_for("render_order_qr_svg", token=token)
    png_url = url_for("render_order_qr_png", token=token)

    # Trả HTML viewer để căn giữa + scale đúng
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>QR Full Size</title>
  <style>
    :root {{
      --bg0:#fbfaf8;
      --bg1:#f3f5f4;
      --card:#ffffff;
      --text:#0f172a;
      --muted:#64748b;
      --border:rgba(15,23,42,.10);
      --shadow: 0 24px 60px -18px rgba(15,23,42,.20);
      --radius: 24px;
      --brand:#0e5c46;
    }}
    html,body{{height:100%;}}
    body{{
      margin:0;
      min-height:100vh;
      display:grid;
      place-items:center;
      background:
        radial-gradient(1200px 600px at 15% 10%, rgba(14,92,70,.10), transparent 60%),
        radial-gradient(900px 520px at 85% 12%, rgba(245,158,11,.10), transparent 55%),
        linear-gradient(180deg, var(--bg0), var(--bg1));
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
      color:var(--text);
      padding: 20px;
      box-sizing: border-box;
    }}
    .card{{
      width:min(92vmin, 820px);
      background:var(--card);
      border:1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 22px;
      position:relative;
    }}
    .badge{{
      position:absolute;
      top:-12px; left:50%;
      transform:translateX(-50%);
      background: rgba(14,92,70,.96);
      color:#fff;
      font-weight:900;
      font-size:.85rem;
      padding:6px 14px;
      border-radius:999px;
      letter-spacing:.6px;
    }}
    .qr-wrap{{
      background:#fff;
      border-radius: 18px;
      border:1px solid rgba(15,23,42,.10);
      padding: 18px; /* quiet-zone thêm, KHÔNG cắt vào QR */
      display:grid;
      place-items:center;
    }}
    /* Ưu tiên SVG: scale không mất pixel */
    img#qr {{
      width:min(86vmin, 760px);
      height:auto;
      aspect-ratio: 1 / 1;
      display:block;
      background:#fff;
    }}
    .meta{{
      margin-top: 14px;
      display:flex;
      justify-content: space-between;
      align-items:center;
      gap: 10px;
      flex-wrap: wrap;
      color: var(--muted);
      font-weight: 700;
      font-size: .92rem;
    }}
    .btn{{
      appearance:none;
      border:1px solid rgba(14,92,70,.28);
      background:#fff;
      color: var(--brand);
      font-weight:900;
      padding:10px 14px;
      border-radius: 14px;
      cursor:pointer;
      text-decoration:none;
      display:inline-flex;
      align-items:center;
      gap:8px;
    }}
    .btn:hover{{ background: rgba(14,92,70,.06); }}
  </style>
</head>
<body>
  <div class="card">
    <div class="badge">SCAN ME</div>
    <div class="qr-wrap">
      <img id="qr" alt="QR Code" src="{svg_url}?v={int(datetime.now().timestamp())}">
    </div>

    <div class="meta">
      <div>Token: <span style="font-family:ui-monospace,monospace; font-weight:900;">{token}</span></div>
      <div style="display:flex; gap:10px; flex-wrap:wrap;">
        <a class="btn" href="{png_url}?v={int(datetime.now().timestamp())}" target="_blank" rel="noopener">Open PNG</a>
        <button class="btn" id="btn-copy">Copy Link</button>
      </div>
    </div>
  </div>

  <script>
    // Nếu SVG load lỗi thì fallback sang PNG
    const img = document.getElementById("qr");
    img.addEventListener("error", () => {{
      img.src = "{png_url}?v=" + Date.now();
    }});

    document.getElementById("btn-copy").addEventListener("click", async () => {{
      const url = window.location.href;
      try {{
        await navigator.clipboard.writeText(url);
        alert("Copied!");
      }} catch(e) {{
        alert(url);
      }}
    }});
  </script>
</body>
</html>"""
    return Response(html, mimetype="text/html")

@app.route('/api/get_latest_order_qr')
def get_latest_order_qr():
    if "username" not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    try:
        order_id = session.get('last_order_id')

        if not order_id:
            customer_name = session.get('username')
            orders = order_controller.model.get_orders_by_customer(customer_name)
            if orders:
                order_id = orders[-1]['id']
            else:
                return jsonify({'success': False, 'message': 'No order found'}), 404

        order = order_controller.model.get_order_by_id(order_id)
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'}), 404

        order_dict = dict(order)
        qr_image = order_dict.get("qr_code_image")
        qr_token = normalize_text(order_dict.get("qr_code"))

        # thiếu QR -> generate lại
        if not qr_image or not qr_token:
            base_url = resolve_public_base_url()
            token_, qr_filename, qr_image_base64 = order_controller.model.generate_qr_code(order_id, base_url=base_url)
            if not token_:
                return jsonify({'success': False, 'message': 'Failed to generate QR code'}), 500

            call_with_supported_kwargs(
                order_controller.model.save_qr_code_to_order,
                {"order_id": order_id, "token": token_, "qr_filename": qr_filename, "qr_image_base64": qr_image_base64}
            )

            qr_token, qr_image = token_, qr_image_base64
            order_dict["qr_filename"] = qr_filename

        # NEW: normalize base64 để jsonify không bao giờ chết vì bytes
        qr_image = normalize_qr_base64(qr_image)

        # URLs ưu tiên dùng relative path (same-origin), tránh lệch host
        qr_svg_url = url_for('render_order_qr_svg', token=qr_token)
        qr_png_url = url_for('render_order_qr_png', token=qr_token)

        return jsonify({
            "success": True,
            "order_id": order_id,
            "qr_code": qr_token,
            "qr_image": qr_image,
            "qr_filename": order_dict.get("qr_filename"),
            "qr_svg_url": qr_svg_url,
            "qr_png_url": qr_png_url
        })

    except Exception as e:
        app.logger.exception("get_latest_order_qr failed")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Server is running'}), 200

@app.route('/api/get_order_by_qr', methods=['POST'])
def get_order_by_qr():
    """API để lấy thông tin order từ mã QR code - OPTIMIZED"""
    import sys
    import traceback
    
    try:
        # Get request data
        try:
            data = request.get_json(force=True, silent=False)
        except Exception as e:
            print(f"[ERROR] Failed to parse JSON: {e}")
            return jsonify({'success': False, 'message': 'Invalid JSON format'}), 400
        
        qr_code = data.get('qr_code', '').strip() if data else ''
        
        if not qr_code:
            print("[WARNING] QR code is empty")
            return jsonify({'success': False, 'message': 'QR code not provided'}), 400
        
        print(f"[DEBUG] QR Code received, length: {len(qr_code)}, preview: {qr_code[:50]}...")
        
        # Get order from model
        try:
            order = order_controller.model.get_order_by_qr_code(qr_code)
        except Exception as e:
            print(f"[ERROR] Error in get_order_by_qr_code: {str(e)}")
            traceback.print_exc()
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        if order:
            # Convert order to dict
            try:
                order_dict = dict(order)
                print(f"[DEBUG] Order retrieved: ID={order_dict.get('id')}, Customer={order_dict.get('customer_name')}")
                
                # Return response
                response = jsonify({
                    'success': True,
                    'order': order_dict
                })
                return response, 200
                
            except Exception as e:
                print(f"[ERROR] Error converting order to dict: {str(e)}")
                traceback.print_exc()
                return jsonify({'success': False, 'message': 'Error processing order data'}), 500
        else:
            print(f"[WARNING] Order not found for QR code")
            return jsonify({'success': False, 'message': 'Order not found. Please verify the QR code.'}), 404
    
    except Exception as e:
        print(f"[ERROR] Unexpected error in get_order_by_qr: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@app.route('/api/complete_order/<int:order_id>', methods=['POST'])
def complete_order_by_qr(order_id):
    """API để hoàn thành order (nhân viên đã kiểm tra QR)"""
    if "username" not in session or session.get("role") != "admin":
        return jsonify({'success': False, 'message': 'Permission denied'})
    
    # Cập nhật status order thành Completed
    if order_controller.model.update_order(order_id, status='Completed'):
        return jsonify({'success': True, 'message': 'Order marked as completed'})
    else:
        return jsonify({'success': False, 'message': 'Failed to complete order'})

@app.route('/qr_diagnostic')
def qr_diagnostic():
    """Diagnostic page for QR codes"""
    if "username" not in session or session.get("role") != "admin":
        return redirect(url_for('login'))
    return render_template('qr_diagnostic.html')

@app.route('/api/debug_qr/<int:order_id>')
def debug_qr(order_id):
    """Debug endpoint to check QR code data stored in database"""
    if "username" not in session or session.get("role") != "admin":
        return jsonify({'success': False, 'message': 'Permission denied'})
    
    try:
        import sqlite3
        conn = sqlite3.connect(order_controller.model.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, customer_name, qr_code, qr_code_image FROM orders WHERE id = ?", (order_id,))
        order = cursor.fetchone()
        conn.close()
        
        if order:
            order_dict = dict(order)
            # Limit output for debugging
            qr_code_preview = order_dict['qr_code'][:200] if order_dict['qr_code'] else 'None'
            qr_image_preview = 'Present' if order_dict['qr_code_image'] else 'None'
            
            return jsonify({
                'success': True,
                'order_id': order_dict['id'],
                'customer_name': order_dict['customer_name'],
                'qr_code_data': qr_code_preview,
                'qr_code_image_status': qr_image_preview,
                'full_qr_code': order_dict['qr_code']
            })
        else:
            return jsonify({'success': False, 'message': 'Order not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/get_order_details/<int:order_id>')
def get_order_details(order_id):
    """API để lấy thông tin chi tiết của order (cho trang view QR)"""
    if "username" not in session or session.get("role") != "admin":
        return jsonify({'success': False, 'message': 'Permission denied'})
    
    order = order_controller.model.get_order_by_id(order_id)
    
    if order:
        order_dict = dict(order)
        return jsonify({'success': True, 'order': order_dict})
    else:
        return jsonify({'success': False, 'message': 'Order not found'})

@app.route('/admin/orders/qr_viewer')
@admin_required
def qr_viewer():
    """Trang xem và in QR code của order"""
    return render_template('view_order_qr.html')

@app.route('/test_qr_scan')
def test_qr_scan():
    """Debug page for testing QR scan"""
    with open('test_qr_scan.html', 'r', encoding='utf-8') as f:
        return f.read()
    

@app.route("/q/o/<token>")
def view_order_by_token(token):
    order = order_controller.model.get_order_by_qr_token(token)
    if not order:
        return "<h3>Order not found</h3>", 404

    order_dict = dict(order)

    raw_items = order_dict.get("items_json") or order_dict.get("items") or ""
    items = []
    try:
        if isinstance(raw_items, str) and raw_items.strip().startswith("["):
            items = json.loads(raw_items)
    except:
        items = []

    return render_template("qr_order_view.html", order=order_dict, items=items)



if __name__ == "__main__":
    app.run(debug=True)