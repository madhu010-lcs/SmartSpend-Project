from app.forecast import forecast_next_month, next_month_label


def test_no_data_returns_none():
    assert forecast_next_month({}) is None


def test_single_month_uses_last_value():
    result = forecast_next_month({"2026-10": 5000})
    assert result["month"] == "2026-11"
    assert result["amount"] == 5000


def test_rising_trend_is_extended():
    result = forecast_next_month({"2026-08": 1000, "2026-09": 2000, "2026-10": 3000})
    assert result["month"] == "2026-11"
    assert result["amount"] == 4000
    assert result["method"] == "linear regression"


def test_gap_month_counts_as_zero():
    # Aug 3000, Sep (no spending) 0, Oct 3000 -> flat-ish, never negative
    result = forecast_next_month({"2026-08": 3000, "2026-10": 3000})
    assert result["amount"] >= 0


def test_falling_trend_never_negative():
    result = forecast_next_month({"2026-08": 3000, "2026-09": 1000, "2026-10": 100})
    assert result["amount"] == 0


def test_year_rollover():
    assert next_month_label("2026-12") == "2027-01"
