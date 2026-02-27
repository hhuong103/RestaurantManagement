from flask import render_template, request, redirect, url_for, session, flash
from model.order_model import OrderModel

class OrderController:
    def __init__(self):
        self.model = OrderModel()

    def list_orders(self):
        orders = self.model.get_all_orders()
        return render_template("orders.html", orders=orders)

    def create_order_form(self):
        available_tables = self.model.get_available_tables()
        return render_template("order_form.html", available_tables=available_tables)

    def store_order(self):
        customer_name = session.get('username')
        items = request.form.get("items", "Unknown")
        quantity = int(request.form.get("quantity", 1))
        price = float(request.form.get("price", 0.0))
        status = request.form.get("status", "Pending")
        note = request.form.get("note", "")
        customer_phone = request.form.get("phone_number")
        customer_address = request.form.get("address")
        table_reservation = request.form.get("table_reservation")
        order_id = self.model.create_order(customer_name, items, quantity, price, status, note, customer_phone, customer_address, table_reservation)
        if order_id:
            # Tạo QR code cho đơn hàng
            qr_code_data, qr_filename, qr_image_base64 = self.model.generate_qr_code(order_id)
            if qr_code_data:
                self.model.save_qr_code_to_order(order_id, qr_code_data, qr_filename, qr_image_base64)
            flash("Order created successfully.", "success")
        else:
            flash("Failed to create order. Table may be reserved.", "error")
        return redirect(url_for("list_orders"))

    def edit_order_form(self, order_id):
        order = self.model.get_order_by_id(order_id)
        available_tables = self.model.get_available_tables()
        return render_template("order_form.html", order=order, available_tables=available_tables)

    def edit_order(self, order_id):
        order = self.model.get_order_by_id(order_id)
        available_tables = self.model.get_available_tables()
        return render_template("edit_order.html", order=order, available_tables=available_tables)

    def update_order(self, order_id):
        customer_name = request.form["customer_name"]
        items = request.form["items"]
        quantity = int(request.form["quantity"])
        price = float(request.form["price"])
        status = request.form.get("status", "Pending")
        note = request.form.get("note", "")
        table_reservation = request.form.get("table_reservation")
        if self.model.update_order(order_id, customer_name, items, quantity, price, status, note, table_reservation):
            flash("Order updated successfully.", "success")
        else:
            flash("Failed to update order. Table may be reserved.", "error")
        return redirect(url_for("list_orders"))

    def delete_order(self, order_id):
        self.model.delete_order(order_id)
        flash("Order deleted successfully.", "success")
        return redirect(url_for("list_orders"))

    def transaction_history(self):
        if "username" not in session:
            flash("Please log in to view your transaction history.", "error")
            return redirect(url_for("login"))
        if session.get("role") == "admin":
            orders = self.model.get_all_orders()
        else:
            customer_name = session["username"]
            orders = self.model.get_orders_by_customer(customer_name)
        return render_template("transaction_history.html", orders=orders)

    def cancel_order(self, order_id):
        if "username" not in session:
            flash("Please log in to cancel an order.", "error")
            return redirect(url_for("login"))
        order = self.model.get_order_by_id(order_id)
        if not order or (session.get("role") != "admin" and order["customer_name"] != session["username"]):
            flash("Order not found or you do not have permission to cancel it.", "error")
            return redirect(url_for("transaction_history"))
        if self.model.cancel_order(order_id, session["username"]):
            flash("Order has been cancelled successfully.", "success")
        else:
            flash("Cannot cancel this order. It may have already been processed.", "error")
        return redirect(url_for("transaction_history"))

    def approve_order(self, order_id):
        if "username" not in session or session.get("role") != "admin":
            flash("You do not have permission to approve orders.", "error")
            return redirect(url_for("login"))
        if self.model.approve_order(order_id, session["username"]):
            flash("Order has been approved successfully.", "success")
        else:
            flash("Cannot approve this order.", "error")
        return redirect(url_for("transaction_history"))

    def get_orders_by_customer(self, customer_name):
        return self.model.get_orders_by_customer(customer_name)

    def manage_tables(self):
        if not session.get('role') == 'admin':
            flash("You do not have permission to access this page.", "error")
            return redirect(url_for("show_menu"))
        tables = self.model.get_all_tables()
        return render_template("manage_tables.html", tables=tables)

    def create_table(self):
        name = request.form.get("name")
        type = request.form.get("type")
        capacity = request.form.get("capacity")
        services = request.form.get("services") or None
        status = request.form.get("status")
        if not name:
            flash("Table name is required.", "error")
            return redirect(url_for("create_table"))
        if self.model.create_table(name, type, capacity, services, status):
            flash("Table created successfully.", "success")
        else:
            flash("Failed to create table. Name may already exist.", "error")
        return redirect(url_for("manage_tables"))

    def edit_table(self, table_id):
        table = self.model.get_table_by_id(table_id)
        if not table:
            flash("Table not found.", "error")
            return redirect(url_for("manage_tables"))
        return render_template("edit_table.html", table=table)

    def update_table(self, table_id):
        name = request.form.get("name")
        status = request.form.get("status")
        reserved_by = request.form.get("reserved_by") or None
        reserved_at = request.form.get("reserved_at") or None
        type = request.form.get("type")
        capacity = request.form.get("capacity")
        services = request.form.get("services") or None
        if not name:
            flash("Table name is required.", "error")
            return redirect(url_for("edit_table", table_id=table_id))
        if self.model.update_table(table_id, name, status, reserved_by, reserved_at, type, capacity, services):
            flash("Table updated successfully.", "success")
        else:
            flash("Failed to update table. Name may already exist.", "error")
        return redirect(url_for("manage_tables"))

    def delete_table(self, table_id):
        if self.model.delete_table(table_id):
            flash("Table deleted successfully.", "success")
        else:
            flash("Failed to delete table.", "error")
        return redirect(url_for("manage_tables"))