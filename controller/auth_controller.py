# auth_controller.py

from flask import request, session, redirect, url_for
from model.user_model import UserModel
from view.auth_view import AuthView


class AuthController:
    def __init__(self):
        self.user_model = UserModel()
        self.auth_view = AuthView()

    def register(self):
        """Handle GET (show form) and POST (create user)."""
        if request.method == "GET":
            return self.auth_view.show_register_form()

        # If POST, create the user
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role", "customer")  # default to customer

        # Check if user already exists
        existing_user = self.user_model.find_user_by_username(username)
        if existing_user:
            return "Username already taken. <a href='/register'>Try again</a>."

        # Create the user
        self.user_model.create_user(username, password, role)
        return "Registration successful. <a href='/login'>Login here</a>."

    def login(self):
        """Handle GET (show form) and POST (verify user)."""
        if request.method == "GET":
            return self.auth_view.show_login_form()

        # If POST, validate credentials
        username = request.form.get("username")
        password = request.form.get("password")

        user = self.user_model.find_user_by_username(username)
        if user and self.user_model.verify_password(password, user["password"]):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("home"))  # Redirect to home
        else:
            return "Invalid credentials. <a href='/login'>Try again</a>."

    def logout(self):
        """Clear the session and redirect home."""
        session.clear()
        return redirect(url_for("home"))

    def home(self):
        """Show a simple home page that changes if the user is logged in."""
        username = session.get("username")
        role = session.get("role")
        return self.auth_view.show_home(username=username, role=role)
