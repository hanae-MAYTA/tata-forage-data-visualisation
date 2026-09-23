"""Command-line entry point: ``python -m online_retail`` rebuilds the clean dataset."""

import logging

from online_retail.data import build_clean_dataset

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    build_clean_dataset()
