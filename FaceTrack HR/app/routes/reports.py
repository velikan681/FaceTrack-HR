from datetime import date, datetime

from flask import Blueprint, render_template, request

from ..models import Employee
from ..services.analytics_service import build_daily_report, build_monthly_report
from ..utils import login_required


reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("/")
@login_required
def index():
    today = date.today()

    selected_date_raw = (request.args.get("date") or today.isoformat()).strip()
    selected_month_raw = (request.args.get("month") or today.strftime("%Y-%m")).strip()
    employee_id_raw = (request.args.get("employee_id") or "").strip()

    try:
        selected_date = datetime.strptime(selected_date_raw, "%Y-%m-%d").date()
    except ValueError:
        selected_date = today

    try:
        selected_month = datetime.strptime(selected_month_raw, "%Y-%m")
        year, month = selected_month.year, selected_month.month
    except ValueError:
        year, month = today.year, today.month
        selected_month_raw = today.strftime("%Y-%m")

    employee_id = int(employee_id_raw) if employee_id_raw.isdigit() else None

    daily_report = build_daily_report(selected_date, employee_id)
    monthly_report = build_monthly_report(year, month, employee_id)
    employees = Employee.query.filter_by(is_active=True).order_by(Employee.full_name.asc()).all()

    return render_template(
        "reports/index.html",
        daily_report=daily_report,
        monthly_report=monthly_report,
        employees=employees,
        selected_date=selected_date.isoformat(),
        selected_month=selected_month_raw,
        selected_employee_id=employee_id,
    )
