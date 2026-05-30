from flask import Flask, request, redirect, url_for, render_template_string, flash, session
import sqlite3
from contextlib import closing
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me-local-only")
DB_PATH = os.getenv("DB_PATH", "circle_events.db")

BASE_HTML = """
<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title }}</title>
  <style>
    :root {
      --bg: #f7f7fb;
      --card: #ffffff;
      --line: #dddde8;
      --text: #222;
      --muted: #666;
      --accent: #4f46e5;
      --accent2: #eef2ff;
      --danger: #b91c1c;
      --danger-bg: #fef2f2;
      --ok: #065f46;
      --ok-bg: #ecfdf5;
      --warn: #92400e;
      --warn-bg: #fffbeb;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    .container {
      width: min(1100px, calc(100% - 32px));
      margin: 32px auto;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      margin-bottom: 24px;
      flex-wrap: wrap;
    }
    .title {
      font-size: 28px;
      font-weight: 800;
      margin: 0;
    }
    .subtitle {
      color: var(--muted);
      margin-top: 6px;
    }
    .btn {
      display: inline-block;
      padding: 10px 16px;
      border-radius: 10px;
      text-decoration: none;
      border: 1px solid var(--accent);
      background: var(--accent);
      color: white;
      font-weight: 700;
      cursor: pointer;
      font: inherit;
    }
    .btn-secondary {
      background: white;
      color: var(--accent);
    }
    .btn-danger {
      background: white;
      color: var(--danger);
      border-color: #fca5a5;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 18px;
    }
    .detail-grid {
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 18px;
      align-items: start;
    }
    @media (max-width: 860px) {
      .detail-grid {
        grid-template-columns: 1fr;
      }
    }
    .card {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 18px;
      box-shadow: 0 4px 18px rgba(0,0,0,0.04);
    }
    .card h2, .card h3 {
      margin-top: 0;
      margin-bottom: 10px;
    }
    .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 12px 0;
    }
    .chip {
      background: var(--accent2);
      color: var(--accent);
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 14px;
      font-weight: 700;
    }
    .chip-ok {
      background: var(--ok-bg);
      color: var(--ok);
    }
    .chip-danger {
      background: var(--danger-bg);
      color: var(--danger);
    }
    .muted { color: var(--muted); }
    .danger { color: var(--danger); }
    .ok { color: var(--ok); }
    .notice {
      padding: 12px 14px;
      border-radius: 12px;
      background: var(--warn-bg);
      color: var(--warn);
      border: 1px solid #fcd34d;
      margin-bottom: 12px;
    }
    form {
      display: grid;
      gap: 14px;
    }
    label {
      display: grid;
      gap: 8px;
      font-weight: 700;
    }
    input, textarea, select {
      width: 100%;
      padding: 12px 14px;
      border-radius: 10px;
      border: 1px solid #cfd3df;
      background: white;
      font: inherit;
    }
    textarea {
      min-height: 120px;
      resize: vertical;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      background: white;
    }
    th, td {
      text-align: left;
      padding: 12px;
      border-bottom: 1px solid #e9e9f2;
      vertical-align: top;
    }
    .flash {
      padding: 12px 14px;
      border-radius: 10px;
      background: #ecfeff;
      border: 1px solid #a5f3fc;
      margin-bottom: 16px;
    }
    .section {
      margin-top: 24px;
    }
    .actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 16px;
      align-items: center;
    }
    .top-actions {
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
    }
    .inline-form {
      display: inline;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <h1 class="title"><a href="{{ url_for('index') }}" style="text-decoration:none;color:inherit;">Circle Event Board</a></h1>
        <div class="subtitle">イベント募集・参加表明・車出し確認をまとめて管理</div>
      </div>
      <div class="top-actions">
        {% if current_user %}
          <span class="muted">ログイン中: <strong>{{ current_user['username'] }}</strong></span>
          <a class="btn btn-secondary" href="{{ url_for('create_event') }}">+ イベントを作成</a>
          <a class="btn btn-danger" href="{{ url_for('logout') }}">ログアウト</a>
        {% else %}
          <a class="btn btn-secondary" href="{{ url_for('login') }}">ログイン</a>
          <a class="btn" href="{{ url_for('register') }}">新規登録</a>
        {% endif %}
      </div>
    </div>

    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for message in messages %}
          <div class="flash">{{ message }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    {{ body|safe }}
  </div>
</body>
</html>
"""

INDEX_BODY = """
<div class="grid">
  {% for event in events %}
    <div class="card">
      <h3>{{ event['title'] }}</h3>
      <div class="muted">日程: {{ event['event_date'] }}</div>
      <div class="muted">作成日: {{ event['created_at'] }}</div>
      <p>{{ event['summary']|replace('\n', '<br>')|safe }}</p>
      <div class="meta">
        {% if event['is_closed'] %}
          <span class="chip chip-danger">募集締切</span>
        {% else %}
          <span class="chip chip-ok">募集中</span>
        {% endif %}
        <span class="chip">参加 {{ event['participant_count'] }}人</span>
        <span class="chip">車の空き 合計 {{ event['total_seats'] }}人分</span>
        <span class="chip">車出し {{ event['driver_count'] }}人</span>
      </div>
      <div class="actions">
        <a class="btn" href="{{ url_for('event_detail', event_id=event['id']) }}">詳細を見る</a>
      </div>
    </div>
  {% else %}
    <div class="card">
      <h3>まだイベントがありません</h3>
      <p class="muted">まずは1件イベントを作成してみてください。</p>
    </div>
  {% endfor %}
</div>
"""

AUTH_BODY = """
<div class="card" style="max-width: 520px; margin: 0 auto;">
  <h2>{{ heading }}</h2>
  <form method="post">
    <label>
      ユーザー名
      <input name="username" required placeholder="例: 山田太郎 / 田中花子">
      {% if mode == 'register' %}
      <div class="muted" style="font-weight:400; font-size:13px;">
        ※ ユーザー名はイベント参加時に表示されます。本名での登録を推奨します。
      </div>
      {% endif %}
    </label>
    <label>
      パスワード
      <input type="password" name="password" required>
    </label>
    <button class="btn" type="submit">{{ button_label }}</button>
  </form>
  <div class="actions">
    {% if mode == 'login' %}
      <a class="btn btn-secondary" href="{{ url_for('register') }}">新規登録へ</a>
    {% else %}
      <a class="btn btn-secondary" href="{{ url_for('login') }}">ログインへ</a>
    {% endif %}
  </div>
</div>
"""

EVENT_FORM_BODY = """
<div class="card" style="max-width: 760px; margin: 0 auto;">
  <h2>{{ heading }}</h2>
  <form method="post">
    <label>
      イベント名
      <input name="title" required placeholder="例: 夏合宿1日目 / 新歓BBQ / 練習会" value="{{ event['title'] if event else '' }}">
    </label>
    <label>
      日程
      <input type="date" name="event_date" required value="{{ event['event_date'] if event else '' }}">
    </label>
    <label>
      概要
      <textarea name="summary" required placeholder="集合時間、場所、持ち物、費用など">{{ event['summary'] if event else '' }}</textarea>
    </label>
    <button class="btn" type="submit">{{ submit_label }}</button>
  </form>
</div>
"""

DETAIL_BODY = """
<div class="card">
  <h2>{{ event['title'] }}</h2>
  <div class="muted">日程: {{ event['event_date'] }}</div>
  <p>{{ event['summary']|replace('\n', '<br>')|safe }}</p>

  {% if current_user and event['created_by_user_id'] == current_user['id'] %}
  <div class="actions" style="margin-bottom: 12px;">
    <a class="btn btn-secondary" href="{{ url_for('edit_event', event_id=event['id']) }}">イベントを編集</a>

    <form method="post" action="{{ url_for('toggle_event_close', event_id=event['id']) }}" class="inline-form">
      {% if event['is_closed'] %}
        <button class="btn btn-secondary" type="submit">募集を再開</button>
      {% else %}
        <button class="btn btn-secondary" type="submit">募集を締め切る</button>
      {% endif %}
    </form>

    <form method="post" action="{{ url_for('delete_event', event_id=event['id']) }}" class="inline-form" onsubmit="return confirm('このイベントを削除します。参加表明もすべて消えます。よろしいですか？');">
      <button class="btn btn-danger" type="submit">イベントを削除</button>
    </form>
  </div>
  {% endif %}

  <div class="meta">
    {% if event['is_closed'] %}
      <span class="chip chip-danger">募集締切</span>
    {% else %}
      <span class="chip chip-ok">募集中</span>
    {% endif %}
    <span class="chip">参加 {{ stats['participant_count'] }}人</span>
    <span class="chip">車の空き 合計 {{ stats['total_seats'] }}人分</span>
    <span class="chip">車出し {{ stats['driver_count'] }}人</span>
  </div>
</div>

<div class="section detail-grid">
  <div class="card">
    <h3>参加者一覧</h3>
    <table>
      <thead>
        <tr>
          <th>名前</th>
          <th>参加状況</th>
          <th>車出し</th>
          <th>乗せられる人数</th>
          <th>コメント</th>
        </tr>
      </thead>
      <tbody>
        {% for p in participants %}
          <tr>
            <td>{{ p['username'] }}</td>
            <td>{{ p['status'] }}</td>
            <td>{% if p['can_drive'] %}<span class="ok">可</span>{% else %}<span class="muted">不可</span>{% endif %}</td>
            <td>{{ p['seat_count'] or 0 }}</td>
            <td>{{ p['comment'] or '' }}</td>
          </tr>
        {% else %}
          <tr>
            <td colspan="5" class="muted">まだ参加表明はありません。</td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <div class="card">
    {% if current_user %}
      {% if event['is_closed'] and not existing_response %}
        <h3>参加表明</h3>
        <p class="muted">このイベントの募集は締め切られています。</p>
      {% else %}
        <h3>{% if existing_response %}参加表明を更新{% else %}参加表明{% endif %}</h3>
        {% if event['is_closed'] %}
          <div class="notice">このイベントは募集締切済みです。既存の参加表明のみ更新できます。</div>
        {% endif %}
        <form method="post" action="{{ url_for('join_event', event_id=event['id']) }}">
          <label>
            ユーザー名
            <input value="{{ current_user['username'] }}" disabled>
          </label>
          <label>
            参加状況
            <select name="status" required>
              <option value="参加希望" {% if existing_response and existing_response['status'] == '参加希望' %}selected{% endif %}>参加希望</option>
              <option value="未定" {% if existing_response and existing_response['status'] == '未定' %}selected{% endif %}>未定</option>
              <option value="不参加" {% if existing_response and existing_response['status'] == '不参加' %}selected{% endif %}>不参加</option>
            </select>
          </label>
          <label>
            車出しできますか？
            <select name="can_drive" id="can_drive" onchange="toggleSeats()">
              <option value="0" {% if not existing_response or not existing_response['can_drive'] %}selected{% endif %}>できない</option>
              <option value="1" {% if existing_response and existing_response['can_drive'] %}selected{% endif %}>できる</option>
            </select>
          </label>
          <label id="seat_wrapper">
            何人乗せられるか
            <input type="number" name="seat_count" min="0" value="{{ existing_response['seat_count'] if existing_response else 0 }}">
          </label>
          <label>
            コメント
            <input name="comment" value="{{ existing_response['comment'] if existing_response and existing_response['comment'] else '' }}" placeholder="集合場所の希望など">
          </label>
          <button class="btn" type="submit">{% if existing_response %}更新する{% else %}送信する{% endif %}</button>
        </form>
      {% endif %}
    {% else %}
      <h3>参加表明にはログインが必要です</h3>
      <p class="muted">先にアカウントを作成してログインしてください。</p>
      <div class="actions">
        <a class="btn" href="{{ url_for('login') }}">ログイン</a>
        <a class="btn btn-secondary" href="{{ url_for('register') }}">新規登録</a>
      </div>
    {% endif %}
  </div>
</div>

<script>
function toggleSeats() {
  const canDrive = document.getElementById('can_drive');
  const wrapper = document.getElementById('seat_wrapper');
  if (!canDrive || !wrapper) return;
  wrapper.style.display = canDrive.value === '1' ? 'grid' : 'none';
}
toggleSeats();
</script>
"""


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with closing(get_db_connection()) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                event_date TEXT NOT NULL,
                summary TEXT NOT NULL,
                created_at TEXT NOT NULL,
                created_by_user_id INTEGER,
                is_closed INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (created_by_user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                can_drive INTEGER NOT NULL DEFAULT 0,
                seat_count INTEGER NOT NULL DEFAULT 0,
                comment TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(event_id, user_id),
                FOREIGN KEY (event_id) REFERENCES events(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            """
        )

        columns = [row[1] for row in conn.execute("PRAGMA table_info(events)").fetchall()]
        if "is_closed" not in columns:
            conn.execute("ALTER TABLE events ADD COLUMN is_closed INTEGER NOT NULL DEFAULT 0")

        conn.commit()


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    with closing(get_db_connection()) as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def require_login():
    if not session.get("user_id"):
        flash("この操作にはログインが必要です。")
        return False
    return True


def event_stats(conn, event_id: int):
    participant_count = conn.execute(
        "SELECT COUNT(*) FROM participants WHERE event_id = ? AND status = '参加希望'",
        (event_id,)
    ).fetchone()[0]
    total_seats = conn.execute(
        "SELECT COALESCE(SUM(seat_count), 0) FROM participants WHERE event_id = ? AND can_drive = 1 AND status = '参加希望'",
        (event_id,)
    ).fetchone()[0]
    driver_count = conn.execute(
        "SELECT COUNT(*) FROM participants WHERE event_id = ? AND can_drive = 1 AND status = '参加希望'",
        (event_id,)
    ).fetchone()[0]
    return {
        "participant_count": participant_count,
        "total_seats": total_seats,
        "driver_count": driver_count,
    }


def render_page(title, body):
    return render_template_string(BASE_HTML, title=title, body=body, current_user=current_user())


@app.route("/")
def index():
    with closing(get_db_connection()) as conn:
        events = conn.execute(
            "SELECT * FROM events ORDER BY event_date ASC, id DESC"
        ).fetchall()

        enriched_events = []
        for event in events:
            stats = event_stats(conn, event["id"])
            enriched_events.append({**dict(event), **stats})

    body = render_template_string(INDEX_BODY, events=enriched_events)
    return render_page("イベント一覧", body)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if len(username) < 2:
            flash("ユーザー名は2文字以上にしてください。")
            return redirect(url_for("register"))
        if len(password) < 4:
            flash("パスワードは4文字以上にしてください。")
            return redirect(url_for("register"))

        with closing(get_db_connection()) as conn:
            existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            if existing:
                flash("そのユーザー名はすでに使われています。")
                return redirect(url_for("register"))

            conn.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), datetime.now().strftime("%Y-%m-%d %H:%M"))
            )
            conn.commit()

        flash("アカウントを作成しました。ログインしてください。")
        return redirect(url_for("login"))

    body = render_template_string(AUTH_BODY, heading="新規登録", button_label="登録する", mode="register")
    return render_page("新規登録", body)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        with closing(get_db_connection()) as conn:
            user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("ユーザー名またはパスワードが違います。")
            return redirect(url_for("login"))

        session["user_id"] = user["id"]
        flash("ログインしました。")
        return redirect(url_for("index"))

    body = render_template_string(AUTH_BODY, heading="ログイン", button_label="ログインする", mode="login")
    return render_page("ログイン", body)


@app.route("/logout")
def logout():
    session.clear()
    flash("ログアウトしました。")
    return redirect(url_for("index"))


@app.route("/events/new", methods=["GET", "POST"])
def create_event():
    if not require_login():
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"].strip()
        event_date = request.form["event_date"]
        summary = request.form["summary"].strip()

        if not title or not event_date or not summary:
            flash("必須項目を入力してください。")
            return redirect(url_for("create_event"))

        with closing(get_db_connection()) as conn:
            conn.execute(
                "INSERT INTO events (title, event_date, summary, created_at, created_by_user_id) VALUES (?, ?, ?, ?, ?)",
                (title, event_date, summary, datetime.now().strftime("%Y-%m-%d %H:%M"), session["user_id"])
            )
            conn.commit()

        flash("イベントを作成しました。")
        return redirect(url_for("index"))

    body = render_template_string(EVENT_FORM_BODY, heading="イベントを作成", submit_label="作成する", event=None)
    return render_page("イベント作成", body)


@app.route("/events/<int:event_id>/edit", methods=["GET", "POST"])
def edit_event(event_id):
    if not require_login():
        return redirect(url_for("login"))

    with closing(get_db_connection()) as conn:
        event = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        if event is None:
            flash("イベントが見つかりません。")
            return redirect(url_for("index"))

        if event["created_by_user_id"] != session["user_id"]:
            flash("イベントを編集できるのは作成者のみです。")
            return redirect(url_for("event_detail", event_id=event_id))

        if request.method == "POST":
            title = request.form["title"].strip()
            event_date = request.form["event_date"]
            summary = request.form["summary"].strip()

            if not title or not event_date or not summary:
                flash("必須項目を入力してください。")
                return redirect(url_for("edit_event", event_id=event_id))

            conn.execute(
                "UPDATE events SET title = ?, event_date = ?, summary = ? WHERE id = ?",
                (title, event_date, summary, event_id)
            )
            conn.commit()
            flash("イベントを更新しました。")
            return redirect(url_for("event_detail", event_id=event_id))

    body = render_template_string(EVENT_FORM_BODY, heading="イベントを編集", submit_label="更新する", event=event)
    return render_page("イベント編集", body)


@app.route("/events/<int:event_id>")
def event_detail(event_id):
    cu = current_user()
    with closing(get_db_connection()) as conn:
        event = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        if event is None:
            flash("イベントが見つかりません。")
            return redirect(url_for("index"))

        participants = conn.execute(
            """
            SELECT p.*, u.username
            FROM participants p
            JOIN users u ON p.user_id = u.id
            WHERE p.event_id = ?
            ORDER BY
              CASE p.status WHEN '参加希望' THEN 0 WHEN '未定' THEN 1 ELSE 2 END,
              p.can_drive DESC,
              p.updated_at ASC,
              p.id ASC
            """,
            (event_id,)
        ).fetchall()
        stats = event_stats(conn, event_id)

        existing_response = None
        if cu:
            existing_response = conn.execute(
                "SELECT * FROM participants WHERE event_id = ? AND user_id = ?",
                (event_id, cu["id"])
            ).fetchone()

    body = render_template_string(
        DETAIL_BODY,
        event=event,
        participants=participants,
        stats=stats,
        current_user=cu,
        existing_response=existing_response,
    )
    return render_page(event["title"], body)


@app.route("/events/<int:event_id>/join", methods=["POST"])
def join_event(event_id):
    if not require_login():
        return redirect(url_for("login"))

    user_id = session["user_id"]
    status = request.form["status"]
    can_drive = int(request.form.get("can_drive", "0"))
    seat_count = int(request.form.get("seat_count", "0") or 0)
    comment = request.form.get("comment", "").strip()

    if can_drive == 0:
        seat_count = 0

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    with closing(get_db_connection()) as conn:
        event = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        if event is None:
            flash("イベントが見つかりません。")
            return redirect(url_for("index"))

        existing = conn.execute(
            "SELECT id FROM participants WHERE event_id = ? AND user_id = ?",
            (event_id, user_id)
        ).fetchone()

        if event["is_closed"] and existing is None:
            flash("このイベントの募集は締め切られています。")
            return redirect(url_for("event_detail", event_id=event_id))

        if existing:
            conn.execute(
                """
                UPDATE participants
                SET status = ?, can_drive = ?, seat_count = ?, comment = ?, updated_at = ?
                WHERE event_id = ? AND user_id = ?
                """,
                (status, can_drive, max(seat_count, 0), comment, now, event_id, user_id)
            )
            flash("参加表明を更新しました。")
        else:
            conn.execute(
                """
                INSERT INTO participants (event_id, user_id, status, can_drive, seat_count, comment, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (event_id, user_id, status, can_drive, max(seat_count, 0), comment, now, now)
            )
            flash("参加表明を受け付けました。")

        conn.commit()

    return redirect(url_for("event_detail", event_id=event_id))


@app.route("/events/<int:event_id>/toggle-close", methods=["POST"])
def toggle_event_close(event_id):
    if not require_login():
        return redirect(url_for("login"))

    with closing(get_db_connection()) as conn:
        event = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        if event is None:
            flash("イベントが見つかりません。")
            return redirect(url_for("index"))
        if event["created_by_user_id"] != session["user_id"]:
            flash("この操作ができるのは作成者のみです。")
            return redirect(url_for("event_detail", event_id=event_id))

        new_value = 0 if event["is_closed"] else 1
        conn.execute("UPDATE events SET is_closed = ? WHERE id = ?", (new_value, event_id))
        conn.commit()

    flash("募集を再開しました。" if new_value == 0 else "募集を締め切りました。")
    return redirect(url_for("event_detail", event_id=event_id))


@app.route("/events/<int:event_id>/delete", methods=["POST"])
def delete_event(event_id):
    if not require_login():
        return redirect(url_for("login"))

    with closing(get_db_connection()) as conn:
        event = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        if event is None:
            flash("イベントが見つかりません。")
            return redirect(url_for("index"))
        if event["created_by_user_id"] != session["user_id"]:
            flash("イベントを削除できるのは作成者のみです。")
            return redirect(url_for("event_detail", event_id=event_id))

        conn.execute("DELETE FROM participants WHERE event_id = ?", (event_id,))
        conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
        conn.commit()

    flash("イベントを削除しました。")
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
