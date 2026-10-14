"""Vercel endpoint that provides fresh public TLEs for catalogued objects.

Only rows with a specific NORAD catalog number are requested. Generic debris
cloud labels intentionally have no live TLE: assigning one arbitrarily would
misrepresent the fragment's real position.
"""
import csv
import json
import time
from pathlib import Path
from http.server import BaseHTTPRequestHandler
from urllib.request import Request, urlopen

DATA = Path(__file__).parent.parent / "data" / "sample_events.csv"
CACHE_SECONDS = 2 * 60 * 60
_cache = {"at": 0, "data": {}}


def catalog_rows():
    with DATA.open(encoding="utf-8") as file:
        return [row for row in csv.DictReader(file) if row.get("norad_id")]


def tle_for(norad_id):
    url = "https://celestrak.org/NORAD/elements/gp.php?CATNR={}&FORMAT=TLE".format(norad_id)
    request = Request(url, headers={"User-Agent": "OrbitalGuard-Demo/1.0"})
    with urlopen(request, timeout=8) as response:
        lines = [line.strip() for line in response.read().decode("utf-8").splitlines() if line.strip()]
    line1 = next((line for line in lines if line.startswith("1 ")), None)
    line2 = next((line for line in lines if line.startswith("2 ")), None)
    if not line1 or not line2:
        raise ValueError("No usable TLE returned")
    return {"norad_id": norad_id, "tle1": line1, "tle2": line2, "retrieved_at": int(time.time())}


def live_orbits():
    if time.time() - _cache["at"] < CACHE_SECONDS:
        return _cache["data"]
    results = {}
    for row in catalog_rows():
        try:
            results[row["event_id"]] = tle_for(row["norad_id"])
        except Exception:
            # A temporary upstream outage leaves this object in the clearly
            # labelled simulated fallback state on the client.
            continue
    _cache.update({"at": time.time(), "data": results})
    return results


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({
            "orbits": live_orbits(),
            "source": "CelesTrak public GP/TLE data",
            "refresh_seconds": CACHE_SECONDS,
            "note": "Only objects with an exact NORAD ID have live propagated positions."
        }).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "public, max-age=300")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
