# ShipTrack AI

ShipTrack AI is an intelligent shipment management and tracking platform focused on India Post first, with a roadmap to become a multi-carrier logistics intelligence product.

## React Landing Page (Waitlist)

The `main` branch contains a premium "Coming Soon" landing page built with React, Vite, Tailwind CSS v4, and Framer Motion. It includes a Waitlist feature that integrates with Netlify Forms.

To run the frontend locally:
```bash
npm install
npm run dev
```

## Product Definition

The full product requirements are documented in:
- `docs/PRD.md`

## Backend / Dashboard Scaffold

- `backend/` Flask API scaffold (`/api/v1/health`, shipment create/list/get/refresh)
- `frontend/` Streamlit dashboard scaffold
- `requirements.txt` Python dependencies for scaffold

### Run backend locally

```bash
pip install -r requirements.txt
python -m backend.main
```

### Run streamlit locally

```bash
streamlit run frontend/app.py
```
