from datetime import date, datetime, time, timedelta

from app import create_app
from app.extensions import db
from app.models import Admin, Attendance, Department, Employee
from app.services.attendance_service import calculate_worked_hours


def seed_admin():
    admin = Admin.query.filter_by(username="admin").first()
    if admin:
        return admin

    admin = Admin(username="admin")
    admin.set_password("admin123")
    db.session.add(admin)
    db.session.commit()
    return admin


def seed_departments():
    names = ["IT", "HR", "Finance", "Security", "Operations"]
    existing = {department.name for department in Department.query.all()}
    for name in names:
        if name not in existing:
            db.session.add(Department(name=name))
    db.session.commit()


def seed_employees():
    employees_data = [
        {
            "full_name": "Ivan Petrov",
            "department_name": "IT",
            "position": "Python Developer",
            "phone": "+998901112233",
            "email": "ivan.petrov@example.com",
        },
        {
            "full_name": "Anna Smirnova",
            "department_name": "HR",
            "position": "HR Manager",
            "phone": "+998902224455",
            "email": "anna.smirnova@example.com",
        },
        {
            "full_name": "Dmitry Volkov",
            "department_name": "Finance",
            "position": "Financial Analyst",
            "phone": "+998903335577",
            "email": "dmitry.volkov@example.com",
        },
        {
            "full_name": "Olga Romanova",
            "department_name": "Operations",
            "position": "Operations Specialist",
            "phone": "+998904446688",
            "email": "olga.romanova@example.com",
        },
    ]

    department_map = {department.name: department for department in Department.query.all()}
    for row in employees_data:
        exists = Employee.query.filter_by(email=row["email"]).first()
        if exists:
            continue
        db.session.add(
            Employee(
                full_name=row["full_name"],
                department_id=department_map[row["department_name"]].id,
                position=row["position"],
                phone=row["phone"],
                email=row["email"],
                photo_filename=None,  # Demo users without images; add real photos in UI.
                face_encoding=None,
            )
        )
    db.session.commit()


def seed_attendance():
    if Attendance.query.count() > 0:
        return

    employees = Employee.query.order_by(Employee.id.asc()).all()
    if not employees:
        return

    today = date.today()
    for day_offset in range(1, 21):
        current_day = today - timedelta(days=day_offset)
        if current_day.weekday() >= 5:
            continue

        for employee in employees:
            # Deterministic "absence pattern" for predictable demo data.
            if (employee.id + day_offset) % 6 == 0:
                continue

            minute_shift = (employee.id * 3 + day_offset) % 35
            check_in_dt = datetime.combine(current_day, time(8, 50)) + timedelta(minutes=minute_shift)
            check_out_dt = check_in_dt + timedelta(hours=8, minutes=(employee.id + day_offset) % 45)

            record = Attendance(
                employee_id=employee.id,
                work_date=current_day,
                check_in=check_in_dt,
                check_out=check_out_dt,
                worked_hours=calculate_worked_hours(check_in_dt, check_out_dt),
                is_late=check_in_dt.time() > time(9, 15),
            )
            db.session.add(record)

    # Add one open attendance today for dashboard demo.
    first_employee = employees[0]
    if today.weekday() < 5:
        check_in_today = datetime.combine(today, time(9, 3))
        db.session.add(
            Attendance(
                employee_id=first_employee.id,
                work_date=today,
                check_in=check_in_today,
                check_out=None,
                worked_hours=0.0,
                is_late=False,
            )
        )

    db.session.commit()


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        seed_admin()
        seed_departments()
        seed_employees()
        seed_attendance()
        print("Database initialized successfully.")
        print("Admin credentials: admin / admin123")


if __name__ == "__main__":
    main()
