import os
import json
import csv
import io
import sqlite3
import pathlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import List, Tuple
from flask_cors import CORS
import numpy as np
from flask import Flask, request, jsonify, send_from_directory, session
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash

# Optional deps used by /predict
try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    HAVE_STATSMODELS = True
except Exception:
    HAVE_STATSMODELS = False

# -------------------------
# App & config
# -------------------------
BASE_DIR = pathlib.Path(__file__).resolve().parent
DB_PATH = str(BASE_DIR / "app.db")

app = Flask(
    __name__,
    static_url_path="/static",
    static_folder=str(BASE_DIR / "static"),
)
CORS(app, supports_credentials=True)

# --- Session security hardening ---
# Strong secret key (env in prod; random fallback for dev)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)

# Size limits, cookie flags, etc.
app.config.update(
    MAX_CONTENT_LENGTH=int(os.getenv("MAX_CONTENT_LENGTH", "10000000")),  # 10MB
    SESSION_COOKIE_NAME="session",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    REMEMBER_COOKIE_HTTPONLY=True,
    REMEMBER_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),  # sliding 30-min window
    SESSION_REFRESH_EACH_REQUEST=True,
)

# Secure cookies when not in debug/testing (i.e., behind HTTPS in prod)
if not app.debug and not app.testing:
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        REMEMBER_COOKIE_SECURE=True,
    )

# -------------------------
# Auth (Flask-Login)
# -------------------------
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, id_, username, password_hash, role):
        self.id = id_
        self.username = username
        self.password_hash = password_hash
        self.role = role

    def get_id(self):
        return str(self.id)

def db_connect():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS forecast_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            predictions TEXT NOT NULL,
            mae REAL,
            mse REAL,
            r2 REAL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS anomaly_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            points_count INTEGER NOT NULL,
            anomalies_count INTEGER NOT NULL,
            method TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    conn.commit()

    # Seed default users if empty
    cur.execute("SELECT COUNT(*) FROM users")
    n = cur.fetchone()[0]
    if n == 0:
        cur.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
            ("admin", generate_password_hash("admin123"), "admin"),
        )
        cur.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
            ("user", generate_password_hash("user123"), "user"),
        )
        conn.commit()
    conn.close()

init_db()

@login_manager.user_loader
def load_user(user_id):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password_hash, role FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return User(*row)
    return None

# -------------------------
# Helpers
# -------------------------
def require_role(role: str):
    def wrapper(fn):
        from functools import wraps
        @wraps(fn)
        def inner(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "Authentication required"}), 401
            if getattr(current_user, "role", None) != role:
                return jsonify({"error": "Forbidden: requires role '%s'" % role}), 403
            return fn(*args, **kwargs)
        return inner
    return wrapper

def parse_sales_from_json(data) -> List[float]:
    if not data:
        return []
    if "sales" in data and isinstance(data["sales"], list):
        return [float(x) for x in data["sales"]]
    if "values" in data and isinstance(data["values"], list):
        return [float(x) for x in data["values"]]
    return []

def parse_sales_from_csv(file_storage) -> List[float]:
    # Accept "sales" column or a single-column CSV
    content = file_storage.read().decode("utf-8", errors="ignore")
    file_storage.seek(0)  # reset for safety
    f = io.StringIO(content)
    reader = csv.DictReader(f)
    sales = []
    if reader.fieldnames and "sales" in [c.strip().lower() for c in reader.fieldnames]:
        # Normalize column names
        lower_map = {c.strip().lower(): c for c in reader.fieldnames}
        sales_col = lower_map["sales"]
        for row in reader:
            if row.get(sales_col, "").strip() == "":
                continue
            sales.append(float(row[sales_col]))
        return sales
    # Try single-column without headers
    f.seek(0)
    reader2 = csv.reader(f)
    for row in reader2:
        if not row:
            continue
        try:
            sales.append(float(row[0]))
        except ValueError:
            # Skip header or bad row
            continue
    return sales

def detect_anomalies(values: List[float], method: str = "zscore", z_thresh: float = 3.0) -> Tuple[List[int], List[float]]:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return [], []
    if method == "zscore":
        mean = arr.mean()
        std = arr.std(ddof=0)
        if std == 0:
            return [], []
        z = (arr - mean) / std
        idx = np.where(np.abs(z) >= z_thresh)[0].tolist()
        return idx, arr[idx].tolist()
    # IQR fallback
    q1, q3 = np.percentile(arr, [25, 75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    idx = np.where((arr < lower) | (arr > upper))[0].tolist()
    return idx, arr[idx].tolist()

# -------------------------
# CSRF protection (double-submit header)
# -------------------------
CSRF_HEADER = "X-CSRF-Token"
EXEMPT_CSRF_PATHS = {"/", "/login", "/logout", "/healthz", "/swagger.yaml"}

def _csrf_exempt_path(path: str) -> bool:
    if path in EXEMPT_CSRF_PATHS:
        return True
    if path.startswith("/static/") or path.startswith("/docs"):
        return True
    return False

@app.before_request
def _enforce_csrf():
    # Only enforce for state-changing requests and when user is authenticated
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and not _csrf_exempt_path(request.path):
        # If not logged in, let @login_required handle it
        if not current_user.is_authenticated:
            return
        token = session.get("csrf_token")
        header = request.headers.get(CSRF_HEADER, "")
        if not token or header != token:
            return jsonify({"error": "CSRF validation failed"}), 403

# -------------------------
# Routes
# -------------------------
@app.route("/")
def home():
    return "Flask API is running."

@app.route("/healthz")
def healthz():
    return jsonify(status="ok", time=datetime.now(timezone.utc).isoformat())

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password_hash, role FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "invalid credentials"}), 401
    user = User(*row)
    if not check_password_hash(user.password_hash, password):
        return jsonify({"error": "invalid credentials"}), 401

    # Rotate session and set CSRF token
    session.clear()
    login_user(user)
    session.permanent = True
    session["csrf_token"] = secrets.token_urlsafe(32)

    # Include CSRF token in JSON and mirror in a readable cookie
    resp = jsonify({"message": "logged in", "username": user.username, "role": user.role, "csrf_token": session["csrf_token"]})
    resp.set_cookie(
        "XSRF-TOKEN",
        session["csrf_token"],
        secure=app.config.get("SESSION_COOKIE_SECURE", False),
        httponly=False,  # readable by JS to send header
        samesite=app.config.get("SESSION_COOKIE_SAMESITE", "Lax"),
    )
    return resp

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    resp = jsonify({"message": "logged out"})
    resp.delete_cookie("XSRF-TOKEN")
    return resp

@app.route("/predict", methods=["POST"])
@login_required
def predict():
    if not HAVE_STATSMODELS:
        return jsonify({"error": "statsmodels not installed on server"}), 500

    req = request.get_json(silent=True) or {}
    sales = parse_sales_from_json(req)
    if not sales:
        return jsonify({"error": "Missing sales data (use 'sales' or 'values' list)"}), 400

    sales_arr = np.asarray(sales, dtype=float)
    if sales_arr.size < 6:
        return jsonify({"error": "Need at least 6 points for forecasting (n-5 requires n≥6)"}), 400

    # Train/test split 80/20
    split = int(len(sales_arr) * 0.8)
    train, test = sales_arr[:split], sales_arr[split:]

    # Choose seasonal_periods conservatively
    seasonal_periods = min(12, max(2, len(train) // 2))
    try:
        model = ExponentialSmoothing(
            train, trend="add", seasonal="add", seasonal_periods=seasonal_periods
        ).fit(optimized=True)
    except Exception:
        model = ExponentialSmoothing(train, trend="add").fit(optimized=True)

    # Evaluate on holdout
    test_pred = model.forecast(len(test))
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score  # lazy import
    mae = float(mean_absolute_error(test, test_pred))
    mse = float(mean_squared_error(test, test_pred))
    r2 = float(r2_score(test, test_pred))

    # ---- horizon handling ----
    default_h = len(sales_arr) - 5  # keep your original default
    horizon = req.get("horizon", default_h)
    try:
        horizon = int(horizon)
    except Exception:
        return jsonify({"error": "horizon must be an integer"}), 400
    horizon = max(1, horizon)
    # soft cap to avoid runaway responses (≈ two seasons)
    horizon = min(horizon, 2 * seasonal_periods)

    # Refit on full series and forecast `horizon` steps
    try:
        full_model = ExponentialSmoothing(
            sales_arr, trend="add", seasonal="add", seasonal_periods=seasonal_periods
        ).fit(optimized=True)
    except Exception:
        full_model = ExponentialSmoothing(sales_arr, trend="add").fit(optimized=True)

    preds = full_model.forecast(horizon)
    preds_list = [float(x) for x in preds.tolist()]

    # Store history
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO forecast_history (user_id, created_at, predictions, mae, mse, r2)
        VALUES (?,?,?,?,?,?)
        """,
        (
            int(current_user.id),
            datetime.now(timezone.utc).isoformat(),
            json.dumps(preds_list),
            mae, mse, r2,
        ),
    )
    conn.commit()
    conn.close()

    return jsonify({"predictions": preds_list, "mae": mae, "mse": mse, "r2": r2})

@app.route("/detect_anomaly", methods=["POST"])
@login_required
def detect_anomaly():
    data = request.get_json(silent=True) or {}
    values = parse_sales_from_json(data)
    if not values:
        return jsonify({"error": "Missing sales/values list"}), 400
    idx, vals = detect_anomalies(values, method=data.get("method", "zscore"))
    # Store history
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO anomaly_history (user_id, created_at, points_count, anomalies_count, method)
        VALUES (?,?,?,?,?)
        """,
        (int(current_user.id), datetime.now(timezone.utc).isoformat(), len(values), len(idx), data.get("method", "zscore")),
    )
    conn.commit()
    conn.close()
    return jsonify({"indices": idx, "values": vals})

@app.route("/detect_anomaly_upload", methods=["POST"])
@login_required
def detect_anomaly_upload():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if not file.filename.lower().endswith(".csv"):
        return jsonify({"error": "Only CSV files allowed"}), 400
    values = parse_sales_from_csv(file)
    if not values:
        return jsonify({"error": "No numeric data found in CSV (expect 'sales' column or single numeric column)"}), 400
    idx, vals = detect_anomalies(values, method=request.form.get("method", "zscore"))
    # Store history
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO anomaly_history (user_id, created_at, points_count, anomalies_count, method)
        VALUES (?,?,?,?,?)
        """,
        (int(current_user.id), datetime.now(timezone.utc).isoformat(), len(values), len(idx), request.form.get("method", "zscore")),
    )
    conn.commit()
    conn.close()
    return jsonify({"indices": idx, "values": vals})

@app.route("/forecast_history", methods=["GET"])
@login_required
@require_role("admin")
def get_forecast_history():
    limit = int(request.args.get("limit", "50"))
    offset = int(request.args.get("offset", "0"))
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT fh.id, u.username, fh.created_at, fh.predictions, fh.mae, fh.mse, fh.r2
        FROM forecast_history fh
        JOIN users u ON u.id = fh.user_id
        ORDER BY fh.created_at DESC
        LIMIT ? OFFSET ?
        """,
        (limit, offset),
    )
    rows = cur.fetchall()
    conn.close()
    items = []
    for r in rows:
        items.append({
            "id": r[0],
            "username": r[1],
            "created_at": r[2],
            "predictions": json.loads(r[3]),
            "mae": r[4],
            "mse": r[5],
            "r2": r[6],
        })
    return jsonify({"items": items, "limit": limit, "offset": offset})

@app.route("/anomaly_history", methods=["GET"])
@login_required
@require_role("admin")
def get_anomaly_history():
    limit = int(request.args.get("limit", "50"))
    offset = int(request.args.get("offset", "0"))
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT ah.id, u.username, ah.created_at, ah.points_count, ah.anomalies_count, ah.method
        FROM anomaly_history ah
        JOIN users u ON u.id = ah.user_id
        ORDER BY ah.created_at DESC
        LIMIT ? OFFSET ?
        """,
        (limit, offset),
    )
    rows = cur.fetchall()
    conn.close()
    items = []
    for r in rows:
        items.append({
            "id": r[0],
            "username": r[1],
            "created_at": r[2],
            "points_count": r[3],
            "anomalies_count": r[4],
            "method": r[5],
        })
    return jsonify({"items": items, "limit": limit, "offset": offset})

# -------------------------
# Swagger UI
# -------------------------
try:
    from flask_swagger_ui import get_swaggerui_blueprint
    SWAGGER_URL = "/docs"
    API_URL = "/static/swagger.yaml"
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL, API_URL, config={"app_name": "Inventory Forecast API"}
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    @app.route("/swagger.yaml")
    def serve_swagger_yaml():
        return send_from_directory(app.static_folder, "swagger.yaml", mimetype="text/yaml")
except Exception:
    # Swagger is optional – app runs without it
    pass

@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({"error": "Authentication required"}), 401
# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=debug)
