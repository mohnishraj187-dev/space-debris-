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

## Technical methodology

### System architecture

```text
ESA CDM dataset
      ↓
Event selection and feature extraction
      ↓
Random Forest-style risk model ──┐
                                 ├─ Combined risk and operator guidance
Physics-based risk model ────────┘
      ↓
Simplified ΔV estimate
      ↓
Dashboard and 3D event visualization
```

### Dataset fields used

The ESA dataset contains many CDM fields. This prototype uses:

| Field | Meaning | Use |
|---|---|---|
| `event_id` | Conjunction event identifier | Event selection |
| `risk` | ESA logarithmic risk label | Reference label |
| `miss_distance` | Predicted closest separation | Risk feature |
| `relative_speed` | Relative encounter speed | Risk feature |
| `time_to_tca` | Time to closest approach, in days | Converted to seconds |
| `t_sigma_r` | Radial uncertainty estimate | Uncertainty feature |
| `hard_body_radius` | Combined physical size assumption | Safety feature |

The complete ESA file also includes relative position and velocity components, covariance determinants, observation quality, orbital parameters, object type, and space-weather variables.

### Feature conversion

The dataset stores time to closest approach in days. The application converts it to seconds:

```text
time_to_closest_approach = time_to_tca × 86,400
```

The model input vector is:

```text
x = [miss_distance, relative_speed,
     time_to_closest_approach, uncertainty,
     hard_body_radius]
```

### Random Forest-style algorithm

The prototype trains 31 shallow decision trees. For every tree:

1. A bootstrap sample is created from the training records.
2. A random subset of features is considered at each split.
3. Candidate thresholds are evaluated.
4. The split with the lowest weighted Gini impurity is selected.
5. Splitting stops at depth 4 or when a node becomes sufficiently small.
6. Each tree returns the proportion of high-risk records in its final leaf.

Gini impurity is:

```text
Gini = 2 × p × (1 − p)
```

where `p` is the proportion of high-risk records in a node.

The ensemble probability is:

```text
ML_probability = (tree_1 + tree_2 + ... + tree_31) / 31
```

The current prototype uses synthetic training records so that it can run without external Python packages. The next research stage should train the model directly on the ESA training CSV using a reproducible label definition and scikit-learn.

### Physics-inspired risk score

First, the application calculates normalized miss distance:

```text
d_norm = miss_distance / (uncertainty + hard_body_radius)
```

A Gaussian-style proximity score is then calculated:

```text
proximity = exp(−0.5 × d_norm²)
```

Urgency increases as closest approach becomes nearer:

```text
urgency = max(0, 1 − time_to_closest_approach / 86,400)
```

Relative speed is normalized and capped:

```text
speed_factor = min(1, relative_speed / 12)
```

The physics score is:

```text
physics_score =
    0.72 × proximity
  + 0.18 × urgency
  + 0.10 × speed_factor
```

### Combined risk and thresholds

The ML and physics outputs are combined as follows:

```text
combined_risk =
    0.65 × ML_probability
  + 0.35 × physics_score
```

Risk levels:

```text
HIGH   if combined_risk ≥ 0.55
MEDIUM if combined_risk ≥ 0.30
LOW    otherwise
```

### Maneuver estimation

The prototype uses a simplified 1 km target separation:

```text
required_separation = max(0, 1000 − current_miss_distance)
```

The estimated impulsive ΔV is:

```text
estimated_ΔV = required_separation /
               (2 × time_to_closest_approach)
```

This is an educational approximation. It does not replace Lambert targeting, numerical orbit propagation, covariance propagation, or mission-specific maneuver constraints.

### Suggestive AI operator guidance

The recommendation layer is deliberately advisory:

```text
LOW:
  Continue monitoring; no maneuver is suggested.

MEDIUM:
  Increase tracking frequency and prepare a low-ΔV alternative.

HIGH:
  Prioritize operator review and compare along-track,
  radial, and cross-track maneuver options.
```

The system does not autonomously command a spacecraft. A human operator must validate any maneuver.

### 3D visualization

The dashboard uses Three.js to render an illustrative event scene containing Earth, a blue target orbit, an orange debris orbit, animated objects, a closest-approach marker, and a green avoidance-path preview. The current paths are parametric ellipses:

```text
x = radius × cos(t)
y = inclination × sin(t)
z = depth × sin(t)
```

The visualization is not to scale and is not yet generated by SGP4 or full CDM covariance propagation.

### LLM and dual contouring scope

No LLM is used in the numerical safety calculation. An LLM may later be used only to explain model outputs in natural language. Dual contouring is also not required for the current prototype; it would be appropriate only for extracting an isosurface from a volumetric 3D risk field.

### Limitations and future work

- Train and validate the model directly on the ESA CSV.
- Handle class imbalance using class weights or resampling.
- Use real covariance matrices instead of one uncertainty scalar.
- Add SGP4/SDP4 orbit propagation from TLE/OMM data.
- Generate true 3D relative trajectories from CDM states.
- Compare validated along-track, radial, and cross-track maneuvers.
- Add ΔV budget, fuel, mission, and timing constraints.
- Evaluate precision, recall, F1-score, ROC-AUC, false-alarm rate, and early-warning time.

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
