from types import SimpleNamespace as NS

from app.insights import alert_messages, budget_status


def _budget(limit):
    return NS(id=1, category="Food", monthly_limit=limit)


def test_levels():
    assert budget_status([_budget(1000)], {"Food": 500})[0]["level"] == "ok"
    assert budget_status([_budget(1000)], {"Food": 800})[0]["level"] == "warning"
    assert budget_status([_budget(1000)], {"Food": 1000})[0]["level"] == "exceeded"


def test_custom_threshold():
    assert budget_status([_budget(1000)], {"Food": 600}, threshold=0.5)[0]["level"] == "warning"


def test_alert_text():
    statuses = budget_status([_budget(1000)], {"Food": 1200})
    msgs = alert_messages(statuses)
    assert len(msgs) == 1 and msgs[0]["level"] == "danger"
    assert alert_messages(budget_status([_budget(1000)], {"Food": 10})) == []
