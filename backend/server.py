"""
LUCY — Part 0: Spine Config Server
Serves the spine.json as a live API with endpoints for each section.
No auth, no DB — spine.json IS the source of truth at this phase.
"""

import json
import os
import sys
import threading
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, send_from_directory, request


PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter

app = Flask(__name__, static_folder="../frontend", static_url_path="")

_lucy_runtime = None
_lucy_router = None
_chat_lock = threading.Lock()



@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

SPINE_PATH = PROJECT_ROOT / "data" / "spine.json"


def get_lucy_router():
    global _lucy_runtime, _lucy_router
    if _lucy_router is None:
        _lucy_runtime = LucyRuntime(project_root=PROJECT_ROOT)
        _lucy_router = CommandRouter(_lucy_runtime)
    return _lucy_router


def load_spine():
    """Load the spine config fresh each call — live editing supported."""
    with open(SPINE_PATH, "r") as f:
        return json.load(f)


def save_spine(data):
    """Save spine config with backup."""
    backup_path = SPINE_PATH.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    if SPINE_PATH.exists():
        with open(backup_path, "w") as f:
            json.dump(load_spine(), f, indent=2)
    with open(SPINE_PATH, "w") as f:
        json.dump(data, f, indent=2)


# ─────────────────────────────────────────
# SPINE ENDPOINTS
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
    agent = next((a for a in spine["agents"] if a["id"] == agent_id.upper()), None)
    if not agent:
        return jsonify({"error": f"Agent {agent_id} not found"}), 404
    return jsonify(agent)


@app.route("/api/agents/<agent_id>/stage", methods=["PATCH"])
def update_agent_stage(agent_id):
    """
    Update an agent's build stage.
    Requires explicit confirmation in request body.
    Body: { "stage": "beta", "confirmed": true, "reason": "..." }
    """
    body = request.get_json()
    if not body or not body.get("confirmed"):
        return jsonify({"error": "Explicit confirmation required. Set confirmed: true."}), 403

    valid_stages = ["planned", "prototype", "beta", "stable", "mature"]
    new_stage = body.get("stage", "").lower()
    if new_stage not in valid_stages:
        return jsonify({"error": f"Invalid stage. Must be one of: {valid_stages}"}), 400

    spine = load_spine()
    agent = next((a for a in spine["agents"] if a["id"] == agent_id.upper()), None)
    if not agent:
        return jsonify({"error": f"Agent {agent_id} not found"}), 404

    old_stage = agent["stage"]
    agent["stage"] = new_stage
    agent["last_stage_change"] = datetime.now().isoformat()
    agent["stage_change_reason"] = body.get("reason", "No reason provided")

    save_spine(spine)
    return jsonify({
        "agent": agent_id.upper(),
        "old_stage": old_stage,
        "new_stage": new_stage,
        "timestamp": datetime.now().isoformat()
    })


@app.route("/api/safety", methods=["GET"])
def get_safety_rules():
    """All safety rules."""
    spine = load_spine()
    return jsonify(spine["safety_rules"])


@app.route("/api/permissions", methods=["GET"])
def get_permissions():
    """Permission level model."""
    spine = load_spine()
    return jsonify(spine["permission_model"])


@app.route("/api/build-order", methods=["GET"])
def get_build_order():
    """Agents sorted by build order with their current stage."""
    spine = load_spine()
    agents = sorted(spine["agents"], key=lambda a: a["build_order"])
    return jsonify([{
        "build_order": a["build_order"],
        "id": a["id"],
        "full_name": a["full_name"],
        "stage": a["stage"],
        "type": a["type"]
    } for a in agents])


@app.route("/api/memory-filter", methods=["GET"])
def get_memory_filter():
    """The three-layer memory filter."""
    spine = load_spine()
    return jsonify(spine["memory_filter"])


@app.route("/api/playground", methods=["GET"])
def get_playground():
    """Playground config."""
    spine = load_spine()
    return jsonify(spine["playground"])


@app.route("/api/status", methods=["GET"])
def get_system_status():
    """Quick system overview — what's on, what's off, what's next."""
    spine = load_spine()
    lucy = spine["lucy"]
    agents = spine["agents"]

    stages = {}
    for a in agents:
        stages[a["stage"]] = stages.get(a["stage"], 0) + 1

    next_agent = next(
        (a for a in sorted(agents, key=lambda x: x["build_order"]) if a["stage"] == "planned"),
        None
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


@app.route("/api/chat", methods=["POST"])
def chat_with_lucy():
    """Send a message through Lucy's command/conversation router."""
    body = request.get_json(silent=True) or {}
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


# ─────────────────────────────────────────
# SERVE FRONTEND
# ─────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.errorhandler(404)
def not_found(e):
    # SPA fallback
    return send_from_directory(app.static_folder, "index.html")


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("LUCY_PORT", 7700))
    print(f"\n  LUCY SPINE SERVER")
    print(f"  Phase: {load_spine()['lucy']['phase']}")
    print(f"  Running at: http://localhost:{port}")
    print(f"  Spine file: {SPINE_PATH}")
    print(f"  Edit spine.json and refresh — changes are live.\n")
    app.run(host="0.0.0.0", port=port, debug=True)
