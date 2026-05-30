"""Event management routes"""

from flask import Blueprint, request, redirect, url_for, render_template, flash, session, current_app
import app.models as models
from app.utils import event_stats, current_user

events_bp = Blueprint("events", __name__)


def require_login():
    """Check if user is logged in"""
    if not session.get("user_id"):
        flash("この操作にはログインが必要です。")
        return False
    return True


@events_bp.route("/")
def index():
    """List all events"""
    db_path = current_app.config["DB_PATH"]
    events = models.get_all_events(db_path)
    cu = current_user(db_path, session)
    
    enriched_events = []
    for event in events:
        stats = event_stats(db_path, event["id"])
        # Check if current user has already participated
        has_participated = models.has_user_participated(db_path, event["id"], cu["id"]) if cu else False
        enriched_events.append({**dict(event), **stats, "has_participated": has_participated})

    return render_template("index.html", events=enriched_events, current_user=cu)


@events_bp.route("/events/new", methods=["GET", "POST"])
def create_event():
    """Create a new event"""
    if not require_login():
        return redirect(url_for("auth.login"))

    db_path = current_app.config["DB_PATH"]

    if request.method == "POST":
        title = request.form["title"].strip()
        event_date = request.form["event_date"]
        summary = request.form["summary"].strip()
        recruitment_deadline = request.form.get("recruitment_deadline", "").strip() or None

        if not title or not event_date or not summary:
            flash("必須項目を入力してください。")
            return redirect(url_for("events.create_event"))

        models.create_event(db_path, title, event_date, summary, session["user_id"], recruitment_deadline)

        flash("イベントを作成しました。")
        return redirect(url_for("events.index"))

    cu = current_user(db_path, session)
    return render_template(
        "event_form.html",
        heading="イベントを作成",
        submit_label="作成する",
        event=None,
        current_user=cu
    )


@events_bp.route("/events/<int:event_id>/edit", methods=["GET", "POST"])
def edit_event(event_id):
    """Edit an event"""
    if not require_login():
        return redirect(url_for("auth.login"))

    db_path = current_app.config["DB_PATH"]
    event = models.get_event_by_id(db_path, event_id)

    if event is None:
        flash("イベントが見つかりません。")
        return redirect(url_for("events.index"))

    if event["created_by_user_id"] != session["user_id"]:
        flash("イベントを編集できるのは作成者のみです。")
        return redirect(url_for("events.event_detail", event_id=event_id))

    if request.method == "POST":
        title = request.form["title"].strip()
        event_date = request.form["event_date"]
        summary = request.form["summary"].strip()
        recruitment_deadline = request.form.get("recruitment_deadline", "").strip() or None

        if not title or not event_date or not summary:
            flash("必須項目を入力してください。")
            return redirect(url_for("events.edit_event", event_id=event_id))

        models.update_event(db_path, event_id, title, event_date, summary, recruitment_deadline)
        flash("イベントを更新しました。")
        return redirect(url_for("events.event_detail", event_id=event_id))

    cu = current_user(db_path, session)
    return render_template(
        "event_form.html",
        heading="イベントを編集",
        submit_label="更新する",
        event=event,
        current_user=cu
    )


@events_bp.route("/events/<int:event_id>")
def event_detail(event_id):
    """Show event details"""
    db_path = current_app.config["DB_PATH"]
    cu = current_user(db_path, session)

    event = models.get_event_by_id(db_path, event_id)
    if event is None:
        flash("イベントが見つかりません。")
        return redirect(url_for("events.index"))

    participants = models.get_event_participants(db_path, event_id)
    stats = event_stats(db_path, event_id)

    existing_response = None
    if cu:
        existing_response = models.get_user_participation(db_path, event_id, cu["id"])

    return render_template(
        "event_detail.html",
        event=event,
        participants=participants,
        stats=stats,
        current_user=cu,
        existing_response=existing_response,
    )


@events_bp.route("/events/<int:event_id>/join", methods=["POST"])
def join_event(event_id):
    """Join or update participation for an event"""
    if not require_login():
        return redirect(url_for("auth.login"))

    db_path = current_app.config["DB_PATH"]
    user_id = session["user_id"]
    status = request.form["status"]
    can_drive = int(request.form.get("can_drive", "0"))
    seat_count = int(request.form.get("seat_count", "0") or 0)
    comment = request.form.get("comment", "").strip()

    event = models.get_event_by_id(db_path, event_id)
    if event is None:
        flash("イベントが見つかりません。")
        return redirect(url_for("events.index"))

    existing = models.get_user_participation(db_path, event_id, user_id)

    if event["is_closed"] and existing is None:
        flash("このイベントの募集は締め切られています。")
        return redirect(url_for("events.event_detail", event_id=event_id))

    models.create_or_update_participation(
        db_path, event_id, user_id, status, can_drive, seat_count, comment
    )

    if existing:
        flash("参加表明を更新しました。")
    else:
        flash("参加表明を受け付けました。")

    return redirect(url_for("events.event_detail", event_id=event_id))


@events_bp.route("/events/<int:event_id>/toggle-close", methods=["POST"])
def toggle_event_close(event_id):
    """Toggle event close status"""
    if not require_login():
        return redirect(url_for("auth.login"))

    db_path = current_app.config["DB_PATH"]
    event = models.get_event_by_id(db_path, event_id)

    if event is None:
        flash("イベントが見つかりません。")
        return redirect(url_for("events.index"))

    if event["created_by_user_id"] != session["user_id"]:
        flash("この操作ができるのは作成者のみです。")
        return redirect(url_for("events.event_detail", event_id=event_id))

    new_value = models.toggle_event_close(db_path, event_id)

    flash("募集を再開しました。" if new_value == 0 else "募集を締め切りました。")
    return redirect(url_for("events.event_detail", event_id=event_id))


@events_bp.route("/events/<int:event_id>/delete", methods=["POST"])
def delete_event(event_id):
    """Delete an event"""
    if not require_login():
        return redirect(url_for("auth.login"))

    db_path = current_app.config["DB_PATH"]
    event = models.get_event_by_id(db_path, event_id)

    if event is None:
        flash("イベントが見つかりません。")
        return redirect(url_for("events.index"))

    if event["created_by_user_id"] != session["user_id"]:
        flash("イベントを削除できるのは作成者のみです。")
        return redirect(url_for("events.event_detail", event_id=event_id))

    models.delete_event(db_path, event_id)

    flash("イベントを削除しました。")
    return redirect(url_for("events.index"))


@events_bp.route("/my-history")
def my_history():
    """Show user's participation history and created events"""
    if not require_login():
        return redirect(url_for("auth.login"))

    db_path = current_app.config["DB_PATH"]
    cu = current_user(db_path, session)
    
    # Get ongoing participated events with stats (recruiting and user wants to participate)
    ongoing_events = models.get_user_ongoing_participated_events(db_path, cu["id"])
    ongoing_with_stats = []
    for event in ongoing_events:
        stats = event_stats(db_path, event["id"])
        ongoing_with_stats.append({**dict(event), **stats})
    
    # Get past participated events with stats (closed events user participated in)
    past_events = models.get_user_past_participated_events(db_path, cu["id"])
    past_with_stats = []
    for event in past_events:
        stats = event_stats(db_path, event["id"])
        past_with_stats.append({**dict(event), **stats})
    
    # Get created events with stats
    created_events = models.get_user_created_events(db_path, cu["id"])
    created_with_stats = []
    for event in created_events:
        stats = event_stats(db_path, event["id"])
        created_with_stats.append({**dict(event), **stats})

    return render_template(
        "history.html",
        ongoing_events=ongoing_with_stats,
        past_events=past_with_stats,
        created_events=created_with_stats,
        current_user=cu
    )
