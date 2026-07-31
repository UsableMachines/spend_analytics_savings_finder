import functools
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.is_active:
            login_user(user)
            nxt = request.args.get("next")
            return redirect(nxt or url_for("main.dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    from app.models import Tenant, Role
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
        else:
            tenant = Tenant.query.first()
            viewer_role = Role.query.filter_by(name="viewer", tenant_id=tenant.id).first()
            u = User(username=username, email=email, tenant_id=tenant.id, role_id=viewer_role.id)
            u.set_password(password)
            db.session.add(u)
            db.session.commit()
            flash("Account created. Please log in.", "success")
            return redirect(url_for("auth.login"))
    return render_template("auth/register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


def role_required(*roles):
    def decorator(f):
        @functools.wraps(f)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.role_name not in roles:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for("main.dashboard"))
            return f(*args, **kwargs)
        return wrapped
    return decorator
