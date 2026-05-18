from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class Admin(TimestampMixin, db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)


class Department(TimestampMixin, db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    employees = db.relationship("Employee", back_populates="department", lazy=True)


class Employee(TimestampMixin, db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False, index=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    position = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(120), nullable=True, unique=True)
    photo_filename = db.Column(db.String(255), nullable=True)
    face_encoding = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    department = db.relationship("Department", back_populates="employees")
    attendances = db.relationship(
        "Attendance",
        back_populates="employee",
        cascade="all, delete-orphan",
        lazy=True,
    )


class Attendance(TimestampMixin, db.Model):
    __tablename__ = "attendance"
    __table_args__ = (
        db.UniqueConstraint("employee_id", "work_date", name="uq_employee_work_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False, index=True)
    work_date = db.Column(db.Date, nullable=False, index=True)
    check_in = db.Column(db.DateTime, nullable=True)
    check_out = db.Column(db.DateTime, nullable=True)
    worked_hours = db.Column(db.Float, default=0.0, nullable=False)
    is_late = db.Column(db.Boolean, default=False, nullable=False)
    note = db.Column(db.String(255), nullable=True)

    employee = db.relationship("Employee", back_populates="attendances")
