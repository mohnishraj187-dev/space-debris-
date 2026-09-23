import json, csv, io, zipfile
from pathlib import Path
from http.server import BaseHTTPRequestHandler

DATA_ZIP = Path(__file__).parent.parent / "data" / "Collision Avoidance Challenge - Dataset.zip"
INNER_TRAIN = "Collision Avoidance Challenge - Dataset/kelvins_competition_data/train_data.zip"

def dataset_events(limit=30):
    events = []
    sample = Path(__file__).parent.parent / "data" / "sample_events.csv"
    if sample.exists():
        with sample.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                events.append({
                    "event_id": row.get("event_id", "OBJ-000"),
                    "name": row.get("name", "Space Object"),
                    "type": row.get("type", "DEBRIS"),
                    "altitude": row.get("altitude", "450"),
                    "velocity": row.get("velocity", "7.5"),
                    "inclination": row.get("inclination", "51.6"),
                    "risk": row.get("risk", "-5.0"),
                    "miss_distance": row.get("miss_distance", "1000"),
                    "relative_speed": row.get("relative_speed", "10000"),
                    "time_to_closest_approach": row.get("time_to_closest_approach", "86400"),
                    "uncertainty": row.get("uncertainty", "50"),
                    "hard_body_radius": row.get("hard_body_radius", "10"),
                    "status": row.get("status", "LOW")
                })
        return events[:limit]
    if DATA_ZIP.exists():
        with zipfile.ZipFile(DATA_ZIP) as outer:
            with outer.open(INNER_TRAIN) as nested_bytes:
                nested = zipfile.ZipFile(io.BytesIO(nested_bytes.read()))
                with nested.open("train_data.csv") as f:
                    candidates = []; first = []; seen = set()
                    for row in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8")):
                        try:
                            if row["event_id"] in seen: continue
                            seen.add(row["event_id"])
                            item = {
                                "event_id": "OBJ-" + row["event_id"],
                                "name": "Catalog Object #" + row["event_id"],
                                "type": "DEBRIS" if int(row["event_id"]) % 2 == 0 else "SATELLITE",
                                "altitude": str(400 + int(row["event_id"]) % 600),
                                "velocity": "7.6",
                                "inclination": "51.6",
                                "risk": row["risk"],
                                "miss_distance": row["miss_distance"],
                                "relative_speed": row["relative_speed"],
                                "time_to_closest_approach": str(float(row["time_to_tca"]) * 86400),
                                "uncertainty": row.get("t_sigma_r", "0"),
                                "hard_body_radius": "10",
                                "status": "MEDIUM" if float(row["risk"]) > -3 else "LOW"
                            }
                            if len(first) < 10: first.append(item)
                            candidates.append((float(row["risk"]), item))
                        except (ValueError, KeyError): pass
                    events = first + [item for _, item in sorted(candidates, key=lambda pair: pair[0], reverse=True) if item not in first]
        return events[:limit]
    return events

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        data = dataset_events()
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
