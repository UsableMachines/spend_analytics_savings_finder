import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Supplier

logger = logging.getLogger(__name__)
suppliers_bp = Blueprint("suppliers", __name__)


@suppliers_bp.route("/suppliers")
@login_required
def supplier_list():
    tid = current_user.tenant_id
    try:
        suppliers = Supplier.query.filter_by(tenant_id=tid).order_by(Supplier.name).all()
    except Exception as exc:
        logger.exception("supplier_list error: %s", exc)
        return render_template("errors/500.html"), 500
    return render_template("suppliers/list.html", suppliers=suppliers)


@suppliers_bp.route("/suppliers/add", methods=["GET", "POST"])
@login_required
def supplier_add():
    if not current_user.can_edit():
        flash("Permission denied.", "danger")
        return redirect(url_for("suppliers.supplier_list"))
    if request.method == "POST":
        try:
            s = Supplier(
                name=request.form.get("name", "").strip(),
                category=request.form.get("category", "").strip(),
                contact_email=request.form.get("contact_email", "").strip(),
                status=request.form.get("status", "active"),
                tenant_id=current_user.tenant_id,
            )
            db.session.add(s)
            db.session.commit()
            flash("Supplier added.", "success")
            return redirect(url_for("suppliers.supplier_list"))
        except Exception as exc:
            db.session.rollback()
            logger.exception("supplier_add error: %s", exc)
            flash(f"Error: {exc}", "danger")
    return render_template("suppliers/form.html", supplier=None)


@suppliers_bp.route("/suppliers/<int:sid>/edit", methods=["GET", "POST"])
@login_required
def supplier_edit(sid):
    if not current_user.can_edit():
        flash("Permission denied.", "danger")
        return redirect(url_for("suppliers.supplier_list"))
    try:
        s = Supplier.query.filter_by(id=sid, tenant_id=current_user.tenant_id).first()
    except Exception as exc:
        logger.exception("supplier_edit load error: %s", exc)
        return render_template("errors/500.html"), 500
    if s is None:
        flash("Supplier not found.", "warning")
        return redirect(url_for("suppliers.supplier_list"))
    if request.method == "POST":
        try:
            s.name = request.form.get("name", "").strip()
            s.category = request.form.get("category", "").strip()
            s.contact_email = request.form.get("contact_email", "").strip()
            s.status = request.form.get("status", "active")
            db.session.commit()
            flash("Supplier updated.", "success")
            return redirect(url_for("suppliers.supplier_list"))
        except Exception as exc:
            db.session.rollback()
            logger.exception("supplier_edit save error: %s", exc)
            flash(f"Error: {exc}", "danger")
    return render_template("suppliers/form.html", supplier=s)


@suppliers_bp.route("/suppliers/<int:sid>/delete", methods=["POST"])
@login_required
def supplier_delete(sid):
    if not current_user.can_edit():
        flash("Permission denied.", "danger")
        return redirect(url_for("suppliers.supplier_list"))
    try:
        s = Supplier.query.filter_by(id=sid, tenant_id=current_user.tenant_id).first()
        if s:
            db.session.delete(s)
            db.session.commit()
            flash("Supplier deleted.", "success")
        else:
            flash("Supplier not found.", "warning")
    except Exception as exc:
        db.session.rollback()
        logger.exception("supplier_delete error: %s", exc)
        flash(f"Error: {exc}", "danger")
    return redirect(url_for("suppliers.supplier_list"))
