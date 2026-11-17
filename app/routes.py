"""Auth and main routes."""
import csv
import io
from datetime import date, datetime

from flask import (Blueprint, Response, current_app, flash, jsonify,
                   redirect, render_template, request, url_for)
from flask_login import current_user, login_required, login_user, logout_user

from . import db
from .forecast import forecast_next_month
from .insights import (alert_messages, budget_status, category_totals,
                       monthly_totals)
from .models import (EXPENSE_CATEGORIES, INCOME_CATEGORIES, Budget,
                     Transaction, User)

auth_bp = Blueprint("auth", __name__)
main_bp = Blueprint("main", __name__)


# ---------------------------------------------------------------- auth
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if len(username) < 3:
            flash("Username needs at least 3 characters.", "danger")
        elif len(password) < 6:
            flash("Password needs at least 6 characters.", "danger")
        elif User.query.filter_by(username=username).first():
            flash("That username is taken. Pick another.", "danger")
        else:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for("main.dashboard"))
    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        user = User.query.filter_by(
            username=request.form.get("username", "").strip()).first()
        if user and user.check_password(request.form.get("password", "")):
            login_user(user)
            return redirect(url_for("main.dashboard"))
        flash("Wrong username or password.", "danger")
    return render_template("login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


# ---------------------------------------------------------------- helpers
def _user_transactions():
    return (Transaction.query.filter_by(user_id=current_user.id)
            .order_by(Transaction.on_date.desc(), Transaction.id.desc()).all())


def _build_summary():
    """Everything the dashboard and /api/summary need."""
    txs = _user_transactions()
    this_month = date.today().strftime("%Y-%m")
    expenses_by_month = monthly_totals(txs, "expense")
    income_by_month = monthly_totals(txs, "income")
    spent_by_cat = category_totals(txs, this_month)

    budgets = Budget.query.filter_by(user_id=current_user.id).all()
    statuses = budget_status(
        budgets, spent_by_cat, current_app.config["ALERT_THRESHOLD"])

    months = sorted(set(expenses_by_month) | set(income_by_month))[-6:]
    forecast = forecast_next_month(expenses_by_month)

    return {
        "month": this_month,
        "income": round(income_by_month.get(this_month, 0.0), 2),
        "expense": round(expenses_by_month.get(this_month, 0.0), 2),
        "by_category": {k: round(v, 2) for k, v in spent_by_cat.items()},
        "monthly": {
            "labels": months,
            "income": [round(income_by_month.get(m, 0.0), 2) for m in months],
            "expense": [round(expenses_by_month.get(m, 0.0), 2) for m in months],
        },
        "forecast": forecast,
        "budgets": statuses,
        "alerts": alert_messages(statuses, current_app.config["CURRENCY"]),
        "recent": txs[:5],
    }


def _parse_amount(raw):
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


# ---------------------------------------------------------------- pages
@main_bp.route("/health")
def health():
    return jsonify(status="ok")


@main_bp.route("/")
@login_required
def dashboard():
    summary = _build_summary()
    chart_data = {
        "byCategory": summary["by_category"],
        "monthly": summary["monthly"],
        "forecast": summary["forecast"],
    }
    return render_template("dashboard.html", s=summary, chart_data=chart_data)


@main_bp.route("/transactions", methods=["GET", "POST"])
@login_required
def transactions():
    if request.method == "POST":
        kind = request.form.get("kind")
        category = request.form.get("category", "")
        amount = _parse_amount(request.form.get("amount"))
        valid = INCOME_CATEGORIES if kind == "income" else EXPENSE_CATEGORIES
        try:
            on_date = datetime.strptime(
                request.form.get("on_date", ""), "%Y-%m-%d").date()
        except ValueError:
            on_date = None

        if kind not in ("income", "expense") or category not in valid:
            flash("Choose a type and a matching category.", "danger")
        elif amount is None:
            flash("Enter an amount greater than zero.", "danger")
        elif on_date is None:
            flash("Enter a valid date.", "danger")
        else:
            db.session.add(Transaction(
                user_id=current_user.id, kind=kind, category=category,
                amount=amount, on_date=on_date,
                note=request.form.get("note", "").strip()[:200]))
            db.session.commit()
            flash(f"Added {kind}: {category}.", "success")
            return redirect(url_for("main.transactions"))

    return render_template(
        "transactions.html", items=_user_transactions(), today=date.today(),
        expense_categories=EXPENSE_CATEGORIES,
        income_categories=INCOME_CATEGORIES)


@main_bp.route("/transactions/<int:tx_id>/delete", methods=["POST"])
@login_required
def delete_transaction(tx_id):
    tx = Transaction.query.filter_by(id=tx_id, user_id=current_user.id).first_or_404()
    db.session.delete(tx)
    db.session.commit()
    flash("Transaction deleted.", "success")
    return redirect(url_for("main.transactions"))


@main_bp.route("/budgets", methods=["GET", "POST"])
@login_required
def budgets():
    if request.method == "POST":
        category = request.form.get("category", "")
        limit = _parse_amount(request.form.get("monthly_limit"))
        if category not in EXPENSE_CATEGORIES:
            flash("Choose an expense category.", "danger")
        elif limit is None:
            flash("Enter a limit greater than zero.", "danger")
        else:
            budget = Budget.query.filter_by(
                user_id=current_user.id, category=category).first()
            if budget:
                budget.monthly_limit = limit
            else:
                db.session.add(Budget(user_id=current_user.id,
                                      category=category, monthly_limit=limit))
            db.session.commit()
            flash(f"Budget saved for {category}.", "success")
            return redirect(url_for("main.budgets"))

    summary = _build_summary()
    return render_template("budgets.html", statuses=summary["budgets"],
                           categories=EXPENSE_CATEGORIES,
                           threshold=int(current_app.config["ALERT_THRESHOLD"] * 100))


@main_bp.route("/budgets/<int:budget_id>/delete", methods=["POST"])
@login_required
def delete_budget(budget_id):
    budget = Budget.query.filter_by(
        id=budget_id, user_id=current_user.id).first_or_404()
    db.session.delete(budget)
    db.session.commit()
    flash("Budget removed.", "success")
    return redirect(url_for("main.budgets"))


# ---------------------------------------------------------------- export + api
def _csv_safe(text):
    """Stop spreadsheet apps from running a note as a formula."""
    return "'" + text if text and text[0] in "=+-@" else text


@main_bp.route("/export.csv")
@login_required
def export_csv():
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["date", "type", "category", "amount", "note"])
    for t in reversed(_user_transactions()):
        writer.writerow([t.on_date.isoformat(), t.kind, t.category,
                         f"{t.amount:.2f}", _csv_safe(t.note or "")])
    return Response(
        buf.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=smartspend.csv"})


@main_bp.route("/api/summary")
@login_required
def api_summary():
    s = _build_summary()
    s.pop("recent")
    return jsonify(s)
