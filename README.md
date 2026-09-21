# OrbitalGuard — IDP Partial Prototype

This is a demonstration prototype for the IDP topic **AI-Assisted Space Situational Awareness and Collision Avoidance**.

It is intentionally not a flight-certified or autonomous operational system. It demonstrates the first ~20% of the proposed workflow:

`conjunction inputs -> feature engineering -> Random Forest-style risk estimate -> physics-based maneuver estimate -> dashboard`

## Run

```bash
cd /home/mohnish/idp_space_safety
python3 app.py
```

Open http://127.0.0.1:8000 in a browser.

## Deploy on Render

The repository includes `render.yaml`. In Render, choose **New → Blueprint**, connect the GitHub repository, and select the `render.yaml` file. Render will run `python3 app.py` and provide a public URL.

The prototype uses only the Python standard library. It creates synthetic training cases, trains 31 small randomized decision trees, and evaluates a user-selected conjunction.

## Important scope note

The current prototype uses synthetic data and a simplified two-body/local encounter model. It does not ingest live TLE/OMM data, parse real CDMs, propagate full 3D orbits, or issue real spacecraft commands. Those are future implementation stages.

## Algorithms and formulas

- Derived relative speed: `v_rel = sqrt(vx^2 + vy^2 + vz^2)`.
- Uncertainty scale: `sigma = sqrt(sigma_x^2 + sigma_y^2 + sigma_z^2)`.
- Normalized miss distance: `d_norm = miss_distance / (sigma + hard_body_radius)`.
- Simplified collision-risk proxy: `risk_proxy = exp(-0.5 * d_norm^2)`, increased by high relative speed and short time-to-closest-approach.
- Labels are generated from that proxy only for demonstration; real labels should come from historical CDM outcomes or a defensible thresholding protocol.
- Random Forest-style model: bootstrap samples + random feature subsets + shallow Gini decision trees; final probability is the mean of tree probabilities.
- Maneuver estimate: `delta_v = max(0.01, required_separation / (2 * time_seconds))`, using a simplified impulsive relative-motion approximation. `required_separation = safety_target - miss_distance`.
- Recommended action: maneuver only when predicted risk is high and the target separation is not already met.

## Suggested explanation in the presentation

“The ML model prioritizes conjunctions for operator attention. The physics module independently estimates a low-Delta-V separation maneuver. The two modules are deliberately kept separate so the ML model does not directly control a spacecraft.”
