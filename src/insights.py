"""Derive human-readable insights from the parsed data."""
from __future__ import annotations
import pandas as pd
from . import transform


def renewable_share(gen_df: pd.DataFrame) -> float:
    """% of current generation from renewables (wind, solar, hydro, biomass)."""
    return float(gen_df.loc[gen_df["fuel"].isin(transform.RENEWABLE), "perc"].sum())


def low_carbon_share(gen_df: pd.DataFrame) -> float:
    """% from low-carbon sources (renewables + nuclear)."""
    return float(gen_df.loc[gen_df["fuel"].isin(transform.LOW_CARBON), "perc"].sum())


def greenest_window(intensity_df: pd.DataFrame) -> dict:
    """The half-hour today with the lowest (best available) intensity."""
    df = intensity_df.copy()
    df["value"] = df["actual"].fillna(df["forecast"])
    row = df.loc[df["value"].idxmin()]
    return {"time": row["time"], "intensity": int(row["value"]), "index": row["index"]}


def dirtiest_window(intensity_df: pd.DataFrame) -> dict:
    df = intensity_df.copy()
    df["value"] = df["actual"].fillna(df["forecast"])
    row = df.loc[df["value"].idxmax()]
    return {"time": row["time"], "intensity": int(row["value"]), "index": row["index"]}


def forecast_accuracy(intensity_df: pd.DataFrame) -> dict:
    """Mean absolute error between forecast and actual, where actual exists."""
    df = intensity_df.dropna(subset=["actual"])
    if df.empty:
        return {"mae": None, "n": 0}
    mae = (df["forecast"] - df["actual"]).abs().mean()
    return {"mae": round(float(mae), 1), "n": int(len(df))}


def day_summary(intensity_df: pd.DataFrame) -> dict:
    df = intensity_df.copy()
    df["value"] = df["actual"].fillna(df["forecast"])
    return {
        "avg": round(float(df["value"].mean()), 1),
        "min": int(df["value"].min()),
        "max": int(df["value"].max()),
    }
