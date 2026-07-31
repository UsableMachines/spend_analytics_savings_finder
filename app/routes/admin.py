import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import User, Tenant, Role
from app.routes.auth import role_required

logger = logging.getLogger(__name__)
admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/")
@role_required("admin")
def admin_home():
    tid = current_user.tenant_id
    try:
        users = User.query.filter_by(tenant_id=tid).order_by(User.username).all()
        roles = Role.query.filter_by(tenant_id=tid).all()
    except Exception as exc:
        logger.exception("admin_home error: %s", exc)
        return render_template("errors/500.html"), 500
    return render_template("admin/users.html", users=users, roles=roles)


@admin_bp.route("/users/<int:uid>/edit", methods=["GET", "POST"])
@role_required("admin")
def user_edit(uid):
    tid = current_user.tenant_id
    try:
        user = User.query.filter_by(id=uid, tenant_id=tid).first()
        roles = Role.query.filter_by(tenant_id=tid).all()
    except Exception as exc:
        logger.exception("user_edit load error: %s", exc)
        return render_template("errors/500.html"), 500
    if user is None:
        flash("User not found.", "warning")
        return redirect(url_for("admin.admin_home"))
    if request.method == "POST":
        try:
            user.email = request.form.get("email", user.email).strip()
            user.role_id = int(request.form.get("role_id", user.role_id))
            user.is_active = "is_active" in request.form
            pwd = request.form.get("password", "").strip()
            if pwd:
                user.set_password(pwd)
            db.session.commit()
            flash("User updated.", "success")
            return redirect(url_for("admin.admin_home"))
        except Exception as exc:
            db.session.rollback()
            logger.exception("user_edit save error: %s", exc)
            flash(f"Error: {exc}", "danger")
    return render_template("admin/user_edit.html", user=user, roles=roles)


@admin_bp.route("/users/<int:uid>/toggle", methods=["POST"])
@role_required("admin")
def user_toggle(uid):
    try:
        user = User.query.filter_by(id=uid, tenant_id=current_user.tenant_id).first()
        if user and user.id != current_user.id:
            user.is_active = not user.is_active
            db.session.commit()
            flash(f"User {'activated' if user.is_active else 'deactivated'}.", "success")
        elif user and user.id == current_user.id:
            flash("You cannot deactivate yourself.", "warning")
    except Exception as exc:
        db.session.rollback()
        logger.exception("user_toggle error: %s", exc)
        flash(f"Error: {exc}", "danger")
    return redirect(url_for("admin.admin_home"))


@admin_bp.route("/tenant", methods=["GET", "POST"])
@role_required("admin")
def tenant_settings():
    try:
        tenant = db.session.get(Tenant, current_user.tenant_id)
    except Exception as exc:
        logger.exception("tenant_settings load error: %s", exc)
        return render_template("errors/500.html"), 500
    if tenant is None:
        flash("Tenant not found.", "warning")
        return redirect(url_for("admin.admin_home"))
    if request.method == "POST":
        try:
            tenant.name = request.form.get("name", tenant.name).strip()
            db.session.commit()
            flash("Organization settings updated.", "success")
        except Exception as exc:
            db.session.rollback()
            logger.exception("tenant_settings save error: %s", exc)
            flash(f"Error: {exc}", "danger")
    return render_template("admin/tenant.html", tenant=tenant)
