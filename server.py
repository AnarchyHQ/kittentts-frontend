#!/usr/bin/env python3
"""KittenTTS Frontend — Web UI & OpenAI-compatible API for KittenTTS models."""

import os
import io
import time

from flask import Flask, request, send_file, jsonify, render_template_string
from kittentts import KittenTTS
import soundfile as sf

# ── Configuration (env vars or defaults) ──────────────────────────────────────
HOST = os.environ.get("KITTENTTS_HOST", "0.0.0.0")
PORT = int(os.environ.get("KITTENTTS_PORT", "5200"))
DEFAULT_MODEL = os.environ.get("KITTENTTS_DEFAULT_MODEL", "mini-0.8")
DEFAULT_VOICE = os.environ.get("KITTENTTS_DEFAULT_VOICE", "Jasper")
SAMPLE_RATE = int(os.environ.get("KITTENTTS_SAMPLE_RATE", "24000"))

# ── Model registry ────────────────────────────────────────────────────────────
VOICES = ["Bella", "Jasper", "Luna", "Bruno", "Rosie", "Hugo", "Kiki", "Leo"]
MODELS = {
    "mini-0.8": "KittenML/kitten-tts-mini-0.8",
    "micro-0.8": "KittenML/kitten-tts-micro-0.8",
    "nano-0.8-fp32": "KittenML/kitten-tts-nano-0.8-fp32",
    "nano-0.8-int8": "KittenML/kitten-tts-nano-0.8-int8",
}

_loaded_models: dict = {}
app = Flask(__name__)

# ── HTML template ─────────────────────────────────────────────────────────────
HTML = '''<!DOCTYPE html>
<html><head><title>KittenTTS Frontend</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,-apple-system,sans-serif;background:#1a1a2e;color:#e0e0e0;display:flex;justify-content:center;align-items:center;min-height:100vh}
.container{background:#16213e;border-radius:16px;padding:40px;max-width:520px;width:90%;box-shadow:0 8px 32px rgba(0,0,0,.4)}
h1{text-align:center;margin-bottom:8px;font-size:1.8em}
h1 span{font-size:1.2em}
.sub{text-align:center;color:#888;margin-bottom:24px;font-size:.9em}
textarea{width:100%;height:100px;background:#0f3460;border:1px solid #333;border-radius:8px;color:#e0e0e0;padding:12px;font-size:15px;resize:vertical;font-family:inherit}
textarea:focus{outline:none;border-color:#e94560}
label{display:block;margin-top:16px;margin-bottom:6px;font-size:.85em;color:#aaa}
.row{display:flex;gap:12px;align-items:center}
select{flex:1;background:#0f3460;border:1px solid #333;border-radius:8px;color:#e0e0e0;padding:10px;font-size:15px}
select:focus{outline:none;border-color:#e94560}
button{flex:1;background:#e94560;color:#fff;border:none;border-radius:8px;padding:12px;font-size:15px;cursor:pointer;font-weight:600;transition:background .2s;margin-top:16px}
button:hover{background:#c73652}
button:disabled{background:#555;cursor:wait}
.audio-box{margin-top:20px;text-align:center}
audio{width:100%;margin-top:8px}
.status{text-align:center;margin-top:12px;color:#888;font-size:.85em;min-height:20px}
.dl{display:inline-block;margin-top:8px;color:#e94560;text-decoration:none;font-size:.9em}
.dl:hover{text-decoration:underline}
.footer{text-align:center;margin-top:24px;padding-top:16px;border-top:1px solid #333;font-size:.8em;color:#666}
.footer a{color:#e94560;text-decoration:none}
.footer a:hover{text-decoration:underline}
</style></head><body>
<div class="container">
<h1><span>😻</span> KittenTTS</h1>
<p class="sub">Lightweight TTS — no GPU required</p>
<textarea id="text" placeholder="Type something to speak...">Hello! I'm KittenTTS, a tiny text to speech model running on CPU.</textarea>
<label>Model</label>
<div class="row">
<select id="model">
{% for k,v in models.items() %}<option value="{{k}}" {{'selected' if k==default_model}}>{{k}}</option>{% endfor %}
</select>
</div>
<label>Voice</label>
<div class="row">
<select id="voice">
{% for v in voices %}<option value="{{v}}" {{'selected' if v==default_voice}}>{{v}}</option>{% endfor %}
</select>
</div>
<label>Speed: <span id="speedVal">1.0</span>x</label>
<input type="range" id="speed" min="0.5" max="2.0" step="0.1" value="1.0" style="width:100%;accent-color:#e94560" oninput="document.getElementById('speedVal').textContent=this.value">
<button id="btn" onclick="speak()">Generate</button>
<div class="audio-box" id="audioBox" style="display:none">
<audio id="player" controls></audio><br>
<a class="dl" id="dlLink" href="#" download="kittentts.wav">⬇ Download WAV</a>
</div>
<div class="status" id="status"></div>
<div class="footer">
Powered by <a href="https://github.com/KittenML/KittenTTS" target="_blank">KittenTTS</a> · 
<a href="https://github.com/AnarchyHQ/kittentts-frontend" target="_blank">Frontend source</a>
</div>
</div>
<script>
async function speak(){
  const btn=document.getElementById('btn'),st=document.getElementById('status');
  const text=document.getElementById('text').value.trim();
  if(!text)return;
  btn.disabled=true;btn.textContent='Generating...';st.textContent='';
  const t0=Date.now();
  try{
    const r=await fetch('/v1/audio/speech',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        input:text,
        voice:document.getElementById('voice').value,
        model:document.getElementById('model').value,
        speed:parseFloat(document.getElementById('speed').value)
      })});
    if(!r.ok)throw new Error(await r.text());
    const blob=await r.blob(),url=URL.createObjectURL(blob);
    document.getElementById('audioBox').style.display='block';
    const player=document.getElementById('player');player.src=url;player.play();
    document.getElementById('dlLink').href=url;
    st.textContent='Generated in '+((Date.now()-t0)/1000).toFixed(1)+'s';
  }catch(e){st.textContent='Error: '+e.message}
  btn.disabled=false;btn.textContent='Generate';
}
</script></body></html>'''


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_model(model_id: str) -> KittenTTS:
    if model_id not in _loaded_models:
        print(f"Loading model {model_id}...")
        _loaded_models[model_id] = KittenTTS(model_id)
        print(f"Model {model_id} loaded.")
    return _loaded_models[model_id]


def resolve_voice(voice: str) -> str:
    if voice.capitalize() in VOICES:
        return voice.capitalize()
    return DEFAULT_VOICE


def resolve_model(model_key: str) -> str:
    return MODELS.get(model_key, MODELS[DEFAULT_MODEL])


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template_string(
        HTML,
        voices=VOICES,
        models=MODELS,
        default_model=DEFAULT_MODEL,
        default_voice=DEFAULT_VOICE,
    )


@app.route("/v1/audio/speech", methods=["POST"])
def speech():
    data = request.json or {}
    text = data.get("input", data.get("text", ""))
    if not text:
        return jsonify({"error": "No text provided"}), 400

    voice = resolve_voice(data.get("voice", DEFAULT_VOICE))
    speed = max(0.5, min(2.0, float(data.get("speed", 1.0))))
    model_id = resolve_model(data.get("model", DEFAULT_MODEL))

    t0 = time.time()
    audio = get_model(model_id).generate(text, voice=voice, speed=speed)
    duration = time.time() - t0

    buf = io.BytesIO()
    sf.write(buf, audio, SAMPLE_RATE, format="WAV")
    buf.seek(0)

    print(f"[{data.get('model', DEFAULT_MODEL)}] {len(text)} chars, {duration:.2f}s, voice={voice}, speed={speed}")
    return send_file(buf, mimetype="audio/wav", download_name="speech.wav")


@app.route("/voices", methods=["GET"])
def voices():
    return jsonify({"voices": VOICES})


@app.route("/models", methods=["GET"])
def list_models():
    return jsonify({"models": MODELS, "default": DEFAULT_MODEL})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "models": list(MODELS.keys()), "loaded": list(_loaded_models.keys())})


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"KittenTTS Frontend starting on {HOST}:{PORT}")
    print(f"Default model: {DEFAULT_MODEL}, Default voice: {DEFAULT_VOICE}")
    get_model(MODELS[DEFAULT_MODEL])  # preload
    app.run(host=HOST, port=PORT)
