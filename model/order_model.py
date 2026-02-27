import sqlite3
from datetime import datetime
import json
import qrcode
import os
from io import BytesIO
import base64
import secrets
import re

from PIL import ImageOps, Image, ImageDraw, ImageFont
from qrcode.constants import ERROR_CORRECT_Q


class OrderModel:
    def __init__(self, db_path="database.db"):
        self.db_path = db_path
        self.create_orders_table()
        self.create_tables_table()
        self.create_order_audit_table()
        self.add_columns_if_not_exist()
        self.initialize_tables()

    # ----------------------------
    # DB Helpers
    # ----------------------------
    def _connect(self, row_factory=False):
        conn = sqlite3.connect(self.db_path)
        if row_factory:
            conn.row_factory = sqlite3.Row
        return conn

    def _has_column(self, cursor, table_name, col_name):
        cursor.execute(f"PRAGMA table_info({table_name})")
        cols = [c[1] for c in cursor.fetchall()]
        return col_name in cols

    def _extract_note_field(self, note: str, key: str) -> str:
        """Lấy 'key: ...' trong note, dừng ở ', <NextKey>:' hoặc cuối chuỗi"""
        if not note:
            return ""
        s = str(note)
        # ví dụ: "Services: A (+20,000 VND), Items: B (x2)"
        pattern = re.compile(rf"{re.escape(key)}\s*:\s*(.*?)(?:,\s*[A-Za-z\s]+:\s*|$)", re.IGNORECASE)
        m = pattern.search(s)
        return (m.group(1) or "").strip() if m else ""

    def _parse_money(self, s: str) -> float:
        # "20,000 VND" / "20.000" -> 20000
        if not s:
            return 0.0
        digits = re.sub(r"[^\d]", "", str(s))
        return float(digits) if digits else 0.0

    def _parse_service_fees_from_note(self, note: str) -> float:
        """Sum tất cả (+xx VND) trong 'Services:'"""
        services_text = self._extract_note_field(note, "Services")
        if not services_text:
            return 0.0
        matches = re.findall(r"\+\s*[\d\.,]+\s*VND", services_text, flags=re.IGNORECASE)
        return sum(self._parse_money(m) for m in matches)

    def _normalize_items(self, items, quantity=None):
        """
        Chuẩn hoá items:
        - Nếu items là list/dict -> lưu JSON list chuẩn + tạo items_text
        - Nếu items là JSON string -> parse -> lưu chuẩn
        - Nếu items là string thường -> items_text=string, items_json="[]"
        Trả: (items_store, items_text, items_json)
        items_store: sẽ dùng để lưu vào cột orders.items (ưu tiên JSON nếu có)
        """
        items_text = ""
        items_json = "[]"

        if items is None:
            items_text = ""
            items_json = "[]"
        elif isinstance(items, (list, tuple)):
            lst = list(items)
            items_json = json.dumps(lst, ensure_ascii=False)
            parts = []
            for it in lst:
                if isinstance(it, dict):
                    name = (it.get("name") or "").strip() or "Item"
                    qty = int(it.get("quantity") or 1)
                else:
                    name = str(it).strip() or "Item"
                    qty = int(quantity or 1)
                parts.append(f"{name} (x{qty})")
            items_text = ", ".join(parts)
        elif isinstance(items, dict):
            items_json = json.dumps([items], ensure_ascii=False)
            name = (items.get("name") or "").strip() or "Item"
            qty = int(items.get("quantity") or 1)
            items_text = f"{name} (x{qty})"
        else:
            # string
            s = str(items).strip()
            if s.startswith("[") or s.startswith("{"):
                # cố parse JSON
                try:
                    obj = json.loads(s)
                    if isinstance(obj, dict):
                        obj = [obj]
                    if isinstance(obj, list):
                        items_json = json.dumps(obj, ensure_ascii=False)
                        parts = []
                        for it in obj:
                            if isinstance(it, dict):
                                name = (it.get("name") or "").strip() or "Item"
                                qty = int(it.get("quantity") or 1)
                            else:
                                name = str(it).strip() or "Item"
                                qty = int(quantity or 1)
                            parts.append(f"{name} (x{qty})")
                        items_text = ", ".join(parts)
                    else:
                        items_text = s
                        items_json = "[]"
                except Exception:
                    items_text = s
                    items_json = "[]"
            else:
                items_text = s
                items_json = "[]"

        # items_store ưu tiên JSON nếu có dữ liệu
        items_store = items_json if items_json != "[]" else (items_text or "[]")
        return items_store, items_text, items_json

    # ----------------------------
    # Create Tables
    # ----------------------------
    def create_orders_table(self):
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        customer_name TEXT NOT NULL,
                        items TEXT NOT NULL,
                        quantity INTEGER NOT NULL DEFAULT 0,
                        price REAL NOT NULL DEFAULT 0,
                        status TEXT DEFAULT 'Pending',
                        note TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP,
                        customer_phone TEXT,
                        customer_address TEXT,
                        table_reservation TEXT,
                        qr_code TEXT,
                        qr_code_image TEXT,
                        cancel_reason TEXT,
                        cancelled_by TEXT,
                        cancelled_at TIMESTAMP,

                        -- ✅ mới: để fix triệt để items + services
                        items_text TEXT,
                        items_json TEXT,
                        subtotal REAL DEFAULT 0,
                        service_fees REAL DEFAULT 0
                    );
                """)
        except sqlite3.Error as e:
            print(f"Error creating orders table: {e}")

    def create_order_audit_table(self):
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS order_audit (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        order_id INTEGER NOT NULL,
                        action TEXT NOT NULL,
                        old_status TEXT,
                        new_status TEXT NOT NULL,
                        performed_by TEXT NOT NULL,
                        reason TEXT,
                        performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (order_id) REFERENCES orders (id)
                    );
                """)
        except sqlite3.Error as e:
            print(f"Error creating order_audit table: {e}")

    def create_tables_table(self):
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS restaurant_tables (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        status TEXT DEFAULT 'Available', -- Available, Reserved
                        reserved_by TEXT,
                        reserved_at TIMESTAMP,
                        capacity INTEGER DEFAULT 2,
                        type TEXT DEFAULT 'Standard',
                        services TEXT
                    );
                """)
        except sqlite3.Error as e:
            print(f"Error creating restaurant_tables table: {e}")

    def initialize_tables(self):
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                tables = [f"Table {i}" for i in range(1, 16)]
                for t in tables:
                    cur.execute("""
                        INSERT OR IGNORE INTO restaurant_tables (name, status)
                        VALUES (?, 'Available')
                    """, (t,))
        except sqlite3.Error as e:
            print(f"Error initializing tables: {e}")

    def add_columns_if_not_exist(self):
        """DB migration cho DB cũ"""
        try:
            with self._connect() as conn:
                cur = conn.cursor()

                # --- orders ---
                cur.execute("PRAGMA table_info(orders)")
                cols = [c[1] for c in cur.fetchall()]

                def add_col(table, col, ddl):
                    if col not in cols:
                        cur.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")

                add_col("orders", "updated_at", "updated_at TIMESTAMP")
                add_col("orders", "qr_code", "qr_code TEXT")
                add_col("orders", "qr_code_image", "qr_code_image TEXT")

                add_col("orders", "qr_filename", "qr_filename TEXT")

                add_col("orders", "cancel_reason", "cancel_reason TEXT")
                add_col("orders", "cancelled_by", "cancelled_by TEXT")
                add_col("orders", "cancelled_at", "cancelled_at TIMESTAMP")

                # ✅ mới để fix items + services
                add_col("orders", "items_text", "items_text TEXT")
                add_col("orders", "items_json", "items_json TEXT")
                add_col("orders", "subtotal", "subtotal REAL DEFAULT 0")
                add_col("orders", "service_fees", "service_fees REAL DEFAULT 0")

                # indexes
                try:
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_orders_qr_code ON orders(qr_code)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at)")
                except Exception:
                    pass

                # --- order_audit: add reason nếu DB cũ chưa có ---
                if not self._has_column(cur, "order_audit", "reason"):
                    try:
                        cur.execute("ALTER TABLE order_audit ADD COLUMN reason TEXT")
                    except Exception:
                        pass

                # --- restaurant_tables ---
                if not self._has_column(cur, "restaurant_tables", "capacity"):
                    cur.execute("ALTER TABLE restaurant_tables ADD COLUMN capacity INTEGER DEFAULT 2")
                if not self._has_column(cur, "restaurant_tables", "type"):
                    cur.execute("ALTER TABLE restaurant_tables ADD COLUMN type TEXT DEFAULT 'Standard'")
                if not self._has_column(cur, "restaurant_tables", "services"):
                    cur.execute("ALTER TABLE restaurant_tables ADD COLUMN services TEXT")

        except sqlite3.Error as e:
            print(f"Error adding columns: {e}")

    # ----------------------------
    # Audit
    # ----------------------------
    def insert_audit(self, order_id, action, old_status, new_status, performed_by, reason=None):
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO order_audit (order_id, action, old_status, new_status, performed_by, reason)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (order_id, action, old_status, new_status, performed_by, reason))
        except sqlite3.Error as e:
            print(f"Error inserting audit: {e}")

    # ----------------------------
    # Orders CRUD
    # ----------------------------
    def get_all_orders(self):
        try:
            with self._connect(row_factory=True) as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM orders")
                return cur.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching all orders: {e}")
            return []

    def get_order_by_id(self, order_id):
        try:
            with self._connect(row_factory=True) as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
                return cur.fetchone()
        except sqlite3.Error as e:
            print(f"Error fetching order {order_id}: {e}")
            return None

    def get_order_by_qr_token(self, token):
        try:
            with self._connect(row_factory=True) as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM orders WHERE qr_code = ? LIMIT 1", (token,))
                return cur.fetchone()
        except sqlite3.Error as e:
            print("Error get_order_by_qr_token:", e)
            return None

    def get_order_by_qr_code(self, qr_code_data):
        """
        Nhận qr_code_data có thể là:
        - URL: .../scan_qr?code=<token>
        - URL: .../q/o/<token>
        - token trực tiếp
        - JSON cũ / ORDER#id / số id
        """
        try:
            if qr_code_data is None:
                return None

            s = str(qr_code_data).strip().lstrip("\ufeff").strip()
            if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
                s = s[1:-1].strip()

            # 1) scan_qr?code=<token>
            m = re.search(r"[?&]code=([^&#]+)", s)
            if m:
                token = m.group(1).strip()
                return self.get_order_by_qr_token(token)

            # 2) /q/o/<token>
            m = re.search(r"/q/o/([^/?#]+)", s)
            if m:
                token = m.group(1).strip()
                return self.get_order_by_qr_token(token)

            # 3) token trực tiếp
            if re.fullmatch(r"[A-Za-z0-9_\-]{10,}", s):
                return self.get_order_by_qr_token(s)

            # 4) JSON cũ
            order_id = None
            if s.startswith("{"):
                try:
                    obj = json.loads(s)
                    order_id = obj.get("order_id")
                except Exception:
                    order_id = None

            # 5) ORDER#id#...
            if not order_id and "#" in s:
                parts = s.split("#")
                if len(parts) >= 2:
                    try:
                        order_id = int(parts[1])
                    except Exception:
                        pass

            # 6) số id
            if not order_id:
                try:
                    order_id = int(s)
                except Exception:
                    return None

            return self.get_order_by_id(order_id)

        except Exception as e:
            print(f"[ERROR] Error processing QR code: {e}")
            return None

    def create_order(
        self,
        customer_name,
        items,
        quantity,
        price,
        status="Pending",
        note=None,
        customer_phone=None,
        customer_address=None,
        table_reservation=None,
        items_json=None,
        subtotal=None,
        service_fees=None
    ):
        """
        ✅ price: tổng cuối cùng (đã gồm services)
        ✅ subtotal: tổng món (chưa services) - nếu None sẽ auto suy ra
        ✅ service_fees: phí dịch vụ - nếu None sẽ auto parse từ note
        ✅ items_json: JSON list món (name/quantity/price). Nếu có, sẽ lưu để scan hiển thị chuẩn
        """
        try:
            # Table reserve (giữ logic cũ)
            with self._connect() as conn:
                cur = conn.cursor()

                if table_reservation and table_reservation != "No Reservation":
                    cur.execute("SELECT status FROM restaurant_tables WHERE name = ?", (table_reservation,))
                    row = cur.fetchone()
                    if not row or row[0] != "Available":
                        return None
                    cur.execute("""
                        UPDATE restaurant_tables
                        SET status='Reserved', reserved_by=?, reserved_at=?
                        WHERE name=?
                    """, (customer_name, datetime.now(), table_reservation))

                # Normalize items
                items_store, items_text_norm, items_json_norm = self._normalize_items(items, quantity=quantity)
                if items_json:
                    # ưu tiên items_json do controller truyền vào
                    try:
                        json.loads(items_json)  # validate
                        items_json_norm = items_json
                        items_store = items_json_norm
                        # tạo text từ items_json nếu có
                        items_store2, items_text_norm2, _ = self._normalize_items(items_json, quantity=quantity)
                        items_text_norm = items_text_norm2 or items_text_norm
                    except Exception:
                        pass

                # Fees parse from note
                auto_service = self._parse_service_fees_from_note(note or "")
                if service_fees is None:
                    service_fees = auto_service

                # subtotal auto
                if subtotal is None:
                    try:
                        subtotal = float(price or 0) - float(service_fees or 0)
                        if subtotal < 0:
                            subtotal = 0
                    except Exception:
                        subtotal = 0

                cur.execute("""
                    INSERT INTO orders (
                        customer_name, items, quantity, price, status, note,
                        created_at, updated_at, customer_phone, customer_address, table_reservation,
                        items_text, items_json, subtotal, service_fees
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    customer_name,
                    items_store or "[]",
                    int(quantity or 0),
                    float(price or 0),
                    status,
                    note,
                    datetime.now(),
                    datetime.now(),
                    customer_phone,
                    customer_address,
                    table_reservation,
                    items_text_norm,
                    items_json_norm,
                    float(subtotal or 0),
                    float(service_fees or 0)
                ))

                order_id = cur.lastrowid
                self.insert_audit(order_id, "Created", None, status, customer_name)
                return order_id

        except sqlite3.Error as e:
            print(f"Error creating order: {e}")
            return None

    def update_order(
        self,
        order_id,
        customer_name=None,
        items=None,
        quantity=None,
        price=None,
        status=None,
        note=None,
        table_reservation=None,
        items_json=None,
        subtotal=None,
        service_fees=None
    ):
        current = self.get_order_by_id(order_id)
        if not current:
            return False

        customer_name = customer_name if customer_name is not None else current["customer_name"]
        quantity = int(quantity if quantity is not None else current["quantity"])
        price = float(price if price is not None else current["price"])
        status = status if status is not None else current["status"]
        note = note if note is not None else current["note"]
        table_reservation = table_reservation if table_reservation is not None else current["table_reservation"]

        # Normalize items
        if items is None:
            items = current["items"]

        items_store, items_text_norm, items_json_norm = self._normalize_items(items, quantity=quantity)
        if items_json:
            try:
                json.loads(items_json)
                items_json_norm = items_json
                items_store = items_json_norm
                items_store2, items_text_norm2, _ = self._normalize_items(items_json, quantity=quantity)
                items_text_norm = items_text_norm2 or items_text_norm
            except Exception:
                pass

        # service fees
        auto_service = self._parse_service_fees_from_note(note or "")
        if service_fees is None:
            service_fees = auto_service

        # subtotal
        if subtotal is None:
            try:
                subtotal = price - float(service_fees or 0)
                if subtotal < 0:
                    subtotal = 0
            except Exception:
                subtotal = 0

        try:
            with self._connect() as conn:
                cur = conn.cursor()

                # đổi bàn
                if table_reservation != current["table_reservation"]:
                    old_table = current["table_reservation"]
                    if old_table and old_table != "No Reservation":
                        cur.execute("""
                            UPDATE restaurant_tables
                            SET status='Available', reserved_by=NULL, reserved_at=NULL
                            WHERE name=?
                        """, (old_table,))

                    if table_reservation and table_reservation != "No Reservation":
                        cur.execute("SELECT status FROM restaurant_tables WHERE name=?", (table_reservation,))
                        row = cur.fetchone()
                        if not row or row[0] != "Available":
                            return False
                        cur.execute("""
                            UPDATE restaurant_tables
                            SET status='Reserved', reserved_by=?, reserved_at=?
                            WHERE name=?
                        """, (customer_name, datetime.now(), table_reservation))

                cur.execute("""
                    UPDATE orders
                    SET customer_name=?,
                        items=?,
                        quantity=?,
                        price=?,
                        status=?,
                        note=?,
                        table_reservation=?,
                        items_text=?,
                        items_json=?,
                        subtotal=?,
                        service_fees=?,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                """, (
                    customer_name,
                    items_store or "[]",
                    quantity,
                    price,
                    status,
                    note,
                    table_reservation,
                    items_text_norm,
                    items_json_norm,
                    float(subtotal or 0),
                    float(service_fees or 0),
                    order_id
                ))
                return True

        except sqlite3.Error as e:
            print(f"Error updating order {order_id}: {e}")
            return False

    def delete_order(self, order_id):
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute("SELECT table_reservation FROM orders WHERE id=?", (order_id,))
                row = cur.fetchone()
                if row and row[0] and row[0] != "No Reservation":
                    cur.execute("""
                        UPDATE restaurant_tables
                        SET status='Available', reserved_by=NULL, reserved_at=NULL
                        WHERE name=?
                    """, (row[0],))
                cur.execute("DELETE FROM orders WHERE id=?", (order_id,))
        except sqlite3.Error as e:
            print(f"Error deleting order {order_id}: {e}")

    # ----------------------------
    # Cancel / Approve
    # ----------------------------
    def can_cancel_order(self, order_id):
        order = self.get_order_by_id(order_id)
        return bool(order and order["status"] == "Pending")

    def cancel_order(self, order_id, performed_by, reason=None):
        if not self.can_cancel_order(order_id):
            return False
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute("SELECT status, table_reservation FROM orders WHERE id=?", (order_id,))
                row = cur.fetchone()
                if not row:
                    return False
                old_status, table_reservation = row[0], row[1]

                if table_reservation and table_reservation != "No Reservation":
                    cur.execute("""
                        UPDATE restaurant_tables
                        SET status='Available', reserved_by=NULL, reserved_at=NULL
                        WHERE name=?
                    """, (table_reservation,))

                cur.execute("""
                    UPDATE orders
                    SET status='Cancelled',
                        updated_at=CURRENT_TIMESTAMP,
                        cancel_reason=?,
                        cancelled_by=?,
                        cancelled_at=CURRENT_TIMESTAMP
                    WHERE id=?
                """, (reason, performed_by, order_id))

                self.insert_audit(order_id, "Cancelled", old_status, "Cancelled", performed_by, reason=reason)
                return True
        except sqlite3.Error as e:
            print(f"Error cancelling order {order_id}: {e}")
            return False

    def approve_order(self, order_id, performed_by):
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute("SELECT status FROM orders WHERE id=?", (order_id,))
                old = cur.fetchone()
                old_status = old[0] if old else None

                cur.execute("""
                    UPDATE orders
                    SET status='Completed', updated_at=CURRENT_TIMESTAMP
                    WHERE id=? AND status='Pending'
                """, (order_id,))
                if cur.rowcount > 0:
                    self.insert_audit(order_id, "Approved", old_status, "Completed", performed_by)
                    return True
                return False
        except sqlite3.Error as e:
            print(f"Error approving order: {e}")
            return False

    def get_orders_by_customer(self, customer_name):
        try:
            with self._connect(row_factory=True) as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM orders WHERE customer_name=?", (customer_name,))
                return cur.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching orders for {customer_name}: {e}")
            return []

    # ----------------------------
    # Tables
    # ----------------------------
    def get_available_tables(self):
        try:
            with self._connect(row_factory=True) as conn:
                cur = conn.cursor()
                cur.execute("SELECT name FROM restaurant_tables WHERE status='Available'")
                return cur.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching available tables: {e}")
            return []

    def get_all_tables(self):
        try:
            with self._connect(row_factory=True) as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM restaurant_tables")
                return cur.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching all tables: {e}")
            return []

    def create_table(self, name, type='Standard', capacity=2, services=None, status='Available'):
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO restaurant_tables (name, type, capacity, services, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, type, int(capacity) if capacity else 2, services, status))
                return True
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")
            return False

    def update_table(self, table_id, name, status=None, reserved_by=None, reserved_at=None, type=None, capacity=None, services=None):
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute("SELECT name FROM restaurant_tables WHERE id=?", (table_id,))
                current = cur.fetchone()
                if not current:
                    return False

                cur.execute("SELECT id FROM restaurant_tables WHERE name=? AND id!=?", (name, table_id))
                if cur.fetchone():
                    return False

                # update orders referencing old table name
                old_name = current[0]
                cur.execute("UPDATE orders SET table_reservation=? WHERE table_reservation=?", (name, old_name))

                fields = ["name=?"]
                vals = [name]

                if status is not None:
                    fields.append("status=?"); vals.append(status)
                if reserved_by is not None:
                    fields.append("reserved_by=?"); vals.append(reserved_by)
                if reserved_at is not None:
                    fields.append("reserved_at=?"); vals.append(reserved_at)
                if type is not None:
                    fields.append("type=?"); vals.append(type)
                if capacity is not None:
                    fields.append("capacity=?"); vals.append(int(capacity) if capacity else 2)
                if services is not None:
                    fields.append("services=?"); vals.append(services)

                vals.append(table_id)
                cur.execute(f"UPDATE restaurant_tables SET {', '.join(fields)} WHERE id=?", vals)
                return True
        except sqlite3.Error as e:
            print(f"Error updating table {table_id}: {e}")
            return False

    def delete_table(self, table_id):
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute("SELECT name FROM restaurant_tables WHERE id=?", (table_id,))
                row = cur.fetchone()
                if not row:
                    return False

                name = row[0]
                cur.execute("UPDATE orders SET table_reservation=NULL WHERE table_reservation=?", (name,))
                cur.execute("DELETE FROM restaurant_tables WHERE id=?", (table_id,))
                return True
        except sqlite3.Error as e:
            print(f"Error deleting table {table_id}: {e}")
            return False

    # ----------------------------
    # QR Code
    # ----------------------------
    def generate_qr_code(self, order_id, base_url=None, existing_token=None):
        """
        ✅ QR chống cắt cạnh:
        - border=6 + expand(border=12)
        - error_correction=Q (chịu lỗi tốt hơn)
        """
        base_url = (base_url or "").rstrip("/")
        token = existing_token or secrets.token_urlsafe(16)

        # dữ liệu để scan
        qr_data = f"{base_url}/scan_qr?code={token}" if base_url else token

        # box_size: pixels per module. border: quiet zone in modules (minimum 4 per spec).
        # Increase box_size (module pixel size) so each QR module is much larger
        # This makes the QR visually bigger without enlarging the surrounding container.
        box_size = 64
        quiet_zone_modules = 12  # generous quiet zone in modules to protect finder patterns
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=box_size,
            border=quiet_zone_modules
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

        # Add extra white margin (in pixels) around the QR to protect finder patterns.
        # Keep this margin moderate since box_size is now large.
        extra_margin = box_size * 6  # e.g., 64*6 = 384px
        img_with_margin_w = img.width + extra_margin * 2
        img_with_margin_h = img.height + extra_margin * 2
        canvas = Image.new("RGB", (img_with_margin_w, img_with_margin_h), "white")
        canvas.paste(img, (extra_margin, extra_margin))

        # Thêm phần chứa token dưới QR để nhân viên có thể nhập tay nếu cần
        try:
            try:
                font = ImageFont.truetype("arial.ttf", 18)
            except Exception:
                font = ImageFont.load_default()

            text = token
            draw = ImageDraw.Draw(canvas)
            text_w, text_h = draw.textsize(text, font=font)

            padding = 14
            new_h = canvas.height + text_h + padding * 2
            new_img = Image.new("RGB", (canvas.width, new_h), "white")
            new_img.paste(canvas, (0, 0))

            text_x = (canvas.width - text_w) // 2
            text_y = canvas.height + padding
            draw = ImageDraw.Draw(new_img)
            draw.text((text_x, text_y), text, fill="black", font=font)
        except Exception:
            new_img = canvas

        # Upsample image if it's still relatively small to avoid browser scaling blur
        try:
            # With a much larger `box_size`, no aggressive upsampling is needed.
            # Keep image as-generated to preserve sharp, large modules.
            min_size_px = 0
            if min_size_px and new_img.width < min_size_px:
                scale = (min_size_px / new_img.width)
                new_size = (int(new_img.width * scale), int(new_img.height * scale))
                # Use NEAREST to keep QR modules sharp
                new_img = new_img.resize(new_size, resample=Image.NEAREST)
        except Exception:
            pass

        # Ensure a very large outer white border so no UI or rounding ever clips finder patterns.
        try:
            outer_margin = box_size * 8  # moderate safety margin given large module size (e.g., 64*8=512px)
            final_w = new_img.width + outer_margin * 2
            final_h = new_img.height + outer_margin * 2
            final_canvas = Image.new("RGB", (final_w, final_h), "white")
            final_canvas.paste(new_img, (outer_margin, outer_margin))
            # Convert to RGB explicitly and remove any alpha channel
            final_img = final_canvas.convert("RGB")
        except Exception:
            final_img = new_img.convert("RGB")

        os.makedirs("static/qr_codes", exist_ok=True)
        # filename kèm token nhỏ để tránh cache lỗi khi cập nhật
        safe_token = re.sub(r"[^A-Za-z0-9_-]", "", token)[:12]
        filename = f"order_{order_id}_qr_{safe_token}.png"
        filepath = os.path.join("static", "qr_codes", filename)

        # Lưu ảnh với DPI cao để đảm bảo camera quét tốt
        # Convert to strict black & white (bilevel) to remove any semi-transparent pixels
        try:
            bw_img = final_img.convert('1')
        except Exception:
            bw_img = final_img.convert('L').point(lambda x: 0 if x < 128 else 255, '1')

        try:
            bw_img.save(filepath, format="PNG", optimize=False, dpi=(300, 300))
        except TypeError:
            bw_img.save(filepath, format="PNG", optimize=False)

        buf = BytesIO()
        bw_img.save(buf, format="PNG", optimize=False)
        qr_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return token, filename, qr_base64

    def save_qr_code_to_order(self, order_id, token, qr_filename=None, qr_image_base64=None):
        """
        Lưu token + ảnh base64 vào DB.
        qr_filename hiện chưa có cột riêng -> không bắt buộc lưu.
        """
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE orders
                    SET qr_code=?, qr_code_image=?, qr_filename=?, updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                """, (token, qr_image_base64, qr_filename, order_id))
                return True
        except sqlite3.Error as e:
            print(f"Error saving QR code to order: {e}")
            return False

    # ----------------------------
    # Revenue / Analytics (giữ như bạn đang dùng)
    # ----------------------------
    def get_revenue_per_month(self, year):
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                query = """
                    SELECT strftime('%m', created_at) AS month, SUM(price)
                    FROM orders
                    WHERE status = 'Completed' AND strftime('%Y', created_at) = ?
                    GROUP BY month ORDER BY month
                """
                cur.execute(query, (str(year),))
                results = cur.fetchall()

            revenue_dict = {m: total for m, total in results}
            return [revenue_dict.get(f"{i:02}", 0) for i in range(1, 13)]
        except sqlite3.Error as e:
            print(f"Error in get_revenue_per_month: {e}")
            return [0] * 12

    def get_customer_counts_per_month(self, year):
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                query = """
                    SELECT strftime('%m', created_at) AS month, COUNT(DISTINCT customer_name)
                    FROM orders
                    WHERE strftime('%Y', created_at) = ?
                    GROUP BY month ORDER BY month
                """
                cur.execute(query, (str(year),))
                results = cur.fetchall()

            d = {m: c for m, c in results}
            return [d.get(f"{i:02}", 0) for i in range(1, 13)]
        except sqlite3.Error as e:
            print(f"Error in get_customer_counts_per_month: {e}")
            return [0] * 12

    def get_monthly_revenue(self, month, year):
        try:
            with self._connect(row_factory=True) as conn:
                cur = conn.cursor()
                month = f"{int(month):02d}"
                year = str(year)
                cur.execute("""
                    SELECT SUM(price) as total_revenue
                    FROM orders
                    WHERE strftime('%m', created_at)=?
                      AND strftime('%Y', created_at)=?
                      AND status='Completed'
                """, (month, year))
                row = cur.fetchone()
                return row["total_revenue"] if row and row["total_revenue"] is not None else 0
        except sqlite3.Error as e:
            print(f"Error calculating monthly revenue: {e}")
            return 0

    def get_revenue_per_day(self, month, year):
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                month = f"{int(month):02d}"
                year = str(year)
                query = """
                    SELECT strftime('%d', created_at) AS day, SUM(price)
                    FROM orders
                    WHERE status='Completed'
                      AND strftime('%m', created_at)=?
                      AND strftime('%Y', created_at)=?
                    GROUP BY day ORDER BY day
                """
                cur.execute(query, (month, year))
                results = cur.fetchall()

            d = {day: total for day, total in results}
            return [d.get(f"{i:02}", 0) for i in range(1, 32)]
        except sqlite3.Error as e:
            print(f"Error in get_revenue_per_day: {e}")
            return [0] * 31
