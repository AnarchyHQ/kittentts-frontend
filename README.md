# 😻 KittenTTS Frontend

Web UI and OpenAI-compatible API server for [KittenTTS](https://github.com/KittenML/KittenTTS) — a state-of-the-art TTS model under 25MB.

![Python 3.12](https://img.shields.io/badge/python-3.12-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

## Features

- 🌐 **Web UI** — Browser-based interface with model/voice/speed controls
- 🔌 **OpenAI-compatible API** — Drop-in replacement for `/v1/audio/speech`
- 🐳 **Docker ready** — One command to run
- 🔄 **Multi-model** — Switch between mini, micro, and nano variants at runtime
- 🎚️ **Speed control** — 0.5x to 2.0x speech rate
- 💻 **CPU-only** — No GPU required

## Quick Start

### Docker (recommended)

```bash
docker compose up -d
```

Open http://localhost:5200 in your browser.

### Docker (manual)

```bash
docker build -t kittentts-frontend .
docker run -d -p 5200:5200 --name kittentts kittentts-frontend
```

### Without Docker

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install https://github.com/KittenML/KittenTTS/releases/download/0.8/kittentts-0.8.0-py3-none-any.whl soundfile flask
python server.py
```

## Configuration

All settings via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `KITTENTTS_HOST` | `0.0.0.0` | Server bind address |
| `KITTENTTS_PORT` | `5200` | Server port |
| `KITTENTTS_DEFAULT_MODEL` | `mini-0.8` | Default model on load |
| `KITTENTTS_DEFAULT_VOICE` | `Jasper` | Default voice |
| `KITTENTTS_SAMPLE_RATE` | `24000` | Audio sample rate (Hz) |

## Available Models

| Key | HuggingFace ID | Quality | Speed |
|-----|----------------|---------|-------|
| `mini-0.8` | KittenML/kitten-tts-mini-0.8 | ⭐⭐⭐ Best | Slower |
| `micro-0.8` | KittenML/kitten-tts-micro-0.8 | ⭐⭐ Good | Medium |
| `nano-0.8-fp32` | KittenML/kitten-tts-nano-0.8-fp32 | ⭐ OK | Fast |
| `nano-0.8-int8` | KittenML/kitten-tts-nano-0.8-int8 | ⭐ OK | Fastest |

## Available Voices

Bella, Jasper, Luna, Bruno, Rosie, Hugo, Kiki, Leo

## API

### Generate Speech

```bash
curl -X POST http://localhost:5200/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello world", "voice": "Luna", "model": "mini-0.8", "speed": 1.0}' \
  -o output.wav
```

### List Voices

```bash
curl http://localhost:5200/voices
```

### List Models

```bash
curl http://localhost:5200/models
```

### Health Check

```bash
curl http://localhost:5200/health
```

## Credits

- **KittenTTS** by [KittenML](https://github.com/KittenML/KittenTTS) — the underlying TTS model
- **Frontend** by [AnarchyHQ](https://github.com/AnarchyHQ)

## License

MIT
