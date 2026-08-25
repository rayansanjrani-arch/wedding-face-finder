FROM python:3.11-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev libboost-python-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim AS runtime
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libopenblas0 liblapack3 libx11-6 libgtk-3-0 libboost-python1.83.0 libgl1 && rm -rf /var/lib/apt/lists/*
RUN groupadd -r appuser && useradd -r -g appuser appuser
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH
COPY wedding_face_finder/ ./wedding_face_finder/
COPY run.py alembic.ini ./
COPY alembic/ ./alembic/
RUN mkdir -p uploads photos thumbnails data logs instance && chown -R appuser:appuser /app /home/appuser
USER appuser
EXPOSE 5000
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 FLASK_APP=wedding_face_finder.app
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "--timeout", "120", "wedding_face_finder.app:create_app()"]