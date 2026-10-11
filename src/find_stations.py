"""Stage 0: list Environment Agency rainfall and river stations near the study area."""
import requests

from config import CENTRE_LAT, CENTRE_LONG, SEARCH_RADIUS_KM

BASE = "https://environment.data.gov.uk/hydrology"


def list_stations(observed_property):
    params = {
        "observedProperty": observed_property,
        "lat": CENTRE_LAT,
        "long": CENTRE_LONG,
        "dist": SEARCH_RADIUS_KM,
        "_limit": 200,
    }
    response = requests.get(f"{BASE}/id/stations.json", params=params, timeout=60)
    response.raise_for_status()
    return response.json()["items"]


def status_label(station):
    status = station.get("status")
    if isinstance(status, list) and status:
        status = status[0]
    if isinstance(status, dict):
        label = status.get("label", "")
        return label[0] if isinstance(label, list) else label
    return ""


def show(title, stations):
    print(f"\n{title} ({len(stations)} found)")
    print(f"{'id':<40} {'name':<30} {'river':<22} {'opened':<12} status")
    for s in stations:
        print(
            f"{s.get('notation', ''):<40} {str(s.get('label', ''))[:29]:<30} "
            f"{str(s.get('riverName', ''))[:21]:<22} {str(s.get('dateOpened', ''))[:10]:<12} "
            f"{status_label(s)}"
        )


if __name__ == "__main__":
    show("RAINFALL stations", list_stations("rainfall"))
    show("RIVER FLOW stations", list_stations("waterFlow"))
    show("RIVER LEVEL stations", list_stations("waterLevel"))
    print(
        "\nPick one active rainfall station and one active river station that opened before "
        "your START_DATE, then paste their ids into src/config.py."
    )
