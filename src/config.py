from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
FIGURES_DIR = ROOT / "reports" / "figures"
API_BASE = "https://api.carbonintensity.org.uk"
REQUEST_TIMEOUT = 10          # seconds
CACHE_TTL = 300               # seconds (5 min) for live responses
