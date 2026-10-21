"""Real-time UK Carbon Intensity dashboard.

Live data from the National Grid ESO Carbon Intensity API, refreshed on every load.
Run:     streamlit run app.py
Deploy:  push to GitHub -> share.streamlit.io -> app.py  (fetches live data online)
"""
from __future__ import annotations
import datetime as dt
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src import api, transform, insights

st.set_page_config(page_title="UK Carbon Intensity (live)", page_icon="⚡", layout="wide")

UK = ZoneInfo("Europe/London")   # show times in UK local time (GMT/BST)


@st.cache_data(ttl=300)  # cache live pulls for 5 minutes
def fetch():
    cur = transform.current_value(api.current_intensity())
    today = transform.intensity_series(api.intensity_today())
    gen = transform.generation_frame(api.generation_mix())
    return cur, today, gen, api.last_source()


st.title("⚡ UK Electricity Carbon Intensity — Live")
st.caption("Real-time data from the National Grid ESO Carbon Intensity API · "
           f"loaded {dt.datetime.now(UK):%Y-%m-%d %H:%M} UK time")

try:
    cur, today, gen, source = fetch()
except Exception as exc:  # pragma: no cover
    st.error(f"Could not load data: {exc}")
    st.stop()

if source == "live":
    st.success("🟢 Live data from the National Grid ESO Carbon Intensity API")
else:
    st.warning("🟠 Could not reach the API, so this is saved sample data. "
               "Check your internet connection and press Refresh in the sidebar.")

today = today.assign(time=today["time"].dt.tz_convert(UK))   # UTC -> UK time

col = st.columns(4)
now_val = cur["actual"] or cur["forecast"]
col[0].metric("Current intensity", f"{now_val} gCO₂/kWh", cur["index"].title())
col[1].metric("Renewable share", f"{insights.renewable_share(gen):.0f}%")
col[2].metric("Low-carbon share", f"{insights.low_carbon_share(gen):.0f}%")
gw = insights.greenest_window(today)
col[3].metric("Greenest time today", f"{gw['time']:%H:%M} UK", f"{gw['intensity']} gCO₂/kWh")

st.divider()
left, right = st.columns([3, 2])

with left:
    st.subheader("Today: forecast vs actual intensity")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=today["time"], y=today["forecast"],
                             name="Forecast", line=dict(dash="dash")))
    fig.add_trace(go.Scatter(x=today["time"], y=today["actual"],
                             name="Actual", line=dict(width=3)))
    fig.update_layout(yaxis_title="gCO₂/kWh", xaxis_title="", height=380,
                      legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, width="stretch")
    acc = insights.forecast_accuracy(today)
    if acc["mae"] is not None:
        st.caption(f"Forecast accuracy so far today: mean absolute error "
                   f"{acc['mae']} gCO₂/kWh across {acc['n']} settled periods.")

with right:
    st.subheader("Current generation mix")
    fig = px.pie(gen, values="perc", names="fuel", hole=0.45,
                 color="category",
                 color_discrete_map={"Renewable": "#2ecc71", "Nuclear": "#3498db",
                                     "Fossil": "#e74c3c", "Imports/Other": "#95a5a6"})
    fig.update_layout(height=380, legend=dict(orientation="v"))
    st.plotly_chart(fig, width="stretch")

st.divider()
s = insights.day_summary(today)
c1, c2, c3 = st.columns(3)
c1.metric("Today's average", f"{s['avg']} gCO₂/kWh")
c2.metric("Cleanest half-hour", f"{s['min']} gCO₂/kWh")
c3.metric("Dirtiest half-hour", f"{s['max']} gCO₂/kWh")

with st.expander("What this means"):
    st.markdown(
        "- **Carbon intensity** = grams of CO₂ emitted per kWh of electricity generated. "
        "Lower is greener.\n"
        "- Intensity falls when **wind and solar** are high and rises when the grid leans on **gas**.\n"
        "- Shifting flexible electricity use (EV charging, appliances) to the **greenest window** "
        "cuts emissions — the practical use-case behind this data.")

st.sidebar.title("⚡ Live UK Grid")
st.sidebar.write("Source: National Grid ESO Carbon Intensity API (no key required).")
if st.sidebar.button("🔄 Refresh now"):
    st.cache_data.clear()
    st.rerun()
st.sidebar.caption("Built by Jai Sooryah Gunaseelan · Python · Streamlit · Plotly")
