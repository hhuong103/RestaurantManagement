from flask import request, redirect, url_for, render_template, flash
from model.user_model import UserModel

class UserController:
    def __init__(self):
        
        self.model = UserModel()

    def list_users(self):
        """
        Display the list of all users.
        """
        users = self.model.get_all_users()
        return render_template("user_list.html", users=users)

    def create_user_form(self):
        """
        Show the 'Create New User' form.
        """
        return render_template("create_user.html")

    def store_user(self):
        """
        Handle form submission to create a new user.
        """
        # Retrieve form data
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")

        # Save the user
        self.model.create_user(username, password, role)

        # Redirect to the user management page
        return redirect(url_for("user_list"))
    
    def delete_user(self, user_id):
        self.model.delete_user(user_id)
        return redirect(url_for("user_list"))
    
    def edit_user_form(self, user_id):
        """
        Hiển thị form chỉnh sửa thông tin người dùng.
        """
        # Lấy thông tin người dùng từ cơ sở dữ liệu
        user = self.model.get_user_by_id(user_id)
        if not user:
            return "User not found", 404

        # Render template và pass thông tin người dùng
        return render_template("edit_user.html", user=user)
    
    def update_user(self, user_id):
      """
      Handle form submission to update a user's information.
      """
      username = request.form.get("username")
      password = request.form.get("password")
      role = request.form.get("role")

    # Check if user exists
      user = self.model.get_user_by_id(user_id)
      if not user:
        flash("User not found.", "error")
        return redirect(url_for("user_list"))

    # Nếu password không được cung cấp, giữ nguyên password cũ
      if not password:
        password = user['password']  # Lấy mật khẩu cũ nếu không nhập mới

      self.model.update_user(user_id, username, password, role)
      flash("User updated successfully!", "success")
      return redirect(url_for("user_list"))