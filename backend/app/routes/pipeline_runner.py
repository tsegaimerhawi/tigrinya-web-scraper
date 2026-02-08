"""
Pipeline Runner UI at /pipeline – scrape, process, ingest from the browser.
Same as script_runner.py but mounted on the main backend for a second URL.
"""
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from queue import Queue
from typing import Optional

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse

from app.config import BASE_DIR

ROOT = Path(BASE_DIR)
CONFIG_PATH = ROOT / "runner_config.json"

CONFIG_SCHEMA = {
    "scraper_limit": {"label": "Number of newspapers to scrape", "type": "number", "default": 20},
    "pdf_dir": {"label": "PDF directory", "type": "string", "default": "pdfs"},
    "qdrant_host": {"label": "Qdrant host", "type": "string", "default": "localhost"},
    "qdrant_port": {"label": "Qdrant port", "type": "number", "default": 6333},
    "collection_llamaindex": {"label": "LlamaIndex collection name", "type": "string", "default": "tigrinya_llamaindex"},
    "llama_batch_size": {"label": "Llama ingest batch size", "type": "number", "default": 50},
    "llama_batch_delay": {"label": "Llama ingest batch delay (seconds)", "type": "number", "default": 60},
}


def load_config() -> dict:
    out = {k: v["default"] for k, v in CONFIG_SCHEMA.items()}
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k in out:
                if k in data:
                    out[k] = data[k]
        except (json.JSONDecodeError, IOError):
            pass
    return out


def save_config(data: dict) -> dict:
    out = load_config()
    for k, v in data.items():
        if k not in CONFIG_SCHEMA:
            continue
        schema = CONFIG_SCHEMA[k]
        if schema["type"] == "number":
            try:
                out[k] = int(v) if v != "" else schema["default"]
            except (TypeError, ValueError):
                out[k] = schema["default"]
        else:
            out[k] = str(v).strip() if v is not None else schema["default"]
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    return out


SCRIPTS = [
    {"id": "scraper", "label": "Scraper", "cmd": [sys.executable, str(ROOT / "scraper.py")], "description": "Download Haddas Ertra PDFs"},
    {"id": "pdf_processor", "label": "PDF Processor", "cmd": [sys.executable, str(ROOT / "pdf_processor.py")], "description": "Extract and clean text from PDFs"},
    {"id": "llama_ingest", "label": "Llama Ingest", "cmd": [sys.executable, str(ROOT / "llama_ingest.py")], "description": "Ingest into Qdrant (LlamaIndex)"},
    {"id": "check_qdrant", "label": "Check Qdrant", "cmd": [sys.executable, str(ROOT / "check_qdrant.py")], "description": "Verify Qdrant and list collections"},
    {"id": "validate_results", "label": "Validate Results", "cmd": [sys.executable, str(ROOT / "validate_results.py")], "description": "Validate raw_data and metadata"},
]


def build_cmd(script_id: str, cmd: list, config: dict, params: Optional[dict]) -> list:
    cmd = list(cmd)
    if script_id == "scraper":
        limit = (params or {}).get("limit")
        if limit is None:
            limit = config.get("scraper_limit", 20)
        limit = max(1, min(500, int(limit)))
        cmd.extend(["--limit", str(limit)])
    elif script_id == "llama_ingest":
        cmd.extend(["--qdrant-host", str(config.get("qdrant_host", "localhost"))])
        cmd.extend(["--qdrant-port", str(int(config.get("qdrant_port", 6333)))])
        cmd.extend(["--collection", str(config.get("collection_llamaindex", "tigrinya_llamaindex"))])
        cmd.extend(["--batch-size", str(int(config.get("llama_batch_size", 50)))])
        cmd.extend(["--batch-delay", str(int(config.get("llama_batch_delay", 60)))])
    elif script_id == "check_qdrant":
        cmd.append(str(config.get("qdrant_host", "localhost")))
        cmd.append(str(int(config.get("qdrant_port", 6333))))
    return cmd


def run_script_into_queue(script_id: str, queue: Queue, params: Optional[dict] = None):
    script = next((s for s in SCRIPTS if s["id"] == script_id), None)
    if not script:
        queue.put(f"data: {json.dumps({'type': 'error', 'line': 'Unknown script'})}\n\n")
        queue.put(None)
        return
    config = load_config()
    cmd = build_cmd(script_id, script["cmd"], config, params)
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["TIGRINYA_DATA_DIR"] = str(ROOT)
    env["QDRANT_HOST"] = str(config.get("qdrant_host", "localhost"))
    env["QDRANT_PORT"] = str(int(config.get("qdrant_port", 6333)))
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        for line in iter(proc.stdout.readline, ""):
            if line:
                queue.put(f"data: {json.dumps({'type': 'line', 'line': line})}\n\n")
        proc.wait()
        queue.put(f"data: {json.dumps({'type': 'done', 'exit_code': proc.returncode})}\n\n")
    except Exception as e:
        queue.put(f"data: {json.dumps({'type': 'error', 'line': str(e)})}\n\n")
    finally:
        queue.put(None)


async def stream_script(script_id: str, params: Optional[dict] = None):
    queue = Queue()
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, run_script_into_queue, script_id, queue, params)
    while True:
        chunk = await loop.run_in_executor(None, queue.get)
        if chunk is None:
            break
        yield chunk


router = APIRouter(prefix="/pipeline", tags=["pipeline-runner"])

# Base path for fetch() in the HTML (same as prefix)
PREFIX = "/pipeline"


@router.get("", response_class=HTMLResponse)
def pipeline_ui():
    """Serve the Pipeline Runner UI (scrape, process, ingest) at /pipeline."""
    return HTMLResponse(content=_get_html(), headers={"Cache-Control": "no-store, no-cache"})


@router.get("/api/scripts")
def list_scripts():
    return [{"id": s["id"], "label": s["label"], "description": s["description"]} for s in SCRIPTS]


@router.get("/api/config")
def get_config():
    return load_config()


@router.get("/api/config/schema")
def get_config_schema():
    return [{"key": k, "label": v["label"], "type": v["type"], "default": v["default"]} for k, v in CONFIG_SCHEMA.items()]


@router.post("/api/config")
async def post_config(request: Request):
    body = await request.json()
    return save_config(body)


@router.get("/run/{script_id}")
async def run_script(script_id: str, limit: Optional[int] = Query(None, description="Scraper: number of newspapers")):
    params = None
    if script_id == "scraper" and limit is not None:
        params = {"limit": max(1, min(500, limit))}
    return StreamingResponse(
        stream_script(script_id, params),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


def _get_html() -> str:
    scripts_json = json.dumps([{"id": s["id"], "label": s["label"], "description": s["description"]} for s in SCRIPTS])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Tigrinya Pipeline Runner</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ font-family: "SF Mono", "Fira Code", Consolas, monospace; margin: 0; padding: 1rem 1.5rem; background: #0f0f12; color: #e4e4e7; min-height: 100vh; }}
    h1 {{ font-size: 1.5rem; font-weight: 600; margin: 0 0 0.5rem 0; color: #fafafa; }}
    .sub {{ color: #71717a; font-size: 0.875rem; margin-bottom: 1.25rem; }}
    .back {{ margin-bottom: 1rem; }}
    .back a {{ color: #60a5fa; text-decoration: none; }}
    .back a:hover {{ text-decoration: underline; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 0.5rem; margin-bottom: 1.25rem; }}
    button {{ font: inherit; padding: 0.6rem 0.9rem; background: #27272a; color: #e4e4e7; border: 1px solid #3f3f46; border-radius: 8px; cursor: pointer; }}
    button:hover {{ background: #3f3f46; }}
    button:disabled {{ opacity: 0.6; cursor: not-allowed; }}
    button.running {{ background: #1e3a5f; border-color: #3b82f6; }}
    .output-wrap {{ border: 1px solid #27272a; border-radius: 8px; background: #18181b; overflow: hidden; }}
    .output {{ padding: 0.75rem 1rem; max-height: 420px; overflow-y: auto; white-space: pre-wrap; word-break: break-all; font-size: 0.8125rem; line-height: 1.5; }}
    .output:empty::before {{ content: "Click a script to run. Output appears here."; color: #52525b; }}
    .status {{ font-size: 0.8125rem; color: #a1a1aa; margin-bottom: 0.5rem; }}
    .status.running {{ color: #60a5fa; }}
    .status.done {{ color: #4ade80; }}
    .status.error {{ color: #f87171; }}
    .header-row {{ display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.75rem; margin-bottom: 1rem; }}
    .config-btn {{ padding: 0.45rem 0.85rem; font-size: 0.875rem; background: #3f3f46; }}
    .modal-overlay {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 1000; align-items: center; justify-content: center; padding: 1rem; }}
    .modal-overlay.open {{ display: flex; }}
    .modal {{ background: #18181b; border: 1px solid #3f3f46; border-radius: 12px; max-width: 420px; width: 100%; max-height: 90vh; overflow: hidden; display: flex; flex-direction: column; }}
    .modal h2 {{ margin: 0; padding: 1rem 1.25rem; font-size: 1.125rem; border-bottom: 1px solid #27272a; color: #fafafa; }}
    .modal .form-body {{ padding: 1rem 1.25rem; overflow-y: auto; }}
    .modal .form-group {{ margin-bottom: 0.85rem; }}
    .modal .form-group label {{ display: block; font-size: 0.8rem; color: #a1a1aa; margin-bottom: 0.25rem; }}
    .modal .form-group input {{ width: 100%; font: inherit; padding: 0.4rem 0.5rem; background: #0f0f12; border: 1px solid #3f3f46; border-radius: 6px; color: #e4e4e7; }}
    .modal .form-actions {{ display: flex; gap: 0.5rem; justify-content: flex-end; padding: 1rem 1.25rem; border-top: 1px solid #27272a; }}
    .modal .form-actions .save {{ background: #2563eb; border-color: #2563eb; color: #fff; }}
  </style>
</head>
<body>
  <div class="back"><a href="/docs">← API docs</a> &nbsp;|&nbsp; <a href="{PREFIX}">{PREFIX}</a></div>
  <div class="header-row">
    <div>
      <h1>🇪🇷 Tigrinya Pipeline Runner</h1>
      <p class="sub">Scrape → Process → Ingest. Run scripts and see live output. <a href="http://localhost:5173" target="_blank" rel="noopener" style="color:#60a5fa;">Open App (Articles + RAG)</a></p>
    </div>
    <button id="config-btn" class="config-btn">Configuration</button>
  </div>
  <div class="grid" id="buttons"></div>
  <p class="status" id="status"></p>
  <div class="output-wrap">
    <div class="output" id="output"></div>
  </div>

  <div id="config-modal" class="modal-overlay">
    <div class="modal">
      <h2>Configuration</h2>
      <div class="form-body" id="config-form-container"></div>
      <div class="form-actions">
        <button id="config-close">Close</button>
        <button id="config-save" class="save">Save</button>
      </div>
    </div>
  </div>

  <script>
    const PREFIX = "{PREFIX}";
    const scripts = {scripts_json};
    const buttonsEl = document.getElementById('buttons');
    const outputEl = document.getElementById('output');
    const statusEl = document.getElementById('status');

    scripts.forEach(s => {{
      const btn = document.createElement('button');
      btn.textContent = s.label;
      btn.title = s.description;
      btn.dataset.scriptId = s.id;
      btn.addEventListener('click', () => run(s.id, btn));
      buttonsEl.appendChild(btn);
    }});

    async function run(scriptId, btn) {{
      document.querySelectorAll('.grid button').forEach(b => b.disabled = true);
      btn.classList.add('running');
      statusEl.textContent = 'Running ' + scriptId + '...';
      statusEl.className = 'status running';
      outputEl.textContent = '';
      try {{
        const res = await fetch(PREFIX + '/run/' + scriptId);
        if (!res.ok) throw new Error(res.statusText);
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        while (true) {{
          const {{ value, done }} = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, {{ stream: true }});
          const lines = buffer.split('\\n\\n');
          buffer = lines.pop() || '';
          for (const chunk of lines) {{
            if (!chunk.startsWith('data: ')) continue;
            try {{
              const data = JSON.parse(chunk.slice(6));
              if (data.type === 'line') {{ outputEl.textContent += data.line; outputEl.scrollTop = outputEl.scrollHeight; }}
              else if (data.type === 'done') {{ statusEl.textContent = 'Finished (exit ' + data.exit_code + ')'; statusEl.className = data.exit_code === 0 ? 'status done' : 'status error'; }}
              else if (data.type === 'error') {{ outputEl.textContent += data.line; statusEl.textContent = 'Error'; statusEl.className = 'status error'; }}
            }} catch (_) {{}}
          }}
        }}
      }} catch (e) {{
        statusEl.textContent = 'Error: ' + e.message;
        statusEl.className = 'status error';
      }} finally {{
        document.querySelectorAll('.grid button').forEach(b => b.disabled = false);
        btn.classList.remove('running');
      }}
    }}

    const configModal = document.getElementById('config-modal');
    const configFormContainer = document.getElementById('config-form-container');
    document.getElementById('config-btn').addEventListener('click', openConfigModal);
    document.getElementById('config-close').addEventListener('click', () => configModal.classList.remove('open'));
    document.getElementById('config-save').addEventListener('click', saveConfig);
    configModal.addEventListener('click', (e) => {{ if (e.target === configModal) configModal.classList.remove('open'); }});

    async function openConfigModal() {{
      const [schemaRes, configRes] = await Promise.all([fetch(PREFIX + '/api/config/schema'), fetch(PREFIX + '/api/config')]);
      const schema = await schemaRes.json();
      const config = await configRes.json();
      configFormContainer.innerHTML = '';
      schema.forEach(({{ key, label, type }}) => {{
        const group = document.createElement('div');
        group.className = 'form-group';
        const lab = document.createElement('label');
        lab.textContent = label;
        lab.setAttribute('for', 'config-' + key);
        const input = document.createElement('input');
        input.id = 'config-' + key;
        input.name = key;
        input.type = type === 'number' ? 'number' : 'text';
        input.value = config[key] != null ? config[key] : '';
        if (type === 'number') {{ input.min = 1; input.step = 1; }}
        group.appendChild(lab);
        group.appendChild(input);
        configFormContainer.appendChild(group);
      }});
      configModal.classList.add('open');
    }}

    async function saveConfig() {{
      const inputs = configFormContainer.querySelectorAll('input[name]');
      const data = {{}};
      inputs.forEach(inp => {{ const val = inp.type === 'number' ? parseInt(inp.value, 10) : inp.value; data[inp.name] = isNaN(val) ? inp.value : val; }});
      try {{ await fetch(PREFIX + '/api/config', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: JSON.stringify(data) }}); configModal.classList.remove('open'); }} catch (e) {{ console.error(e); }}
    }}
  </script>
</body>
</html>"""
