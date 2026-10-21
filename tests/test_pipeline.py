"""Offline tests using the bundled real sample responses. Run: pytest -q"""
import json
from pathlib import Path
import pandas as pd
import pytest
from src import transform, insights, config


def load(name):
    return json.loads((config.DATA_DIR / name).read_text())


@pytest.fixture(scope="module")
def today():
    return transform.intensity_series(load("sample_intensity_date.json"))


@pytest.fixture(scope="module")
def gen():
    return transform.generation_frame(load("sample_generation.json"))


def test_intensity_series_shape(today):
    assert len(today) == 48
    assert list(today.columns) == ["time", "forecast", "actual", "index"]
    assert pd.api.types.is_datetime64_any_dtype(today["time"])


def test_generation_categories(gen):
    assert set(gen["category"]).issubset(
        {"Renewable", "Nuclear", "Fossil", "Imports/Other"})
    assert abs(gen["perc"].sum() - 100) < 5  # mix roughly sums to 100%


def test_renewable_share_in_range(gen):
    share = insights.renewable_share(gen)
    assert 0 <= share <= 100
    assert insights.low_carbon_share(gen) >= share  # low-carbon includes renewables


def test_greenest_is_min(today):
    gw = insights.greenest_window(today)
    dw = insights.dirtiest_window(today)
    assert gw["intensity"] <= dw["intensity"]


def test_forecast_accuracy_non_negative(today):
    acc = insights.forecast_accuracy(today)
    assert acc["n"] > 0 and acc["mae"] >= 0


def test_source_is_live_when_api_responds(monkeypatch):
    """A successful API response is marked as live data."""
    from src import api

    class FakeResp:
        def raise_for_status(self): pass
        def json(self): return load("sample_intensity.json")

    api._CACHE.clear(); api._SOURCE.clear()
    monkeypatch.setattr(api._SESSION, "get", lambda *a, **k: FakeResp())
    api.current_intensity()
    assert api.last_source() == "live"


def test_source_is_sample_when_api_fails(monkeypatch):
    """If every request fails, the bundled sample is used and flagged."""
    import requests
    from src import api

    def boom(*a, **k):
        raise requests.ConnectionError("offline")

    api._CACHE.clear(); api._SOURCE.clear()
    monkeypatch.setattr(api._SESSION, "get", boom)
    monkeypatch.setattr(api.time, "sleep", lambda s: None)
    payload = api.intensity_today()
    assert len(payload["data"]) == 48
    assert api.last_source() == "sample"
