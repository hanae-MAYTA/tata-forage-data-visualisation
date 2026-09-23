import pandas as pd
import pytest

from online_retail import (
    add_date_features,
    clean_transactions,
    data_quality_summary,
    load_raw_data,
    monthly_revenue,
    net_revenue_by_customer,
    revenue_by_country,
    top_customers,
)


@pytest.fixture
def raw() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "InvoiceNo": ["1001", "1001", "C1002", "1003", "1004", "1005"],
            "StockCode": ["22633", "84029G", "22633", "POST", "21981", "85123A"],
            "Description": ["Mug", "Plate", "Mug", "POSTAGE", None, "Lamp"],
            "Quantity": [2, 1, -2, 1, 5, 10],
            "InvoiceDate": pd.to_datetime(
                [
                    "2011-01-05",
                    "2011-01-05",
                    "2011-01-06",
                    "2011-02-01",
                    "2011-02-02",
                    "2010-12-01",
                ]
            ),
            "UnitPrice": [3.0, 10.0, 3.0, 18.0, 0.0, 1.5],
            "CustomerID": pd.array([1, 1, 1, 2, pd.NA, 3], dtype="Int64"),
            "Country": ["France", "France", "France", "United Kingdom", "Spain", "Spain"],
        }
    )


def test_clean_transactions_applies_business_rules(raw):
    clean = clean_transactions(raw)

    assert (clean["Quantity"] >= 1).all()
    assert (clean["UnitPrice"] >= 0).all()
    assert "C1002" not in clean["InvoiceNo"].values
    # Missing CustomerID and zero-price lines are kept on purpose.
    assert clean["CustomerID"].isna().sum() == 1
    assert clean["Revenue"].tolist() == [6.0, 10.0, 18.0, 0.0, 15.0]


def test_add_date_features_does_not_modify_input(raw):
    enriched = add_date_features(raw)

    assert "Year" not in raw.columns
    assert enriched.loc[0, "Year_Month"] == "2011-01"
    assert enriched.loc[0, "Month_Name"] == "January"


def test_monthly_revenue_filters_on_year(raw):
    monthly = monthly_revenue(clean_transactions(raw), year=2011)

    assert monthly.index.tolist() == [1, 2]
    assert monthly.loc[1, "Revenue"] == 16.0
    assert monthly.loc[2, "Orders"] == 2


def test_revenue_by_country_excludes_uk_and_sorts(raw):
    by_country = revenue_by_country(clean_transactions(raw))

    assert "United Kingdom" not in by_country.index
    assert by_country.index.tolist() == ["France", "Spain"]
    assert by_country.loc["Spain", "Customers"] == 1


def test_top_customers_ignores_unknown_customers(raw):
    top = top_customers(clean_transactions(raw), n=2)

    assert top.index.tolist() == [2, 1]
    assert top["Revenue"].tolist() == [18.0, 16.0]


def test_net_revenue_nets_off_cancellations(raw):
    net = net_revenue_by_customer(raw)

    assert net.loc[1] == 10.0  # 6 + 10 - 6


def test_data_quality_summary_counts_issues(raw):
    summary = data_quality_summary(raw)

    assert summary.loc["Cancellation invoices (InvoiceNo starts with 'C')", "Rows"] == 1
    assert summary.loc["UnitPrice = 0", "Rows"] == 1
    assert summary.loc["Non-product lines (postage, fees, adjustments)", "Rows"] == 1


def test_load_raw_data_reports_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="python -m online_retail"):
        load_raw_data(tmp_path / "missing.xlsx")
