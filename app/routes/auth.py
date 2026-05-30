"""Authentication routes"""

from flask import Blueprint, request, redirect, url_for, render_template, flash, session, current_app
from werkzeug.security import check_password_hash
import app.models as models

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """User registration"""
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        db_url = current_app.config["DATABASE_URL"]

        if len(username) < 2:
            flash("ユーザー名は2文字以上にしてください。")
            return redirect(url_for("auth.register"))
        if len(password) < 4:
            flash("パスワードは4文字以上にしてください。")
            return redirect(url_for("auth.register"))

        existing = models.get_user_by_username(db_url, username)
        if existing:
            flash("そのユーザー名はすでに使われています。")
            return redirect(url_for("auth.register"))

        models.create_user(db_url, username, password)

        flash("アカウントを作成しました。ログインしてください。")
        return redirect(url_for("auth.login"))

    return render_template(
        "auth.html",
        heading="新規登録",
        button_label="登録する",
        mode="register"
    )


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """User login"""
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        db_url = current_app.config["DATABASE_URL"]

        user = models.get_user_by_username(db_url, username)

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("ユーザー名またはパスワードが違います。")
            return redirect(url_for("auth.login"))

        session["user_id"] = user["id"]
        flash("ログインしました。")
        return redirect(url_for("events.index"))

    return render_template(
        "auth.html",
        heading="ログイン",
        button_label="ログインする",
        mode="login"
    )


@auth_bp.route("/logout")
def logout():
    """User logout"""
    session.clear()
    flash("ログアウトしました。")
    return redirect(url_for("events.index"))
