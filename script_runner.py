#!/usr/bin/env python3
"""
Script Runner UI Backend
========================
FastAPI server that runs project scripts in subprocess and streams
stdout/stderr to the browser via Server-Sent Events.
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from queue import Queue

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse

# Project root (where script_runner.py lives)
ROOT = Path(__file__).resolve().parent

# Scripts that can be run from the UI
# Each: id, label, cmd (list for subprocess), description
SCRIPTS = [
    {
        "id": "scraper",
        "label": "Scraper",
        "cmd": [sys.executable, str(ROOT / "scraper.py")],
        "description": "Download PDFs from Haddas Ertra",
    },
    {
        "id": "pdf_processor",
        "label": "PDF Processor",
        "cmd": [sys.executable, str(ROOT / "pdf_processor.py")],
        "description": "Extract and clean text from PDFs",
    },
    {
        "id": "llama_ingest",
        "label": "Llama Ingest",
        "cmd": [sys.executable, str(ROOT / "llama_ingest.py")],
        "description": "Ingest PDFs into Qdrant (LlamaIndex)",
    },
    {
        "id": "run_pipeline",
        "label": "Run Pipeline",
        "cmd": [sys.executable, str(ROOT / "run_pipeline.py")],
        "description": "Full Tigrinya NLP pipeline (tagger → critic → refiner)",
    },
    {
        "id": "store_data",
        "label": "Store Data",
        "cmd": [sys.executable, str(ROOT / "store_data.py")],
        "description": "Store refined articles in Qdrant",
    },
    {
        "id": "store_sentences",
        "label": "Store Sentences",
        "cmd": [sys.executable, str(ROOT / "store_sentences.py")],
        "description": "Store Tigrinya sentences in Qdrant",
    },
    {
        "id": "check_qdrant",
        "label": "Check Qdrant",
        "cmd": [sys.executable, str(ROOT / "check_qdrant.py")],
        "description": "Verify Qdrant is running and list collections",
    },
    {
        "id": "test_rag",
        "label": "Test RAG",
        "cmd": [sys.executable, str(ROOT / "test_rag.py")],
        "description": "Run RAG retrieval test",
    },
    {
        "id": "validate_results",
        "label": "Validate Results",
        "cmd": [sys.executable, str(ROOT / "validate_results.py")],
        "description": "Validate pipeline output",
    },
]

app = FastAPI(title="Tigrinya Script Runner")


def run_script_into_queue(script_id: str, queue: Queue):
    """Run a script in subprocess and put SSE chunks into thread-safe queue."""
    script = next((s for s in SCRIPTS if s["id"] == script_id), None)
    if not script:
        queue.put(f"data: {json.dumps({'type': 'error', 'line': 'Unknown script'})}\n\n")
        queue.put(None)
        return
    cmd = script["cmd"]
    cwd = str(ROOT)
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
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


async def stream_script(script_id: str):
    """Async generator that runs the script in a thread and streams SSE."""
    queue = Queue()
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, run_script_into_queue, script_id, queue)
    while True:
        chunk = await loop.run_in_executor(None, lambda: queue.get())
        if chunk is None:
            break
        yield chunk


@app.get("/", response_class=HTMLResponse)
def index():
    """Serve the single-page UI."""
    return get_html()


@app.get("/api/scripts")
def list_scripts():
    """Return list of runnable scripts."""
    return [{"id": s["id"], "label": s["label"], "description": s["description"]} for s in SCRIPTS]


@app.get("/run/{script_id}")
async def run_script(script_id: str):
    """Stream script output as Server-Sent Events."""
    return StreamingResponse(
        stream_script(script_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def get_html() -> str:
    """Inline HTML for the runner UI."""
    scripts_json = json.dumps([{"id": s["id"], "label": s["label"], "description": s["description"]} for s in SCRIPTS])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Tigrinya Script Runner</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      font-family: "SF Mono", "Fira Code", "Consolas", monospace;
      margin: 0;
      padding: 1rem 1.5rem;
      background: #0f0f12;
      color: #e4e4e7;
      min-height: 100vh;
    }}
    h1 {{
      font-size: 1.5rem;
      font-weight: 600;
      margin: 0 0 0.5rem 0;
      color: #fafafa;
    }}
    .sub {{
      color: #71717a;
      font-size: 0.875rem;
      margin-bottom: 1.25rem;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
      gap: 0.5rem;
      margin-bottom: 1.25rem;
    }}
    button {{
      font: inherit;
      padding: 0.6rem 0.9rem;
      background: #27272a;
      color: #e4e4e7;
      border: 1px solid #3f3f46;
      border-radius: 8px;
      cursor: pointer;
      transition: background 0.15s, border-color 0.15s;
    }}
    button:hover {{
      background: #3f3f46;
      border-color: #52525b;
    }}
    button:disabled {{
      opacity: 0.6;
      cursor: not-allowed;
    }}
    button.running {{
      background: #1e3a5f;
      border-color: #3b82f6;
    }}
    .output-wrap {{
      border: 1px solid #27272a;
      border-radius: 8px;
      background: #18181b;
      overflow: hidden;
    }}
    .output-header {{
      padding: 0.5rem 0.75rem;
      font-size: 0.75rem;
      color: #71717a;
      border-bottom: 1px solid #27272a;
    }}
    .output {{
      padding: 0.75rem 1rem;
      max-height: 420px;
      overflow-y: auto;
      white-space: pre-wrap;
      word-break: break-all;
      font-size: 0.8125rem;
      line-height: 1.5;
    }}
    .output:empty::before {{
      content: "Click a script to run it. Output will appear here.";
      color: #52525b;
    }}
    .status {{
      font-size: 0.8125rem;
      color: #a1a1aa;
      margin-bottom: 0.5rem;
    }}
    .status.running {{ color: #60a5fa; }}
    .status.done {{ color: #4ade80; }}
    .status.error {{ color: #f87171; }}
  </style>
</head>
<body>
  <h1>🇪🇷 Tigrinya Script Runner</h1>
  <p class="sub">Run pipeline scripts and see live output</p>
  <div class="grid" id="buttons"></div>
  <div class="status" id="status"></div>
  <div class="output-wrap">
    <div class="output-header">Output</div>
    <div class="output" id="output"></div>
  </div>
  <script>
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
      const others = document.querySelectorAll('.grid button');
      others.forEach(b => b.disabled = true);
      btn.classList.add('running');
      statusEl.textContent = 'Running ' + scriptId + '...';
      statusEl.className = 'status running';
      outputEl.textContent = '';

      try {{
        const res = await fetch('/run/' + scriptId);
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
              if (data.type === 'line') {{
                outputEl.textContent += data.line;
                outputEl.scrollTop = outputEl.scrollHeight;
              }} else if (data.type === 'done') {{
                statusEl.textContent = 'Finished (exit code ' + data.exit_code + ')';
                statusEl.className = data.exit_code === 0 ? 'status done' : 'status error';
              }} else if (data.type === 'error') {{
                outputEl.textContent += data.line;
                statusEl.textContent = 'Error';
                statusEl.className = 'status error';
              }}
            }} catch (_) {{}}
          }}
        }}
      }} catch (e) {{
        statusEl.textContent = 'Error: ' + e.message;
        statusEl.className = 'status error';
        outputEl.textContent += '\\n' + e.message;
      }} finally {{
        others.forEach(b => b.disabled = false);
        btn.classList.remove('running');
      }}
    }}
  </script>
</body>
</html>"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
