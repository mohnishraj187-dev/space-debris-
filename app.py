import json, math, random, csv, io, zipfile, os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

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
    p=sum(y for _,y in rows)/len(rows); return 2*p*(1-p)

class Tree:
    def __init__(self, rows, rng, depth=0, max_depth=4):
        self.prob=sum(y for _,y in rows)/len(rows) if rows else 0
        self.leaf=True
        if depth >= max_depth or len(rows)<12 or self.prob in (0,1): return
        choices=rng.sample(FEATURES, 2); best=None
        for f in choices:
            vals=sorted({r[0][f] for r in rows})
            for t in vals[::max(1,len(vals)//12)]:
                left=[r for r in rows if r[0][f] <= t]; right=[r for r in rows if r[0][f] > t]
                if not left or not right: continue
                score=(len(left)*gini(left)+len(right)*gini(right))/len(rows)
                if best is None or score<best[0]: best=(score,f,t,left,right)
        if best:
            _,self.feature,self.threshold,left,right=best; self.left=Tree(left,rng,depth+1,max_depth); self.right=Tree(right,rng,depth+1,max_depth); self.leaf=False
    def predict(self,x):
        if self.leaf:return self.prob
        return (self.left if x[self.feature]<=self.threshold else self.right).predict(x)

class RandomForest:
    def __init__(self, n_trees=31, seed=11):
        data=make_data(); rng=random.Random(seed); self.trees=[]
        for _ in range(n_trees):
            sample=[data[rng.randrange(len(data))] for _ in data]; self.trees.append(Tree(sample,rng))
    def predict(self,x): return sum(t.predict(x) for t in self.trees)/len(self.trees)

MODEL=RandomForest()

DATA_ZIP=Path(__file__).parent/"data"/"Collision Avoidance Challenge - Dataset.zip"
INNER_TRAIN="Collision Avoidance Challenge - Dataset/kelvins_competition_data/train_data.zip"
def dataset_events(limit=30):
    events=[]
    if not DATA_ZIP.exists():
        sample=Path(__file__).parent/"data"/"sample_events.csv"
        if sample.exists():
            with sample.open() as f:
                for row in csv.DictReader(f): events.append(row)
        return events[:limit]
    with zipfile.ZipFile(DATA_ZIP) as outer:
        with outer.open(INNER_TRAIN) as nested_bytes:
            nested=zipfile.ZipFile(io.BytesIO(nested_bytes.read()))
            with nested.open("train_data.csv") as f:
                candidates=[]; first=[]
                seen=set()
                for row in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8")):
                    try:
                        if row["event_id"] in seen: continue
                        seen.add(row["event_id"])
                        item={"event_id":row["event_id"],"risk":row["risk"],"miss_distance":row["miss_distance"],"relative_speed":row["relative_speed"],"time_to_closest_approach":str(float(row["time_to_tca"])*86400),"uncertainty":row.get("t_sigma_r","0"),"hard_body_radius":"10"}
                        if len(first)<10: first.append(item)
                        candidates.append((float(row["risk"]),item))
                    except (ValueError, KeyError): pass
                events=first+[item for _,item in sorted(candidates,key=lambda pair: pair[0],reverse=True) if item not in first]
    demos=[{"event_id":"prototype-medium","risk":"demo", "miss_distance":"768","relative_speed":"15096","time_to_closest_approach":"86400","uncertainty":"600","hard_body_radius":"10"},{"event_id":"prototype-high","risk":"demo","miss_distance":"335","relative_speed":"14986","time_to_closest_approach":"3600","uncertainty":"600","hard_body_radius":"10"},{"event_id":"prototype-critical","risk":"demo","miss_distance":"101","relative_speed":"14576","time_to_closest_approach":"1800","uncertainty":"300","hard_body_radius":"10"}]
    return events[:max(0,limit-len(demos))]+demos

def analyze(x):
    p=MODEL.predict(x); physics=risk_proxy(x)
    combined=.65*p+.35*physics
    level="HIGH" if combined>=.55 else "MEDIUM" if combined>=.30 else "LOW"
    target=1000.0; required=max(0.0,target-x["miss_distance"])
    dt=max(60.0,x["time_to_closest_approach"])
    dv=max(.01,required/(2*dt)) if required else 0.0
    action="MONITOR" if not required or combined<.30 else "REVIEW MANEUVER"
    if level=="HIGH": suggestion="Prioritize immediate operator review; compare along-track, radial, and cross-track options before TCA."
    elif level=="MEDIUM": suggestion="Increase tracking frequency and prepare a low-Delta-V maneuver alternative."
    else: suggestion="Continue monitoring; no maneuver is suggested by this prototype."
    direction="along-track candidate" if level!="LOW" else "none"
    return {"ml_probability":round(p,4),"physics_score":round(physics,4),"combined_risk":round(combined,4),"risk_level":level,"required_separation_m":round(required,2),"estimated_delta_v_mps":round(dv,5),"action":action,"suggestion":suggestion,"direction":direction,"model":"31-tree Random Forest-style ensemble"}

HTML=Path(__file__).with_name("index.html").read_text()
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path=="/api/events":
            body=json.dumps(dataset_events()).encode(); self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body); return
        self.send_response(200); self.send_header("Content-Type","text/html"); self.end_headers(); self.wfile.write(HTML.encode())
    def do_POST(self):
        if self.path!="/api/analyze": self.send_error(404); return
        try:
            n=int(self.headers.get("Content-Length",0)); x=json.loads(self.rfile.read(n)); out=analyze({k:float(x[k]) for k in FEATURES})
            body=json.dumps(out).encode(); self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
        except Exception as e: self.send_error(400,str(e))
    def log_message(self,*args): pass

if __name__=="__main__":
    port=int(os.environ.get("PORT", "8000"))
    print(f"OrbitalGuard running on port {port}")
    HTTPServer(("0.0.0.0",port),Handler).serve_forever()
