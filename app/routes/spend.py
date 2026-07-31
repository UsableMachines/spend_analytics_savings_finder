import logging
import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import SpendRecord, Supplier, Contract

logger = logging.getLogger(__name__)
spend_bp = Blueprint("spend", __name__)


@spend_bp.route("/spend")
@login_required
def spend_list():
    tid = current_user.tenant_id
    try:
        page = request.args.get("page", 1, type=int)
        category = request.args.get("category", "")
        supplier_id = request.args.get("supplier_id", "", type=str)
        q = SpendRecord.query.filter_by(tenant_id=tid)
        if category:
            q = q.filter(SpendRecord.category == category)
        if supplier_id:
            q = q.filter(SpendRecord.supplier_id == int(supplier_id))
        records = q.order_by(SpendRecord.spend_date.desc()).paginate(page=page, per_page=25)
        suppliers = Supplier.query.filter_by(tenant_id=tid).order_by(Supplier.name).all()
        categories = db.session.query(SpendRecord.category).filter_by(tenant_id=tid).distinct().all()
    except Exception as exc:
        logger.exception("spend_list error: %s", exc)
        return render_template("errors/500.html"), 500
    return render_template("spend/list.html", records=records, suppliers=suppliers,
                           categories=[c[0] for c in categories if c[0]],
                           sel_category=category, sel_supplier=supplier_id)


@spend_bp.route("/spend/add", methods=["GET", "POST"])
@login_required
def spend_add():
    if not current_user.can_edit():
        flash("Permission denied.", "danger")
        return redirect(url_for("spend.spend_list"))
    tid = current_user.tenant_id
    try:
        suppliers = Supplier.query.filter_by(tenant_id=tid).order_by(Supplier.name).all()
        contracts = Contract.query.filter_by(tenant_id=tid).all()
    except Exception as exc:
        logger.exception("spend_add load error: %s", exc)
        return render_template("errors/500.html"), 500

    if request.method == "POST":
        try:
            rec = SpendRecord(
                description=request.form.get("description", "").strip(),
                amount=float(request.form.get("amount", 0)),
                category=request.form.get("category", "").strip(),
                supplier_id=int(request.form["supplier_id"]),
                contract_id=int(request.form["contract_id"]) if request.form.get("contract_id") else None,
                tenant_id=tid,
                spend_date=datetime.date.fromisoformat(request.form["spend_date"]),
                is_maverick="is_maverick" in request.form,
                po_number=request.form.get("po_number", "").strip(),
                department=request.form.get("department", "").strip(),
            )
            db.session.add(rec)
            db.session.commit()
            flash("Spend record added.", "success")
            return redirect(url_for("spend.spend_list"))
        except Exception as exc:
            db.session.rollback()
            logger.exception("spend_add save error: %s", exc)
            flash(f"Error saving record: {exc}", "danger")

    return render_template("spend/form.html", suppliers=suppliers, contracts=contracts, record=None)


@spend_bp.route("/spend/<int:rid>/edit", methods=["GET", "POST"])
@login_required
def spend_edit(rid):
    if not current_user.can_edit():
        flash("Permission denied.", "danger")
        return redirect(url_for("spend.spend_list"))
    tid = current_user.tenant_id
    try:
        rec = SpendRecord.query.filter_by(id=rid, tenant_id=tid).first()
        suppliers = Supplier.query.filter_by(tenant_id=tid).order_by(Supplier.name).all()
        contracts = Contract.query.filter_by(tenant_id=tid).all()
    except Exception as exc:
        logger.exception("spend_edit load error: %s", exc)
        return render_template("errors/500.html"), 500
    if rec is None:
        flash("Record not found.", "warning")
        return redirect(url_for("spend.spend_list"))

    if request.method == "POST":
        try:
            rec.description = request.form.get("description", "").strip()
            rec.amount = float(request.form.get("amount", 0))
            rec.category = request.form.get("category", "").strip()
            rec.supplier_id = int(request.form["supplier_id"])
            rec.contract_id = int(request.form["contract_id"]) if request.form.get("contract_id") else None
            rec.spend_date = datetime.date.fromisoformat(request.form["spend_date"])
            rec.is_maverick = "is_maverick" in request.form
            rec.po_number = request.form.get("po_number", "").strip()
            rec.department = request.form.get("department", "").strip()
            db.session.commit()
            flash("Record updated.", "success")
            return redirect(url_for("spend.spend_list"))
        except Exception as exc:
            db.session.rollback()
            logger.exception("spend_edit save error: %s", exc)
            flash(f"Error updating record: {exc}", "danger")

    return render_template("spend/form.html", suppliers=suppliers, contracts=contracts, record=rec)


@spend_bp.route("/spend/<int:rid>/delete", methods=["POST"])
@login_required
def spend_delete(rid):
    if not current_user.can_edit():
        flash("Permission denied.", "danger")
        return redirect(url_for("spend.spend_list"))
    try:
        rec = SpendRecord.query.filter_by(id=rid, tenant_id=current_user.tenant_id).first()
        if rec:
            db.session.delete(rec)
            db.session.commit()
            flash("Record deleted.", "success")
        else:
            flash("Record not found.", "warning")
    except Exception as exc:
        db.session.rollback()
        logger.exception("spend_delete error: %s", exc)
        flash(f"Error deleting record: {exc}", "danger")
    return redirect(url_for("spend.spend_list"))
