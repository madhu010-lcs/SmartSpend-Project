"""Aggregations used by the dashboard and the API."""
from collections import defaultdict


def monthly_totals(transactions, kind):
    totals = defaultdict(float)
    for t in transactions:
        if t.kind == kind:
            totals[t.month] += t.amount
    return dict(totals)


def category_totals(transactions, month, kind="expense"):
    totals = defaultdict(float)
    for t in transactions:
        if t.kind == kind and t.month == month:
            totals[t.category] += t.amount
    return dict(totals)


def budget_status(budgets, spent_by_category, threshold=0.8):
    """One row per budget with percent used and a level.

    level: 'ok' below the threshold, 'warning' from the threshold up to
    the limit, 'exceeded' at or above the limit.
    """
    rows = []
    for b in budgets:
        spent = spent_by_category.get(b.category, 0.0)
        ratio = spent / b.monthly_limit if b.monthly_limit else 0.0
        if ratio >= 1:
            level = "exceeded"
        elif ratio >= threshold:
            level = "warning"
        else:
            level = "ok"
        rows.append({
            "id": b.id,
            "category": b.category,
            "limit": b.monthly_limit,
            "spent": round(spent, 2),
            "percent": round(ratio * 100, 1),
            "level": level,
        })
    rows.sort(key=lambda r: r["percent"], reverse=True)
    return rows


def alert_messages(statuses, currency="\u20b9"):
    messages = []
    for s in statuses:
        if s["level"] == "exceeded":
            over = s["spent"] - s["limit"]
            messages.append({
                "level": "danger",
                "text": (f"{s['category']}: over budget by {currency}{over:,.0f} "
                         f"({s['percent']:.0f}% of {currency}{s['limit']:,.0f})."),
            })
        elif s["level"] == "warning":
            left = s["limit"] - s["spent"]
            messages.append({
                "level": "warning",
                "text": (f"{s['category']}: {s['percent']:.0f}% used, "
                         f"{currency}{left:,.0f} left this month."),
            })
    return messages
