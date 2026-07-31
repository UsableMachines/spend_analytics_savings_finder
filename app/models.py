import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db


class Tenant(db.Model):
    __tablename__ = "tenants"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    users = db.relationship("User", backref="tenant", lazy="dynamic")
    roles = db.relationship("Role", backref="tenant", lazy="dynamic")


class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=False)
    __table_args__ = (db.UniqueConstraint("name", "tenant_id"),)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    theme = db.Column(db.String(10), default="light")
    role = db.relationship("Role", backref="users")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def role_name(self):
        return self.role.name if self.role else "viewer"

    def has_role(self, role_name):
        return self.role_name == role_name

    def can_edit(self):
        return self.role_name in ("admin", "analyst")

    def is_admin(self):
        return self.role_name == "admin"


class Supplier(db.Model):
    __tablename__ = "suppliers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), nullable=False)
    category = db.Column(db.String(200))
    contact_email = db.Column(db.String(200))
    status = db.Column(db.String(50), default="active")
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    spend_records = db.relationship("SpendRecord", backref="supplier", lazy="dynamic")
    contracts = db.relationship("Contract", backref="supplier", lazy="dynamic")
    __table_args__ = (db.UniqueConstraint("name", "tenant_id"),)


class Contract(db.Model):
    __tablename__ = "contracts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    total_value = db.Column(db.Float, default=0)
    status = db.Column(db.String(50), default="active")
    terms = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class SpendRecord(db.Model):
    __tablename__ = "spend_records"
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(500))
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(200))
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    contract_id = db.Column(db.Integer, db.ForeignKey("contracts.id"), nullable=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=False)
    spend_date = db.Column(db.Date, nullable=False)
    is_maverick = db.Column(db.Boolean, default=False)
    po_number = db.Column(db.String(100))
    department = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class AnalysisRun(db.Model):
    __tablename__ = "analysis_runs"
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=False)
    run_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default="pending")
    summary = db.Column(db.Text)
    score = db.Column(db.Float)
    risk_level = db.Column(db.String(50))
    result_json = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    findings = db.relationship("Finding", backref="analysis_run", lazy="dynamic", cascade="all, delete-orphan")
    creator = db.relationship("User", backref="analysis_runs")


class Finding(db.Model):
    __tablename__ = "findings"
    id = db.Column(db.Integer, primary_key=True)
    analysis_run_id = db.Column(db.Integer, db.ForeignKey("analysis_runs.id"), nullable=False)
    finding_id = db.Column(db.String(100))
    category = db.Column(db.String(200))
    severity = db.Column(db.String(50))
    description = db.Column(db.Text)
    evidence = db.Column(db.Text)
    recommendation = db.Column(db.Text)
