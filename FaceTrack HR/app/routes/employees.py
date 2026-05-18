import os

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError

from ..extensions import db
from ..models import Department, Employee
from ..services.face_service import create_face_encoding_from_file, save_employee_photo
from ..utils import allowed_file, login_required, safe_remove_file


employees_bp = Blueprint("employees", __name__, url_prefix="/employees")


@employees_bp.route("/")
@login_required
def list_employees():
    query_text = (request.args.get("q") or "").strip()

    query = Employee.query.outerjoin(Department, Department.id == Employee.department_id)
    if query_text:
        pattern = f"%{query_text}%"
        query = query.filter(
            or_(
                Employee.full_name.ilike(pattern),
                Employee.position.ilike(pattern),
                Employee.email.ilike(pattern),
                Department.name.ilike(pattern),
            )
        )

    employees = query.order_by(Employee.created_at.desc()).all()
    return render_template("employees/list.html", employees=employees, query_text=query_text)


@employees_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_employee():
    departments = Department.query.order_by(Department.name.asc()).all()

    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        position = (request.form.get("position") or "").strip()
        phone = (request.form.get("phone") or "").strip() or None
        email = (request.form.get("email") or "").strip() or None
        department_raw = (request.form.get("department_id") or "").strip()
        department_id = int(department_raw) if department_raw.isdigit() else None

        photo = request.files.get("photo")
        if not full_name or not position:
            flash("Заполните обязательные поля: ФИО и должность.", "warning")
            return render_template(
                "employees/form.html",
                employee=None,
                departments=departments,
                page_title="Добавить сотрудника",
            )

        if not photo or not photo.filename:
            flash("Для сотрудника обязательно загрузить фото лица.", "warning")
            return render_template(
                "employees/form.html",
                employee=None,
                departments=departments,
                page_title="Добавить сотрудника",
            )

        if not allowed_file(photo.filename, current_app.config["ALLOWED_IMAGE_EXTENSIONS"]):
            flash("Разрешены только изображения JPG, JPEG, PNG.", "warning")
            return render_template(
                "employees/form.html",
                employee=None,
                departments=departments,
                page_title="Добавить сотрудника",
            )

        stored_filename, photo_path = save_employee_photo(photo, current_app.config["UPLOAD_FOLDER"])
        encoding, encoding_error = create_face_encoding_from_file(photo_path)
        if encoding_error:
            safe_remove_file(photo_path)
            flash(encoding_error, "danger")
            return render_template(
                "employees/form.html",
                employee=None,
                departments=departments,
                page_title="Добавить сотрудника",
            )

        employee = Employee(
            full_name=full_name,
            department_id=department_id,
            position=position,
            phone=phone,
            email=email,
            photo_filename=stored_filename,
            face_encoding=encoding,
        )

        try:
            db.session.add(employee)
            db.session.commit()
            flash("Сотрудник успешно добавлен.", "success")
            return redirect(url_for("employees.list_employees"))
        except SQLAlchemyError as exc:
            db.session.rollback()
            safe_remove_file(photo_path)
            flash(f"Ошибка БД при добавлении сотрудника: {exc}", "danger")

    return render_template(
        "employees/form.html",
        employee=None,
        departments=departments,
        page_title="Добавить сотрудника",
    )


@employees_bp.route("/<int:employee_id>/edit", methods=["GET", "POST"])
@login_required
def edit_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    departments = Department.query.order_by(Department.name.asc()).all()

    if request.method == "POST":
        employee.full_name = (request.form.get("full_name") or "").strip()
        employee.position = (request.form.get("position") or "").strip()
        employee.phone = (request.form.get("phone") or "").strip() or None
        employee.email = (request.form.get("email") or "").strip() or None

        department_raw = (request.form.get("department_id") or "").strip()
        employee.department_id = int(department_raw) if department_raw.isdigit() else None

        if not employee.full_name or not employee.position:
            flash("Заполните обязательные поля: ФИО и должность.", "warning")
            return render_template(
                "employees/form.html",
                employee=employee,
                departments=departments,
                page_title="Редактировать сотрудника",
            )

        old_photo_path = None
        new_photo_path = None
        photo = request.files.get("photo")
        if photo and photo.filename:
            if not allowed_file(photo.filename, current_app.config["ALLOWED_IMAGE_EXTENSIONS"]):
                flash("Разрешены только изображения JPG, JPEG, PNG.", "warning")
                return render_template(
                    "employees/form.html",
                    employee=employee,
                    departments=departments,
                    page_title="Редактировать сотрудника",
                )

            stored_filename, new_photo_path = save_employee_photo(photo, current_app.config["UPLOAD_FOLDER"])
            encoding, encoding_error = create_face_encoding_from_file(new_photo_path)
            if encoding_error:
                safe_remove_file(new_photo_path)
                flash(encoding_error, "danger")
                return render_template(
                    "employees/form.html",
                    employee=employee,
                    departments=departments,
                    page_title="Редактировать сотрудника",
                )

            if employee.photo_filename:
                old_photo_path = os.path.join(current_app.config["UPLOAD_FOLDER"], employee.photo_filename)

            employee.photo_filename = stored_filename
            employee.face_encoding = encoding

        try:
            db.session.commit()
            safe_remove_file(old_photo_path)
            flash("Данные сотрудника обновлены.", "success")
            return redirect(url_for("employees.list_employees"))
        except SQLAlchemyError as exc:
            db.session.rollback()
            safe_remove_file(new_photo_path)
            flash(f"Ошибка БД при обновлении сотрудника: {exc}", "danger")

    return render_template(
        "employees/form.html",
        employee=employee,
        departments=departments,
        page_title="Редактировать сотрудника",
    )


@employees_bp.route("/<int:employee_id>/delete", methods=["POST"])
@login_required
def delete_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    photo_path = (
        os.path.join(current_app.config["UPLOAD_FOLDER"], employee.photo_filename)
        if employee.photo_filename
        else None
    )
    try:
        db.session.delete(employee)
        db.session.commit()
        safe_remove_file(photo_path)
        flash("Сотрудник удален.", "info")
    except SQLAlchemyError as exc:
        db.session.rollback()
        flash(f"Ошибка БД при удалении сотрудника: {exc}", "danger")

    return redirect(url_for("employees.list_employees"))
