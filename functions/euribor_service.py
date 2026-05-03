from datetime import datetime
import requests


def fetch_euribor_rate() -> dict:
    """Fetch EURIBOR-like reference rate from ECB Data API.

    The ECB API can change or be unavailable. For MVP robustness, this function
    tries to retrieve a recent short-term euro area money-market rate and falls
    back to a manually editable default.
    """
    fallback = {"rate": 3.0, "source": "Fallback default", "date": datetime.today().date().isoformat()}
    url = "https://data-api.ecb.europa.eu/service/data/FM/M.U2.EUR.RT.MM.EURIBOR3MD_.HSTA?lastNObservations=1"
    headers = {"Accept": "text/csv"}
    try:
        response = requests.get(url, headers=headers, timeout=8)
        response.raise_for_status()
        lines = [line for line in response.text.splitlines() if line and not line.startswith("#")]
        if len(lines) < 2:
            return fallback
        header = lines[0].split(",")
        values = lines[-1].split(",")
        data = dict(zip(header, values))
        rate_value = data.get("OBS_VALUE")
        period = data.get("TIME_PERIOD", fallback["date"])
        if rate_value is None:
            return fallback
        return {"rate": float(rate_value), "source": "ECB Data API", "date": period}
    except Exception:
        return fallback
