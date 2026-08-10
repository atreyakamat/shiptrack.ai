# ShipTrack AI

"Track smarter. Understand deliveries. Organize everything."

ShipTrack AI is a personal and small-business shipment intelligence platform that allows you to easily track, monitor, and analyze your postal shipments.

## Features
- **Centralized Dashboard**: Track all your shipments in one place with a modern, responsive UI.
- **Detailed History**: View the complete routing history of any shipment with a beautiful visual timeline.
- **OCR Receipt Scanner**: Automatically extract tracking numbers from your postal receipts using local OCR.
- **AI Insights**: Generate natural language summaries and health assessments for your shipments using AI.
- **Analytics**: Understand your delivery rates, average transit times, and shipment distributions.
- **Automated Refreshing**: Background scheduler to keep all your active shipments up to date.

### Capabilities Matrix

| Feature | Real Implementation | Demo / Mock Fallback |
|---------|---------------------|----------------------|
| **Tracking API** | India Post API (Unavailable due to CAPTCHA) | Fully realistic multi-stage shipment mock |
| **OCR Extraction** | EasyOCR (Local CPU/GPU inference) | Simulated extraction with UI warnings |
| **AI Insights** | LLM Provider (OpenAI/Ollama integration) | Heuristic rule-based summary generation |
| **Database** | PostgreSQL / SQLite | Included SQLite `shiptrack.db` via `seed.py` |

## Architecture & Tech Stack
- **Frontend**: Streamlit, Plotly (for analytics charts), Custom CSS
- **Backend**: Python, Flask, Flask-SQLAlchemy, Flask-CORS
- **Database**: PostgreSQL (Production), SQLite (Development)
- **OCR Engine**: OpenCV + EasyOCR
- **Testing**: Pytest

---

## Deployment Manual (Docker Compose)

The easiest way to run ShipTrack AI in a production-like environment is via Docker Compose. This spins up the Flask Backend, Streamlit Frontend, and a PostgreSQL database.

**1. Clone the repository:**
```bash
git clone <repository_url>
cd shiptrack.ai
```

**2. Configure Environment:**
Copy the example environment file:
```bash
cp .env.example .env
```
Edit `.env` to configure `DATABASE_URL` for PostgreSQL:
```
DATABASE_URL=postgresql://shiptrack:shiptrack_pass@db:5432/shiptrack
FLASK_ENV=production
```

**3. Build and Run via Docker Compose:**
```bash
docker-compose up -d --build
```

**4. Access the Application:**
- Frontend UI: http://localhost:8501
- Backend API: http://localhost:5000

---

## Local Development Setup

If you prefer to run the application natively for development:

**1. Set up virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

**2. Install dependencies:**
```bash
pip install -r requirements.txt
pip install streamlit plotly
```

**3. Initialize and Seed the Database:**
```bash
python seed.py
```
*This will create the SQLite database and populate it with realistic demo shipments.*

**4. Start the Backend API:**
```bash
python run.py
```

**5. Start the Frontend UI:**
Open a new terminal window and run:
```bash
python -m streamlit run frontend/app.py
```

## India Post Integration Limitations
The public India Post tracking interface currently presents automation constraints such as CAPTCHA and strict anti-bot systems. ShipTrack AI therefore does not attempt to circumvent those controls. The carrier adapter remains implemented so an authorized API or compatible provider can be integrated later. For development and evaluation, please ensure `TRACKING_DEMO_MODE=true` is set in your `.env` to use the fully functional mock provider.

## Testing
Run the test suite using pytest:
```bash
python -m pytest tests/
```
