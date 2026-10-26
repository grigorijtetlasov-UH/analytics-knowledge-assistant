"""Load the Olist CSV files into the `olist` schema.

Usage: uv run python -m app.load_olist [--data-dir data/olist]

Run `uv run python -m app.migrate` first. The load is idempotent: all olist tables are
truncated and refilled inside ONE transaction, so re-running gives the same result and a
failure halfway (bad row, FK violation) leaves the previous data untouched.
"""

import argparse
import csv
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import psycopg
from psycopg import sql

from app.db import connect

DEFAULT_DATA_DIR = Path("data/olist")
COPY_CHUNK_BYTES = 1024 * 1024


class LoadError(Exception):
    """The CSV files are missing or do not look like the Olist dataset."""


@dataclass(frozen=True)
class TableSpec:
    filename: str
    table: str
    # CSV header -> DB column, in CSV order. Equal names except for the typo fix in products.
    columns: dict[str, str]


def same_names(*names: str) -> dict[str, str]:
    return {name: name for name in names}


# Listed in foreign-key order: a table comes after every table it references.
TABLES: tuple[TableSpec, ...] = (
    TableSpec(
        "product_category_name_translation.csv",
        "product_category_translation",
        same_names("product_category_name", "product_category_name_english"),
    ),
    TableSpec(
        "olist_customers_dataset.csv",
        "customers",
        same_names(
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ),
    ),
    TableSpec(
        "olist_sellers_dataset.csv",
        "sellers",
        same_names("seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"),
    ),
    TableSpec(
        "olist_products_dataset.csv",
        "products",
        {
            "product_id": "product_id",
            "product_category_name": "product_category_name",
            "product_name_lenght": "product_name_length",
            "product_description_lenght": "product_description_length",
            "product_photos_qty": "product_photos_qty",
            "product_weight_g": "product_weight_g",
            "product_length_cm": "product_length_cm",
            "product_height_cm": "product_height_cm",
            "product_width_cm": "product_width_cm",
        },
    ),
    TableSpec(
        "olist_orders_dataset.csv",
        "orders",
        same_names(
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ),
    ),
    TableSpec(
        "olist_order_items_dataset.csv",
        "order_items",
        same_names(
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "shipping_limit_date",
            "price",
            "freight_value",
        ),
    ),
    TableSpec(
        "olist_order_payments_dataset.csv",
        "order_payments",
        same_names(
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_installments",
            "payment_value",
        ),
    ),
    TableSpec(
        "olist_order_reviews_dataset.csv",
        "order_reviews",
        same_names(
            "review_id",
            "order_id",
            "review_score",
            "review_comment_title",
            "review_comment_message",
            "review_creation_date",
            "review_answer_timestamp",
        ),
    ),
    TableSpec(
        "olist_geolocation_dataset.csv",
        "geolocation",
        # `id` is not listed: it is an identity column that Postgres fills in.
        same_names(
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng",
            "geolocation_city",
            "geolocation_state",
        ),
    ),
)


def read_header(path: Path) -> list[str]:
    # utf-8-sig strips a UTF-8 byte-order mark if the file starts with one.
    with path.open(encoding="utf-8-sig", newline="") as file:
        return next(csv.reader(file), [])


def validate_files(data_dir: Path) -> list[str]:
    """Return a list of problems (empty if every file exists with the expected header).
    Checking up front gives one clear message instead of a COPY error deep in the load."""
    problems: list[str] = []
    for spec in TABLES:
        path = data_dir / spec.filename
        if not path.is_file():
            problems.append(f"missing file: {path}")
            continue
        header = read_header(path)
        expected = list(spec.columns)
        if header != expected:
            problems.append(f"{spec.filename}: header {header}, expected {expected}")
    return problems


def copy_statement(spec: TableSpec) -> sql.Composed:
    columns = sql.SQL(", ").join(sql.Identifier(column) for column in spec.columns.values())
    # HEADER true: skip the first line (it may start with a byte-order mark; it is skipped
    #   whole, and validate_files has already checked it).
    # FORCE_NULL: in CSV format only an UNQUOTED empty field means NULL; this makes a quoted
    #   empty field ("") NULL too, so an empty timestamp or comment never becomes ''.
    return sql.SQL(
        "COPY olist.{table} ({columns}) FROM STDIN "
        "WITH (FORMAT csv, HEADER true, ENCODING 'UTF8', FORCE_NULL ({columns}))"
    ).format(table=sql.Identifier(spec.table), columns=columns)


def copy_file(cur: psycopg.Cursor, spec: TableSpec, path: Path) -> int:
    """Stream one CSV into its table with COPY (far faster than INSERTs: the geolocation
    file has ~1M rows). Return the number of rows loaded."""
    with path.open("rb") as file, cur.copy(copy_statement(spec)) as copy:
        while chunk := file.read(COPY_CHUNK_BYTES):
            copy.write(chunk)
    return cur.rowcount


def load(conn: psycopg.Connection, data_dir: Path) -> dict[str, int]:
    """Replace the contents of all olist tables with the CSVs in `data_dir`.
    Return row counts per table. `conn` must be in autocommit mode."""
    problems = validate_files(data_dir)
    if problems:
        raise LoadError("\n".join(problems))

    tables = sql.SQL(", ").join(sql.Identifier("olist", spec.table) for spec in TABLES)
    counts: dict[str, int] = {}
    with conn.transaction(), conn.cursor() as cur:
        # One TRUNCATE for all tables: FKs between them are satisfied without CASCADE
        # (CASCADE could silently empty tables added later that reference olist).
        # RESTART IDENTITY resets geolocation.id, so re-runs produce identical ids.
        cur.execute(sql.SQL("TRUNCATE {} RESTART IDENTITY").format(tables))
        for spec in TABLES:
            counts[spec.table] = copy_file(cur, spec, data_dir / spec.filename)
    # Refresh planner statistics: after a bulk load they are stale, which leads to bad
    # query plans for the first metrics queries.
    conn.execute(sql.SQL("ANALYZE {}").format(tables))
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    args = parser.parse_args()

    started = time.perf_counter()
    try:
        with connect(autocommit=True) as conn:
            counts = load(conn, args.data_dir)
    except LoadError as exc:
        print(f"cannot load Olist data:\n{exc}", file=sys.stderr)
        return 1
    for table, rows in counts.items():
        print(f"{table:<30} {rows:>9,}")
    print(f"loaded in {time.perf_counter() - started:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
