"""Parse Carbon Intensity API JSON into tidy pandas DataFrames."""
from __future__ import annotations
import pandas as pd

RENEWABLE = {"wind", "solar", "hydro", "biomass"}
LOW_CARBON = RENEWABLE | {"nuclear"}
FOSSIL = {"gas", "coal"}


def intensity_series(payload: dict) -> pd.DataFrame:
    """Half-hourly intensity payload -> DataFrame[time, forecast, actual, index]."""
    rows = []
    for d in payload["data"]:
        rows.append({
            "time": pd.to_datetime(d["from"]),
            "forecast": d["intensity"].get("forecast"),
            "actual": d["intensity"].get("actual"),
            "index": d["intensity"].get("index"),
        })
    df = pd.DataFrame(rows).sort_values("time").reset_index(drop=True)
    return df


def current_value(payload: dict) -> dict:
    d = payload["data"][0]
    return {
        "time": pd.to_datetime(d["from"]),
        "forecast": d["intensity"].get("forecast"),
        "actual": d["intensity"].get("actual"),
        "index": d["intensity"].get("index"),
    }


def generation_frame(payload: dict) -> pd.DataFrame:
    """Generation-mix payload -> DataFrame[fuel, perc, category] sorted desc."""
    mix = payload["data"]["generationmix"]
    df = pd.DataFrame(mix)
    df["category"] = df["fuel"].map(
        lambda f: "Renewable" if f in RENEWABLE
        else ("Nuclear" if f == "nuclear"
              else ("Fossil" if f in FOSSIL else "Imports/Other")))
    return df.sort_values("perc", ascending=False).reset_index(drop=True)
