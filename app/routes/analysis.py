import json
import logging
import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import AnalysisRun, Finding, SpendRecord, Supplier, Contract
from app.services.kindo_service import is_configured, run_analysis

logger = logging.getLogger(__name__)
analysis_bp = Blueprint("analysis", __name__)


@analysis_bp.route("/analysis")
@login_required
def analysis_list():
    tid = current_user.tenant_id
    try:
        runs = AnalysisRun.query.filter_by(tenant_id=tid).order_by(AnalysisRun.created_at.desc()).all()
    except Exception as exc:
        logger.exception("analysis_list error: %s", exc)
        return render_template("errors/500.html"), 500
    return render_template("analysis/list.html", runs=runs, agent_configured=is_configured())


@analysis_bp.route("/analysis/run", methods=["GET", "POST"])
@login_required
def analysis_run():
    if not current_user.can_edit():
        flash("Permission denied.", "danger")
        return redirect(url_for("analysis.analysis_list"))
    if not is_configured():
        flash("Kindo agent is not configured. Please set KINDO_API_TOKEN and KINDO_AGENT_ID.", "warning")
        return redirect(url_for("analysis.analysis_list"))

    tid = current_user.tenant_id
    if request.method == "POST":
        run_type = request.form.get("run_type", "analyze")
        try:
            records = _gather_spend_data(tid, run_type)
        except Exception as exc:
            logger.exception("analysis_run gather error: %s", exc)
            flash(f"Error gathering data: {exc}", "danger")
            return redirect(url_for("analysis.analysis_list"))

        ar = AnalysisRun(
            tenant_id=tid,
            run_type=run_type,
            status="running",
            created_by=current_user.id,
        )
        db.session.add(ar)
        db.session.commit()

        context = {"organization": current_user.tenant.name}
        result = run_analysis(
            operation=run_type,
            entity_id=f"tenant-{tid}-run-{ar.id}",
            records=records,
            context=context,
        )

        ar.status = "completed" if result.get("status") == "ok" else "failed"
        ar.summary = result.get("summary", "")
        ar.score = result.get("score")
        ar.risk_level = result.get("risk_level")
        ar.result_json = json.dumps(result)
        ar.completed_at = datetime.datetime.utcnow()

        for f in result.get("findings", []):
            finding = Finding(
                analysis_run_id=ar.id,
                finding_id=f.get("id", ""),
                category=f.get("category", ""),
                severity=f.get("severity", ""),
                description=f.get("description", ""),
                evidence=json.dumps(f.get("evidence", [])),
                recommendation=f.get("recommendation", ""),
            )
            db.session.add(finding)

        db.session.commit()
        flash("Analysis complete.", "success")
        return redirect(url_for("analysis.analysis_detail", rid=ar.id))

    return render_template("analysis/run.html")


@analysis_bp.route("/analysis/<int:rid>")
@login_required
def analysis_detail(rid):
    try:
        ar = AnalysisRun.query.filter_by(id=rid, tenant_id=current_user.tenant_id).first()
    except Exception as exc:
        logger.exception("analysis_detail error: %s", exc)
        return render_template("errors/500.html"), 500
    if ar is None:
        flash("Analysis not found.", "warning")
        return redirect(url_for("analysis.analysis_list"))
    result_data = {}
    if ar.result_json:
        try:
            result_data = json.loads(ar.result_json)
        except json.JSONDecodeError:
            pass
    return render_template("analysis/detail.html", run=ar, result=result_data)


def _gather_spend_data(tid, run_type):
    records = []
    spends = SpendRecord.query.filter_by(tenant_id=tid).order_by(SpendRecord.spend_date.desc()).limit(500).all()
    for s in spends:
        records.append({
            "id": s.id,
            "description": s.description,
            "amount": s.amount,
            "category": s.category,
            "supplier": s.supplier.name if s.supplier else "",
            "date": s.spend_date.isoformat() if s.spend_date else "",
            "is_maverick": s.is_maverick,
            "po_number": s.po_number,
            "department": s.department,
            "contract_id": s.contract_id,
        })
    if run_type in ("recommend", "analyze"):
        suppliers = Supplier.query.filter_by(tenant_id=tid).all()
        for sup in suppliers:
            records.append({
                "type": "supplier",
                "id": sup.id,
                "name": sup.name,
                "category": sup.category,
                "status": sup.status,
            })
        contracts = Contract.query.filter_by(tenant_id=tid).all()
        for c in contracts:
            records.append({
                "type": "contract",
                "id": c.id,
                "title": c.title,
                "supplier_id": c.supplier_id,
                "total_value": c.total_value,
                "start_date": c.start_date.isoformat() if c.start_date else "",
                "end_date": c.end_date.isoformat() if c.end_date else "",
                "status": c.status,
            })
    return records
