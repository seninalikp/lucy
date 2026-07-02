"""
agent_registry.py
Creates and reads Lucy's planned agent registry.
All agents are planned/inactive — none run in Part 1.
"""

import json
from pathlib import Path


PLANNED_AGENTS: list[dict] = [
    {
        "id": "ELIE",
        "full_form": "Executive Liaison Intelligence Engine",
        "status": "planned",
        "active": False,
        "role": "Future assistant/coordinator under Lucy",
        "spine_function": "Coordination, approvals, direct assistant interaction",
        "can_run": False,
        "can_modify_files": False,
        "can_access_api_keys": False,
        "can_move_money": False,
        "requires_lucy_approval": True,
        "report_types_later": ["daily_report", "approved_lessons", "risk_notes"],
    },
    {
        "id": "RAY",
        "full_form": "Rapid Automation Yield",
        "status": "planned",
        "active": False,
        "role": "Future automation specialist under Lucy",
        "spine_function": "Task automation, workflow execution",
        "can_run": False,
        "can_modify_files": False,
        "can_access_api_keys": False,
        "can_move_money": False,
        "requires_lucy_approval": True,
        "report_types_later": ["automation_report", "task_log"],
    },
    {
        "id": "ARES",
        "full_form": "Asset Research and Extraction System",
        "status": "planned",
        "active": False,
        "role": "Future research/data mining specialist under Lucy",
        "spine_function": "Data research, asset analysis",
        "can_run": False,
        "can_modify_files": False,
        "can_access_api_keys": False,
        "can_move_money": False,
        "requires_lucy_approval": True,
        "report_types_later": ["research_report", "data_summary"],
    },
    {
        "id": "VANTA",
        "full_form": "Volatility and Neutral Trading Analyst",
        "status": "planned",
        "active": False,
        "role": "Future trading analyst under Lucy",
        "spine_function": "Market analysis, trading signals (analysis only, no live trading)",
        "can_run": False,
        "can_modify_files": False,
        "can_access_api_keys": False,
        "can_move_money": False,
        "requires_lucy_approval": True,
        "report_types_later": ["market_report", "signal_log"],
    },
    {
        "id": "HAVEN",
        "full_form": "Health and Vitality Engine",
        "status": "planned",
        "active": False,
        "role": "Future health assistant under Lucy",
        "spine_function": "Health tracking support, wellness reminders",
        "can_run": False,
        "can_modify_files": False,
        "can_access_api_keys": False,
        "can_move_money": False,
        "requires_lucy_approval": True,
        "report_types_later": ["health_summary", "wellness_notes"],
    },
    {
        "id": "NEXUS",
        "full_form": "Network and Exchange Unified System",
        "status": "planned",
        "active": False,
        "role": "Future integration/connectivity layer under Lucy",
        "spine_function": "API integrations, service connections",
        "can_run": False,
        "can_modify_files": False,
        "can_access_api_keys": False,
        "can_move_money": False,
        "requires_lucy_approval": True,
        "report_types_later": ["integration_report", "connection_log"],
    },
    {
        "id": "ECHO",
        "full_form": "Event Capture and History Operations",
        "status": "planned",
        "active": False,
        "role": "Future event/history tracker under Lucy",
        "spine_function": "Event capture, historical log analysis",
        "can_run": False,
        "can_modify_files": False,
        "can_access_api_keys": False,
        "can_move_money": False,
        "requires_lucy_approval": True,
        "report_types_later": ["event_summary", "history_report"],
    },
    {
        "id": "LEDGER",
        "full_form": "Logging and Expense Data Generator/Reporter",
        "status": "planned",
        "active": False,
        "role": "Future financial ledger/reporting agent under Lucy",
        "spine_function": "Expense tracking, financial summaries",
        "can_run": False,
        "can_modify_files": False,
        "can_access_api_keys": False,
        "can_move_money": False,
        "requires_lucy_approval": True,
        "report_types_later": ["ledger_report", "expense_summary"],
    },
    {
        "id": "SABLE",
        "full_form": "Secure Archive and Backup Logistics Engine",
        "status": "planned",
        "active": False,
        "role": "Future backup/archival specialist under Lucy",
        "spine_function": "Secure backup, archive management",
        "can_run": False,
        "can_modify_files": False,
        "can_access_api_keys": False,
        "can_move_money": False,
        "requires_lucy_approval": True,
        "report_types_later": ["backup_report", "archive_log"],
    },
    {
        "id": "ORBIT",
        "full_form": "Operations and Resource Balancing Intelligence Tracker",
        "status": "planned",
        "active": False,
        "role": "Future resource monitoring agent under Lucy",
        "spine_function": "System resource tracking, operational monitoring",
        "can_run": False,
        "can_modify_files": False,
        "can_access_api_keys": False,
        "can_move_money": False,
        "requires_lucy_approval": True,
        "report_types_later": ["resource_report", "ops_summary"],
    },
    {
        "id": "NOVA",
        "full_form": "Novelty and Output Visualization Agent",
        "status": "planned",
        "active": False,
        "role": "Future creative/visualization agent under Lucy",
        "spine_function": "Creative output, visualization, UI generation",
        "can_run": False,
        "can_modify_files": False,
        "can_access_api_keys": False,
        "can_move_money": False,
        "requires_lucy_approval": True,
        "report_types_later": ["creative_report", "output_summary"],
        "future_submodules": [
            {
                "id": "FRAME",
                "description": "Future visual framing module under NOVA. Not an active agent.",
                "status": "planned_submodule",
                "active": False,
            }
        ],
    },
    {
        "id": "MINT",
        "full_form": "Management and Intelligence Notation Tool",
        "status": "planned",
        "active": False,
        "role": "Future notation/knowledge management agent under Lucy",
        "spine_function": "Note management, knowledge capture",
        "can_run": False,
        "can_modify_files": False,
        "can_access_api_keys": False,
        "can_move_money": False,
        "requires_lucy_approval": True,
        "report_types_later": ["knowledge_report", "note_summary"],
    },
    {
        "id": "ATLAS",
        "full_form": "Adaptive Task and Logistics Allocation System",
        "status": "planned",
        "active": False,
        "role": "Future task allocation/project management agent under Lucy",
        "spine_function": "Task planning, project tracking",
        "can_run": False,
        "can_modify_files": False,
        "can_access_api_keys": False,
        "can_move_money": False,
        "requires_lucy_approval": True,
        "report_types_later": ["project_report", "task_summary"],
    },
    {
        "id": "JESTER",
        "full_form": "Judgment and Entertainment System for Testing/Experimentation Runtime",
        "status": "planned",
        "active": False,
        "role": "Future testing/experimentation sandbox agent under Lucy",
        "spine_function": "Safe experimentation, sandbox testing",
        "can_run": False,
        "can_modify_files": False,
        "can_access_api_keys": False,
        "can_move_money": False,
        "requires_lucy_approval": True,
        "report_types_later": ["test_report", "experiment_log"],
    },
]

REGISTRY_HEADER = {
    "version": "0.1.0",
    "managed_by": "LUCY",
    "note": (
        "These agents are planned under Lucy but are not active yet. "
        "No agent can run, execute code, modify files, or use APIs without "
        "Lucy approval and an explicit activation checkpoint."
    ),
    "agents": PLANNED_AGENTS,
}


class AgentRegistry:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.registry_file = data_dir / "agent_registry.json"
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not self.registry_file.exists():
            self.registry_file.write_text(
                json.dumps(REGISTRY_HEADER, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

    def _read(self) -> dict:
        try:
            return json.loads(self.registry_file.read_text(encoding="utf-8"))
        except Exception:
            return dict(REGISTRY_HEADER)

    def list_agents(self) -> list[dict]:
        return self._read().get("agents", [])

    def get_agent(self, agent_id: str) -> dict | None:
        for agent in self.list_agents():
            if agent["id"].upper() == agent_id.upper():
                return agent
        return None

    def any_active(self) -> bool:
        return any(a.get("active", False) for a in self.list_agents())
