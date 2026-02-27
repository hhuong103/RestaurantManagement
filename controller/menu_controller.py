import os
from uuid import uuid4

from flask import request, redirect, url_for, current_app, render_template, session
from werkzeug.utils import secure_filename

from model.menu_model import MenuModel


class MenuController:
    def __init__(self):
        self.model = MenuModel()

    # ---------- Helpers ----------
    @staticmethod
    def _unique_categories(items):
        """Lấy danh sách category duy nhất theo thứ tự xuất hiện."""
        cats = []
        seen = set()
        for it in items or []:
            c = (it.get("category") or "").strip()
            if c and c not in seen:
                seen.add(c)
                cats.append(c)
        return cats

    @staticmethod
    def _to_float(value, default=0.0):
        try:
            if value is None:
                return float(default)
            s = str(value).strip()
            if s == "":
                return float(default)
            return float(s)
        except Exception:
            return float(default)

    @staticmethod
    def _clamp_rating(r):
        """Giới hạn rating trong [0, 5]."""
        try:
            r = float(r)
        except Exception:
            r = 5.0
        if r < 0:
            return 0.0
        if r > 5:
            return 5.0
        return r

    @staticmethod
    def _save_image_file(image_file):
        """
        Lưu ảnh với tên unique để tránh ghi đè file đang bị Windows lock.
        Trả về image_filename (string) hoặc None nếu không lưu.
        """
        if not image_file or image_file.filename == "":
            return None

        allowed_extensions = {"jpg", "jpeg", "png", "gif"}
        ext = image_file.filename.rsplit(".", 1)[-1].lower()
        if ext not in allowed_extensions:
            return None

        upload_dir = os.path.join(current_app.root_path, "static", "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        base = secure_filename(os.path.splitext(image_file.filename)[0]) or "menu"
        unique_name = f"{base}_{uuid4().hex}.{ext}"
        upload_path = os.path.join(upload_dir, unique_name)

        image_file.save(upload_path)
        return unique_name

    @staticmethod
    def _safe_delete_image(filename):
        """Xóa ảnh best-effort (Windows có thể lock file)."""
        if not filename:
            return
        path = os.path.join(current_app.root_path, "static", "uploads", filename)
        if not os.path.exists(path):
            return
        try:
            os.remove(path)
        except PermissionError:
            # File đang bị process khác dùng (Explorer/Photos/antivirus...), bỏ qua để không crash
            pass
        except Exception:
            pass

    def _render_with_session(self, template_name, **context):
        """Render template kèm username/role nếu đăng nhập."""
        if "username" in session:
            context["username"] = session.get("username")
            context["role"] = session.get("role")
        return render_template(template_name, **context)

    # ---------- Pages ----------
    def request_menu(self):
        """
        Trang menu public (/).
        Hỗ trợ lọc theo category qua querystring: /?category=Dessert
        và search qua /?search=pho (nếu bạn muốn).
        """
        keyword = (request.args.get("search") or "").strip()
        category = (request.args.get("category") or "").strip()

        if keyword or category:
            menu_items = self.model.search_menu(keyword if keyword else None, category if category else None)
        else:
            menu_items = self.model.get_menu()

        # Prefer DB distinct categories if available; fallback to items list
        try:
            categories = self.model.get_distinct_categories()
        except Exception:
            categories = self._unique_categories(self.model.get_menu())

        return self._render_with_session(
            "menu.html",
            items=menu_items,
            categories=categories,
            selected_category=category,
            search_keyword=keyword,
        )

    def create_menu(self):
        """Trang form tạo món (admin)."""
        return self._render_with_session("menu_form.html")

    def store_menu(self):
        """Xử lý tạo món (admin)."""
        name = (request.form.get("name") or "").strip()
        description = (request.form.get("description") or "").strip()
        price = self._to_float(request.form.get("price"), default=0.0)

        rating = self._clamp_rating(request.form.get("rating", 5.0))
        category = (request.form.get("category") or "Main Course").strip() or "Main Course"

        # Upload ảnh (unique filename)
        image_file = request.files.get("image")
        image_filename = self._save_image_file(image_file)

        # Lưu DB
        self.model.store_menu(name, price, description, image_filename, rating, category)
        return redirect(url_for("show_menu_list"))

    def list_menu(self):
        """Trang danh sách món (admin)."""
        menu = self.model.get_menu()
        return self._render_with_session("list_menu.html", items=menu)

    def edit_menu(self, item_id):
        """GET: render form edit, POST: cập nhật DB + upload ảnh."""
        menu_item = self.model.get_menu_item_by_id(item_id)
        if not menu_item:
            return "Item not found", 404

        if request.method == "POST":
            name = (request.form.get("name") or "").strip()
            description = (request.form.get("description") or "").strip()
            price = self._to_float(request.form.get("price"), default=self._to_float(menu_item.get("price"), 0.0))

            rating = self._clamp_rating(request.form.get("rating", menu_item.get("rating", 5.0)))
            category = (request.form.get("category") or menu_item.get("category") or "Main Course").strip() or "Main Course"

            # Ảnh: mặc định giữ ảnh cũ
            image_file = request.files.get("image")
            old_image = menu_item.get("image")
            image_filename = old_image

            # Nếu có ảnh mới -> lưu ảnh mới (unique) rồi best-effort xóa ảnh cũ
            new_saved = self._save_image_file(image_file)
            if new_saved:
                image_filename = new_saved
                if old_image and old_image != image_filename:
                    self._safe_delete_image(old_image)

            # Update DB (có rating + category)
            ok = self.model.update_menu_item(item_id, name, price, description, image_filename, rating, category)
            if ok:
                return redirect(url_for("show_menu_list"))
            return "Error updating menu item", 500

        # GET
        return self._render_with_session("edit_menu.html", item=menu_item)

    def update_menu(self, item_id, name, price, description, image_filename, rating=5.0, category=None):
        """
        Nếu bạn vẫn muốn gọi update_menu() từ nơi khác.
        (edit_menu() bên trên đã update trực tiếp.)
        """
        rating = self._clamp_rating(rating)
        if category is not None:
            category = (str(category).strip() or "Main Course")

        if self.model.update_menu_item(item_id, name, price, description, image_filename, rating, category):
            return redirect(url_for("show_menu_list"))
        return "Error updating menu item", 500

    def delete_menu(self, item_id):
        """Xóa món + best-effort xóa ảnh của món."""
        menu_item = self.model.get_menu_item_by_id(item_id)
        if not menu_item:
            return redirect(url_for("show_menu_list"))

        image_filename = menu_item.get("image")

        self.model.delete_menu(item_id)

        # Best-effort xóa ảnh (không crash nếu Windows lock)
        if image_filename:
            self._safe_delete_image(image_filename)

        return redirect(url_for("show_menu_list"))

    def search(self):
        """Trang search riêng /search?... (nếu bạn dùng route riêng)."""
        keyword = (request.args.get("search") or "").strip()
        category = (request.args.get("category") or "").strip()

        menu_items = self.model.search_menu(keyword if keyword else None, category if category else None)

        try:
            categories = self.model.get_distinct_categories()
        except Exception:
            categories = self._unique_categories(self.model.get_menu())

        return self._render_with_session(
            "search_menu.html",
            items=menu_items,
            categories=categories,
            selected_category=category,
            search_keyword=keyword,
        )

    def buy_now(self, item_id):
        menu_item = self.model.get_menu_item_by_id(item_id)
        if not menu_item:
            return "Menu item not found", 404

        if request.method == "POST":
            name = (request.form.get("name") or "").strip()
            quantity = int(request.form.get("quantity") or 1)
            note = (request.form.get("note") or "").strip()

            price = self._to_float(menu_item.get("price"), 0.0)
            item_name = menu_item.get("name") or ""

            total_price = quantity * price
            self.model.store_order(name, item_name, quantity, total_price, note)

            return self._render_with_session(
                "order_confirmation.html",
                name=name,
                item=menu_item,
                quantity=quantity,
                note=note,
                total_price=total_price,
            )

        return self._render_with_session("buy_now.html", item=menu_item)
