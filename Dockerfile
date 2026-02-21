FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends libsndfile1 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir \
    https://github.com/KittenML/KittenTTS/releases/download/0.8/kittentts-0.8.0-py3-none-any.whl \
    soundfile flask

WORKDIR /app
COPY server.py .

ENV KITTENTTS_HOST=0.0.0.0
ENV KITTENTTS_PORT=5200
ENV KITTENTTS_DEFAULT_MODEL=mini-0.8
ENV KITTENTTS_DEFAULT_VOICE=Jasper
ENV KITTENTTS_SAMPLE_RATE=24000

EXPOSE 5200

CMD ["python", "server.py"]
