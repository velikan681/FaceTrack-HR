from flask import Blueprint, current_app, jsonify, render_template, request, url_for

from ..models import Employee
from ..services.attendance_service import mark_employee_attendance
from ..services.face_service import is_face_library_available, recognize_from_data_url
from ..utils import login_required


attendance_bp = Blueprint("attendance", __name__, url_prefix="/attendance")


@attendance_bp.route("/")
@login_required
def attendance_page():
    face_available, face_error = is_face_library_available()
    return render_template(
        "attendance/live.html",
        face_available=face_available,
        face_error=face_error,
    )


@attendance_bp.route("/recognize", methods=["POST"])
@login_required
def recognize_and_mark():
    face_available, face_error = is_face_library_available()
    if not face_available:
        return jsonify({"status": "error", "message": face_error}), 503

    payload = request.get_json(silent=True) or {}
    data_url = payload.get("image")
    if not data_url:
        return jsonify({"status": "error", "message": "Пустой кадр с камеры."}), 400

    employees = Employee.query.filter(
        Employee.is_active.is_(True),
        Employee.face_encoding.isnot(None),
    ).all()

    if not employees:
        return jsonify(
            {
                "status": "error",
                "message": "Нет сотрудников с face-encoding. Сначала добавьте сотрудников с фото.",
            }
        )

    recognition = recognize_from_data_url(
        data_url=data_url,
        employees=employees,
        tolerance=current_app.config["RECOGNITION_TOLERANCE"],
    )

    if recognition["status"] != "recognized":
        return jsonify(recognition)

    employee = recognition["employee"]
    attendance_result = mark_employee_attendance(employee, current_app.config)
    if not attendance_result["ok"]:
        return jsonify(
            {
                "status": "error",
                "message": attendance_result["message"],
            }
        ), 500

    photo_url = (
        url_for("static", filename=f"uploads/{employee.photo_filename}")
        if employee.photo_filename
        else None
    )
    return jsonify(
        {
            "status": "recognized",
            "message": attendance_result["message"],
            "action": attendance_result["action"],
            "employee": {
                "id": employee.id,
                "full_name": employee.full_name,
                "position": employee.position,
                "department": employee.department.name if employee.department else "Без отдела",
                "photo_url": photo_url,
            },
            "confidence": recognition.get("confidence"),
            "distance": recognition.get("distance"),
        }
    )
