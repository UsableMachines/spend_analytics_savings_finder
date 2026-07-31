import logging
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models import SpendRecord, Supplier, Contract, AnalysisRun
from app.services.kindo_service import is_configured

logger = logging.getLogger(__name__)
main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def dashboard():
    tid = current_user.tenant_id
    try:
        total_spend = db.session.query(func.sum(SpendRecord.amount)).filter_by(tenant_id=tid).scalar() or 0
        supplier_count = Supplier.query.filter_by(tenant_id=tid).count()
        contract_count = Contract.query.filter_by(tenant_id=tid).count()
        maverick_count = SpendRecord.query.filter_by(tenant_id=tid, is_maverick=True).count()
        recent_analyses = AnalysisRun.query.filter_by(tenant_id=tid).order_by(AnalysisRun.created_at.desc()).limit(5).all()
        spend_by_cat = (
            db.session.query(SpendRecord.category, func.sum(SpendRecord.amount))
            .filter_by(tenant_id=tid)
            .group_by(SpendRecord.category)
            .all()
        )
        spend_by_supplier = (
            db.session.query(Supplier.name, func.sum(SpendRecord.amount))
            .join(SpendRecord, SpendRecord.supplier_id == Supplier.id)
            .filter(SpendRecord.tenant_id == tid)
            .group_by(Supplier.name)
            .order_by(func.sum(SpendRecord.amount).desc())
            .limit(10)
            .all()
        )
    except Exception as exc:
        logger.exception("dashboard: service error — %s", exc)
        return render_template("errors/500.html"), 500

    return render_template(
        "dashboard.html",
        total_spend=total_spend,
        supplier_count=supplier_count,
        contract_count=contract_count,
        maverick_count=maverick_count,
        recent_analyses=recent_analyses,
        spend_by_cat=spend_by_cat,
        spend_by_supplier=spend_by_supplier,
        agent_configured=is_configured(),
    )


@main_bp.route("/api/dashboard-data")
@login_required
def dashboard_data():
    tid = current_user.tenant_id
    try:
        spend_by_cat = (
            db.session.query(SpendRecord.category, func.sum(SpendRecord.amount))
            .filter_by(tenant_id=tid)
            .group_by(SpendRecord.category)
            .all()
        )
        spend_by_supplier = (
            db.session.query(Supplier.name, func.sum(SpendRecord.amount))
            .join(SpendRecord, SpendRecord.supplier_id == Supplier.id)
            .filter(SpendRecord.tenant_id == tid)
            .group_by(Supplier.name)
            .order_by(func.sum(SpendRecord.amount).desc())
            .limit(10)
            .all()
        )
    except Exception as exc:
        logger.exception("dashboard_data error: %s", exc)
        return jsonify({"error": "Failed to load data"}), 500
    return jsonify({
        "categories": [{"name": c or "Uncategorized", "amount": a} for c, a in spend_by_cat],
        "suppliers": [{"name": n, "amount": a} for n, a in spend_by_supplier],
    })
