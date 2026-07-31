import logging
import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Contract, Supplier

logger = logging.getLogger(__name__)
contracts_bp = Blueprint("contracts", __name__)


@contracts_bp.route("/contracts")
@login_required
def contract_list():
    tid = current_user.tenant_id
    try:
        contracts = Contract.query.filter_by(tenant_id=tid).order_by(Contract.end_date.desc()).all()
    except Exception as exc:
        logger.exception("contract_list error: %s", exc)
        return render_template("errors/500.html"), 500
    return render_template("contracts/list.html", contracts=contracts)


@contracts_bp.route("/contracts/add", methods=["GET", "POST"])
@login_required
def contract_add():
    if not current_user.can_edit():
        flash("Permission denied.", "danger")
        return redirect(url_for("contracts.contract_list"))
    tid = current_user.tenant_id
    try:
        suppliers = Supplier.query.filter_by(tenant_id=tid).order_by(Supplier.name).all()
    except Exception as exc:
        logger.exception("contract_add load error: %s", exc)
        return render_template("errors/500.html"), 500
    if request.method == "POST":
        try:
            c = Contract(
                title=request.form.get("title", "").strip(),
                supplier_id=int(request.form["supplier_id"]),
                tenant_id=tid,
                start_date=datetime.date.fromisoformat(request.form["start_date"]) if request.form.get("start_date") else None,
                end_date=datetime.date.fromisoformat(request.form["end_date"]) if request.form.get("end_date") else None,
                total_value=float(request.form.get("total_value", 0) or 0),
                status=request.form.get("status", "active"),
                terms=request.form.get("terms", "").strip(),
            )
            db.session.add(c)
            db.session.commit()
            flash("Contract added.", "success")
            return redirect(url_for("contracts.contract_list"))
        except Exception as exc:
            db.session.rollback()
            logger.exception("contract_add save error: %s", exc)
            flash(f"Error: {exc}", "danger")
    return render_template("contracts/form.html", suppliers=suppliers, contract=None)


@contracts_bp.route("/contracts/<int:cid>/edit", methods=["GET", "POST"])
@login_required
def contract_edit(cid):
    if not current_user.can_edit():
        flash("Permission denied.", "danger")
        return redirect(url_for("contracts.contract_list"))
    tid = current_user.tenant_id
    try:
        c = Contract.query.filter_by(id=cid, tenant_id=tid).first()
        suppliers = Supplier.query.filter_by(tenant_id=tid).order_by(Supplier.name).all()
    except Exception as exc:
        logger.exception("contract_edit load error: %s", exc)
        return render_template("errors/500.html"), 500
    if c is None:
        flash("Contract not found.", "warning")
        return redirect(url_for("contracts.contract_list"))
    if request.method == "POST":
        try:
            c.title = request.form.get("title", "").strip()
            c.supplier_id = int(request.form["supplier_id"])
            c.start_date = datetime.date.fromisoformat(request.form["start_date"]) if request.form.get("start_date") else None
            c.end_date = datetime.date.fromisoformat(request.form["end_date"]) if request.form.get("end_date") else None
            c.total_value = float(request.form.get("total_value", 0) or 0)
            c.status = request.form.get("status", "active")
            c.terms = request.form.get("terms", "").strip()
            db.session.commit()
            flash("Contract updated.", "success")
            return redirect(url_for("contracts.contract_list"))
        except Exception as exc:
            db.session.rollback()
            logger.exception("contract_edit save error: %s", exc)
            flash(f"Error: {exc}", "danger")
    return render_template("contracts/form.html", suppliers=suppliers, contract=c)


@contracts_bp.route("/contracts/<int:cid>/delete", methods=["POST"])
@login_required
def contract_delete(cid):
    if not current_user.can_edit():
        flash("Permission denied.", "danger")
        return redirect(url_for("contracts.contract_list"))
    try:
        c = Contract.query.filter_by(id=cid, tenant_id=current_user.tenant_id).first()
        if c:
            db.session.delete(c)
            db.session.commit()
            flash("Contract deleted.", "success")
        else:
            flash("Contract not found.", "warning")
    except Exception as exc:
        db.session.rollback()
        logger.exception("contract_delete error: %s", exc)
        flash(f"Error: {exc}", "danger")
    return redirect(url_for("contracts.contract_list"))
