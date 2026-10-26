import shutil
from decimal import Decimal
from pathlib import Path

import psycopg
import pytest

from app.load_olist import LoadError, load, validate_files
from app.migrate import migrate

# Tiny synthetic CSVs with the real Olist headers and the quirks the loader must handle:
# a byte-order mark, misspelled product headers, quoted and unquoted empty fields,
# a multi-line review, a review_id shared by two orders, zip prefixes with leading zeros.
FIXTURE_DIR = Path(__file__).parent / "fixtures" / "olist_sample"

EXPECTED_COUNTS = {
    "product_category_translation": 2,
    "customers": 3,
    "sellers": 2,
    "products": 3,
    "orders": 3,
    "order_items": 4,
    "order_payments": 4,
    "order_reviews": 3,
    "geolocation": 3,
}


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    """A writable copy of the fixtures, so a test can break one file."""
    return Path(shutil.copytree(FIXTURE_DIR, tmp_path / "olist"))


@pytest.fixture
def migrated_conn(db_conn: psycopg.Connection) -> psycopg.Connection:
    migrate(db_conn)
    return db_conn


def table_counts(conn: psycopg.Connection) -> dict[str, int]:
    return {
        table: conn.execute(f"SELECT count(*) FROM olist.{table}").fetchone()[0]
        for table in EXPECTED_COUNTS
    }


# --- unit tests: no database needed ---


def test_fixture_files_are_valid() -> None:
    assert validate_files(FIXTURE_DIR) == []


def test_validate_reports_missing_file(data_dir: Path) -> None:
    (data_dir / "olist_orders_dataset.csv").unlink()
    problems = validate_files(data_dir)
    assert len(problems) == 1
    assert "missing file" in problems[0]
    assert "olist_orders_dataset.csv" in problems[0]


def test_validate_reports_wrong_header(data_dir: Path) -> None:
    (data_dir / "olist_sellers_dataset.csv").write_text("seller_id,city\ns1,campinas\n")
    problems = validate_files(data_dir)
    assert len(problems) == 1
    assert problems[0].startswith("olist_sellers_dataset.csv: header")


# --- integration tests: run against a throwaway database ---


@pytest.mark.db
def test_load_reports_counts_and_is_idempotent(migrated_conn: psycopg.Connection) -> None:
    assert load(migrated_conn, FIXTURE_DIR) == EXPECTED_COUNTS
    assert load(migrated_conn, FIXTURE_DIR) == EXPECTED_COUNTS
    assert table_counts(migrated_conn) == EXPECTED_COUNTS


@pytest.mark.db
def test_load_preserves_tricky_values(migrated_conn: psycopg.Connection) -> None:
    load(migrated_conn, FIXTURE_DIR)

    def one(query: str) -> tuple:
        return migrated_conn.execute(query).fetchone()

    # Leading zero kept; misspelled CSV header landed in the renamed column.
    assert one("SELECT customer_zip_code_prefix FROM olist.customers WHERE customer_id = 'c1'") == (
        "01037",
    )
    assert one("SELECT product_name_length FROM olist.products WHERE product_id = 'p1'") == (40,)
    # Quoted empty ("") and unquoted empty both became NULL.
    assert one(
        "SELECT order_approved_at, order_delivered_carrier_date FROM olist.orders "
        "WHERE order_id = 'o2'"
    ) == (None, None)
    assert one("SELECT review_comment_title FROM olist.order_reviews WHERE order_id = 'o2'") == (
        None,
    )
    # Multi-line, non-ASCII text survives intact.
    assert one("SELECT review_comment_message FROM olist.order_reviews WHERE review_id = 'r1'") == (
        "Não testei o produto ainda, mas ele veio correto.\nRecomendo!",
    )
    assert one("SELECT sum(price) FROM olist.order_items") == (Decimal("1377.68"),)


@pytest.mark.db
def test_failed_load_keeps_previous_data(migrated_conn: psycopg.Connection, data_dir: Path) -> None:
    load(migrated_conn, data_dir)
    # An order item pointing at a product that does not exist -> FK violation mid-load.
    # newline="\n": on Windows text mode would write "\r\n", and COPY rejects a file
    # that mixes line endings.
    items = data_dir / "olist_order_items_dataset.csv"
    with items.open("a", encoding="utf-8", newline="\n") as file:
        file.write("o3,2,p404,s2,2018-02-19 20:31:37,10.00,1.00\n")

    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        load(migrated_conn, data_dir)
    assert table_counts(migrated_conn) == EXPECTED_COUNTS


@pytest.mark.db
def test_load_rejects_invalid_files_before_touching_data(
    migrated_conn: psycopg.Connection, data_dir: Path
) -> None:
    load(migrated_conn, data_dir)
    (data_dir / "olist_geolocation_dataset.csv").unlink()

    with pytest.raises(LoadError, match="missing file"):
        load(migrated_conn, data_dir)
    assert table_counts(migrated_conn) == EXPECTED_COUNTS
