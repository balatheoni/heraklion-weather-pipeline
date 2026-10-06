import duckdb
import pytest

DB_PATH = "weather.duckdb"


@pytest.fixture(scope="module")
def con():
    try:
        c = duckdb.connect(DB_PATH, read_only=True)
    except duckdb.IOException:
        pytest.skip("weather.duckdb not found - run `python ingestion.py` first")
    yield c
    c.close()


def test_table_not_empty(con):
    assert con.execute("SELECT COUNT(*) FROM raw_weather").fetchone()[0] > 365


def test_no_duplicate_dates(con):
    dupes = con.execute(
        "SELECT COUNT(*) FROM (SELECT date FROM raw_weather GROUP BY date HAVING COUNT(*) > 1)"
    ).fetchone()[0]
    assert dupes == 0


def test_clean_view_has_no_nulls_in_key_columns(con):
    nulls = con.execute(
        "SELECT COUNT(*) FROM clean_weather WHERE date IS NULL OR temp_max IS NULL OR temp_min IS NULL"
    ).fetchone()[0]
    assert nulls == 0


def test_temperatures_are_plausible(con):
    lo, hi = con.execute("SELECT MIN(temp_min), MAX(temp_max) FROM clean_weather").fetchone()
    assert -10 <= lo and hi <= 55


def test_min_not_greater_than_max(con):
    bad = con.execute("SELECT COUNT(*) FROM clean_weather WHERE temp_min > temp_max").fetchone()[0]
    assert bad == 0
