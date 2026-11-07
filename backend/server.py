import json
import os
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, jsonify, send_from_directory, request, redirect, Response

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter

# Dedicated Sovereign Open WebUI (Port 8090) powered by LucyRuntime 300-Stage Brain
app = Flask(__name__)

_lucy_runtime = None
_lucy_router = None
_chat_lock = threading.Lock()

SPINE_PATH = PROJECT_ROOT / "spine.json"


@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    return response


def get_lucy_router():
    global _lucy_runtime, _lucy_router
    with _chat_lock:
        if _lucy_router is None:
            _lucy_runtime = LucyRuntime(project_root=PROJECT_ROOT)
            _lucy_router = CommandRouter(_lucy_runtime)
        return _lucy_router


def load_spine() -> dict:
    if not SPINE_PATH.exists():
        return {"error": "spine.json not found"}
    try:
        with open(SPINE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"error": f"Failed to load spine: {e}"}


def save_spine(data: dict) -> bool:
    try:
        with open(SPINE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving spine: {e}")
        return False


# ─────────────────────────────────────────
# OLLAMA PROTOCOL ADAPTER (STAGES 1–301 RUNTIME BRIDGE)
# ─────────────────────────────────────────

@app.route("/api/version", methods=["GET"])
def ollama_version():
    """Ollama API version handshake."""
    return jsonify({"version": "0.5.1"})


@app.route("/api/tags", methods=["GET"])
def ollama_tags():
    """Disclose Lucy Sovereign Mind as the active Ollama model."""
    return jsonify({
        "models": [
            {
                "name": "lucy:personal",
                "model": "lucy:personal",
                "modified_at": datetime.now(timezone.utc).isoformat(),
                "size": 1929912783,
                "digest": "lucy-personal-stage301",
                "details": {
                    "parent_model": "lucy:personal",
                    "format": "gguf",
                    "family": "qwen2",
                    "families": ["qwen2"],
                    "parameter_size": "3.1B",
                    "quantization_level": "Q4_K_M"
                },
                "capabilities": ["completion"]
            }
        ]
    })


@app.route("/api/show", methods=["POST"])
def ollama_show():
    """Model information endpoint."""
    return jsonify({
        "license": "LUCY Sovereign Operating Assistant — Personal AI Mind for Senin",
        "modelfile": "FROM lucy:personal\nSYSTEM You are LUCY, personal operating assistant for Senin.",
        "parameters": "temperature 0.25\nnum_ctx 2048",
        "template": "{{ .Prompt }}",
        "details": {
            "parent_model": "",
            "format": "gguf",
            "family": "qwen2",
            "parameter_size": "3.1B",
            "quantization_level": "Q4_K_M"
        }
    })


@app.route("/api/chat", methods=["POST"])
def chat_with_lucy():
    """
    Unified chat endpoint.
    Handles both Open WebUI Ollama requests and legacy /api/chat requests.
    Routes ALL prompts through LucyRuntime (all 300 stages + LoRA Harvester).
    """
    body = request.get_json(silent=True) or {}
    
    # 1. Detect if this is an Ollama / Open WebUI message array
    if "messages" in body:
        messages = body.get("messages", [])
        stream = body.get("stream", False)

        # Extract last user message
        user_message = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_message = m.get("content", "")
                break
        
        user_message = str(user_message or "").strip()
        if not user_message:
            user_message = "hello"

        # Fast path for Open WebUI background title / tags generation tasks
        if "### Task:" in user_message or "Generate a concise" in user_message or "Generate a title" in user_message:
            if "tags" in user_message.lower():
                reply_text = '["lucy", "chat"]'
            else:
                reply_text = "💬 Lucy Conversation"
        else:
            # Dispatch through Lucy's complete 300-Stage Brain
            router = get_lucy_router()
            with _chat_lock:
                response = router.handle(user_message)
            reply_text = response.message if hasattr(response, "message") else str(response)

        now_str = datetime.now(timezone.utc).isoformat()

        if stream:
            def generate():
                chunk_content = {
                    "model": "lucy:personal",
                    "created_at": now_str,
                    "message": {"role": "assistant", "content": reply_text},
                    "done": False
                }
                yield json.dumps(chunk_content) + "\n"

                chunk_done = {
                    "model": "lucy:personal",
                    "created_at": now_str,
                    "done": True,
                    "total_duration": 1500000,
                    "load_duration": 100000,
                    "prompt_eval_count": 12,
                    "eval_count": len(reply_text.split())
                }
                yield json.dumps(chunk_done) + "\n"

            return Response(generate(), mimetype="application/x-ndjson")
        else:
            return jsonify({
                "model": "lucy:personal",
                "created_at": now_str,
                "message": {"role": "assistant", "content": reply_text},
                "done": True
            })

    # 2. Legacy Lucy API support
    message = body.get("message", "")
    if not isinstance(message, str):
        return jsonify({"error": "message must be a string"}), 400

    message = message.strip()
    if len(message) > 4000:
        return jsonify({"error": "message is too long"}), 413

    router = get_lucy_router()
    with _chat_lock:
        response = router.handle(message)

    return jsonify({
        "reply": response.message,
        "should_exit": response.should_exit,
        "timestamp": datetime.now().isoformat(),
    })


@app.route("/api/generate", methods=["POST"])
def ollama_generate():
    """Simple generate prompt endpoint."""
    body = request.get_json(silent=True) or {}
    prompt = body.get("prompt", "hello")
    stream = body.get("stream", False)

    # Fast path for Open WebUI background tasks
    if "### Task:" in prompt or "Generate a concise" in prompt or "Generate a title" in prompt:
        if "tags" in prompt.lower():
            reply_text = '["lucy", "chat"]'
        else:
            reply_text = "💬 Lucy Conversation"
    else:
        router = get_lucy_router()
        with _chat_lock:
            response = router.handle(prompt)
        reply_text = response.message if hasattr(response, "message") else str(response)

    now_str = datetime.now(timezone.utc).isoformat()

    if stream:
        def generate():
            yield json.dumps({"model": "lucy:personal", "created_at": now_str, "response": reply_text, "done": False}) + "\n"
            yield json.dumps({"model": "lucy:personal", "created_at": now_str, "done": True}) + "\n"
        return Response(generate(), mimetype="application/x-ndjson")
    else:
        return jsonify({
            "model": "lucy:personal",
            "created_at": now_str,
            "response": reply_text,
            "done": True
        })


# ─────────────────────────────────────────
# SPINE & AGENT GOVERNANCE ENDPOINTS
# ─────────────────────────────────────────

@app.route("/api/spine", methods=["GET"])
def get_full_spine():
    """Full spine config."""
    return jsonify(load_spine())


@app.route("/api/lucy", methods=["GET"])
def get_lucy_status():
    """Lucy core identity and status."""
    spine = load_spine()
    return jsonify(spine["lucy"])


@app.route("/api/agents", methods=["GET"])
def get_agents():
    """All agents with full data."""
    spine = load_spine()
    return jsonify(spine["agents"])


@app.route("/api/agents/<agent_id>", methods=["GET"])
def get_agent(agent_id):
    """Single agent by ID."""
    spine = load_spine()
    agent = spine["agents"].get(agent_id)
    if not agent:
        return jsonify({"error": f"Agent '{agent_id}' not found"}), 404
    return jsonify(agent)


@app.route("/api/agents/<agent_id>/stage", methods=["PATCH"])
def update_agent_stage(agent_id):
    spine = load_spine()
    if agent_id not in spine["agents"]:
        return jsonify({"error": f"Agent '{agent_id}' not found"}), 404

    body = request.get_json(silent=True) or {}
    new_stage = body.get("stage")

    valid_stages = ["concept", "blueprint", "scaffold", "proto", "testing", "live", "paused"]
    if new_stage not in valid_stages:
        return jsonify({
            "error": f"Invalid stage '{new_stage}'. Must be one of: {valid_stages}"
        }), 400

    spine["agents"][agent_id]["stage"] = new_stage
    spine["agents"][agent_id]["updated_at"] = datetime.now().isoformat()

    if save_spine(spine):
        return jsonify({
            "status": "updated",
            "agent_id": agent_id,
            "new_stage": new_stage,
            "timestamp": datetime.now().isoformat()
        })
    else:
        return jsonify({"error": "Failed to save spine.json"}), 500


@app.route("/api/safety", methods=["GET"])
def get_safety_rules():
    """All safety rules."""
    spine = load_spine()
    return jsonify(spine["safety"])


@app.route("/api/permissions", methods=["GET"])
def get_permissions():
    """Permission level model."""
    spine = load_spine()
    return jsonify(spine["permissions"])


@app.route("/api/build-order", methods=["GET"])
def get_build_order():
    """Agents sorted by build order with their current stage."""
    spine = load_spine()
    agents = spine["agents"]
    sorted_agents = sorted(
        [{"id": aid, **adata} for aid, adata in agents.items()],
        key=lambda a: a.get("build_order", 999)
    )
    return jsonify(sorted_agents)


@app.route("/api/memory-filter", methods=["GET"])
def get_memory_filter():
    """Memory retention tier configuration."""
    spine = load_spine()
    return jsonify(spine["memory_filter"])


@app.route("/api/status-summary", methods=["GET"])
def get_status_summary():
    """High-level summary of the whole system for dashboard display."""
    spine = load_spine()
    lucy = spine["lucy"]
    agents = spine["agents"]

    stages = {}
    for a in agents.values():
        s = a.get("stage", "unknown")
        stages[s] = stages.get(s, 0) + 1

    next_agent = min(
        [a for a in agents.values() if a.get("stage") not in ("live", "paused")],
        key=lambda a: a.get("build_order", 999),
        default=None
    )

    return jsonify({
        "lucy_phase": lucy["phase"],
        "lucy_version": lucy["version"],
        "lucy_status": lucy["status"],
        "apis_connected": lucy["apis_connected"],
        "live_trading_enabled": lucy["live_trading_enabled"],
        "root_access_enabled": lucy["root_access_enabled"],
        "total_agents": len(agents),
        "stage_counts": stages,
        "next_to_build": next_agent["id"] if next_agent else None,
        "timestamp": datetime.now().isoformat()
    })


@app.route("/api/spine/reload", methods=["POST"])
def reload_spine():
    """Force a reload confirmation (spine is always fresh-loaded per request)."""
    spine = load_spine()
    return jsonify({
        "status": "reloaded",
        "lucy_version": spine["lucy"]["version"],
        "agent_count": len(spine["agents"]),
        "timestamp": datetime.now().isoformat()
    })


# ─────────────────────────────────────────
# STAGES 54–59 COGNITIVE OPERATOR API
# ─────────────────────────────────────────

@app.route("/api/proactive-brief", methods=["GET"])
def get_proactive_brief():
    """Stage 58 Proactive Executive Briefing."""
    get_lucy_router()
    brief = _lucy_runtime.proactive_briefer.generate_brief()
    return jsonify(brief)


@app.route("/api/workspace-pulse", methods=["GET"])
def get_workspace_pulse():
    """Stage 57 Live Workspace & Git Pulse."""
    get_lucy_router()
    pulse = _lucy_runtime.workspace_sensor.scan_workspace()
    return jsonify(pulse)


@app.route("/api/memory-graph", methods=["GET"])
def get_memory_graph():
    """Stage 54 Temporal Memory Graph status."""
    get_lucy_router()
    graph_st = _lucy_runtime.memory_graph.status() if hasattr(_lucy_runtime, "memory_graph") else {}
    return jsonify(graph_st)


@app.route("/api/execution-receipts", methods=["GET"])
def get_execution_receipts():
    """Stage 55 Cryptographic Execution Receipt Ledger."""
    get_lucy_router()
    receipts_st = _lucy_runtime.receipt_ledger.status() if hasattr(_lucy_runtime, "receipt_ledger") else {}
    return jsonify(receipts_st)


@app.route("/api/lora/status", methods=["GET"])
def get_lora_status():
    """Stage 42/45 LoRA Alignment and Two-Speed Adaptation status."""
    get_lucy_router()
    lora_st = _lucy_runtime.personal_alignment.status() if hasattr(_lucy_runtime, "personal_alignment") else {}
    return jsonify(lora_st)


@app.route("/api/training-queue", methods=["GET"])
def get_training_queue():
    """Verified Training Queue status."""
    get_lucy_router()
    queue_st = _lucy_runtime.training_queue.status() if hasattr(_lucy_runtime, "training_queue") else {}
    return jsonify(queue_st)


@app.route("/api/natural-actions", methods=["GET"])
def get_natural_actions_status():
    """Stage 59 Natural-Language Action Parser status."""
    get_lucy_router()
    parser_st = _lucy_runtime.natural_action_parser.status() if hasattr(_lucy_runtime, "natural_action_parser") else {}
    return jsonify(parser_st)


# ─────────────────────────────────────────
# DEDICATED SOVEREIGN OPEN WEBUI REDIRECT (PORT 8090)
# ─────────────────────────────────────────

@app.route("/")
def index():
    return redirect("http://localhost:8090")


@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "status": "error",
        "message": "Resource not found on spine server. Lucy's Web UI is running at http://localhost:8090"
    }), 404


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

def start_server(port: int | None = None, host: str = "127.0.0.1", debug: bool = False, open_browser: bool = False) -> None:
    if port is None:
        port = int(os.environ.get("LUCY_PORT", 7700))
    print(f"\n  LUCY SOVEREIGN RUNTIME BRIDGE (STAGES 1-301)")
    print(f"  Ollama Protocol Adapter listening at: http://127.0.0.1:{port}")
    print(f"  Connected to Open WebUI at: http://localhost:8090")
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == "__main__":
    start_server(debug=False)
