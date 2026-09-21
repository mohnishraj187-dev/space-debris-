# IDP Project Chat Summary

## Project

AI-assisted Space Situational Awareness and Collision Avoidance for satellites. The prototype combines conjunction-risk prediction, physics-based analysis, maneuver recommendation, and a 3D event showcase.

## Dataset

The selected dataset is the ESA Spacecraft Collision Avoidance Challenge dataset from Zenodo record 4463683.

Local downloaded file:

```text
/home/mohnish/Downloads/lo.zip
```

It contains ESA Conjunction Data Messages from 2015–2019, including training/test data, raw data, event IDs, risk, miss distance, relative speed, time to closest approach, relative position/velocity, and uncertainty-related fields.

## Prototype files

```text
/home/mohnish/idp_space_safety
```

- `app.py` — Python server, dataset loading, Random Forest-style model, risk calculations and ΔV estimate.
- `index.html` — dashboard and Three.js 3D showcase.
- `README.md` — formulas, limitations and deployment instructions.
- `render.yaml` — Render deployment configuration.
- `data/sample_events.csv` — small fallback dataset for Render.

## Algorithms and formulas

The prototype uses a 31-tree Random Forest-style ensemble with bootstrap sampling, random feature selection, shallow decision trees and Gini impurity.

Features:

```text
miss_distance, relative_speed, time_to_closest_approach,
uncertainty, hard_body_radius
```

Physics formulas:

```text
d_norm = miss_distance / (uncertainty + hard_body_radius)
proximity = exp(-0.5 × d_norm²)
urgency = max(0, 1 − time_to_closest_approach / 86400)
speed_factor = min(1, relative_speed / 12)
physics_score = 0.72 × proximity + 0.18 × urgency + 0.10 × speed_factor
combined_risk = 0.65 × ML_probability + 0.35 × physics_score
```

Maneuver estimate:

```text
required_separation = max(0, 1000 − current_miss_distance)
estimated_ΔV = required_separation / (2 × time_to_closest_approach)
```

This is a simplified academic prototype, not a flight-certified maneuver planner.

## 3D showcase

The dashboard contains an illustrative Three.js visualization showing Earth, a blue target satellite orbit, an orange debris orbit, a red closest-approach marker, and a green illustrative avoidance path. It is not yet a full SGP4 orbital propagator and is marked as not to scale.

## Git and Render

GitHub repository:

```text
https://github.com/mohnishraj187-dev/space-debris-
```

Recent commits:

```text
024d0d3 Add orbital collision avoidance IDP prototype
21a8a18 Prepare prototype for Render deployment
1dd253e Fix 3D showcase rendering without camera controls
c3b13f6 Improve 3D event visibility
```

The Render service is named `orbitalguard-idp`. After pushing the latest commit, Render redeploys automatically. The public URL appears on the Render service page when status is `Live`.

## Honest project status

Implemented: dashboard, ESA event selection, risk model, physics scoring, simplified ΔV recommendation, 3D visualization and Render configuration.

Not yet implemented: Random Forest training directly on the full ESA CSV, real SGP4 propagation, validated maneuver optimization, full covariance ellipsoids, LLM explanation layer and spacecraft control.
