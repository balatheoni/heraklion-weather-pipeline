# Heraklion Weather Mini-Pipeline

A small end-to-end data engineering project: **API → DuckDB → SQL transformations → ML → tests**.

```
Open-Meteo API ──► ingestion.py ──► DuckDB (raw_weather)
                                        │
                                  transform.sql  (clean view, rolling avgs,
                                        │         heatwave detection, ML features)
                                        ▼
                                    train.py ──► metrics.json + predictions.png
                                        ▲
                                 tests/test_quality.py (data quality)
```

## What it demonstrates
- **Extract/Load:** 5 years of daily weather for Heraklion from the free Open-Meteo API.
- **Idempotent loading:** `INSERT OR REPLACE` on a primary key, so re-running never duplicates data.
- **SQL:** CTEs, window functions (`LAG`, `LEAD`, rolling `AVG`), gaps-and-islands heatwave detection.
- **Data quality:** pytest checks for duplicates, nulls, plausible ranges.
- **ML:** next-day max temperature with a chronological train/test split, compared against a naive baseline.

## Run it
```bash
pip install -r requirements.txt
python ingestion.py      # download + load + build SQL views
pytest -q                # data quality tests
python train.py          # train & evaluate models
```

## Results
| Model | MAE (°C) | RMSE (°C) |
|---|---|---|
| Baseline (tomorrow = today) | _fill in_ | _fill in_ |
| LinearRegression | _fill in_ | _fill in_ |
| RandomForest | _fill in_ | _fill in_ |

![predictions](predictions.png)

## Explore with SQL
```bash
python -c "import duckdb; print(duckdb.connect('weather.duckdb').sql('SELECT * FROM heatwaves').df())"
```

