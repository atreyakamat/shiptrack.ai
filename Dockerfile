FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Environment variables
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose ports for both Flask (5000) and Streamlit (8501)
EXPOSE 5000 8501

# Command to run both using a shell script or supervisor
# We can use a simple script to start both
RUN echo '#!/bin/bash\n\
flask run --host=0.0.0.0 --port=5000 &\n\
streamlit run frontend/app.py --server.port=8501 --server.address=0.0.0.0\n\
' > start.sh && chmod +x start.sh

CMD ["./start.sh"]
