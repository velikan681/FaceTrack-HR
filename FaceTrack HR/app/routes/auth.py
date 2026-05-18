from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..models import Admin


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_id"):
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        admin = Admin.query.filter_by(username=username).first()
        if not admin or not admin.check_password(password):
            flash("Неверный логин или пароль.", "danger")
            return render_template("login.html")

        session["admin_id"] = admin.id
        session.permanent = True
        flash("Вы успешно вошли в систему.", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Вы вышли из системы.", "info")
    return redirect(url_for("auth.login"))
