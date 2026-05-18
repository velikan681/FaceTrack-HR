from calendar import monthrange
from datetime import date, datetime, timedelta

from sqlalchemy import and_, func

from ..models import Attendance, Department, Employee


def _working_days_in_month(year: int, month: int) -> int:
    days_in_month = monthrange(year, month)[1]
    count = 0
    for day in range(1, days_in_month + 1):
        current = date(year, month, day)
        if current.weekday() < 5:
            count += 1
    return count


def _format_timedelta_hours(start_dt, end_dt) -> float:
    if not start_dt or not end_dt or end_dt < start_dt:
        return 0.0
    return round((end_dt - start_dt).total_seconds() / 3600, 2)


def get_dashboard_stats(target_date: date | None = None) -> dict:
    today = target_date or date.today()

    total_employees = Employee.query.filter_by(is_active=True).count()
    today_records = Attendance.query.filter_by(work_date=today).all()

    present_today = len(today_records)
    late_today = sum(1 for record in today_records if record.is_late)
    absent_today = max(total_employees - present_today, 0)

    recent_records = (
        Attendance.query.join(Employee)
        .filter(Attendance.work_date >= today - timedelta(days=7))
        .order_by(Attendance.work_date.desc(), Attendance.check_in.desc())
        .limit(12)
        .all()
    )

    month_start = date(today.year, today.month, 1)
    days_in_month = monthrange(today.year, today.month)[1]
    month_end = date(today.year, today.month, days_in_month)

    grouped_daily = (
        Attendance.query.with_entities(Attendance.work_date, func.count(Attendance.id))
        .filter(and_(Attendance.work_date >= month_start, Attendance.work_date <= month_end))
        .group_by(Attendance.work_date)
        .all()
    )
    counts_by_date = {row[0]: int(row[1]) for row in grouped_daily}

    trend_labels = []
    trend_values = []
    for day in range(1, days_in_month + 1):
        current = date(today.year, today.month, day)
        trend_labels.append(current.strftime("%d.%m"))
        trend_values.append(counts_by_date.get(current, 0))

    department_grouped = (
        Employee.query.with_entities(func.coalesce(Department.name, "Без отдела"), func.count(Employee.id))
        .outerjoin(Department, Department.id == Employee.department_id)
        .filter(Employee.is_active.is_(True))
        .group_by(func.coalesce(Department.name, "Без отдела"))
        .all()
    )

    department_labels = [row[0] for row in department_grouped]
    department_values = [int(row[1]) for row in department_grouped]

    return {
        "total_employees": total_employees,
        "present_today": present_today,
        "absent_today": absent_today,
        "late_today": late_today,
        "recent_records": recent_records,
        "trend_labels": trend_labels,
        "trend_values": trend_values,
        "department_labels": department_labels,
        "department_values": department_values,
    }


def build_daily_report(target_date: date, employee_id: int | None = None) -> dict:
    employee_query = Employee.query.filter_by(is_active=True)
    if employee_id:
        employee_query = employee_query.filter_by(id=employee_id)
    employees = employee_query.order_by(Employee.full_name.asc()).all()

    attendance_rows = Attendance.query.filter_by(work_date=target_date).all()
    attendance_by_employee = {row.employee_id: row for row in attendance_rows}

    report_rows = []
    for employee in employees:
        attendance = attendance_by_employee.get(employee.id)
        if not attendance:
            status = "Отсутствует"
            check_in = None
            check_out = None
            worked_hours = 0.0
            is_late = False
        else:
            status = "На работе" if attendance.check_in and not attendance.check_out else "Отработал(а)"
            check_in = attendance.check_in
            check_out = attendance.check_out
            worked_hours = (
                attendance.worked_hours
                if attendance.worked_hours
                else _format_timedelta_hours(attendance.check_in, attendance.check_out)
            )
            is_late = attendance.is_late

        report_rows.append(
            {
                "employee": employee,
                "status": status,
                "check_in": check_in,
                "check_out": check_out,
                "worked_hours": worked_hours,
                "is_late": is_late,
            }
        )

    return {"rows": report_rows, "date": target_date}


def build_monthly_report(year: int, month: int, employee_id: int | None = None) -> dict:
    start = date(year, month, 1)
    end_day = monthrange(year, month)[1]
    end = date(year, month, end_day)

    employee_query = Employee.query.filter_by(is_active=True)
    if employee_id:
        employee_query = employee_query.filter_by(id=employee_id)
    employees = employee_query.order_by(Employee.full_name.asc()).all()

    employee_ids = [employee.id for employee in employees]
    attendance_rows = []
    if employee_ids:
        attendance_rows = (
            Attendance.query.filter(
                and_(
                    Attendance.employee_id.in_(employee_ids),
                    Attendance.work_date >= start,
                    Attendance.work_date <= end,
                )
            )
            .order_by(Attendance.work_date.asc())
            .all()
        )

    stats = {
        employee.id: {
            "present_days": 0,
            "late_days": 0,
            "total_hours": 0.0,
            "open_sessions": 0,
        }
        for employee in employees
    }

    for record in attendance_rows:
        employee_stat = stats[record.employee_id]
        employee_stat["present_days"] += 1
        employee_stat["late_days"] += 1 if record.is_late else 0
        if record.check_out is None:
            employee_stat["open_sessions"] += 1
        employee_stat["total_hours"] += record.worked_hours or _format_timedelta_hours(
            record.check_in,
            record.check_out,
        )

    working_days = _working_days_in_month(year, month)
    rows = []
    for employee in employees:
        employee_stat = stats[employee.id]
        absences = max(working_days - employee_stat["present_days"], 0)
        rows.append(
            {
                "employee": employee,
                "present_days": employee_stat["present_days"],
                "late_days": employee_stat["late_days"],
                "absences": absences,
                "total_hours": round(employee_stat["total_hours"], 2),
                "open_sessions": employee_stat["open_sessions"],
            }
        )

    summary = {
        "working_days": working_days,
        "total_present_marks": sum(row["present_days"] for row in rows),
        "total_late_marks": sum(row["late_days"] for row in rows),
        "total_absences": sum(row["absences"] for row in rows),
        "total_hours": round(sum(row["total_hours"] for row in rows), 2),
    }

    return {
        "rows": rows,
        "summary": summary,
        "month_label": datetime(year, month, 1).strftime("%m.%Y"),
    }
