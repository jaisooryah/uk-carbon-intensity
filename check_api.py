"""Quick check that your machine can reach the live National Grid API.

Run:  python check_api.py
"""
import requests

URL = "https://api.carbonintensity.org.uk/intensity"
try:
    r = requests.get(URL, timeout=10)
    r.raise_for_status()
    d = r.json()["data"][0]
    print("✅ Connected to the live API")
    print(f"   Period:   {d['from']} to {d['to']} (UTC)")
    print(f"   Forecast: {d['intensity']['forecast']} gCO2/kWh")
    print(f"   Actual:   {d['intensity']['actual']} gCO2/kWh ({d['intensity']['index']})")
except requests.RequestException as exc:
    print("❌ Could not reach the API:", exc)
    print("   Check your internet connection, VPN or firewall, then try again.")
