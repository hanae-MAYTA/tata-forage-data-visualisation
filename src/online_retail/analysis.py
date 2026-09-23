"""Aggregations answering the business questions, plus data-quality checks."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

# Stock codes that are fees, postage or accounting entries rather than products.
NON_PRODUCT_STOCK_CODES = {
    "POST",
    "DOT",
    "C2",
    "M",
    "D",
    "S",
    "B",
    "BANK CHARGES",
    "AMAZONFEE",
    "CRUK",
}


def data_quality_summary(raw: pd.DataFrame) -> pd.DataFrame:
    """Count the main data-quality issues found in the raw transactions."""
    checks = {
        "Exact duplicate rows": raw.duplicated(),
        "Missing CustomerID": raw["CustomerID"].isna(),
        "Missing Description": raw["Description"].isna(),
        "Cancellation invoices (InvoiceNo starts with 'C')": raw["InvoiceNo"].str.startswith("C"),
        "Quantity < 1": raw["Quantity"] < 1,
        "UnitPrice < 0": raw["UnitPrice"] < 0,
        "UnitPrice = 0": raw["UnitPrice"] == 0,
        "Non-product lines (postage, fees, adjustments)": raw["StockCode"].isin(
            NON_PRODUCT_STOCK_CODES
        ),
    }
    summary = pd.DataFrame({"Rows": {name: int(mask.sum()) for name, mask in checks.items()}})
    summary["% of rows"] = (summary["Rows"] / len(raw) * 100).round(2)
    return summary


def monthly_revenue(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Revenue, orders and active days per month for a given year."""
    in_year = df[df["InvoiceDate"].dt.year == year]
    monthly = in_year.groupby(in_year["InvoiceDate"].dt.month).agg(
        Revenue=("Revenue", "sum"),
        Orders=("InvoiceNo", "nunique"),
        Trading_Days=("InvoiceDate", lambda dates: dates.dt.date.nunique()),
    )
    monthly.index.name = "Month"
    return monthly


def revenue_by_country(
    df: pd.DataFrame, exclude: Iterable[str] = ("United Kingdom",)
) -> pd.DataFrame:
    """Revenue, quantity and customer base per country, sorted by revenue."""
    subset = df[~df["Country"].isin(list(exclude))]
    by_country = subset.groupby("Country").agg(
        Revenue=("Revenue", "sum"),
        Quantity=("Quantity", "sum"),
        Customers=("CustomerID", "nunique"),
        Orders=("InvoiceNo", "nunique"),
    )
    return by_country.sort_values("Revenue", ascending=False)


def top_customers(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """The ``n`` identified customers generating the most revenue."""
    identified = df.dropna(subset=["CustomerID"])
    by_customer = identified.groupby("CustomerID").agg(
        Revenue=("Revenue", "sum"),
        Orders=("InvoiceNo", "nunique"),
        Country=("Country", "first"),
    )
    return by_customer.nlargest(n, "Revenue")


def net_revenue_by_customer(raw: pd.DataFrame) -> pd.Series:
    """Revenue per customer after netting off cancellations and returns."""
    identified = raw.dropna(subset=["CustomerID"])
    line_revenue = identified["Quantity"] * identified["UnitPrice"]
    return line_revenue.groupby(identified["CustomerID"]).sum().rename("Net_Revenue")
