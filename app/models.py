"""Database models."""
from datetime import date

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from . import db, login_manager

EXPENSE_CATEGORIES = [
    "Food", "Transport", "Rent", "Utilities", "Shopping",
    "Health", "Education", "Entertainment", "Savings", "Other",
]
INCOME_CATEGORIES = ["Salary", "Allowance", "Freelance", "Gift", "Other"]


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    transactions = db.relationship(
        "Transaction", backref="user", cascade="all, delete-orphan")
    budgets = db.relationship(
        "Budget", backref="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    kind = db.Column(db.String(10), nullable=False)  # "income" | "expense"
    category = db.Column(db.String(40), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    on_date = db.Column(db.Date, nullable=False, default=date.today)
    note = db.Column(db.String(200), default="")

    @property
    def month(self):
        return self.on_date.strftime("%Y-%m")


class Budget(db.Model):
    __table_args__ = (
        db.UniqueConstraint("user_id", "category", name="uq_budget_user_cat"),
    )
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category = db.Column(db.String(40), nullable=False)
    monthly_limit = db.Column(db.Float, nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
