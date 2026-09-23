"""Loading, cleaning and exporting the Online Retail transactions."""

from __future__ import annotations

import io
import logging
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "online_retail.xlsx"
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "online_retail_clean.csv"

# Public source of the dataset (UCI Machine Learning Repository, CC BY 4.0).
UCI_DATASET_URL = "https://archive.ics.uci.edu/static/public/352/online+retail.zip"
UCI_ARCHIVE_MEMBER = "Online Retail.xlsx"

RAW_COLUMNS = [
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
]

# Identifiers are codes, not numbers: reading them as text keeps the "C" prefix
# of cancellations and alphanumeric stock codes such as "85123A".
_TEXT_COLUMNS = {"InvoiceNo": str, "StockCode": str, "Description": str, "Country": str}


def download_raw_data(path: Path = RAW_DATA_PATH, url: str = UCI_DATASET_URL) -> Path:
    """Download the raw Excel file from the UCI repository if it is not already present."""
    if path.exists():
        logger.info("Raw data already present at %s", path)
        return path

    logger.info("Downloading raw data from %s", url)
    with urllib.request.urlopen(url, timeout=120) as response:
        archive = zipfile.ZipFile(io.BytesIO(response.read()))

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(archive.read(UCI_ARCHIVE_MEMBER))
    return path


def load_raw_data(path: Path = RAW_DATA_PATH) -> pd.DataFrame:
    """Read the raw Excel export and apply consistent column types."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Raw data not found at {path}. Run `python -m online_retail` to download it, "
            "or place the Excel file there manually."
        )

    raw = pd.read_excel(path, dtype=_TEXT_COLUMNS)

    missing_columns = set(RAW_COLUMNS) - set(raw.columns)
    if missing_columns:
        raise ValueError(f"Unexpected file format, missing columns: {sorted(missing_columns)}")

    raw = raw[RAW_COLUMNS]
    raw["Description"] = raw["Description"].str.strip()
    raw["CustomerID"] = raw["CustomerID"].astype("Int64")
    return raw


def clean_transactions(raw: pd.DataFrame) -> pd.DataFrame:
    """Apply the business cleaning rules and compute line revenue.

    Rules from the business brief: keep lines with ``Quantity >= 1`` and
    ``UnitPrice >= 0``. This removes cancellations, returns and stock
    adjustments. Missing ``CustomerID`` values are kept because only the
    customer-level analysis needs them.
    """
    is_valid = (raw["Quantity"] >= 1) & (raw["UnitPrice"] >= 0)
    clean = raw.loc[is_valid].copy()
    clean["Revenue"] = clean["Quantity"] * clean["UnitPrice"]
    return clean.reset_index(drop=True)


def add_date_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add the calendar columns used by the notebooks and the Power BI report."""
    df = df.copy()
    df["Year"] = df["InvoiceDate"].dt.year
    df["Month"] = df["InvoiceDate"].dt.month
    df["Month_Name"] = df["InvoiceDate"].dt.month_name()
    df["Year_Month"] = df["InvoiceDate"].dt.to_period("M").astype(str)
    return df


def load_clean_data(path: Path = PROCESSED_DATA_PATH) -> pd.DataFrame:
    """Read the processed CSV produced by the cleaning step."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Processed data not found at {path}. Run `python -m online_retail` "
            "or notebook 01 first."
        )
    return pd.read_csv(
        path,
        parse_dates=["InvoiceDate"],
        dtype={**_TEXT_COLUMNS, "CustomerID": "Int64"},
    )


def build_clean_dataset(
    raw_path: Path = RAW_DATA_PATH, output_path: Path = PROCESSED_DATA_PATH
) -> pd.DataFrame:
    """Run the full pipeline: download if needed, load, clean, enrich and export."""
    download_raw_data(raw_path)
    raw = load_raw_data(raw_path)
    clean = add_date_features(clean_transactions(raw))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(output_path, index=False)
    logger.info(
        "Kept %s of %s rows (%s removed) -> %s",
        f"{len(clean):,}",
        f"{len(raw):,}",
        f"{len(raw) - len(clean):,}",
        output_path,
    )
    return clean
