import json, math, random
from http.server import BaseHTTPRequestHandler

FEATURES = ["miss_distance", "relative_speed", "time_to_closest_approach", "uncertainty", "hard_body_radius"]

def risk_proxy(x):
    d_norm = x["miss_distance"] / max(1.0, x["uncertainty"] + x["hard_body_radius"])
    proximity = math.exp(-0.5 * d_norm * d_norm)
    urgency = max(0.0, 1.0 - x["time_to_closest_approach"] / 86400.0)
    speed_factor = min(1.0, x["relative_speed"] / 12.0)
    return min(1.0, 0.72 * proximity + 0.18 * urgency + 0.10 * speed_factor)

def make_data(n=900, seed=7):
    rng = random.Random(seed); data=[]
    for _ in range(n):
        x = {"miss_distance": rng.uniform(20, 5000), "relative_speed": rng.uniform(.2, 15),
             "time_to_closest_approach": rng.uniform(900, 172800), "uncertainty": rng.uniform(5, 600),
             "hard_body_radius": rng.uniform(1, 30)}
        y = 1 if risk_proxy(x) >= .34 else 0
        data.append((x,y))
    return data

def gini(rows):
    if not rows: return 0
    p = sum(y for _, y in rows) / len(rows)
    return 2 * p * (1 - p)

class Tree:
    def __init__(self, rows, rng, depth=0, max_depth=4):
        self.prob = sum(y for _, y in rows) / len(rows) if rows else 0
        self.leaf = True
        if depth >= max_depth or len(rows) < 12 or self.prob in (0, 1): return
        choices = rng.sample(FEATURES, 2); best = None
        for f in choices:
            vals = sorted({r[0][f] for r in rows})
            for t in vals[::max(1, len(vals) // 12)]:
                left = [r for r in rows if r[0][f] <= t]; right = [r for r in rows if r[0][f] > t]
                if not left or not right: continue
                score = (len(left) * gini(left) + len(right) * gini(right)) / len(rows)
                if best is None or score < best[0]: best = (score, f, t, left, right)
        if best:
            _, self.feature, self.threshold, left, right = best
            self.left = Tree(left, rng, depth + 1, max_depth)
            self.right = Tree(right, rng, depth + 1, max_depth)
            self.leaf = False
    def predict(self, x):
        if self.leaf: return self.prob
        return (self.left if x[self.feature] <= self.threshold else self.right).predict(x)

class RandomForest:
    def __init__(self, n_trees=31, seed=11):
        data = make_data(); rng = random.Random(seed); self.trees = []
        for _ in range(n_trees):
            sample = [data[rng.randrange(len(data))] for _ in data]
            self.trees.append(Tree(sample, rng))
    def predict(self, x): return sum(t.predict(x) for t in self.trees) / len(self.trees)

MODEL = RandomForest()

def analyze(x):
    p = MODEL.predict(x); physics = risk_proxy(x)
    combined = .65 * p + .35 * physics
    level = "HIGH" if combined >= .55 else "MEDIUM" if combined >= .30 else "LOW"
    target = 1000.0; required = max(0.0, target - x["miss_distance"])
    dt = max(60.0, x["time_to_closest_approach"])
    dv = max(.01, required / (2 * dt)) if required else 0.0
    action = "MONITOR" if not required or combined < .30 else "REVIEW MANEUVER"
    if level == "HIGH":
        suggestion = "Escalate to flight dynamics now. Validate the latest conjunction data, evaluate an along-track avoidance option, and obtain operator approval before TCA."
        plan = [
            "Confirm the orbit solution, covariance, and TCA with an independent data source.",
            "Screen along-track, radial, and cross-track maneuver options against all tracked objects.",
            "Select a reversible, fuel-aware option and obtain human flight-operations approval.",
            "Reassess immediately after any maneuver and continue tracking through TCA."
        ]
    elif level == "MEDIUM":
        suggestion = "Increase tracking frequency and prepare a low-Delta-V maneuver alternative."
        plan = ["Refresh tracking data.", "Prepare a candidate maneuver for operator review.", "Reassess at the next conjunction update."]
    else:
        suggestion = "Continue monitoring; no maneuver is suggested by this prototype."
        plan = ["Continue routine tracking and reassess when new conjunction data arrives."]
    direction = "along-track candidate" if level != "LOW" else "none"
    return {
        "ml_probability": round(p, 4),
        "physics_score": round(physics, 4),
        "combined_risk": round(combined, 4),
        "risk_level": level,
        "required_separation_m": round(required, 2),
        "estimated_delta_v_mps": round(dv, 5),
        "action": action,
        "suggestion": suggestion,
        "direction": direction,
        "advisory_plan": plan,
        "advisory_disclaimer": "Decision support only — never execute a maneuver without validated operational data and qualified human approval.",
        "model": "31-tree Random Forest-style ensemble"
    }

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(length)
            x = json.loads(raw_body.decode("utf-8"))
            out = analyze({k: float(x[k]) for k in FEATURES})
            res_body = json.dumps(out).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(res_body)))
            self.end_headers()
            self.wfile.write(res_body)
        except Exception as e:
            self.send_error(400, str(e))
            
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
