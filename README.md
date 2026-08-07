# ShipTrack AI

ShipTrack AI is an intelligent shipment management and tracking platform focused on India Post first, with a roadmap to become a multi-carrier logistics intelligence product.

## Product Definition

The full product requirements are documented in:

- `/home/runner/work/shiptrack.ai/shiptrack.ai/docs/PRD.md`

## Basic Scaffold

This repository now contains a minimal scaffold aligned to the PRD:

- `backend/` Flask API scaffold (`/api/v1/health`, shipment create/list/get/refresh)
- `frontend/` Streamlit dashboard scaffold
- `requirements.txt` Python dependencies for scaffold

### Run locally

```bash
pip install -r requirements.txt
python -m backend.main
```

In another terminal:

```bash
streamlit run frontend/app.py
```
