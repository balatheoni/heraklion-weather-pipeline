"""Extract + Load: Open-Meteo API -> DuckDB (idempotent), then run SQL transforms."""
from datetime import date, timedelta
from pathlib import Path

import duckdb
import pandas as pd
import requests

DB_PATH = "weather.duckdb"
API_URL = "https://archive-api.open-meteo.com/v1/archive"
LAT, LON = 35.34, 25.13  # Heraklion, Crete
YEARS = 5

DAILY_VARS = {
    "temperature_2m_max": "temp_max",
    "temperature_2m_min": "temp_min",
    "temperature_2m_mean": "temp_mean",
    "precipitation_sum": "precipitation",
    "wind_speed_10m_max": "wind_max",
    "shortwave_radiation_sum": "radiation",
}


def extract(start: date, end: date) -> pd.DataFrame:
    params = {
        "latitude": LAT,
        "longitude": LON,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": ",".join(DAILY_VARS),
        "timezone": "Europe/Athens",
    }
    resp = requests.get(API_URL, params=params, timeout=60)
    resp.raise_for_status()
    daily = resp.json()["daily"]
    df = pd.DataFrame(daily).rename(columns={"time": "date", **DAILY_VARS})
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df


def load(df: pd.DataFrame, db_path: str = DB_PATH) -> None:
    con = duckdb.connect(db_path)
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_weather (
            date DATE PRIMARY KEY,
            temp_max DOUBLE, temp_min DOUBLE, temp_mean DOUBLE,
            precipitation DOUBLE, wind_max DOUBLE, radiation DOUBLE
        )
        """
    )
    # Idempotent: re-running replaces rows with the same date instead of duplicating them
    con.register("incoming", df)
    con.execute(
        """
        INSERT OR REPLACE INTO raw_weather
        SELECT date, temp_max, temp_min, temp_mean, precipitation, wind_max, radiation
        FROM incoming
        """
    )
    n = con.execute("SELECT COUNT(*) FROM raw_weather").fetchone()[0]
    print(f"raw_weather now has {n} rows")
    con.execute(Path("transform.sql").read_text())
    con.close()


if __name__ == "__main__":
    end = date.today() - timedelta(days=7)  # archive data lags a few days
    start = end - timedelta(days=365 * YEARS)
    load(extract(start, end))
