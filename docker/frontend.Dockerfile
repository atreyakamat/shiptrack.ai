FROM python:3.9-slim

WORKDIR /app

# Install Streamlit and requests
COPY frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend code
COPY frontend/ /app/frontend/
COPY .streamlit/ /app/.streamlit/

ENV PYTHONPATH=/app
ENV API_URL=http://nginx:80/api

EXPOSE 8501

CMD ["streamlit", "run", "frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
