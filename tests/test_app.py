from datetime import date


def add_tx(client, kind="expense", category="Food", amount="100", note=""):
    return client.post("/transactions", data={
        "kind": kind, "category": category, "amount": amount,
        "on_date": date.today().isoformat(), "note": note,
    }, follow_redirects=True)


def test_dashboard_requires_login(client):
    resp = client.get("/")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_register_login_logout(client):
    client.post("/register", data={"username": "ravi", "password": "secret123"})
    assert client.get("/").status_code == 200
    client.post("/logout")
    assert client.get("/").status_code == 302
    resp = client.post("/login", data={"username": "ravi", "password": "wrong"})
    assert b"Wrong username or password" in resp.data
    client.post("/login", data={"username": "ravi", "password": "secret123"})
    assert client.get("/").status_code == 200


def test_duplicate_username_rejected(client):
    client.post("/register", data={"username": "ravi", "password": "secret123"})
    client.post("/logout")
    resp = client.post("/register", data={"username": "ravi", "password": "secret123"})
    assert b"taken" in resp.data


def test_add_and_delete_transaction(auth_client):
    resp = add_tx(auth_client, amount="250", category="Transport")
    assert b"Transport" in resp.data
    assert auth_client.get("/api/summary").json["expense"] == 250
    auth_client.post("/transactions/1/delete")
    assert auth_client.get("/api/summary").json["expense"] == 0


def test_invalid_amount_rejected(auth_client):
    resp = add_tx(auth_client, amount="-5")
    assert b"greater than zero" in resp.data


def test_category_must_match_type(auth_client):
    resp = add_tx(auth_client, kind="income", category="Rent")
    assert b"matching category" in resp.data


def test_budget_alert_at_80_percent(auth_client):
    auth_client.post("/budgets", data={"category": "Food", "monthly_limit": "1000"})
    add_tx(auth_client, amount="800")
    data = auth_client.get("/api/summary").json
    assert data["budgets"][0]["level"] == "warning"
    assert any("Food" in a["text"] for a in data["alerts"])
    add_tx(auth_client, amount="300")
    assert auth_client.get("/api/summary").json["budgets"][0]["level"] == "exceeded"


def test_budget_is_updated_not_duplicated(auth_client):
    auth_client.post("/budgets", data={"category": "Food", "monthly_limit": "1000"})
    auth_client.post("/budgets", data={"category": "Food", "monthly_limit": "2000"})
    budgets = auth_client.get("/api/summary").json["budgets"]
    assert len(budgets) == 1 and budgets[0]["limit"] == 2000


def test_csv_export_and_formula_guard(auth_client):
    add_tx(auth_client, amount="42.5", note="=HYPERLINK(evil)")
    resp = auth_client.get("/export.csv")
    assert resp.mimetype == "text/csv"
    text = resp.data.decode()
    assert text.startswith("date,type,category,amount,note")
    assert "42.50" in text
    assert "'=HYPERLINK" in text


def test_users_cannot_see_each_others_data(app):
    a, b = app.test_client(), app.test_client()
    a.post("/register", data={"username": "alice", "password": "secret123"})
    add_tx(a, amount="999")
    b.post("/register", data={"username": "bob", "password": "secret123"})
    assert b.get("/api/summary").json["expense"] == 0
    assert b.post("/transactions/1/delete").status_code == 404


def test_health(client):
    assert client.get("/health").json == {"status": "ok"}
