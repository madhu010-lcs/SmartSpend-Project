"""Next-month spending forecast using linear regression."""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def next_month_label(month):
    """'2026-11' -> '2026-12'."""
    return str(pd.Period(month, freq="M") + 1)


def forecast_next_month(monthly_totals):
    """Predict the month after the latest one in ``monthly_totals``.

    ``monthly_totals`` maps 'YYYY-MM' -> total spent. Months with no
    spending between the first and last entry count as zero.

    Returns None when there is no data, otherwise a dict with the
    forecast month, the predicted amount and the method used.
    """
    if not monthly_totals:
        return None

    series = pd.Series(monthly_totals, dtype=float)
    series.index = pd.PeriodIndex(series.index, freq="M")
    series = series.sort_index()
    full_range = pd.period_range(series.index[0], series.index[-1], freq="M")
    series = series.reindex(full_range, fill_value=0.0)

    target = str(series.index[-1] + 1)

    if len(series) < 2:
        return {"month": target, "amount": round(float(series.iloc[0]), 2),
                "method": "last month (need 2+ months for a trend)"}

    x = np.arange(len(series)).reshape(-1, 1)
    model = LinearRegression().fit(x, series.values)
    predicted = float(model.predict([[len(series)]])[0])
    return {"month": target, "amount": round(max(predicted, 0.0), 2),
            "method": "linear regression"}
