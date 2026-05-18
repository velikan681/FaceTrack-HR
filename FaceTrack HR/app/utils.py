import os
from datetime import datetime, time
from functools import wraps

from flask import flash, redirect, session, url_for


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Войдите в систему, чтобы продолжить.", "warning")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)

    return wrapped_view


def allowed_file(filename: str, allowed_extensions: set[str]) -> bool:
    if "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in allowed_extensions


def parse_time_string(value: str, default_value: time = time(9, 15)) -> time:
    try:
        return datetime.strptime(value, "%H:%M").time()
    except (TypeError, ValueError):
        return default_value


def safe_remove_file(path: str | None) -> None:
    if not path:
        return
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        # Deleting old files should not break business logic.
        pass
