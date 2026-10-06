"""Train models to predict next-day max temperature (time-based split)."""
import json

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

DB_PATH = "weather.duckdb"
TARGET = "target_next_day_max"


def main():
    con = duckdb.connect(DB_PATH, read_only=True)
    df = con.execute("SELECT * FROM ml_features").df().dropna().sort_values("date")
    con.close()

    features = [c for c in df.columns if c not in ("date", TARGET)]
    split = int(len(df) * 0.8)  # chronological split, no shuffling -> no leakage
    train, test = df.iloc[:split], df.iloc[split:]
    X_tr, y_tr = train[features], train[TARGET]
    X_te, y_te = test[features], test[TARGET]

    models = {
        "Baseline (tomorrow = today)": None,
        "LinearRegression": LinearRegression(),
        "RandomForest": RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1),
    }

    results, preds = {}, {}
    for name, model in models.items():
        if model is None:
            p = X_te["temp_max"].values
        else:
            model.fit(X_tr, y_tr)
            p = model.predict(X_te)
        preds[name] = p
        results[name] = {
            "MAE": round(float(mean_absolute_error(y_te, p)), 3),
            "RMSE": round(float(np.sqrt(mean_squared_error(y_te, p))), 3),
        }
        print(f"{name:30s} MAE={results[name]['MAE']}  RMSE={results[name]['RMSE']}")

    with open("metrics.json", "w") as f:
        json.dump(results, f, indent=2)

    best = min((k for k in results if k != "Baseline (tomorrow = today)"),
               key=lambda k: results[k]["MAE"])
    plt.figure(figsize=(11, 4))
    plt.plot(test["date"].values, y_te.values, label="Actual", linewidth=1.5)
    plt.plot(test["date"].values, preds[best], label=f"Predicted ({best})", linewidth=1)
    plt.ylabel("Next-day max temp (°C)")
    plt.title("Heraklion: next-day max temperature, test set")
    plt.legend()
    plt.tight_layout()
    plt.savefig("predictions.png", dpi=120)
    print(f"Saved metrics.json and predictions.png (best model: {best})")


if __name__ == "__main__":
    main()
