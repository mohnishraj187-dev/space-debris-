# Space Debris — Orbital Monitoring System

A modern, high-contrast, aerospace-grade Space Situational Awareness (SSA) & Orbital Debris Monitoring Dashboard built with pure Python and Three.js.

> [!IMPORTANT]
> **Operational Scope**: This repository provides a comprehensive end-to-end space debris tracking, orbital visualization, ML conjunction risk assessment, processing pipeline, and collision avoidance platform.

---

## 🚀 Quick Start (Windows)

Simply double-click or run `start_dashboard.bat` from the terminal:

```cmd
start_dashboard.bat
```

This batch script automatically:
1. Starts the Python HTTP server on port `8000` (`python app.py`).
2. Opens `http://127.0.0.1:8000` in your default web browser.

### Manual Command Line Launch
```bash
python app.py
```
Then open `http://127.0.0.1:8000` in your web browser.

---

## 🛰️ Key Features

- **Aerospace Control Dashboard**: Futuristic dark space theme (`#050811`), high-contrast typography (Inter & JetBrains Mono), live UTC mission clock, and operational status indicators.
- **End-to-End Processing Pipeline**: Visible interactive multi-stage pipeline flow spanning data ingestion, orbit propagation, proximity screening, ML risk model evaluation, and avoidance planning.
- **3D Orbital Situational Display**: Interactive Three.js Earth globe with atmospheric halo glow, wireframe orbital planes (LEO, MEO, GEO), animated satellite (cyan) and debris (amber/red) markers.
- **Tracked Objects Catalog**: 15 sample orbital catalog items (e.g. *ISS*, *Hubble*, *Fengyun-1C Debris*, *Kosmos-2251 Fragment*, *Starlink-3042*) with real-time text search, type filtering (*Satellites* vs *Debris*), and risk level filtering (*LOW*, *MEDIUM*, *HIGH*).
- **Object Inspector & Decision Support**: Slide-over inspector panel calculating combined Random Forest ML probability & physics-based encounter metrics via backend REST API `/api/analyze`.
- **Live Conjunction Alerts**: Real-time demo alert feed highlighting high-risk close approach events.
- **Development Roadmap**: Visually distinct roadmap section outlining planned future expansion modules with interactive status modals.

---

## 🗺️ Development Roadmap

| Module | Status |
|---|---|
| Dashboard Overview & Navigation | ✅ Implemented |
| End-to-End Processing Pipeline | ✅ Implemented |
| Sample Catalog Tracking (15 objects) | ✅ Implemented |
| 3D Orbit Visualization (Three.js) | ✅ Implemented |
| ML + Physics Risk Model | ✅ Implemented |
| Advisory Operator Guidance | ✅ Implemented |
| Real-Time TLE Synchronization | 🔒 Future Phase |
| SGP4 Numerical Orbit Propagation | 🔒 Future Phase |
| AI Optical/Radar Debris Classifier | 🔒 Future Phase |
| Foster-1992 Collision Probability | 🔒 Future Phase |
| Autonomous Avoidance Maneuver Planner | 🔒 Future Phase |

---

## 🔬 Backend & Technical Methodology

The backend (`app.py`) is standard-library pure Python with **zero third-party package dependencies**.

### Risk Calculation Formula
1. **Machine Learning Ensemble**: 31 randomized shallow decision trees trained on bootstrap samples evaluate miss distance, relative speed, time to closest approach (TCA), and uncertainty radius.
2. **Physics Proximity Metric**:
   $$d_{\text{norm}} = \frac{\text{miss\_distance}}{\text{uncertainty} + \text{hard\_body\_radius}}$$
   $$\text{proximity} = \exp(-0.5 \cdot d_{\text{norm}}^2)$$
3. **Combined Priority Risk Score**:
   $$\text{Combined Risk} = 0.65 \cdot \text{ML\_Probability} + 0.35 \cdot \text{Physics\_Score}$$

---

## 📁 Repository Structure

```text
space-debris/
├── app.py                 # Pure Python HTTP Server & REST API endpoints
├── index.html             # Single-page UI with Three.js visualization
├── start_dashboard.bat    # Windows launcher batch script
├── README.md              # Documentation & Roadmap
├── data/
│   └── sample_events.csv  # 15-record sample orbital catalog
```
