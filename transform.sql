-- 1) Clean layer: drop incomplete / physically impossible rows
CREATE OR REPLACE VIEW clean_weather AS
SELECT *
FROM raw_weather
WHERE temp_max IS NOT NULL
  AND temp_min IS NOT NULL
  AND temp_max BETWEEN -10 AND 55
  AND temp_min <= temp_max;

-- 2) 7-day rolling averages (window function)
CREATE OR REPLACE VIEW rolling_weather AS
SELECT
    date,
    temp_max,
    AVG(temp_max) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS temp_max_7d_avg,
    SUM(precipitation) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS precip_7d_sum
FROM clean_weather;

-- 3) Monthly climatology
CREATE OR REPLACE VIEW monthly_climate AS
SELECT
    MONTH(date)                    AS month,
    ROUND(AVG(temp_max), 1)        AS avg_temp_max,
    ROUND(AVG(temp_min), 1)        AS avg_temp_min,
    ROUND(SUM(precipitation) / COUNT(DISTINCT YEAR(date)), 1) AS avg_monthly_precip_mm
FROM clean_weather
GROUP BY 1
ORDER BY 1;

-- 4) Heatwaves: 3+ consecutive days with temp_max >= 35C (gaps-and-islands technique)
CREATE OR REPLACE VIEW heatwaves AS
WITH hot AS (
    SELECT date, temp_max,
           date - CAST(ROW_NUMBER() OVER (ORDER BY date) AS INTEGER) AS grp
    FROM clean_weather
    WHERE temp_max >= 35
)
SELECT
    MIN(date)  AS start_date,
    MAX(date)  AS end_date,
    COUNT(*)   AS days,
    MAX(temp_max) AS peak_temp
FROM hot
GROUP BY grp
HAVING COUNT(*) >= 3
ORDER BY start_date;

-- 5) ML feature table (lags, rolling mean, seasonality, next-day target)
CREATE OR REPLACE VIEW ml_features AS
SELECT
    date,
    temp_max, temp_min, temp_mean, precipitation, wind_max, radiation,
    LAG(temp_max, 1) OVER w AS temp_max_lag1,
    LAG(temp_max, 2) OVER w AS temp_max_lag2,
    LAG(temp_max, 7) OVER w AS temp_max_lag7,
    AVG(temp_max) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS temp_max_roll7,
    MONTH(date)     AS month,
    DAYOFYEAR(date) AS day_of_year,
    LEAD(temp_max, 1) OVER w AS target_next_day_max
FROM clean_weather
WINDOW w AS (ORDER BY date);
