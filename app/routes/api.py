import json
import logging
import datetime
import csv
import io
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import SpendRecord, Supplier, Contract

logger = logging.getLogger(__name__)
api_bp = Blueprint("api", __name__)


@api_bp.route("/spend/import", methods=["POST"])
@login_required
def import_spend():
    if not current_user.can_edit():
        return jsonify({"error": "Permission denied"}), 403
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file uploaded"}), 400
    tid = current_user.tenant_id
    try:
        content = f.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))
        imported = 0
        for row in reader:
            supplier_name = row.get("supplier", "").strip()
            if not supplier_name:
                continue
            supplier = Supplier.query.filter_by(name=supplier_name, tenant_id=tid).first()
            if not supplier:
                supplier = Supplier(name=supplier_name, tenant_id=tid, category=row.get("category", "").strip())
                db.session.add(supplier)
                db.session.flush()
            rec = SpendRecord(
                description=row.get("description", "").strip(),
                amount=float(row.get("amount", 0)),
                category=row.get("category", "").strip(),
                supplier_id=supplier.id,
                tenant_id=tid,
                spend_date=datetime.date.fromisoformat(row.get("date", datetime.date.today().isoformat())),
                is_maverick=row.get("is_maverick", "").lower() in ("true", "1", "yes"),
                po_number=row.get("po_number", "").strip(),
                department=row.get("department", "").strip(),
            )
            db.session.add(rec)
            imported += 1
        db.session.commit()
        return jsonify({"ok": True, "imported": imported})
    except Exception as exc:
        db.session.rollback()
        logger.exception("import_spend error: %s", exc)
        return jsonify({"error": str(exc)}), 500


@api_bp.route("/theme", methods=["POST"])
@login_required
def set_theme():
    theme = request.json.get("theme", "light") if request.is_json else "light"
    if theme not in ("light", "dark"):
        theme = "light"
    try:
        current_user.theme = theme
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("set_theme error: %s", exc)
        return jsonify({"error": str(exc)}), 500
    return jsonify({"ok": True, "theme": theme})
