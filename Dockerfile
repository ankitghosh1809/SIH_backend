# Agent D — targets Render/Railway, not Vercel: PyTorch/PennyLane/Qiskit exceed
# Vercel's serverless size & runtime limits.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render and Railway both inject PORT at runtime; default it for local `docker run`.
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
