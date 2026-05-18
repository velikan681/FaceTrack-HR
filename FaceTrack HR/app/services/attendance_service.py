from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError

from ..extensions import db
from ..models import Attendance
from ..utils import parse_time_string


def calculate_worked_hours(check_in, check_out) -> float:
    if not check_in or not check_out or check_out < check_in:
        return 0.0
    return round((check_out - check_in).total_seconds() / 3600, 2)


def mark_employee_attendance(employee, config: dict) -> dict:
    now = datetime.now()
    today = now.date()

    duplicate_interval = int(config.get("DUPLICATE_INTERVAL_MINUTES", 2))
    min_checkout_minutes = int(config.get("MIN_CHECKOUT_MINUTES", 30))
    late_after = parse_time_string(config.get("LATE_AFTER", "09:15"))

    try:
        record = Attendance.query.filter_by(
            employee_id=employee.id,
            work_date=today,
        ).first()

        if record is None:
            record = Attendance(
                employee_id=employee.id,
                work_date=today,
                check_in=now,
                is_late=now.time() > late_after,
            )
            db.session.add(record)
            db.session.commit()
            return {
                "ok": True,
                "action": "check_in",
                "message": f"{employee.full_name}: зафиксирован приход ({now.strftime('%H:%M:%S')}).",
                "record": record,
            }

        if record.check_out is None:
            # Defensive fallback: if old/corrupted row has no check_in, recover it.
            if record.check_in is None:
                record.check_in = now
                db.session.commit()
                return {
                    "ok": True,
                    "action": "check_in_recovered",
                    "message": (
                        f"{employee.full_name}: восстановлен check-in "
                        f"({now.strftime('%H:%M:%S')}) для некорректной записи."
                    ),
                    "record": record,
                }

            minutes_from_checkin = (now - record.check_in).total_seconds() / 60

            if minutes_from_checkin < duplicate_interval:
                return {
                    "ok": True,
                    "action": "duplicate",
                    "message": "Повторное сканирование слишком рано. Запись не изменена.",
                    "record": record,
                }

            if minutes_from_checkin < min_checkout_minutes:
                return {
                    "ok": True,
                    "action": "too_early_checkout",
                    "message": (
                        "Слишком рано для автоматического check-out. "
                        f"Минимальный интервал: {min_checkout_minutes} минут."
                    ),
                    "record": record,
                }

            record.check_out = now
            record.worked_hours = calculate_worked_hours(record.check_in, record.check_out)
            db.session.commit()
            return {
                "ok": True,
                "action": "check_out",
                "message": f"{employee.full_name}: зафиксирован уход ({now.strftime('%H:%M:%S')}).",
                "record": record,
            }

        minutes_from_checkout = (now - record.check_out).total_seconds() / 60
        if minutes_from_checkout < duplicate_interval:
            return {
                "ok": True,
                "action": "duplicate",
                "message": "Запись за сегодня уже закрыта. Повтор проигнорирован.",
                "record": record,
            }

        return {
            "ok": True,
            "action": "already_closed",
            "message": (
                "За сегодня уже есть приход и уход. "
                "Для простого MVP новая запись за тот же день не создается."
            ),
            "record": record,
        }
    except SQLAlchemyError as exc:
        db.session.rollback()
        return {
            "ok": False,
            "action": "db_error",
            "message": "Ошибка базы данных при записи посещаемости.",
            "error": str(exc),
        }
