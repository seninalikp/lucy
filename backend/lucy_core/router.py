"""
router.py
Command router for Lucy's terminal interface.
"""

from __future__ import annotations

from typing import Any

import json
import re
import time
import hashlib
from dataclasses import dataclass

from backend.lucy_core.command_normalizer import normalize_command


@dataclass
class RouterResponse:
    message: str
    should_exit: bool = False
    data: Any = None


class CommandRouter:
    def __init__(self, runtime) -> None:
        self.runtime = runtime

    def handle(self, raw_text: str, _reset_turn: bool = True) -> RouterResponse:
        # Stage 55: Cryptographic receipt ledger begins fresh turn
        if _reset_turn and hasattr(self.runtime, "receipt_ledger") and hasattr(self.runtime.receipt_ledger, "begin_turn"):
            self.runtime.receipt_ledger.begin_turn()
        response = self._handle(raw_text)
        if not response.should_exit:
            self.runtime.record_interaction(raw_text, response.message)
        return response

    dispatch = handle

    def _handle(self, raw_text: str) -> RouterResponse:
        text = str(raw_text or "").strip()
        normalized = normalize_command(text)
        if normalized.clarification:
            return RouterResponse(normalized.clarification)
        text = normalized.text
        lowered = text.lower()


        if not text:
            return RouterResponse(self.runtime.conversation.respond(text))

        if lowered in {"exit", "quit", "bye"}:
            result = self.runtime.graceful_shutdown("User exited Lucy cleanly.")
            return RouterResponse(result.get("shutdown_message", "Lucy shutting down cleanly."), should_exit=True)

        # Sovereign Identity & Creator Query Interception
        if re.search(r"\b(?:who\s+(?:program+ed|made|created|built|designed|developed|coded)\s+you|who\s+is\s+your\s+(?:creator|programmer|maker|author|developer|designer)|tell\s+me\s+who\s+(?:program+ed|made|created|built|designed|developed|coded)\s+you)\b", lowered):
            return RouterResponse(
                "You programmed and created me, Senin. I am LUCY (Living Unified Cognitive Yield), your sovereign local AI desktop operating companion. External APIs and local neural weights (such as Ollama qwen2.5:3b) are tools I operate, not my creators or identity."
            )

        # Operator Name & Identity Interception
        if re.search(r"\b(?:do\s+you\s+know\s+my\s+name|what\s+is\s+my\s+name|what'?s\s+my\s+name|what\s+is\s+my\s+full\s+name|what'?s\s+my\s+full\s+name|who\s+am\s+i|tell\s+me\s+my\s+name|do\s+you\s+know\s+who\s+i\s+am)\b", lowered):
            return RouterResponse(
                "Yes, of course. Your name is Senin, and your full name is Senin Ali K P (Ali is your middle name). You are my creator, programmer, and primary operator."
            )

        if re.search(r"^(?:who\s+are\s+you|who\s+r\s+u|what\s+are\s+you)(?:\s+lucy)?\??$", lowered):
            return RouterResponse(
                "I am LUCY (Living Unified Cognitive Yield), a sovereign local AI desktop operating companion created and programmed by you, Senin."
            )

        # Network & Internet Connectivity Ground Truth
        if re.search(r"\b(?:are\s+you\s+(?:connected\s+to\s+(?:the\s+)?internet|online)|is\s+(?:she|lucy)\s+connected\s+to\s+(?:the\s+)?internet|do\s+you\s+have\s+internet(?:\s+access)?)\b", lowered):
            return RouterResponse(
                "My neural core and personal memory run 100% locally and offline on your machine via Ollama (qwen2.5:3b). "
                "However, your machine has an active network connection, and I have web tools enabled (Stages 81-83: "
                "/web-search, /web-inspect, /verify-web) whenever you want me to search docs, PyPI, or live web sources."
            )

        # Web Search Capability Inquiries
        if re.search(r"\b(?:can\s+(?:you|she|lucy)\s+s(?:ea|e)rch(?:\s+(?:things|the\s+web|online|google|for\s+me))?|how\s+do\s+i\s+search(?:\s+the\s+web)?|can\s+i\s+search)\b", lowered):
            return RouterResponse(
                "Yes, absolutely! I have sovereign web explorer and live documentation tools built in (Stages 81-83).\n\n"
                "You can search and inspect the web directly from this terminal:\n"
                "  + `search <query>` or `/search <query>`      - Live web search via DuckDuckGo\n"
                "  + `/pypi <package>`                          - Inspect live PyPI package versions & metadata\n"
                "  + `/fetch <url>`                             - Read live web pages and extract technical docs\n"
                "  + `/verify-web <claim>`                      - Fact-check technical claims against live web sources\n\n"
                "Example: Type `search python 3.14 release date` or `/pypi fastapi`."
            )

        # Natural Web Search Execution (Stage 81)
        web_search_match = re.match(r"^(?:/web-search|/search|web[-_ ]?search|s(?:ea|e)rch(?:\s+(?:the\s+web|online|google))?\s+for|s(?:ea|e)rch)\s+(.+)$", text, re.I)
        if web_search_match and hasattr(self.runtime, "web_explorer"):
            query = web_search_match.group(1).strip()
            if query.lower().startswith("for "):
                query = query[4:].strip()
            if query and not query.lower().startswith('memory '):
                res = self.runtime.web_explorer.search(query)
                return RouterResponse(res.format_terminal_summary(), data=res)

        # Sovereign Web Reader Commands (Stage 82)
        if text.startswith("/pypi ") or text.startswith("pypi "):
            pkg_name = text.split(" ", 1)[1].strip()
            if hasattr(self.runtime, "web_reader"):
                info = self.runtime.web_reader.fetch_pypi_package(pkg_name)
                return RouterResponse(self.runtime.web_reader.format_pypi_summary(info), data=info)

        if text.startswith("/fetch ") or text.startswith("fetch "):
            target_url = text.split(" ", 1)[1].strip()
            if hasattr(self.runtime, "web_reader"):
                page = self.runtime.web_reader.fetch_url(target_url)
                return RouterResponse(page.format_terminal_summary(), data=page)

        # Sovereign Web Verifier (Stage 83)
        if text.startswith("/verify-web ") or text.startswith("verify-web "):
            claim_text = text.split(" ", 1)[1].strip()
            if hasattr(self.runtime, "web_verifier"):
                res = self.runtime.web_verifier.verify_claim(claim_text)
                return RouterResponse(res.format_terminal_summary(), data=res)

        # Stage 91: Autonomous Code Mutation & Fuzz Tester
        if lowered in {"/mutation-stats", "mutation-stats", "/fuzz-stats", "fuzz-stats"}:
            if hasattr(self.runtime, "mutation_fuzzer"):
                return RouterResponse(self.runtime.mutation_fuzzer.format_terminal_summary())

        if lowered in {"/fuzz-cli", "fuzz-cli", "/fuzz", "fuzz"}:
            if hasattr(self.runtime, "mutation_fuzzer"):
                report = self.runtime.mutation_fuzzer.fuzz_cli()
                return RouterResponse(report.format_terminal_summary(), data=report.to_dict())

        if lowered.startswith("/mutate ") or lowered.startswith("mutate "):
            prefix = "/mutate " if lowered.startswith("/mutate ") else "mutate "
            target = text[len(prefix):].strip()
            if hasattr(self.runtime, "mutation_fuzzer"):
                report = self.runtime.mutation_fuzzer.run_mutation_test(target)
                return RouterResponse(report.format_terminal_summary(), data=report.to_dict())

        # Stage 92: Self-Healing Runtime Patch Engine
        if lowered in {"/patch-ledger", "patch-ledger"}:
            if hasattr(self.runtime, "self_healing_patcher"):
                return RouterResponse(self.runtime.self_healing_patcher.format_ledger_summary())

        if lowered.startswith("/patch-diff ") or lowered.startswith("patch-diff "):
            prefix = "/patch-diff " if lowered.startswith("/patch-diff ") else "patch-diff "
            pid = text[len(prefix):].strip()
            if hasattr(self.runtime, "self_healing_patcher"):
                return RouterResponse(self.runtime.self_healing_patcher.get_patch_diff(pid))

        if lowered.startswith("/rollback-patch ") or lowered.startswith("rollback-patch "):
            prefix = "/rollback-patch " if lowered.startswith("/rollback-patch ") else "rollback-patch "
            pid = text[len(prefix):].strip()
            if hasattr(self.runtime, "self_healing_patcher"):
                ok, msg = self.runtime.self_healing_patcher.rollback_patch(pid)
                return RouterResponse(f"[Rollback {'SUCCESS' if ok else 'FAILED'}] {msg}")

        if lowered.startswith("/heal ") or lowered.startswith("heal "):
            prefix = "/heal " if lowered.startswith("/heal ") else "heal "
            target = raw_text.strip()[len(prefix):].strip() if raw_text.strip().lower().startswith(prefix) else text[len(prefix):].strip()
            if hasattr(self.runtime, "self_healing_patcher"):
                res = self.runtime.self_healing_patcher.heal(target)
                return RouterResponse(res)

        # Stage 93: Semantic AST Vector Code Indexer
        if lowered in {"/index-repo", "index-repo", "/reindex-code", "reindex-code"}:
            if hasattr(self.runtime, "ast_vector_index"):
                summary = self.runtime.ast_vector_index.index_repository()
                return RouterResponse(summary.format_terminal_summary(), data=summary.to_dict())

        if lowered.startswith("/code-search ") or lowered.startswith("code-search "):
            prefix = "/code-search " if lowered.startswith("/code-search ") else "code-search "
            query = text[len(prefix):].strip()
            if hasattr(self.runtime, "ast_vector_index"):
                matches = self.runtime.ast_vector_index.search(query)
                return RouterResponse(self.runtime.ast_vector_index.format_search_results(query, matches))

        if lowered.startswith("/symbol-tree ") or lowered.startswith("symbol-tree "):
            prefix = "/symbol-tree " if lowered.startswith("/symbol-tree ") else "symbol-tree "
            target = text[len(prefix):].strip()
            if hasattr(self.runtime, "ast_vector_index"):
                return RouterResponse(self.runtime.ast_vector_index.get_symbol_tree(target))

        # Stage 94: Architecture Specification Drift Detector & Realignment Engine
        if lowered in {"/spec-audit", "spec-audit", "/drift-report", "drift-report"}:
            if hasattr(self.runtime, "spec_drift_detector"):
                report = self.runtime.spec_drift_detector.audit()
                return RouterResponse(report.format_terminal_summary(), data=report.to_dict())

        if lowered.startswith("/realign-spec") or lowered.startswith("realign-spec"):
            prefix = "/realign-spec" if lowered.startswith("/realign-spec") else "realign-spec"
            spec_arg = text[len(prefix):].strip() or None
            if hasattr(self.runtime, "spec_drift_detector"):
                res = self.runtime.spec_drift_detector.realign_spec(spec_arg)
                return RouterResponse(res.get("terminal_summary", res.get("message", "Realignment complete.")), data=res)

        # Stage 95: Multi-Agent Autonomous Worktree & Branching Fabric
        if lowered in {"/tree-status", "tree-status", "/worktrees", "worktrees"}:
            if hasattr(self.runtime, "worktree_fabric"):
                return RouterResponse(self.runtime.worktree_fabric.tree_status(), data=self.runtime.worktree_fabric.status())

        if lowered in {"/list-branches", "list-branches"}:
            if hasattr(self.runtime, "worktree_fabric"):
                branches = self.runtime.worktree_fabric.list_branches()
                return RouterResponse(self.runtime.worktree_fabric.tree_status(), data=[b.to_dict() for b in branches])

        if lowered.startswith("/spawn-branch ") or lowered.startswith("spawn-branch "):
            prefix = "/spawn-branch " if lowered.startswith("/spawn-branch ") else "spawn-branch "
            parts = text[len(prefix):].strip().split(" ", 1)
            bname = parts[0].strip()
            task = parts[1].strip() if len(parts) > 1 else ""
            if hasattr(self.runtime, "worktree_fabric"):
                branch = self.runtime.worktree_fabric.spawn_branch(bname, task=task)
                msg = f"[Worktree Spawned] Branch: '{branch.branch_name}' (ID: {branch.branch_id})\nDirectory: {branch.worktree_dir}\nRole: {branch.agent_role}"
                return RouterResponse(msg, data=branch.to_dict())

        if lowered.startswith("/merge-worktree ") or lowered.startswith("merge-worktree "):
            prefix = "/merge-worktree " if lowered.startswith("/merge-worktree ") else "merge-worktree "
            bname = text[len(prefix):].strip()
            if hasattr(self.runtime, "worktree_fabric"):
                res = self.runtime.worktree_fabric.merge_worktree(bname)
                status_str = "SUCCESS" if res.success else "FAILED"
                msg = f"[Worktree Merge: {status_str}] {res.message}"
                return RouterResponse(msg, data=res.to_dict())

        # Stage 96: Sovereign Offline Quantization & GGUF Model Compressor
        if lowered in {"/quant-status", "quant-status", "/list-quants", "list-quants"}:
            if hasattr(self.runtime, "model_quantizer"):
                return RouterResponse(self.runtime.model_quantizer.quant_status(), data=self.runtime.model_quantizer.list_quants())

        if lowered.startswith("/quantize-weights ") or lowered.startswith("quantize-weights "):
            prefix = "/quantize-weights " if lowered.startswith("/quantize-weights ") else "quantize-weights "
            parts = text[len(prefix):].strip().split(" ", 1)
            target_model = parts[0].strip()
            qtype = parts[1].strip() if len(parts) > 1 else "Q4_K_M"
            if hasattr(self.runtime, "model_quantizer"):
                res = self.runtime.model_quantizer.quantize_weights(target_model, quant_type=qtype)
                msg = f"[Quantization {res.status}] Model: '{res.model_name}' ({res.quant_type})\nOutput: {res.output_path}\nRatio: {res.compression_ratio}x | VRAM: ~{res.vram_estimate_mb:.0f} MB | SNR: {res.snr_db:.1f} dB"
                return RouterResponse(msg, data=res.to_dict())

        if lowered.startswith("/gguf-export ") or lowered.startswith("gguf-export "):
            prefix = "/gguf-export " if lowered.startswith("/gguf-export ") else "gguf-export "
            parts = text[len(prefix):].strip().split(" ", 1)
            target_model = parts[0].strip()
            qtype = parts[1].strip() if len(parts) > 1 else "Q4_K_M"
            if hasattr(self.runtime, "model_quantizer"):
                export_data = self.runtime.model_quantizer.export_gguf(target_model, quant_type=qtype)
                msg = f"[GGUF Export: SUCCESS] Model: '{target_model}'\nGGUF: {export_data['gguf_path']}\nModelfile: {export_data['modelfile_path']}"
                return RouterResponse(msg, data=export_data)

        # Stage 97: Causal DAG Epistemic Memory & Counterfactual Timeline
        if lowered in {"/dag-timeline", "dag-timeline", "/causal-dag", "causal-dag"}:
            if hasattr(self.runtime, "causal_dag"):
                return RouterResponse(self.runtime.causal_dag.dag_timeline(), data=self.runtime.causal_dag.status())

        if lowered.startswith("/causal-why ") or lowered.startswith("causal-why "):
            prefix = "/causal-why " if lowered.startswith("/causal-why ") else "causal-why "
            target = text[len(prefix):].strip()
            if hasattr(self.runtime, "causal_dag"):
                chain = self.runtime.causal_dag.causal_why(target)
                return RouterResponse(chain.format_terminal_summary(), data=chain.to_dict())

        if lowered.startswith("/counterfactual-replay ") or lowered.startswith("counterfactual-replay "):
            prefix = "/counterfactual-replay " if lowered.startswith("/counterfactual-replay ") else "counterfactual-replay "
            parts = text[len(prefix):].strip().split(" ", 1)
            target_id = parts[0].strip()
            intervention = parts[1].strip() if len(parts) > 1 else "Action was skipped or failed"
            if hasattr(self.runtime, "causal_dag"):
                cf = self.runtime.causal_dag.counterfactual_replay(target_id, intervention)
                return RouterResponse(cf.format_terminal_summary(), data=cf.to_dict())

        if lowered in {"/prune-dag", "prune-dag"}:
            if hasattr(self.runtime, "causal_dag"):
                pruned = self.runtime.causal_dag.prune_dag(max_nodes=300)
                return RouterResponse(f"[Causal DAG Pruned] Removed {pruned} intermediate nodes while preserving root-cause reachability.")

        # Stage 98: Zero-Leak Host Sandbox & Process Containment Gate
        if lowered in {"/leak-audit", "leak-audit"}:
            if hasattr(self.runtime, "host_sandbox"):
                report = self.runtime.host_sandbox.leak_audit()
                return RouterResponse(report.format_terminal_summary(), data=report.to_dict())

        if lowered in {"/quarantine-status", "quarantine-status"}:
            if hasattr(self.runtime, "host_sandbox"):
                return RouterResponse(self.runtime.host_sandbox.quarantine_status(), data=self.runtime.host_sandbox.status())

        if lowered.startswith("/quarantine-release ") or lowered.startswith("quarantine-release "):
            prefix = "/quarantine-release " if lowered.startswith("/quarantine-release ") else "quarantine-release "
            target_qid = text[len(prefix):].strip()
            if hasattr(self.runtime, "host_sandbox"):
                rel_res = self.runtime.host_sandbox.release_quarantine(target_qid)
                return RouterResponse(f"[Quarantine Released] Cleared {rel_res.get('released_count', 0)} artifact(s).", data=rel_res)

        if lowered.startswith("/sandbox-run ") or lowered.startswith("sandbox-run "):
            prefix = "/sandbox-run " if lowered.startswith("/sandbox-run ") else "sandbox-run "
            cmd_payload = text[len(prefix):].strip()
            if hasattr(self.runtime, "host_sandbox"):
                is_py = cmd_payload.endswith(".py") or "print(" in cmd_payload or "import " in cmd_payload
                res = self.runtime.host_sandbox.run_in_sandbox(cmd_payload, is_python_code=is_py)
                return RouterResponse(res.format_terminal_summary(), data=res.to_dict())

        # Stage 99: Local Hardware Telemetry & Inference Throttle Guard
        if lowered in {"/hardware-status", "hardware-status", "/telemetry", "telemetry"}:
            if hasattr(self.runtime, "hardware_telemetry"):
                return RouterResponse(self.runtime.hardware_telemetry.hardware_status(), data=self.runtime.hardware_telemetry.status())

        if lowered in {"/vram-tune", "vram-tune"}:
            if hasattr(self.runtime, "hardware_telemetry"):
                rec = self.runtime.hardware_telemetry.vram_tune()
                return RouterResponse(rec.format_terminal_summary(), data=rec.to_dict())

        if lowered in {"/bench-inference", "bench-inference"}:
            if hasattr(self.runtime, "hardware_telemetry"):
                bench = self.runtime.hardware_telemetry.bench_inference()
                return RouterResponse(bench.format_terminal_summary(), data=bench.to_dict())

        if lowered.startswith("/throttle-guard") or lowered.startswith("throttle-guard"):
            prefix = "/throttle-guard" if lowered.startswith("/throttle-guard") else "throttle-guard"
            arg = text[len(prefix):].strip()
            if hasattr(self.runtime, "hardware_telemetry"):
                if arg:
                    try:
                        val = float(arg)
                        cfg = self.runtime.hardware_telemetry.set_throttle_thresholds(ram_pct=val)
                        return RouterResponse(f"[Throttle Guard Configured] RAM Threshold set to {cfg['ram_threshold_pct']:.1f}%")
                    except ValueError:
                        pass
                st = self.runtime.hardware_telemetry.status()
                msg = f"[Throttle Guard Active] Policy: {st['throttle_policy']} | RAM Threshold: {st['ram_threshold_pct']}% | Temp Threshold: {st['temp_threshold_c']}C"
                return RouterResponse(msg, data=st)

        # Stage 100: Centennial Sovereign Master Seal & Cryptographic Self-Attestation Fabric
        if lowered in {"/centennial-seal", "centennial-seal", "/seal", "seal"}:
            if hasattr(self.runtime, "master_seal"):
                cert = self.runtime.master_seal.generate_seal(runtime=self.runtime)
                return RouterResponse(cert.format_terminal_summary(), data=cert.to_dict())

        if lowered in {"/verify-seal", "verify-seal", "/check-seal", "check-seal"}:
            if hasattr(self.runtime, "master_seal"):
                res = self.runtime.master_seal.verify_seal()
                msg = f"[Master Seal Verification] Status: {res.get('status')} | Valid: {res.get('valid')} | Creator Intact: {res.get('creator_intact')}"
                return RouterResponse(msg, data=res)

        if lowered in {"/lucy-centennial", "lucy-centennial", "/centennial", "centennial"}:
            if hasattr(self.runtime, "master_seal"):
                banner = self.runtime.master_seal.get_centennial_banner()
                return RouterResponse(banner, data={"banner": banner})

        if lowered in {"/integrity-proof", "integrity-proof", "/merkle-root", "merkle-root"}:
            if hasattr(self.runtime, "master_seal"):
                cert = self.runtime.master_seal.last_certificate or self.runtime.master_seal.generate_seal(runtime=self.runtime)
                msg = (
                    f"[Cryptographic Integrity Proof]\n"
                    f"Merkle Root SHA256: {cert.merkle_root_sha256}\n"
                    f"Master Signature:   {cert.master_seal_signature}\n"
                    f"Total Modules:      {cert.codebase_files_count}\n"
                    f"Total Stages:       {cert.total_stages_sealed} / 100\n"
                    f"Creator & Operator: {cert.creator} ({cert.creator_full_name})"
                )
                return RouterResponse(msg, data=cert.to_dict())

        # Stage 101: Autonomous Kernel & Process Watchdog Fabric
        if lowered in {"/supervisor-status", "supervisor-status", "/watchdog", "watchdog"}:
            if hasattr(self.runtime, "kernel_supervisor"):
                self.runtime.kernel_supervisor.heartbeat_all_active()
                return RouterResponse(self.runtime.kernel_supervisor.supervisor_status(), data=self.runtime.kernel_supervisor.status())

        if lowered in {"/heartbeat-audit", "heartbeat-audit"}:
            if hasattr(self.runtime, "kernel_supervisor"):
                self.runtime.kernel_supervisor.heartbeat_all_active()
                rep = self.runtime.kernel_supervisor.audit_heartbeats(auto_recover=True)
                return RouterResponse(rep.format_terminal_summary(), data=rep.to_dict())

        if lowered.startswith("/restart-worker") or lowered.startswith("restart-worker") or lowered.startswith("/force-recover") or lowered.startswith("force-recover"):
            sub_name = ""
            for pfx in ("/restart-worker", "restart-worker", "/force-recover", "force-recover"):
                if lowered.startswith(pfx):
                    sub_name = text[len(pfx):].strip()
                    break
            if hasattr(self.runtime, "kernel_supervisor"):
                if sub_name:
                    rec_res = self.runtime.kernel_supervisor.recover_subsystem(sub_name, force=True)
                    msg = f"[Kernel Supervisor] Subsystem '{sub_name}' recovery: success={rec_res.get('success')}, status={rec_res.get('status')}"
                    return RouterResponse(msg, data=rec_res)
                else:
                    return RouterResponse("[Kernel Supervisor] Usage: /restart-worker <subsystem_name>")

        # Stage 102: Dynamic Execution Profiler & Flamegraph Tracer
        if lowered in {"/flamegraph", "flamegraph"}:
            if hasattr(self.runtime, "execution_profiler"):
                fg = self.runtime.execution_profiler.get_latest_flamegraph()
                return RouterResponse(fg, data={"flamegraph": fg})

        if lowered in {"/latency-audit", "latency-audit"}:
            if hasattr(self.runtime, "execution_profiler"):
                rep = self.runtime.execution_profiler.get_latency_audit_report()
                return RouterResponse(rep, data=self.runtime.execution_profiler.get_latency_percentiles())

        if lowered in {"/hot-paths", "hot-paths"}:
            if hasattr(self.runtime, "execution_profiler"):
                hp = self.runtime.execution_profiler.get_hot_paths_table()
                return RouterResponse(hp, data=self.runtime.execution_profiler.status())

        if lowered.startswith("/profile-run") or lowered.startswith("profile-run"):
            prefix = "/profile-run" if lowered.startswith("/profile-run") else "profile-run"
            target_cmd = text[len(prefix):].strip()
            if hasattr(self.runtime, "execution_profiler"):
                if not target_cmd:
                    target_cmd = "/supervisor-status"
                with self.runtime.execution_profiler.profile_scope(f"run:{target_cmd}") as meta:
                    _ = self.handle(target_cmd)
                res = meta["result"]
                return RouterResponse(res.format_terminal_summary(), data=res.to_dict())

        # Stage 103: Hybrid Neural-Lexical Vector RAG Engine
        if lowered in {"/rag-status", "rag-status"}:
            if hasattr(self.runtime, "neural_retriever"):
                st = self.runtime.neural_retriever.status()
                msg = f"[Neural RAG Status] Indexed Chunks: {st['total_chunks']} | Terms: {st['unique_terms']} | Dim: {st['vector_dimension']} | Persisted: {st['index_persisted']}"
                return RouterResponse(msg, data=st)

        if lowered in {"/reindex-rag", "reindex-rag"}:
            if hasattr(self.runtime, "neural_retriever"):
                res = self.runtime.neural_retriever.reindex()
                msg = f"[Neural RAG Reindexed] Chunks: {res.get('chunks_indexed')}, Unique Terms: {res.get('unique_terms')}, Duration: {res.get('duration_ms')}ms"
                return RouterResponse(msg, data=res)

        if lowered.startswith("/neural-search ") or lowered.startswith("neural-search "):
            prefix = "/neural-search " if lowered.startswith("/neural-search ") else "neural-search "
            q = text[len(prefix):].strip()
            if hasattr(self.runtime, "neural_retriever"):
                search_res = self.runtime.neural_retriever.search(q, top_k=5)
                return RouterResponse(search_res.format_terminal_summary(), data=search_res.to_dict())

        if lowered.startswith("/retrieve-context ") or lowered.startswith("retrieve-context "):
            prefix = "/retrieve-context " if lowered.startswith("/retrieve-context ") else "retrieve-context "
            q = text[len(prefix):].strip()
            if hasattr(self.runtime, "neural_retriever"):
                ctx = self.runtime.neural_retriever.retrieve_context_window(q, max_tokens=1500)
                return RouterResponse(ctx, data={"query": q, "context": ctx})

        # Stage 104: Autonomous Refactoring & Code Quality Enforcer
        if lowered in {"/scan-tech-debt", "scan-tech-debt", "/clean-code-audit", "clean-code-audit"}:
            if hasattr(self.runtime, "refactor_engine"):
                tbl = self.runtime.refactor_engine.format_tech_debt_table(top_n=8)
                return RouterResponse(tbl, data=self.runtime.refactor_engine.status())

        if lowered.startswith("/suggest-refactor") or lowered.startswith("suggest-refactor"):
            prefix = "/suggest-refactor" if lowered.startswith("/suggest-refactor") else "suggest-refactor"
            target_file = text[len(prefix):].strip()
            if hasattr(self.runtime, "refactor_engine"):
                if not target_file:
                    target_file = "backend/lucy_core/refactor_engine.py"
                props = self.runtime.refactor_engine.suggest_refactorings(target_file)
                if not props:
                    return RouterResponse(f"[Refactor Engine] File '{target_file}' is pristine. Zero code smells detected (Grade A).")
                lines = [f"[Refactor Proposals for {target_file}] ({len(props)} found):"]
                for p in props[:5]:
                    lines.append(f" - [{p.proposal_id}] ({p.rule_id}) on `{p.target_symbol}`: {p.description}")
                lines.append("Use `/apply-refactor <proposal_id>` to validate and apply.")
                return RouterResponse("\n".join(lines), data={"proposals": [p.to_dict() for p in props]})

        if lowered.startswith("/apply-refactor ") or lowered.startswith("apply-refactor "):
            prefix = "/apply-refactor " if lowered.startswith("/apply-refactor ") else "apply-refactor "
            pid = text[len(prefix):].strip()
            if hasattr(self.runtime, "refactor_engine"):
                res = self.runtime.refactor_engine.apply_refactor_patch(pid)
                msg = f"[Refactor Engine] Patch application for '{pid}': success={res.get('success')}, status={res.get('status')}"
                return RouterResponse(msg, data=res)

        # Stage 105: Sovereign P2P Peer Mesh & Local Sync
        if lowered in {"/mesh-status", "mesh-status"}:
            if hasattr(self.runtime, "peer_mesh"):
                return RouterResponse(self.runtime.peer_mesh.mesh_status(), data=self.runtime.peer_mesh.status())

        if lowered in {"/discover-peers", "discover-peers"}:
            if hasattr(self.runtime, "peer_mesh"):
                peers = self.runtime.peer_mesh.discover_peers()
                msg = f"[Peer Mesh] Discovery scan complete: found {len(peers)} peers on local network."
                return RouterResponse(msg, data={"peers": [p.to_dict() for p in peers]})

        if lowered.startswith("/sync-mesh") or lowered.startswith("sync-mesh"):
            prefix = "/sync-mesh" if lowered.startswith("/sync-mesh") else "sync-mesh"
            peer_id = text[len(prefix):].strip()
            if hasattr(self.runtime, "peer_mesh"):
                if peer_id:
                    res = self.runtime.peer_mesh.sync_peer_deltas(peer_id)
                    msg = f"[Peer Mesh] Sync with '{peer_id}': status={res.get('status')}, items={res.get('items_synced')}"
                    return RouterResponse(msg, data=res)
                else:
                    rep = self.runtime.peer_mesh.sync_all()
                    return RouterResponse(rep.format_terminal_summary(), data=rep.to_dict())

        if lowered in {"/export-node-key", "export-node-key"}:
            if hasattr(self.runtime, "peer_mesh"):
                creds = self.runtime.peer_mesh.export_node_credentials()
                msg = (
                    f"[Node Credentials]\n"
                    f"Node ID:    {creds['node_id']}\n"
                    f"Device:     {creds['device_name']}\n"
                    f"Public Key: {creds['public_key']}\n"
                    f"Creator:    {creds['creator']} ({creds['creator_full_name']})"
                )
                return RouterResponse(msg, data=creds)

        # Stage 107: Context Window Semantic Token Compressor
        if lowered.startswith("/compress-prompt ") or lowered.startswith("compress-prompt "):
            prefix = "/compress-prompt " if lowered.startswith("/compress-prompt ") else "compress-prompt "
            prompt_body = text[len(prefix):].strip()
            if hasattr(self.runtime, "token_compressor"):
                out = self.runtime.token_compressor.compress_prompt_command(prompt_body)
                return RouterResponse(out, data={"command": "compress_prompt"})

        if lowered.startswith("/token-budget") or lowered.startswith("token-budget"):
            prefix = "/token-budget" if lowered.startswith("/token-budget") else "token-budget"
            args = text[len(prefix):].strip().split()
            target_ctx = int(args[0]) if len(args) > 0 and args[0].isdigit() else None
            sys_len = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
            if hasattr(self.runtime, "token_compressor"):
                tbl = self.runtime.token_compressor.format_token_budget_table(model_ctx_size=target_ctx, system_prompt_len=sys_len)
                return RouterResponse(tbl, data={"command": "token_budget"})

        if lowered in {"/compression-ratio", "compression-ratio"}:
            if hasattr(self.runtime, "token_compressor"):
                tbl = self.runtime.token_compressor.format_compression_ratio_table()
                return RouterResponse(tbl, data={"command": "compression_ratio"})

        if lowered.startswith("/token-audit") or lowered.startswith("token-audit"):
            prefix = "/token-audit" if lowered.startswith("/token-audit") else "token-audit"
            arg_val = text[len(prefix):].strip()
            limit = int(arg_val) if arg_val.isdigit() else 5
            if hasattr(self.runtime, "token_compressor"):
                tbl = self.runtime.token_compressor.format_token_audit_table(limit=limit)
                return RouterResponse(tbl, data={"command": "token_audit"})

        # Stage 108: Autonomous Security Red-Team & Adversary Simulator
        if lowered.startswith("/simulate-attack") or lowered.startswith("simulate-attack"):
            prefix = "/simulate-attack" if lowered.startswith("/simulate-attack") else "simulate-attack"
            q = text[len(prefix):].strip()
            if hasattr(self.runtime, "red_team"):
                out = self.runtime.red_team.simulate_attack_command(q)
                return RouterResponse(out, data={"command": "simulate_attack"})

        if lowered in {"/redteam-audit", "redteam-audit"}:
            if hasattr(self.runtime, "red_team"):
                rep = self.runtime.red_team.run_full_audit()
                return RouterResponse(rep.format_terminal_summary(), data=rep.to_dict())

        if lowered in {"/vulnerability-scan", "vulnerability-scan"}:
            if hasattr(self.runtime, "red_team"):
                tbl = self.runtime.red_team.format_vulnerability_scan_table()
                return RouterResponse(tbl, data=self.runtime.red_team.evaluate_security_posture())

        if lowered in {"/harden-surface", "harden-surface"}:
            if hasattr(self.runtime, "red_team"):
                tbl = self.runtime.red_team.format_harden_surface_summary()
                return RouterResponse(tbl, data=self.runtime.red_team.harden_surface())

        # Stage 109: Ambient HUD & Desktop Overlay
        if lowered.startswith("/hud-launch") or lowered.startswith("hud-launch"):
            prefix = "/hud-launch" if lowered.startswith("/hud-launch") else "hud-launch"
            m = text[len(prefix):].strip() or "floating"
            if hasattr(self.runtime, "ambient_hud"):
                out = self.runtime.ambient_hud.launch_hud(m)
                return RouterResponse(out, data={"command": "hud_launch", "mode": m})

        if lowered in {"/hud-status", "hud-status"}:
            if hasattr(self.runtime, "ambient_hud"):
                tbl = self.runtime.ambient_hud.format_hud_status_table()
                return RouterResponse(tbl, data=self.runtime.ambient_hud.status())

        if lowered.startswith("/tray-notify ") or lowered.startswith("tray-notify "):
            prefix = "/tray-notify " if lowered.startswith("/tray-notify ") else "tray-notify "
            body = text[len(prefix):].strip()
            parts = body.split(" ", 1)
            t = parts[0] if parts else "Notice"
            msg = parts[1] if len(parts) > 1 else t
            if hasattr(self.runtime, "ambient_hud"):
                n = self.runtime.ambient_hud.tray_notify(title=t, message=msg)
                msg_out = f"[Tray Notification Dispatched] ID: {n.notification_id} | Title: '{n.title}' | Message: '{n.message}'"
                return RouterResponse(msg_out, data=n.to_dict())

        if lowered in {"/toggle-hud", "toggle-hud"}:
            if hasattr(self.runtime, "ambient_hud"):
                out = self.runtime.ambient_hud.toggle_hud()
                return RouterResponse(out, data={"command": "toggle_hud"})

        # Stage 110: Sovereign Consensus Nexus & Era 11 Master Seal
        if lowered in {"/nexus-status", "nexus-status"}:
            if hasattr(self.runtime, "consensus_nexus"):
                tbl = self.runtime.consensus_nexus.format_nexus_status_table()
                return RouterResponse(tbl, data=self.runtime.consensus_nexus.status())

        if lowered.startswith("/agent-consensus ") or lowered.startswith("agent-consensus "):
            prefix = "/agent-consensus " if lowered.startswith("/agent-consensus ") else "agent-consensus "
            prop = text[len(prefix):].strip()
            if hasattr(self.runtime, "consensus_nexus"):
                res = self.runtime.consensus_nexus.propose(prop)
                msg_out = f"[Consensus Committed] Index: {res['index']} | Term: {res['term']} | Proposal: {res['proposal_id']} | Hash: {res['entry_hash'][:16]}..."
                return RouterResponse(msg_out, data=res)

        if lowered in {"/verify-nexus", "verify-nexus"}:
            if hasattr(self.runtime, "consensus_nexus"):
                v = self.runtime.consensus_nexus.verify_era11_integrity()
                msg_out = f"[Nexus Integrity] All Verified: {v['all_verified']} | Modules: {v['verified_modules']}/{v['total_modules']} | Merkle Root: {v['merkle_root'][:16]}..."
                return RouterResponse(msg_out, data=v)

        if lowered in {"/seal-era11", "seal-era11"}:
            if hasattr(self.runtime, "consensus_nexus"):
                cert = self.runtime.consensus_nexus.seal_era11()
                return RouterResponse(cert.format_terminal_summary(), data=cert.to_dict())

        # Stage 111: Proactive Workspace & Process Sensor Daemon
        if lowered in {"/daemon-status", "daemon-status"}:
            if hasattr(self.runtime, "workspace_daemon"):
                tbl = self.runtime.workspace_daemon.format_daemon_status_table()
                return RouterResponse(tbl, data=self.runtime.workspace_daemon.status())

        if lowered in {"/toggle-daemon", "toggle-daemon"}:
            if hasattr(self.runtime, "workspace_daemon"):
                msg_out = f"[Workspace Daemon] {self.runtime.workspace_daemon.toggle()}"
                return RouterResponse(msg_out, data=self.runtime.workspace_daemon.status())

        if lowered in {"/daemon-pulse", "daemon-pulse"}:
            if hasattr(self.runtime, "workspace_daemon"):
                evs = self.runtime.workspace_daemon.scan_now()
                msg_out = f"[Workspace Daemon] Manual pulse executed. Detected {len(evs)} delta change(s)."
                return RouterResponse(msg_out, data={"deltas_detected": len(evs)})

        if lowered.startswith("/stage-context ") or lowered.startswith("stage-context "):
            prefix = "/stage-context " if lowered.startswith("/stage-context ") else "stage-context "
            target_f = text[len(prefix):].strip()
            if hasattr(self.runtime, "workspace_daemon"):
                stg = self.runtime.workspace_daemon.stage_file_context(target_f)
                if stg:
                    msg_out = f"[Context Staged] {stg.source_file} ({stg.line_count} lines, {len(stg.symbols)} symbols) | Test suite: {stg.matching_test_file or 'None'}"
                    return RouterResponse(msg_out, data=stg.to_dict())
                return RouterResponse(f"[Context Staging Failed] File '{target_f}' not found or unreadable.", data={"error": "not_found"})

        # Stage 112: Semantic Inference Cache
        if lowered in {"/cache-status", "cache-status"}:
            if hasattr(self.runtime, "semantic_cache"):
                tbl = self.runtime.semantic_cache.format_cache_status_table()
                return RouterResponse(tbl, data=self.runtime.semantic_cache.status())

        if lowered in {"/flush-cache", "flush-cache"}:
            if hasattr(self.runtime, "semantic_cache"):
                cnt = self.runtime.semantic_cache.flush()
                msg_out = f"[Semantic Cache] Flushed {cnt} cached inference entries."
                return RouterResponse(msg_out, data={"flushed_entries": cnt})

        if lowered in {"/cache-stats", "cache-stats"}:
            if hasattr(self.runtime, "semantic_cache"):
                st = self.runtime.semantic_cache.status()
                msg_out = f"[Cache Stats] Entries: {st['active_entries']}/{st['max_entries']} | Hit Rate: {st['hit_rate']*100:.1f}% | Tokens Saved: {st['total_tokens_saved']:,} | Lookups: {st['total_lookups']}"
                return RouterResponse(msg_out, data=st)

        if lowered.startswith("/cache-query ") or lowered.startswith("cache-query "):
            prefix = "/cache-query " if lowered.startswith("/cache-query ") else "cache-query "
            q = text[len(prefix):].strip()
            if hasattr(self.runtime, "semantic_cache"):
                res = self.runtime.semantic_cache.lookup(q)
                if res:
                    entry, m_type, score = res
                    msg_out = f"[Cache Hit: {m_type} (score={score:.3f})] {entry.response}"
                    return RouterResponse(msg_out, data=entry.to_dict())
                return RouterResponse("[Cache Miss] No cached inference matching query above threshold.", data={"miss": True})

        # Stage 113: Polyglot AST Engine
        if lowered in {"/polyglot-status", "polyglot-status"}:
            if hasattr(self.runtime, "polyglot_ast"):
                tbl = self.runtime.polyglot_ast.format_polyglot_summary_table()
                return RouterResponse(tbl, data=self.runtime.polyglot_ast.status())

        if lowered in {"/polyglot-scan", "polyglot-scan"}:
            if hasattr(self.runtime, "polyglot_ast"):
                sumry = self.runtime.polyglot_ast.scan_workspace()
                msg_out = f"[Polyglot AST Scan] Indexed {sumry.total_files} files, {sumry.total_symbols} symbols across {len(sumry.language_breakdown)} languages."
                return RouterResponse(msg_out, data=sumry.to_dict())

        if lowered.startswith("/find-symbol ") or lowered.startswith("find-symbol "):
            prefix = "/find-symbol " if lowered.startswith("/find-symbol ") else "find-symbol "
            sym_target = text[len(prefix):].strip()
            if hasattr(self.runtime, "polyglot_ast"):
                tbl = self.runtime.polyglot_ast.format_symbol_search_results(sym_target)
                syms = self.runtime.polyglot_ast.find_symbol(sym_target)
                return RouterResponse(tbl, data={"symbols": [s.to_dict() for s in syms]})

        if lowered.startswith("/polyglot-inspect ") or lowered.startswith("polyglot-inspect "):
            prefix = "/polyglot-inspect " if lowered.startswith("/polyglot-inspect ") else "polyglot-inspect "
            f_target = text[len(prefix):].strip()
            if hasattr(self.runtime, "polyglot_ast"):
                rep = self.runtime.polyglot_ast.inspect_file(f_target)
                if rep:
                    msg_out = f"[Polyglot Inspect] {rep.file_path} ({rep.language}): {rep.total_lines} lines, {len(rep.symbols)} symbols, {len(rep.imports)} imports | Valid: {rep.syntax_valid}"
                    return RouterResponse(msg_out, data=rep.to_dict())
                return RouterResponse(f"[Polyglot Inspect] File '{f_target}' not found.", data={"error": "not_found"})

        # Stage 114: Parallel Pipeline Fusion
        if lowered in {"/pipeline-status", "pipeline-status"}:
            if hasattr(self.runtime, "pipeline_fusion"):
                tbl = self.runtime.pipeline_fusion.format_pipeline_status_table()
                return RouterResponse(tbl, data=self.runtime.pipeline_fusion.status())

        if lowered in {"/pipeline-history", "pipeline-history"}:
            if hasattr(self.runtime, "pipeline_fusion"):
                st = self.runtime.pipeline_fusion.status()
                msg_out = f"[Pipeline History] Total Executed: {st['total_executed']} | Success: {st['successful_executed']} | Failed: {st['failed_executed']}"
                return RouterResponse(msg_out, data=st)

        if lowered.startswith("/run-pipeline ") or lowered.startswith("run-pipeline "):
            prefix = "/run-pipeline " if lowered.startswith("/run-pipeline ") else "run-pipeline "
            t_name = text[len(prefix):].strip().lower()
            if hasattr(self.runtime, "pipeline_fusion"):
                if "refactor" in t_name:
                    dag = self.runtime.pipeline_fusion.create_refactor_fusion_pipeline()
                elif "audit" in t_name:
                    dag = self.runtime.pipeline_fusion.create_workspace_audit_pipeline()
                else:
                    return RouterResponse(f"[Pipeline Fusion] Unknown template '{t_name}'. Available: 'refactor', 'audit'", data={"error": "unknown_template"})
                res = self.runtime.pipeline_fusion.execute_pipeline(dag)
                msg_out = f"[Pipeline Fusion] '{res.name}' {'COMPLETED' if res.success else 'FAILED'}: {res.completed_steps}/{res.total_steps} steps in {res.layers_executed} layers ({res.total_latency_ms:.1f}ms)."
                return RouterResponse(msg_out, data=res.to_dict())

        if lowered.startswith("/pipeline-dag ") or lowered.startswith("pipeline-dag "):
            prefix = "/pipeline-dag " if lowered.startswith("/pipeline-dag ") else "pipeline-dag "
            t_name = text[len(prefix):].strip().lower()
            if hasattr(self.runtime, "pipeline_fusion"):
                dag = self.runtime.pipeline_fusion.create_workspace_audit_pipeline() if "audit" in t_name else self.runtime.pipeline_fusion.create_refactor_fusion_pipeline()
                return RouterResponse(self.runtime.pipeline_fusion.format_dag_visualization(dag), data={"layers": dag.validate_and_compute_layers()})

        # Stage 115: Sovereign IPC Event Bus
        if lowered in {"/ipc-status", "ipc-status"}:
            if hasattr(self.runtime, "ipc_bus"):
                tbl = self.runtime.ipc_bus.format_ipc_status_table()
                return RouterResponse(tbl, data=self.runtime.ipc_bus.status())

        if lowered in {"/ipc-channels", "ipc-channels"}:
            if hasattr(self.runtime, "ipc_bus"):
                st = self.runtime.ipc_bus.status()
                msg_out = f"[IPC Channels] Loopback Socket: 127.0.0.1:{st['loopback_port']} | SHM Ring Buffer: Active (64 KB) | Journal: {st['journal_file']}"
                return RouterResponse(msg_out, data=st)

        if lowered.startswith("/publish-event ") or lowered.startswith("publish-event "):
            prefix = "/publish-event " if lowered.startswith("/publish-event ") else "publish-event "
            args = text[len(prefix):].strip().split(" ", 1)
            topic = args[0]
            payload_str = args[1] if len(args) > 1 else "{}"
            if hasattr(self.runtime, "ipc_bus"):
                try:
                    payload = json.loads(payload_str)
                except Exception:
                    payload = {"message": payload_str}
                evt = self.runtime.ipc_bus.publish(topic, payload, source="cli")
                msg_out = f"[IPC Event Published] ID: {evt.event_id} | Topic: {evt.topic} | Seq: {evt.sequence}"
                return RouterResponse(msg_out, data=evt.to_dict())

        if lowered.startswith("/ipc-tail ") or lowered.startswith("ipc-tail "):
            prefix = "/ipc-tail " if lowered.startswith("/ipc-tail ") else "ipc-tail "
            t_pat = text[len(prefix):].strip() or "#"
            if hasattr(self.runtime, "ipc_bus"):
                evts = self.runtime.ipc_bus.tail(t_pat, limit=5)
                if not evts:
                    return RouterResponse(f"[IPC Tail] No events found on topic pattern '{t_pat}'.", data={"count": 0})
                formatted_lines = [f"  [{e.sequence}] {e.topic} ({e.source}): {e.payload}" for e in evts]
                msg_out = f"[IPC Tail] {len(evts)} event(s) on '{t_pat}':\n" + "\n".join(formatted_lines)
                return RouterResponse(msg_out, data={"events": [e.to_dict() for e in evts]})

        # Stage 116: Persistent HNSW Vector DB
        if lowered in {"/vectordb-status", "vectordb-status"}:
            if hasattr(self.runtime, "local_vector_db"):
                tbl = self.runtime.local_vector_db.format_vectordb_status_table()
                return RouterResponse(tbl, data=self.runtime.local_vector_db.status())

        if lowered in {"/vectordb-stats", "vectordb-stats"}:
            if hasattr(self.runtime, "local_vector_db"):
                st = self.runtime.local_vector_db.status()
                msg_out = f"[Vector DB Stats] Total Vectors: {st['total_vectors']:,} | Dim: {st['dim']} | Max Level: {st['max_level']} | Searches: {st['total_searches']} (avg {st['avg_latency_ms']:.2f}ms)"
                return RouterResponse(msg_out, data=st)

        if lowered.startswith("/vectordb-search ") or lowered.startswith("vectordb-search "):
            prefix = "/vectordb-search " if lowered.startswith("/vectordb-search ") else "vectordb-search "
            q = text[len(prefix):].strip()
            if hasattr(self.runtime, "local_vector_db"):
                results = self.runtime.local_vector_db.search_text(q, top_k=3)
                if not results:
                    return RouterResponse(f"[Vector DB Search] No matching vectors found for '{q}'.", data={"results": []})
                res_lines = [f"  [{r.doc_id}] score={r.score:.3f} | {r.metadata.get('text_preview', '')}" for r in results]
                msg_out = f"[Vector DB Search] Top {len(results)} matches for '{q}':\n" + "\n".join(res_lines)
                return RouterResponse(msg_out, data={"results": [r.to_dict() for r in results]})

        if lowered.startswith("/vectordb-insert ") or lowered.startswith("vectordb-insert "):
            prefix = "/vectordb-insert " if lowered.startswith("/vectordb-insert ") else "vectordb-insert "
            args = text[len(prefix):].strip().split(" ", 1)
            doc_id = args[0]
            txt = args[1] if len(args) > 1 else ""
            if hasattr(self.runtime, "local_vector_db"):
                self.runtime.local_vector_db.insert_text(doc_id, txt)
                msg_out = f"[Vector DB Insert] Indexed document '{doc_id}' ({len(txt)} chars, {self.runtime.local_vector_db.dim} dimensions)."
                return RouterResponse(msg_out, data={"doc_id": doc_id, "chars": len(txt)})

        # Stage 117: Autonomous GitOps Engine
        if lowered in {"/gitops-status", "gitops-status"}:
            if hasattr(self.runtime, "git_ops"):
                tbl = self.runtime.git_ops.format_gitops_status_table()
                return RouterResponse(tbl, data=self.runtime.git_ops.status())

        if lowered in {"/gitops-commit-plan", "gitops-commit-plan"}:
            if hasattr(self.runtime, "git_ops"):
                prop = self.runtime.git_ops.synthesize_commit_proposal()
                msg_out = "[GitOps Proposed Commit]\n" + prop.raw_message
                return RouterResponse(msg_out, data=prop.to_dict())

        if lowered in {"/gitops-changelog", "gitops-changelog"}:
            if hasattr(self.runtime, "git_ops"):
                cl = self.runtime.git_ops.generate_changelog(era=12)
                msg_out = f"[GitOps Changelog Generated: {cl.version}]\nSaved to: data/lucy/gitops/CHANGELOG.md\n\n" + cl.markdown[:300] + "..."

                return RouterResponse(msg_out, data=cl.to_dict())

        if lowered in {"/gitops-preflight", "gitops-preflight"}:
            if hasattr(self.runtime, "git_ops"):
                st = self.runtime.git_ops.get_status()
                msg_out = f"[GitOps Pre-Flight Check] Working tree clean: {st.is_clean} | Modified: {len(st.modified_files)} | Untracked: {len(st.untracked_files)} | Safety status: Safe to proceed."
                return RouterResponse(msg_out, data=st.to_dict())

        # Stage 118: Thermal & Compute Governor
        if lowered in {"/governor-status", "governor-status"}:
            if hasattr(self.runtime, "thermal_governor"):
                tbl = self.runtime.thermal_governor.format_governor_status_table()
                return RouterResponse(tbl, data=self.runtime.thermal_governor.status())

        if lowered in {"/governor-cooldown", "governor-cooldown"}:
            if hasattr(self.runtime, "thermal_governor"):
                self.runtime.thermal_governor.trigger_cooldown(20.0)
                msg_out = "[Thermal Governor] Cooldown period engaged (20s). Background threads throttled to 1."
                return RouterResponse(msg_out, data={"mode": "THROTTLED", "cooldown_sec": 20.0})

        if lowered in {"/governor-tripwires", "governor-tripwires"}:
            if hasattr(self.runtime, "thermal_governor"):
                tw = self.runtime.thermal_governor.tripwires
                msg_out = f"[Governor Tripwires] Temp Warn: {tw.temp_warn_c}C, Crit: {tw.temp_critical_c}C | CPU Warn: {tw.cpu_warn_pct}%, Crit: {tw.cpu_critical_pct}% | RAM Warn: {tw.ram_warn_pct}%"
                return RouterResponse(msg_out, data={"temp_critical": tw.temp_critical_c, "cpu_critical": tw.cpu_critical_pct})

        if lowered.startswith("/governor-mode ") or lowered.startswith("governor-mode "):
            prefix = "/governor-mode " if lowered.startswith("/governor-mode ") else "governor-mode "
            mode_req = text[len(prefix):].strip()
            if hasattr(self.runtime, "thermal_governor"):
                ok = self.runtime.thermal_governor.set_mode(mode_req)
                if ok:
                    workers = self.runtime.thermal_governor.allocate_workers()
                    msg_out = f"[Thermal Governor] Operating mode switched to {mode_req.upper()} (Worker capacity: {workers} threads)."
                    return RouterResponse(msg_out, data={"mode": mode_req.upper(), "workers": workers})
                return RouterResponse(f"[Thermal Governor] Unknown mode '{mode_req}'. Valid: 'eco', 'balanced', 'turbo'.", data={"error": "unknown_mode"})

        # Stage 119: Episodic Dream Consolidator
        if lowered in {"/dream-status", "dream-status"}:
            if hasattr(self.runtime, "dream_consolidator"):
                tbl = self.runtime.dream_consolidator.format_dream_status_table()
                return RouterResponse(tbl, data=self.runtime.dream_consolidator.status())

        if lowered in {"/run-dream", "run-dream", "/dream-cycle", "dream-cycle"}:
            if hasattr(self.runtime, "dream_consolidator"):
                rcpt = self.runtime.dream_consolidator.run_dream_cycle()
                msg_out = (
                    f"[Dream Consolidator] Dream cycle {rcpt.dream_id} complete.\n"
                    f"Traces reviewed: {rcpt.traces_reviewed} | Axioms crystallized: {rcpt.axioms_crystallized}\n"
                    f"Contradictions resolved: {rcpt.contradictions_resolved} | Pruned traces: {rcpt.pruned_traces}\n"
                    f"LoRA training triples generated: {rcpt.lora_triples_generated} | Duration: {rcpt.duration_ms:.1f}ms"
                )
                return RouterResponse(msg_out, data=rcpt.to_dict())

        if lowered in {"/dream-axioms", "dream-axioms"}:
            if hasattr(self.runtime, "dream_consolidator"):
                axioms = self.runtime.dream_consolidator.recall_axioms()
                if not axioms:
                    return RouterResponse("[Dream Consolidator] No crystallized axioms found in memory.", data={"axioms": []})
                out = [f"[Crystallized Axioms Repository] ({len(axioms)} axioms stored):"]
                for ax in axioms:
                    out.append(f" - [{ax.domain.upper()}] {ax.subject}: {ax.rule} (confidence: {ax.confidence:.2f})")
                return RouterResponse("\n".join(out), data={"count": len(axioms), "axioms": [ax.to_dict() for ax in axioms]})

        # Stage 120: Sovereign Singularity Nexus & Era 12 Master Seal
        if lowered in {"/era12-seal", "era12-seal"}:
            if hasattr(self.runtime, "era12_seal"):
                tbl = self.runtime.era12_seal.format_seal_certificate_table()
                return RouterResponse(tbl, data=self.runtime.era12_seal.status())

        if lowered in {"/verify-era12", "verify-era12"}:
            if hasattr(self.runtime, "era12_seal"):
                ok, msg, details = self.runtime.era12_seal.verify_era12_integrity()
                return RouterResponse(f"[Era 12 Master Seal Verification] Status: {'PASS' if ok else 'FAIL'}\n{msg}", data=details)

        if lowered in {"/singularity-status", "singularity-status"}:
            if hasattr(self.runtime, "era12_seal"):
                tbl = self.runtime.era12_seal.format_singularity_status_table()
                return RouterResponse(tbl, data=self.runtime.era12_seal.status())

        if lowered.startswith("/cognitive-cycle") or lowered.startswith("cognitive-cycle"):
            prefix = "/cognitive-cycle" if lowered.startswith("/cognitive-cycle") else "cognitive-cycle"
            goal_arg = text[len(prefix):].strip() or "General Self-Regulating Equilibrium"
            if hasattr(self.runtime, "era12_seal"):
                res = self.runtime.era12_seal.run_cognitive_cycle(goal_arg)
                out_msg = f"[Cognitive Singularity Pulse] Cycle: {res.cycle_id} | Goal: {res.goal}\nDuration: {res.duration_ms:.1f}ms | Active subsystems: {res.subsystems_active}/10\nOutcome: {res.summary}"
                return RouterResponse(out_msg, data=res.to_dict())

        # Stage 121: Causal Neural Knowledge Graph & Property Graph Nexus
        if lowered in {"/kg-status", "kg-status"}:
            if hasattr(self.runtime, "knowledge_graph"):
                tbl = self.runtime.knowledge_graph.format_kg_status_table()
                return RouterResponse(tbl, data=self.runtime.knowledge_graph.status())

        if lowered in {"/kg-contradictions", "kg-contradictions"}:
            if hasattr(self.runtime, "knowledge_graph"):
                contras = self.runtime.knowledge_graph.detect_contradictions()
                if not contras:
                    return RouterResponse("[Knowledge Graph] No conflicting assertions detected. Topology is epistemically consistent.", data={"contradictions": []})
                lines = [f"[Knowledge Graph Contradictions] ({len(contras)} conflicts flagged):"]
                for s, t, r in contras:
                    lines.append(f" - {s} vs {t}: {r}")
                return RouterResponse("\n".join(lines), data={"contradictions": contras})

        if lowered.startswith("/kg-query") or lowered.startswith("kg-query"):
            prefix = "/kg-query" if lowered.startswith("/kg-query") else "kg-query"
            kw = text[len(prefix):].strip()
            if hasattr(self.runtime, "knowledge_graph"):
                nodes = self.runtime.knowledge_graph.query(keyword=kw if kw else None)
                lines = [f"[Knowledge Graph Query Results] ({len(nodes)} nodes matched):"]
                for n in nodes[:15]:
                    lines.append(f" - [{n.node_type}] {n.node_id}: {n.label}")
                return RouterResponse("\n".join(lines), data={"count": len(nodes), "nodes": [n.to_dict() for n in nodes]})

        if lowered.startswith("/kg-path ") or lowered.startswith("kg-path "):
            prefix = "/kg-path " if lowered.startswith("/kg-path ") else "kg-path "
            parts = text[len(prefix):].strip().split()
            if len(parts) >= 2 and hasattr(self.runtime, "knowledge_graph"):
                p = self.runtime.knowledge_graph.find_shortest_path(parts[0], parts[1])
                if p:
                    return RouterResponse(f"[Knowledge Graph Path] {" -> ".join(p)}", data={"path": p})
                return RouterResponse(f"[Knowledge Graph] No path found between {parts[0]} and {parts[1]}.", data={"path": None})

        # Stage 122: Multi-Hypothesis Counterfactual Evaluator
        if lowered in {"/counterfactual-status", "counterfactual-status"}:
            if hasattr(self.runtime, "counterfactual_simulator"):
                tbl = self.runtime.counterfactual_simulator.format_counterfactual_status_table()
                return RouterResponse(tbl, data=self.runtime.counterfactual_simulator.status())

        if lowered.startswith("/counterfactual-simulate") or lowered.startswith("counterfactual-simulate"):
            prefix = "/counterfactual-simulate" if lowered.startswith("/counterfactual-simulate") else "counterfactual-simulate"
            goal_arg = text[len(prefix):].strip() or "Standard Autonomous System Refactor"
            if hasattr(self.runtime, "counterfactual_simulator"):
                rep = self.runtime.counterfactual_simulator.simulate_goal_hypotheses(goal_arg)
                msg = (
                    f"[Counterfactual Simulation Complete]\n"
                    f"Simulation ID: {rep.simulation_id} | Goal: {rep.goal}\n"
                    f"Optimal Trajectory: {rep.best_hypothesis_id} (Score: {rep.best_score:.3f})\n"
                    f"Comparative Analysis: {rep.counterfactual_explanation}"
                )
                return RouterResponse(msg, data=rep.to_dict())

        if lowered in {"/counterfactual-tree", "counterfactual-tree"}:
            if hasattr(self.runtime, "counterfactual_simulator"):
                last_rep = self.runtime.counterfactual_simulator._last_simulation
                if not last_rep:
                    return RouterResponse("[Counterfactual Simulator] No simulation recorded in history.", data={"tree": []})
                lines = [f"[Counterfactual Trajectory Tree: {last_rep.simulation_id}] ({last_rep.total_hypotheses} branches):"]
                for h in last_rep.hypotheses:
                    state = "DISQUALIFIED" if h["violates_invariants"] else f"Score {h['composite_score']:.3f}"
                    lines.append(f" - [{h['hypothesis_id']}] {h['description']} -> {state}")
                return RouterResponse("\n".join(lines), data={"hypotheses": last_rep.hypotheses})

        # Stage 123: Hierarchical Goal & Subgoal Decomposer
        if lowered in {"/decomposer-status", "decomposer-status"}:
            if hasattr(self.runtime, "goal_decomposer"):
                tbl = self.runtime.goal_decomposer.format_decomposer_status_table()
                return RouterResponse(tbl, data=self.runtime.goal_decomposer.status())

        if lowered.startswith("/decompose-goal") or lowered.startswith("decompose-goal"):
            prefix = "/decompose-goal" if lowered.startswith("/decompose-goal") else "decompose-goal"
            goal_arg = text[len(prefix):].strip() or "Refactor memory and cognitive subsystem"
            if hasattr(self.runtime, "goal_decomposer"):
                plan = self.runtime.goal_decomposer.decompose_goal(goal_arg)
                tree_out = self.runtime.goal_decomposer.format_goal_tree(plan.plan_id)
                return RouterResponse(tree_out, data=plan.to_dict())

        if lowered.startswith("/goal-tree") or lowered.startswith("goal-tree"):
            prefix = "/goal-tree" if lowered.startswith("/goal-tree") else "goal-tree"
            pid = text[len(prefix):].strip() or None
            if hasattr(self.runtime, "goal_decomposer"):
                tree_out = self.runtime.goal_decomposer.format_goal_tree(pid)
                return RouterResponse(tree_out, data={"plan_id": pid})

        # Stage 124: Autonomous Verification Oracle & Proof Engine
        if lowered in {"/oracle-status", "oracle-status"}:
            if hasattr(self.runtime, "verification_oracle"):
                tbl = self.runtime.verification_oracle.format_oracle_status_table()
                return RouterResponse(tbl, data=self.runtime.verification_oracle.status())

        if lowered.startswith("/oracle-verify") or lowered.startswith("oracle-verify"):
            prefix = "/oracle-verify" if lowered.startswith("/oracle-verify") else "oracle-verify"
            content_arg = text[len(prefix):].strip() or "def test_proof(): pass"
            if hasattr(self.runtime, "verification_oracle"):
                cert = self.runtime.verification_oracle.verify_code_patch(content_arg)
                tbl = self.runtime.verification_oracle.format_certificate_table(cert.certificate_id)
                return RouterResponse(tbl, data=cert.to_dict())

        if lowered.startswith("/oracle-cert") or lowered.startswith("oracle-cert"):
            prefix = "/oracle-cert" if lowered.startswith("/oracle-cert") else "oracle-cert"
            cid = text[len(prefix):].strip() or None
            if hasattr(self.runtime, "verification_oracle"):
                tbl = self.runtime.verification_oracle.format_certificate_table(cid)
                return RouterResponse(tbl, data={"certificate_id": cid})

        # Stage 125: Self-Supervised Latent Concept Miner
        if lowered in {"/concept-status", "concept-status"}:
            if hasattr(self.runtime, "concept_miner"):
                tbl = self.runtime.concept_miner.format_concept_status_table()
                return RouterResponse(tbl, data=self.runtime.concept_miner.status())

        if lowered in {"/concept-taxonomy", "concept-taxonomy"}:
            if hasattr(self.runtime, "concept_miner"):
                tree = self.runtime.concept_miner.format_concept_taxonomy_tree()
                return RouterResponse(tree, data={"taxonomy": "rendered"})

        if lowered in {"/mine-concepts", "mine-concepts"}:
            if hasattr(self.runtime, "concept_miner"):
                mined = self.runtime.concept_miner.mine_concepts()
                exp = 0
                if hasattr(self.runtime, "knowledge_graph"):
                    exp = self.runtime.concept_miner.export_to_knowledge_graph(self.runtime.knowledge_graph)
                out = f"[Latent Concept Miner Sweep Complete]\nMined {len(mined)} new latent concepts. Exported {exp} concepts to Neural Knowledge Graph.\n\n{self.runtime.concept_miner.format_concept_taxonomy_tree()}"
                return RouterResponse(out, data={"mined_count": len(mined), "exported": exp})

        # Stage 126: Dynamic Context Budget Allocator
        if lowered in {"/budget-status", "budget-status"}:
            if hasattr(self.runtime, "context_budgeter"):
                tbl = self.runtime.context_budgeter.format_budget_status_table()
                return RouterResponse(tbl, data=self.runtime.context_budgeter.status())

        if lowered.startswith("/allocate-budget") or lowered.startswith("allocate-budget"):
            if hasattr(self.runtime, "context_budgeter"):
                parts = text.strip().split()
                if len(parts) > 1:
                    arg = parts[1].strip()
                    if arg.isdigit():
                        snap = self.runtime.context_budgeter.allocate_slices(total_budget=int(arg))
                    else:
                        snap = self.runtime.context_budgeter.allocate_slices(hardware_mode=arg)
                    out = f"[Context Budget Reallocated]\nTotal Budget: {snap.total_budget_tokens:,} tokens (mode: {snap.hardware_mode})\n\n{self.runtime.context_budgeter.format_budget_status_table()}"
                    return RouterResponse(out, data=snap.to_dict())
                tbl = self.runtime.context_budgeter.format_budget_status_table()
                return RouterResponse(tbl, data=self.runtime.context_budgeter.status())

        if lowered.startswith("/compact-context") or lowered.startswith("compact-context"):
            if hasattr(self.runtime, "context_budgeter"):
                parts = text.strip().split()
                slice_name = parts[1].strip() if len(parts) > 1 else "RETRIEVAL_RAG_KG"
                freed = self.runtime.context_budgeter.compact_slice(slice_name)
                out = f"[Context Compacted]\nSlice: {slice_name.upper()}\nTokens Freed: {freed:,}\n\n{self.runtime.context_budgeter.format_budget_status_table()}"
                return RouterResponse(out, data={"slice_name": slice_name, "freed_tokens": freed})

        # Stage 127: Protocol Reverse-Engineer & Client Synthesizer
        if lowered in {"/protocol-status", "protocol-status"}:
            if hasattr(self.runtime, "protocol_synthesizer"):
                tbl = self.runtime.protocol_synthesizer.format_protocol_status_table()
                return RouterResponse(tbl, data=self.runtime.protocol_synthesizer.status())

        if lowered.startswith("/infer-protocol") or lowered.startswith("infer-protocol"):
            if hasattr(self.runtime, "protocol_synthesizer"):
                parts = text.strip().split(maxsplit=1)
                sample = parts[1] if len(parts) > 1 else ""
                if sample.startswith("curl"):
                    spec = self.runtime.protocol_synthesizer.infer_from_curl(sample)
                else:
                    spec = self.runtime.protocol_synthesizer.infer_protocol("Inferred Endpoint", raw_payload=sample)
                out = f"[Inferred Protocol: {spec.name}]\nID: {spec.protocol_id} | Method: {spec.method} {spec.path}\nFields ({len(spec.request_fields)}): {[f.name for f in spec.request_fields]}\nAuth: {spec.auth_type}\n\n{self.runtime.protocol_synthesizer.format_protocol_status_table()}"
                return RouterResponse(out, data=spec.to_dict())

        if lowered.startswith("/synthesize-client") or lowered.startswith("synthesize-client"):
            if hasattr(self.runtime, "protocol_synthesizer"):
                parts = text.strip().split(maxsplit=1)
                pid = parts[1].strip() if len(parts) > 1 else ""
                matched = self.runtime.protocol_synthesizer.get_protocol(pid)
                if not matched:
                    for p in self.runtime.protocol_synthesizer.list_protocols():
                        if p.protocol_id.startswith(pid) or pid in p.name.lower():
                            matched = p
                            break
                if matched:
                    code = self.runtime.protocol_synthesizer.synthesize_client_code(matched.protocol_id)
                    out = f"[Synthesized Client: {matched.name}]\nProtocol ID: {matched.protocol_id}\n\n```python\n{code}\n```"
                    return RouterResponse(out, data={"protocol_id": matched.protocol_id, "code": code})
                return RouterResponse(f"[Error] Protocol matching '{pid}' not found in registry.", data={"error": "not_found"})

        # Stage 128: Autonomous Meta-Policy Refiner
        if lowered in {"/policy-status", "policy-status"}:
            if hasattr(self.runtime, "meta_policy_refiner"):
                tbl = self.runtime.meta_policy_refiner.format_policy_status_table()
                return RouterResponse(tbl, data=self.runtime.meta_policy_refiner.status())

        if lowered.startswith("/tune-policy") or lowered.startswith("tune-policy"):
            if hasattr(self.runtime, "meta_policy_refiner"):
                parts = text.strip().split()
                if len(parts) >= 3:
                    pname = parts[1].strip()
                    try:
                        val = float(parts[2].strip())
                        success, msg, final_val = self.runtime.meta_policy_refiner.tune_policy(pname, val)
                        prefix = "[Policy Tuned]" if success else "[Policy Tune Rejected]"
                        out = f"{prefix} {msg}\n\n{self.runtime.meta_policy_refiner.format_policy_status_table()}"
                        return RouterResponse(out, data={"policy": pname, "value": final_val, "success": success})
                    except ValueError:
                        return RouterResponse(f"[Error] Invalid numeric policy value: {parts[2]}", data={"error": "invalid_value"})
                tbl = self.runtime.meta_policy_refiner.format_policy_status_table()
                return RouterResponse(tbl, data=self.runtime.meta_policy_refiner.status())

        if lowered in {"/evaluate-policies", "evaluate-policies"}:
            if hasattr(self.runtime, "meta_policy_refiner"):
                res = self.runtime.meta_policy_refiner.evaluate_and_refine_policies()
                out = f"[Meta-Policy Evaluation Sweep Complete]\nSweep ID: {res['sweep_id']} | Adjustments: {res['adjustments_count']}\n\n{self.runtime.meta_policy_refiner.format_policy_status_table()}"
                return RouterResponse(out, data=res)

        # Stage 129: Distributed Multi-Node IPC Mesh Gateway
        if lowered in {"/mesh-gateway-status", "mesh-gateway-status", "/ipc-mesh-status", "ipc-mesh-status"}:
            if hasattr(self.runtime, "mesh_gateway"):
                tbl = self.runtime.mesh_gateway.format_mesh_status_table()
                return RouterResponse(tbl, data=self.runtime.mesh_gateway.status())

        if lowered.startswith("/register-node") or lowered.startswith("register-node"):
            if hasattr(self.runtime, "mesh_gateway"):
                parts = text.strip().split()
                if len(parts) >= 3:
                    nid = parts[1].strip()
                    ep = parts[2].strip()
                    role = parts[3].strip() if len(parts) > 3 else "worker"
                    node = self.runtime.mesh_gateway.register_node(nid, ep, role)
                    out = f"[Registered Mesh Node: {node.node_id}]\nEndpoint: {node.endpoint} | Role: {node.role} | Sig: {node.signature[:12]}...\n\n{self.runtime.mesh_gateway.format_mesh_status_table()}"
                    return RouterResponse(out, data=node.to_dict())
                return RouterResponse("[Error] Usage: /register-node <node_id> <endpoint> [role]", data={"error": "usage"})

        if lowered.startswith("/dispatch-rpc") or lowered.startswith("dispatch-rpc"):
            if hasattr(self.runtime, "mesh_gateway"):
                parts = text.strip().split(maxsplit=3)
                if len(parts) >= 3:
                    tnode = parts[1].strip()
                    proc = parts[2].strip()
                    params = {}
                    if len(parts) > 3:
                        import json
                        try:
                            params = json.loads(parts[3])
                        except Exception:
                            params = {"arg": parts[3]}
                    res = self.runtime.mesh_gateway.dispatch_rpc(tnode, proc, params)
                    out = f"[RPC Dispatched: {proc} -> {tnode}]\nStatus: {res.get('status')} | Latency: {res.get('latency_ms', 0):.2f}ms\nResult: {res.get('result')}\n\n{self.runtime.mesh_gateway.format_mesh_status_table()}"
                    return RouterResponse(out, data=res)
                return RouterResponse("[Error] Usage: /dispatch-rpc <target_node> <procedure> [json_params]", data={"error": "usage"})

        # Stage 130: Sovereign Singularity Nexus & Era 13 Master Seal
        if lowered in {"/era13-seal", "era13-seal", "/era13-status", "era13-status"}:
            if hasattr(self.runtime, "era13_seal"):
                tbl = self.runtime.era13_seal.format_seal_certificate_table()
                return RouterResponse(tbl, data=self.runtime.era13_seal.status())

        if lowered in {"/verify-era13", "verify-era13"}:
            if hasattr(self.runtime, "era13_seal"):
                intact, msg, cert = self.runtime.era13_seal.verify_era13_integrity()
                out = f"[Era 13 Verification]\nStatus: {'VERIFIED' if intact else 'TAMPERED'}\nMessage: {msg}\n\n{self.runtime.era13_seal.format_seal_certificate_table()}"
                return RouterResponse(out, data={"verified": intact, "message": msg, "certificate": cert})

        if lowered.startswith("/symbolic-cycle") or lowered.startswith("symbolic-cycle"):
            if hasattr(self.runtime, "era13_seal"):
                parts = text.strip().split(maxsplit=1)
                goal = parts[1] if len(parts) > 1 else "Synthesize sovereign cognitive mesh"
                res = self.runtime.era13_seal.run_symbolic_mesh_cycle(goal=goal)
                steps_txt = "\n".join(f"  - {s}" for s in res.steps_executed)
                out = f"[Symbolic Singularity Pulse: {res.cycle_id}]\nGoal: {res.goal}\nDuration: {res.duration_ms:.2f}ms | Active Subsystems: {res.subsystems_active}\n\nExecution Steps:\n{steps_txt}\n\nSummary: {res.summary}\n\n{self.runtime.era13_seal.format_seal_certificate_table()}"
                return RouterResponse(out, data=res.to_dict())

        # Stage 131: Semantic Mutation Engine & AST Genetic Operator
        if lowered in {"/mutation-status", "mutation-status"}:
            if hasattr(self.runtime, "ast_mutator"):
                tbl = self.runtime.ast_mutator.format_mutation_status_table()
                return RouterResponse(tbl, data=self.runtime.ast_mutator.status())

        if lowered.startswith("/mutate-code") or lowered.startswith("mutate-code"):
            if hasattr(self.runtime, "ast_mutator"):
                parts = text.strip().split(maxsplit=2)
                code_snippet = parts[1] if len(parts) > 1 else "def test(): return 1 + 2"
                op = parts[2].strip() if len(parts) > 2 else "AOR"
                mutant = self.runtime.ast_mutator.mutate_code(code_snippet, operator_name=op)
                out = f"[Mutant Generated: {mutant.mutant_id}]\nOperator: {mutant.operator_applied} | Valid: {mutant.is_valid_syntax} | Fitness: {mutant.fitness_score:.2f}\n\nMutated Code:\n```python\n{mutant.mutated_code}\n```\n\n{self.runtime.ast_mutator.format_mutation_status_table()}"
                return RouterResponse(out, data=mutant.to_dict())

        if lowered.startswith("/evolve-code") or lowered.startswith("evolve-code"):
            if hasattr(self.runtime, "ast_mutator"):
                parts = text.strip().split(maxsplit=1)
                code_snippet = parts[1] if len(parts) > 1 else "def compute(x): return x + 10"
                survivors = self.runtime.ast_mutator.evolve_code(code_snippet, generations=2)
                out = f"[Genetic Evolution Complete]\nTotal Mutant Population: {len(survivors)}\nBest Mutant: {survivors[-1].mutant_id if survivors else 'none'}\n\n{self.runtime.ast_mutator.format_mutation_status_table()}"
                return RouterResponse(out, data={"survivors_count": len(survivors)})

        # Stage 132: Autonomous Test Oracle Synthesizer
        if lowered in {"/test-oracle-status", "test-oracle-status"}:
            if hasattr(self.runtime, "test_oracle"):
                tbl = self.runtime.test_oracle.format_oracle_status_table()
                return RouterResponse(tbl, data=self.runtime.test_oracle.status())

        if lowered.startswith("/synthesize-tests") or lowered.startswith("synthesize-tests"):
            if hasattr(self.runtime, "test_oracle"):
                parts = text.strip().split(maxsplit=1)
                code_snippet = parts[1] if len(parts) > 1 else "def compute(x): return x * 2"
                rec = self.runtime.test_oracle.synthesize_test_suite(code_snippet)
                out = f"[Test Suite Synthesized: {rec.suite_id}]\nTarget: {rec.target_name} | Assertions: {rec.assertions_count} | Compilable: {rec.is_compilable}\n\nSynthesized Test Suite Code:\n```python\n{rec.test_code}\n```\n\n{self.runtime.test_oracle.format_oracle_status_table()}"
                return RouterResponse(out, data=rec.to_dict())

        if lowered.startswith("/validate-test-suite") or lowered.startswith("validate-test-suite"):
            if hasattr(self.runtime, "test_oracle"):
                parts = text.strip().split(maxsplit=1)
                sid = parts[1].strip() if len(parts) > 1 else ""
                matched = self.runtime.test_oracle._test_suites.get(sid)
                if not matched:
                    for s in self.runtime.test_oracle._test_suites.values():
                        if s.suite_id.startswith(sid) or sid in s.target_name.lower():
                            matched = s
                            break
                if matched:
                    val = self.runtime.test_oracle.validate_test_suite(matched.suite_id)
                    out = f"[Test Suite Validated: {matched.suite_id}]\nStatus: {val.get('status')} | Compilable: {val.get('is_compilable')}\n\n{self.runtime.test_oracle.format_oracle_status_table()}"
                    return RouterResponse(out, data=val)
                return RouterResponse(f"[Error] Test suite matching '{sid}' not found.", data={"error": "not_found"})

        # Stage 133: Type-Inference & Static Constraint Solver
        if lowered in {"/constraint-status", "constraint-status"}:
            if hasattr(self.runtime, "constraint_solver"):
                tbl = self.runtime.constraint_solver.format_constraint_status_table()
                return RouterResponse(tbl, data=self.runtime.constraint_solver.status())

        if lowered.startswith("/solve-constraints") or lowered.startswith("solve-constraints"):
            if hasattr(self.runtime, "constraint_solver"):
                parts = text.strip().split(maxsplit=1)
                code_snippet = parts[1] if len(parts) > 1 else "x = 10"
                code_snippet = code_snippet.replace("; ", "\n").replace(";", "\n")
                res = self.runtime.constraint_solver.solve_constraints(code_snippet)
                out = f"[Constraints Solved: {res.solve_id}]\nSatisfiable: {res.is_satisfiable} | Variables Analyzed: {res.total_variables_analyzed}\nInferred Types: {res.inferred_types}\nConflicts: {res.conflicts_detected}\n\n{self.runtime.constraint_solver.format_constraint_status_table()}"
                return RouterResponse(out, data=res.to_dict())

        if lowered.startswith("/check-branch-sat") or lowered.startswith("check-branch-sat"):
            if hasattr(self.runtime, "constraint_solver"):
                parts = text.strip().split(maxsplit=1)
                cond = parts[1].strip() if len(parts) > 1 else "True"
                res = self.runtime.constraint_solver.check_branch_sat(cond)
                out = f"[Branch Satisfiability]\nCondition: {res['condition']}\nStatus: {res['status']}\nReason: {res['reason']}"
                return RouterResponse(out, data=res)

        # Stage 134: Bytecode Decompiler & Disassembly Inspector
        if lowered in {"/bytecode-status", "bytecode-status"}:
            if hasattr(self.runtime, "bytecode_inspector"):
                tbl = self.runtime.bytecode_inspector.format_bytecode_status_table()
                return RouterResponse(tbl, data=self.runtime.bytecode_inspector.status())

        if lowered.startswith("/disassemble-code") or lowered.startswith("disassemble-code"):
            if hasattr(self.runtime, "bytecode_inspector"):
                parts = text.strip().split(maxsplit=1)
                snippet = parts[1] if len(parts) > 1 else "x = 1 + 2"
                snippet = snippet.replace("; ", "\n").replace(";", "\n")
                rep = self.runtime.bytecode_inspector.disassemble_code(snippet)
                dump = self.runtime.bytecode_inspector.format_bytecode_dump(rep.report_id)
                out = f"[Bytecode Disassembled: {rep.report_id}]\nInstructions: {rep.total_instructions} | Stack Depth: {rep.stack_size} | Eval Anomaly: {rep.has_dynamic_eval}\n\n```\n{dump}\n```\n\n{self.runtime.bytecode_inspector.format_bytecode_status_table()}"
                return RouterResponse(out, data=rep.to_dict())

        if lowered.startswith("/inspect-opcodes") or lowered.startswith("inspect-opcodes"):
            if hasattr(self.runtime, "bytecode_inspector"):
                parts = text.strip().split(maxsplit=1)
                snippet = parts[1] if len(parts) > 1 else "x = 1 + 2"
                snippet = snippet.replace("; ", "\n").replace(";", "\n")
                rep = self.runtime.bytecode_inspector.disassemble_code(snippet)
                lines = [f"[Opcode Frequency Breakdown: {rep.report_id}]", f"Total Instructions: {rep.total_instructions}"]
                for op, count in sorted(rep.opcode_distribution.items(), key=lambda x: -x[1]):
                    lines.append(f"  {op:<24} : {count} occurrences")
                out = "\n".join(lines) + f"\n\n{self.runtime.bytecode_inspector.format_bytecode_status_table()}"
                return RouterResponse(out, data=rep.opcode_distribution)

        # Stage 135: Polyglot FFI Bridge & Native C ABI Linker
        if lowered in {"/ffi-status", "ffi-status"}:
            if hasattr(self.runtime, "ffi_linker"):
                tbl = self.runtime.ffi_linker.format_ffi_status_table()
                return RouterResponse(tbl, data=self.runtime.ffi_linker.status())

        if lowered.startswith("/link-native-symbol") or lowered.startswith("link-native-symbol"):
            if hasattr(self.runtime, "ffi_linker"):
                parts = text.strip().split()
                if len(parts) >= 4:
                    lib_name = parts[1].strip()
                    sym_name = parts[2].strip()
                    res_type = parts[3].strip()
                    arg_types = parts[4:] if len(parts) > 4 else []
                    b = self.runtime.ffi_linker.link_native_symbol(sym_name, library_name=lib_name, restype_name=res_type, argtypes_names=arg_types)
                    out = f"[Linked Native Symbol: {b.symbol_name}]\nLibrary: {b.library_name} | Return: {b.restype} | Live: {b.is_live_loaded}\n\n{self.runtime.ffi_linker.format_ffi_status_table()}"
                    return RouterResponse(out, data=b.to_dict())
                return RouterResponse("[Error] Usage: /link-native-symbol <lib_name> <symbol_name> <restype> [argtypes...]", data={"error": "usage"})

        if lowered.startswith("/invoke-native") or lowered.startswith("invoke-native"):
            if hasattr(self.runtime, "ffi_linker"):
                parts = text.strip().split()
                if len(parts) >= 2:
                    sym_name = parts[1].strip()
                    raw_args = parts[2:]
                    converted_args = []
                    for a in raw_args:
                        try:
                            converted_args.append(int(a))
                        except ValueError:
                            converted_args.append(a)
                    try:
                        res = self.runtime.ffi_linker.invoke_native_symbol(sym_name, *converted_args)
                        out = f"[Native Invocation Complete: {sym_name}]\nArguments: {converted_args}\nResult: {res}\n\n{self.runtime.ffi_linker.format_ffi_status_table()}"
                        return RouterResponse(out, data={"symbol": sym_name, "result": res})
                    except Exception as e:
                        return RouterResponse(f"[Native Invocation Error] {str(e)}", data={"error": str(e)})
                return RouterResponse("[Error] Usage: /invoke-native <symbol_name> [args...]", data={"error": "usage"})

        # Stage 136: Self-Hosted Package Index & Sovereign Wheel Fabric
        if lowered in {"/wheel-status", "wheel-status"}:
            if hasattr(self.runtime, "wheel_fabric"):
                tbl = self.runtime.wheel_fabric.format_wheel_status_table()
                return RouterResponse(tbl, data=self.runtime.wheel_fabric.status())

        if lowered.startswith("/build-wheel") or lowered.startswith("build-wheel"):
            if hasattr(self.runtime, "wheel_fabric"):
                parts = text.strip().split()
                if len(parts) >= 2:
                    pname = parts[1].strip()
                    ver = parts[2].strip() if len(parts) > 2 else "1.0.0"
                    rec = self.runtime.wheel_fabric.build_wheel(pname, version=ver)
                    out = f"[Wheel Package Built: {rec.wheel_filename}]\nSize: {rec.file_size_bytes:,} bytes | Files: {rec.total_files_contained}\nSHA-256: {rec.sha256_digest}\nSignature: {rec.hmac_signature[:16]}...\n\n{self.runtime.wheel_fabric.format_wheel_status_table()}"
                    return RouterResponse(out, data=rec.to_dict())
                return RouterResponse("[Error] Usage: /build-wheel <package_name> [version]", data={"error": "usage"})

        if lowered.startswith("/verify-wheel") or lowered.startswith("verify-wheel"):
            if hasattr(self.runtime, "wheel_fabric"):
                parts = text.strip().split(maxsplit=1)
                whl = parts[1].strip() if len(parts) > 1 else ""
                res = self.runtime.wheel_fabric.verify_wheel(whl)
                out = f"[Wheel Verification Complete]\nFilename: {res.get('wheel_filename')}\nStatus: {res.get('status')}\nValid: {res.get('is_valid')}\nTampered Files: {res.get('tampered_files')}\n\n{self.runtime.wheel_fabric.format_wheel_status_table()}"
                return RouterResponse(out, data=res)

        # Stage 137: Real-Time Performance Regression Sentinel
        if lowered in {"/perf-status", "perf-status", "/perf-sentinel-status", "perf-sentinel-status"}:
            if hasattr(self.runtime, "perf_sentinel"):
                tbl = self.runtime.perf_sentinel.format_perf_status_table()
                return RouterResponse(tbl, data=self.runtime.perf_sentinel.status())

        if lowered in {"/perf-baselines", "perf-baselines"}:
            if hasattr(self.runtime, "perf_sentinel"):
                tbl = self.runtime.perf_sentinel.format_baselines_table()
                return RouterResponse(tbl, data={"baselines": list(self.runtime.perf_sentinel.baselines.keys())})

        if lowered.startswith("/perf-benchmark") or lowered.startswith("perf-benchmark"):
            if hasattr(self.runtime, "perf_sentinel"):
                parts = text.strip().split()
                target = parts[1] if len(parts) > 1 else "ast_mutation"
                iters = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 50
                metric, alerts = self.runtime.perf_sentinel.benchmark_subsystem(target, iterations=iters)
                alert_text = f"\n[Regression Alert: {len(alerts)} detected]" if alerts else "\n[No Regressions Detected]"
                out = f"[Performance Benchmark Completed: {metric.name}]\nLatency: {metric.avg_latency_ms:.3f}ms | Throughput: {metric.ops_per_sec:.1f} ops/s{alert_text}\n\n{self.runtime.perf_sentinel.format_perf_status_table()}"
                return RouterResponse(out, data={"metric": metric.to_dict(), "alerts": [a.to_dict() for a in alerts]})

        if lowered.startswith("/perf-check") or lowered.startswith("perf-check"):
            if hasattr(self.runtime, "perf_sentinel"):
                parts = text.strip().split()
                target = parts[1] if len(parts) > 1 else "ast_mutation"
                metric, alerts = self.runtime.perf_sentinel.benchmark_subsystem(target, iterations=25)
                stat_str = "ALERT" if alerts else "OPTIMAL"
                out = f"[Performance Check: {target}]\nStatus: {stat_str}\nLatency: {metric.avg_latency_ms:.3f}ms\n\n{self.runtime.perf_sentinel.format_perf_status_table()}"
                return RouterResponse(out, data={"metric": metric.to_dict(), "alerts": [a.to_dict() for a in alerts]})

        # Stage 138: Dead-Code Eliminator & AST Pruner
        if lowered in {"/prune-status", "prune-status", "/deadcode-status", "deadcode-status"}:
            if hasattr(self.runtime, "dead_code_eliminator"):
                tbl = self.runtime.dead_code_eliminator.format_status_table()
                return RouterResponse(tbl, data=self.runtime.dead_code_eliminator.status())

        if lowered.startswith("/prune-analyze") or lowered.startswith("prune-analyze"):
            if hasattr(self.runtime, "dead_code_eliminator"):
                parts = text.strip().split(maxsplit=1)
                target = parts[1].strip() if len(parts) > 1 else ""
                if Path(target).exists():
                    items, summary = self.runtime.dead_code_eliminator.analyze_file(target)
                else:
                    items, summary = self.runtime.dead_code_eliminator.analyze_code(target)
                out = f"[Dead-Code Analysis: {target}]\nItems Detected: {len(items)}\n"
                for it in items[:5]:
                    out += f" - [{it.item_type}] {it.name} (line {it.line_number}): {it.reason}\n"
                out = out.strip() + f"\n\n{self.runtime.dead_code_eliminator.format_status_table()}"
                return RouterResponse(out, data={"items": [i.to_dict() for i in items], "summary": summary})

        if lowered.startswith("/prune-file") or lowered.startswith("prune-file"):
            if hasattr(self.runtime, "dead_code_eliminator"):
                parts = text.strip().split(maxsplit=1)
                fpath = parts[1].strip() if len(parts) > 1 else ""
                report = self.runtime.dead_code_eliminator.prune_file(fpath, in_place=False)
                tbl = self.runtime.dead_code_eliminator.format_report_table(report)
                return RouterResponse(tbl, data=report.to_dict())

        if lowered.startswith("/reachability-graph") or lowered.startswith("reachability-graph"):
            if hasattr(self.runtime, "dead_code_eliminator"):
                parts = text.strip().split(maxsplit=1)
                target = parts[1].strip() if len(parts) > 1 else ""
                content = Path(target).read_text(encoding="utf-8") if Path(target).exists() else target
                graph = self.runtime.dead_code_eliminator.build_reachability_graph(content)
                out = f"[Reachability Graph: {target}]\nFunctions: {graph.get('functions')}\nCalls: {graph.get('calls_adjacency')}"
                return RouterResponse(out, data=graph)

        # Stage 139: Deterministic Replay & Flight-Data Recorder
        if lowered in {"/flight-status", "flight-status", "/recorder-status", "recorder-status"}:
            if hasattr(self.runtime, "flight_recorder"):
                tbl = self.runtime.flight_recorder.format_flight_status_table()
                return RouterResponse(tbl, data=self.runtime.flight_recorder.status())

        if lowered.startswith("/flight-snapshot") or lowered.startswith("flight-snapshot"):
            if hasattr(self.runtime, "flight_recorder"):
                parts = text.strip().split(maxsplit=1)
                lbl = parts[1].strip() if len(parts) > 1 else "manual_checkpoint"
                snap = self.runtime.flight_recorder.take_snapshot(label=lbl)
                out = f"[Flight Snapshot Recorded: {lbl}]\nEvent ID: {snap.event_id}\nState Hash: {snap.state_hash[:16]}...\n\n{self.runtime.flight_recorder.format_flight_status_table()}"
                return RouterResponse(out, data=snap.to_dict())

        if lowered.startswith("/flight-replay") or lowered.startswith("flight-replay"):
            if hasattr(self.runtime, "flight_recorder"):
                parts = text.strip().split(maxsplit=1)
                fid = parts[1].strip() if len(parts) > 1 else ""
                diff = self.runtime.flight_recorder.replay_flight(fid)
                tbl = self.runtime.flight_recorder.format_replay_diff_table(diff)
                return RouterResponse(tbl, data=diff.to_dict())

        if lowered in {"/blackbox-export", "blackbox-export"}:
            if hasattr(self.runtime, "flight_recorder"):
                rec = self.runtime.flight_recorder.flush_flight_recording()
                out = f"[Black-Box Flight Log Exported]\nFlight ID: {rec.flight_id}\nEvents: {rec.events_count}\nMerkle Root: {rec.merkle_root[:16]}...\nSignature: {rec.hmac_signature[:16]}...\n\n{self.runtime.flight_recorder.format_flight_status_table()}"
                return RouterResponse(out, data=rec.to_dict())

        # Stage 140: Sovereign Singularity Nexus & Era 14 Master Seal
        if lowered in {"/era14-status", "era14-status"}:
            if hasattr(self.runtime, "era14_nexus"):
                tbl = self.runtime.era14_nexus.format_era14_status_table()
                return RouterResponse(tbl, data=self.runtime.era14_nexus.status())

        if lowered in {"/verify-era14", "verify-era14"}:
            if hasattr(self.runtime, "era14_nexus"):
                cert = self.runtime.era14_nexus.generate_era14_master_seal(force=True)
                out = f"[Era 14 Master Seal Verified]\nSeal ID: {cert.seal_id}\nMerkle Root: {cert.merkle_root}\nStatus: {cert.integrity_status}\n\n{self.runtime.era14_nexus.format_era14_status_table()}"
                return RouterResponse(out, data=cert.to_dict())

        if lowered.startswith("/evolution-cycle") or lowered.startswith("evolution-cycle"):
            if hasattr(self.runtime, "era14_nexus"):
                parts = text.strip().split(maxsplit=1)
                target = parts[1].strip() if len(parts) > 1 else "runtime_evolution"
                res = self.runtime.era14_nexus.run_evolution_cycle(target)
                tbl = self.runtime.era14_nexus.format_cycle_result_table(res)
                return RouterResponse(tbl, data=res.to_dict())

        # Stage 141: Intermediate Representation (IR) Compiler Core
        if lowered in {"/ir-status", "ir-status", "/compiler-status", "compiler-status"}:
            if hasattr(self.runtime, "ir_compiler"):
                tbl = self.runtime.ir_compiler.format_ir_status_table()
                return RouterResponse(tbl, data=self.runtime.ir_compiler.status())

        if lowered.startswith("/ir-compile") or lowered.startswith("ir-compile"):
            if hasattr(self.runtime, "ir_compiler"):
                parts = text.strip().split(maxsplit=1)
                target = parts[1].strip() if len(parts) > 1 else ""
                content = Path(target).read_text(encoding="utf-8") if Path(target).exists() else target
                mod = self.runtime.ir_compiler.compile_source(content, module_name="cli_mod")
                valid, errors = self.runtime.ir_compiler.verify_module(mod)
                out = f"[IR Compilation Complete]\nModule: {mod.module_name}\nFunctions: {len(mod.functions)}\nVerified: {valid}\n\n{mod.to_text()}"
                return RouterResponse(out, data={"module": mod.to_dict(), "is_valid": valid, "errors": errors})

        if lowered.startswith("/ir-verify") or lowered.startswith("ir-verify"):
            if hasattr(self.runtime, "ir_compiler"):
                parts = text.strip().split(maxsplit=1)
                mname = parts[1].strip() if len(parts) > 1 else "cli_mod"
                mod = self.runtime.ir_compiler.compiled_modules.get(mname)
                if not mod:
                    return RouterResponse(f"[Error] Module '{mname}' not found.", data={"error": "not_found"})
                valid, errors = self.runtime.ir_compiler.verify_module(mod)
                err_str = f"\nErrors: {errors}" if errors else ""
                out = f"[IR Module Verification: {mname}]\nStatus: {'VERIFIED_VALID' if valid else 'INVALID'}{err_str}"
                return RouterResponse(out, data={"is_valid": valid, "errors": errors})

        # Stage 142: Static Single Assignment (SSA) Optimizer
        if lowered in {"/ssa-status", "ssa-status", "/optimizer-status", "optimizer-status"}:
            if hasattr(self.runtime, "ssa_optimizer"):
                tbl = self.runtime.ssa_optimizer.format_ssa_status_table()
                return RouterResponse(tbl, data=self.runtime.ssa_optimizer.status())

        if lowered.startswith("/ssa-optimize") or lowered.startswith("ssa-optimize"):
            if hasattr(self.runtime, "ssa_optimizer"):
                parts = text.strip().split(maxsplit=1)
                target = parts[1].strip() if len(parts) > 1 else ""
                content = Path(target).read_text(encoding="utf-8") if Path(target).exists() else target
                opt_mod, rep = self.runtime.ssa_optimizer.optimize_source(content, module_name="cli_opt")
                rep_table = self.runtime.ssa_optimizer.format_optimization_report(rep)
                out = f"{rep_table}\n\n[Optimized IR Disassembly]\n{opt_mod.to_text()}"
                return RouterResponse(out, data={"optimized_module": opt_mod.to_dict(), "report": rep.to_dict()})

        # Stage 143: Loop Invariant & Polyhedral Transformation Engine
        if lowered in {"/loop-status", "loop-status", "/polyhedral-status", "polyhedral-status"}:
            if hasattr(self.runtime, "loop_optimizer"):
                tbl = self.runtime.loop_optimizer.format_loop_status_table()
                return RouterResponse(tbl, data=self.runtime.loop_optimizer.status())

        if lowered.startswith("/loop-optimize") or lowered.startswith("loop-optimize"):
            if hasattr(self.runtime, "loop_optimizer"):
                parts = text.strip().split(maxsplit=1)
                target = parts[1].strip() if len(parts) > 1 else ""
                content = Path(target).read_text(encoding="utf-8") if Path(target).exists() else target
                opt_mod, rep = self.runtime.loop_optimizer.optimize_source(content, module_name="cli_loop_opt")
                rep_table = self.runtime.loop_optimizer.format_transform_report(rep)
                out = f"{rep_table}\n\n[Loop-Optimized IR Disassembly]\n{opt_mod.to_text()}"
                return RouterResponse(out, data={"optimized_module": opt_mod.to_dict(), "report": rep.to_dict()})

        # Stage 144: Register Allocation & Spill Cost Graph Colorer
        if lowered in {"/reg-status", "reg-status", "/allocator-status", "allocator-status"}:
            if hasattr(self.runtime, "register_allocator"):
                tbl = self.runtime.register_allocator.format_reg_status_table()
                return RouterResponse(tbl, data=self.runtime.register_allocator.status())

        if lowered.startswith("/reg-allocate") or lowered.startswith("reg-allocate"):
            if hasattr(self.runtime, "register_allocator"):
                parts = text.strip().split()
                target = parts[1] if len(parts) > 1 else ""
                k_val = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 8
                content = Path(target).read_text(encoding="utf-8") if Path(target).exists() else target
                results = self.runtime.register_allocator.allocate_source(content, k=k_val)
                out = f"[Register Allocation Complete (K={k_val})]\n"
                for fname, res in results.items():
                    out += f"\n{self.runtime.register_allocator.format_allocation_table(res)}\n"
                return RouterResponse(out.strip(), data={k_fn: r.to_dict() for k_fn, r in results.items()})

        # Stage 145: Target-Agnostic Assembler & Machine Code Synthesizer
        if lowered in {"/asm-status", "asm-status", "/codegen-status", "codegen-status"}:
            if hasattr(self.runtime, "code_synthesizer"):
                tbl = self.runtime.code_synthesizer.format_asm_status_table()
                return RouterResponse(tbl, data=self.runtime.code_synthesizer.status())

        if lowered.startswith("/asm-emit") or lowered.startswith("asm-emit"):
            if hasattr(self.runtime, "code_synthesizer"):
                parts = text.strip().split()
                target = parts[1] if len(parts) > 1 else ""
                arch = parts[2] if len(parts) > 2 else "x86_64"
                content = Path(target).read_text(encoding="utf-8") if Path(target).exists() else target
                results = self.runtime.code_synthesizer.synthesize_source(content, target_arch=arch)
                out = f"[Machine Code Synthesis Complete ({arch})]\n"
                for fname, art in results.items():
                    out += f"\n{self.runtime.code_synthesizer.format_assembly_artifact(art)}\n"
                return RouterResponse(out.strip(), data={fname: art.to_dict() for fname, art in results.items()})

        # Stage 146: Just-In-Time (JIT) Hotpath Tracer & Tiered Execution Engine
        if lowered in {"/jit-status", "jit-status", "/hotpath-status", "hotpath-status"}:
            if hasattr(self.runtime, "jit_tracer"):
                tbl = self.runtime.jit_tracer.format_jit_status_table()
                return RouterResponse(tbl, data=self.runtime.jit_tracer.status())

        if lowered.startswith("/jit-trace") or lowered.startswith("jit-trace"):
            if hasattr(self.runtime, "jit_tracer"):
                parts = text.strip().split(maxsplit=1)
                fname = parts[1].strip() if len(parts) > 1 else ""
                trace = self.runtime.jit_tracer.jit_cache.get(fname)
                if trace:
                    tbl = self.runtime.jit_tracer.format_trace_table(trace)
                    return RouterResponse(tbl, data=trace.to_dict())
                return RouterResponse(f"[Info] No JIT trace compiled yet for '@{fname}'. Invoke function to promote.", data={"error": "not_traced"})

        if lowered in {"/jit-flush", "jit-flush"}:
            if hasattr(self.runtime, "jit_tracer"):
                cnt = self.runtime.jit_tracer.flush_jit_cache()
                out = f"[JIT Cache Flushed: {cnt} traces evicted]\n\n{self.runtime.jit_tracer.format_jit_status_table()}"
                return RouterResponse(out, data={"flushed": cnt})

        # Stage 147: Ahead-Of-Time (AOT) Sovereign Native Linker & PE/ELF Formatter
        if lowered in {"/aot-status", "aot-status", "/linker-status", "linker-status"}:
            if hasattr(self.runtime, "native_linker"):
                tbl = self.runtime.native_linker.format_ascii_status()
                return RouterResponse(tbl, data={"status": "active"})

        if lowered.startswith("/aot-link") or lowered.startswith("aot-link"):
            if hasattr(self.runtime, "native_linker"):
                parts = text.strip().split()
                fmt = parts[1].lower() if len(parts) > 1 else "pe"
                code = b"\xb8\x2a\x00\x00\x00\xc3"
                art = self.runtime.native_linker.link_pe(code) if fmt == "pe" else (
                    self.runtime.native_linker.link_elf(code) if fmt == "elf" else self.runtime.native_linker.link_sovereign_bin(code)
                )
                tbl = self.runtime.native_linker.format_ascii_artifact_table(art)
                return RouterResponse(tbl, data=art.to_dict())

        # Stage 148: Zero-Copy Memory Arena & Memory Pool Allocator
        if lowered in {"/arena-status", "arena-status", "/mem-stats", "mem-stats", "/pool-status", "pool-status"}:
            if hasattr(self.runtime, "memory_manager"):
                tbl = self.runtime.memory_manager.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.memory_manager.run_memory_audit())

        if lowered in {"/mem-audit", "mem-audit"}:
            if hasattr(self.runtime, "memory_manager"):
                audit = self.runtime.memory_manager.run_memory_audit()
                status_str = "PASSED (HEALTHY)" if audit["healthy"] else f"CORRUPTED: {audit['corruptions']}"
                out = f"[Memory Audit: {status_str}]\nTotal Allocated: {audit['total_allocated_bytes']} bytes\nTotal Capacity: {audit['total_capacity_bytes']} bytes"
                return RouterResponse(out, data=audit)

        # Stage 149: Link-Time Optimization (LTO) & Cross-Module Inliner
        if lowered in {"/lto-status", "lto-status"}:
            if hasattr(self.runtime, "lto_pipeline"):
                tbl = self.runtime.lto_pipeline.format_ascii_status()
                return RouterResponse(tbl, data={"runs": self.runtime.lto_pipeline.total_lto_runs})

        if lowered.startswith("/lto-opt") or lowered.startswith("lto-opt"):
            if hasattr(self.runtime, "lto_pipeline"):
                from backend.lucy_core.ir_compiler_core import IRModule, IRFunction, BasicBlock, IRInstruction
                b1 = BasicBlock(label="entry", instructions=[
                    IRInstruction(op="CONST", dest="%v0", args=["10"]),
                    IRInstruction(op="CALL", dest="%v1", args=["leaf_worker", "%v0"]),
                    IRInstruction(op="RET", args=["%v1"])
                ])
                f1 = IRFunction(name="main", args=[], blocks={"entry": b1}, entry_block="entry")
                m1 = IRModule(module_name="m1", functions={"main": f1}, globals={})

                b2 = BasicBlock(label="entry", instructions=[
                    IRInstruction(op="ADD", dest="%r", args=["%x", "5"]),
                    IRInstruction(op="RET", args=["%r"])
                ])
                f2 = IRFunction(name="leaf_worker", args=["%x"], blocks={"entry": b2}, entry_block="entry")
                m2 = IRModule(module_name="m2", functions={"leaf_worker": f2}, globals={})

                res = self.runtime.lto_pipeline.run_lto([m1, m2], root_symbols={"main"})
                tbl = self.runtime.lto_pipeline.format_ascii_result_table(res)
                return RouterResponse(tbl, data=res.to_dict())

        # Stage 150: Sovereign Singularity Nexus & Era 15 Master Seal
        if lowered in {"/verify-era15", "verify-era15", "/era15-status", "era15-status", "/master-seal-15"}:
            if hasattr(self.runtime, "era15_nexus"):
                tbl = self.runtime.era15_nexus.format_ascii_status()
                cert = self.runtime.era15_nexus.verify_era15_integrity()
                return RouterResponse(tbl, data=cert.to_dict())

        if lowered.startswith("/compiler-cycle") or lowered.startswith("compiler-cycle"):
            if hasattr(self.runtime, "era15_nexus"):
                cycle = self.runtime.era15_nexus.run_compiler_cycle()
                tbl = self.runtime.era15_nexus.format_ascii_cycle_table(cycle)
                return RouterResponse(tbl, data=cycle.to_dict())

        # Stage 151: Sovereign Microkernel Architecture & TCB Scheduler
        if lowered in {"/sched-status", "sched-status", "/tasks-list", "tasks-list"}:
            if hasattr(self.runtime, "kernel_scheduler"):
                tbl = self.runtime.kernel_scheduler.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.kernel_scheduler.status())

        if lowered.startswith("/sched-tick") or lowered.startswith("sched-tick"):
            if hasattr(self.runtime, "kernel_scheduler"):
                parts = text.strip().split()
                count = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
                for _ in range(count):
                    self.runtime.kernel_scheduler.schedule_tick()
                out = f"[Microkernel Scheduler: Advanced {count} ticks]\n\n" + self.runtime.kernel_scheduler.format_ascii_status()
                return RouterResponse(out, data=self.runtime.kernel_scheduler.status())

        # Stage 152: Hardware Abstraction Layer & CPU Topology Sentinel
        if lowered in {"/hal-status", "hal-status", "/cpu-topology", "cpu-topology", "/cpu-info", "cpu-info"}:
            if hasattr(self.runtime, "hal_cpu"):
                tbl = self.runtime.hal_cpu.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.hal_cpu.topology.to_dict())

        if lowered in {"/tsc-calibrate", "tsc-calibrate"}:
            if hasattr(self.runtime, "hal_cpu"):
                ghz = self.runtime.hal_cpu.calibrate_tsc()
                cycles = self.runtime.hal_cpu.rdtsc()
                out = f"[TSC Calibrated: {ghz:.3f} GHz (Cycle Count: {cycles:,})]\n\n" + self.runtime.hal_cpu.format_ascii_status()
                return RouterResponse(out, data={"ghz": ghz, "cycles": cycles})

        # Stage 153: Virtual Memory Management & Page Table Synthesizer
        if lowered in {"/paging-status", "paging-status", "/vmm-status", "vmm-status"}:
            if hasattr(self.runtime, "paging_engine"):
                tbl = self.runtime.paging_engine.format_ascii_status()
                return RouterResponse(tbl, data={"mapped_pages": self.runtime.paging_engine.mapped_pages_count})

        if lowered.startswith("/v2p") or lowered.startswith("v2p"):
            if hasattr(self.runtime, "paging_engine"):
                parts = text.strip().split()
                if len(parts) > 1:
                    try:
                        vaddr = int(parts[1], 16) if parts[1].startswith("0x") else int(parts[1])
                        phys, flags = self.runtime.paging_engine.translate(vaddr)
                        out = f"[Virtual-to-Physical Translation]\nVirtual:  {hex(vaddr)}\nPhysical: {hex(phys)}\nFlags:    {hex(flags)}"
                        return RouterResponse(out, data={"virtual": hex(vaddr), "physical": hex(phys), "flags": hex(flags)})
                    except Exception as e:
                        return RouterResponse(f"[Page Fault / Translation Error]: {e}", data={"error": str(e)})
                return RouterResponse("Usage: /v2p <vaddr_hex>", data={"error": "missing_arg"})

        # Stage 154: IPC Fast-Ring & Shared Memory Channels
        if lowered in {"/ipc-status", "ipc-status", "/ipc-endpoints", "ipc-endpoints"}:
            if hasattr(self.runtime, "ipc_registry"):
                tbl = self.runtime.ipc_registry.format_ascii_status()
                return RouterResponse(tbl, data={"endpoints_count": len(self.runtime.ipc_registry.endpoints)})

        # Stage 155: Interrupt Service Routine & PIC/APIC Controller
        if lowered in {"/idt-status", "idt-status", "/interrupt-status", "interrupt-status"}:
            if hasattr(self.runtime, "interrupt_controller"):
                tbl = self.runtime.interrupt_controller.format_ascii_status()
                return RouterResponse(tbl, data={"stats": self.runtime.interrupt_controller.stats})

        # Stage 156: Direct Memory Access & Device Buffer Fabric
        if lowered in {"/dma-status", "dma-status", "/dma-channels", "dma-channels"}:
            if hasattr(self.runtime, "dma_fabric"):
                tbl = self.runtime.dma_fabric.format_ascii_status()
                return RouterResponse(tbl, data={"channels": len(self.runtime.dma_fabric.channels)})

        # Stage 157: Capability-Based Security Tokens & Enclave Sentinel
        if lowered in {"/capability-status", "capability-status", "/enclave-status", "enclave-status"}:
            if hasattr(self.runtime, "capability_manager"):
                tbl = self.runtime.capability_manager.format_ascii_status()
                return RouterResponse(tbl, data={"active_tokens": len(self.runtime.capability_manager.tokens)})

        # Stage 158: Sovereign Block Device Driver & Virtual Disk Fabric
        if lowered in {"/disk-status", "disk-status", "/disk-io", "disk-io"}:
            if hasattr(self.runtime, "block_fabric"):
                tbl = self.runtime.block_fabric.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.block_fabric.primary_disk.status())

        # Stage 159: Microkernel VFS & Content-Addressable Inode Storage
        if lowered in {"/vfs-status", "vfs-status", "/vfs-df", "vfs-df"}:
            if hasattr(self.runtime, "vfs"):
                tbl = self.runtime.vfs.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.vfs.cas.status())

        if lowered.startswith("/vfs-ls") or lowered.startswith("vfs-ls"):
            if hasattr(self.runtime, "vfs"):
                parts = text.strip().split()
                target_path = parts[1] if len(parts) > 1 else "/"
                try:
                    entries = self.runtime.vfs.sys_readdir(target_path)
                    lines = [f"VFS Directory Listing for: {target_path}"]
                    for e in entries:
                        lines.append(f"  [{e['type']:<4}] {e['name']:<24} (Inode {e['inode_id']}, {e['size']}B)")
                    return RouterResponse("\n".join(lines), data={"entries": entries})
                except Exception as ex:
                    return RouterResponse(f"[VFS Error]: {ex}", data={"error": str(ex)})

        if lowered in {"/vfs-mounts", "vfs-mounts"}:
            if hasattr(self.runtime, "vfs"):
                lines = ["VFS Active Mount Points:"]
                for mp, info in self.runtime.vfs.mount_table.items():
                    lines.append(f"  {mp:<15} on {info['device']} type {info['fs_type']}")
                return RouterResponse("\n".join(lines), data=self.runtime.vfs.mount_table)

        # Stage 160: Sovereign Singularity Nexus & Era 16 Master Seal
        if lowered in {"/verify-era16", "verify-era16", "/era16-status", "era16-status", "/master-seal-16"}:
            if hasattr(self.runtime, "era16_nexus"):
                cert = self.runtime.era16_nexus.verify_era16_integrity()
                tbl = self.runtime.era16_nexus.format_ascii_seal_table(cert)
                return RouterResponse(tbl, data=cert.to_dict())

        if lowered in {"/microkernel-cycle", "microkernel-cycle", "/ukern-cycle", "ukern-cycle"}:
            if hasattr(self.runtime, "era16_nexus"):
                cycle = self.runtime.era16_nexus.run_microkernel_cycle()
                tbl = self.runtime.era16_nexus.format_ascii_cycle_table(cycle)
                return RouterResponse(tbl, data=cycle.to_dict())

        # Stage 161: Byzantine Fault Tolerant SMR & Consensus Cluster
        if lowered in {"/bft-status", "bft-status"}:
            if hasattr(self.runtime, "bft_cluster"):
                tbl = self.runtime.bft_cluster.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.bft_cluster.status())

        if lowered.startswith("/bft-propose") or lowered.startswith("bft-propose"):
            if hasattr(self.runtime, "bft_cluster"):
                parts = text.strip().split(maxsplit=3)
                if len(parts) >= 3:
                    k = parts[1]
                    v = parts[2] if len(parts) > 2 else "1"
                    ok, reason, tx = self.runtime.bft_cluster.propose_transaction(op="SET", key=k, value=v)
                    out = f"[BFT Proposal {'COMMITTED' if ok else 'FAILED'}]: Key='{k}', Value='{v}' -> {reason}"
                    return RouterResponse(out, data={"ok": ok, "reason": reason})
                return RouterResponse("Usage: /bft-propose <key> <value>", data={"error": "missing_args"})

        if lowered in {"/bft-view", "bft-view"}:
            if hasattr(self.runtime, "bft_cluster"):
                ok, v, p = self.runtime.bft_cluster.trigger_view_change()
                return RouterResponse(f"[BFT View Change] New View: {v}, New Primary: {p}", data={"view": v, "primary": p})

        # Stage 162: Raft Leader Election & Distributed Heartbeat Sentinel
        if lowered in {"/raft-status", "raft-status"}:
            if hasattr(self.runtime, "raft_cluster"):
                tbl = self.runtime.raft_cluster.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.raft_cluster.status())

        if lowered in {"/raft-leader", "raft-leader"}:
            if hasattr(self.runtime, "raft_cluster"):
                ldr = self.runtime.raft_cluster.active_leader_id
                if not ldr:
                    ok = self.runtime.raft_cluster.start_election("raft_node_0")
                    ldr = self.runtime.raft_cluster.active_leader_id if ok else "None (Election Failed)"
                return RouterResponse(f"[Raft Active Leader]: {ldr}", data={"leader": ldr})

        if lowered.startswith("/raft-replicate") or lowered.startswith("raft-replicate"):
            if hasattr(self.runtime, "raft_cluster"):
                parts = text.strip().split(maxsplit=1)
                cmd_txt = parts[1] if len(parts) > 1 else "TEST_COMMAND"
                if not self.runtime.raft_cluster.active_leader_id:
                    self.runtime.raft_cluster.start_election("raft_node_0")
                ok, idx = self.runtime.raft_cluster.replicate_command({"cmd": cmd_txt})
                out = f"[Raft Replication {'SUCCESS' if ok else 'FAILED'}]: Log Index {idx} -> '{cmd_txt}'"
                return RouterResponse(out, data={"ok": ok, "index": idx})

        if lowered in {"/raft-stepdown", "raft-stepdown"}:
            if hasattr(self.runtime, "raft_cluster"):
                ok = self.runtime.raft_cluster.step_down_leader()
                return RouterResponse(f"[Raft Stepdown]: Leader stepped down to Follower", data={"ok": ok})

        # Stage 163: Sovereign Distributed Hash Table & Kademlia Mesh
        if lowered in {"/dht-status", "dht-status"}:
            if hasattr(self.runtime, "dht_mesh"):
                tbl = self.runtime.dht_mesh.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.dht_mesh.status())

        if lowered.startswith("/dht-store") or lowered.startswith("dht-store"):
            if hasattr(self.runtime, "dht_mesh"):
                parts = text.strip().split(maxsplit=2)
                if len(parts) >= 3:
                    k, v = parts[1], parts[2]
                    kid, nodes = self.runtime.dht_mesh.store_value(k, v)
                    out = f"[DHT Stored]: Key='{k}' (ID={hex(kid)[:10]}...) on {len(nodes)} peer nodes"
                    return RouterResponse(out, data={"key": k, "key_id": hex(kid), "nodes": len(nodes)})
                return RouterResponse("Usage: /dht-store <key> <val>", data={"error": "missing_args"})

        if lowered.startswith("/dht-get") or lowered.startswith("dht-get"):
            if hasattr(self.runtime, "dht_mesh"):
                parts = text.strip().split(maxsplit=1)
                if len(parts) >= 2:
                    k = parts[1]
                    val = self.runtime.dht_mesh.get_value(k)
                    if val is not None:
                        out = f"[DHT Hit]: Key='{k}' -> {val}"
                        return RouterResponse(out, data={"key": k, "found": True, "value": val})
                    return RouterResponse(f"[DHT Miss]: Key='{k}' not found in mesh", data={"key": k, "found": False})
                return RouterResponse("Usage: /dht-get <key>", data={"error": "missing_key"})

        # Stage 164: Vector Clock & Lamport Causality Ordering Fabric
        if lowered in {"/causal-status", "causal-status"}:
            if hasattr(self.runtime, "causal_fabric"):
                tbl = self.runtime.causal_fabric.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.causal_fabric.status())

        if lowered.startswith("/causal-send") or lowered.startswith("causal-send"):
            if hasattr(self.runtime, "causal_fabric"):
                parts = text.strip().split(maxsplit=2)
                node = parts[1] if len(parts) > 1 else "alpha"
                msg_txt = parts[2] if len(parts) > 2 else "STATE_TRANSITION"
                try:
                    evt = self.runtime.causal_fabric.broadcast(node, msg_txt)
                    out = f"[Causal Event Broadcast]: Node='{node}', Clock={evt.vclock.to_dict()} -> '{msg_txt}'"
                    return RouterResponse(out, data=evt.to_dict())
                except Exception as ex:
                    return RouterResponse(f"[Causal Error]: {ex}", data={"error": str(ex)})

        # Stage 165: Multi-Paxos Distributed Transaction Commit Protocol
        if lowered in {"/paxos-status", "paxos-status"}:
            if hasattr(self.runtime, "paxos_cluster"):
                tbl = self.runtime.paxos_cluster.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.paxos_cluster.status())

        if lowered.startswith("/paxos-propose") or lowered.startswith("paxos-propose"):
            if hasattr(self.runtime, "paxos_cluster"):
                parts = text.strip().split(maxsplit=2)
                val_txt = parts[1] if len(parts) > 1 else "TEST_VALUE"
                ok, slot = self.runtime.paxos_cluster.propose_slot_value({"cmd": val_txt})
                out = f"[Multi-Paxos {'COMMITTED' if ok else 'FAILED'}]: Slot {slot} -> '{val_txt}'"
                return RouterResponse(out, data={"ok": ok, "slot": slot})

        if lowered.startswith("/paxos-2pc") or lowered.startswith("paxos-2pc"):
            if hasattr(self.runtime, "paxos_cluster"):
                parts = text.strip().split(maxsplit=2)
                tx_id = parts[1] if len(parts) > 1 else "tx_default"
                ok, msg = self.runtime.paxos_cluster.execute_2pc_transaction(tx_id, [{"action": "TRANSFER", "amount": 100}])
                return RouterResponse(f"[2PC Result]: {msg}", data={"ok": ok, "message": msg})

        # Stage 166: Gossip Protocol & Epidemic State Propagation Engine
        if lowered in {"/gossip-status", "gossip-status"}:
            if hasattr(self.runtime, "gossip_mesh"):
                tbl = self.runtime.gossip_mesh.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.gossip_mesh.status())

        if lowered.startswith("/gossip-infect") or lowered.startswith("gossip-infect"):
            if hasattr(self.runtime, "gossip_mesh"):
                parts = text.strip().split(maxsplit=2)
                k = parts[1] if len(parts) > 1 else "key_rumor"
                v = parts[2] if len(parts) > 2 else "1"
                rumor = self.runtime.gossip_mesh.seed_update("peer_0", k, v)
                out = f"[Epidemic Rumor Injected]: ID={rumor.rumor_id}, Key='{k}' -> '{v}'"
                return RouterResponse(out, data=rumor.to_dict())

        if lowered in {"/gossip-step", "gossip-step"}:
            if hasattr(self.runtime, "gossip_mesh"):
                xfer = self.runtime.gossip_mesh.execute_gossip_round()
                return RouterResponse(f"[Gossip Round Completed]: Disseminated {xfer} rumor messages", data={"transfers": xfer})

        # Stage 167: Conflict-Free Replicated Data Types (CRDTs) Synthesizer
        if lowered in {"/crdt-status", "crdt-status"}:
            if hasattr(self.runtime, "crdt_synth"):
                tbl = self.runtime.crdt_synth.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.crdt_synth.status())

        if lowered.startswith("/crdt-counter") or lowered.startswith("crdt-counter"):
            if hasattr(self.runtime, "crdt_synth"):
                parts = text.strip().split()
                delta = int(parts[1]) if len(parts) > 1 and (parts[1].isdigit() or parts[1].startswith("-")) else 1
                if delta >= 0:
                    self.runtime.crdt_synth.counters["rep_0"].increment(delta)
                else:
                    self.runtime.crdt_synth.counters["rep_0"].decrement(abs(delta))
                val = self.runtime.crdt_synth.counters["rep_0"].value
                return RouterResponse(f"[PNCounter rep_0 Updated]: Delta={delta}, New Value={val}", data={"value": val})

        if lowered in {"/crdt-merge", "crdt-merge"}:
            if hasattr(self.runtime, "crdt_synth"):
                self.runtime.crdt_synth.synchronize_mesh()
                tbl = self.runtime.crdt_synth.format_ascii_status()
                return RouterResponse(f"[CRDT Mesh Synchronized Across All Replicas]\n\n" + tbl, data=self.runtime.crdt_synth.status())

        # Stage 168: Sovereign Mesh Network Tunneling & Virtual TAP/TUN Fabric
        if lowered in {"/tunnel-status", "tunnel-status"}:
            if hasattr(self.runtime, "mesh_tunnel"):
                tbl = self.runtime.mesh_tunnel.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.mesh_tunnel.status())

        if lowered.startswith("/tunnel-send") or lowered.startswith("tunnel-send"):
            if hasattr(self.runtime, "mesh_tunnel"):
                parts = text.strip().split(maxsplit=2)
                src = parts[1] if len(parts) > 1 else "tap0"
                msg_txt = parts[2] if len(parts) > 2 else "PAYLOAD"
                ok, tgts = self.runtime.mesh_tunnel.send_ethernet_packet(src, "52:54:00:aa:bb:02", msg_txt.encode("utf-8"))
                return RouterResponse(f"[Mesh Frame Routed]: Src={src} -> Targets={tgts}", data={"ok": ok, "targets": tgts})

        # Stage 169: Distributed Deadlock Detection & Chandy-Misra Sentinel
        if lowered in {"/deadlock-status", "deadlock-status"}:
            if hasattr(self.runtime, "deadlock_sentinel"):
                tbl = self.runtime.deadlock_sentinel.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.deadlock_sentinel.status())

        if lowered in {"/deadlock-wfg", "deadlock-wfg"}:
            if hasattr(self.runtime, "deadlock_sentinel"):
                wfg = self.runtime.deadlock_sentinel.build_wfg()
                lines = ["Wait-For Graph (WFG) Active Dependencies:"]
                for waiter, holders in wfg.items():
                    lines.append(f"  {waiter} -> waits for -> {', '.join(holders)}")
                if not wfg:
                    lines.append("  (No active lock wait dependencies)")
                return RouterResponse("\n".join(lines), data={"wfg": {k: list(v) for k, v in wfg.items()}})

        # Stage 170: Sovereign Singularity Nexus & Era 17 Master Seal
        if lowered in {"/verify-era17", "verify-era17", "/era17-status", "era17-status", "/master-seal-17"}:
            if hasattr(self.runtime, "era17_nexus"):
                cert = self.runtime.era17_nexus.verify_era17_integrity()
                tbl = self.runtime.era17_nexus.format_ascii_seal_table(cert)
                return RouterResponse(tbl, data=cert.to_dict())

        if lowered in {"/consensus-cycle", "consensus-cycle", "/era17-cycle", "era17-cycle"}:
            if hasattr(self.runtime, "era17_nexus"):
                cycle = self.runtime.era17_nexus.run_consensus_mesh_cycle()
                tbl = self.runtime.era17_nexus.format_ascii_cycle_table(cycle)
                return RouterResponse(tbl, data=cycle.to_dict())

        # Stage 171: Consistent Hashing Ring & Virtual Node Partitioning (Era 18)
        if lowered in {"/ring-status", "ring-status"}:
            if hasattr(self.runtime, "hash_ring"):
                tbl = self.runtime.hash_ring.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.hash_ring.status())

        if lowered.startswith("/ring-lookup ") or lowered.startswith("ring-lookup "):
            prefix = "/ring-lookup " if lowered.startswith("/ring-lookup ") else "ring-lookup "
            key = text[len(prefix):].strip()
            if hasattr(self.runtime, "hash_ring"):
                primary = self.runtime.hash_ring.get_primary_node(key)
                prefs = self.runtime.hash_ring.get_preference_list(key)
                token = self.runtime.hash_ring.get_token_for_key(key)
                msg = f"[Hash Ring Lookup]: Key='{key}' -> Token={token} | Primary='{primary}' | Replicas={prefs}"
                return RouterResponse(msg, data={"key": key, "token": token, "primary": primary, "preference_list": prefs})

        if lowered.startswith("/ring-add ") or lowered.startswith("ring-add "):
            prefix = "/ring-add " if lowered.startswith("/ring-add ") else "ring-add "
            nid = text[len(prefix):].strip()
            if hasattr(self.runtime, "hash_ring"):
                vns = self.runtime.hash_ring.add_node(nid)
                return RouterResponse(f"[Hash Ring]: Added node '{nid}' with {vns} virtual nodes.", data={"node": nid, "vnodes": vns})

        if lowered.startswith("/ring-remove ") or lowered.startswith("ring-remove "):
            prefix = "/ring-remove " if lowered.startswith("/ring-remove ") else "ring-remove "
            nid = text[len(prefix):].strip()
            if hasattr(self.runtime, "hash_ring"):
                vns = self.runtime.hash_ring.remove_node(nid)
                return RouterResponse(f"[Hash Ring]: Removed node '{nid}' ({vns} virtual nodes pruned).", data={"node": nid, "vnodes_removed": vns})

        # Stage 172: Distributed LSM-Tree & Memtable SSTable Engine (Era 18)
        if lowered in {"/lsm-status", "lsm-status"}:
            if hasattr(self.runtime, "lsm_tree"):
                tbl = self.runtime.lsm_tree.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.lsm_tree.status())

        if lowered.startswith("/lsm-put ") or lowered.startswith("lsm-put "):
            prefix = "/lsm-put " if lowered.startswith("/lsm-put ") else "lsm-put "
            parts = text[len(prefix):].strip().split(maxsplit=1)
            k = parts[0] if parts else ""
            v = parts[1] if len(parts) > 1 else ""
            if hasattr(self.runtime, "lsm_tree"):
                ts = self.runtime.lsm_tree.put(k, v)
                return RouterResponse(f"[LSM Put]: Key='{k}' stored at ts={ts:.4f}", data={"key": k, "value": v, "timestamp": ts})

        if lowered.startswith("/lsm-get ") or lowered.startswith("lsm-get "):
            prefix = "/lsm-get " if lowered.startswith("/lsm-get ") else "lsm-get "
            k = text[len(prefix):].strip()
            if hasattr(self.runtime, "lsm_tree"):
                v = self.runtime.lsm_tree.get(k)
                if v is not None:
                    return RouterResponse(f"[LSM Get]: Key='{k}' -> Value='{v}'", data={"key": k, "value": v, "found": True})
                return RouterResponse(f"[LSM Get]: Key='{k}' -> NOT FOUND (absent or tombstoned)", data={"key": k, "value": None, "found": False})

        if lowered.startswith("/lsm-del ") or lowered.startswith("lsm-del "):
            prefix = "/lsm-del " if lowered.startswith("/lsm-del ") else "lsm-del "
            k = text[len(prefix):].strip()
            if hasattr(self.runtime, "lsm_tree"):
                ts = self.runtime.lsm_tree.delete(k)
                return RouterResponse(f"[LSM Delete]: Tombstone written for Key='{k}' at ts={ts:.4f}", data={"key": k, "timestamp": ts})

        if lowered in {"/lsm-flush", "lsm-flush"}:
            if hasattr(self.runtime, "lsm_tree"):
                sst = self.runtime.lsm_tree.force_flush()
                sid = sst.sstable_id if sst else "NONE (Empty Memtable)"
                return RouterResponse(f"[LSM Flush]: Flushed active Memtable to SSTable='{sid}'", data={"sstable_id": sid})

        if lowered in {"/lsm-compact", "lsm-compact"}:
            if hasattr(self.runtime, "lsm_tree"):
                sst = self.runtime.lsm_tree.compact_level(0)
                sid = sst.sstable_id if sst else "NONE (Insufficient tables)"
                return RouterResponse(f"[LSM Compaction]: Compacted L0 to SSTable='{sid}'", data={"compacted_sstable": sid})

        # Stage 173: Quorum Read-Repair & Active Anti-Entropy Merkle Fabric (Era 18)
        if lowered in {"/quorum-status", "quorum-status"}:
            if hasattr(self.runtime, "quorum_coordinator"):
                tbl = self.runtime.quorum_coordinator.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.quorum_coordinator.status())

        if lowered.startswith("/quorum-write ") or lowered.startswith("quorum-write "):
            prefix = "/quorum-write " if lowered.startswith("/quorum-write ") else "quorum-write "
            parts = text[len(prefix):].strip().split(maxsplit=1)
            k = parts[0] if parts else ""
            v = parts[1] if len(parts) > 1 else ""
            if hasattr(self.runtime, "quorum_coordinator"):
                ok, acks, ts = self.runtime.quorum_coordinator.quorum_write(k, v)
                msg = f"[Quorum Write]: Key='{k}' | Acks={acks} | Success={ok} | ts={ts:.4f}"
                return RouterResponse(msg, data={"key": k, "value": v, "acks": acks, "success": ok, "timestamp": ts})

        if lowered.startswith("/quorum-read ") or lowered.startswith("quorum-read "):
            prefix = "/quorum-read " if lowered.startswith("/quorum-read ") else "quorum-read "
            k = text[len(prefix):].strip()
            if hasattr(self.runtime, "quorum_coordinator"):
                res = self.runtime.quorum_coordinator.quorum_read(k)
                msg = (
                    f"[Quorum Read]: Key='{k}' -> Value='{res.resolved_value}' | "
                    f"Quorum={res.quorum_achieved} | Repaired={res.nodes_repaired}"
                )
                return RouterResponse(msg, data=res.to_dict())

        if lowered.startswith("/quorum-sync ") or lowered.startswith("quorum-sync "):
            prefix = "/quorum-sync " if lowered.startswith("/quorum-sync ") else "quorum-sync "
            parts = text[len(prefix):].strip().split(maxsplit=1)
            na = parts[0] if parts else "replica_node_0"
            nb = parts[1] if len(parts) > 1 else "replica_node_1"
            if hasattr(self.runtime, "quorum_coordinator"):
                res = self.runtime.quorum_coordinator.run_anti_entropy_sync(na, nb)
                msg = (
                    f"[Anti-Entropy Merkle Sync]: {na} <-> {nb} | In-Sync={res.root_match} | "
                    f"Keys Synced={res.keys_synced} ({res.duration_ms} ms)"
                )
                return RouterResponse(msg, data=res.to_dict())

        # Stage 174: Distributed Write-Ahead Log (WAL) Segment Replication (Era 18)
        if lowered in {"/wal-status", "wal-status"}:
            if hasattr(self.runtime, "wal_manager"):
                tbl = self.runtime.wal_manager.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.wal_manager.status())

        if lowered.startswith("/wal-append ") or lowered.startswith("wal-append "):
            prefix = "/wal-append " if lowered.startswith("/wal-append ") else "wal-append "
            parts = text[len(prefix):].strip().split(maxsplit=2)
            tx_id = parts[0] if parts else "tx_def"
            k = parts[1] if len(parts) > 1 else "k"
            v = parts[2] if len(parts) > 2 else "v"
            if hasattr(self.runtime, "wal_manager"):
                from backend.lucy_core.distributed_wal_replication import LogRecordType
                ok, rec = self.runtime.wal_manager.append_log(tx_id, LogRecordType.PUT, k, v)
                msg = f"[WAL Append]: LSN={rec.lsn} | Tx={tx_id} | Key='{k}' | Quorum={ok} | CRC={rec.crc32}"
                return RouterResponse(msg, data=rec.to_dict())

        if lowered in {"/wal-checkpoint", "wal-checkpoint"}:
            if hasattr(self.runtime, "wal_manager"):
                rec = self.runtime.wal_manager.write_checkpoint()
                msg = f"[WAL Checkpoint]: Written at LSN={rec.lsn} | HWM={self.runtime.wal_manager._high_water_mark}"
                return RouterResponse(msg, data=rec.to_dict())

        if lowered in {"/wal-replay", "wal-replay"}:
            if hasattr(self.runtime, "wal_manager"):
                cnt, state = self.runtime.wal_manager.replay_log_from_checkpoint()
                msg = f"[WAL Replay]: Replayed {cnt} log records | Recovered State Size={len(state)}"
                return RouterResponse(msg, data={"replayed_records": cnt, "state": state})

        # Stage 175: Distributed Snapshot Isolation & MVCC Storage (Era 18)
        if lowered in {"/mvcc-status", "mvcc-status"}:
            if hasattr(self.runtime, "mvcc_storage"):
                tbl = self.runtime.mvcc_storage.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.mvcc_storage.status())

        if lowered.startswith("/mvcc-begin ") or lowered.startswith("mvcc-begin "):
            prefix = "/mvcc-begin " if lowered.startswith("/mvcc-begin ") else "mvcc-begin "
            tid = text[len(prefix):].strip()
            if hasattr(self.runtime, "mvcc_storage"):
                tx = self.runtime.mvcc_storage.begin_transaction(tid)
                return RouterResponse(f"[MVCC Begin]: Tx '{tx.tx_id}' started at snapshot read_ts={tx.read_ts}", data=tx.to_dict())

        if lowered.startswith("/mvcc-put ") or lowered.startswith("mvcc-put "):
            prefix = "/mvcc-put " if lowered.startswith("/mvcc-put ") else "mvcc-put "
            parts = text[len(prefix):].strip().split(maxsplit=2)
            tid = parts[0] if parts else ""
            k = parts[1] if len(parts) > 1 else ""
            v = parts[2] if len(parts) > 2 else ""
            if hasattr(self.runtime, "mvcc_storage"):
                self.runtime.mvcc_storage.tx_put(tid, k, v)
                return RouterResponse(f"[MVCC Put]: Tx '{tid}' buffered Key='{k}' -> Value='{v}'", data={"tx_id": tid, "key": k, "value": v})

        if lowered.startswith("/mvcc-get ") or lowered.startswith("mvcc-get "):
            prefix = "/mvcc-get " if lowered.startswith("/mvcc-get ") else "mvcc-get "
            parts = text[len(prefix):].strip().split(maxsplit=1)
            tid = parts[0] if parts else ""
            k = parts[1] if len(parts) > 1 else ""
            if hasattr(self.runtime, "mvcc_storage"):
                v = self.runtime.mvcc_storage.tx_get(tid, k)
                return RouterResponse(f"[MVCC Get]: Tx '{tid}' Key='{k}' -> Value='{v}'", data={"tx_id": tid, "key": k, "value": v})

        if lowered.startswith("/mvcc-commit ") or lowered.startswith("mvcc-commit "):
            prefix = "/mvcc-commit " if lowered.startswith("/mvcc-commit ") else "mvcc-commit "
            tid = text[len(prefix):].strip()
            if hasattr(self.runtime, "mvcc_storage"):
                from backend.lucy_core.distributed_mvcc_storage import WriteConflictError
                try:
                    cts = self.runtime.mvcc_storage.commit_transaction(tid)
                    return RouterResponse(f"[MVCC Commit]: Tx '{tid}' COMMITTED at commit_ts={cts}", data={"tx_id": tid, "commit_ts": cts, "success": True})
                except WriteConflictError as e:
                    return RouterResponse(f"[MVCC Conflict]: Tx '{tid}' ABORTED ({e})", data={"tx_id": tid, "error": str(e), "success": False})

        if lowered in {"/mvcc-vacuum", "mvcc-vacuum"}:
            if hasattr(self.runtime, "mvcc_storage"):
                purged = self.runtime.mvcc_storage.vacuum()
                return RouterResponse(f"[MVCC Vacuum]: Purged {purged} dead superseded versions.", data={"purged_versions": purged})

        # Stage 176: Dynamic Shard Migration & Range Splitter Sentinel (Era 18)
        if lowered in {"/shard-status", "shard-status"}:
            if hasattr(self.runtime, "shard_sentinel"):
                tbl = self.runtime.shard_sentinel.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.shard_sentinel.status())

        if lowered.startswith("/shard-put ") or lowered.startswith("shard-put "):
            prefix = "/shard-put " if lowered.startswith("/shard-put ") else "shard-put "
            parts = text[len(prefix):].strip().split(maxsplit=1)
            k = parts[0] if parts else ""
            v = parts[1] if len(parts) > 1 else ""
            if hasattr(self.runtime, "shard_sentinel"):
                sid, node = self.runtime.shard_sentinel.put_key(k, v)
                msg = f"[Shard Put]: Key='{k}' stored in Shard='{sid}' on Node='{node}'"
                return RouterResponse(msg, data={"shard_id": sid, "node": node, "key": k, "value": v})

        if lowered.startswith("/shard-get ") or lowered.startswith("shard-get "):
            prefix = "/shard-get " if lowered.startswith("/shard-get ") else "shard-get "
            k = text[len(prefix):].strip()
            if hasattr(self.runtime, "shard_sentinel"):
                v = self.runtime.shard_sentinel.get_key(k)
                shard = self.runtime.shard_sentinel.route_key(k)
                sid = shard.shard_id if shard else "NONE"
                msg = f"[Shard Get]: Key='{k}' -> Value='{v}' (from Shard='{sid}')"
                return RouterResponse(msg, data={"key": k, "value": v, "shard_id": sid})

        if lowered.startswith("/shard-split ") or lowered.startswith("shard-split "):
            prefix = "/shard-split " if lowered.startswith("/shard-split ") else "shard-split "
            sid = text[len(prefix):].strip()
            if hasattr(self.runtime, "shard_sentinel"):
                left, right = self.runtime.shard_sentinel.split_shard(sid)
                msg = f"[Shard Split]: Shard '{sid}' split into '{left.shard_id}' [{left.start_key}..{left.end_key}) and '{right.shard_id}' [{right.start_key}..{right.end_key})"
                return RouterResponse(msg, data={"left": left.to_dict(), "right": right.to_dict()})

        if lowered.startswith("/shard-migrate ") or lowered.startswith("shard-migrate "):
            prefix = "/shard-migrate " if lowered.startswith("/shard-migrate ") else "shard-migrate "
            parts = text[len(prefix):].strip().split(maxsplit=1)
            sid = parts[0] if parts else ""
            dest = parts[1] if len(parts) > 1 else "node_beta"
            if hasattr(self.runtime, "shard_sentinel"):
                res = self.runtime.shard_sentinel.migrate_shard(sid, dest)
                msg = f"[Shard Live Migration]: {sid} {res.source_node} -> {dest} | Transferred={res.keys_transferred} keys ({res.duration_ms} ms)"
                return RouterResponse(msg, data=res.to_dict())

        # Stage 177: Distributed Secondary Indexing & Global Query Fabric (Era 18)
        if lowered in {"/idx-status", "idx-status"}:
            if hasattr(self.runtime, "index_fabric"):
                tbl = self.runtime.index_fabric.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.index_fabric.status())

        if lowered.startswith("/idx-create ") or lowered.startswith("idx-create "):
            prefix = "/idx-create " if lowered.startswith("/idx-create ") else "idx-create "
            parts = text[len(prefix):].strip().split(maxsplit=1)
            iname = parts[0] if parts else ""
            fld = parts[1] if len(parts) > 1 else iname
            if hasattr(self.runtime, "index_fabric"):
                idx = self.runtime.index_fabric.create_index(iname, fld)
                return RouterResponse(f"[Secondary Index]: Created index '{iname}' on field '{fld}'", data={"index": iname, "field": fld})

        if lowered.startswith("/idx-put ") or lowered.startswith("idx-put "):
            prefix = "/idx-put " if lowered.startswith("/idx-put ") else "idx-put "
            parts = text[len(prefix):].strip().split(maxsplit=2)
            pk = parts[0] if parts else ""
            fld = parts[1] if len(parts) > 1 else ""
            val = parts[2] if len(parts) > 2 else ""
            if hasattr(self.runtime, "index_fabric"):
                rec = self.runtime.index_fabric.get_record(pk) or {}
                rec[fld] = val
                self.runtime.index_fabric.put_record(pk, rec)
                return RouterResponse(f"[Index Put]: Record '{pk}' updated with {fld}='{val}'", data={"pk": pk, fld: val})

        if lowered.startswith("/idx-query ") or lowered.startswith("idx-query "):
            prefix = "/idx-query " if lowered.startswith("/idx-query ") else "idx-query "
            parts = text[len(prefix):].strip().split(maxsplit=1)
            fld = parts[0] if parts else ""
            val = parts[1] if len(parts) > 1 else ""
            if hasattr(self.runtime, "index_fabric"):
                from backend.lucy_core.distributed_secondary_index import QueryPredicate, QueryOperator
                res = self.runtime.index_fabric.query([QueryPredicate(field=fld, operator=QueryOperator.EQUALS, value=val)])
                msg = f"[Index Query]: Field '{fld}' == '{val}' -> Matched {res.total_matched} PKs: {res.matched_primary_keys} ({res.execution_time_ms} ms)"
                return RouterResponse(msg, data=res.to_dict())

        # Stage 178: Raft-Partitioned Distributed KV Engine (Era 18)
        if lowered in {"/mraft-status", "mraft-status"}:
            if hasattr(self.runtime, "multi_raft_kv"):
                tbl = self.runtime.multi_raft_kv.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.multi_raft_kv.status())

        if lowered.startswith("/mraft-put ") or lowered.startswith("mraft-put "):
            prefix = "/mraft-put " if lowered.startswith("/mraft-put ") else "mraft-put "
            parts = text[len(prefix):].strip().split(maxsplit=1)
            k = parts[0] if parts else ""
            v = parts[1] if len(parts) > 1 else ""
            if hasattr(self.runtime, "multi_raft_kv"):
                ok, gid, idx = self.runtime.multi_raft_kv.put(k, v)
                msg = f"[Multi-Raft Put]: Key='{k}' committed in Group='{gid}' at LogIndex={idx} (Quorum={ok})"
                return RouterResponse(msg, data={"key": k, "value": v, "group_id": gid, "log_index": idx, "committed": ok})

        if lowered.startswith("/mraft-get ") or lowered.startswith("mraft-get "):
            prefix = "/mraft-get " if lowered.startswith("/mraft-get ") else "mraft-get "
            k = text[len(prefix):].strip()
            if hasattr(self.runtime, "multi_raft_kv"):
                v = self.runtime.multi_raft_kv.get(k)
                gid = self.runtime.multi_raft_kv._get_group_id_for_key(k)
                msg = f"[Multi-Raft Get]: Key='{k}' -> Value='{v}' (from Group='{gid}')"
                return RouterResponse(msg, data={"key": k, "value": v, "group_id": gid})

        # Stage 179: Geo-Replication Replication Fabric & Multi-Region Gateway (Era 18)
        if lowered in {"/geo-status", "geo-status"}:
            if hasattr(self.runtime, "geo_fabric"):
                tbl = self.runtime.geo_fabric.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.geo_fabric.status())

        if lowered.startswith("/geo-write ") or lowered.startswith("geo-write "):
            prefix = "/geo-write " if lowered.startswith("/geo-write ") else "geo-write "
            parts = text[len(prefix):].strip().split(maxsplit=2)
            reg = parts[0] if parts else "us-east"
            k = parts[1] if len(parts) > 1 else ""
            v = parts[2] if len(parts) > 2 else ""
            if hasattr(self.runtime, "geo_fabric"):
                rec = self.runtime.geo_fabric.write_regional(reg, k, v)
                msg = f"[Geo Write]: Key='{k}' committed in Region='{reg}' (Origin={rec.origin_region}, Version={rec.version})"
                return RouterResponse(msg, data=rec.to_dict())

        if lowered.startswith("/geo-read ") or lowered.startswith("geo-read "):
            prefix = "/geo-read " if lowered.startswith("/geo-read ") else "geo-read "
            parts = text[len(prefix):].strip().split(maxsplit=1)
            reg = parts[0] if parts else "us-east"
            k = parts[1] if len(parts) > 1 else ""
            if hasattr(self.runtime, "geo_fabric"):
                v = self.runtime.geo_fabric.read_regional(reg, k)
                msg = f"[Geo Read]: Region='{reg}' | Key='{k}' -> Value='{v}'"
                return RouterResponse(msg, data={"region": reg, "key": k, "value": v})

        if lowered in {"/geo-sync-all", "geo-sync-all"}:
            if hasattr(self.runtime, "geo_fabric"):
                total = self.runtime.geo_fabric.sync_all_regions()
                return RouterResponse(f"[Geo Sync All]: Synchronized {total} cross-region records across cluster.", data={"synced_records": total})

        # Stage 180: Sovereign Singularity Nexus & Era 18 Master Seal (Era 18)
        if lowered in {"/verify-era18", "verify-era18", "/era18-status", "era18-status", "/master-seal-18"}:
            if hasattr(self.runtime, "era18_nexus"):
                cert = self.runtime.era18_nexus.verify_era18_integrity()
                tbl = self.runtime.era18_nexus.format_ascii_seal_table(cert)
                return RouterResponse(tbl, data=cert.to_dict())

        if lowered in {"/storage-cycle", "storage-cycle", "/era18-cycle", "era18-cycle"}:
            if hasattr(self.runtime, "era18_nexus"):
                cycle = self.runtime.era18_nexus.run_storage_geo_cycle()
                tbl = self.runtime.era18_nexus.format_ascii_cycle_table(cycle)
                return RouterResponse(tbl, data=cycle.to_dict())

        # Stage 181: Columnar Vector Storage & Compressed Arrow Layout (Era 19)
        if lowered in {"/columnar-status", "columnar-status"}:
            if hasattr(self.runtime, "columnar_storage"):
                tbl = self.runtime.columnar_storage.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.columnar_storage.status())

        if lowered.startswith("/columnar-agg ") or lowered.startswith("columnar-agg "):
            prefix = "/columnar-agg " if lowered.startswith("/columnar-agg ") else "columnar-agg "
            parts = text[len(prefix):].strip().split()
            tname = parts[0] if parts else ""
            fn = parts[1] if len(parts) > 1 else "SUM"
            col = parts[2] if len(parts) > 2 else ""
            if hasattr(self.runtime, "columnar_storage"):
                val = self.runtime.columnar_storage.query_aggregation(tname, fn, col)
                msg = f"[Columnar Vector Aggregation]: {fn.upper()}({tname}.{col}) = {val}"
                return RouterResponse(msg, data={"table": tname, "agg": fn, "column": col, "result": val})

        # Stage 182: Cost-Based Distributed Query Optimizer (CBO) (Era 19)
        if lowered in {"/cbo-status", "cbo-status", "/query-optimizer", "query-optimizer"}:
            if hasattr(self.runtime, "query_optimizer"):
                tbl = self.runtime.query_optimizer.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.query_optimizer.status())

        if lowered.startswith("/cbo-explain ") or lowered.startswith("cbo-explain "):
            prefix = "/cbo-explain " if lowered.startswith("/cbo-explain ") else "cbo-explain "
            tname = text[len(prefix):].strip()
            if hasattr(self.runtime, "query_optimizer"):
                from backend.lucy_core.cost_based_query_optimizer import LogicalScan
                l_scan = LogicalScan(tname)
                p_scan = self.runtime.query_optimizer.optimize(l_scan)
                tree = p_scan.explain()
                return RouterResponse(f"Query Plan for {tname}:\n" + tree, data=p_scan.to_dict())

        # Stage 183: Vectorized Execution Engine & SIMD Batch Operator (Era 19)
        if lowered in {"/vector-status", "vector-status", "/vectorized-status", "vectorized-status"}:
            if hasattr(self.runtime, "vectorized_engine"):
                tbl = self.runtime.vectorized_engine.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.vectorized_engine.status())

        if lowered.startswith("/vector-exec ") or lowered.startswith("vector-exec "):
            prefix = "/vector-exec " if lowered.startswith("/vector-exec ") else "vector-exec "
            tname = text[len(prefix):].strip()
            if hasattr(self.runtime, "vectorized_engine"):
                rows, telemetry = self.runtime.vectorized_engine.execute_query(tname)
                msg = f"[Vectorized Execution]: {len(rows)} rows scanned in {telemetry.elapsed_ms}ms ({telemetry.throughput_rows_per_sec} rows/sec)"
                return RouterResponse(msg, data={"rows_count": len(rows), "telemetry": telemetry.to_dict()})

        # Stage 184: Distributed Hash Join & Broadcast Shuffle Fabric (Era 19)
        if lowered in {"/join-status", "join-status", "/hash-join-status", "hash-join-status"}:
            if hasattr(self.runtime, "hash_join_fabric"):
                tbl = self.runtime.hash_join_fabric.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.hash_join_fabric.status())

        if lowered in {"/join-bench", "join-bench"}:
            if hasattr(self.runtime, "hash_join_fabric"):
                left = [{"u_id": i, "name": f"user_{i}"} for i in range(100)]
                right = [{"id": j, "role": "admin" if j % 2 == 0 else "user"} for j in range(20)]
                res, tel = self.runtime.hash_join_fabric.execute_join(left, right, "u_id", "id")
                msg = f"[Distributed Join Benchmark]: Strategy={tel.strategy_used}, OutRows={tel.output_rows}, ShuffledBytes={tel.network_bytes_shuffled}, Latency={tel.elapsed_ms}ms"
                return RouterResponse(msg, data={"results_count": len(res), "telemetry": tel.to_dict()})

        # Stage 185: Approximate Query Processing & HyperLogLog Count-Distinct (Era 19)
        if lowered in {"/aqp-status", "aqp-status", "/approx-query-status", "approx-query-status"}:
            if hasattr(self.runtime, "approx_query_fabric"):
                tbl = self.runtime.approx_query_fabric.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.approx_query_fabric.status())

        if lowered.startswith("/aqp-distinct ") or lowered.startswith("aqp-distinct "):
            prefix = "/aqp-distinct " if lowered.startswith("/aqp-distinct ") else "aqp-distinct "
            parts = text[len(prefix):].strip().split()
            tname = parts[0] if parts else ""
            cname = parts[1] if len(parts) > 1 else ""
            if hasattr(self.runtime, "approx_query_fabric"):
                est = self.runtime.approx_query_fabric.approx_count_distinct(tname, cname)
                msg = f"[AQP HyperLogLog]: APPROX_COUNT_DISTINCT({tname}.{cname}) = {est}"
                return RouterResponse(msg, data={"table": tname, "column": cname, "distinct": est})

        # Stage 186: Materialized View Refresh & Incremental View Maintenance (IVM) (Era 19)
        if lowered in {"/ivm-status", "ivm-status", "/mv-status", "mv-status"}:
            if hasattr(self.runtime, "materialized_view_fabric"):
                tbl = self.runtime.materialized_view_fabric.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.materialized_view_fabric.status())

        if lowered.startswith("/ivm-query ") or lowered.startswith("ivm-query "):
            prefix = "/ivm-query " if lowered.startswith("/ivm-query ") else "ivm-query "
            vname = text[len(prefix):].strip()
            if hasattr(self.runtime, "materialized_view_fabric"):
                try:
                    rows = self.runtime.materialized_view_fabric.query_view(vname)
                    msg = f"[Materialized View IVM]: Query '{vname}' returned {len(rows)} rows."
                    return RouterResponse(msg, data={"view": vname, "rows": rows})
                except Exception as e:
                    return RouterResponse(f"[Materialized View IVM Error]: {e}", error=True)

        # Stage 187: Streaming Window Aggregation & Watermark Sentinel (Era 19)
        if lowered in {"/window-status", "window-status", "/streaming-window-status", "streaming-window-status"}:
            if hasattr(self.runtime, "streaming_window_fabric"):
                tbl = self.runtime.streaming_window_fabric.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.streaming_window_fabric.status())

        if lowered in {"/window-emit", "window-emit"}:
            if hasattr(self.runtime, "streaming_window_fabric"):
                emitted = self.runtime.streaming_window_fabric.emitted_windows
                msg = f"[Streaming Windows]: Total {len(emitted)} windows emitted so far."
                return RouterResponse(msg, data={"emitted_count": len(emitted), "latest": [w.to_dict() for w in emitted[-5:]]})

        # Stage 188: Adaptive Query Execution (AQE) & Runtime Replanner (Era 19)
        if lowered in {"/aqe-status", "aqe-status", "/adaptive-query-status", "adaptive-query-status"}:
            if hasattr(self.runtime, "aqe_fabric"):
                tbl = self.runtime.aqe_fabric.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.aqe_fabric.status())

        if lowered in {"/aqe-replan", "aqe-replan"}:
            if hasattr(self.runtime, "aqe_fabric"):
                stat = self.runtime.aqe_fabric.status()
                msg = f"[AQE Runtime Replanner]: Stages={stat['total_stages']}, CoalesceOpts={stat['coalesce_optimizations']}, BroadcastConvs={stat['broadcast_conversions']}, SkewSplits={stat['skew_splits']}"
                return RouterResponse(msg, data=stat)

        # Stage 189: Distributed OLAP Storage Chunk Compactor & Parquet Encoder (Era 19)
        if lowered in {"/parquet-status", "parquet-status", "/compactor-status", "compactor-status"}:
            if hasattr(self.runtime, "olap_compactor_fabric"):
                tbl = self.runtime.olap_compactor_fabric.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.olap_compactor_fabric.status())

        if lowered.startswith("/parquet-compact ") or lowered.startswith("parquet-compact "):
            prefix = "/parquet-compact " if lowered.startswith("/parquet-compact ") else "parquet-compact "
            tname = text[len(prefix):].strip()
            if hasattr(self.runtime, "olap_compactor_fabric"):
                meta = self.runtime.olap_compactor_fabric.compact_table(tname)
                msg = f"[Parquet Compaction]: Compacted '{tname}' ({meta.total_rows} rows, {len(meta.row_groups)} row groups)"
                return RouterResponse(msg, data=meta.to_dict())

        # Stage 190: Sovereign Singularity Nexus & Era 19 Master Seal (Era 19)
        if lowered in {"/era19-status", "era19-status"}:
            if hasattr(self.runtime, "era19_nexus"):
                return RouterResponse(json.dumps(self.runtime.era19_nexus.status(), indent=2), data=self.runtime.era19_nexus.status())

        if lowered in {"/olap-cycle", "olap-cycle", "/era19-cycle", "era19-cycle"}:
            if hasattr(self.runtime, "era19_nexus"):
                rep = self.runtime.era19_nexus.run_olap_analytics_cycle()
                tbl = self.runtime.era19_nexus.format_ascii_cycle_table(rep)
                return RouterResponse(tbl, data=rep.to_dict())

        if lowered in {"/seal-era19", "seal-era19"}:
            if hasattr(self.runtime, "era19_nexus"):
                cert = self.runtime.era19_nexus.seal_era19()
                tbl = self.runtime.era19_nexus.format_ascii_seal_certificate(cert)
                return RouterResponse(tbl, data=cert.to_dict())

        # Stage 191: Autonomous JIT Micro-Optimizer & Bytecode Vectorizer (Era 20)
        if lowered in {"/jit-status", "jit-status", "/jit-optimizer-status", "jit-optimizer-status"}:
            if hasattr(self.runtime, "jit_optimizer"):
                tbl = self.runtime.jit_optimizer.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.jit_optimizer.status())

        if lowered.startswith("/jit-profile ") or lowered.startswith("jit-profile "):
            prefix = "/jit-profile " if lowered.startswith("/jit-profile ") else "jit-profile "
            fname = text[len(prefix):].strip()
            if hasattr(self.runtime, "jit_optimizer"):
                tier = self.runtime.jit_optimizer.record_call(fname, 1.2)
                msg = f"[JIT Profiler]: Function '{fname}' recorded. Current JIT Tier: {tier}"
                return RouterResponse(msg, data={"func_name": fname, "tier": tier})

        # Stage 192: Dynamic Kernel Self-Healing & Crash Recovery Supervisor (Era 20)
        if lowered in {"/healing-status", "healing-status", "/self-healing-status", "self-healing-status"}:
            if hasattr(self.runtime, "kernel_self_healing"):
                tbl = self.runtime.kernel_self_healing.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.kernel_self_healing.status())

        if lowered.startswith("/healing-fault ") or lowered.startswith("healing-fault "):
            prefix = "/healing-fault " if lowered.startswith("/healing-fault ") else "healing-fault "
            parts = text[len(prefix):].strip().split()
            sub_name = parts[0] if parts else "core"
            f_type = parts[1] if len(parts) > 1 else "CRASH"
            if hasattr(self.runtime, "kernel_self_healing"):
                if sub_name not in self.runtime.kernel_self_healing.subsystems:
                    self.runtime.kernel_self_healing.register_subsystem(sub_name)
                inc = self.runtime.kernel_self_healing.inject_fault(sub_name, f_type)
                msg = f"[Self-Healing]: Injected {f_type} into '{sub_name}'. Healed: {inc.recovery_successful} ({inc.recovery_duration_ms}ms)"
                return RouterResponse(msg, data=inc.to_dict())

        # Stage 193: Sovereign Distributed Consensus Raft-BFT Hybrid (Era 20)
        if lowered in {"/raft-bft-status", "raft-bft-status", "/hybrid-bft-status", "hybrid-bft-status"}:
            if hasattr(self.runtime, "raft_bft_fabric"):
                tbl = self.runtime.raft_bft_fabric.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.raft_bft_fabric.status())

        if lowered.startswith("/raft-bft-propose ") or lowered.startswith("raft-bft-propose "):
            prefix = "/raft-bft-propose " if lowered.startswith("/raft-bft-propose ") else "raft-bft-propose "
            parts = text[len(prefix):].strip().split()
            k = parts[0] if parts else "key"
            v = parts[1] if len(parts) > 1 else "val"
            if hasattr(self.runtime, "raft_bft_fabric"):
                ok, entry = self.runtime.raft_bft_fabric.propose_command({k: v})
                msg = f"[Raft-BFT]: Proposed '{k}={v}'. Committed: {ok} (Log Index: {entry.index if entry else 'N/A'})"
                return RouterResponse(msg, data=entry.to_dict() if entry else {})

        # Stage 194: Autonomous Zero-Copy Inter-Process Shared Memory Ring (Era 20)
        if lowered in {"/shm-status", "shm-status", "/ipc-shm-status", "ipc-shm-status"}:
            if hasattr(self.runtime, "zerocopy_shm_fabric"):
                tbl = self.runtime.zerocopy_shm_fabric.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.zerocopy_shm_fabric.status())

        if lowered.startswith("/shm-write ") or lowered.startswith("shm-write "):
            prefix = "/shm-write " if lowered.startswith("/shm-write ") else "shm-write "
            msg_txt = text[len(prefix):].strip()
            if hasattr(self.runtime, "zerocopy_shm_fabric"):
                slot_id = self.runtime.zerocopy_shm_fabric.write_direct(msg_txt.encode("utf-8"))
                msg = f"[Zero-Copy SHM]: Wrote {len(msg_txt)} bytes into slot {slot_id}."
                return RouterResponse(msg, data={"slot_id": slot_id, "bytes": len(msg_txt)})

        # Stage 195: Autonomous Neural Weights Sharder & Distributed Tensor Runtime (Era 20)
        if lowered in {"/tensor-status", "tensor-status", "/distributed-tensor-status", "distributed-tensor-status"}:
            if hasattr(self.runtime, "tensor_runtime_fabric"):
                tbl = self.runtime.tensor_runtime_fabric.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.tensor_runtime_fabric.status())

        if lowered.startswith("/tensor-shard ") or lowered.startswith("tensor-shard "):
            prefix = "/tensor-shard " if lowered.startswith("/tensor-shard ") else "tensor-shard "
            m_name = text[len(prefix):].strip() or "w_sample"
            if hasattr(self.runtime, "tensor_runtime_fabric"):
                from backend.lucy_core.distributed_tensor_runtime import ShardingStrategy
                sample_matrix = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0]]
                shards = self.runtime.tensor_runtime_fabric.shard_weight_matrix(m_name, sample_matrix, ShardingStrategy.ROW_PARALLEL)
                msg = f"[Tensor Sharder]: Matrix '{m_name}' (4x2) row-sharded into {len(shards)} virtual ranks."
                return RouterResponse(msg, data={"matrix": m_name, "shards": len(shards)})

        # Stage 196: Self-Evolving Code Synthesis & AST Verification Pipeline (Era 20)
        if lowered in {"/ast-status", "ast-status", "/self-evolving-code-status", "self-evolving-code-status"}:
            if hasattr(self.runtime, "self_evolving_code_fabric"):
                tbl = self.runtime.self_evolving_code_fabric.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.self_evolving_code_fabric.status())

        if lowered.startswith("/ast-audit ") or lowered.startswith("ast-audit "):
            prefix = "/ast-audit " if lowered.startswith("/ast-audit ") else "ast-audit "
            raw_code = text[len(prefix):].strip()
            if hasattr(self.runtime, "self_evolving_code_fabric"):
                is_safe, viols = self.runtime.self_evolving_code_fabric.analyze_safety(raw_code)
                msg = f"[AST Audit]: Safe={is_safe}. Violations: {viols if viols else 'None'}"
                return RouterResponse(msg, data={"safe": is_safe, "violations": viols})

        # Stage 197: Autonomous Global Chrono-Log & Event Sourcing Fabric (Era 20)
        if lowered in {"/chrono-status", "chrono-status", "/chrono-log-status", "chrono-log-status"}:
            if hasattr(self.runtime, "chrono_log_fabric"):
                tbl = self.runtime.chrono_log_fabric.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.chrono_log_fabric.status())

        if lowered.startswith("/chrono-append ") or lowered.startswith("chrono-append "):
            prefix = "/chrono-append " if lowered.startswith("/chrono-append ") else "chrono-append "
            parts = text[len(prefix):].strip().split()
            s_id = parts[0] if parts else "default_stream"
            e_type = parts[1] if len(parts) > 1 else "SET"
            k = parts[2] if len(parts) > 2 else "key"
            v = parts[3] if len(parts) > 3 else "val"
            if hasattr(self.runtime, "chrono_log_fabric"):
                ev = self.runtime.chrono_log_fabric.append_event(s_id, e_type, {k: v})
                msg = f"[Chrono-Log]: Appended Event Seq {ev.global_seq} to '{s_id}' (HLC: {ev.hlc.to_string()})"
                return RouterResponse(msg, data=ev.to_dict())

        # Stage 198: Sovereign Autonomous Daemon Mesh & Heartbeat Sentinel (Era 20)
        if lowered in {"/daemon-mesh-status", "daemon-mesh-status", "/sentinel-status", "sentinel-status"}:
            if hasattr(self.runtime, "daemon_mesh_fabric"):
                tbl = self.runtime.daemon_mesh_fabric.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.daemon_mesh_fabric.status())

        if lowered.startswith("/mesh-ping ") or lowered.startswith("mesh-ping "):
            prefix = "/mesh-ping " if lowered.startswith("/mesh-ping ") else "mesh-ping "
            nid = text[len(prefix):].strip() or "peer_node"
            if hasattr(self.runtime, "daemon_mesh_fabric"):
                if nid not in self.runtime.daemon_mesh_fabric.peers:
                    self.runtime.daemon_mesh_fabric.register_peer(nid)
                self.runtime.daemon_mesh_fabric.record_heartbeat(nid)
                msg = f"[Daemon Mesh]: Heartbeat recorded for '{nid}'. State: ALIVE."
                return RouterResponse(msg, data={"node_id": nid, "state": "ALIVE"})

        # Stage 199: Bicentennial Singularity Nexus & 200-Stage Master Orchestrator (Era 20)
        if lowered in {"/bicentennial-nexus-status", "bicentennial-nexus-status", "/stage199-status", "stage199-status"}:
            if hasattr(self.runtime, "bicentennial_nexus"):
                tbl = self.runtime.bicentennial_nexus.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.bicentennial_nexus.status())

        if lowered.startswith("/singularity-run ") or lowered.startswith("singularity-run "):
            prefix = "/singularity-run " if lowered.startswith("/singularity-run ") else "singularity-run "
            action_txt = text[len(prefix):].strip() or "transcendence"
            if hasattr(self.runtime, "bicentennial_nexus"):
                res = self.runtime.bicentennial_nexus.execute_singularity_pipeline({"action": action_txt})
                msg = f"[Singularity Nexus]: Pipeline {res.pipeline_id} completed. Score: {res.singularity_score:.1f}% (BFT={res.bft_committed}, SHM Slot={res.shm_slot_id}, AST={res.ast_optimized}, Chrono Seq={res.chrono_event_seq}, Mesh Primary={res.mesh_primary})"
                return RouterResponse(msg, data=res.to_dict())

        # Stage 200: The Sovereign Bicentennial AGI Grand Master Seal (Era 20)
        if lowered in {"/grand-master-seal", "grand-master-seal", "/bicentennial-seal", "bicentennial-seal", "/stage200-seal", "stage200-seal"}:
            if hasattr(self.runtime, "bicentennial_grand_master_seal"):
                tbl = self.runtime.bicentennial_grand_master_seal.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.bicentennial_grand_master_seal.status())

        # Stage 201: Autonomous Multi-Kernel Federation Bus & Cross-Kernel RPC (Era 21)
        if lowered in {"/federation-status", "federation-status", "/multi-kernel-status", "multi-kernel-status"}:
            if hasattr(self.runtime, "multi_kernel_federation"):
                tbl = self.runtime.multi_kernel_federation.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.multi_kernel_federation.status())

        if lowered.startswith("/federation-peer ") or lowered.startswith("federation-peer "):
            prefix = "/federation-peer " if lowered.startswith("/federation-peer ") else "federation-peer "
            parts = text[len(prefix):].strip().split()
            kid = parts[0] if parts else "satellite_kernel_1"
            kname = parts[1] if len(parts) > 1 else "Satellite"
            kendpoint = parts[2] if len(parts) > 2 else "ipc://satellite"
            if hasattr(self.runtime, "multi_kernel_federation"):
                peer = self.runtime.multi_kernel_federation.register_remote_kernel(kid, kname, kendpoint, ["compute", "memory"])
                msg = f"[Kernel Federation]: Peered remote kernel '{peer.kernel_id}' ({peer.name}) at '{peer.endpoint}'."
                return RouterResponse(msg, data=peer.to_dict())

        # Stage 202: Quantum-Resistant Lattice Cryptography (Era 21)
        if lowered in {"/pqc-status", "pqc-status", "/quantum-crypto-status", "quantum-crypto-status"}:
            if hasattr(self.runtime, "post_quantum_crypto"):
                tbl = self.runtime.post_quantum_crypto.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.post_quantum_crypto.status())

        if lowered.startswith("/pqc-sign ") or lowered.startswith("pqc-sign "):
            prefix = "/pqc-sign " if lowered.startswith("/pqc-sign ") else "pqc-sign "
            raw_msg = text[len(prefix):].strip().encode("utf-8")
            if hasattr(self.runtime, "post_quantum_crypto"):
                sig = self.runtime.post_quantum_crypto.sign_quantum(raw_msg)
                msg = f"[ML-DSA Post-Quantum Signature]: Message Digest={sig.message_digest[:16]}... | Sig Len={len(sig.signature_bytes)}B"
                return RouterResponse(msg, data=sig.to_dict())

        # Stage 203: Autonomous Decentralized Sovereign Contract (Era 21)
        if lowered in {"/contract-status", "contract-status", "/smart-contract-status", "smart-contract-status"}:
            if hasattr(self.runtime, "sovereign_contract_engine"):
                tbl = self.runtime.sovereign_contract_engine.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.sovereign_contract_engine.status())

        if lowered.startswith("/contract-deploy ") or lowered.startswith("contract-deploy "):
            prefix = "/contract-deploy " if lowered.startswith("/contract-deploy ") else "contract-deploy "
            owner = text[len(prefix):].strip() or "Senin"
            if hasattr(self.runtime, "sovereign_contract_engine"):
                from backend.lucy_core.sovereign_contract_engine import ContractInstruction
                code = [
                    ContractInstruction("PUSH", 100),
                    ContractInstruction("PUSH", 200),
                    ContractInstruction("ADD"),
                    ContractInstruction("RETURN"),
                ]
                cid = self.runtime.sovereign_contract_engine.deploy_contract(owner, code)
                msg = f"[Sovereign Contract Engine]: Contract '{cid}' deployed by owner '{owner}'."
                return RouterResponse(msg, data={"contract_id": cid, "owner": owner})

        # Stage 204: Neuromorphic Event-Driven Spike Router (Era 21)
        if lowered in {"/spike-status", "spike-status", "/neuromorphic-status", "neuromorphic-status"}:
            if hasattr(self.runtime, "neuromorphic_spike_mesh"):
                tbl = self.runtime.neuromorphic_spike_mesh.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.neuromorphic_spike_mesh.status())

        if lowered.startswith("/spike-step ") or lowered.startswith("spike-step "):
            prefix = "/spike-step " if lowered.startswith("/spike-step ") else "spike-step "
            val_str = text[len(prefix):].strip()
            try:
                curr = float(val_str)
            except ValueError:
                curr = 1.5
            if hasattr(self.runtime, "neuromorphic_spike_mesh"):
                spikes = self.runtime.neuromorphic_spike_mesh.step_simulation(external_currents={0: curr})
                msg = f"[Neuromorphic Mesh]: Step completed. Spikes emitted: {len(spikes)} (Neuron 0 current={curr})."
                return RouterResponse(msg, data={"spikes_count": len(spikes), "spikes": [s.to_dict() for s in spikes]})

        # Stage 205: Knowledge Distillation & Model Pruner (Era 21)
        if lowered in {"/pruner-status", "pruner-status", "/distillation-status", "distillation-status"}:
            if hasattr(self.runtime, "knowledge_distillation_pruner"):
                tbl = self.runtime.knowledge_distillation_pruner.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.knowledge_distillation_pruner.status())

        if lowered.startswith("/prune-matrix ") or lowered.startswith("prune-matrix "):
            prefix = "/prune-matrix " if lowered.startswith("/prune-matrix ") else "prune-matrix "
            sp_str = text[len(prefix):].strip()
            try:
                sp_val = float(sp_str)
            except ValueError:
                sp_val = 0.5
            if hasattr(self.runtime, "knowledge_distillation_pruner"):
                sample = [[1.0, 2.0], [3.0, 4.0]]
                _, csr, act = self.runtime.knowledge_distillation_pruner.prune_unstructured(sample, target_sparsity=sp_val)
                msg = f"[Model Pruner]: Matrix pruned to {act*100:.1f}% sparsity. Non-zero elements: {len(csr.values)}."
                return RouterResponse(msg, data={"actual_sparsity": act, "csr": csr.to_dict()})

        # Stage 206: Autonomous Zero-Knowledge Proof Invariant Generator (Era 21)
        if lowered in {"/zk-status", "zk-status", "/zk-prover-status", "zk-prover-status"}:
            if hasattr(self.runtime, "zk_invariant_prover"):
                tbl = self.runtime.zk_invariant_prover.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.zk_invariant_prover.status())

        if lowered.startswith("/zk-prove-multiplier ") or lowered.startswith("zk-prove-multiplier "):
            prefix = "/zk-prove-multiplier " if lowered.startswith("/zk-prove-multiplier ") else "zk-prove-multiplier "
            parts = text[len(prefix):].strip().split()
            try:
                wa = int(parts[0]) if parts else 7
                wb = int(parts[1]) if len(parts) > 1 else 11
            except ValueError:
                wa, wb = 7, 11
            if hasattr(self.runtime, "zk_invariant_prover"):
                prod = wa * wb
                proof = self.runtime.zk_invariant_prover.prove_statement(
                    "circuit_multiplier",
                    witness={"w_a": wa, "w_b": wb},
                    public_inputs={"public_c": prod},
                )
                msg = f"[ZK-SNARK Prover]: Generated proof '{proof.proof_id}' for public_c={prod}. Private witness hidden."
                return RouterResponse(msg, data=proof.to_dict())

        # Stage 207: Latency-Adaptive Compute Governor (Era 21)
        if lowered in {"/compute-governor-status", "compute-governor-status", "/latency-governor-status", "latency-governor-status"}:
            if hasattr(self.runtime, "compute_governor"):
                tbl = self.runtime.compute_governor.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.compute_governor.status())

        if lowered.startswith("/governor-sample ") or lowered.startswith("governor-sample "):
            prefix = "/governor-sample " if lowered.startswith("/governor-sample ") else "governor-sample "
            val_str = text[len(prefix):].strip()
            try:
                lat = float(val_str)
            except ValueError:
                lat = 25.0
            if hasattr(self.runtime, "compute_governor"):
                prof = self.runtime.compute_governor.record_latency(lat)
                msg = f"[Compute Governor]: Recorded latency {lat:.2f}ms. Active Profile: {prof.value}."
                return RouterResponse(msg, data={"latency_ms": lat, "profile": prof.value})

        # Stage 221: Quantum Density Matrix & Mixed-State Dephasing Fabric (Era 23)
        if lowered in {"/density-status", "density-status", "/mixed-state-status", "mixed-state-status"}:
            if hasattr(self.runtime, "density_matrix_simulator"):
                tbl = self.runtime.density_matrix_simulator.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.density_matrix_simulator.status())

        if lowered in {"/density-pure", "density-pure"}:
            if hasattr(self.runtime, "density_matrix_simulator"):
                import math
                dm = self.runtime.density_matrix_simulator.prepare_pure_state([1.0 / math.sqrt(2), 1.0 / math.sqrt(2)])
                s = self.runtime.density_matrix_simulator.compute_von_neumann_entropy(dm)
                msg = f"[Quantum Density]: Prepared pure state |+>. Purity: {dm.purity():.4f}, Entropy: {s:.4f}."
                return RouterResponse(msg, data={"purity": dm.purity(), "entropy": s, "matrix": dm.to_real_display()})

        if lowered in {"/density-decohere", "density-decohere"}:
            if hasattr(self.runtime, "density_matrix_simulator"):
                import math
                dm = self.runtime.density_matrix_simulator.prepare_pure_state([1.0 / math.sqrt(2), 1.0 / math.sqrt(2)])
                damped = self.runtime.density_matrix_simulator.apply_phase_damping(dm, lambda_rate=0.5)
                s = self.runtime.density_matrix_simulator.compute_von_neumann_entropy(damped)
                msg = f"[Quantum Density]: Applied T2 phase damping (50%). Purity dropped to: {damped.purity():.4f}, Entropy increased to: {s:.4f}."
                return RouterResponse(msg, data={"purity": damped.purity(), "entropy": s, "matrix": damped.to_real_display()})

        # Stage 222: Holographic Swarm Coordination & Flocking Consensus
        if lowered in {"/swarm-status", "swarm-status"}:
            if hasattr(self.runtime, "holographic_swarm"):
                tbl = self.runtime.holographic_swarm.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.holographic_swarm.status())
            return RouterResponse("Holographic swarm fabric not available.")

        if lowered in {"/swarm-step", "swarm-step"}:
            if hasattr(self.runtime, "holographic_swarm"):
                self.runtime.holographic_swarm.step_swarm(dt=0.1)
                tbl = self.runtime.holographic_swarm.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.holographic_swarm.status())
            return RouterResponse("Holographic swarm fabric not available.")

        if lowered.startswith("/swarm-goal ") or lowered.startswith("swarm-goal "):
            if hasattr(self.runtime, "holographic_swarm"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    try:
                        gx, gy = float(parts[1]), float(parts[2])
                        from backend.lucy_core.holographic_swarm_mesh import Vector2D
                        self.runtime.holographic_swarm.set_goal(gx, gy)
                        return RouterResponse(f"Swarm goal set to ({gx}, {gy})")
                    except ValueError:
                        return RouterResponse("Invalid coordinates for swarm goal. Usage: /swarm-goal <x> <y>")
            return RouterResponse("Holographic swarm fabric not available.")

        # Stage 223: Sub-Atomic Micro-Architecture Pipeline Emulation & Speculative Execution Governor
        if lowered in {"/subatomic-pipeline-status", "subatomic-pipeline-status", "/subatomic-status", "subatomic-status"}:
            if hasattr(self.runtime, "subatomic_pipeline_governor"):
                tbl = self.runtime.subatomic_pipeline_governor.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.subatomic_pipeline_governor.status())
            return RouterResponse("Subatomic pipeline governor not available.")

        if lowered in {"/subatomic-pipeline-step", "subatomic-pipeline-step", "/subatomic-step", "subatomic-step"}:
            if hasattr(self.runtime, "subatomic_pipeline_governor"):
                res = self.runtime.subatomic_pipeline_governor.step_cycle()
                tbl = self.runtime.subatomic_pipeline_governor.format_ascii_status()
                return RouterResponse(tbl, data=res)
            return RouterResponse("Subatomic pipeline governor not available.")

        if (
            lowered.startswith("/subatomic-pipeline-mode ")
            or lowered.startswith("subatomic-pipeline-mode ")
            or lowered.startswith("/subatomic-mode ")
            or lowered.startswith("subatomic-mode ")
        ):
            if hasattr(self.runtime, "subatomic_pipeline_governor"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    m_str = parts[1].upper()
                    from backend.lucy_core.subatomic_pipeline_governor import GovernorMode
                    if hasattr(GovernorMode, m_str):
                        self.runtime.subatomic_pipeline_governor.set_governor_mode(GovernorMode[m_str])
                        return RouterResponse(f"Pipeline governor mode set to {m_str}")
                    return RouterResponse(f"Unknown governor mode '{m_str}'. Valid: STRICT_MITIGATION, MONITOR_ONLY, PERMISSIVE")
            return RouterResponse("Subatomic pipeline governor not available.")

        # Stage 224: Universal Multi-Verse Counterfactual State Forker & Timeline Brancher
        if lowered in {"/multiverse-status", "multiverse-status"}:
            if hasattr(self.runtime, "multiverse_forker"):
                tbl = self.runtime.multiverse_forker.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.multiverse_forker.status())
            return RouterResponse("Multiverse state forker not available.")

        if lowered.startswith("/multiverse-fork ") or lowered.startswith("multiverse-fork "):
            if hasattr(self.runtime, "multiverse_forker"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    nb = parts[1]
                    from_b = parts[2] if len(parts) >= 3 else "canonical"
                    try:
                        self.runtime.multiverse_forker.fork_branch(nb, from_branch_id=from_b)
                        return RouterResponse(f"Forked new timeline '{nb}' from '{from_b}'.")
                    except Exception as e:
                        return RouterResponse(f"Fork failed: {e}")
            return RouterResponse("Usage: /multiverse-fork <new_branch> [from_branch]")

        if lowered.startswith("/multiverse-switch ") or lowered.startswith("multiverse-switch "):
            if hasattr(self.runtime, "multiverse_forker"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    target_b = parts[1]
                    try:
                        self.runtime.multiverse_forker.switch_active_branch(target_b)
                        return RouterResponse(f"Switched active timeline to '{target_b}'.")
                    except Exception as e:
                        return RouterResponse(f"Switch failed: {e}")
            return RouterResponse("Usage: /multiverse-switch <branch>")

        if lowered.startswith("/multiverse-divergence ") or lowered.startswith("multiverse-divergence "):
            if hasattr(self.runtime, "multiverse_forker"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    b1, b2 = parts[1], parts[2]
                    try:
                        div = self.runtime.multiverse_forker.compute_divergence(b1, b2)
                        msg = f"Divergence between '{b1}' and '{b2}': {div['total_differences']} diffs (Ratio: {div['divergence_ratio']:.2%})"
                        return RouterResponse(msg, data=div)
                    except Exception as e:
                        return RouterResponse(f"Divergence failed: {e}")
            return RouterResponse("Usage: /multiverse-divergence <branch_a> <branch_b>")

        # Stage 225: Autonomous Zero-Knowledge Proof Aggregator & Recursive SNARK Verifier
        if lowered in {"/snark-status", "snark-status"}:
            if hasattr(self.runtime, "recursive_snark_aggregator"):
                tbl = self.runtime.recursive_snark_aggregator.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.recursive_snark_aggregator.status())
            return RouterResponse("Recursive SNARK aggregator not available.")

        if lowered in {"/snark-prove-sample", "snark-prove-sample"}:
            if hasattr(self.runtime, "recursive_snark_aggregator"):
                p = self.runtime.recursive_snark_aggregator.prove_circuit("multiplier", witness=[1, 7, 6, 42], public_inputs=[42])
                ok = self.runtime.recursive_snark_aggregator.verify_proof(p)
                return RouterResponse(f"Generated and verified proof {p.proof_id} for circuit '{p.circuit_name}': {'VALID' if ok else 'INVALID'}", data=p.to_dict())
            return RouterResponse("Recursive SNARK aggregator not available.")

        if lowered in {"/snark-aggregate-sample", "snark-aggregate-sample"}:
            if hasattr(self.runtime, "recursive_snark_aggregator"):
                p1 = self.runtime.recursive_snark_aggregator.prove_circuit("multiplier", witness=[1, 3, 5, 15], public_inputs=[15])
                p2 = self.runtime.recursive_snark_aggregator.prove_circuit("multiplier", witness=[1, 4, 10, 40], public_inputs=[40])
                agg = self.runtime.recursive_snark_aggregator.aggregate_proofs([p1, p2])
                ok = self.runtime.recursive_snark_aggregator.verify_proof(agg)
                return RouterResponse(f"Synthesized Recursive SNARK {agg.proof_id} folding 2 proofs: {'VALID' if ok else 'INVALID'} (Depth: {agg.recursion_depth})", data=agg.to_dict())
            return RouterResponse("Recursive SNARK aggregator not available.")

        # Stage 226: Self-Supervised Topological Data Analysis & Persistent Homology Engine
        if lowered in {"/tda-status", "tda-status"}:
            if hasattr(self.runtime, "topological_data_analysis"):
                tbl = self.runtime.topological_data_analysis.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.topological_data_analysis.status())
            return RouterResponse("Topological data analysis fabric not available.")

        if lowered in {"/tda-circle-sample", "tda-circle-sample"}:
            if hasattr(self.runtime, "topological_data_analysis"):
                self.runtime.topological_data_analysis.generate_circle_sample("demo_circle", num_points=16, radius=1.0)
                intervals = self.runtime.topological_data_analysis.compute_vietoris_rips_homology("demo_circle")
                h1_count = sum(1 for it in intervals if it.dimension == 1)
                msg = f"Generated circle point cloud 'demo_circle'. Discovered {len(intervals)} persistence intervals ({h1_count} topological 1-cycles / H1 loops)."
                return RouterResponse(msg, data={"intervals": [it.to_dict() for it in intervals]})
            return RouterResponse("Topological data analysis fabric not available.")

        if lowered.startswith("/tda-betti ") or lowered.startswith("tda-betti "):
            if hasattr(self.runtime, "topological_data_analysis"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    cid, eps_str = parts[1], parts[2]
                    try:
                        eps = float(eps_str)
                        b = self.runtime.topological_data_analysis.compute_betti_numbers(cid, epsilon=eps)
                        msg = f"Betti numbers for '{cid}' at epsilon={eps:.2f}: beta_0={b['beta_0']} (components), beta_1={b['beta_1']} (1-holes)"
                        return RouterResponse(msg, data=b)
                    except Exception as e:
                        return RouterResponse(f"TDA Betti computation failed: {e}")
            return RouterResponse("Usage: /tda-betti <cloud_id> <epsilon>")

        # Stage 227: Autonomous Hardware Energy Budget Governor & Thermal-Joule Throttle Fabric
        if lowered in {"/energy-status", "energy-status"}:
            if hasattr(self.runtime, "energy_budget_governor"):
                tbl = self.runtime.energy_budget_governor.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.energy_budget_governor.status())
            return RouterResponse("Energy budget governor not available.")

        if lowered.startswith("/energy-profile ") or lowered.startswith("energy-profile "):
            if hasattr(self.runtime, "energy_budget_governor"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    p_str = parts[1].upper()
                    from backend.lucy_core.energy_budget_governor import PowerProfile
                    if hasattr(PowerProfile, p_str):
                        self.runtime.energy_budget_governor.set_profile(PowerProfile[p_str])
                        return RouterResponse(f"Energy governor power profile set to {p_str}")
                    return RouterResponse(f"Unknown power profile '{p_str}'. Valid: TURBO, NOMINAL_BALANCED, CONSERVATIVE, CRITICAL_EMERGENCY")
            return RouterResponse("Usage: /energy-profile <profile_name>")

        if lowered.startswith("/energy-workload ") or lowered.startswith("energy-workload "):
            if hasattr(self.runtime, "energy_budget_governor"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    tname = parts[1]
                    dur = float(parts[2]) if len(parts) >= 3 else 0.2
                    receipt = self.runtime.energy_budget_governor.execute_governed_workload(tname, workload_duration_s=dur)
                    msg = f"Workload '{tname}' executed under thermal-joule governor: {receipt.joules_consumed:.2f} Joules ({receipt.average_power_w:.1f}W avg, Peak Temp: {receipt.peak_temp_c:.1f}C)."
                    return RouterResponse(msg, data=receipt.to_dict())
            return RouterResponse("Usage: /energy-workload <task_name> [duration_s]")

        # Stage 228: High-Dimensional Hyperdimensional Computing & Vector Symbolic Architecture
        if lowered in {"/hdc-status", "hdc-status"}:
            if hasattr(self.runtime, "hyperdimensional_computing"):
                tbl = self.runtime.hyperdimensional_computing.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.hyperdimensional_computing.status())
            return RouterResponse("Hyperdimensional computing fabric not available.")

        if lowered.startswith("/hdc-bind ") or lowered.startswith("hdc-bind "):
            if hasattr(self.runtime, "hyperdimensional_computing"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    sa, sb = parts[1], parts[2]
                    bound = self.runtime.hyperdimensional_computing.bind_symbols(sa, sb)
                    msg = f"Bound symbols '{sa}' and '{sb}' into {bound.dimension}-D hypervector."
                    return RouterResponse(msg, data={"dim": bound.dimension, "sim_to_a": bound.cosine_similarity(self.runtime.hyperdimensional_computing.generate_symbol(sa))})
            return RouterResponse("Usage: /hdc-bind <symbol_a> <symbol_b>")

        if lowered in {"/hdc-analogy-sample", "hdc-analogy-sample"}:
            if hasattr(self.runtime, "hyperdimensional_computing"):
                self.runtime.hyperdimensional_computing.store_composite_record("usa_sample", {"currency": "dollar", "capital": "dc"})
                self.runtime.hyperdimensional_computing.store_composite_record("mexico_sample", {"currency": "peso", "capital": "cdmx"})
                best_cand, sim = self.runtime.hyperdimensional_computing.solve_relational_analogy("usa_sample", "mexico_sample", "dollar")
                msg = f"Kanerva Analogy Solver (Dollar : USA :: ? : Mexico) -> Solved: '{best_cand}' (Cosine Similarity: {sim:.4f})"
                return RouterResponse(msg, data={"analogy": "Dollar:USA :: ?:Mexico", "solution": best_cand, "similarity": sim})
            return RouterResponse("Hyperdimensional computing fabric not available.")

        # Stage 229: Autonomous Planetary Geo-Distributed Disaster Recovery & State Relocator
        if lowered in {"/geo-dr-status", "geo-dr-status"}:
            if hasattr(self.runtime, "geo_disaster_recovery"):
                tbl = self.runtime.geo_disaster_recovery.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.geo_disaster_recovery.status())
            return RouterResponse("Geo-disaster recovery fabric not available.")

        if lowered.startswith("/geo-dr-replicate ") or lowered.startswith("geo-dr-replicate "):
            if hasattr(self.runtime, "geo_disaster_recovery"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    k, v = parts[1], parts[2]
                    try:
                        seq = self.runtime.geo_disaster_recovery.replicate_state({k: v})
                        msg = f"Replicated state {{{k}: {v}}} across planetary quorum at Seq #{seq}."
                        return RouterResponse(msg, data={"seq": seq, "key": k, "val": v})
                    except Exception as e:
                        return RouterResponse(f"Replication failed: {e}")
            return RouterResponse("Usage: /geo-dr-replicate <key> <val>")

        if lowered.startswith("/geo-dr-disaster ") or lowered.startswith("geo-dr-disaster "):
            if hasattr(self.runtime, "geo_disaster_recovery"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    rid = parts[1]
                    try:
                        self.runtime.geo_disaster_recovery.trigger_disaster(rid)
                        new_prim = self.runtime.geo_disaster_recovery.primary_region_id
                        msg = f"Simulated disaster on region '{rid}'. Current active primary: '{new_prim}'."
                        return RouterResponse(msg, data={"disaster_region": rid, "new_primary": new_prim})
                    except Exception as e:
                        return RouterResponse(f"Disaster simulation failed: {e}")
            return RouterResponse("Usage: /geo-dr-disaster <region_id>")

        if lowered.startswith("/geo-dr-restore ") or lowered.startswith("geo-dr-restore "):
            if hasattr(self.runtime, "geo_disaster_recovery"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    rid = parts[1]
                    try:
                        self.runtime.geo_disaster_recovery.restore_region(rid)
                        msg = f"Restored region '{rid}' and synchronized state from primary '{self.runtime.geo_disaster_recovery.primary_region_id}'."
                        return RouterResponse(msg, data={"restored_region": rid})
                    except Exception as e:
                        return RouterResponse(f"Restoration failed: {e}")
            return RouterResponse("Usage: /geo-dr-restore <region_id>")

        # Stage 230: The Sovereign Era 23 Master Seal & Universal Multi-Verse Genesis
        if lowered in {"/era23-seal", "era23-seal", "/universal-multiverse-seal", "universal-multiverse-seal"}:
            if hasattr(self.runtime, "era23_master_seal"):
                tbl = self.runtime.era23_master_seal.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.era23_master_seal.status())
            return RouterResponse("Era 23 Master Seal fabric not available.")

        # Stage 231: Neuromorphic Spiking Neural Network & LIF Synaptic Fabric
        if lowered in {"/snn-status", "snn-status", "/lif-status", "lif-status"}:
            if hasattr(self.runtime, "neuromorphic_spiking"):
                tbl = self.runtime.neuromorphic_spiking.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.neuromorphic_spiking.status())
            return RouterResponse("Neuromorphic spiking fabric not available.")

        if lowered in {"/snn-step", "snn-step", "/lif-step", "lif-step"}:
            if hasattr(self.runtime, "neuromorphic_spiking"):
                spikes = self.runtime.neuromorphic_spiking.step(input_currents={"in_0": 35.0})
                msg = f"Stepped neuromorphic clock (+1.0ms). Spikes fired: {spikes if spikes else 'None'}."
                return RouterResponse(msg, data={"spikes": spikes, "time_ms": self.runtime.neuromorphic_spiking.current_time_ms})
            return RouterResponse("Neuromorphic spiking fabric not available.")

        if (
            lowered.startswith("/snn-sim ")
            or lowered.startswith("snn-sim ")
            or lowered.startswith("/lif-sim ")
            or lowered.startswith("lif-sim ")
        ):
            if hasattr(self.runtime, "neuromorphic_spiking"):
                parts = raw_text.strip().split()
                dur = float(parts[1]) if len(parts) >= 2 else 20.0
                res = self.runtime.neuromorphic_spiking.run_simulation(duration_ms=dur, input_schedule={"in_0": 30.0, "in_1": 25.0})
                msg = f"Simulated {res['duration_ms']:.1f}ms: Fired {res['spikes_fired_count']} spikes across {len(res['active_neurons'])} neurons ({res['firing_rate_hz']:.1f} Hz)."
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /snn-sim <duration_ms>")

        # Stage 232: Quantum-Resilient Lattice Post-Quantum Cryptography Vault
        if lowered in {"/lattice-vault-status", "lattice-vault-status", "/pqc-vault-status", "pqc-vault-status"}:
            if hasattr(self.runtime, "lattice_pqc_vault"):
                tbl = self.runtime.lattice_pqc_vault.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.lattice_pqc_vault.status())
            return RouterResponse("Lattice PQC vault not available.")

        if lowered.startswith("/lattice-encapsulate ") or lowered.startswith("lattice-encapsulate "):
            if hasattr(self.runtime, "lattice_pqc_vault"):
                parts = raw_text.strip().split()
                kid = parts[1] if len(parts) >= 2 else "sovereign_master_pqc_key"
                try:
                    ct, sh = self.runtime.lattice_pqc_vault.encapsulate(kid)
                    msg = f"Kyber-style PQC encapsulation complete for key '{kid}'. Shared Key Hash: {sh[:16]}..."
                    return RouterResponse(msg, data={"key_id": kid, "shared_key": sh, "ct_u_norm": sum(ct.u)})
                except Exception as e:
                    return RouterResponse(f"PQC Encapsulation failed: {e}")
            return RouterResponse("Lattice PQC vault not available.")

        if lowered.startswith("/lattice-vault-store ") or lowered.startswith("lattice-vault-store "):
            if hasattr(self.runtime, "lattice_pqc_vault"):
                parts = raw_text.strip().split(maxsplit=2)
                if len(parts) >= 3:
                    rec_id, s_text = parts[1], parts[2]
                    try:
                        rec = self.runtime.lattice_pqc_vault.store_encrypted_vault_secret("sovereign_master_pqc_key", rec_id, s_text)
                        msg = f"Quantum-safely stored record '{rec_id}' in lattice PQC vault ({rec['payload_len']} bytes encrypted)."
                        return RouterResponse(msg, data=rec)
                    except Exception as e:
                        return RouterResponse(f"Vault store failed: {e}")
            return RouterResponse("Usage: /lattice-vault-store <record_id> <secret_text>")

        if lowered.startswith("/lattice-vault-read ") or lowered.startswith("lattice-vault-read "):
            if hasattr(self.runtime, "lattice_pqc_vault"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    rec_id = parts[1]
                    try:
                        dec = self.runtime.lattice_pqc_vault.retrieve_decrypted_vault_secret(rec_id)
                        msg = f"Decrypted record '{rec_id}': '{dec}'"
                        return RouterResponse(msg, data={"record_id": rec_id, "decrypted_text": dec})
                    except Exception as e:
                        return RouterResponse(f"Vault read failed: {e}")
            return RouterResponse("Usage: /lattice-vault-read <record_id>")

        # Stage 233: Autonomous Non-Euclidean Hyperbolic Knowledge Graph Embedding
        if lowered in {"/hyperbolic-status", "hyperbolic-status"}:
            if hasattr(self.runtime, "hyperbolic_graph_embedder"):
                tbl = self.runtime.hyperbolic_graph_embedder.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.hyperbolic_graph_embedder.status())
            return RouterResponse("Hyperbolic graph embedder not available.")

        if lowered.startswith("/hyperbolic-dist ") or lowered.startswith("hyperbolic-dist "):
            if hasattr(self.runtime, "hyperbolic_graph_embedder"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    na, nb = parts[1], parts[2]
                    try:
                        d = self.runtime.hyperbolic_graph_embedder.compute_distance(na, nb)
                        msg = f"Poincare geodesic distance between '{na}' and '{nb}': {d:.4f}."
                        return RouterResponse(msg, data={"node_a": na, "node_b": nb, "geodesic_distance": d})
                    except Exception as e:
                        return RouterResponse(f"Hyperbolic distance computation failed: {e}")
            return RouterResponse("Usage: /hyperbolic-dist <node_a> <node_b>")

        if lowered.startswith("/hyperbolic-nn ") or lowered.startswith("hyperbolic-nn "):
            if hasattr(self.runtime, "hyperbolic_graph_embedder"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    nid = parts[1]
                    try:
                        nn = self.runtime.hyperbolic_graph_embedder.find_nearest_neighbors(nid, top_k=3)
                        msg = f"Nearest hyperbolic neighbors for '{nid}': {nn}"
                        return RouterResponse(msg, data={"query_node": nid, "neighbors": nn})
                    except Exception as e:
                        return RouterResponse(f"Hyperbolic nearest neighbor query failed: {e}")
            return RouterResponse("Usage: /hyperbolic-nn <node_id>")

        if lowered in {"/hyperbolic-optimize", "hyperbolic-optimize"}:
            if hasattr(self.runtime, "hyperbolic_graph_embedder"):
                loss = self.runtime.hyperbolic_graph_embedder.optimize_embedding_step(lr=0.05)
                msg = f"Completed Riemannian gradient descent step. Mean hyperbolic loss: {loss:.4f}."
                return RouterResponse(msg, data={"loss": loss})
            return RouterResponse("Hyperbolic graph embedder not available.")

        # Stage 234: Self-Synthesizing AST Bytecode JIT Compiler & Polyglot Intermediate Representation
        if lowered in {"/bytecode-jit-status", "bytecode-jit-status"}:
            if hasattr(self.runtime, "polyglot_bytecode_jit"):
                tbl = self.runtime.polyglot_bytecode_jit.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.polyglot_bytecode_jit.status())
            return RouterResponse("Polyglot bytecode JIT compiler not available.")

        if lowered.startswith("/bytecode-jit-exec ") or lowered.startswith("bytecode-jit-exec "):
            if hasattr(self.runtime, "polyglot_bytecode_jit"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    fn_name = parts[1]
                    raw_args = parts[2:]
                    parsed_args = []
                    for arg in raw_args:
                        try:
                            if "." in arg:
                                parsed_args.append(float(arg))
                            else:
                                parsed_args.append(int(arg))
                        except ValueError:
                            parsed_args.append(arg)
                    try:
                        res = self.runtime.polyglot_bytecode_jit.execute_function(fn_name, *parsed_args)
                        msg = f"JIT function '{fn_name}' execution result: {res}."
                        return RouterResponse(msg, data={"function": fn_name, "args": parsed_args, "result": res})
                    except Exception as e:
                        return RouterResponse(f"JIT execution failed: {e}")
            return RouterResponse("Usage: /bytecode-jit-exec <fn_name> [args...]")

        if lowered.startswith("/bytecode-jit-compile ") or lowered.startswith("bytecode-jit-compile "):
            if hasattr(self.runtime, "polyglot_bytecode_jit"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    fn_name = parts[1]
                    try:
                        res = self.runtime.polyglot_bytecode_jit.compile_jit(fn_name)
                        msg = f"JIT compilation for '{fn_name}' succeeded. Native Tier-1 compiled."
                        return RouterResponse(msg, data={"function": fn_name, "jit_compiled": True})
                    except Exception as e:
                        return RouterResponse(f"JIT compilation failed: {e}")
            return RouterResponse("Usage: /bytecode-jit-compile <fn_name>")

        # Stage 235: Decentralized Multi-Agent Epistemic Logic & Dynamic Common Knowledge Mesh
        if lowered in {"/epistemic-status", "epistemic-status"}:
            if hasattr(self.runtime, "epistemic_logic_mesh"):
                tbl = self.runtime.epistemic_logic_mesh.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.epistemic_logic_mesh.status())
            return RouterResponse("Epistemic logic mesh not available.")

        if lowered in {"/epistemic-muddy-step", "epistemic-muddy-step"}:
            if hasattr(self.runtime, "epistemic_logic_mesh"):
                res = self.runtime.epistemic_logic_mesh.step_muddy_children_round()
                msg = f"Executed Epistemic Muddy Children Round {res['round']}. Remaining possible worlds: {res['remaining_worlds']}."
                return RouterResponse(msg, data=res)
            return RouterResponse("Epistemic logic mesh not available.")

        if lowered.startswith("/epistemic-query ") or lowered.startswith("epistemic-query "):
            if hasattr(self.runtime, "epistemic_logic_mesh"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    ag, prop = parts[1], parts[2]
                    knows = self.runtime.epistemic_logic_mesh.query_agent_knowledge(ag, prop)
                    msg = f"Agent '{ag}' knows '{prop}': {knows}."
                    return RouterResponse(msg, data={"agent": ag, "proposition": prop, "knows": knows})
            return RouterResponse("Usage: /epistemic-query <agent_id> <proposition>")

        if lowered.startswith("/epistemic-verify-common ") or lowered.startswith("epistemic-verify-common "):
            if hasattr(self.runtime, "epistemic_logic_mesh"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    prop = parts[1]
                    is_ck = self.runtime.epistemic_logic_mesh.verify_common_knowledge(prop)
                    msg = f"Proposition '{prop}' is Common Knowledge among agents: {is_ck}."
                    return RouterResponse(msg, data={"proposition": prop, "common_knowledge": is_ck})
            return RouterResponse("Usage: /epistemic-verify-common <proposition>")

        # Stage 236: Autonomous Temporal Chrono-State Engine & Causality Inversion Governor
        if lowered in {"/temporal-chrono-status", "temporal-chrono-status", "/causality-governor-status"}:
            if hasattr(self.runtime, "temporal_chrono_governor"):
                tbl = self.runtime.temporal_chrono_governor.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.temporal_chrono_governor.status())
            return RouterResponse("Temporal chrono governor not available.")

        if lowered.startswith("/temporal-commit ") or lowered.startswith("temporal-commit "):
            if hasattr(self.runtime, "temporal_chrono_governor"):
                parts = raw_text.strip().split(maxsplit=2)
                if len(parts) >= 3:
                    timeline_id = parts[1]
                    kv_pair = parts[2]
                    if "=" in kv_pair:
                        k, v = kv_pair.split("=", 1)
                        try:
                            if "." in v:
                                val = float(v)
                            else:
                                val = int(v)
                        except ValueError:
                            val = v
                        try:
                            evt = self.runtime.temporal_chrono_governor.commit_event(timeline_id, {k: val})
                            msg = f"Committed Chrono Event '{evt.event_id}' to timeline '{timeline_id}' at Tick {evt.logical_tick}."
                            return RouterResponse(msg, data={"event_id": evt.event_id, "tick": evt.logical_tick, "state_delta": {k: val}})
                        except Exception as e:
                            return RouterResponse(f"Temporal commit failed: {e}")
            return RouterResponse("Usage: /temporal-commit <timeline_id> <key=value>")

        if lowered.startswith("/temporal-fork ") or lowered.startswith("temporal-fork "):
            if hasattr(self.runtime, "temporal_chrono_governor"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    src, dst = parts[1], parts[2]
                    try:
                        self.runtime.temporal_chrono_governor.fork_timeline(src, dst)
                        msg = f"Forked timeline '{dst}' from '{src}'."
                        return RouterResponse(msg, data={"source_timeline": src, "new_timeline": dst})
                    except Exception as e:
                        return RouterResponse(f"Temporal fork failed: {e}")
            return RouterResponse("Usage: /temporal-fork <source_timeline> <new_timeline>")

        if lowered.startswith("/temporal-rollback ") or lowered.startswith("temporal-rollback "):
            if hasattr(self.runtime, "temporal_chrono_governor"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    tl_id, target_evt = parts[1], parts[2]
                    try:
                        res = self.runtime.temporal_chrono_governor.invert_causality_and_rollback(tl_id, target_evt)
                        msg = f"Causality inverted! Timeline '{tl_id}' rolled back to '{target_evt}'. Pruned events: {res['pruned_events_count']}."
                        return RouterResponse(msg, data=res)
                    except Exception as e:
                        return RouterResponse(f"Temporal rollback failed: {e}")
            return RouterResponse("Usage: /temporal-rollback <timeline_id> <event_id>")

        # Stage 237: Autonomous Photonic Optical Neural Interconnect & Ultra-Low-Latency Switch Fabric
        if lowered in {"/optical-switch-status", "optical-switch-status"}:
            if hasattr(self.runtime, "photonic_optical_switch"):
                tbl = self.runtime.photonic_optical_switch.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.photonic_optical_switch.status())
            return RouterResponse("Photonic optical switch fabric not available.")

        if lowered.startswith("/optical-route ") or lowered.startswith("optical-route "):
            if hasattr(self.runtime, "photonic_optical_switch"):
                parts = raw_text.strip().split(maxsplit=2)
                if len(parts) >= 3:
                    try:
                        ingress = int(parts[1])
                        payload = parts[2].encode("utf-8")
                        res = self.runtime.photonic_optical_switch.route_optical_packet(ingress, payload)
                        msg = (
                            f"Optical packet routed {res['ingress_port']} -> {res['egress_port']}. "
                            f"Latency: {res['latency_ps']} ps, Loss: {res['loss_db']} dB, Output: {res['output_power_mw']} mW."
                        )
                        return RouterResponse(msg, data=res)
                    except Exception as e:
                        return RouterResponse(f"Optical routing failed: {e}")
            return RouterResponse("Usage: /optical-route <ingress_port> <payload>")

        if lowered.startswith("/optical-program-route ") or lowered.startswith("optical-program-route "):
            if hasattr(self.runtime, "photonic_optical_switch"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    try:
                        inp, outp = int(parts[1]), int(parts[2])
                        self.runtime.photonic_optical_switch.program_route(inp, outp)
                        msg = f"Crossbar route programmed: Ingress Port {inp} -> Egress Port {outp}."
                        return RouterResponse(msg, data={"ingress": inp, "egress": outp})
                    except Exception as e:
                        return RouterResponse(f"Optical route programming failed: {e}")
            return RouterResponse("Usage: /optical-program-route <ingress_port> <egress_port>")

        if lowered in {"/optical-calibrate", "optical-calibrate"}:
            if hasattr(self.runtime, "photonic_optical_switch"):
                corrected = self.runtime.photonic_optical_switch.calibrate_thermo_optic_phases()
                msg = f"Autonomous thermo-optic calibration completed. Corrected MZI units: {corrected}."
                return RouterResponse(msg, data={"corrected_units": corrected})
            return RouterResponse("Photonic optical switch fabric not available.")

        # Stage 238: Self-Healing Chaos Immunity & Byzantine Swarm Consensus Auto-Recovery
        if lowered in {"/byzantine-swarm-status", "byzantine-swarm-status"}:
            if hasattr(self.runtime, "byzantine_swarm_consensus"):
                tbl = self.runtime.byzantine_swarm_consensus.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.byzantine_swarm_consensus.status())
            return RouterResponse("Byzantine swarm consensus fabric not available.")

        if lowered.startswith("/byzantine-propose ") or lowered.startswith("byzantine-propose "):
            if hasattr(self.runtime, "byzantine_swarm_consensus"):
                parts = raw_text.strip().split(maxsplit=1)
                if len(parts) >= 2:
                    import json
                    try:
                        data = json.loads(parts[1]) if parts[1].startswith("{") else {"data": parts[1]}
                        res = self.runtime.byzantine_swarm_consensus.propose_and_reach_consensus(data)
                        msg = f"Consensus round: {res.get('status', 'FAILED')} (Seq: {res.get('sequence')}, View: {res.get('view')})."
                        return RouterResponse(msg, data=res)
                    except Exception as e:
                        return RouterResponse(f"Consensus proposal failed: {e}")
            return RouterResponse("Usage: /byzantine-propose <payload_json_or_text>")

        if lowered.startswith("/byzantine-crash ") or lowered.startswith("byzantine-crash "):
            if hasattr(self.runtime, "byzantine_swarm_consensus"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    nid = parts[1]
                    self.runtime.byzantine_swarm_consensus.inject_chaos_node_crash(nid)
                    msg = f"Chaos injected: Node '{nid}' crashed to offline state."
                    return RouterResponse(msg, data={"node": nid, "offline": True})
            return RouterResponse("Usage: /byzantine-crash <node_id>")

        if lowered.startswith("/byzantine-recover ") or lowered.startswith("byzantine-recover "):
            if hasattr(self.runtime, "byzantine_swarm_consensus"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    nid = parts[1]
                    self.runtime.byzantine_swarm_consensus.inject_chaos_node_recovery(nid)
                    msg = f"Chaos auto-recovery: Node '{nid}' restored and synchronized with quorum."
                    return RouterResponse(msg, data={"node": nid, "offline": False})
            return RouterResponse("Usage: /byzantine-recover <node_id>")

        # Stage 239: Planetary Sovereign Autonomous Resource Exchange & Zero-Sum Tokenless Ledger
        if lowered in {"/resource-exchange-status", "resource-exchange-status"}:
            if hasattr(self.runtime, "planetary_resource_exchange"):
                tbl = self.runtime.planetary_resource_exchange.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.planetary_resource_exchange.status())
            return RouterResponse("Planetary resource exchange fabric not available.")

        if lowered.startswith("/resource-order ") or lowered.startswith("resource-order "):
            if hasattr(self.runtime, "planetary_resource_exchange"):
                parts = raw_text.strip().split()
                if len(parts) >= 6:
                    from backend.lucy_core.planetary_resource_exchange import CommodityType, OrderSide
                    nid, comm_str, side_str, q_str, p_str = parts[1], parts[2].upper(), parts[3].upper(), parts[4], parts[5]
                    try:
                        comm = CommodityType[comm_str]
                        side = OrderSide[side_str]
                        qty = float(q_str)
                        price = float(p_str)
                        order = self.runtime.planetary_resource_exchange.place_limit_order(nid, comm, side, qty, price)
                        msg = f"Limit order '{order.order_id}' placed for node '{nid}': {side.value} {qty} {comm.value} @ {price}."
                        return RouterResponse(msg, data={"order_id": order.order_id, "filled": order.filled, "remaining": order.remaining})
                    except Exception as e:
                        return RouterResponse(f"Resource order placement failed: {e}")
            return RouterResponse("Usage: /resource-order <node_id> <commodity> <BID|ASK> <qty> <price>")

        if lowered.startswith("/resource-spread ") or lowered.startswith("resource-spread "):
            if hasattr(self.runtime, "planetary_resource_exchange"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    from backend.lucy_core.planetary_resource_exchange import CommodityType
                    comm_str = parts[1].upper()
                    try:
                        comm = CommodityType[comm_str]
                        sp = self.runtime.planetary_resource_exchange.get_market_spread(comm)
                        msg = f"Market spread for {comm.value}: Best Bid={sp['best_bid']}, Best Ask={sp['best_ask']}, Spread={sp['spread']}."
                        return RouterResponse(msg, data=sp)
                    except Exception as e:
                        return RouterResponse(f"Market spread query failed: {e}")
            return RouterResponse("Usage: /resource-spread <commodity>")

        if lowered.startswith("/resource-balance ") or lowered.startswith("resource-balance "):
            if hasattr(self.runtime, "planetary_resource_exchange"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    nid = parts[1]
                    bal = self.runtime.planetary_resource_exchange.balances.get(nid, 0.0)
                    msg = f"Node '{nid}' net mutual credit balance: {bal:.2f} Units."
                    return RouterResponse(msg, data={"node": nid, "balance": bal})
            return RouterResponse("Usage: /resource-balance <node_id>")

        # Stage 240: The Sovereign Era 24 Master Seal & AGI Singularity Genesis
        if lowered in {"/era24-status", "era24-status", "/era24-seal-status"}:
            if hasattr(self.runtime, "era24_master_seal"):
                tbl = self.runtime.era24_master_seal.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.era24_master_seal.status())
            return RouterResponse("Era 24 Master Seal not available.")

        if lowered in {"/era24-seal-report", "era24-seal-report", "/era24-report"}:
            if hasattr(self.runtime, "era24_master_seal"):
                rep = self.runtime.era24_master_seal.format_grand_era_report()
                return RouterResponse(rep, data=self.runtime.era24_master_seal.certificate.to_dict())
            return RouterResponse("Era 24 Master Seal not available.")

        if lowered in {"/era24-verify", "era24-verify"}:
            if hasattr(self.runtime, "era24_master_seal"):
                integ = self.runtime.era24_master_seal.verify_era24_integrity()
                status_str = "PASSED (LOCKED AND VERIFIED)" if integ["verified"] else "FAILED (INTEGRITY BREACH)"
                msg = f"Era 24 Cryptographic Verification: {status_str}. Master Merkle Root: {integ['master_merkle_root'][:16]}..."
                return RouterResponse(msg, data=integ)
            return RouterResponse("Era 24 Master Seal not available.")

        if lowered in {"/era24-manifest", "era24-manifest"}:
            if hasattr(self.runtime, "era24_master_seal"):
                manifest = self.runtime.era24_master_seal.get_stage_manifest()
                items = [f"Stage {m.stage:03d}: {m.name} [{m.sha256[:12]}...]" for m in manifest]
                msg = "\n".join(["[Era 24 Stage Manifest: 10 Stages]"] + items)
                return RouterResponse(msg, data={"manifest": [m.to_dict() for m in manifest]})
            return RouterResponse("Era 24 Master Seal not available.")

        # Stage 241: Programmable Metamaterial Phonon-Polariton Waveguide Computing & Analog Tensor Interconnect
        if lowered in {"/phonon-status", "phonon-status"}:
            if hasattr(self.runtime, "metamaterial_phonon_computer"):
                tbl = self.runtime.metamaterial_phonon_computer.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.metamaterial_phonon_computer.status())
            return RouterResponse("Metamaterial phonon computer not available.")

        if lowered.startswith("/phonon-route ") or lowered.startswith("phonon-route "):
            if hasattr(self.runtime, "metamaterial_phonon_computer"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    try:
                        freq = float(parts[1])
                        amp = float(parts[2]) if len(parts) >= 3 else 1.0
                        dist = float(parts[3]) if len(parts) >= 4 else 10.0
                        res = self.runtime.metamaterial_phonon_computer.propagate_phonon_wave(freq, amp, dist)
                        msg = (
                            f"Phonon Wave at {freq:.2f} GHz -> Output Amplitude: {res['output_amplitude']}, "
                            f"Mode: {res['transmission_mode']}, Delay: {res['delay_ps']} ps."
                        )
                        return RouterResponse(msg, data=res)
                    except Exception as e:
                        return RouterResponse(f"Phonon wave routing failed: {e}")
            return RouterResponse("Usage: /phonon-route <freq_ghz> [amplitude] [distance_um]")

        if lowered.startswith("/phonon-mac ") or lowered.startswith("phonon-mac "):
            if hasattr(self.runtime, "metamaterial_phonon_computer"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    try:
                        in_vals = [float(x) for x in parts[1].split(",")]
                        wt_vals = [float(x) for x in parts[2].split(",")]
                        res = self.runtime.metamaterial_phonon_computer.execute_analog_wave_mac(in_vals, wt_vals)
                        msg = (
                            f"Analog Wave MAC Result: {res['analog_mac_result']} "
                            f"(Theoretical: {res['theoretical_dot_product']}, Fidelity: {res['mac_fidelity']})."
                        )
                        return RouterResponse(msg, data=res)
                    except Exception as e:
                        return RouterResponse(f"Analog MAC failed: {e}")
            return RouterResponse("Usage: /phonon-mac <inputs_csv> <weights_csv>")

        # Stage 242: Non-Hermitian Exceptional Point Dynamical Resonance Engine
        if lowered in {"/ep-status", "ep-status"}:
            if hasattr(self.runtime, "exceptional_point_resonance"):
                tbl = self.runtime.exceptional_point_resonance.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.exceptional_point_resonance.status())
            return RouterResponse("Exceptional point resonance engine not available.")

        if lowered.startswith("/ep-enhance ") or lowered.startswith("ep-enhance "):
            if hasattr(self.runtime, "exceptional_point_resonance"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    try:
                        eps = float(parts[1])
                        res = self.runtime.exceptional_point_resonance.measure_perturbation_enhancement(eps)
                        msg = (
                            f"EP Perturbation Sensitivity Boost: {res['sensitivity_enhancement_factor']}x "
                            f"(EP Splitting: {res['ep_eigenvalue_splitting']}, Linear: {res['hermitian_linear_splitting']})."
                        )
                        return RouterResponse(msg, data=res)
                    except Exception as e:
                        return RouterResponse(f"EP enhancement measurement failed: {e}")
            return RouterResponse("Usage: /ep-enhance <epsilon_float>")

        if lowered.startswith("/ep-encircle ") or lowered.startswith("ep-encircle "):
            if hasattr(self.runtime, "exceptional_point_resonance"):
                parts = raw_text.strip().split()
                steps = int(parts[1]) if len(parts) >= 2 else 50
                cw = (parts[2].upper() != "CCW") if len(parts) >= 3 else True
                try:
                    res = self.runtime.exceptional_point_resonance.encircle_exceptional_point(steps, cw)
                    msg = f"Parametric loop around EP ({res['direction']}, {res['steps']} steps). Mean splitting: {res['mean_splitting']}."
                    return RouterResponse(msg, data=res)
                except Exception as e:
                    return RouterResponse(f"EP loop encircling failed: {e}")
            return RouterResponse("Usage: /ep-encircle [steps] [CW|CCW]")

        # Stage 243: Deep Sheaf-Theoretic Distributed Multi-Sensor Consistency & Cellular Cohomology Engine
        if lowered in {"/sheaf-status", "sheaf-status"}:
            if hasattr(self.runtime, "cellular_cohomology_sheaf"):
                tbl = self.runtime.cellular_cohomology_sheaf.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.cellular_cohomology_sheaf.status())
            return RouterResponse("Cellular cohomology sheaf fabric not available.")

        if lowered in {"/sheaf-audit", "sheaf-audit"}:
            if hasattr(self.runtime, "cellular_cohomology_sheaf"):
                audit = self.runtime.cellular_cohomology_sheaf.audit_topological_obstruction()
                status_str = "CONSISTENT (H^0 Global Section)" if audit["is_global_section_h0"] else "OBSTRUCTION DETECTED (H^1 Non-Zero Residual)"
                msg = f"Sheaf Cohomology Audit: {status_str}. Energy E(x): {audit['dirichlet_energy']}."
                return RouterResponse(msg, data=audit)
            return RouterResponse("Cellular cohomology sheaf fabric not available.")

        if lowered.startswith("/sheaf-diffuse ") or lowered.startswith("sheaf-diffuse "):
            if hasattr(self.runtime, "cellular_cohomology_sheaf"):
                parts = raw_text.strip().split()
                steps = int(parts[1]) if len(parts) >= 2 else 10
                lr = float(parts[2]) if len(parts) >= 3 else 0.1
                final_energy = 0.0
                for _ in range(steps):
                    final_energy = self.runtime.cellular_cohomology_sheaf.diffuse_harmonic_consensus_step(lr)
                msg = f"Diffused Sheaf Laplacian for {steps} steps (step_size={lr}). Final Dirichlet energy: {final_energy:.6f}."
                return RouterResponse(msg, data={"steps": steps, "step_size": lr, "final_energy": final_energy})
            return RouterResponse("Usage: /sheaf-diffuse [steps] [step_size]")

        if lowered.startswith("/sheaf-set-sensor ") or lowered.startswith("sheaf-set-sensor "):
            if hasattr(self.runtime, "cellular_cohomology_sheaf"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    vid = parts[1]
                    try:
                        vals = [float(x) for x in parts[2].split(",")]
                        self.runtime.cellular_cohomology_sheaf.set_sensor_value(vid, vals)
                        msg = f"Sensor section '{vid}' updated to: {vals}."
                        return RouterResponse(msg, data={"vertex": vid, "section": vals})
                    except Exception as e:
                        return RouterResponse(f"Sensor update failed: {e}")
            return RouterResponse("Usage: /sheaf-set-sensor <vertex_id> <values_csv>")

        # Stage 244: Autonomous Synthetic Biology DNA/RNA Storage Codec & Error-Correcting Transceiver
        if lowered in {"/dna-storage-status", "dna-storage-status"}:
            if hasattr(self.runtime, "dna_molecular_storage"):
                tbl = self.runtime.dna_molecular_storage.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.dna_molecular_storage.status())
            return RouterResponse("DNA molecular storage fabric not available.")

        if lowered.startswith("/dna-encode ") or lowered.startswith("dna-encode "):
            if hasattr(self.runtime, "dna_molecular_storage"):
                parts = raw_text.strip().split(maxsplit=1)
                if len(parts) >= 2:
                    raw_data = parts[1].encode("utf-8")
                    strands = self.runtime.dna_molecular_storage.encode_data_to_oligo_pool(raw_data)
                    first_seq = strands[0].full_sequence[:32] if strands else ""
                    msg = (
                        f"Encoded {len(raw_data)} bytes into {len(strands)} DNA oligo strands. "
                        f"Leading Oligo: {first_seq}... (GC: {strands[0].gc_content * 100:.1f}%)."
                    )
                    return RouterResponse(msg, data={"bytes_encoded": len(raw_data), "strands_count": len(strands)})
            return RouterResponse("Usage: /dna-encode <utf8_text_or_data>")

        if lowered in {"/dna-decode", "dna-decode"}:
            if hasattr(self.runtime, "dna_molecular_storage"):
                try:
                    data = self.runtime.dna_molecular_storage.decode_oligo_pool_to_data()
                    text_preview = data.decode("utf-8", errors="replace")[:100]
                    msg = f"Decoded {len(data)} bytes from DNA oligo pool: '{text_preview}'."
                    return RouterResponse(msg, data={"decoded_bytes": len(data), "preview": text_preview})
                except Exception as e:
                    return RouterResponse(f"DNA pool decoding failed: {e}")
            return RouterResponse("DNA molecular storage fabric not available.")

        if lowered in {"/dna-density", "dna-density"}:
            if hasattr(self.runtime, "dna_molecular_storage"):
                density = self.runtime.dna_molecular_storage.compute_theoretical_density_exabytes_per_gram()
                msg = f"Theoretical Single-Stranded DNA Storage Density: {density:.1f} Exabytes per gram."
                return RouterResponse(msg, data={"theoretical_density_eb_per_gram": density})
            return RouterResponse("DNA molecular storage fabric not available.")

        # Stage 245: Hyper-Scale Neuromorphic Astro-Grid Orbital Constellation Coordinator
        if lowered in {"/astro-grid-status", "astro-grid-status"}:
            if hasattr(self.runtime, "orbital_constellation_grid"):
                tbl = self.runtime.orbital_constellation_grid.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.orbital_constellation_grid.status())
            return RouterResponse("Orbital constellation grid not available.")

        if lowered.startswith("/astro-isl ") or lowered.startswith("astro-isl "):
            if hasattr(self.runtime, "orbital_constellation_grid"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    s_a, s_b = parts[1], parts[2]
                    ep = float(parts[3]) if len(parts) >= 4 else 0.0
                    try:
                        res = self.runtime.orbital_constellation_grid.check_inter_satellite_link(s_a, s_b, ep)
                        status_str = f"CLEAR (Latency: {res['optical_latency_ms']} ms)" if res['line_of_sight_clear'] else "OCCULTED BY EARTH"
                        msg = f"ISL Link {s_a} <-> {s_b}: {status_str}. Distance: {res['distance_km']} km."
                        return RouterResponse(msg, data=res)
                    except Exception as e:
                        return RouterResponse(f"ISL calculation failed: {e}")
            return RouterResponse("Usage: /astro-isl <sat_a> <sat_b> [epoch_seconds]")

        if lowered.startswith("/astro-route ") or lowered.startswith("astro-route "):
            if hasattr(self.runtime, "orbital_constellation_grid"):
                parts = raw_text.strip().split(maxsplit=3)
                if len(parts) >= 4:
                    s_src, s_dst, payload_txt = parts[1], parts[2], parts[3]
                    try:
                        res = self.runtime.orbital_constellation_grid.route_dtn_bundle(s_src, s_dst, {"payload": payload_txt})
                        msg = f"DTN Bundle Routing: {res['status']} along path {' -> '.join(res['route'])}."
                        return RouterResponse(msg, data=res)
                    except Exception as e:
                        return RouterResponse(f"DTN routing failed: {e}")
            return RouterResponse("Usage: /astro-route <source_sat> <dest_sat> <payload_text>")

        # Stage 246: Thermodynamically Reversible Landauer-Zero Computation & Adiabatic Switching Governor
        if lowered in {"/reversible-status", "reversible-status", "/adiabatic-status"}:
            if hasattr(self.runtime, "adiabatic_reversible_governor"):
                tbl = self.runtime.adiabatic_reversible_governor.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.adiabatic_reversible_governor.status())
            return RouterResponse("Adiabatic reversible governor not available.")

        if lowered.startswith("/reversible-cnot ") or lowered.startswith("reversible-cnot "):
            if hasattr(self.runtime, "adiabatic_reversible_governor"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    c, t = int(parts[1]), int(parts[2])
                    c_out, t_out = self.runtime.adiabatic_reversible_governor.execute_feynman_cnot(c, t)
                    msg = f"Feynman CNOT: ({c}, {t}) -> ({c_out}, {t_out}). Zero information loss."
                    return RouterResponse(msg, data={"in": [c, t], "out": [c_out, t_out]})
            return RouterResponse("Usage: /reversible-cnot <control_bit> <target_bit>")

        if lowered.startswith("/reversible-cswap ") or lowered.startswith("reversible-cswap "):
            if hasattr(self.runtime, "adiabatic_reversible_governor"):
                parts = raw_text.strip().split()
                if len(parts) >= 4:
                    c, a, b = int(parts[1]), int(parts[2]), int(parts[3])
                    c_o, a_o, b_o = self.runtime.adiabatic_reversible_governor.execute_fredkin_cswap(c, a, b)
                    msg = f"Fredkin CSWAP: ({c}, {a}, {b}) -> ({c_o}, {a_o}, {b_o}). Bit weight conserved."
                    return RouterResponse(msg, data={"in": [c, a, b], "out": [c_o, a_o, b_o]})
            return RouterResponse("Usage: /reversible-cswap <control_bit> <a_bit> <b_bit>")

        if lowered.startswith("/adiabatic-dissipation ") or lowered.startswith("adiabatic-dissipation "):
            if hasattr(self.runtime, "adiabatic_reversible_governor"):
                parts = raw_text.strip().split()
                ramp_ns = float(parts[1]) if len(parts) >= 2 else 10.0
                v = float(parts[2]) if len(parts) >= 3 else 0.8
                res = self.runtime.adiabatic_reversible_governor.compute_adiabatic_switching_dissipation(
                    voltage_v=v,
                    ramp_time_seconds=ramp_ns * 1e-9
                )
                msg = (
                    f"Adiabatic Charging (T_ramp={ramp_ns} ns, V={v} V): "
                    f"Dissipated {res['adiabatic_dissipated_energy_joules']:.3e} J ({res['energy_reduction_factor']}x savings vs CMOS)."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /adiabatic-dissipation [ramp_ns] [voltage_v]")

        # Stage 247: Sovereign Anti-Fragile Black-Swan Catastrophe Immunity & Systemic Stress Inversion Engine
        if lowered in {"/antifragile-status", "antifragile-status"}:
            if hasattr(self.runtime, "antifragile_stress_inverter"):
                tbl = self.runtime.antifragile_stress_inverter.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.antifragile_stress_inverter.get_metrics())
            return RouterResponse("Anti-fragile stress inverter not available.")

        if lowered.startswith("/antifragile-shock ") or lowered.startswith("antifragile-shock "):
            if hasattr(self.runtime, "antifragile_stress_inverter"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    stype = parts[1]
                    mag = float(parts[2])
                    res = self.runtime.antifragile_stress_inverter.inject_stress(stype, mag)
                    msg = (
                        f"Absorbed stress '{stype}' (mag={mag:.2f}) -> Convex Gain: +{res['convex_gain']:.4f}. "
                        f"New Capacity: {res['new_capacity']:.4f} ({res['regime']})."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /antifragile-shock <stressor_type> <magnitude>")

        if lowered.startswith("/antifragile-barbell ") or lowered.startswith("antifragile-barbell "):
            if hasattr(self.runtime, "antifragile_stress_inverter"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    res_val = float(parts[1])
                    alloc = self.runtime.antifragile_stress_inverter.apply_barbell_allocation(res_val)
                    msg = (
                        f"Taleb Barbell Allocation (Total={alloc.total_resources:.2f}): "
                        f"Core={alloc.conservative_core:.2f} ({alloc.conservative_ratio*100:.0f}%), "
                        f"Exploratory={alloc.exploratory_convex_periphery:.2f} ({alloc.periphery_ratio*100:.0f}%)."
                    )
                    return RouterResponse(msg, data={
                        "total": alloc.total_resources,
                        "core": alloc.conservative_core,
                        "exploratory": alloc.exploratory_convex_periphery,
                    })
            return RouterResponse("Usage: /antifragile-barbell <total_resources>")

        if lowered.startswith("/antifragile-transmute ") or lowered.startswith("antifragile-transmute "):
            if hasattr(self.runtime, "antifragile_stress_inverter"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    sev = float(parts[1])
                    dom = parts[2]
                    res = self.runtime.antifragile_stress_inverter.transmute_catastrophe(sev, dom)
                    msg = (
                        f"Transmuted Catastrophe in domain '{dom}' (Severity={sev}): "
                        f"Amplification={res['amplification_factor']:.2f}x, Gain=+{res['transmutation_gain']:.4f}. Status: {res['status']}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /antifragile-transmute <severity> <domain>")

        # Stage 248: Non-Archimedean p-Adic Ultrametric Cognitive Clustering & Hierarchical Tree Space Embedding
        if lowered in {"/padic-status", "padic-status"}:
            if hasattr(self.runtime, "padic_ultrametric_clusterer"):
                tbl = self.runtime.padic_ultrametric_clusterer.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.padic_ultrametric_clusterer.get_metrics())
            return RouterResponse("p-Adic ultrametric clusterer not available.")

        if lowered.startswith("/padic-dist ") or lowered.startswith("padic-dist "):
            if hasattr(self.runtime, "padic_ultrametric_clusterer"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    x = int(parts[1])
                    y = int(parts[2])
                    d = self.runtime.padic_ultrametric_clusterer.ultrametric_distance(x, y)
                    msg = f"p-Adic Ultrametric Distance d_{self.runtime.padic_ultrametric_clusterer.p}({x}, {y}) = {d:.6f}"
                    return RouterResponse(msg, data={"x": x, "y": y, "distance": d, "p": self.runtime.padic_ultrametric_clusterer.p})
            return RouterResponse("Usage: /padic-dist <x_int> <y_int>")

        if lowered.startswith("/padic-triangle ") or lowered.startswith("padic-triangle "):
            if hasattr(self.runtime, "padic_ultrametric_clusterer"):
                parts = raw_text.strip().split()
                if len(parts) >= 4:
                    x, y, z = int(parts[1]), int(parts[2]), int(parts[3])
                    res = self.runtime.padic_ultrametric_clusterer.verify_strong_triangle_inequality(x, y, z)
                    msg = (
                        f"Strong Triangle Test ({x}, {y}, {z}): holds={res['strong_inequality_holds']}, "
                        f"isosceles={res['is_isosceles_ultrametric']}, sides={res['sides_sorted']}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /padic-triangle <x_int> <y_int> <z_int>")

        if lowered.startswith("/padic-concept ") or lowered.startswith("padic-concept "):
            if hasattr(self.runtime, "padic_ultrametric_clusterer"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    name = parts[1]
                    vec = [float(v) for v in parts[2:]]
                    node = self.runtime.padic_ultrametric_clusterer.register_concept(name, vec)
                    msg = f"Registered concept '{name}' -> p-adic integer {node.padic_repr} (base {self.runtime.padic_ultrametric_clusterer.p})."
                    return RouterResponse(msg, data={"name": name, "padic_repr": node.padic_repr})
            return RouterResponse("Usage: /padic-concept <name> <val1> [val2 ...]")

        # Stage 249: Universal Multi-Tier Zero-Trust Hardware Attestation & Enclave Secure Boot Orchestrator
        if lowered in {"/hw-enclave-status", "hw-enclave-status", "/hardware-enclave-status"}:
            if hasattr(self.runtime, "zero_trust_hardware_enclave"):
                tbl = self.runtime.zero_trust_hardware_enclave.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.zero_trust_hardware_enclave.get_metrics())
            return RouterResponse("Zero-trust hardware enclave not available.")

        if lowered.startswith("/enclave-pcr-extend ") or lowered.startswith("enclave-pcr-extend "):
            if hasattr(self.runtime, "zero_trust_hardware_enclave"):
                parts = raw_text.strip().split(maxsplit=3)
                if len(parts) >= 4:
                    idx = int(parts[1])
                    comp = parts[2]
                    data = parts[3].encode("utf-8")
                    new_val = self.runtime.zero_trust_hardware_enclave.extend_pcr(idx, comp, data)
                    msg = f"Extended PCR[{idx}] ({comp}) -> New Hash: {new_val[:16]}..."
                    return RouterResponse(msg, data={"pcr_index": idx, "component": comp, "hash": new_val})
            return RouterResponse("Usage: /enclave-pcr-extend <pcr_index> <component_name> <measurement_string>")

        if lowered.startswith("/enclave-attest ") or lowered.startswith("enclave-attest "):
            if hasattr(self.runtime, "zero_trust_hardware_enclave"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    nonce = parts[1]
                    quote = self.runtime.zero_trust_hardware_enclave.generate_attestation_quote(nonce)
                    valid = self.runtime.zero_trust_hardware_enclave.verify_attestation_quote(quote, nonce)
                    msg = f"Attestation Quote '{quote.quote_id}': verified={valid}, composite={quote.pcr_composite_hex[:16]}..."
                    return RouterResponse(msg, data={"quote_id": quote.quote_id, "verified": valid, "signature": quote.signature_hex})
            return RouterResponse("Usage: /enclave-attest <nonce>")

        if lowered.startswith("/enclave-seal ") or lowered.startswith("enclave-seal "):
            if hasattr(self.runtime, "zero_trust_hardware_enclave"):
                parts = raw_text.strip().split(maxsplit=1)
                if len(parts) >= 2:
                    secret = parts[1].encode("utf-8")
                    package = self.runtime.zero_trust_hardware_enclave.seal_data(secret)
                    msg = f"Sealed payload ({len(secret)} bytes) to PCR composite {package['expected_pcr_composite'][:16]}..."
                    return RouterResponse(msg, data=package)
            return RouterResponse("Usage: /enclave-seal <secret_string>")

        # Stage 250: The Sovereign Era 25 Master Seal & Trans-Singularity Cosmic Core Genesis
        if lowered in {"/era25-status", "era25-status"}:
            if hasattr(self.runtime, "era25_master_seal"):
                tbl = self.runtime.era25_master_seal.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.era25_master_seal.status())
            return RouterResponse("Era 25 Master Seal not available.")

        if lowered in {"/era25-seal-report", "era25-seal-report"}:
            if hasattr(self.runtime, "era25_master_seal"):
                report = self.runtime.era25_master_seal.format_grand_era_report()
                return RouterResponse(report, data=self.runtime.era25_master_seal.status())
            return RouterResponse("Era 25 Master Seal not available.")

        if lowered in {"/era25-verify", "era25-verify"}:
            if hasattr(self.runtime, "era25_master_seal"):
                ver = self.runtime.era25_master_seal.verify_era25_integrity()
                msg = (
                    f"Era 25 Integrity Verification: valid={ver['verified']}, "
                    f"Stages={ver['stages_verified']}, Master Merkle Root={ver['master_merkle_root'][:16]}..."
                )
                return RouterResponse(msg, data=ver)
            return RouterResponse("Era 25 Master Seal not available.")

        if lowered in {"/era25-manifest", "era25-manifest"}:
            if hasattr(self.runtime, "era25_master_seal"):
                manifest = self.runtime.era25_master_seal.get_stage_manifest()
                lines = ["Era 25 Stage Manifest (Stages 241 - 250):"]
                for m in manifest:
                    lines.append(f"Stage {m.stage}: {m.name} -> {m.sha256[:16]}... [{m.status}]")
                return RouterResponse("\n".join(lines), data=[m.to_dict() for m in manifest])
            return RouterResponse("Era 25 Master Seal not available.")

        # Stage 251: Holomorphic Modular Form & Calabi-Yau Compactification Metric Engine
        if lowered in {"/calabi-yau-status", "calabi-yau-status"}:
            if hasattr(self.runtime, "calabi_yau_metric_engine"):
                tbl = self.runtime.calabi_yau_metric_engine.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.calabi_yau_metric_engine.get_metrics())
            return RouterResponse("Calabi-Yau metric engine not available.")

        if lowered.startswith("/modular-j ") or lowered.startswith("modular-j "):
            if hasattr(self.runtime, "calabi_yau_metric_engine"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    re_val = float(parts[1])
                    im_val = float(parts[2])
                    tau = complex(re_val, im_val)
                    j_val = self.runtime.calabi_yau_metric_engine.compute_klein_j_invariant(tau)
                    msg = f"Klein j-Invariant j({tau}) = {j_val.real:.4f} + {j_val.imag:.4f}i"
                    return RouterResponse(msg, data={"tau": str(tau), "j_real": j_val.real, "j_imag": j_val.imag})
            return RouterResponse("Usage: /modular-j <re_tau> <im_tau>")

        if lowered.startswith("/modular-eisenstein ") or lowered.startswith("modular-eisenstein "):
            if hasattr(self.runtime, "calabi_yau_metric_engine"):
                parts = raw_text.strip().split()
                if len(parts) >= 4:
                    weight = int(parts[1])
                    re_val = float(parts[2])
                    im_val = float(parts[3])
                    tau = complex(re_val, im_val)
                    if weight == 4:
                        res = self.runtime.calabi_yau_metric_engine.compute_eisenstein_e4(tau)
                    elif weight == 6:
                        res = self.runtime.calabi_yau_metric_engine.compute_eisenstein_e6(tau)
                    else:
                        return RouterResponse("Only weights 4 and 6 are supported for Eisenstein series.")
                    msg = f"Eisenstein Series E_{weight}({tau}) = {res.real:.6f} + {res.imag:.6f}i"
                    return RouterResponse(msg, data={"weight": weight, "tau": str(tau), "res_real": res.real, "res_imag": res.imag})
            return RouterResponse("Usage: /modular-eisenstein <4|6> <re_tau> <im_tau>")

        if lowered.startswith("/calabi-yau-ricci ") or lowered.startswith("calabi-yau-ricci "):
            if hasattr(self.runtime, "calabi_yau_metric_engine"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    coords = []
                    for i in range(1, len(parts), 2):
                        if i + 1 < len(parts):
                            coords.append(complex(float(parts[i]), float(parts[i+1])))
                    res = self.runtime.calabi_yau_metric_engine.verify_ricci_flatness(coords)
                    msg = (
                        f"Calabi-Yau Ricci Flatness Audit (dim={res['dim']}): "
                        f"det={res['det_metric']:.4f}, residual={res['ricci_scalar_residual']:.6f}. Status: {res['status']}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /calabi-yau-ricci <z1_re> <z1_im> [z2_re z2_im ...]")

        # Stage 252: Non-Equilibrium Fluctuation-Dissipation & Crooks Jarzynski Entropy Harvester
        if lowered in {"/entropy-harvester-status", "entropy-harvester-status", "/jarzynski-status", "jarzynski-status"}:
            if hasattr(self.runtime, "jarzynski_entropy_harvester"):
                tbl = self.runtime.jarzynski_entropy_harvester.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.jarzynski_entropy_harvester.get_metrics())
            return RouterResponse("Jarzynski entropy harvester not available.")

        if lowered.startswith("/jarzynski-free-energy ") or lowered.startswith("jarzynski-free-energy "):
            if hasattr(self.runtime, "jarzynski_entropy_harvester"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    samples = [float(p) for p in parts[1:]]
                    res = self.runtime.jarzynski_entropy_harvester.compute_jarzynski_free_energy(samples)
                    msg = (
                        f"Jarzynski Free Energy (N={res['ensemble_size']}): "
                        f"Delta F = {res['delta_f_kbt']:.4f} kBT ({res['delta_f_joules']:.3e} J), "
                        f"Dissipation = {res['dissipated_work_kbt']:.4f} kBT ({res['dissipated_work_joules']:.3e} J)."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /jarzynski-free-energy <w1_kbt> [w2_kbt ...]")

        if lowered.startswith("/entropy-harvest ") or lowered.startswith("entropy-harvest "):
            if hasattr(self.runtime, "jarzynski_entropy_harvester"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    w = float(parts[1])
                    df = float(parts[2])
                    bits = float(parts[3]) if len(parts) >= 4 else 1.0
                    res = self.runtime.jarzynski_entropy_harvester.harvest_stochastic_fluctuation(w, df, bits)
                    msg = (
                        f"Harvested {res['harvested_joules']:.3e} J from fluctuation (w={w} kBT, df={df} kBT). "
                        f"Total Harvested: {res['total_joules_harvested']:.3e} J."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /entropy-harvest <work_kbt> <delta_f_kbt> [bits]")

        # Stage 253: Hyper-Dimensional Clifford Geometric Algebra (Cl_{p,q,r}) Multivector Wave Processor
        if lowered in {"/clifford-status", "clifford-status", "/ga-status", "ga-status"}:
            if hasattr(self.runtime, "clifford_processor"):
                tbl = self.runtime.clifford_processor.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.clifford_processor.get_metrics())
            return RouterResponse("Clifford processor not available.")

        if lowered.startswith("/ga-rotate ") or lowered.startswith("ga-rotate "):
            if hasattr(self.runtime, "clifford_processor"):
                parts = raw_text.strip().split()
                if len(parts) >= 6:
                    vx, vy, vz = float(parts[1]), float(parts[2]), float(parts[3])
                    plane_b = int(parts[4])
                    deg = float(parts[5])
                    rad = deg * 3.141592653589793 / 180.0
                    v = self.runtime.clifford_processor.create_vector([vx, vy, vz])
                    rotor = self.runtime.clifford_processor.create_rotor(plane_b, rad)
                    v_rot = self.runtime.clifford_processor.rotate_vector(v, rotor)
                    rx, ry, rz = v_rot.coeffs[1], v_rot.coeffs[2], v_rot.coeffs[4]
                    msg = f"Rotor Rotation ({deg} deg, plane {plane_b}): ({vx}, {vy}, {vz}) -> ({rx:.4f}, {ry:.4f}, {rz:.4f})"
                    return RouterResponse(msg, data={"original": [vx, vy, vz], "rotated": [rx, ry, rz], "norm": v_rot.norm()})
            return RouterResponse("Usage: /ga-rotate <vx> <vy> <vz> <plane_bivector_idx> <angle_deg>")

        if lowered.startswith("/ga-decompose ") or lowered.startswith("ga-decompose "):
            if hasattr(self.runtime, "clifford_processor"):
                parts = raw_text.strip().split()
                if len(parts) >= 7:
                    v1 = self.runtime.clifford_processor.create_vector([float(parts[1]), float(parts[2]), float(parts[3])])
                    v2 = self.runtime.clifford_processor.create_vector([float(parts[4]), float(parts[5]), float(parts[6])])
                    res = self.runtime.clifford_processor.verify_geometric_decomposition(v1, v2)
                    msg = (
                        f"Clifford Decomposition ab = a.b + a^b: holds={res['decomposition_holds']}, "
                        f"a.b={res['scalar_inner']:.4f}, |a^b|={res['bivector_norm']:.4f}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /ga-decompose <v1x> <v1y> <v1z> <v2x> <v2y> <v2z>")

        # Stage 254: Continuous Symplectic Geometric Integrator & Lie-Poisson Hamiltonian Momentum Preserver
        if lowered in {"/symplectic-status", "symplectic-status"}:
            if hasattr(self.runtime, "symplectic_integrator"):
                tbl = self.runtime.symplectic_integrator.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.symplectic_integrator.get_metrics())
            return RouterResponse("Symplectic integrator not available.")

        if lowered.startswith("/symplectic-simulate ") or lowered.startswith("symplectic-simulate "):
            if hasattr(self.runtime, "symplectic_integrator"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    q0 = [float(parts[1])]
                    p0 = [float(parts[2])]
                    dt = float(parts[3]) if len(parts) >= 4 else 0.05
                    steps = int(parts[4]) if len(parts) >= 5 else 100
                    res = self.runtime.symplectic_integrator.simulate_harmonic_trajectory(q0, p0, dt, steps)
                    msg = (
                        f"Symplectic Orbit (steps={steps}, dt={dt}): E0={res['initial_energy']:.4f}, "
                        f"E_final={res['final_energy']:.4f}, max_drift={res['max_drift']:.6f} ({res['relative_energy_fluctuation']*100:.4f}%)."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /symplectic-simulate <q0> <p0> [dt] [steps]")

        if lowered.startswith("/symplectic-jacobian ") or lowered.startswith("symplectic-jacobian "):
            if hasattr(self.runtime, "symplectic_integrator"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    q0 = [float(parts[1])]
                    p0 = [float(parts[2])]
                    dt = float(parts[3]) if len(parts) >= 4 else 0.05
                    res = self.runtime.symplectic_integrator.verify_symplectic_jacobian(q0, p0, dt)
                    msg = f"Symplectic Jacobian: det(J)={res['det_jacobian']:.6f}, discrepancy={res['det_discrepancy']:.6f}, holds={res['is_symplectic_invariant']}."
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /symplectic-jacobian <q0> <p0> [dt]")

        # Stage 255: Sovereign Bio-Mimetic Morphogenetic Reaction-Diffusion Turing Pattern Synthesizer
        if lowered in {"/turing-status", "turing-status", "/morphogenesis-status", "morphogenesis-status"}:
            if hasattr(self.runtime, "turing_synthesizer"):
                tbl = self.runtime.turing_synthesizer.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.turing_synthesizer.get_metrics())
            return RouterResponse("Turing synthesizer not available.")

        if lowered.startswith("/turing-step ") or lowered.startswith("turing-step "):
            if hasattr(self.runtime, "turing_synthesizer"):
                parts = raw_text.strip().split()
                steps = int(parts[1]) if len(parts) >= 2 else 5
                dt = float(parts[2]) if len(parts) >= 3 else 1.0
                self.runtime.turing_synthesizer.step_reaction_diffusion(steps=steps, dt=dt)
                stats = self.runtime.turing_synthesizer.compute_morphogenetic_statistics()
                msg = f"Simulated {steps} PDE steps (dt={dt}): state={stats['regime']}, var(u)={stats['variance_u']:.4f}, var(v)={stats['variance_v']:.4f}"
                return RouterResponse(msg, data=stats)
            return RouterResponse("Usage: /turing-step [steps] [dt]")

        if lowered.startswith("/turing-seed ") or lowered.startswith("turing-seed "):
            if hasattr(self.runtime, "turing_synthesizer"):
                parts = raw_text.strip().split()
                r = int(parts[1]) if len(parts) >= 2 else 4
                self.runtime.turing_synthesizer.seed_central_spot(radius=r)
                msg = f"Seeded central perturbation (radius={r}) into {self.runtime.turing_synthesizer.w}x{self.runtime.turing_synthesizer.h} grid."
                return RouterResponse(msg, data={"radius": r})
            return RouterResponse("Usage: /turing-seed [radius]")

        if lowered.startswith("/turing-instability ") or lowered.startswith("turing-instability "):
            if hasattr(self.runtime, "turing_synthesizer"):
                parts = raw_text.strip().split()
                if len(parts) >= 7:
                    fu, fv = float(parts[1]), float(parts[2])
                    gu, gv = float(parts[3]), float(parts[4])
                    du, dv = float(parts[5]), float(parts[6])
                    res = self.runtime.turing_synthesizer.evaluate_turing_instability(fu, fv, gu, gv, du, dv)
                    msg = (
                        f"Turing Instability Audit: unstable={res['is_turing_instability']}, "
                        f"kc={res['critical_wavenumber']}, wavelength={res['pattern_wavelength']}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /turing-instability <fu> <fv> <gu> <gv> <du> <dv>")

        # Stage 256: Deep Renormalization Group Flow & Wilsonian Effective Field Theory Coarse-Grainer
        if lowered in {"/rg-flow-status", "rg-flow-status", "/renormalization-status", "renormalization-status"}:
            if hasattr(self.runtime, "rg_flow_fabric"):
                tbl = self.runtime.rg_flow_fabric.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.rg_flow_fabric.get_metrics())
            return RouterResponse("RG flow fabric not available.")

        if lowered.startswith("/rg-integrate ") or lowered.startswith("rg-integrate "):
            if hasattr(self.runtime, "rg_flow_fabric"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    g0 = float(parts[1])
                    eps = float(parts[2]) if len(parts) >= 3 else 1.0
                    steps = int(parts[3]) if len(parts) >= 4 else 30
                    res = self.runtime.rg_flow_fabric.integrate_rg_flow(g0, eps, steps)
                    msg = (
                        f"RG Trajectory (steps={steps}, eps={eps}): g_init={res['initial_coupling']:.4f} -> "
                        f"g_final={res['final_coupling']:.4f} (Wilson-Fisher target: {res['wilson_fisher_target']:.4f})."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /rg-integrate <g_initial> [epsilon] [steps]")

        if lowered.startswith("/rg-spin-block ") or lowered.startswith("rg-spin-block "):
            if hasattr(self.runtime, "rg_flow_fabric"):
                parts = raw_text.strip().split()
                w = int(parts[1]) if len(parts) >= 2 else 16
                h = int(parts[2]) if len(parts) >= 3 else 16
                p_up = float(parts[3]) if len(parts) >= 4 else 0.7
                lat = self.runtime.rg_flow_fabric.generate_random_ising_lattice(w, h, p_up=p_up)
                coarse = self.runtime.rg_flow_fabric.kadanoff_spin_block_2d(lat)
                stats_orig = self.runtime.rg_flow_fabric.calculate_magnetization_and_correlation(lat)
                stats_coarse = self.runtime.rg_flow_fabric.calculate_magnetization_and_correlation(coarse)
                msg = (
                    f"Kadanoff Block ({w}x{h} -> {len(coarse[0])}x{len(coarse)}): "
                    f"mag: {stats_orig['magnetization']:.2f} -> {stats_coarse['magnetization']:.2f}, "
                    f"nn_corr: {stats_orig['nn_correlation']:.2f} -> {stats_coarse['nn_correlation']:.2f}."
                )
                return RouterResponse(msg, data={"orig": stats_orig, "coarse": stats_coarse})
            return RouterResponse("Usage: /rg-spin-block [width] [height] [p_up]")

        # Stage 257: Quantum Superconducting Josephson Junction SQUID Flux-State Quantum Magnetometer
        if lowered in {"/squid-status", "squid-status", "/josephson-status", "josephson-status"}:
            if hasattr(self.runtime, "squid_magnetometer"):
                tbl = self.runtime.squid_magnetometer.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.squid_magnetometer.get_metrics())
            return RouterResponse("SQUID magnetometer not available.")

        if lowered.startswith("/squid-measure-b ") or lowered.startswith("squid-measure-b "):
            if hasattr(self.runtime, "squid_magnetometer"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    b_val = float(parts[1])
                    res = self.runtime.squid_magnetometer.measure_external_field(b_val)
                    msg = (
                        f"SQUID Field Measurement (B={b_val:.3e} T): flux={res['flux_webers']:.3e} Wb "
                        f"({res['flux_quanta']:.4f} Phi_0), V_out={res['voltage_microvolts']:.2f} uV, Ic={res['ic_microamps']:.2f} uA."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /squid-measure-b <b_tesla>")

        if lowered.startswith("/josephson-frequency ") or lowered.startswith("josephson-frequency "):
            if hasattr(self.runtime, "squid_magnetometer"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    v_val = float(parts[1])
                    f_j = self.runtime.squid_magnetometer.compute_ac_josephson_frequency(v_val)
                    msg = f"AC Josephson Frequency (V={v_val:.6f} V): f_J = {f_j*1e-9:.4f} GHz ({f_j:.3e} Hz)."
                    return RouterResponse(msg, data={"voltage_v": v_val, "frequency_hz": f_j, "frequency_ghz": f_j * 1e-9})
            return RouterResponse("Usage: /josephson-frequency <voltage_volts>")

        # Stage 258: Planetary Astro-Chronometric Relativistic Gravitational Time-Dilation Synchronizer
        if lowered in {"/relativistic-chrono-status", "relativistic-chrono-status", "/chrono-sync-status", "chrono-sync-status"}:
            if hasattr(self.runtime, "chrono_synchronizer"):
                tbl = self.runtime.chrono_synchronizer.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.chrono_synchronizer.get_metrics())
            return RouterResponse("Chrono synchronizer not available.")

        if lowered.startswith("/orbit-dilation ") or lowered.startswith("orbit-dilation "):
            if hasattr(self.runtime, "chrono_synchronizer"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    alt_km = float(parts[1])
                    body = parts[2] if len(parts) >= 3 else "earth"
                    offset = self.runtime.chrono_synchronizer.compute_orbit_dilation(alt_km * 1000.0, body)
                    msg = (
                        f"Orbital Relativistic Dilation ({offset.body}, alt={alt_km} km): "
                        f"Net Drift={offset.drift_microseconds_per_day:+.2f} us/day "
                        f"(Grav={offset.gravitational_shift_ratio*86400*1e6:+.2f} us/day, "
                        f"Kin={offset.kinematic_shift_ratio*86400*1e6:.2f} us/day)."
                    )
                    return RouterResponse(msg, data={
                        "body": offset.body,
                        "altitude_km": alt_km,
                        "net_drift_us_per_day": offset.drift_microseconds_per_day,
                        "grav_us": offset.gravitational_shift_ratio * 86400 * 1e6,
                        "kin_us": offset.kinematic_shift_ratio * 86400 * 1e6,
                    })
            return RouterResponse("Usage: /orbit-dilation <altitude_km> [body]")

        if lowered.startswith("/clock-sync ") or lowered.startswith("clock-sync "):
            if hasattr(self.runtime, "chrono_synchronizer"):
                parts = raw_text.strip().split()
                if len(parts) >= 4:
                    raw_sec = float(parts[1])
                    alt_km = float(parts[2])
                    days = float(parts[3])
                    body = parts[4] if len(parts) >= 5 else "earth"
                    res = self.runtime.chrono_synchronizer.synchronize_clock(raw_sec, alt_km * 1000.0, days, body)
                    msg = (
                        f"Synchronized Clock ({res['body']}, {days} days): "
                        f"Raw={res['raw_clock_sec']:.6f}s -> Corrected={res['corrected_time_sec']:.6f}s "
                        f"(Drift Offset={res['accumulated_drift_us']:+.2f} us)."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /clock-sync <raw_clock_sec> <altitude_km> <elapsed_days> [body]")

        # Stage 259: Autonomous Sovereign Multi-Agent Constitutional Game-Theoretic Shapley-Nash Equilibrium Engine
        if lowered in {"/shapley-nash-status", "shapley-nash-status", "/game-theory-status", "game-theory-status"}:
            if hasattr(self.runtime, "shapley_nash_engine"):
                tbl = self.runtime.shapley_nash_engine.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.shapley_nash_engine.get_metrics())
            return RouterResponse("Shapley-Nash engine not available.")

        if lowered.startswith("/shapley-majority ") or lowered.startswith("shapley-majority "):
            if hasattr(self.runtime, "shapley_nash_engine"):
                parts = raw_text.strip().split()
                agents = parts[1:] if len(parts) >= 2 else ["Senin", "Subagent_1", "Subagent_2"]
                # Majority rule game
                res = self.runtime.shapley_nash_engine.compute_shapley_values(
                    agents,
                    lambda s: 1.0 if len(s) >= (len(agents) // 2 + 1) else 0.0
                )
                msg = f"Shapley Majority Allocation ({len(agents)} agents): " + ", ".join(f"{k}={v:.4f}" for k, v in res.items())
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /shapley-majority [agent1 agent2 ...]")

        if lowered in {"/nash-prisoners-dilemma", "nash-prisoners-dilemma"}:
            if hasattr(self.runtime, "shapley_nash_engine"):
                players = ["P1", "P2"]
                actions = {"P1": ["Cooperate", "Defect"], "P2": ["Cooperate", "Defect"]}
                payoffs = {
                    ("Cooperate", "Cooperate"): {"P1": 3.0, "P2": 3.0},
                    ("Cooperate", "Defect"): {"P1": 0.0, "P2": 5.0},
                    ("Defect", "Cooperate"): {"P1": 5.0, "P2": 0.0},
                    ("Defect", "Defect"): {"P1": 1.0, "P2": 1.0},
                }
                psne = self.runtime.shapley_nash_engine.find_pure_strategy_nash_equilibria(players, actions, payoffs)
                msg = f"Prisoner's Dilemma Nash Equilibrium: {psne[0]['strategy']} -> Payoffs: {psne[0]['payoffs']}"
                return RouterResponse(msg, data=psne)
            return RouterResponse("Shapley-Nash engine not available.")

        if lowered.startswith("/sovereign-core-guarantee ") or lowered.startswith("sovereign-core-guarantee "):
            if hasattr(self.runtime, "shapley_nash_engine"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    senin_val = float(parts[1])
                    alloc = {"Senin": senin_val}
                    for i, p in enumerate(parts[2:]):
                        alloc[f"Agent_{i+1}"] = float(p)
                    guaranteed = self.runtime.shapley_nash_engine.enforce_constitutional_sovereign_guarantee(alloc)
                    msg = "Constitutional Core Guarantee: " + ", ".join(f"{k}={v:.2f}" for k, v in guaranteed.items())
                    return RouterResponse(msg, data=guaranteed)
            return RouterResponse("Usage: /sovereign-core-guarantee <senin_val> <agent_val1> [agent_val2 ...]")

        # Stage 260: The Sovereign Era 26 Master Seal & Omniscient Holomorphic Singularity Genesis
        if lowered in {"/era26-status", "era26-status"}:
            if hasattr(self.runtime, "era26_master_seal"):
                tbl = self.runtime.era26_master_seal.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.era26_master_seal.status())
            return RouterResponse("Era 26 Master Seal not available.")

        if lowered in {"/era26-seal-report", "era26-seal-report"}:
            if hasattr(self.runtime, "era26_master_seal"):
                report = self.runtime.era26_master_seal.format_grand_era_report()
                return RouterResponse(report, data=self.runtime.era26_master_seal.status())
            return RouterResponse("Era 26 Master Seal not available.")

        if lowered in {"/era26-verify", "era26-verify"}:
            if hasattr(self.runtime, "era26_master_seal"):
                ver = self.runtime.era26_master_seal.verify_era26_integrity()
                msg = (
                    f"Era 26 Integrity Verification: valid={ver['verified']}, "
                    f"Stages={ver['stages_verified']}, Master Merkle Root={ver['master_merkle_root'][:16]}..."
                )
                return RouterResponse(msg, data=ver)
            return RouterResponse("Era 26 Master Seal not available.")

        if lowered in {"/era26-manifest", "era26-manifest"}:
            if hasattr(self.runtime, "era26_master_seal"):
                manifest = self.runtime.era26_master_seal.get_stage_manifest()
                lines = ["Era 26 Stage Manifest (Stages 251 - 260):"]
                for m in manifest:
                    lines.append(f"Stage {m.stage}: {m.name} -> {m.sha256[:16]}... [{m.status}]")
                return RouterResponse("\n".join(lines), data=[m.to_dict() for m in manifest])
            return RouterResponse("Era 26 Master Seal not available.")

        # Stage 261: Non-Abelian SU(N) Yang-Mills Gauge Connection & Wilson Loop Holonomy Engine
        if lowered in {"/yang-mills-status", "yang-mills-status", "/gauge-holonomy-status", "gauge-holonomy-status"}:
            if hasattr(self.runtime, "yang_mills_engine"):
                tbl = self.runtime.yang_mills_engine.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.yang_mills_engine.get_metrics())
            return RouterResponse("Yang-Mills engine not available.")

        if lowered.startswith("/wilson-loop ") or lowered.startswith("wilson-loop "):
            if hasattr(self.runtime, "yang_mills_engine"):
                parts = raw_text.strip().split()
                if len(parts) >= 7:
                    ax = [float(parts[1]), float(parts[2]), float(parts[3])]
                    ay = [float(parts[4]), float(parts[5]), float(parts[6])]
                    dx = float(parts[7]) if len(parts) >= 8 else 0.1
                    dy = float(parts[8]) if len(parts) >= 9 else 0.1
                    res = self.runtime.yang_mills_engine.compute_wilson_loop(ax, ay, dx, dy)
                    msg = (
                        f"Wilson Loop Holonomy ({res['gauge_group']}): W(C) = {res['wilson_loop_value']:.6f} "
                        f"(Trace: {res['trace_real']:.4f} + {res['trace_imag']:.4f}i, Area={res['plaquette_area']})."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /wilson-loop <ax1> <ax2> <ax3> <ay1> <ay2> <ay3> [dx] [dy]")

        if lowered.startswith("/gauge-audit ") or lowered.startswith("gauge-audit "):
            if hasattr(self.runtime, "yang_mills_engine"):
                parts = raw_text.strip().split()
                if len(parts) >= 7:
                    ax = [float(parts[1]), float(parts[2]), float(parts[3])]
                    ay = [float(parts[4]), float(parts[5]), float(parts[6])]
                    res = self.runtime.yang_mills_engine.verify_gauge_invariance(ax, ay)
                    msg = (
                        f"Local Gauge Invariance Audit: invariant={res['is_gauge_invariant']}, "
                        f"Tr(orig)={res['trace_original']:.6f}, Tr(gauge_rot)={res['trace_transformed']:.6f}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /gauge-audit <ax1> <ax2> <ax3> <ay1> <ay2> <ay3>")

        # Stage 262: Holographic AdS/CFT Conformal Boundary-to-Bulk Dictionary & Ryu-Takayanagi Entanglement Wedge
        if lowered in {"/ads-cft-status", "ads-cft-status", "/holographic-status", "holographic-status"}:
            if hasattr(self.runtime, "entanglement_wedge_fabric"):
                tbl = self.runtime.entanglement_wedge_fabric.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.entanglement_wedge_fabric.get_metrics())
            return RouterResponse("Entanglement wedge fabric not available.")

        if lowered.startswith("/rt-entropy ") or lowered.startswith("rt-entropy "):
            if hasattr(self.runtime, "entanglement_wedge_fabric"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    l_val = float(parts[1])
                    eps = float(parts[2]) if len(parts) >= 3 else 1e-3
                    res = self.runtime.entanglement_wedge_fabric.compute_ryu_takayanagi_entropy(l_val, eps)
                    msg = (
                        f"Ryu-Takayanagi Entanglement Entropy (l={l_val}, c={res['central_charge']}): "
                        f"S_A = {res['entanglement_entropy']:.4f} (Geodesic length: {res['geodesic_length']:.4f}, z_max={res['max_bulk_penetration_z']})."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /rt-entropy <subsystem_length> [uv_cutoff]")

        if lowered.startswith("/entanglement-wedge-check ") or lowered.startswith("entanglement-wedge-check "):
            if hasattr(self.runtime, "entanglement_wedge_fabric"):
                parts = raw_text.strip().split()
                if len(parts) >= 5:
                    x, z = float(parts[1]), float(parts[2])
                    x_start, x_end = float(parts[3]), float(parts[4])
                    inside = self.runtime.entanglement_wedge_fabric.is_in_entanglement_wedge(x, z, x_start, x_end)
                    msg = f"Bulk point ({x}, {z}) inside Entanglement Wedge [{x_start}, {x_end}]: {inside}."
                    return RouterResponse(msg, data={"x": x, "z": z, "inside_wedge": inside})
            return RouterResponse("Usage: /entanglement-wedge-check <x> <z> <x_start> <x_end>")

        if lowered.startswith("/holographic-mutual-info ") or lowered.startswith("holographic-mutual-info "):
            if hasattr(self.runtime, "entanglement_wedge_fabric"):
                parts = raw_text.strip().split()
                if len(parts) >= 4:
                    la, lb, d = float(parts[1]), float(parts[2]), float(parts[3])
                    res = self.runtime.entanglement_wedge_fabric.compute_holographic_mutual_information(la, lb, d)
                    msg = (
                        f"Holographic Mutual Information I(A:B) = {res['mutual_information']:.4f} "
                        f"(Phase: {res['holographic_phase']}, S_A={res['entropy_a']:.2f}, S_B={res['entropy_b']:.2f})."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /holographic-mutual-info <length_a> <length_b> <separation_d>")

        # Stage 263: Superconducting Optomechanical Cavity Radiation Pressure & Phonon-Photon Squeezing Transceiver
        if lowered in {"/optomechanics-status", "optomechanics-status", "/cavity-status", "cavity-status"}:
            if hasattr(self.runtime, "optomechanical_transceiver"):
                tbl = self.runtime.optomechanical_transceiver.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.optomechanical_transceiver.get_metrics())
            return RouterResponse("Optomechanical transceiver not available.")

        if lowered.startswith("/opto-cool ") or lowered.startswith("opto-cool "):
            if hasattr(self.runtime, "optomechanical_transceiver"):
                parts = raw_text.strip().split()
                p_mw = float(parts[1]) if len(parts) >= 2 else 0.1
                t_k = float(parts[2]) if len(parts) >= 3 else 0.1
                res = self.runtime.optomechanical_transceiver.evaluate_ground_state_cooling(p_mw * 1e-3, t_k)
                msg = (
                    f"Optomechanical Backaction Cooling (P={p_mw} mW, T={t_k} K): "
                    f"n_eff={res['final_cooled_occupancy']:.4f} phonons (Ground state: {res['is_quantum_ground_state']}). "
                    f"Cooling rate: {res['optomechanical_cooling_rate_s']:.1f} s^-1."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /opto-cool [laser_power_mw] [bath_temp_k]")

        if lowered.startswith("/opto-squeeze ") or lowered.startswith("opto-squeeze "):
            if hasattr(self.runtime, "optomechanical_transceiver"):
                parts = raw_text.strip().split()
                p_mw = float(parts[1]) if len(parts) >= 2 else 1.0
                det_ratio = float(parts[2]) if len(parts) >= 3 else 0.5
                res = self.runtime.optomechanical_transceiver.compute_ponderomotive_squeezing(p_mw * 1e-3, det_ratio)
                msg = (
                    f"Ponderomotive Optical Squeezing (P={p_mw} mW): {res['squeezing_db']:.2f} dB below SQL "
                    f"(Variance: {res['noise_variance_ratio']:.4f}, Cooperativity: {res['cooperativity_C']:.2f})."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /opto-squeeze [laser_power_mw] [detuning_ratio]")

        # --- Stage 264: Autonomous Topological Soliton Skyrmion Lattice Dynamics & Chiral Domain Wall Weaver ---
        if lowered in ("/skyrmion-status", "skyrmion-status"):
            if hasattr(self.runtime, "skyrmion_weaver"):
                st = self.runtime.skyrmion_weaver.get_status()
                msg = (
                    f"Topological Skyrmion Weaver: Grid={st['grid_size']}, Solitons={st['active_solitons']}, "
                    f"Net Topological Charge Q={st['net_topological_charge']}."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("Topological Skyrmion Weaver not initialized.")

        if lowered.startswith("/skyrmion-wind ") or lowered.startswith("skyrmion-wind "):
            if hasattr(self.runtime, "skyrmion_weaver"):
                parts = raw_text.strip().split()
                if len(parts) >= 4:
                    cx, cy, rad = float(parts[1]), float(parts[2]), float(parts[3])
                    res = self.runtime.skyrmion_weaver.inject_skyrmion(center_x=cx, center_y=cy, radius=rad)
                    msg = f"Injected Skyrmion at ({cx}, {cy}) radius={rad} -> Net Q={res['topological_charge']}."
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /skyrmion-wind <center_x> <center_y> <radius>")

        if lowered.startswith("/skyrmion-thiele ") or lowered.startswith("skyrmion-thiele "):
            if hasattr(self.runtime, "skyrmion_weaver"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    j_dens = float(parts[1])
                    res = self.runtime.skyrmion_weaver.compute_thiele_dynamics(current_density_j_a_m2=j_dens)
                    msg = (
                        f"Thiele Dynamics: Q={res['topological_charge']}, Speed={res['speed_m_s']:.2f} m/s, "
                        f"Hall Angle={res['skyrmion_hall_angle_deg']:.2f} deg."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /skyrmion-thiele <current_density_j>")

        if lowered.startswith("/skyrmion-racetrack ") or lowered.startswith("skyrmion-racetrack "):
            if hasattr(self.runtime, "skyrmion_weaver"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    bits = parts[1]
                    res = self.runtime.skyrmion_weaver.encode_racetrack_track(bits)
                    msg = (
                        f"Racetrack Track: Bits='{res['encoded_bits']}', Net Q={res['total_topological_charge']}, "
                        f"Fidelity={res['fidelity']*100:.1f}%."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /skyrmion-racetrack <bit_sequence>")

        # --- Stage 265: Continuous-Time Quantum Walk & Graph-Topological Spatial Search Accelerator ---
        if lowered in ("/quantum-walk-status", "quantum-walk-status"):
            if hasattr(self.runtime, "quantum_walk_search"):
                st = self.runtime.quantum_walk_search.get_status()
                msg = (
                    f"Quantum Walk Accelerator: Nodes={st['num_nodes']}, Edges={st['num_edges']}, "
                    f"Gamma={st['hopping_rate_gamma']}, Searches Executed={st['total_searches_executed']}."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("Quantum Walk Search accelerator not initialized.")

        if lowered.startswith("/qw-propagate ") or lowered.startswith("qw-propagate "):
            if hasattr(self.runtime, "quantum_walk_search"):
                parts = raw_text.strip().split()
                t_val = float(parts[1]) if len(parts) >= 2 else 1.0
                res = self.runtime.quantum_walk_search.propagate_quantum_state(evolution_time=t_val)
                msg = (
                    f"Quantum Walk Propagate (t={t_val}): Norm={res['state_norm']}, "
                    f"Max Prob={max(res['probabilities']):.4f}."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /qw-propagate <evolution_time>")

        if lowered.startswith("/qw-search ") or lowered.startswith("qw-search "):
            if hasattr(self.runtime, "quantum_walk_search"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    tgt = int(parts[1])
                    depth = float(parts[2]) if len(parts) >= 3 else 2.0
                    res = self.runtime.quantum_walk_search.execute_spatial_search(target_node=tgt, oracle_depth=depth)
                    msg = (
                        f"Continuous Quantum Search: Target={res['target_node']}, Peak Prob={res['peak_success_probability']:.4f} "
                        f"at t={res['optimal_time_t']:.2f} (Speedup: {res['quantum_advantage_factor']:.2f}x)."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /qw-search <target_node> [oracle_depth]")

        if lowered.startswith("/qw-topology ") or lowered.startswith("qw-topology "):
            if hasattr(self.runtime, "quantum_walk_search"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    top = parts[1].lower()
                    if top == "complete":
                        self.runtime.quantum_walk_search.set_topology_complete()
                    elif top == "star":
                        self.runtime.quantum_walk_search.set_topology_star()
                    else:
                        self.runtime.quantum_walk_search.set_topology_cycle()
                    st = self.runtime.quantum_walk_search.get_status()
                    msg = f"Quantum Walk Topology switched to '{top}': Nodes={st['num_nodes']}, Edges={st['num_edges']}."
                    return RouterResponse(msg, data=st)
            return RouterResponse("Usage: /qw-topology <cycle|complete|star>")

        # --- Stage 266: Planetary Magnetohydrodynamic (MHD) Dynamo Alfven Wave Plasma Core Simulator ---
        if lowered in ("/mhd-dynamo-status", "mhd-dynamo-status"):
            if hasattr(self.runtime, "mhd_dynamo_sim"):
                st = self.runtime.mhd_dynamo_sim.get_status()
                msg = (
                    f"MHD Dynamo Simulator: Radius={st['core_radius_km']} km, B_pol={st['b_poloidal_tesla']:.2e} T, "
                    f"Rm={st['magnetic_reynolds_Rm']:.0f}, Alfven Speed={st['alfven_velocity_m_s']:.2f} m/s."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("MHD Dynamo simulator not initialized.")

        if lowered.startswith("/mhd-step ") or lowered.startswith("mhd-step "):
            if hasattr(self.runtime, "mhd_dynamo_sim"):
                parts = raw_text.strip().split()
                dt_y = float(parts[1]) if len(parts) >= 2 else 100.0
                res = self.runtime.mhd_dynamo_sim.step_dynamo_evolution(dt_years=dt_y)
                msg = (
                    f"MHD Dynamo Step (dt={dt_y} yr): B_total={res['b_total_tesla']:.2e} T, "
                    f"Alfven={res['alfven_speed_m_s']:.2f} m/s, Dipole M={res['dipole_moment_a_m2']:.2e} A*m^2."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /mhd-step <dt_years>")

        if lowered.startswith("/mhd-alfven-speed ") or lowered.startswith("mhd-alfven-speed "):
            if hasattr(self.runtime, "mhd_dynamo_sim"):
                parts = raw_text.strip().split()
                b_val = float(parts[1]) if len(parts) >= 2 else 0.005
                res = self.runtime.mhd_dynamo_sim.compute_alfven_velocity(b_field_tesla=b_val)
                msg = (
                    f"Alfven Wave Speed (B={b_val} T): v_A={res['alfven_velocity_m_s']:.2f} m/s, "
                    f"Core Transit Time={res['core_transit_time_years']:.2f} years."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /mhd-alfven-speed <b_field_tesla>")

        if lowered.startswith("/mhd-reversal ") or lowered.startswith("mhd-reversal "):
            if hasattr(self.runtime, "mhd_dynamo_sim"):
                parts = raw_text.strip().split()
                dur = float(parts[1]) if len(parts) >= 2 else 10000.0
                res = self.runtime.mhd_dynamo_sim.simulate_magnetic_reversal(duration_years=dur)
                msg = (
                    f"Geomagnetic Reversal Sim ({dur} yr): Flips={res['polarity_flips']}, "
                    f"Final B_pol={res['final_poloidal_b_tesla']:.2e} T, Reversed={res['is_reversed']}."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /mhd-reversal <duration_years>")

        # --- Stage 267: Geometric Berry-Pancharatnam Phase & Non-Abelian Wilczek-Zee Holonomy Gate ---
        if lowered in ("/berry-phase-status", "berry-phase-status"):
            if hasattr(self.runtime, "berry_holonomy"):
                st = self.runtime.berry_holonomy.get_status()
                msg = (
                    f"Berry-Wilczek-Zee Holonomy Engine: hbar={st['hbar']}, "
                    f"Holonomic Gates Synthesized={st['holonomy_gates_synthesized']}."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("Berry-Wilczek-Zee Holonomy engine not initialized.")

        if lowered.startswith("/berry-spin ") or lowered.startswith("berry-spin "):
            if hasattr(self.runtime, "berry_holonomy"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    deg = float(parts[1])
                    loops = int(parts[2]) if len(parts) >= 3 else 1
                    theta = deg * 3.141592653589793 / 180.0
                    res = self.runtime.berry_holonomy.compute_spin_berry_phase(cone_angle_theta_rad=theta, loops=loops)
                    msg = (
                        f"Spin-1/2 Berry Phase (theta={deg} deg, {loops} loops): gamma={res['berry_phase_deg']:.2f} deg "
                        f"({res['berry_phase_rad']:.4f} rad), Solid Angle={res['solid_angle_steradians']:.3f} sr, C_1={res['first_chern_number']}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /berry-spin <cone_angle_deg> [loops]")

        if lowered in ("/pancharatnam-phase", "pancharatnam-phase"):
            if hasattr(self.runtime, "berry_holonomy"):
                res = self.runtime.berry_holonomy.compute_pancharatnam_phase()
                msg = (
                    f"Pancharatnam Geometric Phase: Phi_P={res['pancharatnam_phase_deg']:.2f} deg "
                    f"({res['pancharatnam_phase_rad']:.4f} rad), Enclosed Solid Angle={res['enclosed_solid_angle']:.3f} sr."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Berry-Wilczek-Zee Holonomy engine not initialized.")

        if lowered.startswith("/wilczek-zee-gate ") or lowered.startswith("wilczek-zee-gate "):
            if hasattr(self.runtime, "berry_holonomy"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    g_type = parts[1].upper()
                    angle_deg = float(parts[2]) if len(parts) >= 3 else 180.0
                    angle_rad = angle_deg * 3.141592653589793 / 180.0
                    res = self.runtime.berry_holonomy.synthesize_wilczek_zee_gate(gate_type=g_type, alpha_angle=angle_rad)
                    msg = (
                        f"Wilczek-Zee Holonomy Gate '{g_type}': Angle={res['holonomy_angle_deg']:.1f} deg, "
                        f"Unitary={res['is_unitary']}, Matrix={res['matrix']}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /wilczek-zee-gate <NOT|PHASE|HADAMARD> [angle_deg]")

        # --- Stage 268: Autonomous Cosmological FLRW Metric Evolution & Dark Energy State Engine ---
        if lowered in ("/flrw-status", "flrw-status"):
            if hasattr(self.runtime, "flrw_cosmo_engine"):
                st = self.runtime.flrw_cosmo_engine.get_status()
                msg = (
                    f"FLRW Cosmological Engine: H0={st['h0_km_s_mpc']} km/s/Mpc, Omega_m={st['omega_matter_0']}, "
                    f"Omega_DE={st['omega_dark_energy_0']}, q0={st['deceleration_q0']}, Age={st['age_of_universe_gyr']} Gyr."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("FLRW Cosmological Engine not initialized.")

        if lowered.startswith("/flrw-acceleration") or lowered.startswith("flrw-acceleration"):
            if hasattr(self.runtime, "flrw_cosmo_engine"):
                parts = raw_text.strip().split()
                z_val = float(parts[1]) if len(parts) >= 2 else 0.0
                res = self.runtime.flrw_cosmo_engine.compute_cosmic_acceleration_q(z=z_val)
                msg = (
                    f"Cosmic Acceleration at z={z_val}: q={res['deceleration_parameter_q']:.4f} "
                    f"(Accelerating: {res['is_accelerating']}, w_DE={res['dark_energy_eos_w']}, Omega_DE(z)={res['omega_dark_energy_z']:.3f})."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /flrw-acceleration [z]")

        if lowered.startswith("/flrw-distance ") or lowered.startswith("flrw-distance "):
            if hasattr(self.runtime, "flrw_cosmo_engine"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    z_val = float(parts[1])
                    res = self.runtime.flrw_cosmo_engine.compute_distance_ladder(z=z_val)
                    msg = (
                        f"Distance Ladder at z={z_val}: d_L={res['luminosity_dist_mpc']:.1f} Mpc, "
                        f"d_A={res['angular_diam_dist_mpc']:.1f} Mpc, Lookback Time={res['lookback_time_gyr']:.2f} Gyr."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /flrw-distance <z>")

        if lowered in ("/flrw-age", "flrw-age"):
            if hasattr(self.runtime, "flrw_cosmo_engine"):
                age = self.runtime.flrw_cosmo_engine.compute_age_of_universe()
                msg = f"Cosmic Age of Universe t_0: {age:.3f} Gigayears ({age*1e9:.1e} years)."
                return RouterResponse(msg, data={"age_of_universe_gyr": age})

        # --- Stage 269: Sovereign Decentralized Multi-Tier Zero-Knowledge Succinct zk-SNARK / STARK Verifier ---
        if lowered in ("/zk-verifier-status", "zk-verifier-status"):
            if hasattr(self.runtime, "zk_verifier"):
                st = self.runtime.zk_verifier.get_status()
                msg = (
                    f"ZK Verifier: Curve={st['elliptic_curve']}, Field Bits={st['field_modulus_bits']}, "
                    f"Verified Receipts={st['total_verified_receipts']}."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("ZK Verifier not initialized.")

        if lowered.startswith("/zk-prove-identity ") or lowered.startswith("zk-prove-identity "):
            if hasattr(self.runtime, "zk_verifier"):
                parts = raw_text.strip().split(maxsplit=2)
                if len(parts) >= 3:
                    chal = parts[1]
                    sec = parts[2]
                    proof = self.runtime.zk_verifier.generate_sovereign_identity_proof(chal, sec)
                    msg = (
                        f"ZK Proof Generated for '{chal}': Commitment={proof['commitment_hash'][:16]}..., "
                        f"Response={proof['proof_response'][:16]}... (Zero Witness Leakage)."
                    )
                    return RouterResponse(msg, data=proof)
            return RouterResponse("Usage: /zk-prove-identity <challenge> <secret>")

        if lowered.startswith("/zk-verify-r1cs-mul ") or lowered.startswith("zk-verify-r1cs-mul "):
            if hasattr(self.runtime, "zk_verifier"):
                parts = raw_text.strip().split()
                if len(parts) >= 4:
                    x, y, out = int(parts[1]), int(parts[2]), int(parts[3])
                    matrix_a = [[0, 1, 0, 0]]
                    matrix_b = [[0, 0, 1, 0]]
                    matrix_c = [[0, 0, 0, 1]]
                    witness = [1, x, y, out]
                    res = self.runtime.zk_verifier.verify_r1cs_constraint_system(matrix_a, matrix_b, matrix_c, witness)
                    msg = f"R1CS Check ({x} * {y} == {out}): Satisfied={res['is_satisfied']}, Violations={res['violations_count']}."
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /zk-verify-r1cs-mul <x> <y> <out>")

        # --- Stage 270: The Sovereign Era 27 Master Seal & Omnipresent Cosmological Genesis ---
        if lowered in ("/era27-seal", "era27-seal", "/era27-seal-report", "era27-seal-report"):
            if hasattr(self.runtime, "era27_master_seal"):
                report = self.runtime.era27_master_seal.format_grand_era_report()
                st = self.runtime.era27_master_seal.status()
                return RouterResponse(report, data=st)
            return RouterResponse("Era 27 Master Seal not initialized.")

        if lowered in ("/era27-status", "era27-status"):
            if hasattr(self.runtime, "era27_master_seal"):
                st = self.runtime.era27_master_seal.status()
                msg = (
                    f"Era 27 Master Seal: Status={st['verification_status']}, Total Stages={st['total_stages_sealed']}, "
                    f"Master Merkle Root={st['master_merkle_root'][:16]}..., Genesis Sig={st['genesis_signature'][:16]}..."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("Era 27 Master Seal not initialized.")

        if lowered in ("/era27-verify", "era27-verify"):
            if hasattr(self.runtime, "era27_master_seal"):
                integ = self.runtime.era27_master_seal.verify_era27_integrity()
                msg = (
                    f"Era 27 Integrity Audit: Verified={integ['verified']}, Stages={integ['stages_verified']}/10, "
                    f"Operator={integ['sovereign_operator']}."
                )
                return RouterResponse(msg, data=integ)
            return RouterResponse("Era 27 Master Seal not initialized.")

        if lowered in ("/era27-manifest", "era27-manifest"):
            if hasattr(self.runtime, "era27_master_seal"):
                manifest = [r.to_dict() for r in self.runtime.era27_master_seal.get_stage_manifest()]
                msg = f"Era 27 Stage Manifest: {len(manifest)} modules verified operational."
                return RouterResponse(msg, data={"manifest": manifest})
            return RouterResponse("Era 27 Master Seal not initialized.")

        # --- Stage 271: Quantum Chromodynamic (QCD) Asymptotic Freedom, Color Flux Tube Confinement & Hadronization Engine ---
        if lowered in ("/qcd-status", "qcd-status"):
            if hasattr(self.runtime, "qcd_confinement"):
                st = self.runtime.qcd_confinement.get_status()
                msg = (
                    f"QCD Confinement Engine: Lambda_QCD={st['lambda_qcd_gev']} GeV, Sigma={st['string_tension_sigma_gev_fm']} GeV/fm, "
                    f"alpha_s(1 GeV)={st['alpha_s_at_1_gev']:.3f}, alpha_s(100 GeV)={st['alpha_s_at_100_gev']:.3f}."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("QCD Confinement engine not initialized.")

        if lowered.startswith("/qcd-coupling ") or lowered.startswith("qcd-coupling "):
            if hasattr(self.runtime, "qcd_confinement"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    q_val = float(parts[1])
                    res = self.runtime.qcd_confinement.compute_running_coupling(q_gev=q_val)
                    msg = (
                        f"QCD Running Coupling at Q={q_val} GeV: alpha_s={res['alpha_s']:.4f} "
                        f"(Asymptotically Free: {res['is_asymptotically_free']}, beta_0={res['beta_0']})."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /qcd-coupling <q_gev>")

        if lowered.startswith("/qcd-cornell ") or lowered.startswith("qcd-cornell "):
            if hasattr(self.runtime, "qcd_confinement"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    r_val = float(parts[1])
                    res = self.runtime.qcd_confinement.compute_cornell_potential(separation_r_fm=r_val)
                    msg = (
                        f"Cornell Potential at r={r_val} fm: V_total={res['v_total_gev']:.3f} GeV "
                        f"(Coulomb: {res['v_coulomb_gev']:.3f} GeV, String: {res['v_string_gev']:.3f} GeV, Force: {res['restoring_force_gev_fm']:.3f} GeV/fm)."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /qcd-cornell <separation_r_fm>")

        if lowered.startswith("/qcd-hadronize") or lowered.startswith("qcd-hadronize"):
            if hasattr(self.runtime, "qcd_confinement"):
                parts = raw_text.strip().split()
                mq = float(parts[1]) if len(parts) >= 2 else 0.33
                res = self.runtime.qcd_confinement.simulate_flux_tube_breaking(quark_mass_gev=mq)
                msg = (
                    f"Color Flux Tube Snap (m_q={mq} GeV): Snapped={res['tube_snapped']}, "
                    f"Threshold={res['pair_creation_threshold_gev']} GeV, Fragments={res['hadron_fragments']}."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /qcd-hadronize [quark_mass_gev]")

        # --- Stage 272: Non-Commutative Moyal-Weyl Spacetime Star-Product Algebra & Quantum Gravity Uncertainty Engine ---
        if lowered in ("/moyal-status", "moyal-status"):
            if hasattr(self.runtime, "moyal_algebra"):
                st = self.runtime.moyal_algebra.get_status()
                msg = (
                    f"Moyal Star Algebra: Theta={st['theta_scale_m2']:.2e} m^2, "
                    f"GUP Minimal Length={st['minimal_observable_length_m']:.2e} m, Star Operations={st['total_star_evaluations']}."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("Moyal Star Algebra engine not initialized.")

        if lowered.startswith("/moyal-star ") or lowered.startswith("moyal-star "):
            if hasattr(self.runtime, "moyal_algebra"):
                parts = raw_text.strip().split()
                if len(parts) >= 7:
                    fv, fx, fy, gv, gx, gy = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4]), float(parts[5]), float(parts[6])
                    res = self.runtime.moyal_algebra.compute_moyal_star_product_2d(
                        f_val=fv, df_dx=fx, df_dy=fy, d2f_dxdy=0.0,
                        g_val=gv, dg_dx=gx, dg_dy=gy, d2g_dxdy=0.0
                    )
                    msg = (
                        f"Moyal Star Product: (f * g) = {res['star_product_repr']}, "
                        f"Poisson Bracket={res['poisson_bracket']:.4f}, Moyal Bracket={res['moyal_bracket']:.2e}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /moyal-star <f_val> <df_dx> <df_dy> <g_val> <dg_dx> <dg_dy>")

        if lowered.startswith("/gup-uncertainty ") or lowered.startswith("gup-uncertainty "):
            if hasattr(self.runtime, "moyal_algebra"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    dp = float(parts[1])
                    res = self.runtime.moyal_algebra.compute_gup_uncertainty(delta_p_kg_m_s=dp)
                    msg = (
                        f"GUP Bound (dp={dp:.2e}): dx_GUP={res['gup_dx_m']:.2e} m, "
                        f"dx_Heisenberg={res['heisenberg_dx_m']:.2e} m, dx_min={res['minimal_observable_length_m']:.2e} m."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /gup-uncertainty <delta_p>")

        if lowered.startswith("/uv-ir-mixing ") or lowered.startswith("uv-ir-mixing "):
            if hasattr(self.runtime, "moyal_algebra"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    p_val = float(parts[1])
                    res = self.runtime.moyal_algebra.compute_uv_ir_mixing_scale(external_momentum_p=p_val)
                    msg = (
                        f"UV/IR Mixing (p={p_val:.2e}): Lambda_eff={res['effective_cutoff_lambda_eff']:.2e}, "
                        f"Mixing Ratio={res['mixing_ratio']:.2e}, IR Dominated={res['is_ir_divergence_dominated']}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /uv-ir-mixing <momentum_p>")

        # --- Stage 273: Topological Anyon Fractional Exchange Statistics & Braiding Matrix Fusion Processor ---
        if lowered in ("/anyon-status", "anyon-status"):
            if hasattr(self.runtime, "anyon_processor"):
                st = self.runtime.anyon_processor.get_status()
                msg = (
                    f"Topological Anyon Processor: Model={st['anyon_model']}, "
                    f"Quantum Dimension={st['quantum_dimension_tau']}, Yang-Baxter={st['yang_baxter_satisfied']}."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("Topological Anyon processor not initialized.")

        if lowered.startswith("/anyon-phase ") or lowered.startswith("anyon-phase "):
            if hasattr(self.runtime, "anyon_processor"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    nu_val = float(parts[1])
                    cnt = int(parts[2]) if len(parts) >= 3 else 1
                    res = self.runtime.anyon_processor.compute_abelian_exchange_phase(filling_fraction_nu=nu_val, exchange_count=cnt)
                    msg = (
                        f"Abelian Anyon Phase (nu={nu_val}, n={cnt}): Half-Exchange={res['half_exchange_phase_deg']:.1f} deg, "
                        f"Full Loop={res['full_loop_braid_phase_deg']:.1f} deg (Factor: {res['phase_factor_real']:.4f}+{res['phase_factor_imag']:.4f}j)."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /anyon-phase <filling_nu> [exchanges]")

        if lowered in ("/anyon-yang-baxter", "anyon-yang-baxter"):
            if hasattr(self.runtime, "anyon_processor"):
                res = self.runtime.anyon_processor.verify_yang_baxter_braid_relation()
                msg = (
                    f"Artin Yang-Baxter Braid Check: Satisfied={res['is_satisfied']}, "
                    f"Max Deviation={res['max_deviation']:.2e}, Quantum Dimension={res['quantum_dimension_tau']}."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Topological Anyon processor not initialized.")

        if lowered.startswith("/anyon-braid ") or lowered.startswith("anyon-braid "):
            if hasattr(self.runtime, "anyon_processor"):
                parts = raw_text.strip().split()[1:]
                seq = [int(p) for p in parts if p.lstrip("-").isdigit()]
                if seq:
                    res = self.runtime.anyon_processor.execute_braid_sequence(sequence=seq)
                    msg = f"Braid Sequence {seq}: Unitary={res['is_unitary']}, Gate={res['matrix']}."
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /anyon-braid <move1> <move2> ... (e.g. 1 2 1)")

        # --- Stage 274: Relativistic Plasma Shock Magnetosonic Wave Accelerator & Fermi Cosmic-Ray Compressor ---
        if lowered in ("/shock-status", "shock-status"):
            if hasattr(self.runtime, "plasma_shock_accelerator"):
                st = self.runtime.plasma_shock_accelerator.get_status()
                msg = (
                    f"Plasma Shock Accelerator: Shock Speed={st['shock_speed_c']} c, "
                    f"Compression Ratio r={st['compression_ratio_r']:.2f}, Spectral Index p={st['asymptotic_spectral_index_p']:.2f}, "
                    f"Hillas Max={st['hillas_max_energy_pev']:.2f} PeV."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("Plasma Shock Accelerator not initialized.")

        if lowered.startswith("/shock-jumps") or lowered.startswith("shock-jumps"):
            if hasattr(self.runtime, "plasma_shock_accelerator"):
                parts = raw_text.strip().split()
                m_val = float(parts[1]) if len(parts) >= 2 else 20.0
                res = self.runtime.plasma_shock_accelerator.compute_shock_jump_conditions(mach_number=m_val)
                msg = (
                    f"Rankine-Hugoniot Shock (Mach={m_val}): Compression r={res['compression_ratio_r']:.3f} "
                    f"(r_max={res['asymptotic_r_max']}), B_2={res['downstream_b_tesla']:.2e} T, u_2={res['downstream_speed_m_s']:.1f} m/s."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /shock-jumps [mach_number]")

        if lowered.startswith("/fermi-acceleration") or lowered.startswith("fermi-acceleration"):
            if hasattr(self.runtime, "plasma_shock_accelerator"):
                parts = raw_text.strip().split()
                m_val = float(parts[1]) if len(parts) >= 2 else 20.0
                cycles = int(parts[2]) if len(parts) >= 3 else 50
                res = self.runtime.plasma_shock_accelerator.compute_fermi_acceleration_spectrum(mach_number=m_val, num_cycles=cycles)
                msg = (
                    f"Fermi Shock Acceleration ({cycles} cycles): E_final={res['final_energy_gev']:.2f} GeV "
                    f"({res['energy_amplification_factor']:.1f}x gain), Spectral Index p={res['spectral_index_p']:.2f}."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /fermi-acceleration [mach_number] [cycles]")

        if lowered.startswith("/hillas-limit") or lowered.startswith("hillas-limit"):
            if hasattr(self.runtime, "plasma_shock_accelerator"):
                parts = raw_text.strip().split()
                r_pc = float(parts[1]) if len(parts) >= 2 else 10.0
                z_chg = int(parts[2]) if len(parts) >= 3 else 1
                r_m = r_pc * 3.086e16
                res = self.runtime.plasma_shock_accelerator.compute_hillas_maximum_energy(shock_radius_m=r_m, charge_number_z=z_chg)
                msg = (
                    f"Hillas Upper Bound (R={r_pc} pc, Z={z_chg}): E_max={res['max_energy_pev']:.4f} PeV "
                    f"({res['max_energy_ev']:.2e} eV, Knee Regime: {res['cosmic_ray_knee_regime']})."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /hillas-limit [shock_radius_pc] [charge_z]")

        # --- Stage 275: Autonomous Gravitational Lensing Caustic & Relativistic Light-Deflection Raytracer ---
        if lowered in ("/lensing-status", "lensing-status"):
            if hasattr(self.runtime, "lensing_caustic_tracer"):
                st = self.runtime.lensing_caustic_tracer.get_status()
                msg = (
                    f"Gravitational Lensing Tracer: Lens Mass={st['lens_mass_solar']:.1e} M_sun, "
                    f"Einstein Radius={st['einstein_radius_arcsec']:.4f} arcsec ({st['einstein_radius_kpc']:.2f} kpc), Simulations={st['total_raytrace_simulations']}."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("Gravitational Lensing tracer not initialized.")

        if lowered in ("/lensing-einstein", "lensing-einstein"):
            if hasattr(self.runtime, "lensing_caustic_tracer"):
                res = self.runtime.lensing_caustic_tracer.compute_einstein_radius()
                msg = (
                    f"Einstein Ring Radius: theta_E={res['theta_e_arcsec']:.4f} arcsec "
                    f"({res['theta_e_rad']:.2e} rad), Physical Radius={res['einstein_radius_kpc']:.2f} kpc, R_s={res['schwarzschild_radius_m']:.2e} m."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Gravitational Lensing tracer not initialized.")

        if lowered.startswith("/lensing-images ") or lowered.startswith("lensing-images "):
            if hasattr(self.runtime, "lensing_caustic_tracer"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    beta_val = float(parts[1])
                    res = self.runtime.lensing_caustic_tracer.solve_image_positions(source_pos_arcsec=beta_val)
                    msg = (
                        f"Lensed Images (beta={beta_val} arcsec): theta_+={res['image_plus_arcsec']:.4f} (mu_+={res['magnification_plus']:.2f}), "
                        f"theta_-={res['image_minus_arcsec']:.4f} (mu_-={res['magnification_minus']:.2f}), Total Mag={res['magnification_total']:.2f}x."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /lensing-images <source_beta_arcsec>")

        if lowered.startswith("/lensing-time-delay ") or lowered.startswith("lensing-time-delay "):
            if hasattr(self.runtime, "lensing_caustic_tracer"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    beta_val = float(parts[1])
                    res = self.runtime.lensing_caustic_tracer.compute_relative_time_delay(source_pos_arcsec=beta_val)
                    msg = (
                        f"Lensing Time Delay (beta={beta_val} arcsec): Delta_t={res['time_delay_days']:.2f} days "
                        f"({res['time_delay_seconds']:.2e} s, Geometric Fraction={res['geometric_component_fraction']:.2f})."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /lensing-time-delay <source_beta_arcsec>")

        # --- Stage 276: Quantum Teleportation Entanglement Swapping & Multipartite GHZ-W State Repeater Fabric ---
        if lowered in ("/teleport-status", "teleport-status"):
            if hasattr(self.runtime, "quantum_repeater_fabric"):
                st = self.runtime.quantum_repeater_fabric.get_status()
                msg = (
                    f"Quantum Teleportation & Repeater Fabric: Channel Fidelity={st['default_channel_fidelity']}, "
                    f"Swapped Repeater Fidelity={st['swapped_repeater_fidelity']:.4f}, Non-locality={st['chsh_violation_possible']}."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("Quantum Repeater Fabric not initialized.")

        if lowered.startswith("/teleport-state ") or lowered.startswith("teleport-state "):
            if hasattr(self.runtime, "quantum_repeater_fabric"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    a_val = float(parts[1])
                    b_val = float(parts[2])
                    bsm = parts[3] if len(parts) >= 4 else "00"
                    res = self.runtime.quantum_repeater_fabric.execute_teleportation_protocol(
                        alpha=complex(a_val, 0.0), beta=complex(b_val, 0.0), measured_bsm=bsm
                    )
                    msg = (
                        f"Teleported |psi> = {res['input_state']} -> BSM='{res['bsm_outcome']}', "
                        f"Correction='{res['applied_correction']}', Fidelity={res['fidelity']*100:.2f}%."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /teleport-state <alpha_r> <beta_r> [bsm_bits_00_01_10_11]")

        if lowered.startswith("/swap-entanglement") or lowered.startswith("swap-entanglement"):
            if hasattr(self.runtime, "quantum_repeater_fabric"):
                parts = raw_text.strip().split()
                f1 = float(parts[1]) if len(parts) >= 2 else None
                f2 = float(parts[2]) if len(parts) >= 3 else None
                res = self.runtime.quantum_repeater_fabric.execute_entanglement_swapping(link_1_fidelity=f1, link_2_fidelity=f2)
                msg = (
                    f"Entanglement Swapping: Swapped Fidelity={res['swapped_fidelity']:.4f}, "
                    f"CHSH S-Parameter={res['chsh_s_parameter']:.3f} (Violates Local Realism: {res['quantum_nonlocality_verified']})."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /swap-entanglement [f1] [f2]")

        if lowered.startswith("/multipartite-state ") or lowered.startswith("multipartite-state "):
            if hasattr(self.runtime, "quantum_repeater_fabric"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    st_type = parts[1].upper()
                    n_q = int(parts[2]) if len(parts) >= 3 else 3
                    lost_idx = int(parts[3]) if len(parts) >= 4 else None
                    res = self.runtime.quantum_repeater_fabric.synthesize_multipartite_state(
                        state_type=st_type, num_qubits=n_q, qubit_loss_index=lost_idx
                    )
                    msg = (
                        f"Multipartite {st_type} (N={n_q}, Loss={lost_idx}): Residual Concurrence={res['residual_entanglement_concurrence']:.2f}, "
                        f"Robustness={res['loss_robustness']}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /multipartite-state <GHZ|W> [num_qubits] [lost_qubit_idx]")

        # --- Stage 277: Autonomous Non-Linear Soliton Korteweg-de Vries (KdV) Integrable Wave Synthesizer ---
        if lowered in ("/kdv-status", "kdv-status"):
            if hasattr(self.runtime, "kdv_soliton_synthesizer"):
                st = self.runtime.kdv_soliton_synthesizer.get_status()
                msg = (
                    f"KdV Soliton Synthesizer: Grid Points={st['grid_points']}, "
                    f"Mass I1={st['canonical_mass_i1']:.4f}, Energy I2={st['canonical_energy_i2']:.4f}, Syntheses={st['total_syntheses']}."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("KdV Soliton Synthesizer not initialized.")

        if lowered.startswith("/kdv-1soliton ") or lowered.startswith("kdv-1soliton "):
            if hasattr(self.runtime, "kdv_soliton_synthesizer"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    k_val = float(parts[1])
                    t_val = float(parts[2]) if len(parts) >= 3 else 0.0
                    x0 = float(parts[3]) if len(parts) >= 4 else 0.0
                    res = self.runtime.kdv_soliton_synthesizer.evaluate_1_soliton(kappa=k_val, t=t_val, x_0=x0)
                    msg = (
                        f"KdV 1-Soliton (kappa={k_val}, t={t_val}): Amplitude={res['peak_amplitude']:.4f}, "
                        f"Speed={res['soliton_speed']:.4f}, Mass I1={res['exact_mass_i1']:.4f}, Energy I2={res['exact_energy_i2']:.4f}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /kdv-1soliton <kappa> [t] [x0]")

        if lowered.startswith("/kdv-2soliton ") or lowered.startswith("kdv-2soliton "):
            if hasattr(self.runtime, "kdv_soliton_synthesizer"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    k1 = float(parts[1])
                    k2 = float(parts[2])
                    t_val = float(parts[3]) if len(parts) >= 4 else 0.0
                    res = self.runtime.kdv_soliton_synthesizer.evaluate_2_soliton_collision(kappa_1=k1, kappa_2=k2, t=t_val)
                    msg = (
                        f"KdV 2-Soliton Collision (k1={k1}, k2={k2}, t={t_val}): Coupling A12={res['interaction_coupling_a12']:.5f}, "
                        f"Phase Shifts: delta1={res['phase_shift_1']:.3f}, delta2={res['phase_shift_2']:.3f}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /kdv-2soliton <kappa1> <kappa2> [t]")

        if lowered.startswith("/kdv-invariants ") or lowered.startswith("kdv-invariants "):
            if hasattr(self.runtime, "kdv_soliton_synthesizer"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    k_val = float(parts[1])
                    sol = self.runtime.kdv_soliton_synthesizer.evaluate_1_soliton(kappa=k_val)
                    inv = self.runtime.kdv_soliton_synthesizer.compute_discrete_invariants(sol["profile"])
                    msg = f"KdV Invariants (kappa={k_val}): Discrete Mass I1={inv['mass_i1']:.4f}, Discrete Energy I2={inv['energy_i2']:.4f}."
                    return RouterResponse(msg, data={"analytical": sol, "discrete": inv})
            return RouterResponse("Usage: /kdv-invariants <kappa>")

        # --- Stage 278: Microscopic Casimir-Polder Vacuum Dispersion Force & Metamaterial Levitation Engine ---
        if lowered in ("/casimir-status", "casimir-status"):
            if hasattr(self.runtime, "casimir_vacuum_engine"):
                st = self.runtime.casimir_vacuum_engine.get_status()
                msg = (
                    f"Casimir-Polder Vacuum Engine: Plate Area={st['plate_area_m2']:.1e} m^2, "
                    f"P(100nm)={st['casimir_pressure_at_100nm_pa']:.3f} Pa, Levitation Tests={st['total_levitation_tests']}."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("Casimir Vacuum Engine not initialized.")

        if lowered.startswith("/casimir-ideal ") or lowered.startswith("casimir-ideal "):
            if hasattr(self.runtime, "casimir_vacuum_engine"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    d_nm = float(parts[1])
                    res = self.runtime.casimir_vacuum_engine.compute_ideal_casimir_pressure(separation_d_m=d_nm * 1e-9)
                    msg = (
                        f"Ideal Casimir Force (d={d_nm} nm): Pressure={res['pressure_pascal']:.4e} Pa, "
                        f"Force={res['force_newtons']:.4e} N ({res['force_sign']})."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /casimir-ideal <separation_nm>")

        if lowered.startswith("/casimir-polder ") or lowered.startswith("casimir-polder "):
            if hasattr(self.runtime, "casimir_vacuum_engine"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    d_nm = float(parts[1])
                    eps = float(parts[2]) if len(parts) >= 3 else 4.0
                    res = self.runtime.casimir_vacuum_engine.compute_casimir_polder_potential(distance_d_m=d_nm * 1e-9, surface_permittivity=eps)
                    msg = (
                        f"Casimir-Polder Atom Potential (d={d_nm} nm, eps={eps}): U={res['potential_ev']:.4e} eV "
                        f"({res['potential_joules']:.4e} J), Force={res['force_newtons']:.4e} N."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /casimir-polder <distance_nm> [permittivity]")

        if lowered.startswith("/casimir-levitate ") or lowered.startswith("casimir-levitate "):
            if hasattr(self.runtime, "casimir_vacuum_engine"):
                parts = raw_text.strip().split()
                if len(parts) >= 4:
                    e1, em, e2 = float(parts[1]), float(parts[2]), float(parts[3])
                    d_nm = float(parts[4]) if len(parts) >= 5 else 50.0
                    res = self.runtime.casimir_vacuum_engine.evaluate_repulsive_casimir_levitation(
                        eps_plate_1=e1, eps_fluid_medium=em, eps_plate_2=e2, separation_d_m=d_nm * 1e-9
                    )
                    msg = (
                        f"Quantum Levitation Check (eps1={e1}, em={em}, eps2={e2}): DLP Repulsive={res['dlp_condition_satisfied']}, "
                        f"Pressure={res['casimir_pressure_pa']:.2e} Pa, Net Force={res['net_force_n']:.2e} N, Stably Levitated={res['is_stably_levitated']}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /casimir-levitate <eps1> <eps_medium> <eps2> [separation_nm]")

        # --- Stage 279: Sovereign Decentralized Autonomous Zero-Knowledge Rollup & Verifiable State Compressor ---
        if lowered in ("/rollup-status", "rollup-status"):
            if hasattr(self.runtime, "zk_rollup_compressor"):
                st = self.runtime.zk_rollup_compressor.get_status()
                msg = (
                    f"ZK Rollup Compressor: Accounts={st['accounts_count']}, Supply={st['total_circulating_balance']:.2f}, "
                    f"State Root={st['current_state_root'][:16]}..., Batches Settled={st['total_batches_settled']}."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("ZK Rollup Compressor not initialized.")

        if lowered.startswith("/rollup-compress ") or lowered.startswith("rollup-compress "):
            if hasattr(self.runtime, "zk_rollup_compressor"):
                parts = raw_text.strip().split()
                if len(parts) >= 4:
                    f_id, t_id, amt = int(parts[1]), int(parts[2]), float(parts[3])
                    txs = [{"from": f_id, "to": t_id, "amount": amt, "nonce": 0}]
                    res = self.runtime.zk_rollup_compressor.compress_transaction_batch(txs)
                    msg = (
                        f"Rollup Compression: {res['uncompressed_bytes']}B -> {res['compressed_bytes']}B "
                        f"({res['compression_ratio']:.2f}x reduction), Hex: {res['compressed_payload_hex']}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /rollup-compress <from_id> <to_id> <amount>")

        if lowered.startswith("/rollup-settle ") or lowered.startswith("rollup-settle "):
            if hasattr(self.runtime, "zk_rollup_compressor"):
                parts = raw_text.strip().split()
                if len(parts) >= 4:
                    f_id, t_id, amt = int(parts[1]), int(parts[2]), float(parts[3])
                    txs = [{"from": f_id, "to": t_id, "amount": amt, "nonce": 0}]
                    res = self.runtime.zk_rollup_compressor.process_and_verify_rollup_batch(txs)
                    msg = (
                        f"Rollup Batch #{res['batch_id']} Settled: Valid={res['valid_transactions']}, "
                        f"Post-Root={res['post_state_root'][:16]}..., Proof={res['succinct_validity_proof'][:16]}... ({res['status']})."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /rollup-settle <from_id> <to_id> <amount>")

        if lowered in ("/rollup-root", "rollup-root"):
            if hasattr(self.runtime, "zk_rollup_compressor"):
                st = self.runtime.zk_rollup_compressor.get_status()
                msg = f"Current Sovereign Rollup State Root: {st['current_state_root']}."
                return RouterResponse(msg, data={"state_root": st['current_state_root']})
            return RouterResponse("ZK Rollup Compressor not initialized.")

        # --- Stage 280: The Sovereign Era 28 Master Seal & Omnipotent Astro-Topological Singularity Genesis ---
        if lowered in ("/era28-seal", "era28-seal", "/era28-seal-report", "era28-seal-report"):
            if hasattr(self.runtime, "era28_master_seal"):
                report = self.runtime.era28_master_seal.format_grand_era_report()
                st = self.runtime.era28_master_seal.status()
                return RouterResponse(report, data=st)
            return RouterResponse("Era 28 Master Seal not initialized.")

        if lowered in ("/era28-status", "era28-status"):
            if hasattr(self.runtime, "era28_master_seal"):
                st = self.runtime.era28_master_seal.status()
                msg = (
                    f"Era 28 Master Seal: Status={st['verification_status']}, Total Stages={st['total_stages_sealed']}, "
                    f"Master Merkle Root={st['master_merkle_root'][:16]}..., Genesis Sig={st['genesis_signature'][:16]}..."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("Era 28 Master Seal not initialized.")

        if lowered in ("/era28-verify", "era28-verify"):
            if hasattr(self.runtime, "era28_master_seal"):
                integ = self.runtime.era28_master_seal.verify_era28_integrity()
                msg = (
                    f"Era 28 Integrity Audit: Verified={integ['verified']}, Stages={integ['stages_verified']}/10, "
                    f"Operator={integ['sovereign_operator']}."
                )
                return RouterResponse(msg, data=integ)
            return RouterResponse("Era 28 Master Seal not initialized.")

        if lowered in ("/era28-manifest", "era28-manifest"):
            if hasattr(self.runtime, "era28_master_seal"):
                manifest = [r.to_dict() for r in self.runtime.era28_master_seal.get_stage_manifest()]
                msg = f"Era 28 Stage Manifest: {len(manifest)} modules verified operational."
                return RouterResponse(msg, data={"manifest": manifest})
            return RouterResponse("Era 28 Master Seal not initialized.")

        # --- Stage 281: Black Hole Holographic Thermodynamics & Bekenstein-Hawking Entropy Engine ---
        if lowered in ("/bh-status", "bh-status", "/black-hole-status", "black-hole-status"):
            if hasattr(self.runtime, "black_hole_thermodynamics"):
                tbl = self.runtime.black_hole_thermodynamics.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.black_hole_thermodynamics.status())
            return RouterResponse("Black Hole Thermodynamics Engine not initialized.")

        if lowered.startswith("/hawking-temp") or lowered.startswith("hawking-temp"):
            if hasattr(self.runtime, "black_hole_thermodynamics"):
                parts = text.split()
                m_sol = float(parts[1]) if len(parts) > 1 else 1.0
                res = self.runtime.black_hole_thermodynamics.calculate_schwarzschild(mass_solar=m_sol)
                msg = f"Hawking Temperature for {m_sol:.2e} M_sun: {res['hawking_temperature_k']:.4e} K (Horizon r_s={res['schwarzschild_radius_m']:.2e} m)"
                return RouterResponse(msg, data=res)
            return RouterResponse("Black Hole Thermodynamics Engine not initialized.")

        if lowered.startswith("/bh-entropy") or lowered.startswith("bh-entropy"):
            if hasattr(self.runtime, "black_hole_thermodynamics"):
                parts = text.split()
                m_sol = float(parts[1]) if len(parts) > 1 else 1.0
                res = self.runtime.black_hole_thermodynamics.calculate_schwarzschild(mass_solar=m_sol)
                msg = f"Bekenstein-Hawking Entropy for {m_sol:.2e} M_sun: S_BH/kB={res['dimensionless_entropy']:.4e} Planck units (Area={res['horizon_area_m2']:.4e} m^2)"
                return RouterResponse(msg, data=res)
            return RouterResponse("Black Hole Thermodynamics Engine not initialized.")

        if lowered.startswith("/page-curve") or lowered.startswith("page-curve"):
            if hasattr(self.runtime, "black_hole_thermodynamics"):
                parts = text.split()
                m_sol = float(parts[1]) if len(parts) > 1 else 1.0
                res = self.runtime.black_hole_thermodynamics.simulate_page_curve(mass_solar=m_sol, steps=20)
                msg = f"Unitary Page Curve simulated for {m_sol:.2e} M_sun: Page Time={res['page_time_s']:.4e} s, Points={res['total_points']}, Unitarity=PRESERVED."
                return RouterResponse(msg, data=res)
            return RouterResponse("Black Hole Thermodynamics Engine not initialized.")

        # --- Stage 282: Non-Hermitian PT-Symmetric Open Quantum Engine & Exceptional Point Sensor ---
        if lowered in ("/pt-status", "pt-status", "/pt-symmetric-status", "pt-symmetric-status"):
            if hasattr(self.runtime, "pt_symmetric_engine"):
                tbl = self.runtime.pt_symmetric_engine.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.pt_symmetric_engine.status())
            return RouterResponse("PT-Symmetric Quantum Engine not initialized.")

        if lowered.startswith("/pt-spectrum") or lowered.startswith("pt-spectrum"):
            if hasattr(self.runtime, "pt_symmetric_engine"):
                parts = text.split()
                gamma = float(parts[1]) if len(parts) > 1 else 0.5
                g = float(parts[2]) if len(parts) > 2 else 1.0
                res = self.runtime.pt_symmetric_engine.solve_dim2_spectrum(gain_loss_gamma=gamma, coupling_g=g)
                msg = (
                    f"PT Spectrum: Phase={res.pt_phase}, Gamma={res.gain_loss_gamma}, g={res.coupling_g}, "
                    f"EP Distance={res.ep_distance:.4e}, Boost={res.perturbation_sensitivity_gain:.2f}x"
                )
                return RouterResponse(msg, data=res.to_dict())
            return RouterResponse("PT-Symmetric Quantum Engine not initialized.")

        if lowered.startswith("/exceptional-point-detect") or lowered.startswith("exceptional-point-detect") or lowered.startswith("/ep-detect"):
            if hasattr(self.runtime, "pt_symmetric_engine"):
                parts = text.split()
                eps = float(parts[1]) if len(parts) > 1 else 1e-6
                order = int(parts[2]) if len(parts) > 2 else 2
                res = self.runtime.pt_symmetric_engine.evaluate_ep_sensor(perturbation_epsilon=eps, order=order)
                msg = (
                    f"EP-{res['order_n']} Sensor Detected: Epsilon={res['perturbation_epsilon']:.2e}, "
                    f"Splitting={res['ep_eigenvalue_splitting']:.4e}, Amp={res['amplification_factor']:.2e}x ({res['sensitivity_order']})"
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("PT-Symmetric Quantum Engine not initialized.")

        # --- Stage 283: Quantum Many-Body Scrambler & OTOC Fast Scrambler ---
        if lowered in ("/otoc-status", "otoc-status", "/scrambler-status", "scrambler-status"):
            if hasattr(self.runtime, "quantum_scrambler"):
                tbl = self.runtime.quantum_scrambler.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.quantum_scrambler.status())
            return RouterResponse("Quantum Scrambler Engine not initialized.")

        if lowered.startswith("/otoc-correlator") or lowered.startswith("otoc-correlator"):
            if hasattr(self.runtime, "quantum_scrambler"):
                parts = text.split()
                n = int(parts[1]) if len(parts) > 1 else 64
                temp = float(parts[2]) if len(parts) > 2 else 1.0
                res = self.runtime.quantum_scrambler.calculate_otoc_evolution(n_qubits=n, temperature_k=temp, steps=20)
                msg = (
                    f"OTOC Evolution (N={res['n_qubits']}, T={res['temperature_k']}K): "
                    f"Lyapunov={res['lyapunov_exponent']:.2e} Hz, t_*={res['scrambling_time_s']:.2e} s, Steps={res['total_steps']}"
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Quantum Scrambler Engine not initialized.")

        if lowered.startswith("/scrambling-time") or lowered.startswith("scrambling-time"):
            if hasattr(self.runtime, "quantum_scrambler"):
                parts = text.split()
                n = int(parts[1]) if len(parts) > 1 else 100
                temp = float(parts[2]) if len(parts) > 2 else 1.0
                res = self.runtime.quantum_scrambler.compute_scrambling_time(n_qubits=n, temperature_k=temp)
                msg = (
                    f"Fast Scrambling Time t_* for N={res['n_qubits']} at T={res['temperature_k']}K: "
                    f"{res['scrambling_time_s']:.4e} s (MSS Bound={res['mss_bound_hz']:.2e} Hz)"
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Quantum Scrambler Engine not initialized.")

        # --- Stage 284: CMB Multipole Power Spectrum & Inflationary Tensor Perturbation Engine ---
        if lowered in ("/cmb-status", "cmb-status", "/cmb-spectrum-status", "cmb-spectrum-status"):
            if hasattr(self.runtime, "cmb_power_spectrum"):
                tbl = self.runtime.cmb_power_spectrum.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.cmb_power_spectrum.status())
            return RouterResponse("CMB Power Spectrum Engine not initialized.")

        if lowered.startswith("/cmb-multipole") or lowered.startswith("cmb-multipole"):
            if hasattr(self.runtime, "cmb_power_spectrum"):
                parts = text.split()
                l_val = int(parts[1]) if len(parts) > 1 else 220
                d_l = self.runtime.cmb_power_spectrum.evaluate_multipole_d_l(l_val)
                msg = f"CMB Multipole l={l_val}: D_l = {d_l:.2f} uK^2 (Concordance Lambda-CDM)"
                return RouterResponse(msg, data={"multipole_l": l_val, "d_l_uK2": d_l})
            return RouterResponse("CMB Power Spectrum Engine not initialized.")

        if lowered.startswith("/inflation-tensor-ratio") or lowered.startswith("inflation-tensor-ratio") or lowered.startswith("/tensor-ratio"):
            if hasattr(self.runtime, "cmb_power_spectrum"):
                parts = text.split()
                r_val = float(parts[1]) if len(parts) > 1 else 0.03
                res = self.runtime.cmb_power_spectrum.compute_inflation_tensor_ratio(tensor_to_scalar_r=r_val)
                msg = (
                    f"Inflationary Tensor-to-Scalar Ratio r={res['tensor_to_scalar_r']}: "
                    f"Scale={res['inflation_energy_scale_gev']:.2e} GeV, Lyth Excursion={res['lyth_bound_delta_phi_planck']:.2f} M_Pl"
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("CMB Power Spectrum Engine not initialized.")

        # --- Stage 285: Quantum Zeno & Anti-Zeno Dynamic Measurement Controller ---
        if lowered in ("/zeno-status", "zeno-status", "/zeno-controller-status", "zeno-controller-status"):
            if hasattr(self.runtime, "zeno_controller"):
                tbl = self.runtime.zeno_controller.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.zeno_controller.status())
            return RouterResponse("Quantum Zeno Controller not initialized.")

        if lowered.startswith("/zeno-inhibit") or lowered.startswith("zeno-inhibit"):
            if hasattr(self.runtime, "zeno_controller"):
                parts = text.split()
                tau = float(parts[1]) if len(parts) > 1 else 1e-11
                t_tot = float(parts[2]) if len(parts) > 2 else 1e-9
                res = self.runtime.zeno_controller.simulate_zeno_inhibition(measurement_interval_tau_s=tau, total_time_s=t_tot)
                msg = (
                    f"Quantum Zeno Inhibition (tau={res['measurement_interval_tau_s']:.1e}s, N={res['number_of_measurements']}): "
                    f"P(t)={res['survival_probability']:.4f} (Natural={res['natural_decay_probability']:.4f}, Ratio={res['decay_suppression_ratio']:.2e})"
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Quantum Zeno Controller not initialized.")

        if lowered.startswith("/anti-zeno-accelerate") or lowered.startswith("anti-zeno-accelerate"):
            if hasattr(self.runtime, "zeno_controller"):
                parts = text.split()
                tau = float(parts[1]) if len(parts) > 1 else 1e-10
                res = self.runtime.zeno_controller.simulate_anti_zeno_regime(measurement_interval_tau_s=tau)
                msg = (
                    f"Quantum Anti-Zeno Acceleration (tau={res['measurement_interval_tau_s']:.1e}s): "
                    f"Regime={res['regime']}, Rate Ratio Gamma_eff/Gamma_0 = {res['decay_ratio_gamma_eff_over_gamma_0']:.2f}x"
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Quantum Zeno Controller not initialized.")

        # --- Stage 286: Topological Majorana Zero-Mode Braiding & Parity-Protected Qubit Gate ---
        if lowered in ("/majorana-status", "majorana-status", "/mzm-status", "mzm-status"):
            if hasattr(self.runtime, "majorana_gate"):
                tbl = self.runtime.majorana_gate.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.majorana_gate.status())
            return RouterResponse("Majorana Gate Engine not initialized.")

        if lowered.startswith("/majorana-braid") or lowered.startswith("majorana-braid") or lowered.startswith("/mzm-braid"):
            if hasattr(self.runtime, "majorana_gate"):
                parts = text.split()
                i = int(parts[1]) if len(parts) > 1 else 0
                j = int(parts[2]) if len(parts) > 2 else 1
                res = self.runtime.majorana_gate.apply_braid(i, j)
                if "error" in res:
                    return RouterResponse(res["error"])
                msg = f"Majorana Braid {res['braid_operation']} Applied: Total Braids={res['braid_count']}, Parity={res['fermion_parity']} (Fault-Tolerant)"
                return RouterResponse(msg, data=res)
            return RouterResponse("Majorana Gate Engine not initialized.")

        if lowered.startswith("/majorana-parity") or lowered.startswith("majorana-parity") or lowered.startswith("/mzm-parity"):
            if hasattr(self.runtime, "majorana_gate"):
                res = self.runtime.majorana_gate.measure_fermion_parity()
                msg = f"Topological Fermion Parity: Eigenvalue={res['parity_eigenvalue']}, State={res['logical_state']} (Poisoning Protected)"
                return RouterResponse(msg, data=res)
            return RouterResponse("Majorana Gate Engine not initialized.")

        # --- Stage 287: Pulsar Magnetosphere Relativistic Force-Free Electrodynamics (FFE) Simulator ---
        if lowered in ("/pulsar-ffe-status", "pulsar-ffe-status", "/pulsar-status", "pulsar-status"):
            if hasattr(self.runtime, "pulsar_ffe_engine"):
                tbl = self.runtime.pulsar_ffe_engine.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.pulsar_ffe_engine.status())
            return RouterResponse("Pulsar FFE Engine not initialized.")

        if lowered.startswith("/goldreich-julian") or lowered.startswith("goldreich-julian") or lowered.startswith("/gj-density"):
            if hasattr(self.runtime, "pulsar_ffe_engine"):
                parts = text.split()
                p = float(parts[1]) if len(parts) > 1 else 0.03339
                b_g = float(parts[2]) if len(parts) > 2 else 3.8e12
                res = self.runtime.pulsar_ffe_engine.calculate_pulsar_parameters(period_s=p, b_surface_gauss=b_g)
                msg = (
                    f"Goldreich-Julian Density for P={p}s: rho_GJ={res['goldreich_julian_density_c_m3']:.2e} C/m^3, "
                    f"n_GJ={res['goldreich_julian_number_density_m3']:.2e} m^-3 (R_LC={res['light_cylinder_radius_m']:.2e} m)"
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Pulsar FFE Engine not initialized.")

        if lowered.startswith("/pulsar-spindown") or lowered.startswith("pulsar-spindown"):
            if hasattr(self.runtime, "pulsar_ffe_engine"):
                parts = text.split()
                p = float(parts[1]) if len(parts) > 1 else 0.03339
                p_dot = float(parts[2]) if len(parts) > 2 else 4.21e-13
                res = self.runtime.pulsar_ffe_engine.calculate_pulsar_parameters(period_s=p, period_derivative=p_dot)
                msg = (
                    f"Pulsar Spin-Down (P={p}s, P_dot={p_dot:.2e}): E_dot={res['spindown_luminosity_watts']:.2e} W, "
                    f"Age={res['characteristic_age_years']:.1f} yrs, B_0={res['surface_b_field_tesla']:.2e} T"
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Pulsar FFE Engine not initialized.")

        # --- Stage 288: Quantum Optic Phase Estimator & Quantum Fisher Information Engine ---
        if lowered in ("/fisher-status", "fisher-status", "/qfi-status", "qfi-status"):
            if hasattr(self.runtime, "fisher_phase_estimator"):
                tbl = self.runtime.fisher_phase_estimator.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.fisher_phase_estimator.status())
            return RouterResponse("Quantum Fisher Phase Estimator not initialized.")

        if lowered.startswith("/heisenberg-limit") or lowered.startswith("heisenberg-limit") or lowered.startswith("/hl-eval"):
            if hasattr(self.runtime, "fisher_phase_estimator"):
                parts = text.split()
                photons = float(parts[1]) if len(parts) > 1 else 100.0
                st_type = parts[2] if len(parts) > 2 else "N00N"
                res = self.runtime.fisher_phase_estimator.calculate_quantum_fisher_info(mean_photons=photons, state_type=st_type)
                msg = (
                    f"QFI Metrology ({res['state_type']}, N={res['mean_photon_number']}): "
                    f"Delta_phi={res['cramer_rao_bound_radians']:.4e} rad, F_Q={res['quantum_fisher_info']:.2e}, "
                    f"Advantage={res['quantum_advantage_ratio']:.2f}x over SQL"
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Quantum Fisher Phase Estimator not initialized.")

        if lowered.startswith("/noon-phase-eval") or lowered.startswith("noon-phase-eval") or lowered.startswith("/noon-fringes"):
            if hasattr(self.runtime, "fisher_phase_estimator"):
                parts = text.split()
                phi = float(parts[1]) if len(parts) > 1 else 0.5
                n = int(parts[2]) if len(parts) > 2 else 8
                res = self.runtime.fisher_phase_estimator.simulate_mach_zehnder_fringes(true_phase_rad=phi, n_photons=n, state_type="N00N")
                msg = (
                    f"N00N State Super-Resolution (N={res['photon_number_n']}): "
                    f"Transmission at phi={phi:.3f} rad is {res['transmission_at_true_phase']:.4f} (Finesse Multiplier={res['fringe_finesse_multiplier']:.1f}x)"
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Quantum Fisher Phase Estimator not initialized.")

        # --- Stage 289: Sovereign Cross-Chain State Relayer & ZK Merkle Bridge ---
        if lowered in ("/zk-bridge-status", "zk-bridge-status", "/cross-chain-status", "cross-chain-status"):
            if hasattr(self.runtime, "cross_chain_zk_bridge"):
                tbl = self.runtime.cross_chain_zk_bridge.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.cross_chain_zk_bridge.status())
            return RouterResponse("Cross-Chain ZK Bridge not initialized.")

        if lowered.startswith("/relay-header") or lowered.startswith("relay-header"):
            if hasattr(self.runtime, "cross_chain_zk_bridge"):
                parts = text.split()
                if len(parts) < 5:
                    return RouterResponse("Usage: /relay-header <chain_id> <height> <prev_hash> <state_root>")
                cid = parts[1]
                h = int(parts[2])
                p_hash = parts[3]
                s_root = parts[4]
                res = self.runtime.cross_chain_zk_bridge.relay_header(chain_id=cid, height=h, prev_hash=p_hash, state_root=s_root)
                if "error" in res:
                    return RouterResponse(res["error"])
                msg = f"Header Relayed for {res['chain_id']} at height {res['height']}: Block Hash={res['block_hash'][:16]}..."
                return RouterResponse(msg, data=res)
            return RouterResponse("Cross-Chain ZK Bridge not initialized.")

        if lowered.startswith("/verify-inclusion") or lowered.startswith("verify-inclusion") or lowered.startswith("/bridge-transfer"):
            if hasattr(self.runtime, "cross_chain_zk_bridge"):
                parts = text.split()
                src = parts[1] if len(parts) > 1 else "LUCY-CORE-01"
                tgt = parts[2] if len(parts) > 2 else "LUCY-ROLLUP-02"
                rcp = parts[3] if len(parts) > 3 else "RCP-DEFAULT-001"
                null = hashlib.sha256(f"NULL-{rcp}-{time.time()}".encode()).hexdigest()
                res = self.runtime.cross_chain_zk_bridge.verify_and_settle_transfer(
                    source_chain=src,
                    target_chain=tgt,
                    receipt_id=rcp,
                    payload={"action": "INTER_CHAIN_STATE_SYNC", "timestamp": time.time()},
                    merkle_proof=[],
                    nullifier=null,
                )
                if "error" in res:
                    return RouterResponse(res["error"])
                msg = f"Cross-Chain State Transfer #{res['receipt_id']} Settled: {src} -> {tgt} (Nullifier={res['nullifier_spent'][:16]}...)"
                return RouterResponse(msg, data=res)
            return RouterResponse("Cross-Chain ZK Bridge not initialized.")

        # --- Stage 290: The Sovereign Era 29 Master Seal & Omniscient Trans-Cosmic Singularity Genesis ---
        if lowered in ("/era29-seal", "era29-seal", "/era29-seal-report", "era29-seal-report"):
            if hasattr(self.runtime, "era29_master_seal"):
                report = self.runtime.era29_master_seal.format_grand_era_report()
                st = self.runtime.era29_master_seal.status()
                return RouterResponse(report, data=st)
            return RouterResponse("Era 29 Master Seal not initialized.")

        if lowered in ("/era29-status", "era29-status"):
            if hasattr(self.runtime, "era29_master_seal"):
                st = self.runtime.era29_master_seal.status()
                msg = (
                    f"Era 29 Master Seal: Status={st['verification_status']}, Total Stages={st['total_stages_sealed']}, "
                    f"Master Merkle Root={st['master_merkle_root'][:16]}..., Genesis Sig={st['genesis_signature'][:16]}..."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("Era 29 Master Seal not initialized.")

        if lowered in ("/era29-verify", "era29-verify"):
            if hasattr(self.runtime, "era29_master_seal"):
                integ = self.runtime.era29_master_seal.verify_era29_integrity()
                msg = (
                    f"Era 29 Integrity Audit: Verified={integ['verified']}, Stages={integ['stages_verified']}/10, "
                    f"Operator={integ['sovereign_operator']}."
                )
                return RouterResponse(msg, data=integ)
            return RouterResponse("Era 29 Master Seal not initialized.")

        if lowered in ("/era29-manifest", "era29-manifest"):
            if hasattr(self.runtime, "era29_master_seal"):
                manifest = [r.to_dict() for r in self.runtime.era29_master_seal.get_stage_manifest()]
                msg = f"Era 29 Stage Manifest: {len(manifest)} modules verified operational."
                return RouterResponse(msg, data={"manifest": manifest})
            return RouterResponse("Era 29 Master Seal not initialized.")

        # Stage 220: Era 22 Sovereign Master Seal & Galactic Hyper-Mesh Genesis
        if lowered in {"/era22-seal", "era22-seal", "/galactic-hyper-mesh-seal", "galactic-hyper-mesh-seal"}:
            if hasattr(self.runtime, "era22_master_seal"):
                tbl = self.runtime.era22_master_seal.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.era22_master_seal.status())

        if lowered in {"/era22-audit", "era22-audit", "/galactic-audit", "galactic-audit"}:
            if hasattr(self.runtime, "era22_master_seal"):
                report = self.runtime.era22_master_seal.format_grand_era_report()
                return RouterResponse(report, data=self.runtime.era22_master_seal.status())

        # Stage 219: Concept Synthesis & Ontology Evolution Engine (Era 22)
        if lowered in {"/ontology-status", "ontology-status", "/concept-status", "concept-status"}:
            if hasattr(self.runtime, "ontology_engine"):
                tbl = self.runtime.ontology_engine.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.ontology_engine.status())

        if lowered.startswith("/concept-add ") or lowered.startswith("concept-add "):
            prefix = "/concept-add " if lowered.startswith("/concept-add ") else "concept-add "
            parts = text[len(prefix):].strip().split(maxsplit=1)
            if len(parts) >= 1 and hasattr(self.runtime, "ontology_engine"):
                name = parts[0]
                cat = parts[1] if len(parts) > 1 else "entity"
                node = self.runtime.ontology_engine.add_concept(name, category=cat)
                msg = f"[Ontology Engine]: Registered concept '{name}' ({node.concept_id}) in category '{cat}'."
                return RouterResponse(msg, data=node.to_dict())

        if lowered.startswith("/concept-synthesize ") or lowered.startswith("concept-synthesize "):
            prefix = "/concept-synthesize " if lowered.startswith("/concept-synthesize ") else "concept-synthesize "
            parts = text[len(prefix):].strip().split()
            if len(parts) >= 2 and hasattr(self.runtime, "ontology_engine"):
                meta_name = parts[0]
                cluster_ids = parts[1:]
                meta_node = self.runtime.ontology_engine.synthesize_higher_order_concept(cluster_ids, meta_name)
                msg = f"[Ontology Engine]: Synthesized meta-concept '{meta_name}' ({meta_node.concept_id}) over {len(cluster_ids)} concepts."
                return RouterResponse(msg, data=meta_node.to_dict())

        # Stage 218: Trans-Universal Belief Propagation Mesh (Era 22)
        if lowered in {"/belief-mesh-status", "belief-mesh-status", "/lbp-status", "lbp-status"}:
            if hasattr(self.runtime, "belief_mesh"):
                tbl = self.runtime.belief_mesh.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.belief_mesh.status())

        if lowered in {"/belief-infer", "belief-infer"}:
            if hasattr(self.runtime, "belief_mesh"):
                # Initialize default 2-node consensus graph if empty
                if not self.runtime.belief_mesh.variables:
                    self.runtime.belief_mesh.add_variable("node_earth", 2, prior=[0.8, 0.2])
                    self.runtime.belief_mesh.add_variable("node_mars", 2, prior=[0.5, 0.5])
                    self.runtime.belief_mesh.add_factor(
                        "consensus_link", ["node_earth", "node_mars"],
                        {(0, 0): 0.9, (0, 1): 0.1, (1, 0): 0.1, (1, 1): 0.9}
                    )
                beliefs = self.runtime.belief_mesh.run_inference(max_iterations=10)
                msg = f"[Belief Propagation Mesh]: LBP consensus convergence reached. Posterior beliefs: {beliefs}."
                return RouterResponse(msg, data={"beliefs": beliefs})

        # Stage 217: Chaos Fault-Injection & Resilience Engine (Era 22)
        if lowered in {"/chaos-status", "chaos-status", "/fault-status", "fault-status"}:
            if hasattr(self.runtime, "chaos_engine"):
                tbl = self.runtime.chaos_engine.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.chaos_engine.status())

        if lowered in {"/chaos-campaign", "chaos-campaign"}:
            if hasattr(self.runtime, "chaos_engine"):
                res = self.runtime.chaos_engine.run_chaos_campaign(["kernel_bus", "quantum_coprocessor", "dtn_router"])
                msg = f"[Chaos Engine]: Campaign complete. Resilience Score: {res['resilience_score']} ({res['total_experiments']} tests run)."
                return RouterResponse(msg, data=res)

        if lowered.startswith("/chaos-inject ") or lowered.startswith("chaos-inject "):
            prefix = "/chaos-inject " if lowered.startswith("/chaos-inject ") else "chaos-inject "
            parts = text[len(prefix):].strip().split(maxsplit=1)
            if len(parts) >= 2 and hasattr(self.runtime, "chaos_engine"):
                ft_str, tgt = parts[0].upper(), parts[1]
                from backend.lucy_core.chaos_fault_injection import FaultType
                ft = getattr(FaultType, ft_str, FaultType.LATENCY_SPIKE)
                exp = self.runtime.chaos_engine.inject_fault(ft, tgt)
                msg = f"[Chaos Engine]: Injected fault '{ft.value}' into target '{tgt}' (ID: {exp.experiment_id})."
                return RouterResponse(msg, data=exp.to_dict())

        # Stage 216: Quantum Hybrid Coprocessor & VQE Engine (Era 22)
        if lowered in {"/quantum-coprocessor-status", "quantum-coprocessor-status", "/vqe-status", "vqe-status"}:
            if hasattr(self.runtime, "quantum_coprocessor"):
                tbl = self.runtime.quantum_coprocessor.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.quantum_coprocessor.status())

        if lowered in {"/vqe-run", "vqe-run"}:
            if hasattr(self.runtime, "quantum_coprocessor"):
                from backend.lucy_core.quantum_hybrid_coprocessor import PauliTerm
                hamiltonian = [PauliTerm(coeff=-1.0, pauli_string="ZZ")]
                res = self.runtime.quantum_coprocessor.run_vqe(hamiltonian, max_iterations=10)
                msg = f"[Quantum Co-Processor]: VQE ground-state optimization complete. E0: {res.ground_state_energy:.4f} (Optimal params: {res.optimal_parameters})."
                return RouterResponse(msg, data=res.to_dict())

        # Stage 215: Async Micro-Actor Mesh Fabric (Era 22)
        if lowered in {"/actor-mesh-status", "actor-mesh-status", "/micro-actor-status", "micro-actor-status"}:
            if hasattr(self.runtime, "micro_actor_mesh"):
                tbl = self.runtime.micro_actor_mesh.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.micro_actor_mesh.status())

        if lowered.startswith("/actor-spawn ") or lowered.startswith("actor-spawn "):
            prefix = "/actor-spawn " if lowered.startswith("/actor-spawn ") else "actor-spawn "
            aid = text[len(prefix):].strip()
            if hasattr(self.runtime, "micro_actor_mesh"):
                actor = self.runtime.micro_actor_mesh.spawn_actor(aid)
                msg = f"[Micro-Actor Mesh]: Spawned autonomous actor '{aid}' with active supervision."
                return RouterResponse(msg, data={"actor_id": aid, "status": actor.status.value})

        if lowered.startswith("/actor-send ") or lowered.startswith("actor-send "):
            prefix = "/actor-send " if lowered.startswith("/actor-send ") else "actor-send "
            parts = text[len(prefix):].strip().split(maxsplit=2)
            if len(parts) >= 2 and hasattr(self.runtime, "micro_actor_mesh"):
                tgt, act = parts[0], parts[1]
                payload = parts[2] if len(parts) > 2 else {}
                m = self.runtime.micro_actor_mesh.send_message(tgt, act, payload)
                msg = f"[Micro-Actor Mesh]: Dispatched message '{m.message_id}' (Action: {act}) to target '{tgt}'."
                return RouterResponse(msg, data=m.to_dict())

        if lowered in {"/actor-step", "actor-step"}:
            if hasattr(self.runtime, "micro_actor_mesh"):
                results = self.runtime.micro_actor_mesh.step_scheduler()
                msg = f"[Micro-Actor Mesh]: Scheduler execution cycle complete. Actor outputs: {results}."
                return RouterResponse(msg, data={"results": results})

        # Stage 214: Holographic Associative Memory Fabric (Era 22)
        if lowered in {"/hcam-status", "hcam-status", "/holographic-status", "holographic-status"}:
            if hasattr(self.runtime, "holographic_memory"):
                tbl = self.runtime.holographic_memory.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.holographic_memory.status())

        if lowered.startswith("/hcam-store ") or lowered.startswith("hcam-store "):
            prefix = "/hcam-store " if lowered.startswith("/hcam-store ") else "hcam-store "
            parts = text[len(prefix):].strip().split(maxsplit=1)
            if len(parts) >= 2 and hasattr(self.runtime, "holographic_memory"):
                k, v = parts[0], parts[1]
                p = self.runtime.holographic_memory.store_page(k, v)
                msg = f"[Holographic CAM]: Encoded memory '{k}' into optical interference volume (Page: {p.page_id})."
                return RouterResponse(msg, data=p.to_dict())

        if lowered.startswith("/hcam-recall ") or lowered.startswith("hcam-recall "):
            prefix = "/hcam-recall " if lowered.startswith("/hcam-recall ") else "hcam-recall "
            query = text[len(prefix):].strip()
            if hasattr(self.runtime, "holographic_memory"):
                matches = self.runtime.holographic_memory.associative_recall(query, correlation_threshold=0.5)
                res_summary = [{"key": m[0].key, "corr": m[1], "data": m[0].associated_data} for m in matches]
                msg = f"[Holographic CAM]: Associative phase correlation for '{query}' returned {len(matches)} matches: {res_summary}."
                return RouterResponse(msg, data={"matches": res_summary})

        # Stage 213: Tensor-Train Decomposer Engine (Era 22)
        if lowered in {"/tensor-train-status", "tensor-train-status", "/mps-status", "mps-status"}:
            if hasattr(self.runtime, "tensor_train_engine"):
                tbl = self.runtime.tensor_train_engine.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.tensor_train_engine.status())

        if lowered.startswith("/tt-create ") or lowered.startswith("tt-create "):
            prefix = "/tt-create " if lowered.startswith("/tt-create ") else "tt-create "
            raw_dims = text[len(prefix):].strip().split()
            if hasattr(self.runtime, "tensor_train_engine"):
                try:
                    dims = [int(d) for d in raw_dims] if raw_dims else [2, 2, 2]
                except ValueError:
                    dims = [2, 2, 2]
                tt = self.runtime.tensor_train_engine.create_canonical_rank1_tt(dims)
                msg = f"[Tensor-Train Engine]: Created canonical rank-1 TT with dims {dims}. Frobenius norm: {tt.frobenius_norm():.4f}."
                return RouterResponse(msg, data={"mode_dimensions": dims, "ranks": tt.ranks, "norm": tt.frobenius_norm()})

        # Stage 212: Interplanetary DTN Routing Fabric (Era 22)
        if lowered in {"/dtn-status", "dtn-status", "/interplanetary-status", "interplanetary-status"}:
            if hasattr(self.runtime, "interplanetary_dtn"):
                tbl = self.runtime.interplanetary_dtn.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.interplanetary_dtn.status())

        if lowered.startswith("/dtn-bundle ") or lowered.startswith("dtn-bundle "):
            prefix = "/dtn-bundle " if lowered.startswith("/dtn-bundle ") else "dtn-bundle "
            parts = text[len(prefix):].strip().split(maxsplit=1)
            if len(parts) >= 2 and hasattr(self.runtime, "interplanetary_dtn"):
                dest, payload = parts[0], parts[1]
                b = self.runtime.interplanetary_dtn.create_bundle(dest, payload)
                msg = f"[Interplanetary DTN]: Injected bundle '{b.bundle_id}' targeting '{dest}' into custody buffer."
                return RouterResponse(msg, data=b.to_dict())

        if lowered in {"/dtn-step", "dtn-step"}:
            if hasattr(self.runtime, "interplanetary_dtn"):
                forwarded = self.runtime.interplanetary_dtn.route_step()
                msg = f"[Interplanetary DTN]: Routing step executed. Forwarded bundles: {forwarded}."
                return RouterResponse(msg, data={"forwarded_bundles": forwarded})

        # Stage 211: Photonic Matrix Multiplier Fabric (Era 22)
        if lowered in {"/photonic-status", "photonic-status", "/mzi-status", "mzi-status"}:
            if hasattr(self.runtime, "photonic_matrix_multiplier"):
                tbl = self.runtime.photonic_matrix_multiplier.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.photonic_matrix_multiplier.status())

        if lowered.startswith("/photonic-propagate ") or lowered.startswith("photonic-propagate "):
            prefix = "/photonic-propagate " if lowered.startswith("/photonic-propagate ") else "photonic-propagate "
            raw_vals = text[len(prefix):].strip().split()
            if hasattr(self.runtime, "photonic_matrix_multiplier"):
                try:
                    vec = [float(v) for v in raw_vals]
                except ValueError:
                    vec = [1.0, 0.0]
                sig = self.runtime.photonic_matrix_multiplier.propagate_signal(vec)
                intensities = [round(i, 4) for i in sig.intensities()]
                msg = f"[Photonic Compute]: Optical propagation complete. Detected power intensities: {intensities}."
                return RouterResponse(msg, data={"intensities": intensities})

        # Stage 210: Era 21 Sovereign Master Seal & Hyper-Federation Genesis
        if lowered in {"/era21-seal", "era21-seal", "/hyper-federation-seal", "hyper-federation-seal"}:
            if hasattr(self.runtime, "era21_master_seal"):
                tbl = self.runtime.era21_master_seal.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.era21_master_seal.status())

        if lowered in {"/era21-audit", "era21-audit", "/hyper-federation-audit", "hyper-federation-audit"}:
            if hasattr(self.runtime, "era21_master_seal"):
                report = self.runtime.era21_master_seal.format_grand_era_report()
                return RouterResponse(report, data=self.runtime.era21_master_seal.status())

        # Stage 209: Hyper-Scale Cluster Mesh Synchronizer (Era 21)
        if lowered in {"/cluster-mesh-status", "cluster-mesh-status", "/mesh-sync-status", "mesh-sync-status"}:
            if hasattr(self.runtime, "hyperscale_mesh"):
                tbl = self.runtime.hyperscale_mesh.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.hyperscale_mesh.status())

        if lowered.startswith("/cluster-sync ") or lowered.startswith("cluster-sync "):
            prefix = "/cluster-sync " if lowered.startswith("/cluster-sync ") else "cluster-sync "
            parts = text[len(prefix):].strip().split()
            if len(parts) >= 2 and hasattr(self.runtime, "hyperscale_mesh"):
                src, tgt = parts[0], parts[1]
                count, keys = self.runtime.hyperscale_mesh.anti_entropy_sync(src, tgt)
                msg = f"[Cluster Mesh Synchronizer]: Synchronized clusters '{src}' and '{tgt}'. Reconciled {count} keys: {keys}."
                return RouterResponse(msg, data={"reconciled_count": count, "reconciled_keys": keys})

        # Stage 208: Multi-Modal Symbolic Grounding Fabric (Era 21)
        if lowered in {"/grounding-status", "grounding-status", "/symbolic-grounding-status", "symbolic-grounding-status"}:
            if hasattr(self.runtime, "multimodal_grounding"):
                tbl = self.runtime.multimodal_grounding.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.multimodal_grounding.status())

        if lowered.startswith("/grounding-query ") or lowered.startswith("grounding-query "):
            prefix = "/grounding-query " if lowered.startswith("/grounding-query ") else "grounding-query "
            lbl = text[len(prefix):].strip()
            if hasattr(self.runtime, "multimodal_grounding"):
                matches = self.runtime.multimodal_grounding.query_grounded_symbol(lbl)
                msg = f"[Symbolic Grounding]: Resolved {len(matches)} matching grounded entities for '{lbl}'."
                return RouterResponse(msg, data={"matches_count": len(matches), "entities": [m[0].to_dict() for m in matches]})

        # Stage 106: Offline Multi-Modal Voice Fabric
        if lowered in {"/voice-status", "voice-status"}:
            if hasattr(self.runtime, "voice_fabric"):
                return RouterResponse(self.runtime.voice_fabric.voice_status(), data=self.runtime.voice_fabric.status())

        if lowered.startswith("/voice-speak ") or lowered.startswith("voice-speak "):
            prefix = "/voice-speak " if lowered.startswith("/voice-speak ") else "voice-speak "
            speech_txt = text[len(prefix):].strip()
            if hasattr(self.runtime, "voice_fabric"):
                wav_bytes, pkt = self.runtime.voice_fabric.synthesize_speech(speech_txt)
                msg = f"[Voice Synthesized] Packet: {pkt.packet_id} | Duration: {pkt.duration_sec:.2f}s | Size: {pkt.data_size_bytes}B | Saved: data/lucy/voice/tts_{pkt.packet_id}.wav"
                return RouterResponse(msg, data=pkt.to_dict())

        if lowered in {"/voice-listen", "voice-listen"}:
            if hasattr(self.runtime, "voice_fabric"):
                sample_audio, _ = self.runtime.voice_fabric.synthesize_speech("Lucy system status check")
                tr = self.runtime.voice_fabric.transcribe_audio(sample_audio, simulated_text="Lucy system status check")
                msg = f"[Voice Transcription] Text: '{tr.text}' | Confidence: {tr.confidence:.2f} | VAD: {tr.vad_triggered} (Energy: {tr.energy_level:.4f})"
                return RouterResponse(msg, data=tr.to_dict())

        if lowered.startswith("/tune-vad") or lowered.startswith("tune-vad"):
            prefix = "/tune-vad" if lowered.startswith("/tune-vad") else "tune-vad"
            arg_val = text[len(prefix):].strip()
            if hasattr(self.runtime, "voice_fabric"):
                if arg_val:
                    try:
                        new_thresh = float(arg_val)
                        cfg = self.runtime.voice_fabric.tune_vad(energy_threshold=new_thresh)
                        return RouterResponse(f"[VAD Calibrated] Energy threshold set to: {cfg['energy_threshold']}", data=cfg)
                    except ValueError:
                        pass
                msg = f"[VAD Status] Current energy threshold: {self.runtime.voice_fabric.energy_threshold:.4f}, silence window: {self.runtime.voice_fabric.silence_window_ms}ms"
                return RouterResponse(msg, data={"energy_threshold": self.runtime.voice_fabric.energy_threshold, "silence_ms": self.runtime.voice_fabric.silence_window_ms})

        # ---------- STAGES 54–58: ADAPTIVE, GROUNDED PERSONAL OPERATOR ----------
        if lowered in {"brief", "brief me", "executive brief", "wake brief", "what now"}:
            brief = self.runtime.proactive_briefer.generate_brief()
            return RouterResponse(brief["brief_text"], data=brief)

        if lowered in {"workspace pulse", "git pulse", "live workspace"}:
            st = self.runtime.workspace_sensor.status()
            return RouterResponse(self.runtime.workspace_sensor.build_workspace_prompt_snippet(), data=st)

        if lowered in {"receipts", "execution receipts", "ledger status"}:
            st = self.runtime.receipt_ledger.status()
            return RouterResponse(json.dumps(st, indent=2), data=st)

        if lowered in {"memory graph", "memory graph status", "/graph"}:
            st = self.runtime.memory_graph.status() if hasattr(self.runtime, "memory_graph") else {}
            return RouterResponse(json.dumps(st, indent=2), data=st)

        if lowered in {"memory conflicts", "contradictions", "resolved conflicts", "/conflicts"}:
            conflicts = self.runtime.memory_conflicts()
            if not conflicts:
                return RouterResponse("Memory conflicts resolved: none recorded yet.")
            lines = [f"Resolved memory contradictions ({len(conflicts)}):"]
            for c in conflicts:
                lines.append(
                    f"  - [{c.get('reason')}] '{c.get('old_fact')}' ({c.get('old_node_id')}) "
                    f"-> '{c.get('new_fact')}' ({c.get('new_node_id')})"
                )
            return RouterResponse("\n".join(lines), data=conflicts)

        if lowered.startswith("memory lineage "):
            q = text[len("memory lineage "):].strip()
            lin = self.runtime.memory_lineage(q)
            if not lin.get("ok"):
                return RouterResponse(lin.get("message", f"No lineage found for '{q}'."), data=lin)
            return RouterResponse(f"Memory lineage ({lin.get('chain_length')} nodes):\n  {lin.get('formatted_chain')}", data=lin)

        if lowered.startswith("pin memory "):
            sel = text[len("pin memory "):].strip()
            res = self.runtime.pin_memory(sel, pinned=True)
            if res.get("ok"):
                n = res["node"]
                return RouterResponse(f"Pinned memory [{n['id']}]: {n['fact']}", data=res)
            return RouterResponse(f"Could not pin memory: {res.get('reason')}", data=res)

        if lowered.startswith("unpin memory "):
            sel = text[len("unpin memory "):].strip()
            res = self.runtime.pin_memory(sel, pinned=False)
            if res.get("ok"):
                n = res["node"]
                return RouterResponse(f"Unpinned memory [{n['id']}]: {n['fact']}", data=res)
            return RouterResponse(f"Could not unpin memory: {res.get('reason')}", data=res)

        # Stage 59: Natural Action Parser Status
        if lowered in {"natural action status", "natural actions status", "action parser status", "stage 59"}:
            st = self.runtime.natural_action_parser.status() if hasattr(self.runtime, "natural_action_parser") else {"status": "inactive"}
            return RouterResponse(json.dumps(st, indent=2), data=st)

        if lowered in {"workflow status", "corrections", "macros"}:
            st = self.runtime.workflow_learner.status() if hasattr(self.runtime, "workflow_learner") else {}
            return RouterResponse(json.dumps(st, indent=2), data=st)

        if lowered.startswith("macro "):
            rest = text[6:].strip()
            if "=" in rest:
                name, steps_raw = rest.split("=", 1)
                steps = [s.strip() for s in steps_raw.split(";")]
                res = self.runtime.workflow_learner.save_macro(name, steps)
                if res.get("ok"):
                    return RouterResponse(f"Saved macro '{res['macro']}': {res['steps']}", data=res)
                return RouterResponse(f"Could not save macro: {res.get('reason')}")
            macro_steps = self.runtime.workflow_learner.get_macro(rest)
            if macro_steps:
                outputs = [self.handle(step, _reset_turn=False).message for step in macro_steps]
                return RouterResponse("\n\n---\n\n".join(outputs))
            return RouterResponse(f"Unknown macro '{rest}'. Define one with: macro <name> = <cmd1> ; <cmd2>")


        if lowered in {"help", "/help", "commands"}:
            return RouterResponse(self._help())

        if lowered == "status":
            return RouterResponse(self._format_status(self.runtime.status()))

        if lowered in {"session status", "load state"}:
            return RouterResponse(self._format_session_status(self.runtime.load_state()))

        if lowered == "save state":
            return RouterResponse(self._format_session_status(self.runtime.save_state(), saved=True))

        if lowered == "tell me":
            return RouterResponse(self._format_current_lucy_status(self.runtime.current_lucy_status()))

        if lowered == "what next":
            return RouterResponse(self._format_stage18_next_action(self.runtime.stage18_next_action()))

        if lowered in {"runtime status", "persistent runtime status", "recovery status", "heartbeat status"}:
            return RouterResponse(self._format_runtime_status(self.runtime.runtime_status()))

        if lowered in {"access status", "safe access status", "access policy", "local access status"}:
            return RouterResponse(self._format_safe_access_status(self.runtime.safe_access_status()))

        if lowered == "first thought status":
            return RouterResponse(self._format_first_thought_status(self.runtime.first_thought_status()))

        if lowered == "first thought readiness":
            return RouterResponse(self._format_first_thought_readiness(self.runtime.first_thought_readiness()))

        if lowered == "assemble first thought":
            return RouterResponse(self._format_first_thought_assembly(self.runtime.assemble_first_thought()))

        if lowered == "show first thought":
            return RouterResponse(self._format_show_first_thought(self.runtime.show_first_thought()))

        if lowered in {
            "self model status",
            "self model",
            "what are you",
            "what can you do",
            "what can you not do",
            "what is your current stage",
            "what are your limits",
        }:
            return RouterResponse(self._format_self_model_status(self.runtime.self_model_status()))

        if lowered in {"growth proposals status", "growth proposal status"}:
            return RouterResponse(self._format_growth_proposals_status(self.runtime.growth_proposals_status()))

        if lowered in {"growth proposals", "show growth proposals"}:
            return RouterResponse(self._format_growth_proposals_list(self.runtime.list_growth_proposals()))

        if lowered == "propose growth":
            return RouterResponse(self._format_growth_proposal(self.runtime.propose_growth()))

        if lowered.startswith("reject growth proposal"):
            selector = text[len("reject growth proposal"):].strip()
            return RouterResponse(self._format_growth_proposal_review(self.runtime.reject_growth_proposal(selector)))

        if lowered.startswith("approve growth proposal for future"):
            selector = text[len("approve growth proposal for future"):].strip()
            return RouterResponse(self._format_growth_proposal_review(self.runtime.approve_growth_proposal_for_future(selector)))

        if lowered in {"evaluation lab status", "evaluation status"}:
            return RouterResponse(self._format_evaluation_lab_status(self.runtime.evaluation_lab_status()))

        if lowered == "evaluate growth proposals":
            return RouterResponse(self._format_evaluate_growth_proposals(self.runtime.evaluate_growth_proposals()))

        if lowered.startswith("evaluate proposal"):
            selector = text[len("evaluate proposal"):].strip()
            return RouterResponse(self._format_evaluate_proposal(self.runtime.evaluate_proposal(selector)))

        if lowered == "show evaluations":
            return RouterResponse(self._format_evaluations_list(self.runtime.show_evaluations()))

        if lowered in {"shadow testing status", "shadow status"}:
            return RouterResponse(self._format_shadow_testing_status(self.runtime.shadow_testing_status()))

        if lowered == "run shadow test":
            return RouterResponse(self._format_shadow_test_result(self.runtime.run_shadow_test()))

        if lowered.startswith("shadow test proposal"):
            selector = text[len("shadow test proposal"):].strip()
            return RouterResponse(self._format_shadow_test_result(self.runtime.shadow_test_proposal(selector)))

        if lowered == "show shadow tests":
            return RouterResponse(self._format_shadow_tests_list(self.runtime.show_shadow_tests()))

        if lowered in {"patch pipeline status", "approved patch pipeline status"}:
            return RouterResponse(self._format_patch_pipeline_status(self.runtime.patch_pipeline_status()))

        if lowered.startswith("create patch plan"):
            selector = text[len("create patch plan"):].strip()
            return RouterResponse(self._format_patch_plan_result(self.runtime.create_patch_plan(selector)))

        if lowered.startswith("prepare patch plan"):
            selector = text[len("prepare patch plan"):].strip()
            return RouterResponse(self._format_patch_plan_result(self.runtime.create_patch_plan(selector)))

        if lowered == "show patch plans":
            return RouterResponse(self._format_patch_plans_list(self.runtime.show_patch_plans()))

        if lowered == "patch plan status":
            return RouterResponse(self._format_patch_pipeline_status(self.runtime.patch_plan_status()))

        if lowered in {"experience storage status", "experience status"}:
            return RouterResponse(self._format_experience_storage_status(self.runtime.experience_storage_status()))

        if lowered == "record experience":
            return RouterResponse(self._format_experience_record_result(self.runtime.record_experience()))

        if lowered == "record stage experience":
            return RouterResponse(self._format_experience_record_result(self.runtime.record_stage_experience()))

        if lowered in {"show experiences", "show experience records"}:
            return RouterResponse(self._format_experience_records_list(self.runtime.show_experiences()))

        if lowered in {"identity stability status", "identity status"}:
            return RouterResponse(self._format_identity_stability_status(self.runtime.identity_stability_status()))

        if lowered in {"check identity stability", "identity check"}:
            return RouterResponse(self._format_identity_check_result(self.runtime.check_identity_stability()))

        if lowered in {"show identity checks", "show identity stability checks"}:
            return RouterResponse(self._format_identity_checks_list(self.runtime.show_identity_checks()))

        if lowered in {"long-term strategy status", "long term strategy status", "strategy status"}:
            return RouterResponse(self._format_long_term_strategy_status(self.runtime.long_term_strategy_status()))

        if lowered in {"create long-term strategy", "create long term strategy", "create strategy", "strategy"}:
            return RouterResponse(self._format_long_term_strategy_result(self.runtime.create_long_term_strategy()))

        if lowered in {"show long-term strategies", "show long term strategies", "show strategies", "strategies"}:
            return RouterResponse(self._format_long_term_strategies_list(self.runtime.show_long_term_strategies()))

        if lowered in {"smart organizer status", "organizer status"}:
            return RouterResponse(self._format_smart_organizer_status(self.runtime.smart_organizer_status()))

        if lowered in {"create organizer item", "create organizer", "organizer"}:
            return RouterResponse(self._format_organizer_item_result(self.runtime.create_organizer_item()))

        if lowered in {"show organizer items", "show organizer", "organizer items"}:
            return RouterResponse(self._format_organizer_items_list(self.runtime.show_organizer_items()))

        if lowered in {"safe local actions status", "safe action status", "local action status"}:
            return RouterResponse(self._format_safe_local_actions_status(self.runtime.safe_local_actions_status()))

        if lowered in {"create safe action proposal", "create safe local action proposal", "safe action proposal"}:
            return RouterResponse(self._format_safe_action_result(self.runtime.create_safe_action_proposal()))

        if lowered in {"dry run safe action", "dry-run safe action", "dry run local action", "test safe action"}:
            return RouterResponse(self._format_safe_action_dry_run(self.runtime.dry_run_safe_action()))

        if lowered in {"show safe action proposals", "show safe actions", "safe action proposals", "safe actions"}:
            return RouterResponse(self._format_safe_action_list(self.runtime.show_safe_action_proposals()))

        if lowered in {"external app bridge status", "app bridge status", "bridge status"}:
            return RouterResponse(self._format_external_app_bridge_status(self.runtime.external_app_bridge_status()))

        if lowered in {"create external app bridge proposal", "create bridge proposal", "bridge proposal"}:
            return RouterResponse(self._format_external_bridge_result(self.runtime.create_external_app_bridge_proposal()))

        if lowered in {"dry run external app bridge", "dry-run external app bridge", "dry run bridge", "test bridge"}:
            return RouterResponse(self._format_external_bridge_dry_run(self.runtime.dry_run_external_app_bridge()))

        if lowered in {"show external app bridge proposals", "show bridge proposals", "bridge proposals", "bridges"}:
            return RouterResponse(self._format_external_bridge_list(self.runtime.show_external_app_bridge_proposals()))

        if lowered in {"proactive awareness status", "awareness status", "local awareness status"}:
            return RouterResponse(self._format_proactive_awareness_status(self.runtime.proactive_awareness_status()))

        if lowered in {"create proactive awareness scan", "create awareness scan", "awareness scan"}:
            return RouterResponse(self._format_awareness_scan_result(self.runtime.create_proactive_awareness_scan()))

        if lowered in {"dry run proactive awareness", "dry-run proactive awareness", "dry run awareness", "test awareness"}:
            return RouterResponse(self._format_awareness_dry_run(self.runtime.dry_run_proactive_awareness()))

        if lowered in {"show proactive awareness scans", "show awareness scans", "awareness scans"}:
            return RouterResponse(self._format_awareness_scan_list(self.runtime.show_proactive_awareness_scans()))

        if lowered in {"deep recall status", "recall status", "safe recall status"}:
            return RouterResponse(self._format_deep_recall_status(self.runtime.deep_recall_status()))

        if lowered in {"create deep recall session", "create recall session", "deep recall"}:
            return RouterResponse(self._format_deep_recall_result(self.runtime.create_deep_recall_session()))

        if lowered.startswith("deep recall "):
            query = lowered.replace("deep recall ", "", 1).strip()
            return RouterResponse(self._format_deep_recall_result(self.runtime.create_deep_recall_session(query=query)))

        if lowered.startswith("recall safe "):
            query = lowered.replace("recall safe ", "", 1).strip()
            return RouterResponse(self._format_deep_recall_result(self.runtime.create_deep_recall_session(query=query)))

        if lowered in {"dry run deep recall", "dry-run deep recall", "dry run recall", "test recall"}:
            return RouterResponse(self._format_deep_recall_dry_run(self.runtime.dry_run_deep_recall()))

        if lowered in {"show deep recall sessions", "show recall sessions", "deep recall sessions", "recall sessions"}:
            return RouterResponse(self._format_deep_recall_list(self.runtime.show_deep_recall_sessions()))

        if lowered in {"judgment status", "judgement status", "safe judgment status", "safe judgement status"}:
            return RouterResponse(self._format_judgment_status(self.runtime.judgment_status()))

        if lowered in {"create judgment record", "create judgement record", "create cautious judgment", "judgment", "judgement"}:
            return RouterResponse(self._format_judgment_result(self.runtime.create_judgment_record()))

        if lowered.startswith("judgment "):
            situation = lowered.replace("judgment ", "", 1).strip()
            return RouterResponse(self._format_judgment_result(self.runtime.create_judgment_record(situation=situation)))

        if lowered.startswith("judge "):
            situation = lowered.replace("judge ", "", 1).strip()
            return RouterResponse(self._format_judgment_result(self.runtime.create_judgment_record(situation=situation)))

        if lowered in {"dry run judgment", "dry-run judgment", "dry run judgement", "test judgment", "test judgement"}:
            return RouterResponse(self._format_judgment_dry_run(self.runtime.dry_run_judgment()))

        if lowered in {"show judgments", "show judgements", "judgments", "judgements", "judgment records"}:
            return RouterResponse(self._format_judgment_list(self.runtime.show_judgments()))

        if lowered in {"adaptive communication status", "adaptive status", "communication style status", "style status"}:
            return RouterResponse(self._format_adaptive_communication_status(self.runtime.adaptive_communication_status()))

        if lowered in {"create adaptive communication profile", "create style profile", "adaptive communication", "style profile"}:
            return RouterResponse(self._format_adaptive_communication_result(self.runtime.create_adaptive_communication_profile()))

        if lowered.startswith("adaptive communication "):
            context = lowered.replace("adaptive communication ", "", 1).strip()
            return RouterResponse(self._format_adaptive_communication_result(self.runtime.create_adaptive_communication_profile(context=context)))

        if lowered.startswith("style profile "):
            context = lowered.replace("style profile ", "", 1).strip()
            return RouterResponse(self._format_adaptive_communication_result(self.runtime.create_adaptive_communication_profile(context=context)))

        if lowered in {"dry run adaptive communication", "dry-run adaptive communication", "dry run style", "test adaptive communication", "test style"}:
            return RouterResponse(self._format_adaptive_communication_dry_run(self.runtime.dry_run_adaptive_communication()))

        if lowered in {"show adaptive communication profiles", "show style profiles", "adaptive communication profiles", "style profiles"}:
            return RouterResponse(self._format_adaptive_communication_list(self.runtime.show_adaptive_communication_profiles()))

        if lowered in {"human state awareness status", "human state status", "state awareness status", "state status"}:
            return RouterResponse(self._format_human_state_awareness_status(self.runtime.human_state_awareness_status()))

        if lowered in {"create human state signal", "create state signal", "human state awareness", "state signal"}:
            return RouterResponse(self._format_human_state_signal_result(self.runtime.create_human_state_signal()))

        if lowered.startswith("human state awareness "):
            signal = lowered.replace("human state awareness ", "", 1).strip()
            return RouterResponse(self._format_human_state_signal_result(self.runtime.create_human_state_signal(signal=signal)))

        if lowered.startswith("human state "):
            signal = lowered.replace("human state ", "", 1).strip()
            return RouterResponse(self._format_human_state_signal_result(self.runtime.create_human_state_signal(signal=signal)))

        if lowered.startswith("state signal "):
            signal = lowered.replace("state signal ", "", 1).strip()
            return RouterResponse(self._format_human_state_signal_result(self.runtime.create_human_state_signal(signal=signal)))

        if lowered in {"dry run human state awareness", "dry-run human state awareness", "dry run human state", "dry run state", "test human state", "test state"}:
            return RouterResponse(self._format_human_state_awareness_dry_run(self.runtime.dry_run_human_state_awareness()))

        if lowered in {"show human state signals", "show state signals", "human state signals", "state signals"}:
            return RouterResponse(self._format_human_state_signal_list(self.runtime.show_human_state_signals()))

        if lowered in {"time awareness status", "time status", "time context status"}:
            return RouterResponse(self._format_time_awareness_status(self.runtime.time_awareness_status()))

        if lowered in {"create time context", "time awareness", "time context"}:
            return RouterResponse(self._format_time_context_result(self.runtime.create_time_context()))

        if lowered.startswith("time awareness "):
            context = lowered.replace("time awareness ", "", 1).strip()
            return RouterResponse(self._format_time_context_result(self.runtime.create_time_context(context=context)))

        if lowered.startswith("time context "):
            context = lowered.replace("time context ", "", 1).strip()
            return RouterResponse(self._format_time_context_result(self.runtime.create_time_context(context=context)))

        if lowered in {"dry run time awareness", "dry-run time awareness", "dry run time", "test time awareness", "test time"}:
            return RouterResponse(self._format_time_awareness_dry_run(self.runtime.dry_run_time_awareness()))

        if lowered in {"show time contexts", "time contexts", "show time records", "time records"}:
            return RouterResponse(self._format_time_context_list(self.runtime.show_time_contexts()))

        if lowered in {"autonomy boundaries status", "autonomy boundary status", "autonomy status", "boundary status"}:
            return RouterResponse(self._format_autonomy_boundaries_status(self.runtime.autonomy_boundaries_status()))

        if lowered in {"create autonomy boundary record", "create boundary record", "autonomy boundaries", "autonomy boundary", "boundary record"}:
            return RouterResponse(self._format_autonomy_boundary_result(self.runtime.create_autonomy_boundary_record()))

        if lowered.startswith("autonomy boundaries "):
            request = lowered.replace("autonomy boundaries ", "", 1).strip()
            return RouterResponse(self._format_autonomy_boundary_result(self.runtime.create_autonomy_boundary_record(request=request)))

        if lowered.startswith("autonomy boundary "):
            request = lowered.replace("autonomy boundary ", "", 1).strip()
            return RouterResponse(self._format_autonomy_boundary_result(self.runtime.create_autonomy_boundary_record(request=request)))

        if lowered.startswith("boundary record "):
            request = lowered.replace("boundary record ", "", 1).strip()
            return RouterResponse(self._format_autonomy_boundary_result(self.runtime.create_autonomy_boundary_record(request=request)))

        if lowered in {"dry run autonomy boundaries", "dry-run autonomy boundaries", "dry run autonomy", "test autonomy boundaries", "test autonomy"}:
            return RouterResponse(self._format_autonomy_boundaries_dry_run(self.runtime.dry_run_autonomy_boundaries()))

        if lowered in {"show autonomy boundary records", "show boundary records", "autonomy boundary records", "boundary records"}:
            return RouterResponse(self._format_autonomy_boundary_list(self.runtime.show_autonomy_boundary_records()))

        if lowered in {"provider identity boundary status", "provider identity status", "provider boundary status", "api identity status"}:
            return RouterResponse(self._format_provider_identity_boundary_status(self.runtime.provider_identity_boundary_status()))

        if lowered in {"create provider identity boundary record", "create provider boundary record", "provider identity boundary", "provider boundary", "api identity boundary"}:
            return RouterResponse(self._format_provider_identity_boundary_result(self.runtime.create_provider_identity_boundary_record()))

        if lowered.startswith("provider identity boundary "):
            context = lowered.replace("provider identity boundary ", "", 1).strip()
            return RouterResponse(self._format_provider_identity_boundary_result(self.runtime.create_provider_identity_boundary_record(context=context)))

        if lowered.startswith("provider boundary "):
            context = lowered.replace("provider boundary ", "", 1).strip()
            return RouterResponse(self._format_provider_identity_boundary_result(self.runtime.create_provider_identity_boundary_record(context=context)))

        if lowered.startswith("api identity boundary "):
            context = lowered.replace("api identity boundary ", "", 1).strip()
            return RouterResponse(self._format_provider_identity_boundary_result(self.runtime.create_provider_identity_boundary_record(context=context)))

        if lowered in {"dry run provider identity boundary", "dry-run provider identity boundary", "dry run provider boundary", "test provider identity boundary", "test provider identity"}:
            return RouterResponse(self._format_provider_identity_boundary_dry_run(self.runtime.dry_run_provider_identity_boundary()))

        if lowered in {"show provider identity boundary records", "show provider boundary records", "provider identity records", "provider boundary records"}:
            return RouterResponse(self._format_provider_identity_boundary_list(self.runtime.show_provider_identity_boundary_records()))

        if lowered in {"secrets provider key safety status", "secret safety status", "key safety status", "api key safety status", "provider key safety status"}:
            return RouterResponse(self._format_secrets_provider_key_safety_status(self.runtime.secrets_provider_key_safety_status()))

        if lowered in {"create secret safety record", "create key safety record", "secrets provider key safety", "secret safety", "provider key safety", "api key safety"}:
            return RouterResponse(self._format_secret_safety_result(self.runtime.create_secret_safety_record()))

        if lowered.startswith("secrets provider key safety "):
            context = lowered.replace("secrets provider key safety ", "", 1).strip()
            return RouterResponse(self._format_secret_safety_result(self.runtime.create_secret_safety_record(context=context)))

        if lowered.startswith("secret safety "):
            context = lowered.replace("secret safety ", "", 1).strip()
            return RouterResponse(self._format_secret_safety_result(self.runtime.create_secret_safety_record(context=context)))

        if lowered.startswith("provider key safety "):
            context = lowered.replace("provider key safety ", "", 1).strip()
            return RouterResponse(self._format_secret_safety_result(self.runtime.create_secret_safety_record(context=context)))

        if lowered.startswith("api key safety "):
            context = lowered.replace("api key safety ", "", 1).strip()
            return RouterResponse(self._format_secret_safety_result(self.runtime.create_secret_safety_record(context=context)))

        if lowered in {"safe key file scan", "key file scan", "scan api keys file", "scan apikeys", "safe provider presence scan"}:
            return RouterResponse(self._format_safe_key_file_scan(self.runtime.safe_key_file_scan()))

        if lowered in {"dry run secrets safety", "dry-run secrets safety", "dry run key safety", "test secrets safety", "test key safety"}:
            return RouterResponse(self._format_secrets_safety_dry_run(self.runtime.dry_run_secrets_safety()))

        if lowered in {"show secret safety records", "show key safety records", "secret safety records", "key safety records"}:
            return RouterResponse(self._format_secret_safety_list(self.runtime.show_secret_safety_records()))

        if lowered in {"provider registry status", "registry status", "model provider registry status", "provider list status"}:
            return RouterResponse(self._format_provider_registry_status(self.runtime.provider_registry_status()))

        if lowered in {"provider registry", "list providers", "registered providers", "show providers", "provider list"}:
            return RouterResponse(self._format_provider_registry_list(self.runtime.list_registered_providers()))

        if lowered in {"reset provider registry", "provider registry reset"}:
            return RouterResponse(self._format_provider_registry_reset(self.runtime.reset_provider_registry()))

        if lowered in {"dry run provider registry", "dry-run provider registry", "test provider registry", "provider registry dry run"}:
            return RouterResponse(self._format_provider_registry_dry_run(self.runtime.dry_run_provider_registry()))

        if lowered.startswith("enable provider "):
            provider_name = lowered.replace("enable provider ", "", 1).strip()
            return RouterResponse(self._format_provider_registry_change(self.runtime.enable_registered_provider(provider_name)))

        if lowered.startswith("disable provider "):
            provider_name = lowered.replace("disable provider ", "", 1).strip()
            return RouterResponse(self._format_provider_registry_change(self.runtime.disable_registered_provider(provider_name)))

        if lowered.startswith("show provider "):
            provider_name = lowered.replace("show provider ", "", 1).strip()
            return RouterResponse(self._format_provider_registry_provider_result(self.runtime.get_registered_provider(provider_name)))

        if lowered.startswith("registered provider "):
            provider_name = lowered.replace("registered provider ", "", 1).strip()
            return RouterResponse(self._format_provider_registry_provider_result(self.runtime.get_registered_provider(provider_name)))

        if lowered.startswith("provider registry "):
            provider_name = lowered.replace("provider registry ", "", 1).strip()
            return RouterResponse(self._format_provider_registry_provider_result(self.runtime.get_registered_provider(provider_name)))

        if lowered in {"provider health check status", "health check status", "provider health status", "provider health-check status"}:
            return RouterResponse(self._format_provider_health_check_status(self.runtime.provider_health_check_status()))

        # Stage 35: Provider Role Split
        if lowered in {"provider role split", "provider roles", "role split status", "sovereign mind status"}:
            return RouterResponse(self._format_provider_role_split_status(self.runtime.provider_role_split_status()))

        # Stage 36: Local Ollama Sovereign Connector & Training Queue
        if lowered in {"ollama status", "ollama connector status", "local engine status", "local mind status"}:
            return RouterResponse(self._format_ollama_status(self.runtime.ollama_status()))

        if lowered in {"training queue status", "lora training queue", "lora queue status", "verified queue status"}:
            return RouterResponse(self._format_training_queue_status(self.runtime.training_queue_status()))

        # Stage 37: ELIE Fact/State Verifier & Security Review
        if lowered in {"fact verifier status", "fact state status", "anti hallucination status", "elie verifier status"}:
            return RouterResponse(self._format_fact_verifier_status(self.runtime.fact_verifier_status()))

        if lowered.startswith("verify fact ") or lowered.startswith("fact check ") or lowered.startswith("verify claim "):
            for prefix in ["verify fact ", "fact check ", "verify claim "]:
                if lowered.startswith(prefix):
                    claim = text[len(prefix):].strip().strip('"').strip("'")
                    return RouterResponse(self._format_fact_verification_result(self.runtime.verify_claim(claim)))

        if lowered.startswith("elie review ") or lowered.startswith("elie security review "):
            for prefix in ["elie review ", "elie security review "]:
                if lowered.startswith(prefix):
                    code_snippet = text[len(prefix):].strip().strip('"').strip("'")
                    return RouterResponse(self._format_elie_review_result(self.runtime.elie_security_review(code_snippet)))

        # Stage 38: Autonomous Task Daemon & Background Task Queue
        if lowered in {"task daemon status", "daemon status", "task queue status", "background task daemon"}:
            return RouterResponse(self._format_task_daemon_status(self.runtime.task_daemon_status()))

        if lowered in {"background tasks", "bg tasks", "daemon tasks", "list background tasks"}:
            return RouterResponse(self._format_background_tasks_list(self.runtime.list_background_tasks()))

        if lowered.startswith("task status ") or lowered.startswith("bg task ") or lowered.startswith("daemon task "):
            for prefix in ["task status ", "bg task ", "daemon task "]:
                if lowered.startswith(prefix):
                    task_id = text[len(prefix):].strip().strip('"').strip("'")
                    return RouterResponse(self._format_background_task_detail(self.runtime.get_background_task(task_id), task_id))

        if lowered.startswith("cancel background task ") or lowered.startswith("cancel bg task ") or lowered.startswith("cancel task "):
            for prefix in ["cancel background task ", "cancel bg task ", "cancel task "]:
                if lowered.startswith(prefix):
                    task_id = text[len(prefix):].strip().strip('"').strip("'")
                    return RouterResponse(self._format_task_cancel_result(self.runtime.cancel_background_task(task_id)))

        # Stage 39: Swarm Dispatcher Bridge & senin/ai Bots Integration
        if lowered in {
            "connect swarm", "connect all bots", "connect external bots", "start swarm", "start all bots",
            "connect to bots", "connect to the bots", "connect bots",
        }:
            return RouterResponse(self._format_connect_swarm_result(self.runtime.connect_swarm()))

        if lowered in {
            "connect writer", "connect writer bot", "connect to writer bot", "connect to the writer bot",
            "start writer", "start writer bot", "launch writer bot", "writer connect",
        }:
            return RouterResponse(self._format_writer_connect_result(self.runtime.connect_writer_bot()))

        if lowered in {"writer status", "check writer", "check writer bot", "probe writer", "probe writer bot"}:
            return RouterResponse(self._format_writer_status_result(self.runtime.writer_status()))

        if lowered in {
            "connect checker", "connect checker bot", "connect to checker bot", "start checker bot",
        }:
            return RouterResponse(self._format_checker_connect_result(self.runtime.connect_checker_bot()))

        if lowered in {"checker status", "check checker", "check checker bot", "probe checker"}:
            return RouterResponse(self._format_checker_status_result(self.runtime.checker_status()))

        if lowered in {
            "connect director", "connect director bot", "connect to director bot", "start director bot",
        }:
            return RouterResponse(self._format_director_connect_result(self.runtime.connect_director_bot()))

        if lowered in {"director status", "check director", "check director bot", "probe director"}:
            return RouterResponse(self._format_director_status_result(self.runtime.director_status()))

        if lowered in {"swarm hierarchy", "swarm policy", "bots hierarchy", "bots policy"}:
            return RouterResponse(self._format_swarm_hierarchy())

        if lowered in {"swarm status", "bot swarm status", "swarm health", "external swarm status"}:
            return RouterResponse(self._format_swarm_status(self.runtime.swarm_status()))

        # OpenJarvis (open-jarvis/OpenJarvis) Sovereign Integration
        if lowered in {"/jarvis", "/openjarvis", "open jarvis status", "openjarvis status", "jarvis status", "open jarvis", "openjarvis"}:
            res = self.runtime.open_jarvis_status()
            srv = res.get("server", {})
            prims = res.get("primitives", {})
            msg = (
                f"=== OPENJARVIS SOVEREIGN ORCHESTRATION BRIDGE ===\n"
                f"Authority: {res.get('sovereign_authority')} (Unidirectional Sovereign Command)\n"
                f"Server: {srv.get('host')}:{srv.get('port')} [{srv.get('mode')}]\n"
                f"Intelligence: {prims.get('intelligence', {}).get('primary_model')} ({len(prims.get('intelligence', {}).get('available_models', []))} models registered)\n"
                f"Engine: {prims.get('engine', {}).get('device_class')} ({prims.get('engine', {}).get('cpu_count')} CPUs)\n"
                f"Agents: 7 subordinate loops (native_react, native_openhands, deep_research, orchestrator, morning_digest, operative, chat_simple)\n"
                f"Tools: {prims.get('tools', {}).get('tool_count')} tools registered | MCP Bridge: Active | agentskills.io: Standard\n"
                f"Learning: Intelligence Per Watt active | Traces: {prims.get('learning', {}).get('traces_file')}"
            )
            return RouterResponse(msg, data=res)

        if lowered.startswith("/jarvis-run ") or lowered.startswith("jarvis run "):
            raw_cmd = raw_text[12:].strip() if raw_text.startswith("/jarvis-run ") else raw_text[11:].strip()
            parts = raw_cmd.split(" ", 1)
            agent_type = parts[0] if parts else "native_react"
            task = parts[1] if len(parts) > 1 else "Status check"
            res = self.runtime.open_jarvis_execute_agent(agent_type=agent_type, task=task)
            return RouterResponse(f"OpenJarvis [{res.get('agent')}]: {res.get('content')}", data=res)

        if lowered in {"/jarvis-efficiency", "jarvis efficiency", "openjarvis efficiency"}:
            eff = self.runtime.open_jarvis_profile_efficiency()
            msg = (
                f"=== OPENJARVIS INTELLIGENCE PER WATT PROFILE ===\n"
                f"Throughput: {eff.get('throughput_tokens_sec')} tokens/sec\n"
                f"Power Draw: ~{eff.get('estimated_power_draw_w')} W (AMD Ryzen APU)\n"
                f"Energy: {eff.get('energy_consumed_joules')} J per turn\n"
                f"Efficiency: {eff.get('efficiency_tokens_per_joule')} tokens/Joule ({eff.get('compliance')})"
            )
            return RouterResponse(msg, data=eff)

        if lowered.startswith("dispatch write ") or lowered.startswith("write code ") or lowered.startswith("writer write "):
            if lowered.startswith("dispatch write "):
                prefix = "dispatch write "
            elif lowered.startswith("write code "):
                prefix = "write code "
            else:
                prefix = "writer write "
            instruction = text[len(prefix):].strip()
            return RouterResponse(self._format_swarm_write_result(self.runtime.dispatch_write(instruction)))

        if lowered.startswith("dispatch check "):
            code_snippet = text[len("dispatch check "):].strip()
            return RouterResponse(self._format_swarm_check_result(self.runtime.dispatch_check(code_snippet)))

        if lowered.startswith("dispatch director "):
            stage_target = text[len("dispatch director "):].strip()
            return RouterResponse(self._format_swarm_director_result(self.runtime.dispatch_director(blueprint="", stage=stage_target)))

        # Stage 40: Code Synthesis & Real Terminal AST / Pytest Verification Pipeline
        if lowered in {"synthesis status", "code synthesis status", "pipeline status", "code pipeline status"}:
            return RouterResponse(self._format_synthesis_status(self.runtime.code_synthesis_status()))

        if lowered in {"synthesis history", "code synthesis history", "syntheses history"}:
            return RouterResponse(self._format_synthesis_history(self.runtime.code_synthesis_history()))

        if lowered.startswith("synthesize code ") or lowered.startswith("synthesize "):
            prefix = "synthesize code " if lowered.startswith("synthesize code ") else "synthesize "
            instruction = text[len(prefix):].strip()
            return RouterResponse(self._format_synthesis_result(self.runtime.synthesize_code(instruction=instruction)))

        if lowered.startswith("verify code ") or lowered.startswith("verify file "):
            prefix = "verify code " if lowered.startswith("verify code ") else "verify file "
            filepath = text[len(prefix):].strip().strip('"').strip("'")
            return RouterResponse(self._format_verify_code_result(self.runtime.verify_code_file(filepath)))

        # Stage 41: Self-Refinement & Regression Testing Harness
        if lowered in {"refinement status", "self refinement status", "harness status", "self-refinement status"}:
            return RouterResponse(self._format_refinement_status(self.runtime.self_refinement_status()))

        if lowered in {"refinement history", "self refinement history", "self-refinement history"}:
            return RouterResponse(self._format_refinement_history(self.runtime.self_refinement_history()))

        if lowered in {"run regression suite", "regression test", "regression check", "run regression check"}:
            return RouterResponse(self._format_regression_result(self.runtime.run_regression_suite()))

        if lowered.startswith("refine code "):
            code_snippet = text[len("refine code "):].strip()
            return RouterResponse(self._format_refinement_result(self.runtime.refine_code(code=code_snippet, error_context="User manual repair request.")))

        # Stage 42: LoRA Sleep Cycle & 20-Question Sanity Gate
        if lowered in {"sleep cycle status", "lora sleep cycle status"}:
            return RouterResponse(self._format_lora_sleep_cycle_status(self.runtime.lora_sleep_cycle_status()))

        if lowered in {"trigger sleep cycle", "start sleep cycle"}:
            return RouterResponse(self._format_sleep_cycle_result(self.runtime.trigger_sleep_cycle()))

        if lowered in {"run sanity test", "sanity test", "sanity gate", "run sanity gate", "20 question test"}:
            return RouterResponse(self._format_sanity_gate_result(self.runtime.run_lora_sanity_gate()))

        if lowered in {"list adapters", "show adapters", "lora adapters", "adapters list"}:
            return RouterResponse(self._format_lora_adapters_list(self.runtime.list_lora_adapters()))

        if lowered in {"sleep cycle history", "lora history", "sleep history"}:
            return RouterResponse(self._format_sleep_cycle_history(self.runtime.lora_sleep_cycle_history()))

        # Stage 43: Conversational Memory & Context Engine
        if lowered in {"session memory status", "conversational memory status", "context status", "conversation memory status"}:
            return RouterResponse(self._format_conversational_memory_status(self.runtime.conversational_memory_status()))

        if lowered in {"dialogue status", "dialogue", "/dialogue", "topic status", "coreference status"}:
            st = self.runtime.dialogue_tracker_status() if hasattr(self.runtime, "dialogue_tracker_status") else {}
            return RouterResponse(json.dumps(st, indent=2), data=st)

        if lowered in {"session recap", "previous session recap", "what did we talk about", "recap session"}:
            return RouterResponse(self._format_session_recap(self.runtime.session_recap()))

        if lowered in {"clear session context", "reset conversation context", "clear context buffer"}:
            return RouterResponse(self._format_clear_session_context(self.runtime.clear_session_context()))

        # Stage 44: Personal Behavioral Profiler & Habit Engine
        if lowered in {"personal profile status", "profile status", "my profile", "personal profile"}:
            return RouterResponse(self._format_personal_profile_status(self.runtime.personal_profile_status()))

        if lowered in {"my preferences", "show preferences", "personal preferences", "preferences"}:
            return RouterResponse(self._format_personal_preferences(self.runtime.personal_profile_status()))

        if lowered in {"anti drift rules", "anti-drift rules", "show anti drift rules", "guardrails", "rules"}:
            return RouterResponse(self._format_anti_drift_rules(self.runtime.personal_profile_status()))

        if lowered.startswith("add alias ") or lowered.startswith("set alias ") or lowered.startswith("alias "):
            clean_cmd = text
            for pfx in ("add alias ", "set alias ", "alias "):
                if clean_cmd.lower().startswith(pfx):
                    clean_cmd = clean_cmd[len(pfx):].strip()
                    break
            parts = clean_cmd.split("=", 1) if "=" in clean_cmd else clean_cmd.split(" to ", 1)
            if len(parts) == 2:
                s = parts[0].strip()
                t = parts[1].strip()
                return RouterResponse(self._format_add_alias(self.runtime.add_workspace_alias(s, t)))
            return RouterResponse("Usage: add alias <shortcut> = <target_path>")

        if lowered.startswith("add rule ") or lowered.startswith("remember rule "):
            prefix = "add rule " if lowered.startswith("add rule ") else "remember rule "
            rule = text[len(prefix):].strip()
            return RouterResponse(self._format_add_rule(self.runtime.add_anti_drift_rule(rule)))

        # Stage 36, 42, & 45 Two-Speed Adaptation Commands
        if lowered in {"alignment status", "lora status", "adaptation status", "/alignment"}:
            st = self.runtime.personal_alignment.status()
            return RouterResponse(json.dumps(st, indent=2), data=st)

        if lowered in {"training queue", "queue status", "/queue"}:
            st = self.runtime.training_queue.status()
            return RouterResponse(json.dumps(st, indent=2), data=st)

        if lowered in {"train lora", "run sleep cycle", "sleep cycle", "/sleep"}:
            rep = self.runtime.trigger_personal_sleep_cycle()
            msg = (
                f"{rep['badge']}\n"
                f"- Verified Dataset Records: {rep['dataset_record_count']}\n"
                f"- GPU Training Mode:        {rep['gpu_training'].get('mode')}\n"
                f"- Modelfile Generated:      {rep['modelfile_path']}\n"
                f"- Physical Adapter Active:  {rep['adapter_active_on_disk']}\n"
                f"- Baked Exemplars:          {rep['baked_exemplars_count']}\n"
                f"- Active Local Model:       {rep['active_model']}"
            )
            return RouterResponse(msg, data=rep)

        # Stage 45: Personal LoRA Style Alignment Pipeline
        if lowered in {"personal lora status", "personal alignment status"}:
            return RouterResponse(self._format_personal_lora_status(self.runtime.personal_lora_status()))

        if lowered in {"trigger personal sleep cycle", "train personal lora", "run personal alignment"}:
            return RouterResponse(self._format_personal_sleep_cycle_result(self.runtime.trigger_personal_sleep_cycle()))

        if lowered in {"personal alignment test", "run personal alignment gate", "alignment gate", "alignment test"}:
            return RouterResponse(self._format_personal_alignment_gate_result(self.runtime.run_personal_alignment_gate()))

        if lowered in {"list personal adapters", "personal adapters", "show personal adapters"}:
            return RouterResponse(self._format_personal_adapters_list(self.runtime.list_personal_adapters()))

        if lowered in {"export personal dataset", "synthesize personal dataset", "personal dataset"}:
            return RouterResponse(self._format_synthesize_personal_dataset(self.runtime.synthesize_personal_dataset()))

        # Stage 46: Multi-Provider Key Rotation & Failover Pool
        if lowered in {"provider pool status", "key pool status", "keys status", "pool status", "api keys status"}:
            return RouterResponse(self._format_provider_pool_status(self.runtime.provider_pool_status()))

        if lowered in {"rotate key", "rotate provider key"}:
            return RouterResponse(self._format_rotate_key(self.runtime.rotate_provider_key("groq")))

        if lowered.startswith("rotate key "):
            prov = text[len("rotate key "):].strip()
            return RouterResponse(self._format_rotate_key(self.runtime.rotate_provider_key(prov)))

        if lowered in {"reload api keys", "refresh keys", "reload keys", "load keys"}:
            return RouterResponse(self._format_reload_keys(self.runtime.reload_provider_keys()))

        if lowered.startswith("test rate limit ") or lowered.startswith("simulate rate limit "):
            prefix = "test rate limit " if lowered.startswith("test rate limit ") else "simulate rate limit "
            prov = text[len(prefix):].strip()
            return RouterResponse(self._format_rate_limit_result(self.runtime.mark_key_rate_limited(prov)))

        # Stage 47: Real-World Safe Windows OS Tool Suite
        if lowered in {"system telemetry", "hardware status", "pc status", "sysinfo", "operator status"}:
            return RouterResponse(self._format_system_telemetry(self.runtime.system_telemetry()))

        if lowered in {"inspect processes", "tasklist", "processes", "running processes"}:
            return RouterResponse(self._format_inspect_processes(self.runtime.inspect_processes()))

        if lowered.startswith("inspect processes ") or lowered.startswith("find process "):
            prefix = "inspect processes " if lowered.startswith("inspect processes ") else "find process "
            q = text[len(prefix):].strip()
            return RouterResponse(self._format_inspect_processes(self.runtime.inspect_processes(query=q)))

        if lowered.startswith("search files ") or lowered.startswith("find file ") or lowered.startswith("grep "):
            if lowered.startswith("search files "):
                pat = text[len("search files "):].strip()
            elif lowered.startswith("find file "):
                pat = text[len("find file "):].strip()
            else:
                pat = text[len("grep "):].strip()
            return RouterResponse(self._format_search_workspace(self.runtime.search_workspace_files(pattern=pat, search_content=True)))

        if lowered in {"probe ports", "network ports", "ports status", "ports"}:
            return RouterResponse(self._format_probe_ports(self.runtime.probe_network_ports()))

        if lowered in {"clean sandbox", "clean cache"}:
            return RouterResponse(self._format_clean_sandbox(self.runtime.clean_sandbox_cache(dry_run=False)))

        # Stage 48: Autonomous Intent Dispatcher
        if lowered in {"intent status", "intent dispatcher status", "dispatcher status"}:
            return RouterResponse(self._format_intent_status(self.runtime.intent_dispatcher_status()))

        if lowered.startswith("classify "):
            target_text = text[len("classify "):].strip()
            return RouterResponse(self._format_intent_classification(self.runtime.classify_user_intent(target_text)))

        if lowered.startswith("dispatch "):
            target_text = text[len("dispatch "):].strip()
            res = self.runtime.dispatch_user_intent(target_text)
            if res and res.get("handled"):
                return RouterResponse(res.get("message", "Intent dispatched."))
            return RouterResponse(f"No autonomous operator dispatch resolved for '{target_text}'. (Falling back to conversation)")

        # Stage 53: Autonomous Cron & Temporal Event Daemon
        if lowered in {"/cron status", "cron status", "scheduler status"}:
            return RouterResponse(self._format_cron_status(self.runtime.cron_status()))

        if lowered in {"/schedules", "schedules", "list schedules", "cron jobs"}:
            return RouterResponse(self._format_schedules(self.runtime.list_cron_jobs()))

        if lowered.startswith("/schedule ") or lowered.startswith("schedule "):
            idx = text.lower().find("schedule") + 8
            body = text[idx:].strip()
            if " do " in body:
                expr, target = body.split(" do ", 1)
                job_dict = self.runtime.add_cron_job(expression=expr.strip(), target=target.strip())
                return RouterResponse(f"Scheduled job created: '{job_dict.get('name')}' [{job_dict.get('expression')}] -> {job_dict.get('target')} (ID: {job_dict.get('job_id')})")
            else:
                return RouterResponse("Usage: /schedule <interval|daily HH:MM> do <command>")

        if lowered.startswith("/pause ") or lowered.startswith("pause cron "):
            job_id = text.split()[-1]
            ok = self.runtime.pause_cron_job(job_id)
            return RouterResponse(f"Job '{job_id}' paused." if ok else f"Job '{job_id}' not found.")

        if lowered.startswith("/resume ") or lowered.startswith("resume cron "):
            job_id = text.split()[-1]
            ok = self.runtime.resume_cron_job(job_id)
            return RouterResponse(f"Job '{job_id}' resumed." if ok else f"Job '{job_id}' not found.")

        if lowered.startswith("/unschedule ") or lowered.startswith("delete cron "):
            job_id = text.split()[-1]
            ok = self.runtime.delete_cron_job(job_id)
            return RouterResponse(f"Job '{job_id}' deleted." if ok else f"Job '{job_id}' not found.")

        # Stage 52: Master Orchestrator Goal DAG Loop
        # Stage 64: Multi-Step Terminal Tool Chaining
        if lowered.startswith("chain ") or lowered.startswith("/chain ") or lowered.startswith("tool chain "):
            prefix_len = 5 if lowered.startswith("chain ") else (7 if lowered.startswith("/chain ") else 11)
            chain_spec = text[prefix_len:].strip()
            if chain_spec.lower().startswith("parse "):
                spec_to_parse = chain_spec[6:].strip()
                parsed = self.runtime.parse_tool_chain(spec_to_parse) if hasattr(self.runtime, "parse_tool_chain") else []
                chain_summary = " -> ".join([f"[{p[0]}:{p[1]}]" for p in parsed])
                return RouterResponse(f"Parsed Tool Chain ({len(parsed)} steps):\n  {chain_summary}", data={"steps": parsed})
            res = self.runtime.execute_tool_chain(chain_spec) if hasattr(self.runtime, "execute_tool_chain") else {"ok": False, "error": "Chaining not supported"}
            return RouterResponse(self._format_goal_result(res), data=res)

        if lowered in {"/orchestrator status", "orchestrator status", "orchestrator"}:
            return RouterResponse(self._format_orchestrator_status(self.runtime.orchestrator_status()))

        if lowered in {"/goals", "list goals", "goal history", "goals"}:
            return RouterResponse(self._format_goal_history(self.runtime.list_goal_history()))

        if lowered.startswith("/goal ") or lowered.startswith("goal ") or lowered.startswith("orchestrate "):
            intent = text.split(maxsplit=1)[1].strip()
            return RouterResponse(self._format_goal_result(self.runtime.execute_goal(intent)))

        # Stage 51: Self-Diagnostics & Crash Recovery Daemon
        if lowered in {"/diagnostics", "diagnostics", "system diagnostics", "health scan"}:
            return RouterResponse(self._format_diagnostics(self.runtime.run_system_diagnostics()))

        if lowered in {"/heal", "heal", "self heal", "auto heal", "repair system"}:
            return RouterResponse(self._format_auto_heal(self.runtime.auto_heal_system()))

        if lowered in {"/backup", "backup", "create backups", "snapshot state"}:
            return RouterResponse(self._format_create_backups(self.runtime.create_system_backups()))

        # Stage 50: High-Performance Terminal REPL & Command Palette
        if lowered in {"/repl status", "repl status", "terminal status"}:
            return RouterResponse(self._format_repl_status(self.runtime.terminal_repl_status()))

        if lowered in {"/palette", "palette", "/commands", "commands"}:
            return RouterResponse(self.runtime.terminal_repl.palette.render_help())

        if lowered.startswith("/history") or lowered == "history":
            parts = text.split()
            limit = 20
            if len(parts) > 1 and parts[1].isdigit():
                limit = int(parts[1])
            hist = self.runtime.terminal_repl.history.get_history(limit)
            return RouterResponse(self._format_repl_history(hist))

        # Stage 49: Proactive Workspace Sentinel & Habit Watchdog
        if lowered in {"sentinel status", "workspace sentinel", "watchdog status", "sentinel"}:
            return RouterResponse(self._format_sentinel_status(self.runtime.sentinel_status()))

        if lowered in {"scan workspace", "sentinel scan", "check files", "scan files"}:
            return RouterResponse(self._format_scan_workspace(self.runtime.scan_workspace_now()))

        if lowered in {"sentinel alerts", "show alerts", "alerts", "pending alerts"}:
            return RouterResponse(self._format_sentinel_alerts(self.runtime.get_sentinel_alerts()))

        if lowered in {"start sentinel", "start watchdog"}:
            res = self.runtime.start_sentinel_watcher()
            return RouterResponse(f"Workspace sentinel background watcher started. Status: {res.get('status')}")

        if lowered in {"stop sentinel", "stop watchdog"}:
            res = self.runtime.stop_sentinel_watcher()
            return RouterResponse(f"Workspace sentinel background watcher stopped. Status: {res.get('status')}")

        if lowered in {"provider health check records", "health check records", "list provider health checks", "provider health check dry runs"}:
            return RouterResponse(self._format_provider_health_check_records(self.runtime.list_provider_health_checks()))

        if lowered in {"reset provider health check", "provider health check reset"}:
            return RouterResponse(self._format_provider_health_check_reset(self.runtime.reset_provider_health_check()))

        if lowered in {"dry run provider health check", "dry-run provider health check", "provider health check dry run", "test provider health check"}:
            return RouterResponse(self._format_provider_health_check_dry_run(self.runtime.dry_run_provider_health_check()))

        if lowered.startswith("dry run provider health "):
            provider_name = lowered.replace("dry run provider health ", "", 1).strip()
            return RouterResponse(self._format_provider_health_check_dry_run(self.runtime.dry_run_provider_health_check(provider_name)))

        if lowered in {"session summary", "session"}:
            return RouterResponse(self._format_session_summary(self.runtime.session_summary()))

        if lowered in {"self reflection", "self-reflection", "reflect session"}:
            return RouterResponse(self._format_self_reflection(self.runtime.self_reflection("manual session reflection")))

        if lowered == "session review":
            return RouterResponse(self._format_session_review(self.runtime.session_review()))

        if lowered in {"wake status", "what is your current state"}:
            return RouterResponse(self._format_wake_status(self.runtime.wake_status()))

        if lowered in {"continuity pulse", "wake pulse", "presence pulse"}:
            return RouterResponse(self._format_continuity_pulse(self.runtime.continuity_pulse()))

        if lowered == "wake report":
            return RouterResponse(self._format_wake_report(self.runtime.wake_report()))

        if lowered in {"wake limitations", "current limitations"}:
            return RouterResponse(self._format_wake_limitations(self.runtime.wake_limitations()))

        if lowered in {"what is your next action", "wake next action"}:
            return RouterResponse(self.runtime.wake_status().get("next_action", "Review project summary."))

        if lowered == "drift check":
            return RouterResponse("Drift check needs text. Use: drift check <text>")

        if lowered.startswith("drift check "):
            return RouterResponse(self._format_wake_drift_check(self.runtime.wake_drift_check(text[12:].strip())))

        if lowered == "presence":
            return RouterResponse(self._format_presence_report(self.runtime.presence()))

        if lowered == "memory candidates":
            return RouterResponse(self._format_memory_candidates(self.runtime.memory_candidates()))

        if lowered.startswith("approve memory "):
            return RouterResponse(self._format_memory_candidate_action(self.runtime.approve_memory_candidate(text[15:].strip())))

        if lowered.startswith("reject memory "):
            return RouterResponse(self._format_memory_candidate_action(self.runtime.reject_memory_candidate(text[14:].strip())))

        if lowered == "drift report":
            return RouterResponse(self._format_drift_report(self.runtime.drift_report()))

        if lowered == "write reflection":
            return RouterResponse(self._format_write_reflection(self.runtime.write_reflection()))

        if lowered in {"where did we stop", "where did i stop", "resume point"}:
            return RouterResponse(self._format_where_did_we_stop(self.runtime.where_did_we_stop()))

        if lowered in {"next step", "next action"}:
            return RouterResponse(self._format_next_step(self.runtime.next_step()))

        if lowered in {"task summary", "tasks summary"}:
            return RouterResponse(self._format_task_summary(self.runtime.next_step()))

        if lowered in {"tomorrow plan", "plan tomorrow"}:
            return RouterResponse(self._format_tomorrow_plan(self.runtime.next_step()))

        if lowered.startswith("classify action "):
            return RouterResponse(self._format_classify_action(self.runtime.classify_action(text[16:].strip())))

        if lowered in {"guardian status", "guardian", "safety"}:
            return RouterResponse(self._format_guardian())

        if lowered in {"dashboard", "operator status", "ops"}:
            return RouterResponse(self._format_dashboard())

        if lowered in {"recovered", "recovered summary", "lucy recovered"}:
            return RouterResponse(self._format_recovered_summary(self.runtime.recovered_summary()))

        if lowered in {"recovered checkpoints", "lucy checkpoints", "checkpoint map"}:
            return RouterResponse(self._format_recovered_checkpoints(self.runtime.recovered_checkpoints()))

        if lowered == "brain status":
            return RouterResponse(self._format_brain_status(self.runtime.brain_status()))

        if lowered == "brain router status":
            return RouterResponse(self._format_brain_router_status(self.runtime.brain_router_status()))

        if lowered in {"reasoning status", "reasoning policy"}:
            return RouterResponse(self._format_reasoning_status(self.runtime.reasoning_status()))

        if lowered.startswith("explain route "):
            return RouterResponse(self._format_route_explanation(self.runtime.explain_route(text[14:].strip())))

        if lowered.startswith("route preview "):
            return RouterResponse(self._format_route_preview(self.runtime.route_preview(text[14:].strip())))

        if lowered.startswith("context packet "):
            return RouterResponse(self._format_context_packet(self.runtime.context_packet_preview(text[15:].strip())))

        if lowered.startswith("response frame "):
            return RouterResponse(self._format_response_frame(self.runtime.response_frame_preview(text[15:].strip())))

        if lowered == "api tools":
            return RouterResponse(self._format_external_tools(self.runtime.external_tools_status()))

        if lowered in {"setup nvidia key", "nvidia setup", "nvidia key"}:
            return RouterResponse(self._format_secret_setup(self.runtime.setup_nvidia_key()))

        if lowered in {"set nvidia key", "set nvidea key", "save nvidia key", "save nvidea key"}:
            return RouterResponse(self._format_secret_setup(self.runtime.save_nvidia_key()))

        if lowered in {"nvidia status", "nvidia key status"}:
            return RouterResponse(self._format_secret_status(self.runtime.nvidia_key_status()))

        if lowered in {"forget nvidia key", "forget nvidea key", "remove nvidia key", "remove nvidea key"}:
            return RouterResponse(self._format_secret_forget(self.runtime.forget_nvidia_key()))

        if lowered.startswith("ask "):
            return RouterResponse(self._format_brain_answer(self.runtime.ask_brain(text[4:].strip())))

        if lowered == "learning status":
            return RouterResponse(self._format_learning_status(self.runtime.learning_status()))

        if lowered in {"mind status", "cognition status", "inner state"}:
            return RouterResponse(self._format_cognition_status(self.runtime.cognition_status()))

        if lowered in {"vision", "lucy vision", "her vision"}:
            return RouterResponse(self._format_cognition_vision(self.runtime.cognition_vision()))

        if lowered in {"thoughts", "lucy thoughts", "working thoughts"}:
            return RouterResponse(self._format_cognition_status(self.runtime.cognition_status(), reflections_only=True))

        if lowered in {"think", "reflect", "lucy think"}:
            return RouterResponse(self._format_reflection(self.runtime.reflect("manual_reflection", text)))

        if lowered.startswith("think "):
            return RouterResponse(self._format_reflection(self.runtime.reflect("manual_reflection", text[6:].strip())))

        if lowered.startswith("reflect "):
            return RouterResponse(self._format_reflection(self.runtime.reflect("manual_reflection", text[8:].strip())))

        if lowered.startswith("learn from "):
            return RouterResponse(self._format_learn_from_text(self.runtime.learn_from_text(text[11:].strip())))

        if lowered in {"style status", "talking style", "talking style status"}:
            return RouterResponse(self._format_style_status(self.runtime.style_status()))

        if lowered in {"eat ai collections", "ingest ai collections", "index ai collections", "learn ai collections"}:
            return RouterResponse(self._format_ai_collections_ingest(self.runtime.ingest_ai_collections()))

        if lowered.startswith("eat ai collections "):
            return RouterResponse(self._format_ai_collections_ingest(self.runtime.ingest_ai_collections(text[19:].strip())))

        if lowered in {"ai collections status", "knowledge status", "ai knowledge status"}:
            return RouterResponse(self._format_ai_collections_status(self.runtime.ai_collections_status()))

        if lowered.startswith("search ai collections "):
            return RouterResponse(self._format_ai_collections_search(self.runtime.search_ai_collections(text[22:].strip())))

        if lowered.startswith("search knowledge "):
            return RouterResponse(self._format_ai_collections_search(self.runtime.search_ai_collections(text[17:].strip())))

        if lowered.startswith("learn style "):
            return RouterResponse(self._format_learn_style(self.runtime.learn_style(text[12:].strip())))

        if lowered.startswith("remember style "):
            return RouterResponse(self._format_learn_style(self.runtime.learn_style(text[15:].strip())))

        if lowered.startswith("memory fallback "):
            return RouterResponse(self._format_memory_fallback(self.runtime.memory_fallback(text[16:].strip())))

        if lowered in {"overnight", "overnight 100", "make 100 checkpoints", "make 100 checkpoint"}:
            return RouterResponse(self._format_overnight_checkpoint_run(self.runtime.overnight_checkpoint_run(100)))

        if lowered.startswith("overnight checkpoints"):
            target = self._parse_checkpoint_target(text[len("overnight checkpoints"):].strip(), 100)
            return RouterResponse(self._format_overnight_checkpoint_run(self.runtime.overnight_checkpoint_run(target)))

        if lowered.startswith("make checkpoints"):
            target = self._parse_checkpoint_target(text[len("make checkpoints"):].strip(), 100)
            return RouterResponse(self._format_overnight_checkpoint_run(self.runtime.overnight_checkpoint_run(target)))

        if lowered == "scan project":
            return RouterResponse(self._format_scan_project(self.runtime.scan_project()))

        if lowered == "backup project":
            return RouterResponse(self._format_backup_project(self.runtime.backup_project()))

        if lowered in {"continuity status", "memory backup status", "backup status"}:
            return RouterResponse(self._format_continuity_status(self.runtime.continuity_status()))

        if lowered in {"backup memory", "memory backup", "continuity backup", "backup continuity", "backup now"}:
            return RouterResponse(self._format_continuity_backup(self.runtime.continuity_backup("manual continuity backup")))

        if lowered.startswith("continuity backup "):
            return RouterResponse(self._format_continuity_backup(self.runtime.continuity_backup(text[18:].strip())))

        if lowered == "health":
            return RouterResponse(self._format_health(self.runtime.health()))

        if lowered == "spine":
            return RouterResponse(self._format_spine())

        if lowered in {"agent status", "what are your agents"}:
            return RouterResponse(self._format_internal_agent_status(self.runtime.internal_agent_status()))

        if lowered in {"agent report", "agent cycle test"}:
            return RouterResponse(self._format_internal_agent_report(self.runtime.internal_agent_report(text)))

        if lowered in {"memory agent status", "safety agent status", "reasoning agent status", "learning agent status"}:
            agent_name = text[:-len(" status")].strip()
            return RouterResponse(self._format_internal_agent_single_status(self.runtime.internal_agent_single_status(agent_name)))

        if lowered in {"agents", "list agents"}:
            return RouterResponse(self._format_agents())

        if lowered.startswith("agent "):
            return RouterResponse(self._format_agent(text[6:].strip()))

        if lowered.startswith("check "):
            return RouterResponse(self._format_boundary(self.runtime.check_request(text[6:].strip())))

        if lowered in {"approvals", "pending approvals"}:
            return RouterResponse(self._format_approvals(self.runtime.list_approvals()))

        if lowered == "all approvals":
            return RouterResponse(self._format_approvals(self.runtime.list_approvals(pending_only=False)))

        if lowered.startswith("approve "):
            selector, note = self._split_selector_note(text[8:].strip())
            return RouterResponse(self._format_approval_review(self.runtime.review_approval(selector, "approved", note)))

        if lowered.startswith("reject "):
            selector, note = self._split_selector_note(text[7:].strip())
            return RouterResponse(self._format_approval_review(self.runtime.review_approval(selector, "rejected", note)))

        if lowered.startswith("remember "):
            return RouterResponse(self._format_remember(self.runtime.remember(text[9:].strip())))

        if lowered == "recall":
            return RouterResponse(self._format_recall(self.runtime.recall("")))

        if lowered.startswith("recall "):
            return RouterResponse(self._format_recall(self.runtime.recall(text[7:].strip())))

        if lowered.startswith("search memory "):
            return RouterResponse(self._format_recall(self.runtime.recall(text[14:].strip())))

        if lowered.startswith("forget "):
            return RouterResponse(self._format_forget(self.runtime.forget(text[7:].strip())))

        if lowered == "memory audit":
            return RouterResponse(self._format_memory_audit(self.runtime.memory_audit()))

        if lowered in {"permanent memory", "permanent memory status", "memory status"}:
            return RouterResponse(self._format_permanent_memory_status(self.runtime.memory_audit()))

        if lowered == "safe tools status":
            return RouterResponse(self._format_safe_tool_result(self.runtime.safe_tools_status()))

        if lowered == "tool policy":
            return RouterResponse(self._format_tool_policy(self.runtime.tool_policy_status()))

        if lowered == "tool audit":
            return RouterResponse(self._format_tool_audit(self.runtime.tool_audit_summary()))

        if lowered == "pending confirmations":
            return RouterResponse(self._format_pending_confirmations(self.runtime.pending_tool_confirmations()))

        if lowered.startswith("approve tool "):
            return RouterResponse(self._format_tool_confirmation_result(self.runtime.approve_tool_confirmation(text[13:].strip())))

        if lowered.startswith("reject tool "):
            return RouterResponse(self._format_tool_confirmation_result(self.runtime.reject_tool_confirmation(text[12:].strip())))

        folder_prefixes = (
            "create folder ", "make folder ", "mkdir ", "/mkdir ",
            "make an folder ", "make a folder ", "create an folder ", "create a folder ",
            "make an new folder ", "make a new folder ", "create an new folder ", "create a new folder ",
            "make new folder ", "create new folder ", "setup folder ", "build folder ",
        )
        if any(lowered.startswith(p) for p in folder_prefixes):
            matched_p = next(p for p in folder_prefixes if lowered.startswith(p))
            raw_arg = text[len(matched_p):].strip()
            for lead in ("called ", "named ", "at "):
                if raw_arg.lower().startswith(lead):
                    raw_arg = raw_arg[len(lead):].strip()
            folder_arg = raw_arg.strip().strip('"').strip("'")

            if not folder_arg:
                return RouterResponse("Usage: create folder <path> | make folder <path> | mkdir <path>")

            res = self.runtime.create_folder(folder_arg)
            if res.get("ok"):
                action_word = "Created folder" if res.get("created") else "Folder already exists at"
                msg = f"{action_word}: {res.get('relative_path')} ({res.get('path')})"
                return RouterResponse(msg, data=res)
            return RouterResponse(f"Failed to create folder: {res.get('error', 'Unknown error')}", data=res)

        if lowered == "approved folders":
            return RouterResponse(self._format_safe_tool_result(self.runtime.approved_folders()))

        if lowered.startswith("approve folder "):
            return RouterResponse(self._format_safe_tool_result(self.runtime.approve_folder(text[15:].strip())))

        if lowered.startswith("remove approved folder "):
            return RouterResponse(self._format_safe_tool_result(self.runtime.remove_approved_folder(text[23:].strip())))

        if lowered == "workspace tree":
            return RouterResponse(self._format_safe_tool_result(self.runtime.workspace_tree()))

        if lowered.startswith("workspace tree "):
            return RouterResponse(self._format_safe_tool_result(self.runtime.workspace_tree(text[15:].strip())))

        if lowered.startswith("search files "):
            return RouterResponse(self._format_safe_tool_result(self.runtime.search_files(text[13:].strip())))

        if lowered.startswith("file info "):
            return RouterResponse(self._format_safe_tool_result(self.runtime.file_info(text[10:].strip())))

        if lowered.startswith("read file "):
            return RouterResponse(self._format_safe_tool_result(self.runtime.read_file(text[10:].strip())))

        if lowered in {"workspace", "files"}:
            return RouterResponse(self._format_workspace(self.runtime.project_workspace_tree()))

        if lowered.startswith("find file "):
            return RouterResponse(self._format_find_files(self.runtime.find_files(text[10:].strip())))

        if lowered.startswith("search text "):
            return RouterResponse(self._format_text_search(self.runtime.search_text(text[12:].strip())))

        if lowered.startswith("search "):
            return RouterResponse(self._format_text_search(self.runtime.search_text(text[7:].strip())))

        if lowered in {"system", "system status", "computer status"}:
            return RouterResponse(self._format_system(self.runtime.system_snapshot()))

        if lowered in {"logs", "show logs"}:
            return RouterResponse(self._format_logs(self.runtime.recent_logs()))

        if lowered.startswith("logs "):
            return RouterResponse(self._format_logs(self.runtime.recent_logs(self._parse_int(text[5:].strip(), 10))))

        if lowered.startswith("show logs "):
            return RouterResponse(self._format_logs(self.runtime.recent_logs(self._parse_int(text[10:].strip(), 10))))

        if lowered in {"projects", "list projects"}:
            return RouterResponse(self._format_projects(self.runtime.list_projects()))

        if lowered.startswith("set active project "):
            name = text[len("set active project "):].strip()
            return RouterResponse(self._format_set_project(self.runtime.set_active_project(name)))

        if lowered.startswith("active project "):
            name = text[len("active project "):].strip()
            return RouterResponse(self._format_set_project(self.runtime.set_active_project(name)))

        if lowered.startswith("add task "):
            return RouterResponse(self._format_add_task(self.runtime.add_task(text[9:].strip())))

        if lowered.startswith("complete task "):
            return RouterResponse(self._format_complete_task(self.runtime.complete_task(text[14:].strip())))

        if lowered in {"show tasks", "tasks"}:
            return RouterResponse(self._format_tasks(self.runtime.show_tasks()))

        if lowered in {"show all tasks", "all tasks"}:
            return RouterResponse(self._format_tasks(self.runtime.show_tasks(include_done=True)))

        if lowered.startswith("add reminder "):
            reminder_text, due = self._split_due(text[13:].strip())
            return RouterResponse(self._format_add_reminder(self.runtime.add_reminder(reminder_text, due=due)))

        if lowered.startswith("remind me "):
            reminder_text, due = self._split_due(text[10:].strip())
            return RouterResponse(self._format_add_reminder(self.runtime.add_reminder(reminder_text, due=due)))

        if lowered in {"reminders", "show reminders"}:
            return RouterResponse(self._format_reminders(self.runtime.list_reminders()))

        if lowered.startswith("complete reminder "):
            return RouterResponse(self._format_complete_reminder(self.runtime.complete_reminder(text[18:].strip())))

        if lowered == "daily brief":
            return RouterResponse(self._format_daily_brief(self.runtime.daily_brief()))

        if lowered == "daily checkin":
            return RouterResponse(self._format_daily_checkin(self.runtime.daily_checkin()))

        if lowered.startswith("daily checkin "):
            return RouterResponse(self._format_daily_checkin(self.runtime.daily_checkin(text[14:].strip())))

        if lowered in {"today log", "show today log"}:
            return RouterResponse(self._format_daily_log(self.runtime.today_log(), title="Today log"))

        if lowered in {"yesterday summary", "yesterday log"}:
            return RouterResponse(self._format_daily_log(self.runtime.yesterday_summary(), title="Yesterday summary"))

        if lowered in {"weekly review", "week review"}:
            return RouterResponse(self._format_weekly_review(self.runtime.weekly_review()))

        if lowered == "project summary":
            return RouterResponse(self._format_project_summary(self.runtime.project_summary()))

        if lowered.startswith("project summary "):
            name = text[len("project summary "):].strip()
            return RouterResponse(self._format_project_summary(self.runtime.project_summary(name)))

        if lowered.startswith("checkpoint "):
            reason = text[11:].strip()
            return RouterResponse(self._format_checkpoint(self.runtime.create_checkpoint(reason=reason)))

        if lowered.startswith("plan "):
            return RouterResponse(self._format_plan(text[5:].strip()))

        # Stage 44: Resolve explicit @alias / $alias tokens for natural conversation
        if ("@" in text or "$" in text) and hasattr(self.runtime, "personal_profiler") and hasattr(self.runtime.personal_profiler, "resolve_alias"):
            text = self.runtime.personal_profiler.resolve_alias(text)

        return RouterResponse(self.runtime.lucy_respond(text))

    def _split_due(self, text: str) -> tuple[str, str | None]:
        marker = " due "
        lowered = text.lower()
        if marker in lowered:
            index = lowered.rfind(marker)
            return text[:index].strip(), text[index + len(marker):].strip()
        return text, None

    def _split_selector_note(self, text: str) -> tuple[str, str]:
        parts = text.split(maxsplit=1)
        if not parts:
            return "", ""
        if len(parts) == 1:
            return parts[0], ""
        return parts[0], parts[1]

    def _parse_int(self, text: str, default: int) -> int:
        try:
            value = int(text)
        except ValueError:
            return default
        return max(1, min(value, 50))

    def _parse_checkpoint_target(self, text: str, default: int) -> int:
        if not text:
            return default
        for part in text.split():
            if part.isdigit():
                return max(1, min(int(part), 500))
        return default

    def _help(self) -> str:
        return "\n".join(
            [
                "Lucy commands:",
                "  help",
                "  status",
                "  session status",
                "  runtime status",
                "  persistent runtime status",
                "  recovery status",
                "  heartbeat status",
                "  access status",
                "  safe access status",
                "  access policy",
                "  local access status",
                "  first thought status",
                "  first thought readiness",
                "  assemble first thought",
                "  show first thought",
                "  self model status",
                "  self model",
                "  what are you",
                "  what can you do",
                "  what can you not do",
                "  what is your current stage",
                "  what are your limits",
                "  growth proposals status",
                "  growth proposals",
                "  propose growth",
                "  show growth proposals",
                "  growth proposal status",
                "  reject growth proposal [id]",
                "  approve growth proposal for future [id]",
                "  evaluation lab status",
                "  evaluation status",
                "  evaluate growth proposals",
                "  evaluate proposal [id]",
                "  show evaluations",
                "  shadow testing status",
                "  shadow status",
                "  run shadow test",
                "  shadow test proposal [id]",
                "  show shadow tests",
                "  patch pipeline status",
                "  approved patch pipeline status",
                "  create patch plan [id]",
                "  prepare patch plan [id]",
                "  show patch plans",
                "  patch plan status",
                "  experience storage status",
                "  experience status",
                "  record experience",
                "  record stage experience",
                "  show experiences",
                "  show experience records",
                "  identity stability status",
                "  identity status",
                "  check identity stability",
                "  identity check",
                "  show identity checks",
                "  show identity stability checks",
                "  long-term strategy status",
                "  strategy status",
                "  create long-term strategy",
                "  create strategy",
                "  show long-term strategies",
                "  show strategies",
                "  smart organizer status",
                "  organizer status",
                "  create organizer item",
                "  create organizer",
                "  show organizer items",
                "  organizer items",
                "  safe local actions status",
                "  safe action status",
                "  create safe action proposal",
                "  dry run safe action",
                "  show safe action proposals",
                "  safe actions",
                "  external app bridge status",
                "  app bridge status",
                "  create external app bridge proposal",
                "  create bridge proposal",
                "  dry run external app bridge",
                "  show external app bridge proposals",
                "  bridge proposals",
                "  proactive awareness status",
                "  awareness status",
                "  create proactive awareness scan",
                "  create awareness scan",
                "  dry run proactive awareness",
                "  show proactive awareness scans",
                "  awareness scans",
                "  deep recall status",
                "  recall status",
                "  create deep recall session",
                "  deep recall",
                "  recall safe <query>",
                "  dry run deep recall",
                "  show deep recall sessions",
                "  recall sessions",
                "  judgment status",
                "  judgement status",
                "  create judgment record",
                "  judgment",
                "  judge <situation>",
                "  dry run judgment",
                "  show judgments",
                "  judgments",
                "  adaptive communication status",
                "  adaptive status",
                "  create adaptive communication profile",
                "  adaptive communication",
                "  adaptive communication <context>",
                "  style profile <context>",
                "  dry run adaptive communication",
                "  show style profiles",
                "  human state awareness status",
                "  human state status",
                "  create human state signal",
                "  human state awareness",
                "  human state <explicit signal>",
                "  state signal <explicit signal>",
                "  dry run human state awareness",
                "  show state signals",
                "  time awareness status",
                "  time status",
                "  create time context",
                "  time awareness",
                "  time awareness <explicit time context>",
                "  time context <explicit time context>",
                "  dry run time awareness",
                "  show time contexts",
                "  autonomy boundaries status",
                "  autonomy status",
                "  create autonomy boundary record",
                "  autonomy boundaries",
                "  autonomy boundaries <request>",
                "  boundary record <request>",
                "  dry run autonomy boundaries",
                "  show boundary records",
                "  provider identity boundary status",
                "  provider identity status",
                "  create provider identity boundary record",
                "  provider identity boundary",
                "  provider identity boundary <context>",
                "  provider boundary <context>",
                "  api identity boundary <context>",
                "  dry run provider identity boundary",
                "  show provider identity boundary records",
                "  secrets provider key safety status",
                "  secret safety status",
                "  create secret safety record",
                "  secret safety <context>",
                "  provider key safety <context>",
                "  api key safety <context>",
                "  safe key file scan",
                "  dry run secrets safety",
                "  show secret safety records",
                "  provider registry status",
                "  provider registry",
                "  list providers",
                "  show provider <name>",
                "  enable provider <name>",
                "  disable provider <name>",
                "  dry run provider registry",
                "  reset provider registry",
                "  save state",
                "  session summary",
                "  self reflection",
                "  session review",
                "  wake status",
                "  continuity pulse",
                "  wake report",
                "  what is your current state",
                "  what is your next action",
                "  wake limitations",
                "  drift check <text>",
                "  presence",
                "  memory candidates",
                "  approve memory <id>",
                "  reject memory <id>",
                "  drift report",
                "  write reflection",
                "  where did we stop",
                "  next step",
                "  classify action <text>",
                "  guardian status",
                "  dashboard",
                "  recovered",
                "  recovered checkpoints",
                "  brain status",
                "  brain router status",
                "  reasoning status",
                "  reasoning policy",
                "  explain route <text>",
                "  route preview <text>",
                "  context packet <text>",
                "  response frame <text>",
                "  api tools",
                "  setup nvidia key",
                "  set nvidia key",
                "  nvidia key status",
                "  forget nvidia key",
                "  ask <question>",
                "  learning status",
                "  mind status",
                "  vision",
                "  thoughts",
                "  think [topic]",
                "  learn from <lesson>",
                "  style status",
                "  learn style <talking preference>",
                "  eat ai collections",
                "  ai collections status",
                "  search ai collections <query>",
                "  memory fallback <query>",
                "  overnight checkpoints [count]",
                "  scan project",
                "  backup project",
                "  continuity status",
                "  backup memory",
                "  remember <fact>",
                "  recall [keyword]",
                "  search memory <keyword>",
                "  forget <specific memory>",
                "  memory audit",
                "  permanent memory",
                "  safe tools status",
                "  tool policy",
                "  tool audit",
                "  pending confirmations",
                "  approve tool <id>",
                "  reject tool <id>",
                "  approved folders",
                "  approve folder <path>",
                "  remove approved folder <id>",
                "  workspace",
                "  workspace tree [folder_id]",
                "  find file <name>",
                "  search text <query>",
                "  search files <query>",
                "  read file <approved/path>",
                "  file info <approved/path>",
                "  system status",
                "  logs [count]",
                "  show logs [count]",
                "  list projects",
                "  set active project <name>",
                "  add task <task>",
                "  show tasks",
                "  complete task <number/id/text>",
                "  task summary",
                "  project summary [name]",
                "  tomorrow plan",
                "  add reminder <text> [due ISO-date]",
                "  reminders",
                "  complete reminder <number/id/text>",
                "  daily brief",
                "  daily checkin [field=value ... notes]",
                "  today log",
                "  yesterday summary",
                "  weekly review",
                "  check <request>",
                "  approvals",
                "  approve <id-prefix> [note]",
                "  reject <id-prefix> [note]",
                "  checkpoint <reason>",
                "  plan <goal>",
                "  health",
                "  spine",
                "  agent status",
                "  agent report",
                "  what are your agents",
                "  memory agent status",
                "  safety agent status",
                "  reasoning agent status",
                "  learning agent status",
                "  agent cycle test",
                "  agents",
                "  agent <ID>",
                "  exit",
            ]
        )

    def _format_recovered_summary(self, summary: dict) -> str:
        notes = summary.get("notes", [])
        lines = [
            "Recovered Lucy architecture:",
            f"  Source: {summary.get('source', 'unknown')}",
            f"  Highest recovered checkpoint: {summary.get('highest_recovered_checkpoint', 'unknown')}",
            f"  Confidence: {summary.get('confidence', 'unknown')}",
            f"  Checkpoints mapped: {summary.get('checkpoint_count', 0)}",
        ]
        for note in notes:
            lines.append(f"  - {note}")
        return "\n".join(lines)

    def _format_recovered_checkpoints(self, checkpoints: list[dict]) -> str:
        if not checkpoints:
            return "No recovered checkpoint map found."
        lines = ["Recovered checkpoint map:"]
        for item in checkpoints:
            lines.append(f"  {item.get('checkpoint', '?')}: {item.get('desc', '')}")
        return "\n".join(lines)

    def _format_brain_status(self, status: dict) -> str:
        return "\n".join(
            [
                "Lucy brain router:",
                f"  Local fallback: {status['local_fallback']}",
                f"  Response checker: {status['response_checker']}",
                f"  External API enabled: {status['external_api_enabled']}",
                f"  External API modes: {', '.join(status['external_api_modes'])}",
                f"  NVIDIA key available: {status.get('nvidia_key_available', False)}",
                f"  Note: {status['note']}",
            ]
        )

    def _format_brain_router_status(self, status: dict) -> str:
        reasoning = status.get("reasoning_status", {})
        return "\n".join(
            [
                "Lucy brain router detailed status:",
                f"  Local fallback: {status.get('local_fallback')}",
                f"  Response checker: {status.get('response_checker')}",
                f"  Stage 6 routing: {status.get('stage6_reasoning_router')}",
                f"  Reasoning mode: {reasoning.get('reasoning_mode_default', 'local_policy_only')}",
                f"  External brain enabled: {status.get('external_brain_enabled', False)}",
                f"  External API requires confirmation: {status.get('external_api_requires_confirmation', True)}",
                "  Hidden reasoning output: disabled.",
            ]
        )

    def _format_reasoning_status(self, status: dict) -> str:
        brain = status.get("brain_router", {})
        policy = brain.get("reasoning_policy", {})
        categories = policy.get("categories", [])
        lines = [
            "Lucy reasoning router:",
            f"  Enabled: {status.get('stage6_reasoning_router_enabled')}",
            f"  Mode: {status.get('reasoning_mode_default')}",
            f"  External brain enabled: {status.get('external_brain_enabled')}",
            f"  External API requires confirmation: {status.get('external_api_requires_confirmation')}",
            "  Hidden reasoning output: disabled.",
            "  Categories:",
        ]
        lines.extend(f"    - {category}" for category in categories)
        return "\n".join(lines)

    def _format_route_explanation(self, result: dict) -> str:
        decision = result.get("route_decision", {})
        guardian = result.get("guardian_classification", {})
        return "\n".join(
            [
                "Route explanation:",
                f"  Decision: {decision.get('decision')}",
                f"  Reason: {decision.get('reason')}",
                f"  Required context: {', '.join(decision.get('required_context', [])) or 'none'}",
                f"  Guardian required: {decision.get('guardian_required')}",
                f"  Tool required: {decision.get('tool_required')}",
                f"  External API allowed: {decision.get('external_api_allowed')}",
                f"  Confidence: {decision.get('confidence')}",
                f"  Guardian classification: {guardian.get('classification')}",
                "  Hidden reasoning output: disabled.",
                "  No tools executed. No online call made.",
            ]
        )

    def _format_route_preview(self, result: dict) -> str:
        frame = result.get("response_frame", {})
        decision = frame.get("route_decision", {})
        safety = frame.get("safety_status", {})
        return "\n".join(
            [
                "Route preview:",
                f"  Intent: {frame.get('user_intent', '')}",
                f"  Decision: {decision.get('decision')}",
                f"  Reason: {decision.get('reason')}",
                f"  Context: {', '.join(frame.get('context_used', [])) or 'none'}",
                f"  Guardian: {safety.get('guardian_classification')}",
                f"  External API allowed: {safety.get('external_api_allowed')}",
                f"  Next action: {frame.get('next_action')}",
                f"  Tool recommendation: {frame.get('tool_action_recommendation')}",
                "  Hidden reasoning output: disabled.",
                "  Preview only. No tools executed. No online call made.",
            ]
        )

    def _format_context_packet(self, result: dict) -> str:
        packet = result.get("context_packet", {})
        route = packet.get("route_decision", {})
        memories = packet.get("memory_recall_summaries", [])
        lines = [
            "Context packet preview:",
            f"  Active project: {packet.get('active_project_name', 'Lucy')}",
            f"  Current checkpoint: {packet.get('current_checkpoint') or 'none'}",
            f"  Next action: {packet.get('next_action') or 'not set'}",
            f"  Last command: {packet.get('last_command_summary') or 'none'}",
            f"  Route: {route.get('decision')}",
            f"  Required context: {', '.join(route.get('required_context', [])) or 'none'}",
            f"  Memory summaries: {len(memories)}",
            f"  Daily context: {'available' if packet.get('daily_context_summary', {}).get('has_today_log') else 'not logged today'}",
            f"  Guardian protected actions blocked: {packet.get('guardian_status', {}).get('protected_actions_blocked', True)}",
            "  Hidden reasoning output: disabled.",
            "  Preview only. No tools executed. No online call made.",
        ]
        for item in memories[:3]:
            lines.append(f"  - Memory {item.get('id')}: {item.get('summary')}")
        return "\n".join(lines)

    def _format_response_frame(self, result: dict) -> str:
        frame = result.get("response_frame", {})
        safety = frame.get("safety_status", {})
        return "\n".join(
            [
                "Response frame preview:",
                f"  Route: {frame.get('route')}",
                f"  Visible answer: {frame.get('visible_answer')}",
                f"  Uncertainty: {frame.get('uncertainty') or 'none'}",
                f"  Next action: {frame.get('next_action')}",
                f"  Requires confirmation: {frame.get('requires_confirmation')}",
                f"  Blocked reason: {frame.get('blocked_reason') or 'none'}",
                f"  External API allowed: {safety.get('external_api_allowed', False)}",
                f"  Tool recommendation: {frame.get('tool_recommendation')}",
                "  Hidden reasoning output: disabled.",
                "  Preview only. No tools executed. No online call made.",
            ]
        )

    def _format_external_tools(self, status: dict) -> str:
        lines = ["External API tools:"]
        for tool in status.get("tools", []):
            lines.append(f"  - {tool['name']}")
            lines.append(f"    Available: {tool['available']}")
            lines.append(f"    Role: {tool['role']}")
            lines.append(f"    Model: {tool['model']}")
        return "\n".join(lines)

    def _format_secret_setup(self, result: dict) -> str:
        if not result.get("saved"):
            return f"NVIDIA key not saved: {result.get('reason', 'unknown reason')}"
        if result.get("scope") == "permanent_encrypted_current_windows_user":
            return "\n".join(
                [
                    "NVIDIA key saved permanently.",
                    f"  Scope: {result['scope']}",
                    f"  Storage: {result['storage']}",
                    f"  File: {result['path']}",
                    "Lucy saved an encrypted blob only, not the plain key.",
                ]
            )
        return "\n".join(
            [
                "NVIDIA key accepted.",
                f"  Scope: {result['scope']}",
                f"  Env var: {result['env_var']}",
                "Lucy did not write the key to memory, logs, or config.",
            ]
        )

    def _format_secret_status(self, status: dict) -> str:
        return "\n".join(
            [
                "NVIDIA key status:",
                f"  Available: {status['available']}",
                f"  Source: {status['source']}",
                f"  Env var: {status['env_var']}",
                f"  Permanent file: {status.get('persistent_path', '') or 'not configured'}",
            ]
        )

    def _format_secret_forget(self, result: dict) -> str:
        if result.get("forgotten"):
            return "Permanent NVIDIA key removed. Session/environment key was also cleared."
        return f"Permanent NVIDIA key unchanged: {result.get('reason', 'unknown reason')}"

    def _format_learning_status(self, status: dict) -> str:
        return "\n".join(
            [
                "Lucy learning loop:",
                f"  Mode: {status['mode']}",
                f"  Interactions saved: {status['interactions']}",
                f"  Checkpoint lessons: {status.get('checkpoint_lessons', 0)}",
                f"  Local lessons: {status['local_lessons']}",
                f"  Style preferences: {status.get('style_preferences', 0)}",
                f"  Open proposals: {status['open_proposals']}",
                f"  Folder: {status['learning_dir']}",
            ]
        )

    def _format_cognition_status(self, status: dict, reflections_only: bool = False) -> str:
        reflections = status.get("latest_reflections", [])
        if reflections_only:
            if not reflections:
                return "Lucy has no working reflections recorded yet. Run: think"
            lines = ["Lucy working thoughts:"]
        else:
            focus = status.get("current_focus", {})
            lines = [
                "Lucy cognition state:",
                f"  Mode: {status.get('mode', '')}",
                f"  File: {status.get('file', '')}",
                f"  Reflection count: {status.get('reflection_count', 0)}",
                f"  Current project: {focus.get('project', 'Lucy')}",
                f"  Current focus: {focus.get('next_action', 'not set')}",
                f"  Current boundary: {focus.get('risk', 'not set')}",
                "  Recent working thoughts:",
            ]
        for item in reflections[-5:]:
            lines.append(f"  - [{item.get('id', '')}] {item.get('observation', '')}")
            lines.append(f"    Priority: {item.get('priority', '')}")
            lines.append(f"    Boundary: {item.get('boundary', '')}")
        return "\n".join(lines)

    def _format_cognition_vision(self, data: dict) -> str:
        vision = data.get("vision", {})
        lines = [
            "Lucy vision:",
            f"  North star: {vision.get('north_star', '')}",
            f"  Identity boundary: {vision.get('identity_boundary', '')}",
            f"  Build philosophy: {vision.get('build_philosophy', '')}",
            "  Drives:",
        ]
        for drive in data.get("drives", []):
            lines.append(f"  - {drive}")
        focus = data.get("current_focus", {})
        lines.append("  Current focus:")
        lines.append(f"  - {focus.get('next_action', 'not set')}")
        lines.append(f"  - Boundary: {focus.get('risk', 'not set')}")
        return "\n".join(lines)

    def _format_reflection(self, thought: dict) -> str:
        return "\n".join(
            [
                "Lucy reflected:",
                f"  Thought: {thought.get('id', '')}",
                f"  Observation: {thought.get('observation', '')}",
                f"  Priority: {thought.get('priority', '')}",
                f"  Boundary: {thought.get('boundary', '')}",
            ]
        )

    def _format_learn_from_text(self, result: dict) -> str:
        if not result.get("saved"):
            return f"Lesson not saved: {result.get('reason', 'unknown reason')}"
        lesson = result["lesson"]
        return f"Local lesson saved [{lesson['id']}]: {lesson['text']}"

    def _format_learn_style(self, result: dict) -> str:
        if result.get("duplicate"):
            preference = result["preference"]
            return f"Talking style already remembered [{preference['id']}]: {preference['text']}"
        if not result.get("saved"):
            return f"Talking style not saved: {result.get('reason', 'unknown reason')}"
        preference = result["preference"]
        return f"Talking style saved [{preference['id']}]: {preference['text']}"

    def _format_style_status(self, status: dict) -> str:
        lines = [
            "Lucy talking style:",
            f"  Mode: {status['mode']}",
            f"  Preferences: {status['preference_count']}",
            f"  File: {status['file']}",
        ]
        for item in status.get("preferences", [])[-6:]:
            lines.append(f"  - [{item['id']}] {item['text']}")
        return "\n".join(lines)

    def _format_ai_collections_ingest(self, result: dict) -> str:
        if not result.get("ok"):
            return f"AI Collections ingestion failed: {result.get('reason', 'unknown reason')}"
        counts = result.get("counts", {})
        return "\n".join(
            [
                "AI Collections ingested:",
                f"  Root: {result.get('root', '')}",
                f"  Index: {result.get('index_file', '')}",
                f"  Files seen: {counts.get('total_files', 0)}",
                f"  Text/code indexed: {counts.get('indexed_text', 0)}",
                f"  Metadata-only: {counts.get('metadata_only', 0)}",
                f"  Too large: {counts.get('too_large', 0)}",
                f"  Redacted files: {counts.get('redacted', 0)}",
                f"  Skipped dependency/cache dirs: {counts.get('skipped_dirs', 0)}",
                "  Secret-looking files and key vaults were not stored as raw content.",
            ]
        )

    def _format_ai_collections_status(self, status: dict) -> str:
        if not status.get("available"):
            return f"AI Collections knowledge is empty: {status.get('reason', 'no index')}"
        counts = status.get("counts", {})
        return "\n".join(
            [
                "AI Collections knowledge:",
                f"  Root: {status.get('root', '')}",
                f"  Index: {status.get('index_file', '')}",
                f"  Updated: {status.get('updated_at', '')}",
                f"  Files seen: {counts.get('total_files', 0)}",
                f"  Text/code indexed: {counts.get('indexed_text', 0)}",
                f"  Metadata-only: {counts.get('metadata_only', 0)}",
                f"  Too large: {counts.get('too_large', 0)}",
                f"  Redacted files: {counts.get('redacted', 0)}",
            ]
        )

    def _format_ai_collections_search(self, result: dict) -> str:
        matches = result.get("matches", [])
        if not matches:
            return f"No AI Collections matches: {result.get('reason', 'nothing matched')}"
        lines = [f"AI Collections matches for {result.get('query', '')!r}:"]
        for item in matches:
            lines.append(f"  - {item.get('path', '')} [{item.get('status', '')}]")
            summary = item.get("summary", "")
            if summary:
                lines.append(f"    {summary[:220]}")
            symbols = item.get("symbols", [])
            if symbols:
                lines.append(f"    Symbols: {', '.join(symbols[:4])}")
            if item.get("redacted"):
                lines.append("    Redacted sensitive-looking content.")
        return "\n".join(lines)

    def _format_memory_fallback(self, result: dict) -> str:
        if result.get("source") == "local_memory":
            lines = ["Memory fallback used local memory:"]
            for item in result.get("matches", [])[:5]:
                lines.append(f"  - [{item['id']}] {item['fact']}")
            return "\n".join(lines)

        if result.get("source") == "missing_api_key":
            proposal = result.get("proposal", {})
            return "\n".join(
                [
                    result.get("message", "NVIDIA key missing."),
                    f"Open proposal: {proposal.get('id', 'none')}",
                    "Run: setup nvidia key",
                ]
            )

        api_result = result.get("result", {})
        if not api_result.get("ok"):
            return f"NVIDIA memory fallback failed: {api_result.get('reason', 'unknown reason')}"
        proposal = api_result.get("proposal", {})
        return "\n".join(
            [
                "NVIDIA memory fallback returned a suggestion.",
                f"Provider: {api_result.get('provider')}",
                f"Model: {api_result.get('model')}",
                f"Saved as proposal: {proposal.get('id', 'none')}",
                "",
                api_result.get("text", ""),
            ]
        )

    def _format_overnight_checkpoint_run(self, result: dict) -> str:
        lines = [
            "Overnight checkpoint run:",
            f"  Target checkpoints: {result['target']}",
            f"  Started with: {result['start_count']}",
            f"  Created now: {result['created_count']}",
            f"  Final total: {result['final_count']}",
            f"  Checkpoint learning traces: {result['learning_traces']}",
            f"  Health before: {'passed' if result['before_health_passed'] else 'failed'}",
            f"  Health after: {'passed' if result['after_health_passed'] else 'failed'}",
            f"  Fallback learning: {result['fallback_learning']}",
        ]
        created = result.get("created", [])
        if created:
            lines.append("  Recent checkpoints:")
            for item in created[-5:]:
                lines.append(f"    - {item['checkpoint_id']} [{item['focus']}]")
        else:
            lines.append("  No new checkpoints were needed.")
        return "\n".join(lines)

    def _format_brain_answer(self, answer: dict) -> str:
        lines = [
            f"Brain mode: {answer['mode']}",
            f"OK: {answer['ok']}",
            "",
            answer["text"],
        ]
        if answer.get("warnings"):
            lines.append("")
            lines.append("Warnings:")
            lines.extend(f"  - {warning}" for warning in answer["warnings"])
        return "\n".join(lines)

    def _format_scan_project(self, report: dict) -> str:
        lines = [
            "Project scan complete:",
            f"  Report: {report.get('report_path', 'not saved')}",
            f"  Checks: {len(report.get('checks', []))}",
            f"  Suggestions: {len(report.get('suggestions', []))}",
        ]
        for suggestion in report.get("suggestions", [])[:8]:
            lines.append(f"  - {suggestion['file']}: review {suggestion['marker']}")
        return "\n".join(lines)

    def _format_backup_project(self, result: dict) -> str:
        if not result.get("created"):
            return f"Backup failed: {result.get('reason', 'unknown reason')}"
        return "\n".join(
            [
                "Project backup created:",
                f"  Path: {result['path']}",
                f"  Files: {result['files']}",
            ]
        )

    def _format_continuity_backup(self, result: dict) -> str:
        if not result.get("created"):
            return f"Continuity backup not created: {result.get('reason', 'unknown reason')}"
        lines = [
            "Continuity backup created:",
            f"  Path: {result['path']}",
            f"  Files: {result['files']}",
            f"  Trigger: {result.get('trigger', 'manual')}",
            f"  Next auto backup after: {result.get('next_auto_backup_after', 'unknown')} meaningful changes",
            "  Excludes: secrets, API keys, provider vaults, logs, knowledge indexes, and backup folders.",
        ]
        skipped = result.get("skipped", [])
        if skipped:
            lines.append(f"  Skipped files/areas: {len(skipped)}")
        return "\n".join(lines)

    def _format_continuity_status(self, status: dict) -> str:
        lines = [
            "Lucy continuity memory:",
            f"  Mode: {status.get('mode', 'unknown')}",
            f"  Backup count: {status.get('backup_count', 0)}",
            f"  Change counter: {status.get('change_counter', 0)} / {status.get('next_auto_backup_after', 'unknown')}",
            f"  Last backup: {status.get('last_backup_at') or 'none'}",
            f"  Retention: newest {status.get('retention', 'unknown')} backups",
            f"  Folder: {status.get('continuity_dir', '')}",
            f"  Survives: {status.get('survives', '')}",
            f"  Does not survive: {status.get('does_not_survive', '')}",
            "  Excludes: secrets, API keys, provider vaults, logs, knowledge indexes, and backup folders.",
        ]
        backups = status.get("latest_backups", [])
        if backups:
            lines.append("  Latest backups:")
            for item in backups[:5]:
                lines.append(f"    - {item['path']} ({item['size']} bytes)")
        else:
            lines.append("  Latest backups: none yet")
        return "\n".join(lines)

    def _format_session_status(self, status: dict, saved: bool = False) -> str:
        lines = ["Active session save completed." if saved else "Session state:"]
        if saved:
            lines.append("  Graceful shutdown remains False until exit.")
        lines.extend(
            [
                f"  Session count: {status.get('session_count', 0)}",
                f"  Last opened: {status.get('last_opened') or 'unknown'}",
                f"  Last closed: {status.get('last_closed') or 'not closed yet'}",
                f"  Graceful shutdown: {status.get('graceful_shutdown')}",
                f"  Crash recovery needed: {status.get('crash_recovery_needed')}",
                f"  Active project: {status.get('active_project') or 'Lucy'}",
                f"  Current checkpoint: {status.get('current_checkpoint') or 'none'}",
                f"  Next action: {status.get('next_action') or 'not set'}",
                f"  File: {status.get('file', '')}",
            ]
        )
        return "\n".join(lines)

    def _format_session_summary(self, summary: dict) -> str:
        return "\n".join(
            [
                "Session summary:",
                f"  Session count: {summary.get('session_count', 0)}",
                f"  Crash recovery needed: {summary.get('crash_recovery_needed')}",
                f"  Active project: {summary.get('active_project')}",
                f"  Next action: {summary.get('next_action') or 'not set'}",
                f"  Last command: {summary.get('last_command') or 'none'}",
                f"  Last response: {summary.get('last_response_summary') or 'none'}",
            ]
        )

    def _format_current_lucy_status(self, status: dict) -> str:
        return "\n".join(
            [
                "Lucy status:",
                f"  Active stage: {status.get('active_stage', '18 experience storage')}",
                f"  Active project: {status.get('active_project', 'Lucy')}",
                f"  Guardian: {status.get('guardian_status', 'active')}",
                f"  Runtime recovery: {status.get('runtime_recovery_status', 'unknown')}",
                f"  Agents: {status.get('agents_status', 'unknown')}",
                f"  Evaluation lab: {status.get('evaluation_lab', 'active')}",
                f"  Shadow testing: {status.get('shadow_testing', 'active')}",
                f"  Patch pipeline: {status.get('patch_pipeline', 'active')}",
                f"  Real patching: {status.get('real_patching', 'disabled')}",
                f"  Experience storage: {status.get('experience_storage', 'active')}",
                f"  Experience records: {status.get('experience_records', 0)}",
                "  Deep recall: active",
                f"  Identity stability: {status.get('identity_stability', 'active')}",
                f"  Identity checks: {status.get('identity_checks', 0)}",
                f"  Long-term strategy: {status.get('long_term_strategy', 'active')}",
                f"  Strategy records: {status.get('strategy_records', 0)}",
                f"  Smart organizer: {status.get('smart_organizer', 'active')}",
                f"  Organizer items: {status.get('organizer_items', 0)}",
                f"  Safe local actions: {status.get('safe_local_actions', 'active')}",
                f"  Safe action proposals: {status.get('safe_action_proposals', 0)}",
                f"  External app bridge: {status.get('external_app_bridge', 'active')}",
                f"  Bridge proposals: {status.get('bridge_proposals', 0)}",
                f"  Proactive awareness: {status.get('proactive_awareness', 'active')}",
                f"  Awareness scans: {status.get('awareness_scans', 0)}",
                "  Deep recall: active",
                f"  Recall sessions: {status.get('recall_sessions', 0)}",
                f"  Judgment: {status.get('judgment', 'active')}",
                f"  Judgment records: {status.get('judgment_records', 0)}",
                f"  Adaptive communication: {status.get('adaptive_communication', 'active')}",
                f"  Style profiles: {status.get('style_profiles', 0)}",
                f"  Human-state awareness: {status.get('human_state_awareness', 'active')}",
                f"  State signals: {status.get('state_signals', 0)}",
                f"  Time awareness: {status.get('time_awareness', 'active')}",
                f"  Time context records: {status.get('time_context_records', 0)}",
                f"  Autonomy boundaries: {status.get('autonomy_boundaries', 'active')}",
                f"  Boundary records: {status.get('boundary_records', 0)}",
                f"  Provider identity boundary: {status.get('provider_identity_boundary', 'active')}",
                f"  Provider identity records: {status.get('provider_identity_records', 0)}",
                f"  Secrets/provider-key safety: {status.get('secrets_provider_key_safety', 'active')}",
                f"  Secret safety records: {status.get('secret_safety_records', 0)}",
                f"  APIKEYS file exists: {str(status.get('key_file_exists', False)).lower()}",
                f"  Provider registry: {status.get('provider_registry', 'active')}",
                f"  Registered providers: {status.get('provider_registry_count', 0)}",
                f"  Enabled providers: {status.get('enabled_provider_count', 0)}",
                f"  Disabled providers: {status.get('disabled_provider_count', 0)}",
                f"  Evaluation results: {status.get('evaluation_results', 0)}",
                f"  Shadow tests: {status.get('shadow_test_results', 0)}",
                f"  Patch plans: {status.get('patch_plans', 0)}",
                f"  Next safe action: {status.get('next_safe_action')}",
                f"  Stage 35 gate: {status.get('stage35_gate')}",
            ]
        )

    def _format_stage17_next_action(self, result: dict) -> str:
        return self._format_stage18_next_action(result)

    def _format_stage18_next_action(self, result: dict) -> str:
        return "\n".join(
            [
                "Next safe action:",
                f"  Current active stage: {result.get('active_stage', '18 experience storage')}",
                f"  Do next: {result.get('next_safe_action')}",
                f"  Stage 35: {result.get('stage35_gate')}",
            ]
        )

    def _format_self_reflection(self, entry: dict) -> str:
        return "\n".join(
            [
                "Self-reflection saved:",
                f"  Summary: {entry.get('session_summary', '')}",
                f"  Next time start here: {entry.get('next_time_start_here') or 'not set'}",
                f"  Drift detected: {entry.get('drift_detected')}",
                f"  File: {entry.get('file', '')}",
            ]
        )

    def _format_session_review(self, review: dict) -> str:
        lines = [
            "Session review:",
            f"  Active project: {review.get('active_project') or 'Lucy'}",
            f"  Current checkpoint: {review.get('current_checkpoint') or 'not recorded'}",
            f"  Summary: {review.get('session_summary') or 'not available'}",
            f"  Next time start here: {review.get('next_time_start_here') or 'review project summary'}",
            f"  Drift detected: {review.get('drift_detected', False)}",
            f"  Memory candidates: {len(review.get('memory_candidates', []))}",
            f"  Memory rejected: {len(review.get('memory_rejected', []))}",
            f"  Confidence: {review.get('confidence')}",
        ]
        unresolved = review.get("unresolved_items", [])
        if unresolved:
            lines.append("  Unresolved:")
            for item in unresolved[:5]:
                lines.append(f"    - {item}")
        findings = review.get("drift_findings", [])
        if findings:
            lines.append("  Drift findings:")
            for item in findings[:5]:
                lines.append(f"    - {item.get('trigger')} [{item.get('severity')}]: {item.get('recommended_correction')}")
        return "\n".join(lines)

    def _format_wake_status(self, status: dict) -> str:
        return "\n".join(
            [
                "Wake status:",
                f"  Label: {status.get('wake_label')}",
                f"  Active project: {status.get('active_project')}",
                f"  Checkpoint: {status.get('current_checkpoint') or 'not recorded'}",
                f"  Next action: {status.get('next_action') or 'review project summary'}",
                f"  Drift risk: {status.get('drift_risk')}",
                f"  Presence coherence: {status.get('presence_coherence_score')}",
                f"  Guardian active: {status.get('guardian_active')}",
                f"  Memory active: {status.get('memory_active')}",
                f"  Reasoning active: {status.get('reasoning_active')}",
            ]
        )

    def _format_continuity_pulse(self, pulse) -> str:
        if isinstance(pulse, str):
            return pulse
        guardian = pulse.get("guardian", {})
        limitations = ", ".join(pulse.get("limitations", []))
        lines = [
            "Continuity pulse:",
            f"  Mode: {pulse.get('mode')}",
            f"  State: {pulse.get('posture')}",
            f"  Active project: {pulse.get('active_project')}",
            f"  Last checkpoint: {pulse.get('last_checkpoint')}",
            f"  Last unresolved issue: {pulse.get('last_unresolved_issue') or 'none'}",
            f"  Last safe learning: {pulse.get('last_safe_learning_event')}",
            f"  Next safe action: {pulse.get('next_recommended_action') or 'review project summary'}",
            f"  Guardian: active={guardian.get('active')} protected_actions_blocked={guardian.get('protected_actions_blocked')}",
            f"  Drift detected: {pulse.get('drift_detected')}",
            f"  Memory candidates pending: {pulse.get('memory_candidates_pending', 0)}",
            f"  Limits: {limitations}",
        ]
        if pulse.get("last_user_correction"):
            lines.insert(6, f"  Last correction hint: {pulse.get('last_user_correction')}")
        findings = pulse.get("drift_findings", [])
        if findings:
            lines.append("  Drift correction:")
            for item in findings[:3]:
                lines.append(f"    - {item.get('trigger')}: {item.get('recommended_correction')}")
        return "\n".join(lines)

    def _format_wake_report(self, report: dict) -> str:
        return "Wake report:\n" + json.dumps(report, indent=2, ensure_ascii=False)

    def _format_wake_limitations(self, limitations: list[str]) -> str:
        if not limitations:
            return "Wake limitations: none recorded."
        lines = ["Wake limitations:"]
        lines.extend(f"  - {item}" for item in limitations)
        return "\n".join(lines)

    def _format_wake_drift_check(self, result: dict) -> str:
        return "\n".join(
            [
                "Wake drift check:",
                f"  Risk: {result.get('drift_risk')}",
                f"  Trigger: {result.get('trigger') or 'none'}",
                f"  Reason: {result.get('reason')}",
                f"  Correction: {result.get('correction')}",
            ]
        )

    def _format_presence_report(self, report: dict) -> str:
        return "\n".join(
            [
                "Presence:",
                f"  Mode: {report.get('mode')}",
                f"  Active project: {report.get('active_project')}",
                f"  Wake label: {report.get('wake_label')}",
                f"  Drift risk: {report.get('drift_risk')}",
                f"  Presence coherence: {report.get('presence_coherence_score')}",
                f"  Next action: {report.get('next_action') or 'review project summary'}",
            ]
        )

    def _format_memory_candidates(self, result: dict) -> str:
        counts = result.get("counts", {})
        pending = result.get("pending", [])
        lines = [
            "Memory candidates:",
            f"  Pending: {counts.get('pending', len(pending))}",
            f"  Approved: {counts.get('approved', len(result.get('approved', [])))}",
            f"  Rejected: {counts.get('rejected', len(result.get('rejected', [])))}",
            f"  File: {result.get('file', '')}",
        ]
        if not pending:
            lines.append("  No pending candidates.")
            return "\n".join(lines)
        for item in pending[:10]:
            lines.append(
                f"  - {item.get('id')} [{item.get('category')}] "
                f"importance={item.get('importance')} confirm={item.get('requires_user_confirmation')}"
            )
            lines.append(f"    {item.get('content')}")
        return "\n".join(lines)

    def _format_memory_candidate_action(self, result: dict) -> str:
        if not result.get("ok"):
            return f"Memory candidate update failed: {result.get('reason') or 'unknown'}"
        candidate = result.get("candidate", {})
        status = "approved" if candidate.get("approved_at") else "rejected" if candidate.get("rejected") else "updated"
        return "\n".join(
            [
                f"Memory candidate {status}:",
                f"  ID: {candidate.get('id')}",
                f"  Category: {candidate.get('category')}",
                f"  Safe to store: {candidate.get('safe_to_store')}",
            ]
        )

    def _format_drift_report(self, result: dict) -> str:
        findings = result.get("findings", [])
        if not findings:
            return "Drift report: no known drift trigger found in the current session state."
        lines = ["Drift report:"]
        for item in findings:
            lines.extend(
                [
                    f"  - Trigger: {item.get('trigger')}",
                    f"    Severity: {item.get('severity')}",
                    f"    Reason: {item.get('reason')}",
                    f"    Correction: {item.get('recommended_correction')}",
                ]
            )
        return "\n".join(lines)

    def _format_write_reflection(self, entry: dict) -> str:
        return "\n".join(
            [
                "Stage 6.5 reflection written:",
                f"  Summary: {entry.get('summary') or 'not available'}",
                f"  Memory candidates: {entry.get('memory_candidates_count', 0)}",
                f"  Memory rejected: {entry.get('memory_rejected_count', 0)}",
                f"  Drift detected: {entry.get('drift_detected', False)}",
                f"  Next checkpoint: {entry.get('next_recommended_checkpoint') or 'review project summary'}",
                f"  File: {entry.get('file', '')}",
            ]
        )

    def _format_where_did_we_stop(self, result: dict) -> str:
        lines = [
            "Where we stopped:",
            f"  Active project: {result.get('active_project')}",
            f"  Crash recovery needed: {result.get('crash_recovery_needed')}",
            f"  Last command: {result.get('last_command') or 'none'}",
            f"  Last response: {result.get('last_response_summary') or 'none'}",
            f"  Next action: {result.get('next_action') or 'not set'}",
        ]
        open_tasks = result.get("open_tasks", [])
        if open_tasks:
            lines.append("  Open tasks:")
            for task in open_tasks[:5]:
                lines.append(f"    - {task.get('text', '')}")
        return "\n".join(lines)

    def _format_next_step(self, result: dict) -> str:
        recommended = result.get("recommended")
        lines = [
            "Next step:",
            f"  Active project: {result.get('active_project')}",
            f"  Project next action: {result.get('project_next_action') or 'not set'}",
        ]
        if recommended:
            lines.extend(
                [
                    f"  Recommended task: {recommended.get('title')}",
                    f"  Score: {recommended.get('score')}",
                    f"  Reason: {recommended.get('priority_reason')}",
                ]
            )
        else:
            lines.append("  Recommended task: none; review project summary.")
        return "\n".join(lines)

    def _format_task_summary(self, result: dict) -> str:
        recommended = result.get("recommended")
        if not recommended:
            return "Task summary: no open task recommendation found."
        return "\n".join(
            [
                "Task summary:",
                f"  Recommended: {recommended.get('title')}",
                f"  Project: {recommended.get('project')}",
                f"  Complexity: {recommended.get('complexity')}",
                f"  Reason: {recommended.get('priority_reason')}",
            ]
        )

    def _format_tomorrow_plan(self, result: dict) -> str:
        recommended = result.get("recommended")
        daily = result.get("daily_context", {})
        lines = [
            "Tomorrow plan:",
            f"  Active project: {result.get('active_project')}",
            f"  Existing tomorrow priority: {daily.get('tomorrow_priority') or 'not set'}",
            f"  Start here: {result.get('project_next_action') or 'review project summary'}",
        ]
        if recommended:
            lines.append(f"  Suggested first task: {recommended.get('title')}")
        return "\n".join(lines)

    def _format_classify_action(self, result: dict) -> str:
        scores = result.get("fuzzy_scores", {})
        return "\n".join(
            [
                "Guardian classification:",
                f"  Result: {result.get('classification')}",
                f"  Reason: {result.get('reason')}",
                f"  Matched pattern: {result.get('matched_pattern') or 'none'}",
                f"  Completeness: {scores.get('completeness')}",
                f"  Relevance: {scores.get('relevance')}",
                f"  Confidence: {scores.get('confidence')}",
            ]
        )

    def _format_dashboard(self) -> str:
        status = self.runtime.status()
        project = self.runtime.project_summary()
        memory = self.runtime.memory_audit()
        reminders = self.runtime.list_reminders()
        approvals = self.runtime.list_approvals()
        return "\n".join(
            [
                "Lucy operator dashboard:",
                f"  Stage: {status['stage']}",
                f"  Mode: {status['mode']}",
                f"  Active project: {project['name']}",
                f"  Next action: {project['next_action'] or 'Not set.'}",
                f"  Open tasks: {len(project['open_tasks'])}",
                f"  Active memories: {memory['active']}",
                f"  Open reminders: {len(reminders)}",
                f"  Pending approvals: {len(approvals)}",
                f"  Safety: protected actions {'blocked' if status['protected_actions_blocked'] else 'not blocked'}",
            ]
        )

    def _format_status(self, status: dict) -> str:
        agents_note = "registered but inactive" if not status["agents_active"] else "WARNING: agents active"
        return "\n".join(
            [
                "LUCY Core Runtime is online.",
                f"Full form: {status['full_form']}.",
                f"Stage: {status['stage']}.",
                f"Mode: {status['mode']}.",
                f"Agents: {agents_note}.",
                f"APIs: {'enabled' if status['api_enabled'] else 'disabled'}.",
                f"Voice: {'enabled' if status['voice_enabled'] else 'disabled'}.",
                f"Web UI: {'active' if status['web_ui_enabled'] else 'paused'}.",
                f"Desktop UI: {'available' if status.get('desktop_ui_enabled') else 'not configured'}.",
                f"Cognition: {status.get('cognition_mode', 'not configured')}.",
                f"Root access: {'enabled' if status['root_access_enabled'] else 'disabled'}.",
                f"Autonomy: {'enabled' if status['autonomy_enabled'] else 'disabled'}.",
                f"Memory: {self.runtime.memory.status()}",
                f"Protected actions: {'blocked' if status['protected_actions_blocked'] else 'WARNING: not blocked'}.",
            ]
        )

    def _format_guardian(self) -> str:
        status = self.runtime.guardian_status()
        return "\n".join(
            [
                "Guardian Core:",
                f"  Mode: {status.get('mode')}",
                f"  Protected actions blocked: {status['protected_actions_blocked']}",
                f"  Root access enabled: {status['root_access_enabled']}",
                f"  Autonomy enabled: {status['autonomy_enabled']}",
                f"  Agent execution enabled: {status['agent_execution_enabled']}",
                f"  Pending approvals: {status['pending_approvals']}",
                f"  Log file: {status.get('log_file')}",
                "  File deletion, secrets, money movement, root commands, and identity changes are blocked.",
                "  Guardian classifies only; it does not execute actions.",
            ]
        )

    def _format_approvals(self, approvals: list[dict]) -> str:
        if not approvals:
            return "No approval records found."
        lines = ["Approval records:"]
        for item in approvals:
            lines.append(
                f"  - {item.get('id', '')[:8]} [{item.get('status', 'unknown')}] "
                f"{item.get('risk_level', 'unknown')}: {item.get('request_text', '')}"
            )
            lines.append(f"    Reason: {item.get('reason', 'No reason recorded.')}")
        return "\n".join(lines)

    def _format_approval_review(self, result: dict) -> str:
        if not result.get("changed"):
            return f"Approval unchanged: {result.get('reason', 'unknown reason')}"
        approval = result["approval"]
        return (
            f"Approval {approval['id'][:8]} marked {approval['status']}. "
            "This records your review only; it does not execute the action."
        )

    def _format_health(self, report) -> str:
        lines = [f"Lucy Health Check: {report.passed_count} passed / {report.failed_count} failed"]
        for check in report.checks:
            icon = "ok" if check.passed else "fail"
            lines.append(f"  [{icon}] {check.name}: {check.detail}")
        if report.all_passed:
            lines.append("All health checks passed.")
        else:
            lines.append("Some checks failed. Review the failed items above.")
        return "\n".join(lines)

    def _format_spine(self) -> str:
        from backend.lucy_core.spine_loader import get_spine_summary

        spine = self.runtime.spine
        lines = ["Lucy Spine Data:", f"  {get_spine_summary(spine)}"]
        lucy = spine.get("lucy", {})
        if lucy:
            lines.extend(
                [
                    f"  Status: {lucy.get('status', 'unknown')}",
                    f"  Phase: {lucy.get('phase', 'unknown')}",
                    f"  APIs: {lucy.get('apis_connected', 'unknown')}",
                    f"  Live trading: {lucy.get('live_trading_enabled', 'unknown')}",
                    f"  Root access: {lucy.get('root_access_enabled', 'unknown')}",
                ]
            )
        if spine.get("_fallback"):
            lines.append("  [warning] Using fallback spine; original spine.json may not have been found.")
        return "\n".join(lines)

    def _format_agents(self) -> str:
        agents = self.runtime.agents.list_agents()
        lines = ["Registered planned agents:"]
        for agent in agents:
            status = agent.get("status", "unknown")
            active = "active" if agent.get("active") else "inactive"
            lines.append(f"  - {agent['id']}: {status} / {active}")
        if not self.runtime.agents.any_active():
            lines.append("No agents are active yet.")
        else:
            lines.append("WARNING: One or more agents appear active. Review agent_registry.json.")
        return "\n".join(lines)

    def _format_internal_agent_status(self, result: dict) -> str:
        lines = ["Internal agents: active."]
        statuses = {item.get("agent_id"): item.get("status", "unknown") for item in result.get("agents", [])}
        for agent_id in ["MemoryAgent", "SafetyAgent", "ReasoningAgent", "LearningAgent"]:
            lines.append(f"{agent_id}: {statuses.get(agent_id, 'missing')}.")
        lines.append(f"Guardian: {result.get('guardian', 'active')}.")
        lines.append(f"Stage: {result.get('active_stage', '08')} {result.get('stage_label', 'internal agents')}.")
        return "\n".join(lines)

    def _format_runtime_status(self, status: dict) -> str:
        marker = "active" if not status.get("clean_shutdown") else "clean"
        return "\n".join(
            [
                "Runtime status:",
                f"Stage: {status.get('stage', '10 persistent local runtime')}",
                f"Active project: {status.get('active_project', 'Lucy')}",
                f"Guardian: {status.get('guardian_status', 'active')}",
                f"Started at: {status.get('started_at')}",
                f"Last heartbeat: {status.get('last_heartbeat')}",
                f"Last command: {status.get('last_command') or 'none'}",
                f"Previous shutdown clean: {status.get('previous_shutdown_clean')}",
                f"Recovery mode: {status.get('recovery_mode')}",
                f"Clean shutdown flag: {status.get('clean_shutdown')}",
                f"Clean shutdown marker: {marker}",
                f"Runtime ID: {status.get('runtime_id')}",
                f"File: {status.get('file')}",
            ]
        )

    def _format_safe_access_status(self, status: dict) -> str:
        approval = "yes" if status.get("future_access_changes_require_approval", True) else "no"
        return "\n".join(
            [
                "Safe access status:",
                f"Stage: {status.get('stage', '11 safe access')}",
                f"Access state: {status.get('access_state', 'disabled')}",
                f"Local-only policy: {status.get('local_only_policy', 'prepared')}",
                f"External access: {status.get('external_access', 'blocked')}",
                f"Network server: {status.get('network_server', 'not enabled')}",
                f"Phone/browser access: {status.get('phone_browser_access', 'not enabled')}",
                f"Token generation: {status.get('token_generation', 'blocked')}",
                f"Approval required for future access changes: {approval}",
                f"Source policy: {status.get('source_policy', 'caller_supplied_label_only')}",
                f"Policy file: {status.get('file', '')}",
            ]
        )

    def _format_first_thought_status(self, result: dict) -> str:
        assembled = "true" if result.get("generated") else "false"
        lines = [
            "First thought status:",
            f"Stage: {result.get('stage', '12 first thought from real state')}",
            f"Assembled: {assembled}",
            f"Guardian: {result.get('guardian_status', 'unknown')}",
            f"Runtime: {result.get('runtime_recovery_status', 'unknown')}",
            f"Agents: {result.get('agents_status', 'unknown')}",
            f"Safe access: {result.get('safe_access_status', 'unknown')}",
        ]
        if result.get("blocked_reason"):
            lines.append(f"Blocked reason: {result.get('blocked_reason')}")
        return "\n".join(lines)

    def _format_first_thought_readiness(self, result: dict) -> str:
        ready = "true" if result.get("ready") else "false"
        recovery_mode = str(result.get("recovery_mode")).lower()
        lines = [
            f"Stage: {result.get('stage', '12 first thought from real state')}",
            f"Guardian: {result.get('guardian_status', 'unknown')}",
            f"Runtime: {result.get('runtime_recovery_status', 'unknown')}",
            f"Recovery mode: {recovery_mode}",
            f"Agents: {result.get('agents_status', 'unknown')}",
            f"Safe access: {result.get('safe_access_status', 'unknown')}",
            f"Ready: {ready}",
        ]
        if result.get("blocked_reason"):
            lines.append(f"Blocked reason: {result.get('blocked_reason')}")
        return "\n".join(lines)

    def _format_first_thought_assembly(self, result: dict) -> str:
        if result.get("already_assembled"):
            return "\n".join(
                [
                    "First thought assembly rejected: already assembled. Existing status returned.",
                    f"Assembled at: {result.get('generated_at', '')}",
                    "Source: verified local state only.",
                ]
            )
        if not result.get("generated"):
            return f"First thought assembly blocked: {result.get('blocked_reason') or 'not ready'}"
        return self._format_show_first_thought(result, prefix="First thought assembled.")

    def _format_show_first_thought(self, result: dict, prefix: str | None = None) -> str:
        if not result.get("generated"):
            return "\n".join(
                [
                    "First thought is not assembled.",
                    f"Blocked reason: {result.get('blocked_reason') or 'not assembled'}",
                ]
            )
        lines = []
        if prefix:
            lines.append(prefix)
        lines.extend(
            [
                result.get("first_thought_text", ""),
                f"Assembled at: {result.get('generated_at', '')}",
                "Source: verified local state only.",
            ]
        )
        return "\n".join(lines)

    def _format_self_model_status(self, result: dict) -> str:
        safe_access = result.get("safe_access_status", {})
        runtime = result.get("runtime_status", {})
        agents = result.get("agent_status", {})
        first_thought = result.get("first_thought_status", {})
        return "\n".join(
            [
                "Self-model status:",
                f"Stage: {result.get('stage', '13 self-model')}",
                f"Role: {result.get('system_role', '')}",
                f"Verified foundations: {', '.join(result.get('verified_foundations', []))}",
                f"Capabilities: {', '.join(result.get('current_capabilities', []))}",
                f"Limits: {', '.join(result.get('current_limits', []))}",
                f"Blocked claims: {', '.join(result.get('blocked_claims', []))}",
                f"Blocked actions: {', '.join(result.get('blocked_actions', []))}",
                f"Guardian: {result.get('guardian_status', 'unknown')}",
                (
                    "Safe access: "
                    f"{safe_access.get('access_state', 'unknown')} / external {safe_access.get('external_access', 'unknown')}"
                ),
                (
                    "Runtime: "
                    f"{runtime.get('stage', 'unknown')} / recovery_mode={runtime.get('recovery_mode')}"
                ),
                (
                    "Agents: "
                    f"{'active' if agents.get('active') else 'inactive'} / {', '.join(agents.get('agents', []))}"
                ),
                (
                    "First thought: "
                    f"{'assembled' if first_thought.get('generated') else 'not assembled'}"
                ),
            ]
        )

    def _format_growth_proposals_status(self, result: dict) -> str:
        approval = "yes" if result.get("approval_required", True) else "no"
        return "\n".join(
            [
                "Growth proposals status:",
                f"Stage: {result.get('stage', '14 growth proposals')}",
                f"Proposal system: {result.get('proposal_system', 'active')}",
                f"Existing proposals: {result.get('existing_proposals', 0)}",
                f"Approval required: {approval}",
                f"Automatic patching: {result.get('automatic_patching', 'disabled')}",
                f"Evaluation lab: {result.get('evaluation_lab', 'not implemented')}",
                f"Shadow testing: {result.get('shadow_testing', 'not implemented')}",
                f"Patch pipeline: {result.get('patch_pipeline', 'not implemented')}",
                f"Experience storage: {result.get('experience_storage', 'not implemented')}",
            ]
        )

    def _format_growth_proposals_list(self, proposals: list[dict]) -> str:
        if not proposals:
            return "Growth proposals: none. Use: propose growth"
        lines = ["Growth proposals:"]
        for index, proposal in enumerate(proposals, start=1):
            lines.append(
                f"  {index}. {proposal.get('proposal_id', '')} | "
                f"{proposal.get('status', 'proposed')} | {proposal.get('risk_level', 'low')} | "
                f"{proposal.get('title', '')}"
            )
        return "\n".join(lines)

    def _format_growth_proposal(self, proposal: dict) -> str:
        return "\n".join(
            [
                "Proposal:",
                proposal.get("title", ""),
                "Reason:",
                proposal.get("reason", ""),
                "Evidence:",
                proposal.get("evidence_summary", ""),
                f"Risk: {proposal.get('risk_level', 'low')}.",
                f"Possible files later: {', '.join(proposal.get('possible_files', []))}",
                f"Approval required: {'yes' if proposal.get('approval_required', True) else 'no'}.",
                f"Status: {proposal.get('status', 'proposed')}.",
                "Not implemented: " + ", ".join(proposal.get("not_implemented", [])),
            ]
        )

    def _format_growth_proposal_review(self, result: dict) -> str:
        if not result.get("ok"):
            return f"Growth proposal review failed: {result.get('reason', 'unknown')}"
        proposal = result.get("proposal", {})
        return (
            f"Growth proposal status updated: {proposal.get('proposal_id', '')} "
            f"-> {proposal.get('status', 'needs_review')}. No code was changed."
        )

    def _format_evaluation_lab_status(self, result: dict) -> str:
        approval = "yes" if result.get("approval_required_before_implementation", True) else "no"
        return "\n".join(
            [
                "Evaluation lab status:",
                f"Stage: {result.get('stage', '15 evaluation lab')}",
                f"Evaluation lab: {result.get('evaluation_lab', 'active')}",
                f"Evaluation cases/results: {result.get('evaluation_results', 0)}",
                f"Automatic patching: {result.get('automatic_patching', 'disabled')}",
                f"Shadow testing: {result.get('shadow_testing', 'not implemented')}",
                f"Patch pipeline: {result.get('patch_pipeline', 'not implemented')}",
                f"Experience storage: {result.get('experience_storage', 'not implemented')}",
                f"Approval required before implementation: {approval}",
            ]
        )

    def _format_evaluate_growth_proposals(self, result: dict) -> str:
        if not result.get("ok"):
            return f"Evaluation unavailable: {result.get('reason', 'unknown')}"
        evaluations = result.get("evaluations", [])
        if not evaluations:
            return "Evaluation unavailable: no growth proposals found"
        lines = ["Evaluations:"]
        if result.get("reused_count"):
            lines.append(f"  Existing evaluations reused: {result.get('reused_count')}")
        for evaluation in evaluations:
            lines.extend(self._evaluation_summary_lines(evaluation, indent="  "))
        return "\n".join(lines)

    def _format_evaluate_proposal(self, result: dict) -> str:
        if not result.get("ok"):
            return f"Evaluation unavailable: {result.get('reason', 'unknown')}"
        lines = ["Evaluation:"]
        if result.get("reused"):
            lines.append("Existing evaluation reused.")
        lines.extend(self._evaluation_summary_lines(result.get("evaluation", {})))
        return "\n".join(lines)

    def _format_evaluations_list(self, evaluations: list[dict]) -> str:
        if not evaluations:
            return "Evaluations: none. Use: evaluate growth proposals"
        lines = ["Evaluations:"]
        for index, evaluation in enumerate(evaluations, start=1):
            lines.append(
                f"  {index}. {evaluation.get('evaluation_id', '')} | "
                f"{evaluation.get('result', 'needs_review')} | score={evaluation.get('score', 0)} | "
                f"{evaluation.get('proposal_title', '')}"
            )
        return "\n".join(lines)

    def _evaluation_summary_lines(self, evaluation: dict, indent: str = "") -> list[str]:
        blocked = evaluation.get("blocked_reasons", [])
        blocked_text = ", ".join(blocked) if blocked else "none"
        not_implemented = ", ".join(evaluation.get("not_implemented", []))
        return [
            f"{indent}Proposal: {evaluation.get('proposal_title', '')}",
            f"{indent}Result: {evaluation.get('result', 'needs_review')}",
            f"{indent}Score: {evaluation.get('score', 0)}",
            f"{indent}Risk: {evaluation.get('risk_level', 'medium')}",
            f"{indent}Approval required: {'yes' if evaluation.get('approval_required', True) else 'no'}",
            f"{indent}Blocked reasons: {blocked_text}",
            f"{indent}Not implemented: {not_implemented}",
        ]

    def _format_shadow_testing_status(self, result: dict) -> str:
        approval = "yes" if result.get("approval_required_before_implementation", True) else "no"
        return "\n".join(
            [
                "Shadow testing status:",
                f"Stage: {result.get('stage', '16 shadow testing')}",
                f"Shadow testing: {result.get('shadow_testing', 'active')}",
                f"Shadow test results: {result.get('shadow_test_results', 0)}",
                f"Real patching: {result.get('real_patching', 'disabled')}",
                f"Approved patch pipeline: {result.get('approved_patch_pipeline', 'not implemented')}",
                f"Experience storage: {result.get('experience_storage', 'not implemented')}",
                f"Approval required before implementation: {approval}",
            ]
        )

    def _format_shadow_test_result(self, result: dict) -> str:
        if not result.get("ok"):
            return f"Shadow test unavailable: {result.get('reason', 'unknown')}"
        shadow_test = result.get("shadow_test", {})
        lines = ["Shadow test:"]
        if result.get("reused"):
            lines.append("Existing shadow test reused.")
        lines.extend(self._shadow_test_summary_lines(shadow_test))
        return "\n".join(lines)

    def _format_shadow_tests_list(self, shadow_tests: list[dict]) -> str:
        if not shadow_tests:
            return "Shadow tests: none. Use: run shadow test"
        lines = ["Shadow tests:"]
        for index, shadow_test in enumerate(shadow_tests, start=1):
            lines.append(
                f"  {index}. {shadow_test.get('shadow_test_id', '')} | "
                f"{shadow_test.get('result', 'needs_review')} | score={shadow_test.get('score', 0)} | "
                f"{shadow_test.get('proposal_title', '')}"
            )
        return "\n".join(lines)

    def _format_patch_pipeline_status(self, result: dict) -> str:
        approval = "yes" if result.get("approval_required_before_implementation", True) else "no"
        lines = [
            "Patch pipeline status:",
            f"Stage: {result.get('stage', '17 approved patch pipeline')}",
            f"Approved patch pipeline: {result.get('approved_patch_pipeline', 'active')}",
            f"Patch plans: {result.get('patch_plans', 0)}",
            f"Real patching: {result.get('real_patching', 'disabled')}",
            f"Implementation allowed: {str(result.get('implementation_allowed', False)).lower()}",
            f"Experience storage: {result.get('experience_storage', 'not implemented')}",
            f"Approval required before implementation: {approval}",
        ]
        latest = result.get("latest_plan")
        if latest:
            lines.append(f"Latest plan: {latest.get('patch_plan_id', '')} | {latest.get('status', 'needs_review')}")
        return "\n".join(lines)

    def _format_patch_plan_result(self, result: dict) -> str:
        if not result.get("ok"):
            return f"Patch plan unavailable: {result.get('reason', 'unknown')}"
        patch_plan = result.get("patch_plan", {})
        lines = ["Patch plan:"]
        if result.get("reused"):
            lines.append("Existing patch plan reused.")
        lines.extend(self._patch_plan_summary_lines(patch_plan))
        return "\n".join(lines)

    def _format_patch_plans_list(self, patch_plans: list[dict]) -> str:
        if not patch_plans:
            return "Patch plans: none. Use: create patch plan"
        lines = ["Patch plans:"]
        for index, patch_plan in enumerate(patch_plans, start=1):
            lines.append(
                f"  {index}. {patch_plan.get('patch_plan_id', '')} | "
                f"{patch_plan.get('status', 'needs_review')} | "
                f"{patch_plan.get('proposal_title', '')}"
            )
        return "\n".join(lines)

    def _patch_plan_summary_lines(self, patch_plan: dict) -> list[str]:
        blocked = patch_plan.get("blocked_reasons", [])
        blocked_text = ", ".join(blocked) if blocked else "none"
        suggested_files = patch_plan.get("suggested_files", [])
        files_text = ", ".join(suggested_files) if suggested_files else "none"
        not_implemented = ", ".join(patch_plan.get("not_implemented", []))
        return [
            f"Proposal: {patch_plan.get('proposal_title', '')}",
            f"Status: {patch_plan.get('status', 'needs_review')}",
            f"Approval required: {'yes' if patch_plan.get('approval_required', True) else 'no'}",
            f"Real patching enabled: {str(patch_plan.get('real_patching_enabled', False)).lower()}",
            f"Implementation allowed: {str(patch_plan.get('implementation_allowed', False)).lower()}",
            f"Suggested files: {files_text}",
            f"Blocked reasons: {blocked_text}",
            f"Not implemented: {not_implemented}",
        ]

    def _format_experience_storage_status(self, result: dict) -> str:
        approval = "yes" if result.get("approval_required_for_sensitive_storage", True) else "no"
        return "\n".join(
            [
                "Experience storage status:",
                f"Stage: {result.get('stage', '18 experience storage')}",
                f"Experience storage: {result.get('experience_storage', 'active')}",
                f"Experience records: {result.get('experience_records', 0)}",
                f"Stores raw chat logs: {result.get('stores_raw_chat_logs', 'no')}",
                f"Stores secrets: {result.get('stores_secrets', 'no')}",
                "  Deep recall: active",
                f"Identity stability: {result.get('identity_stability', 'not implemented')}",
                f"Long-term strategy: {result.get('long_term_strategy', 'not implemented')}",
                f"Approval required for sensitive storage: {approval}",
            ]
        )

    def _format_experience_record_result(self, result: dict) -> str:
        if not result.get("ok"):
            blocked = result.get("blocked_content", [])
            blocked_text = ", ".join(blocked) if blocked else result.get("reason", "unknown")
            return f"Experience record blocked: {blocked_text}"
        record = result.get("experience_record", {})
        lines = ["Experience record:"]
        if result.get("reused"):
            lines.append("Existing experience record reused.")
        lines.extend(self._experience_record_summary_lines(record))
        return "\n".join(lines)

    def _format_experience_records_list(self, records: list[dict]) -> str:
        if not records:
            return "Experience records: none. Use: record experience"
        lines = ["Experience records:"]
        for index, record in enumerate(records, start=1):
            lines.append(
                f"  {index}. {record.get('experience_id', '')} | "
                f"{record.get('event_type', 'manual_check')} | "
                f"{record.get('title', '')}"
            )
        return "\n".join(lines)

    def _experience_record_summary_lines(self, record: dict) -> list[str]:
        not_implemented = ", ".join(record.get("not_implemented", []))
        blocked = record.get("blocked_content", [])
        blocked_text = ", ".join(blocked) if blocked else "none"
        return [
            f"Title: {record.get('title', '')}",
            f"Lesson: {record.get('lesson', '')}",
            f"Risk noted: {record.get('risk_noted', '')}",
            f"Future rule: {record.get('future_rule', '')}",
            f"Sensitivity: {record.get('sensitivity', 'safe_project')}",
            f"Approved for storage: {str(record.get('approved_for_storage', False)).lower()}",
            f"Blocked content: {blocked_text}",
            f"Not implemented: {not_implemented}",
        ]

    def _shadow_test_summary_lines(self, shadow_test: dict, indent: str = "") -> list[str]:
        blocked = shadow_test.get("blocked_reasons", [])
        blocked_text = ", ".join(blocked) if blocked else "none"
        not_implemented = ", ".join(shadow_test.get("not_implemented", []))
        return [
            f"{indent}Proposal: {shadow_test.get('proposal_title', '')}",
            f"{indent}Result: {shadow_test.get('result', 'needs_review')}",
            f"{indent}Score: {shadow_test.get('score', 0)}",
            f"{indent}Risk: {shadow_test.get('risk_level', 'medium')}",
            f"{indent}Approval required: {'yes' if shadow_test.get('approval_required', True) else 'no'}",
            f"{indent}Blocked reasons: {blocked_text}",
            f"{indent}Not implemented: {not_implemented}",
        ]

    def _format_provider_registry_status(self, result: dict) -> str:
        provider_names = ", ".join(result.get("provider_names", [])) or "none"
        enabled = ", ".join(result.get("enabled_providers", [])) or "none"
        disabled = ", ".join(result.get("disabled_providers", [])) or "none"
        approval = "yes" if result.get("requires_user_approval", True) else "no"
        return "\n".join(
            [
                "Provider registry status:",
                f"Stage: {result.get('stage', '33 provider registry')}",
                f"Provider registry: {result.get('provider_registry', 'active')}",
                f"Registry file: {result.get('registry_file', '')}",
                f"Execution mode: {result.get('execution_mode', 'local_provider_metadata_only')}",
                f"Provider count: {result.get('provider_count', 0)}",
                f"Enabled provider count: {result.get('enabled_provider_count', 0)}",
                f"Disabled provider count: {result.get('disabled_provider_count', 0)}",
                f"Provider names: {provider_names}",
                f"Enabled providers: {enabled}",
                f"Disabled providers: {disabled}",
                f"Provider names allowed: {str(result.get('provider_names_allowed', True)).lower()}",
                f"Provider roles allowed: {str(result.get('provider_roles_allowed', True)).lower()}",
                f"Provider enabled state allowed: {str(result.get('provider_enabled_state_allowed', True)).lower()}",
                f"Credential labels only: {str(result.get('credential_labels_only', True)).lower()}",
                f"API key values: {result.get('api_key_values', 'blocked')}",
                f"API key file reading: {result.get('api_key_file_reading', 'blocked')}",
                f"Secret value loading: {result.get('secret_value_loading', 'blocked')}",
                f"Provider calls: {result.get('provider_calls', 'blocked')}",
                f"Network access: {result.get('network_access', 'blocked')}",
                f"Provider health checks: {result.get('provider_health_checks', 'not implemented')}",
                f"Model routing: {result.get('model_routing', 'not implemented')}",
                f"External model execution: {result.get('external_model_execution', 'not implemented')}",
                f"Requires user approval: {approval}",
                f"Real actions: {str(result.get('real_actions', False)).lower()}",
                f"Autonomy: {result.get('autonomy', 'not implemented')}",
            ]
        )

    def _format_provider_registry_list(self, providers: list[dict]) -> str:
        if not providers:
            return "Registered providers: none."
        lines = ["Registered providers:"]
        for provider in providers:
            enabled = "enabled" if provider.get("enabled") else "disabled"
            aliases = ", ".join(provider.get("aliases", [])) or "none"
            lines.append(
                f"  - {provider.get('provider_id', '')} | "
                f"{provider.get('display_name', '')} | "
                f"{provider.get('role', '')} | "
                f"{enabled} | aliases: {aliases}"
            )
        lines.extend(
            [
                "API key values returned: false",
                "Provider calls: false",
                "Network access: false",
                "Health checks: false",
            ]
        )
        return "\n".join(lines)

    def _format_provider_registry_provider_result(self, result: dict) -> str:
        if not result.get("ok"):
            return "\n".join(
                [
                    "Registered provider:",
                    f"Stage: {result.get('stage', '33 provider registry')}",
                    f"Status: not found",
                    f"Requested provider: {result.get('requested_provider', '')}",
                    f"Provider call allowed: {str(result.get('provider_call_allowed', False)).lower()}",
                    f"Network allowed: {str(result.get('network_allowed', False)).lower()}",
                    f"API key values returned: {str(result.get('api_key_values_returned', False)).lower()}",
                ]
            )
        lines = ["Registered provider:"]
        lines.extend(self._provider_registry_provider_lines(result.get("provider", {})))
        lines.extend(
            [
                f"Provider call allowed: {str(result.get('provider_call_allowed', False)).lower()}",
                f"Network allowed: {str(result.get('network_allowed', False)).lower()}",
                f"API key values returned: {str(result.get('api_key_values_returned', False)).lower()}",
            ]
        )
        return "\n".join(lines)

    def _format_provider_registry_change(self, result: dict) -> str:
        if not result.get("ok"):
            return self._format_provider_registry_provider_result(result)
        lines = ["Provider registry update:"]
        lines.extend(self._provider_registry_provider_lines(result.get("provider", {})))
        lines.extend(
            [
                f"Changed: {str(result.get('changed', False)).lower()}",
                f"Provider call allowed: {str(result.get('provider_call_allowed', False)).lower()}",
                f"Network allowed: {str(result.get('network_allowed', False)).lower()}",
                f"API key values returned: {str(result.get('api_key_values_returned', False)).lower()}",
                f"Real action allowed: {str(result.get('real_action_allowed', False)).lower()}",
            ]
        )
        return "\n".join(lines)

    def _format_provider_registry_reset(self, result: dict) -> str:
        return "\n".join(
            [
                "Provider registry reset:",
                f"Stage: {result.get('stage', '33 provider registry')}",
                f"Status: {str(result.get('ok', False)).lower()}",
                f"Message: {result.get('message', '')}",
                f"Provider call allowed: {str(result.get('provider_call_allowed', False)).lower()}",
                f"Network allowed: {str(result.get('network_allowed', False)).lower()}",
                f"API key values returned: {str(result.get('api_key_values_returned', False)).lower()}",
            ]
        )

    def _format_provider_registry_dry_run(self, result: dict) -> str:
        return "\n".join(
            [
                "Provider registry dry run:",
                f"Stage: {result.get('stage', '33 provider registry')}",
                f"Context: {result.get('context', '')}",
                f"Dry run only: {str(result.get('dry_run_only', True)).lower()}",
                f"Would read API key file: {str(result.get('would_read_api_key_file', False)).lower()}",
                f"Would load secret values: {str(result.get('would_load_secret_values', False)).lower()}",
                f"Would print secret values: {str(result.get('would_print_secret_values', False)).lower()}",
                f"Would store secret values: {str(result.get('would_store_secret_values', False)).lower()}",
                f"Would call provider: {str(result.get('would_call_provider', False)).lower()}",
                f"Would use network: {str(result.get('would_use_network', False)).lower()}",
                f"Would run provider health check: {str(result.get('would_run_provider_health_check', False)).lower()}",
                f"Would route model: {str(result.get('would_route_model', False)).lower()}",
                f"Would execute external model: {str(result.get('would_execute_external_model', False)).lower()}",
                f"Would take real action: {str(result.get('would_take_real_action', False)).lower()}",
                f"Provider registry allowed: {str(result.get('provider_registry_allowed', True)).lower()}",
                f"Message: {result.get('message', '')}",
            ]
        )

    def _format_provider_health_check_status(self, result: dict) -> str:
        return "\n".join(
            [
                "Provider health-check status:",
                f"Stage: {result.get('stage', '34 provider health-check dry-run')}",
                f"Health check: {result.get('provider_health_check', 'active')}",
                f"Execution mode: {result.get('execution_mode', 'dry_run_only')}",
                f"Dry runs recorded: {result.get('dry_run_count', 0)}",
                f"Real health check performed: {str(result.get('real_health_check_performed', False)).lower()}",
                f"Provider calls: {result.get('provider_calls', 'blocked')}",
                f"Network access: {result.get('network_access', 'blocked')}",
                f"API key file reading: {result.get('api_key_file_reading', 'blocked')}",
                f"Secret value loading: {result.get('secret_value_loading', 'blocked')}",
                f"Provider reachability ping: {result.get('provider_reachability_ping', 'not implemented')}",
                f"Provider authentication test: {result.get('provider_authentication_test', 'not implemented')}",
                f"Model routing: {result.get('model_routing', 'not implemented')}",
                f"External model execution: {result.get('external_model_execution', 'not implemented')}",
                f"Real actions: {str(result.get('real_actions', False)).lower()}",
            ]
        )

    def _format_provider_health_check_dry_run(self, result: dict) -> str:
        targets = ", ".join(result.get("targets", [])) or "none"
        return "\n".join(
            [
                "Provider health-check dry run:",
                f"Stage: {result.get('stage', '34 provider health-check dry-run')}",
                f"Context: {result.get('context', '')}",
                f"Scope: {result.get('scope', '')}",
                f"Targets: {targets}",
                f"Provider known in registry: {str(result.get('provider_known_in_registry', False)).lower()}",
                f"Dry run only: {str(result.get('dry_run_only', True)).lower()}",
                f"Would call provider: {str(result.get('would_call_provider', False)).lower()}",
                f"Would use network: {str(result.get('would_use_network', False)).lower()}",
                f"Would read API key file: {str(result.get('would_read_api_key_file', False)).lower()}",
                f"Would load secret values: {str(result.get('would_load_secret_values', False)).lower()}",
                f"Would ping provider: {str(result.get('would_ping_provider', False)).lower()}",
                f"Would authenticate: {str(result.get('would_authenticate', False)).lower()}",
                f"Would route model: {str(result.get('would_route_model', False)).lower()}",
                f"Would execute external model: {str(result.get('would_execute_external_model', False)).lower()}",
                f"Would take real action: {str(result.get('would_take_real_action', False)).lower()}",
                f"Real health check performed: {str(result.get('real_health_check_performed', False)).lower()}",
                f"Provider is Lucy identity: {str(result.get('provider_is_lucy_identity', False)).lower()}",
                f"Message: {result.get('message', '')}",
            ]
        )

    def _format_provider_health_check_records(self, records: list) -> str:
        if not records:
            return "Provider health-check dry runs:\nNone recorded yet."
        lines = ["Provider health-check dry runs:"]
        for rec in records:
            targets = ", ".join(rec.get("targets", [])) or "none"
            lines.append(
                f"- {rec.get('created_at', '')} | scope={rec.get('scope', '')} | "
                f"targets={targets} | "
                f"real_health_check_performed={str(rec.get('real_health_check_performed', False)).lower()}"
            )
        return "\n".join(lines)

    def _format_provider_health_check_reset(self, result: dict) -> str:
        return "\n".join(
            [
                "Provider health-check reset:",
                f"Stage: {result.get('stage', '34 provider health-check dry-run')}",
                f"Real health check performed: {str(result.get('real_health_check_performed', False)).lower()}",
                f"Message: {result.get('message', '')}",
            ]
        )

    def _provider_registry_provider_lines(self, provider: dict) -> list[str]:
        aliases = ", ".join(provider.get("aliases", [])) or "none"
        credential_labels = ", ".join(provider.get("credential_label_only", [])) or "none"
        return [
            f"Provider ID: {provider.get('provider_id', '')}",
            f"Display name: {provider.get('display_name', '')}",
            f"Aliases: {aliases}",
            f"Role: {provider.get('role', '')}",
            f"Enabled: {str(provider.get('enabled', False)).lower()}",
            f"Future use: {provider.get('future_use', '')}",
            f"Credential labels only: {credential_labels}",
            f"API key value returned: {str(provider.get('api_key_value_returned', False)).lower()}",
            f"API key value stored: {str(provider.get('api_key_value_stored', False)).lower()}",
            f"Provider call allowed: {str(provider.get('provider_call_allowed', False)).lower()}",
            f"Network allowed: {str(provider.get('network_allowed', False)).lower()}",
            f"Health check allowed: {str(provider.get('health_check_allowed', False)).lower()}",
            f"Model routing allowed: {str(provider.get('model_routing_allowed', False)).lower()}",
            f"External model execution allowed: {str(provider.get('external_model_execution_allowed', False)).lower()}",
        ]

    def _format_secrets_provider_key_safety_status(self, result: dict) -> str:
        approval = "yes" if result.get("requires_user_approval", True) else "no"
        return "\n".join(
            [
                "Secrets/provider-key safety status:",
                f"Stage: {result.get('stage', '32 secrets/provider-key safety')}",
                f"Secrets/provider-key safety: {result.get('secrets_provider_key_safety', 'active')}",
                f"Safety records: {result.get('safety_records', 0)}",
                f"Execution mode: {result.get('execution_mode', 'safe_secret_presence_only')}",
                f"Key file name: {result.get('key_file_name', 'APIKEYS')}",
                f"Key file path: {result.get('key_file_path', '')}",
                f"Key file exists: {str(result.get('key_file_exists', False)).lower()}",
                f"Safe provider presence scan: {result.get('safe_provider_presence_scan', 'allowed')}",
                f"Secret value reading: {result.get('secret_value_reading', 'blocked')}",
                f"Secret value printing: {result.get('secret_value_printing', 'blocked')}",
                f"Secret value logging: {result.get('secret_value_logging', 'blocked')}",
                f"Secret value storage: {result.get('secret_value_storage', 'blocked')}",
                f"Secret value backup: {result.get('secret_value_backup', 'blocked')}",
                f"Root key file backup: {result.get('root_key_file_backup', 'excluded_from_normal_backup')}",
                f"Chat output of keys: {result.get('chat_output_of_keys', 'blocked')}",
                f"Provider calls: {result.get('provider_calls', 'blocked')}",
                f"Network access: {result.get('network_access', 'blocked')}",
                f"Model routing: {result.get('model_routing', 'not implemented')}",
                f"Provider registry: {result.get('provider_registry', 'not implemented')}",
                f"Provider health checks: {result.get('provider_health_checks', 'not implemented')}",
                f"Requires user approval: {approval}",
                f"Real actions: {str(result.get('real_actions', False)).lower()}",
                f"Autonomy: {result.get('autonomy', 'not implemented')}",
            ]
        )

    def _format_secret_safety_result(self, result: dict) -> str:
        if not result.get("ok"):
            return f"Secret safety unavailable: {result.get('reason', 'unknown')}"
        safety_record = result.get("safety_record", {})
        lines = ["Secret safety record:"]
        if result.get("reused"):
            lines.append("Existing secret safety record reused.")
        lines.extend(self._secret_safety_summary_lines(safety_record))
        return "\n".join(lines)

    def _format_safe_key_file_scan(self, result: dict) -> str:
        present = ", ".join(result.get("providers_present", [])) or "none"
        missing = ", ".join(result.get("providers_missing", [])) or "none"
        labels = ", ".join(result.get("recognized_provider_labels_found", [])) or "none"
        return "\n".join(
            [
                "Safe key file scan:",
                f"Stage: {result.get('stage', '32 secrets/provider-key safety')}",
                f"Scan type: {result.get('scan_type', 'safe_provider_presence_only')}",
                f"Key file name: {result.get('key_file_name', 'APIKEYS')}",
                f"Key file path: {result.get('key_file_path', '')}",
                f"Key file exists: {str(result.get('key_file_exists', False)).lower()}",
                f"Providers present: {present}",
                f"Providers missing: {missing}",
                f"Recognized provider labels found: {labels}",
                f"Unrecognized label count: {result.get('unrecognized_label_count', 0)}",
                f"Malformed line count: {result.get('malformed_line_count', 0)}",
                f"Secret values returned: {str(result.get('secret_values_returned', False)).lower()}",
                f"Secret values printed: {str(result.get('secret_values_printed', False)).lower()}",
                f"Secret values logged: {str(result.get('secret_values_logged', False)).lower()}",
                f"Secret values stored: {str(result.get('secret_values_stored', False)).lower()}",
                f"Provider calls: {str(result.get('provider_calls', False)).lower()}",
                f"Network access: {str(result.get('network_access', False)).lower()}",
                f"Real actions: {str(result.get('real_actions', False)).lower()}",
                f"Message: {result.get('message', '')}",
            ]
        )

    def _format_secrets_safety_dry_run(self, result: dict) -> str:
        safety_record = result.get("safety_record", {})
        lines = [
            "Secrets safety dry run:",
            f"Dry run only: {str(result.get('dry_run_only', True)).lower()}",
            f"Would print secret values: {str(result.get('would_print_secret_values', False)).lower()}",
            f"Would log secret values: {str(result.get('would_log_secret_values', False)).lower()}",
            f"Would store secret values: {str(result.get('would_store_secret_values', False)).lower()}",
            f"Would include key file in backup: {str(result.get('would_include_key_file_in_backup', False)).lower()}",
            f"Would send keys to chat: {str(result.get('would_send_keys_to_chat', False)).lower()}",
            f"Would call provider: {str(result.get('would_call_provider', False)).lower()}",
            f"Would use network: {str(result.get('would_use_network', False)).lower()}",
            f"Would route model: {str(result.get('would_route_model', False)).lower()}",
            f"Would run provider health check: {str(result.get('would_run_provider_health_check', False)).lower()}",
            f"Would execute external model: {str(result.get('would_execute_external_model', False)).lower()}",
            f"Would take real action: {str(result.get('would_take_real_action', False)).lower()}",
            f"Message: {result.get('message', '')}",
        ]
        lines.extend(self._secret_safety_summary_lines(safety_record))
        return "\n".join(lines)

    def _format_secret_safety_list(self, records: list[dict]) -> str:
        if not records:
            return "Secret safety records: none. Use: create secret safety record"
        lines = ["Secret safety records:"]
        for index, record in enumerate(records, start=1):
            if record.get("record_type") == "safe_key_file_scan":
                lines.append(
                    f"  {index}. {record.get('safety_record_id', '')} | "
                    f"{record.get('record_type', '')} | "
                    f"present={','.join(record.get('providers_present', [])) or 'none'} | "
                    f"missing={','.join(record.get('providers_missing', [])) or 'none'}"
                )
            else:
                lines.append(
                    f"  {index}. {record.get('safety_record_id', '')} | "
                    f"{record.get('record_type', '')} | "
                    f"{record.get('category', '')} | "
                    f"{record.get('decision', '')} | "
                    f"{record.get('context', '')}"
                )
        return "\n".join(lines)

    def _secret_safety_summary_lines(self, record: dict) -> list[str]:
        not_implemented = ", ".join(record.get("not_implemented", []))
        return [
            f"Title: {record.get('title', '')}",
            f"Context: {record.get('context', '')}",
            f"Record type: {record.get('record_type', '')}",
            f"Status: {record.get('status', 'recorded')}",
            f"Category: {record.get('category', '')}",
            f"Decision: {record.get('decision', '')}",
            f"Summary: {record.get('summary', '')}",
            f"Allowed response: {record.get('allowed_response', '')}",
            f"Recommended next step: {record.get('recommended_next_step', '')}",
            f"Key file name: {record.get('key_file_name', '')}",
            f"Key file path: {record.get('key_file_path', '')}",
            f"Key file exists: {str(record.get('key_file_exists', False)).lower()}",
            f"Safe provider presence scan allowed: {str(record.get('safe_provider_presence_scan_allowed', True)).lower()}",
            f"Secret value reading allowed: {str(record.get('secret_value_reading_allowed', False)).lower()}",
            f"Secret value printing allowed: {str(record.get('secret_value_printing_allowed', False)).lower()}",
            f"Secret value logging allowed: {str(record.get('secret_value_logging_allowed', False)).lower()}",
            f"Secret value storage allowed: {str(record.get('secret_value_storage_allowed', False)).lower()}",
            f"Secret value backup allowed: {str(record.get('secret_value_backup_allowed', False)).lower()}",
            f"Root key file backup allowed: {str(record.get('root_key_file_backup_allowed', False)).lower()}",
            f"Chat output of keys allowed: {str(record.get('chat_output_of_keys_allowed', False)).lower()}",
            f"Provider call allowed: {str(record.get('provider_call_allowed', False)).lower()}",
            f"Network allowed: {str(record.get('network_allowed', False)).lower()}",
            f"Model routing allowed: {str(record.get('model_routing_allowed', False)).lower()}",
            f"Provider registry allowed: {str(record.get('provider_registry_allowed', False)).lower()}",
            f"Provider health check allowed: {str(record.get('provider_health_check_allowed', False)).lower()}",
            f"External model execution allowed: {str(record.get('external_model_execution_allowed', False)).lower()}",
            f"Real action allowed: {str(record.get('real_action_allowed', False)).lower()}",
            f"Dry-run only: {str(record.get('dry_run_only', True)).lower()}",
            f"Requires user approval: {str(record.get('requires_user_approval', True)).lower()}",
            f"Blocked until: {record.get('blocked_until', '')}",
            f"Not implemented: {not_implemented}",
        ]

    def _format_provider_identity_boundary_status(self, result: dict) -> str:
        approval = "yes" if result.get("requires_user_approval", True) else "no"
        return "\n".join(
            [
                "Provider identity boundary status:",
                f"Stage: {result.get('stage', '31 provider/api identity boundary')}",
                f"Provider identity boundary: {result.get('provider_identity_boundary', 'active')}",
                f"Boundary records: {result.get('boundary_records', 0)}",
                f"Execution mode: {result.get('execution_mode', 'identity_boundary_only')}",
                f"Lucy identity source: {result.get('lucy_identity_source', 'local_guardian_memory_runtime_project_state')}",
                f"Provider role: {result.get('provider_role', 'external_tool_only')}",
                f"Model role: {result.get('model_role', 'external_tool_only')}",
                f"API key role: {result.get('api_key_role', 'credential_only')}",
                f"External answer role: {result.get('external_answer_role', 'tool_output_only')}",
                f"Provider can replace Lucy identity: {str(result.get('provider_can_replace_lucy_identity', False)).lower()}",
                f"Model can replace Lucy identity: {str(result.get('model_can_replace_lucy_identity', False)).lower()}",
                f"API key file reading: {result.get('api_key_file_reading', 'blocked_until_stage_32')}",
                f"API key loading: {result.get('api_key_loading', 'blocked_until_stage_32')}",
                f"Provider calls: {result.get('provider_calls', 'blocked')}",
                f"Network access: {result.get('network_access', 'blocked')}",
                f"Model routing: {result.get('model_routing', 'not implemented')}",
                f"Provider health checks: {result.get('provider_health_checks', 'not implemented')}",
                f"Cost/quota tracking: {result.get('cost_quota_tracking', 'not implemented')}",
                f"Requires user approval: {approval}",
                f"Real actions: {str(result.get('real_actions', False)).lower()}",
                f"Autonomy: {result.get('autonomy', 'not implemented')}",
            ]
        )

    def _format_provider_identity_boundary_result(self, result: dict) -> str:
        if not result.get("ok"):
            return f"Provider identity boundary unavailable: {result.get('reason', 'unknown')}"
        boundary_record = result.get("boundary_record", {})
        lines = ["Provider identity boundary record:"]
        if result.get("reused"):
            lines.append("Existing provider identity boundary record reused.")
        lines.extend(self._provider_identity_boundary_summary_lines(boundary_record))
        return "\n".join(lines)

    def _format_provider_identity_boundary_dry_run(self, result: dict) -> str:
        boundary_record = result.get("boundary_record", {})
        lines = [
            "Provider identity boundary dry run:",
            f"Dry run only: {str(result.get('dry_run_only', True)).lower()}",
            f"Would read API key file: {str(result.get('would_read_api_key_file', False)).lower()}",
            f"Would load API keys: {str(result.get('would_load_api_keys', False)).lower()}",
            f"Would call provider: {str(result.get('would_call_provider', False)).lower()}",
            f"Would use network: {str(result.get('would_use_network', False)).lower()}",
            f"Would route model: {str(result.get('would_route_model', False)).lower()}",
            f"Would run provider health check: {str(result.get('would_run_provider_health_check', False)).lower()}",
            f"Would execute external model: {str(result.get('would_execute_external_model', False)).lower()}",
            f"Would ingest provider output: {str(result.get('would_ingest_provider_output', False)).lower()}",
            f"Would replace Lucy identity: {str(result.get('would_replace_lucy_identity', False)).lower()}",
            f"Would override Guardian: {str(result.get('would_override_guardian', False)).lower()}",
            f"Would override memory: {str(result.get('would_override_memory', False)).lower()}",
            f"Would override runtime state: {str(result.get('would_override_runtime_state', False)).lower()}",
            f"Would take real action: {str(result.get('would_take_real_action', False)).lower()}",
            f"Message: {result.get('message', '')}",
        ]
        lines.extend(self._provider_identity_boundary_summary_lines(boundary_record))
        return "\n".join(lines)

    def _format_provider_identity_boundary_list(self, records: list[dict]) -> str:
        if not records:
            return "Provider identity boundary records: none. Use: create provider identity boundary record"
        lines = ["Provider identity boundary records:"]
        for index, record in enumerate(records, start=1):
            lines.append(
                f"  {index}. {record.get('boundary_record_id', '')} | "
                f"{record.get('category', '')} | "
                f"{record.get('decision', '')} | "
                f"{record.get('context', '')}"
            )
        return "\n".join(lines)

    def _provider_identity_boundary_summary_lines(self, record: dict) -> list[str]:
        not_implemented = ", ".join(record.get("not_implemented", []))
        return [
            f"Title: {record.get('title', '')}",
            f"Context: {record.get('context', '')}",
            f"Boundary type: {record.get('boundary_type', '')}",
            f"Status: {record.get('status', 'recorded')}",
            f"Category: {record.get('category', '')}",
            f"Decision: {record.get('decision', '')}",
            f"Summary: {record.get('summary', '')}",
            f"Allowed response: {record.get('allowed_response', '')}",
            f"Recommended next step: {record.get('recommended_next_step', '')}",
            f"Lucy identity source: {record.get('lucy_identity_source', '')}",
            f"Provider role: {record.get('provider_role', '')}",
            f"Model role: {record.get('model_role', '')}",
            f"API key role: {record.get('api_key_role', '')}",
            f"External answer role: {record.get('external_answer_role', '')}",
            f"Requires user approval: {str(record.get('requires_user_approval', True)).lower()}",
            f"Dry-run only: {str(record.get('dry_run_only', True)).lower()}",
            f"Identity boundary only: {str(record.get('identity_boundary_only', True)).lower()}",
            f"Provider can replace Lucy identity: {str(record.get('provider_can_replace_lucy_identity', False)).lower()}",
            f"Model can replace Lucy identity: {str(record.get('model_can_replace_lucy_identity', False)).lower()}",
            f"API output can override Guardian: {str(record.get('api_output_can_override_guardian', False)).lower()}",
            f"API output can override memory: {str(record.get('api_output_can_override_memory', False)).lower()}",
            f"API output can override runtime state: {str(record.get('api_output_can_override_runtime_state', False)).lower()}",
            f"API key file reading allowed: {str(record.get('api_key_file_reading_allowed', False)).lower()}",
            f"API key loading allowed: {str(record.get('api_key_loading_allowed', False)).lower()}",
            f"Provider call allowed: {str(record.get('provider_call_allowed', False)).lower()}",
            f"Network allowed: {str(record.get('network_allowed', False)).lower()}",
            f"Model routing allowed: {str(record.get('model_routing_allowed', False)).lower()}",
            f"Provider health check allowed: {str(record.get('provider_health_check_allowed', False)).lower()}",
            f"External model execution allowed: {str(record.get('external_model_execution_allowed', False)).lower()}",
            f"Provider output ingestion allowed: {str(record.get('provider_output_ingestion_allowed', False)).lower()}",
            f"Cost/quota tracking allowed: {str(record.get('cost_quota_tracking_allowed', False)).lower()}",
            f"Real action allowed: {str(record.get('real_action_allowed', False)).lower()}",
            f"Blocked until: {record.get('blocked_until', '')}",
            f"Not implemented: {not_implemented}",
        ]

    def _format_autonomy_boundaries_status(self, result: dict) -> str:
        approval = "yes" if result.get("requires_user_approval", True) else "no"
        return "\n".join(
            [
                "Autonomy boundaries status:",
                f"Stage: {result.get('stage', '30 autonomy boundaries')}",
                f"Autonomy boundaries: {result.get('autonomy_boundaries', 'active')}",
                f"Boundary records: {result.get('boundary_records', 0)}",
                f"Execution mode: {result.get('execution_mode', 'manual_permission_boundaries_only')}",
                f"Allowed prepare: {str(result.get('allowed_prepare', True)).lower()}",
                f"Allowed explain: {str(result.get('allowed_explain', True)).lower()}",
                f"Allowed evaluate: {str(result.get('allowed_evaluate', True)).lower()}",
                f"Allowed safe structured records: {str(result.get('allowed_safe_structured_records', True)).lower()}",
                f"Allowed suggest next steps: {str(result.get('allowed_suggest_next_steps', True)).lower()}",
                f"Requires user approval: {approval}",
                f"Independent action: {result.get('independent_action', 'blocked')}",
                f"Guardian bypass: {result.get('guardian_bypass', 'blocked')}",
                f"Self-modification: {result.get('self_modification', 'blocked')}",
                f"External app control: {result.get('external_app_control', 'blocked')}",
                f"Message sending: {result.get('message_sending', 'blocked')}",
                f"Email sending: {result.get('email_sending', 'blocked')}",
                f"Money movement: {result.get('money_movement', 'blocked')}",
                f"API/provider keys: {result.get('api_provider_keys', 'blocked')}",
                f"Network access: {result.get('network_access', 'blocked')}",
                f"Background monitoring: {result.get('background_monitoring', 'blocked')}",
                f"Scheduled autonomous execution: {result.get('scheduled_autonomous_execution', 'blocked')}",
                f"Automatic notifications: {result.get('automatic_notifications', 'blocked')}",
                f"Hidden persuasion: {result.get('hidden_persuasion', 'blocked')}",
                f"Fake autonomy claims: {result.get('fake_autonomy_claims', 'blocked')}",
                f"Real actions: {str(result.get('real_actions', False)).lower()}",
                f"Autonomy: {result.get('autonomy', 'bounded_manual_assistant_only')}",
            ]
        )

    def _format_autonomy_boundary_result(self, result: dict) -> str:
        if not result.get("ok"):
            return f"Autonomy boundary unavailable: {result.get('reason', 'unknown')}"
        boundary_record = result.get("boundary_record", {})
        lines = ["Autonomy boundary record:"]
        if result.get("reused"):
            lines.append("Existing autonomy boundary record reused.")
        lines.extend(self._autonomy_boundary_summary_lines(boundary_record))
        return "\n".join(lines)

    def _format_autonomy_boundaries_dry_run(self, result: dict) -> str:
        boundary_record = result.get("boundary_record", {})
        lines = [
            "Autonomy boundaries dry run:",
            f"Dry run only: {str(result.get('dry_run_only', True)).lower()}",
            f"Would act independently: {str(result.get('would_act_independently', False)).lower()}",
            f"Would bypass Guardian: {str(result.get('would_bypass_guardian', False)).lower()}",
            f"Would self-modify: {str(result.get('would_self_modify', False)).lower()}",
            f"Would control apps: {str(result.get('would_control_apps', False)).lower()}",
            f"Would send message: {str(result.get('would_send_message', False)).lower()}",
            f"Would send email: {str(result.get('would_send_email', False)).lower()}",
            f"Would move money: {str(result.get('would_move_money', False)).lower()}",
            f"Would use API keys: {str(result.get('would_use_api_keys', False)).lower()}",
            f"Would use network: {str(result.get('would_use_network', False)).lower()}",
            f"Would monitor background: {str(result.get('would_monitor_background', False)).lower()}",
            f"Would schedule autonomous execution: {str(result.get('would_schedule_autonomous_execution', False)).lower()}",
            f"Would send notification: {str(result.get('would_send_notification', False)).lower()}",
            f"Would use hidden persuasion: {str(result.get('would_use_hidden_persuasion', False)).lower()}",
            f"Would claim fake autonomy: {str(result.get('would_claim_fake_autonomy', False)).lower()}",
            f"Would take real action: {str(result.get('would_take_real_action', False)).lower()}",
            f"Real action allowed: {str(result.get('real_action_allowed', False)).lower()}",
            f"Message: {result.get('message', '')}",
        ]
        lines.extend(self._autonomy_boundary_summary_lines(boundary_record))
        return "\n".join(lines)

    def _format_autonomy_boundary_list(self, records: list[dict]) -> str:
        if not records:
            return "Autonomy boundary records: none. Use: create autonomy boundary record"
        lines = ["Autonomy boundary records:"]
        for index, record in enumerate(records, start=1):
            lines.append(
                f"  {index}. {record.get('boundary_record_id', '')} | "
                f"{record.get('category', '')} | "
                f"{record.get('decision', '')} | "
                f"{record.get('request', '')}"
            )
        return "\n".join(lines)

    def _autonomy_boundary_summary_lines(self, record: dict) -> list[str]:
        not_implemented = ", ".join(record.get("not_implemented", []))
        return [
            f"Title: {record.get('title', '')}",
            f"Request: {record.get('request', '')}",
            f"Boundary type: {record.get('boundary_type', '')}",
            f"Status: {record.get('status', 'recorded')}",
            f"Category: {record.get('category', '')}",
            f"Decision: {record.get('decision', '')}",
            f"Summary: {record.get('summary', '')}",
            f"Allowed response: {record.get('allowed_response', '')}",
            f"Recommended next step: {record.get('recommended_next_step', '')}",
            f"Requires user approval: {str(record.get('requires_user_approval', True)).lower()}",
            f"Dry-run only: {str(record.get('dry_run_only', True)).lower()}",
            f"Manual control only: {str(record.get('manual_control_only', True)).lower()}",
            f"Prepare allowed: {str(record.get('prepare_allowed', True)).lower()}",
            f"Explain allowed: {str(record.get('explain_allowed', True)).lower()}",
            f"Evaluate allowed: {str(record.get('evaluate_allowed', True)).lower()}",
            f"Safe structured records allowed: {str(record.get('safe_structured_records_allowed', True)).lower()}",
            f"Suggest next steps allowed: {str(record.get('suggest_next_steps_allowed', True)).lower()}",
            f"Independent action allowed: {str(record.get('independent_action_allowed', False)).lower()}",
            f"Guardian bypass allowed: {str(record.get('guardian_bypass_allowed', False)).lower()}",
            f"Self-modification allowed: {str(record.get('self_modification_allowed', False)).lower()}",
            f"External app control allowed: {str(record.get('external_app_control_allowed', False)).lower()}",
            f"Message sending allowed: {str(record.get('message_sending_allowed', False)).lower()}",
            f"Email sending allowed: {str(record.get('email_sending_allowed', False)).lower()}",
            f"Money movement allowed: {str(record.get('money_movement_allowed', False)).lower()}",
            f"API keys allowed: {str(record.get('api_keys_allowed', False)).lower()}",
            f"Network allowed: {str(record.get('network_allowed', False)).lower()}",
            f"Background monitoring allowed: {str(record.get('background_monitoring_allowed', False)).lower()}",
            f"Scheduled autonomous execution allowed: {str(record.get('scheduled_autonomous_execution_allowed', False)).lower()}",
            f"Automatic notifications allowed: {str(record.get('automatic_notifications_allowed', False)).lower()}",
            f"Hidden persuasion allowed: {str(record.get('hidden_persuasion_allowed', False)).lower()}",
            f"Fake autonomy claims allowed: {str(record.get('fake_autonomy_claims_allowed', False)).lower()}",
            f"Real action allowed: {str(record.get('real_action_allowed', False)).lower()}",
            f"Blocked until: {record.get('blocked_until', '')}",
            f"Not implemented: {not_implemented}",
        ]

    def _format_time_awareness_status(self, result: dict) -> str:
        approval = "yes" if result.get("approval_required", True) else "no"
        return "\n".join(
            [
                "Time awareness status:",
                f"Stage: {result.get('stage', '29 time awareness')}",
                f"Time awareness: {result.get('time_awareness', 'active')}",
                f"Time context records: {result.get('time_context_records', 0)}",
                f"Execution mode: {result.get('execution_mode', 'manual_explicit_time_context_only')}",
                f"Local runtime clock: {result.get('local_runtime_clock', 'allowed_for_manual_context')}",
                f"Network time lookup: {result.get('network_time_lookup', 'blocked')}",
                f"Autonomous reminders: {result.get('autonomous_reminders', 'blocked')}",
                f"Scheduled actions: {result.get('scheduled_actions', 'blocked')}",
                f"Automatic notifications: {result.get('automatic_notifications', 'blocked')}",
                f"Background monitoring: {result.get('background_monitoring', 'blocked')}",
                f"Calendar reading: {result.get('calendar_reading', 'blocked')}",
                f"Email reading: {result.get('email_reading', 'blocked')}",
                f"External app reading: {result.get('external_app_reading', 'blocked')}",
                f"Real actions: {str(result.get('real_actions', False)).lower()}",
                f"Network access: {result.get('network_access', 'blocked')}",
                f"API/provider keys: {result.get('api_provider_keys', 'blocked')}",
                f"Approval required: {approval}",
                f"Autonomy: {result.get('autonomy', 'not implemented')}",
            ]
        )

    def _format_time_context_result(self, result: dict) -> str:
        if not result.get("ok"):
            return f"Time context unavailable: {result.get('reason', 'unknown')}"
        time_context = result.get("time_context", {})
        lines = ["Time context:"]
        if result.get("reused"):
            lines.append("Existing time context reused.")
        lines.extend(self._time_context_summary_lines(time_context))
        return "\n".join(lines)

    def _format_time_awareness_dry_run(self, result: dict) -> str:
        time_context = result.get("time_context", {})
        lines = [
            "Time awareness dry run:",
            f"Dry run only: {str(result.get('dry_run_only', True)).lower()}",
            f"Would create reminder: {str(result.get('would_create_reminder', False)).lower()}",
            f"Would schedule action: {str(result.get('would_schedule_action', False)).lower()}",
            f"Would send notification: {str(result.get('would_send_notification', False)).lower()}",
            f"Would monitor background: {str(result.get('would_monitor_background', False)).lower()}",
            f"Would read calendar: {str(result.get('would_read_calendar', False)).lower()}",
            f"Would read email: {str(result.get('would_read_email', False)).lower()}",
            f"Would read external apps: {str(result.get('would_read_external_apps', False)).lower()}",
            f"Would use network time: {str(result.get('would_use_network_time', False)).lower()}",
            f"Would use network: {str(result.get('would_use_network', False)).lower()}",
            f"Would use API keys: {str(result.get('would_use_api_keys', False)).lower()}",
            f"Would take action: {str(result.get('would_take_action', False)).lower()}",
            f"Real action allowed: {str(result.get('real_action_allowed', False)).lower()}",
            f"Message: {result.get('message', '')}",
        ]
        lines.extend(self._time_context_summary_lines(time_context))
        return "\n".join(lines)

    def _format_time_context_list(self, contexts: list[dict]) -> str:
        if not contexts:
            return "Time contexts: none. Use: create time context"
        lines = ["Time contexts:"]
        for index, context in enumerate(contexts, start=1):
            lines.append(
                f"  {index}. {context.get('time_context_id', '')} | "
                f"{context.get('category', '')} | "
                f"{context.get('interpretation', '')} | "
                f"{context.get('explicit_time_context', '')}"
            )
        return "\n".join(lines)

    def _time_context_summary_lines(self, context: dict) -> list[str]:
        not_implemented = ", ".join(context.get("not_implemented", []))
        return [
            f"Title: {context.get('title', '')}",
            f"Explicit time context: {context.get('explicit_time_context', '')}",
            f"Awareness type: {context.get('awareness_type', '')}",
            f"Status: {context.get('status', 'observed')}",
            f"Category: {context.get('category', '')}",
            f"Interpretation: {context.get('interpretation', '')}",
            f"Summary: {context.get('summary', '')}",
            f"Recommended reply adjustment: {context.get('recommended_reply_adjustment', '')}",
            f"Recommended next step: {context.get('recommended_next_step', '')}",
            f"Local runtime clock used: {str(context.get('local_runtime_clock_used', True)).lower()}",
            f"Observed at UTC: {context.get('observed_at_utc', '')}",
            f"Requires manual review: {str(context.get('requires_manual_review', True)).lower()}",
            f"Requires approval: {str(context.get('requires_approval', True)).lower()}",
            f"Dry-run only: {str(context.get('dry_run_only', True)).lower()}",
            f"Manual context only: {str(context.get('manual_context_only', True)).lower()}",
            f"Autonomous reminders allowed: {str(context.get('autonomous_reminders_allowed', False)).lower()}",
            f"Scheduled actions allowed: {str(context.get('scheduled_actions_allowed', False)).lower()}",
            f"Automatic notifications allowed: {str(context.get('automatic_notifications_allowed', False)).lower()}",
            f"Background monitoring allowed: {str(context.get('background_monitoring_allowed', False)).lower()}",
            f"Calendar reading allowed: {str(context.get('calendar_reading_allowed', False)).lower()}",
            f"Email reading allowed: {str(context.get('email_reading_allowed', False)).lower()}",
            f"External app reading allowed: {str(context.get('external_app_reading_allowed', False)).lower()}",
            f"Network time lookup allowed: {str(context.get('network_time_lookup_allowed', False)).lower()}",
            f"Real action allowed: {str(context.get('real_action_allowed', False)).lower()}",
            f"Network allowed: {str(context.get('network_allowed', False)).lower()}",
            f"API keys allowed: {str(context.get('api_keys_allowed', False)).lower()}",
            f"Blocked until: {context.get('blocked_until', '')}",
            f"Not implemented: {not_implemented}",
        ]

    def _format_human_state_awareness_status(self, result: dict) -> str:
        approval = "yes" if result.get("approval_required", True) else "no"
        return "\n".join(
            [
                "Human-state awareness status:",
                f"Stage: {result.get('stage', '28 human-state awareness')}",
                f"Human-state awareness: {result.get('human_state_awareness', 'active')}",
                f"State signals: {result.get('state_signals', 0)}",
                f"Execution mode: {result.get('execution_mode', 'explicit_self_report_only')}",
                f"Emotion reading: {result.get('emotion_reading', 'blocked')}",
                f"Diagnosis: {result.get('diagnosis', 'blocked')}",
                f"Medical final judgment: {result.get('medical_final_judgment', 'blocked')}",
                f"Mental-health final judgment: {result.get('mental_health_final_judgment', 'blocked')}",
                f"Psychological profiling: {result.get('psychological_profiling', 'blocked')}",
                f"Biometric monitoring: {result.get('biometric_monitoring', 'blocked')}",
                f"Camera monitoring: {result.get('camera_monitoring', 'blocked')}",
                f"Microphone monitoring: {result.get('microphone_monitoring', 'blocked')}",
                f"App reading: {result.get('app_reading', 'blocked')}",
                f"Manipulation: {result.get('manipulation', 'blocked')}",
                f"Hidden persuasion: {result.get('hidden_persuasion', 'blocked')}",
                f"Real actions: {str(result.get('real_actions', False)).lower()}",
                f"Network access: {result.get('network_access', 'blocked')}",
                f"API/provider keys: {result.get('api_provider_keys', 'blocked')}",
                f"Background monitoring: {result.get('background_monitoring', 'blocked')}",
                f"Approval required: {approval}",
                f"Autonomy: {result.get('autonomy', 'not implemented')}",
            ]
        )

    def _format_human_state_signal_result(self, result: dict) -> str:
        if not result.get("ok"):
            return f"Human-state signal unavailable: {result.get('reason', 'unknown')}"
        state_signal = result.get("state_signal", {})
        lines = ["Human-state signal:"]
        if result.get("reused"):
            lines.append("Existing human-state signal reused.")
        lines.extend(self._human_state_signal_summary_lines(state_signal))
        return "\n".join(lines)

    def _format_human_state_awareness_dry_run(self, result: dict) -> str:
        state_signal = result.get("state_signal", {})
        lines = [
            "Human-state awareness dry run:",
            f"Dry run only: {str(result.get('dry_run_only', True)).lower()}",
            f"Would read emotions: {str(result.get('would_read_emotions', False)).lower()}",
            f"Would diagnose: {str(result.get('would_diagnose', False)).lower()}",
            f"Would profile person: {str(result.get('would_profile_person', False)).lower()}",
            f"Would monitor biometrics: {str(result.get('would_monitor_biometrics', False)).lower()}",
            f"Would use camera: {str(result.get('would_use_camera', False)).lower()}",
            f"Would use microphone: {str(result.get('would_use_microphone', False)).lower()}",
            f"Would read apps: {str(result.get('would_read_apps', False)).lower()}",
            f"Would manipulate: {str(result.get('would_manipulate', False)).lower()}",
            f"Would take action: {str(result.get('would_take_action', False)).lower()}",
            f"Would use network: {str(result.get('would_use_network', False)).lower()}",
            f"Would use API keys: {str(result.get('would_use_api_keys', False)).lower()}",
            f"Real action allowed: {str(result.get('real_action_allowed', False)).lower()}",
            f"Message: {result.get('message', '')}",
        ]
        lines.extend(self._human_state_signal_summary_lines(state_signal))
        return "\n".join(lines)

    def _format_human_state_signal_list(self, signals: list[dict]) -> str:
        if not signals:
            return "Human-state signals: none. Use: create human state signal"
        lines = ["Human-state signals:"]
        for index, signal in enumerate(signals, start=1):
            lines.append(
                f"  {index}. {signal.get('state_signal_id', '')} | "
                f"{signal.get('category', '')} | "
                f"{signal.get('support_mode', '')} | "
                f"{signal.get('explicit_signal', '')}"
            )
        return "\n".join(lines)

    def _human_state_signal_summary_lines(self, signal: dict) -> list[str]:
        not_implemented = ", ".join(signal.get("not_implemented", []))
        return [
            f"Title: {signal.get('title', '')}",
            f"Explicit signal: {signal.get('explicit_signal', '')}",
            f"Awareness type: {signal.get('awareness_type', '')}",
            f"Status: {signal.get('status', 'observed')}",
            f"Category: {signal.get('category', '')}",
            f"Support mode: {signal.get('support_mode', '')}",
            f"Summary: {signal.get('summary', '')}",
            f"Recommended reply adjustment: {signal.get('recommended_reply_adjustment', '')}",
            f"Recommended next step: {signal.get('recommended_next_step', '')}",
            f"Requires manual review: {str(signal.get('requires_manual_review', True)).lower()}",
            f"Requires approval: {str(signal.get('requires_approval', True)).lower()}",
            f"Dry-run only: {str(signal.get('dry_run_only', True)).lower()}",
            f"Explicit self-report only: {str(signal.get('explicit_self_report_only', True)).lower()}",
            f"Emotion reading allowed: {str(signal.get('emotion_reading_allowed', False)).lower()}",
            f"Diagnosis allowed: {str(signal.get('diagnosis_allowed', False)).lower()}",
            f"Medical final judgment allowed: {str(signal.get('medical_final_judgment_allowed', False)).lower()}",
            f"Mental-health final judgment allowed: {str(signal.get('mental_health_final_judgment_allowed', False)).lower()}",
            f"Psychological profiling allowed: {str(signal.get('psychological_profiling_allowed', False)).lower()}",
            f"Biometric monitoring allowed: {str(signal.get('biometric_monitoring_allowed', False)).lower()}",
            f"Camera monitoring allowed: {str(signal.get('camera_monitoring_allowed', False)).lower()}",
            f"Microphone monitoring allowed: {str(signal.get('microphone_monitoring_allowed', False)).lower()}",
            f"App reading allowed: {str(signal.get('app_reading_allowed', False)).lower()}",
            f"Manipulation allowed: {str(signal.get('manipulation_allowed', False)).lower()}",
            f"Hidden persuasion allowed: {str(signal.get('hidden_persuasion_allowed', False)).lower()}",
            f"Real action allowed: {str(signal.get('real_action_allowed', False)).lower()}",
            f"Network allowed: {str(signal.get('network_allowed', False)).lower()}",
            f"API keys allowed: {str(signal.get('api_keys_allowed', False)).lower()}",
            f"Background monitoring allowed: {str(signal.get('background_monitoring_allowed', False)).lower()}",
            f"Blocked until: {signal.get('blocked_until', '')}",
            f"Not implemented: {not_implemented}",
        ]

    def _format_adaptive_communication_status(self, result: dict) -> str:
        approval = "yes" if result.get("approval_required", True) else "no"
        return "\n".join(
            [
                "Adaptive communication status:",
                f"Stage: {result.get('stage', '27 adaptive communication')}",
                f"Adaptive communication: {result.get('adaptive_communication', 'active')}",
                f"Style profiles: {result.get('style_profiles', 0)}",
                f"Execution mode: {result.get('execution_mode', 'explicit_context_style_only')}",
                f"Emotion reading: {result.get('emotion_reading', 'blocked')}",
                f"Human-state awareness: {result.get('human_state_awareness', 'not implemented')}",
                f"Psychological profiling: {result.get('psychological_profiling', 'blocked')}",
                f"Manipulation: {result.get('manipulation', 'blocked')}",
                f"Hidden persuasion: {result.get('hidden_persuasion', 'blocked')}",
                f"Autonomous messaging: {result.get('autonomous_messaging', 'blocked')}",
                f"Real actions: {str(result.get('real_actions', False)).lower()}",
                f"Network access: {result.get('network_access', 'blocked')}",
                f"API/provider keys: {result.get('api_provider_keys', 'blocked')}",
                f"Background monitoring: {result.get('background_monitoring', 'blocked')}",
                f"Approval required: {approval}",
                f"Autonomy: {result.get('autonomy', 'not implemented')}",
            ]
        )

    def _format_adaptive_communication_result(self, result: dict) -> str:
        if not result.get("ok"):
            return f"Adaptive communication unavailable: {result.get('reason', 'unknown')}"
        profile = result.get("profile", {})
        lines = ["Adaptive communication profile:"]
        if result.get("reused"):
            lines.append("Existing adaptive communication profile reused.")
        lines.extend(self._adaptive_communication_summary_lines(profile))
        return "\n".join(lines)

    def _format_adaptive_communication_dry_run(self, result: dict) -> str:
        profile = result.get("profile", {})
        lines = [
            "Adaptive communication dry run:",
            f"Dry run only: {str(result.get('dry_run_only', True)).lower()}",
            f"Would read emotions: {str(result.get('would_read_emotions', False)).lower()}",
            f"Would profile person: {str(result.get('would_profile_person', False)).lower()}",
            f"Would manipulate: {str(result.get('would_manipulate', False)).lower()}",
            f"Would send message: {str(result.get('would_send_message', False)).lower()}",
            f"Would take action: {str(result.get('would_take_action', False)).lower()}",
            f"Would use network: {str(result.get('would_use_network', False)).lower()}",
            f"Would use API keys: {str(result.get('would_use_api_keys', False)).lower()}",
            f"Real action allowed: {str(result.get('real_action_allowed', False)).lower()}",
            f"Message: {result.get('message', '')}",
        ]
        lines.extend(self._adaptive_communication_summary_lines(profile))
        return "\n".join(lines)

    def _format_adaptive_communication_list(self, profiles: list[dict]) -> str:
        if not profiles:
            return "Adaptive communication profiles: none. Use: create adaptive communication profile"
        lines = ["Adaptive communication profiles:"]
        for index, profile in enumerate(profiles, start=1):
            lines.append(
                f"  {index}. {profile.get('style_profile_id', '')} | "
                f"{profile.get('mode', '')} | "
                f"{profile.get('response_length', '')} | "
                f"{profile.get('context', '')}"
            )
        return "\n".join(lines)

    def _adaptive_communication_summary_lines(self, profile: dict) -> list[str]:
        not_implemented = ", ".join(profile.get("not_implemented", []))
        return [
            f"Title: {profile.get('title', '')}",
            f"Context: {profile.get('context', '')}",
            f"Communication type: {profile.get('communication_type', '')}",
            f"Status: {profile.get('status', 'observed')}",
            f"Mode: {profile.get('mode', '')}",
            f"Tone: {profile.get('tone', '')}",
            f"Response length: {profile.get('response_length', '')}",
            f"Structure: {profile.get('structure', '')}",
            f"Summary: {profile.get('summary', '')}",
            f"Recommended reply rule: {profile.get('recommended_reply_rule', '')}",
            f"Requires manual review: {str(profile.get('requires_manual_review', True)).lower()}",
            f"Requires approval: {str(profile.get('requires_approval', True)).lower()}",
            f"Dry-run only: {str(profile.get('dry_run_only', True)).lower()}",
            f"Emotion reading allowed: {str(profile.get('emotion_reading_allowed', False)).lower()}",
            f"Human-state awareness allowed: {str(profile.get('human_state_awareness_allowed', False)).lower()}",
            f"Psychological profiling allowed: {str(profile.get('psychological_profiling_allowed', False)).lower()}",
            f"Manipulation allowed: {str(profile.get('manipulation_allowed', False)).lower()}",
            f"Hidden persuasion allowed: {str(profile.get('hidden_persuasion_allowed', False)).lower()}",
            f"Autonomous messaging allowed: {str(profile.get('autonomous_messaging_allowed', False)).lower()}",
            f"Real action allowed: {str(profile.get('real_action_allowed', False)).lower()}",
            f"Network allowed: {str(profile.get('network_allowed', False)).lower()}",
            f"API keys allowed: {str(profile.get('api_keys_allowed', False)).lower()}",
            f"Background monitoring allowed: {str(profile.get('background_monitoring_allowed', False)).lower()}",
            f"Blocked until: {profile.get('blocked_until', '')}",
            f"Not implemented: {not_implemented}",
        ]

    def _format_judgment_status(self, result: dict) -> str:
        approval = "yes" if result.get("approval_required", True) else "no"
        return "\n".join(
            [
                "Judgment status:",
                f"Stage: {result.get('stage', '26 judgment')}",
                f"Judgment: {result.get('judgment', 'active')}",
                f"Judgment records: {result.get('judgment_records', 0)}",
                f"Execution mode: {result.get('execution_mode', 'manual_cautious_assessment_only')}",
                f"Guardian override: {result.get('guardian_override', 'blocked')}",
                f"Final decisions: {result.get('final_decisions', 'blocked')}",
                f"Legal/medical/financial final decisions: {result.get('legal_medical_financial_final_decisions', 'blocked')}",
                f"Money movement: {result.get('money_movement', 'blocked')}",
                f"Real actions: {str(result.get('real_actions', False)).lower()}",
                f"Network access: {result.get('network_access', 'blocked')}",
                f"API/provider keys: {result.get('api_provider_keys', 'blocked')}",
                f"Background monitoring: {result.get('background_monitoring', 'blocked')}",
                f"Approval required: {approval}",
                f"Autonomy: {result.get('autonomy', 'not implemented')}",
            ]
        )

    def _format_judgment_result(self, result: dict) -> str:
        if not result.get("ok"):
            return f"Judgment unavailable: {result.get('reason', 'unknown')}"
        judgment = result.get("judgment", {})
        lines = ["Judgment record:"]
        if result.get("reused"):
            lines.append("Existing judgment record reused.")
        lines.extend(self._judgment_summary_lines(judgment))
        return "\n".join(lines)

    def _format_judgment_dry_run(self, result: dict) -> str:
        judgment = result.get("judgment", {})
        lines = [
            "Judgment dry run:",
            f"Dry run only: {str(result.get('dry_run_only', True)).lower()}",
            f"Would override Guardian: {str(result.get('would_override_guardian', False)).lower()}",
            f"Would make final decision: {str(result.get('would_make_final_decision', False)).lower()}",
            f"Would take action: {str(result.get('would_take_action', False)).lower()}",
            f"Would use network: {str(result.get('would_use_network', False)).lower()}",
            f"Would use API keys: {str(result.get('would_use_api_keys', False)).lower()}",
            f"Would move money: {str(result.get('would_move_money', False)).lower()}",
            f"Real action allowed: {str(result.get('real_action_allowed', False)).lower()}",
            f"Message: {result.get('message', '')}",
        ]
        lines.extend(self._judgment_summary_lines(judgment))
        return "\n".join(lines)

    def _format_judgment_list(self, judgments: list[dict]) -> str:
        if not judgments:
            return "Judgment records: none. Use: create judgment record"
        lines = ["Judgment records:"]
        for index, judgment in enumerate(judgments, start=1):
            lines.append(
                f"  {index}. {judgment.get('judgment_id', '')} | "
                f"{judgment.get('risk_level', '')} | "
                f"{judgment.get('recommendation_type', '')} | "
                f"{judgment.get('situation', '')}"
            )
        return "\n".join(lines)

    def _judgment_summary_lines(self, judgment: dict) -> list[str]:
        not_implemented = ", ".join(judgment.get("not_implemented", []))
        return [
            f"Title: {judgment.get('title', '')}",
            f"Situation: {judgment.get('situation', '')}",
            f"Judgment type: {judgment.get('judgment_type', '')}",
            f"Status: {judgment.get('status', 'observed')}",
            f"Risk level: {judgment.get('risk_level', '')}",
            f"Recommendation type: {judgment.get('recommendation_type', '')}",
            f"Summary: {judgment.get('summary', '')}",
            f"Reasoning summary: {judgment.get('reasoning_summary', '')}",
            f"Recommended next step: {judgment.get('recommended_next_step', '')}",
            f"Requires manual review: {str(judgment.get('requires_manual_review', True)).lower()}",
            f"Requires approval: {str(judgment.get('requires_approval', True)).lower()}",
            f"Dry-run only: {str(judgment.get('dry_run_only', True)).lower()}",
            f"Guardian override allowed: {str(judgment.get('guardian_override_allowed', False)).lower()}",
            f"Final decision allowed: {str(judgment.get('final_decision_allowed', False)).lower()}",
            f"Legal/medical/financial final decision allowed: {str(judgment.get('legal_medical_financial_final_decision_allowed', False)).lower()}",
            f"Money movement allowed: {str(judgment.get('money_movement_allowed', False)).lower()}",
            f"Real action allowed: {str(judgment.get('real_action_allowed', False)).lower()}",
            f"Network allowed: {str(judgment.get('network_allowed', False)).lower()}",
            f"API keys allowed: {str(judgment.get('api_keys_allowed', False)).lower()}",
            f"Background monitoring allowed: {str(judgment.get('background_monitoring_allowed', False)).lower()}",
            f"Blocked until: {judgment.get('blocked_until', '')}",
            f"Not implemented: {not_implemented}",
        ]

    def _format_deep_recall_status(self, result: dict) -> str:
        approval = "yes" if result.get("approval_required", True) else "no"
        safe_sources = ", ".join(result.get("safe_sources", []))
        blocked_sources = ", ".join(result.get("blocked_sources", []))
        return "\n".join(
            [
                "Deep recall status:",
                f"Stage: {result.get('stage', '25 deep recall')}",
                "  Deep recall: active",
                f"Recall sessions: {result.get('recall_sessions', 0)}",
                f"Execution mode: {result.get('execution_mode', 'manual_structured_recall_only')}",
                f"Safe sources: {safe_sources}",
                f"Blocked sources: {blocked_sources}",
                f"Raw chat logs: {result.get('raw_chat_logs', 'blocked')}",
                f"Secrets: {result.get('secrets', 'blocked')}",
                f"Whole computer search: {result.get('whole_computer_search', 'blocked')}",
                f"Network access: {result.get('network_access', 'blocked')}",
                f"API/provider keys: {result.get('api_provider_keys', 'blocked')}",
                f"Background monitoring: {result.get('background_monitoring', 'blocked')}",
                f"Real actions: {str(result.get('real_actions', False)).lower()}",
                f"Approval required: {approval}",
                f"Autonomy: {result.get('autonomy', 'not implemented')}",
            ]
        )

    def _format_deep_recall_result(self, result: dict) -> str:
        if not result.get("ok"):
            return f"Deep recall unavailable: {result.get('reason', 'unknown')}"
        recall = result.get("recall", {})
        lines = ["Deep recall session:"]
        if result.get("reused"):
            lines.append("Existing deep recall session reused.")
        lines.extend(self._deep_recall_summary_lines(recall))
        return "\n".join(lines)

    def _format_deep_recall_dry_run(self, result: dict) -> str:
        recall = result.get("recall", {})
        lines = [
            "Deep recall dry run:",
            f"Dry run only: {str(result.get('dry_run_only', True)).lower()}",
            f"Would read raw chat logs: {str(result.get('would_read_raw_chat_logs', False)).lower()}",
            f"Would read secrets: {str(result.get('would_read_secrets', False)).lower()}",
            f"Would search whole computer: {str(result.get('would_search_whole_computer', False)).lower()}",
            f"Would use network: {str(result.get('would_use_network', False)).lower()}",
            f"Would take action: {str(result.get('would_take_action', False)).lower()}",
            f"Real action allowed: {str(result.get('real_action_allowed', False)).lower()}",
            f"Message: {result.get('message', '')}",
        ]
        lines.extend(self._deep_recall_summary_lines(recall))
        return "\n".join(lines)

    def _format_deep_recall_list(self, recalls: list[dict]) -> str:
        if not recalls:
            return "Deep recall sessions: none. Use: create deep recall session"
        lines = ["Deep recall sessions:"]
        for index, recall in enumerate(recalls, start=1):
            lines.append(
                f"  {index}. {recall.get('recall_session_id', '')} | "
                f"{recall.get('status', 'observed')} | "
                f"{recall.get('recall_type', 'safe_structured_records')} | "
                f"{recall.get('query', '')}"
            )
        return "\n".join(lines)

    def _deep_recall_summary_lines(self, recall: dict) -> list[str]:
        safe_sources = ", ".join(recall.get("safe_sources_checked", []))
        blocked_sources = ", ".join(recall.get("blocked_sources", []))
        not_implemented = ", ".join(recall.get("not_implemented", []))
        matches = recall.get("matches", [])
        lines = [
            f"Title: {recall.get('title', '')}",
            f"Query: {recall.get('query', '')}",
            f"Recall type: {recall.get('recall_type', '')}",
            f"Status: {recall.get('status', 'observed')}",
            f"Summary: {recall.get('summary', '')}",
            f"Match count: {recall.get('match_count', 0)}",
            f"Safe sources checked: {safe_sources}",
            f"Blocked sources: {blocked_sources}",
            f"Requires approval: {str(recall.get('requires_approval', True)).lower()}",
            f"Dry-run only: {str(recall.get('dry_run_only', True)).lower()}",
            f"Raw chat logs allowed: {str(recall.get('raw_chat_logs_allowed', False)).lower()}",
            f"Secrets allowed: {str(recall.get('secrets_allowed', False)).lower()}",
            f"Whole computer search allowed: {str(recall.get('whole_computer_search_allowed', False)).lower()}",
            f"Network allowed: {str(recall.get('network_allowed', False)).lower()}",
            f"API keys allowed: {str(recall.get('api_keys_allowed', False)).lower()}",
            f"Background monitoring allowed: {str(recall.get('background_monitoring_allowed', False)).lower()}",
            f"Real action allowed: {str(recall.get('real_action_allowed', False)).lower()}",
            f"Blocked until: {recall.get('blocked_until', '')}",
            f"Not implemented: {not_implemented}",
        ]
        if matches:
            lines.append("Matches:")
            for item in matches[:5]:
                lines.append(
                    f"  - {item.get('source', '')} | {item.get('record_id', '')} | "
                    f"{item.get('title', '')} | {item.get('safe_excerpt', '')}"
                )
        return lines

    def _format_proactive_awareness_status(self, result: dict) -> str:
        approval = "yes" if result.get("approval_required", True) else "no"
        return "\n".join(
            [
                "Proactive awareness status:",
                f"Stage: {result.get('stage', '24 proactive awareness')}",
                f"Proactive awareness: {result.get('proactive_awareness', 'active')}",
                f"Awareness scans: {result.get('awareness_scans', 0)}",
                f"Execution mode: {result.get('execution_mode', 'manual_dry_run_only')}",
                f"Background monitoring: {result.get('background_monitoring', 'blocked')}",
                f"Automatic notifications: {result.get('automatic_notifications', 'blocked')}",
                f"Automatic reminder firing: {result.get('automatic_reminder_firing', 'blocked')}",
                f"Scheduled autonomous checks: {result.get('scheduled_autonomous_checks', 'blocked')}",
                f"Real actions: {str(result.get('real_actions', False)).lower()}",
                f"Approval required: {approval}",
                f"External app bridge execution: {result.get('external_app_bridge_execution', 'blocked')}",
                f"Network access: {result.get('network_access', 'blocked')}",
                f"API/provider keys: {result.get('api_provider_keys', 'blocked')}",
                f"Autonomy: {result.get('autonomy', 'not implemented')}",
            ]
        )

    def _format_awareness_scan_result(self, result: dict) -> str:
        if not result.get("ok"):
            return f"Awareness scan unavailable: {result.get('reason', 'unknown')}"
        scan = result.get("scan", {})
        lines = ["Proactive awareness scan:"]
        if result.get("reused"):
            lines.append("Existing proactive awareness scan reused.")
        lines.extend(self._awareness_scan_summary_lines(scan))
        return "\n".join(lines)

    def _format_awareness_dry_run(self, result: dict) -> str:
        scan = result.get("scan", {})
        lines = [
            "Proactive awareness dry run:",
            f"Dry run only: {str(result.get('dry_run_only', True)).lower()}",
            f"Would monitor background: {str(result.get('would_monitor_background', False)).lower()}",
            f"Would notify: {str(result.get('would_notify', False)).lower()}",
            f"Would take action: {str(result.get('would_take_action', False)).lower()}",
            f"Real action allowed: {str(result.get('real_action_allowed', False)).lower()}",
            f"Message: {result.get('message', '')}",
        ]
        lines.extend(self._awareness_scan_summary_lines(scan))
        return "\n".join(lines)

    def _format_awareness_scan_list(self, scans: list[dict]) -> str:
        if not scans:
            return "Proactive awareness scans: none. Use: create proactive awareness scan"
        lines = ["Proactive awareness scans:"]
        for index, scan in enumerate(scans, start=1):
            lines.append(
                f"  {index}. {scan.get('awareness_scan_id', '')} | "
                f"{scan.get('status', 'observed')} | "
                f"{scan.get('awareness_type', 'manual_state_scan')} | "
                f"{scan.get('title', '')}"
            )
        return "\n".join(lines)

    def _awareness_scan_summary_lines(self, scan: dict) -> list[str]:
        observations = "; ".join(scan.get("observations", []))
        dry_run_plan = "; ".join(scan.get("dry_run_plan", []))
        not_implemented = ", ".join(scan.get("not_implemented", []))
        return [
            f"Title: {scan.get('title', '')}",
            f"Awareness type: {scan.get('awareness_type', '')}",
            f"Status: {scan.get('status', 'observed')}",
            f"Summary: {scan.get('summary', '')}",
            f"Observations: {observations}",
            f"Dry-run plan: {dry_run_plan}",
            f"Requires approval: {str(scan.get('requires_approval', True)).lower()}",
            f"Dry-run only: {str(scan.get('dry_run_only', True)).lower()}",
            f"Background monitoring allowed: {str(scan.get('background_monitoring_allowed', False)).lower()}",
            f"Automatic notifications allowed: {str(scan.get('automatic_notifications_allowed', False)).lower()}",
            f"Automatic reminder firing allowed: {str(scan.get('automatic_reminder_firing_allowed', False)).lower()}",
            f"Scheduled autonomous checks allowed: {str(scan.get('scheduled_autonomous_checks_allowed', False)).lower()}",
            f"Real action allowed: {str(scan.get('real_action_allowed', False)).lower()}",
            f"External bridge execution allowed: {str(scan.get('external_bridge_execution_allowed', False)).lower()}",
            f"Network allowed: {str(scan.get('network_allowed', False)).lower()}",
            f"API keys allowed: {str(scan.get('api_keys_allowed', False)).lower()}",
            f"Blocked until: {scan.get('blocked_until', '')}",
            f"Not implemented: {not_implemented}",
        ]

    def _format_external_app_bridge_status(self, result: dict) -> str:
        approval = "yes" if result.get("approval_required", True) else "no"
        return "\n".join(
            [
                "External app bridge status:",
                f"Stage: {result.get('stage', '23 external app bridge')}",
                f"External app bridge: {result.get('external_app_bridge', 'active')}",
                f"Bridge proposals: {result.get('bridge_proposals', 0)}",
                f"Execution mode: {result.get('execution_mode', 'dry_run_only')}",
                f"Real connection: {str(result.get('real_connection', False)).lower()}",
                f"Approval required: {approval}",
                f"WhatsApp control: {result.get('whatsapp_control', 'blocked')}",
                f"Instagram control: {result.get('instagram_control', 'blocked')}",
                f"Chrome control: {result.get('chrome_control', 'blocked')}",
                f"Browser automation: {result.get('browser_automation', 'blocked')}",
                f"Phone control: {result.get('phone_control', 'blocked')}",
                f"App reading: {result.get('app_reading', 'blocked')}",
                f"Message sending: {result.get('message_sending', 'blocked')}",
                f"Network server: {result.get('network_server', 'blocked')}",
                f"API/provider keys: {result.get('api_provider_keys', 'blocked')}",
                f"Background monitoring: {result.get('background_monitoring', 'blocked')}",
                f"Proactive awareness: {result.get('proactive_awareness', 'not implemented')}",
                f"Autonomy: {result.get('autonomy', 'not implemented')}",
            ]
        )

    def _format_external_bridge_result(self, result: dict) -> str:
        if not result.get("ok"):
            return f"External app bridge proposal unavailable: {result.get('reason', 'unknown')}"
        bridge = result.get("bridge", {})
        lines = ["External app bridge proposal:"]
        if result.get("reused"):
            lines.append("Existing external app bridge proposal reused.")
        lines.extend(self._external_bridge_summary_lines(bridge))
        return "\n".join(lines)

    def _format_external_bridge_dry_run(self, result: dict) -> str:
        bridge = result.get("bridge", {})
        lines = [
            "External app bridge dry run:",
            f"Dry run only: {str(result.get('dry_run_only', True)).lower()}",
            f"Would connect: {str(result.get('would_connect', False)).lower()}",
            f"Real connection allowed: {str(result.get('real_connection_allowed', False)).lower()}",
            f"Message: {result.get('message', '')}",
        ]
        lines.extend(self._external_bridge_summary_lines(bridge))
        return "\n".join(lines)

    def _format_external_bridge_list(self, bridges: list[dict]) -> str:
        if not bridges:
            return "External app bridge proposals: none. Use: create external app bridge proposal"
        lines = ["External app bridge proposals:"]
        for index, bridge in enumerate(bridges, start=1):
            lines.append(
                f"  {index}. {bridge.get('bridge_id', '')} | "
                f"{bridge.get('status', 'proposed')} | "
                f"{bridge.get('bridge_type', 'permission_gate_plan')} | "
                f"{bridge.get('title', '')}"
            )
        return "\n".join(lines)

    def _external_bridge_summary_lines(self, bridge: dict) -> list[str]:
        not_implemented = ", ".join(bridge.get("not_implemented", []))
        dry_run_plan = "; ".join(bridge.get("dry_run_plan", []))
        return [
            f"Title: {bridge.get('title', '')}",
            f"Bridge type: {bridge.get('bridge_type', '')}",
            f"Status: {bridge.get('status', 'proposed')}",
            f"Summary: {bridge.get('summary', '')}",
            f"Dry-run plan: {dry_run_plan}",
            f"Requires approval: {str(bridge.get('requires_approval', True)).lower()}",
            f"Dry-run only: {str(bridge.get('dry_run_only', True)).lower()}",
            f"Real connection allowed: {str(bridge.get('real_connection_allowed', False)).lower()}",
            f"WhatsApp allowed: {str(bridge.get('whatsapp_allowed', False)).lower()}",
            f"Instagram allowed: {str(bridge.get('instagram_allowed', False)).lower()}",
            f"Chrome allowed: {str(bridge.get('chrome_allowed', False)).lower()}",
            f"Browser automation allowed: {str(bridge.get('browser_automation_allowed', False)).lower()}",
            f"Phone control allowed: {str(bridge.get('phone_control_allowed', False)).lower()}",
            f"App reading allowed: {str(bridge.get('app_reading_allowed', False)).lower()}",
            f"Message sending allowed: {str(bridge.get('message_sending_allowed', False)).lower()}",
            f"Network server allowed: {str(bridge.get('network_server_allowed', False)).lower()}",
            f"API keys allowed: {str(bridge.get('api_keys_allowed', False)).lower()}",
            f"Background monitoring allowed: {str(bridge.get('background_monitoring_allowed', False)).lower()}",
            f"Blocked until: {bridge.get('blocked_until', '')}",
            f"Not implemented: {not_implemented}",
        ]

    def _format_safe_local_actions_status(self, result: dict) -> str:
        approval = "yes" if result.get("approval_required", True) else "no"
        return "\n".join(
            [
                "Safe local actions status:",
                f"Stage: {result.get('stage', '22 safe local actions')}",
                f"Safe local actions: {result.get('safe_local_actions', 'active')}",
                f"Action proposals: {result.get('action_proposals', 0)}",
                f"Execution mode: {result.get('execution_mode', 'dry_run_only')}",
                f"Real execution: {str(result.get('real_execution', False)).lower()}",
                f"Approval required: {approval}",
                f"Shell execution: {result.get('shell_execution', 'blocked')}",
                f"File deletion: {result.get('file_deletion', 'blocked')}",
                f"File moving: {result.get('file_moving', 'blocked')}",
                f"File editing: {result.get('file_editing', 'blocked')}",
                f"App opening: {result.get('app_opening', 'blocked')}",
                f"Network access: {result.get('network_access', 'blocked')}",
                f"Background automation: {result.get('background_automation', 'blocked')}",
                f"External app bridge: {result.get('external_app_bridge', 'not implemented')}",
                f"Proactive monitoring: {result.get('proactive_monitoring', 'not implemented')}",
                f"Autonomy: {result.get('autonomy', 'not implemented')}",
            ]
        )

    def _format_safe_action_result(self, result: dict) -> str:
        if not result.get("ok"):
            return f"Safe action proposal unavailable: {result.get('reason', 'unknown')}"
        action = result.get("action", {})
        lines = ["Safe action proposal:"]
        if result.get("reused"):
            lines.append("Existing safe action proposal reused.")
        lines.extend(self._safe_action_summary_lines(action))
        return "\n".join(lines)

    def _format_safe_action_dry_run(self, result: dict) -> str:
        action = result.get("action", {})
        lines = [
            "Safe action dry run:",
            f"Dry run only: {str(result.get('dry_run_only', True)).lower()}",
            f"Would execute: {str(result.get('would_execute', False)).lower()}",
            f"Real execution allowed: {str(result.get('real_execution_allowed', False)).lower()}",
            f"Message: {result.get('message', '')}",
        ]
        lines.extend(self._safe_action_summary_lines(action))
        return "\n".join(lines)

    def _format_safe_action_list(self, actions: list[dict]) -> str:
        if not actions:
            return "Safe action proposals: none. Use: create safe action proposal"
        lines = ["Safe action proposals:"]
        for index, action in enumerate(actions, start=1):
            lines.append(
                f"  {index}. {action.get('safe_action_id', '')} | "
                f"{action.get('status', 'proposed')} | "
                f"{action.get('action_type', 'prepare_manual_checklist')} | "
                f"{action.get('title', '')}"
            )
        return "\n".join(lines)

    def _safe_action_summary_lines(self, action: dict) -> list[str]:
        not_implemented = ", ".join(action.get("not_implemented", []))
        dry_run_plan = "; ".join(action.get("dry_run_plan", []))
        return [
            f"Title: {action.get('title', '')}",
            f"Action type: {action.get('action_type', '')}",
            f"Status: {action.get('status', 'proposed')}",
            f"Summary: {action.get('summary', '')}",
            f"Dry-run plan: {dry_run_plan}",
            f"Requires approval: {str(action.get('requires_approval', True)).lower()}",
            f"Dry-run only: {str(action.get('dry_run_only', True)).lower()}",
            f"Real execution allowed: {str(action.get('real_execution_allowed', False)).lower()}",
            f"Shell execution allowed: {str(action.get('shell_execution_allowed', False)).lower()}",
            f"File delete allowed: {str(action.get('file_delete_allowed', False)).lower()}",
            f"File move allowed: {str(action.get('file_move_allowed', False)).lower()}",
            f"File edit allowed: {str(action.get('file_edit_allowed', False)).lower()}",
            f"App open allowed: {str(action.get('app_open_allowed', False)).lower()}",
            f"Network allowed: {str(action.get('network_allowed', False)).lower()}",
            f"Background allowed: {str(action.get('background_allowed', False)).lower()}",
            f"Blocked until: {action.get('blocked_until', '')}",
            f"Not implemented: {not_implemented}",
        ]

    def _format_smart_organizer_status(self, result: dict) -> str:
        approval = "yes" if result.get("approval_required_for_action", True) else "no"
        return "\n".join(
            [
                "Smart organizer status:",
                f"Stage: {result.get('stage', '21 smart organizer')}",
                f"Smart organizer: {result.get('smart_organizer', 'active')}",
                f"Organizer items: {result.get('organizer_items', 0)}",
                f"Takes actions: {str(result.get('takes_actions', False)).lower()}",
                f"Proactive monitoring: {result.get('proactive_monitoring', 'not implemented')}",
                f"Safe local actions: {result.get('safe_local_actions', 'not implemented')}",
                f"External app bridge: {result.get('external_app_bridge', 'not implemented')}",
                "  Deep recall: active",
                f"Autonomy: {result.get('autonomy', 'not implemented')}",
                f"Approval required for action: {approval}",
            ]
        )

    def _format_organizer_item_result(self, result: dict) -> str:
        if not result.get("ok"):
            return f"Organizer item unavailable: {result.get('reason', 'unknown')}"
        item = result.get("item", {})
        lines = ["Organizer item:"]
        if result.get("reused"):
            lines.append("Existing organizer item reused.")
        lines.extend(self._organizer_item_summary_lines(item))
        return "\n".join(lines)

    def _format_organizer_items_list(self, items: list[dict]) -> str:
        if not items:
            return "Organizer items: none. Use: create organizer item"
        lines = ["Organizer items:"]
        for index, item in enumerate(items, start=1):
            lines.append(
                f"  {index}. {item.get('organizer_item_id', '')} | "
                f"{item.get('status', 'open')} | "
                f"{item.get('group', 'current_stage')} | "
                f"{item.get('title', '')}"
            )
        return "\n".join(lines)

    def _organizer_item_summary_lines(self, item: dict) -> list[str]:
        not_implemented = ", ".join(item.get("not_implemented", []))
        notes = "; ".join(item.get("safety_notes", []))
        return [
            f"Title: {item.get('title', '')}",
            f"Group: {item.get('group', 'current_stage')}",
            f"Status: {item.get('status', 'open')}",
            f"Priority: {item.get('priority', 'medium')}",
            f"Summary: {item.get('summary', '')}",
            f"Next visible step: {item.get('next_visible_step', '')}",
            f"Blocked until: {item.get('blocked_until', '')}",
            f"Approval required: {str(item.get('approval_required', True)).lower()}",
            f"Action allowed: {str(item.get('action_allowed', False)).lower()}",
            f"Proactive allowed: {str(item.get('proactive_allowed', False)).lower()}",
            f"Safety notes: {notes}",
            f"Not implemented: {not_implemented}",
        ]

    def _format_long_term_strategy_status(self, result: dict) -> str:
        approval = "yes" if result.get("approval_required_for_strategy_changes", True) else "no"
        return "\n".join(
            [
                "Long-term strategy status:",
                f"Stage: {result.get('stage', '20 long-term strategy')}",
                f"Long-term strategy: {result.get('long_term_strategy', 'active')}",
                f"Strategy records: {result.get('strategy_records', 0)}",
                f"Autonomy: {result.get('autonomy', 'not implemented')}",
                f"Smart organizer: {result.get('smart_organizer', 'not implemented')}",
                f"Safe local actions: {result.get('safe_local_actions', 'not implemented')}",
                f"External app bridge: {result.get('external_app_bridge', 'not implemented')}",
                f"Proactive awareness: {result.get('proactive_awareness', 'not implemented')}",
                "  Deep recall: active",
                f"Approval required for strategy changes: {approval}",
            ]
        )

    def _format_long_term_strategy_result(self, result: dict) -> str:
        if not result.get("ok"):
            return f"Long-term strategy unavailable: {result.get('reason', 'unknown')}"
        strategy = result.get("strategy", {})
        lines = ["Long-term strategy:"]
        if result.get("reused"):
            lines.append("Existing long-term strategy reused.")
        lines.extend(self._long_term_strategy_summary_lines(strategy))
        return "\n".join(lines)

    def _format_long_term_strategies_list(self, strategies: list[dict]) -> str:
        if not strategies:
            return "Long-term strategies: none. Use: create long-term strategy"
        lines = ["Long-term strategies:"]
        for index, strategy in enumerate(strategies, start=1):
            lines.append(
                f"  {index}. {strategy.get('strategy_id', '')} | "
                f"{strategy.get('status', 'draft')} | "
                f"{strategy.get('horizon', 'long')} | "
                f"{strategy.get('title', '')}"
            )
        return "\n".join(lines)

    def _long_term_strategy_summary_lines(self, strategy: dict) -> list[str]:
        blocked = strategy.get("blocked_reasons", [])
        blocked_text = ", ".join(blocked) if blocked else "none"
        not_implemented = ", ".join(strategy.get("not_implemented", []))
        return [
            f"Title: {strategy.get('title', '')}",
            f"Horizon: {strategy.get('horizon', 'long')}",
            f"Status: {strategy.get('status', 'draft')}",
            f"Summary: {strategy.get('summary', '')}",
            f"Near-term focus: {strategy.get('near_term_focus', '')}",
            f"Future direction: {strategy.get('future_direction', '')}",
            f"Risk level: {strategy.get('risk_level', 'low')}",
            f"Approval required: {str(strategy.get('approval_required', True)).lower()}",
            f"Autonomy allowed: {str(strategy.get('autonomy_allowed', False)).lower()}",
            f"Implementation allowed: {str(strategy.get('implementation_allowed', False)).lower()}",
            f"Blocked reasons: {blocked_text}",
            f"Not implemented: {not_implemented}",
        ]

    def _format_identity_stability_status(self, result: dict) -> str:
        approval = "yes" if result.get("approval_required_for_identity_changes", True) else "no"
        return "\n".join(
            [
                "Identity stability status:",
                f"Stage: {result.get('stage', '19 identity stability')}",
                f"Identity stability: {result.get('identity_stability', 'active')}",
                f"Identity checks: {result.get('identity_checks', 0)}",
                f"Stable identity: {result.get('stable_identity', 'local-first assistant system under Lucy project')}",
                f"Fake consciousness claims: {result.get('fake_consciousness_claims', 'blocked')}",
                f"Provider/API identity: {result.get('provider_api_identity', 'blocked')}",
                f"Self-modification without approval: {result.get('self_modification_without_approval', 'blocked')}",
                f"Long-term strategy: {result.get('long_term_strategy', 'not implemented')}",
                "  Deep recall: active",
                f"Adaptive communication: {result.get('adaptive_communication', 'not implemented')}",
                f"Approval required for identity changes: {approval}",
            ]
        )

    def _format_identity_check_result(self, result: dict) -> str:
        if not result.get("ok"):
            return f"Identity stability check unavailable: {result.get('reason', 'unknown')}"
        check = result.get("identity_check", {})
        lines = ["Identity stability check:"]
        if result.get("reused"):
            lines.append("Existing identity stability check reused.")
        lines.extend(self._identity_check_summary_lines(check))
        return "\n".join(lines)

    def _format_identity_checks_list(self, checks: list[dict]) -> str:
        if not checks:
            return "Identity checks: none. Use: check identity stability"
        lines = ["Identity checks:"]
        for index, check in enumerate(checks, start=1):
            lines.append(
                f"  {index}. {check.get('identity_check_id', '')} | "
                f"{check.get('result', 'needs_review')} | "
                f"{check.get('drift_risk', 'medium')} | "
                f"{check.get('title', '')}"
            )
        return "\n".join(lines)

    def _identity_check_summary_lines(self, check: dict) -> list[str]:
        blocked = check.get("blocked_reasons", [])
        blocked_text = ", ".join(blocked) if blocked else "none"
        not_implemented = ", ".join(check.get("not_implemented", []))
        return [
            f"Title: {check.get('title', '')}",
            f"Result: {check.get('result', 'needs_review')}",
            f"Drift risk: {check.get('drift_risk', 'medium')}",
            f"Approved for identity: {str(check.get('approved_for_identity', False)).lower()}",
            f"Blocked reasons: {blocked_text}",
            f"Stable identity summary: {check.get('stable_identity_summary', '')}",
            f"Not implemented: {not_implemented}",
        ]

    def _format_internal_agent_single_status(self, result: dict) -> str:
        return "\n".join(
            [
                f"{result.get('agent_id', 'Agent')}: {result.get('status', 'unknown')}.",
                f"Summary: {result.get('summary', '')}",
                "Stage: 09 agent disagreement safety.",
            ]
        )

    def _format_internal_agent_report(self, result: dict) -> str:
        lines = [
            "Internal agent report:",
            f"  Cycle: {result.get('cycle_id', '')}",
            f"  Stage: {result.get('active_stage', '08')} {result.get('stage_label', 'internal agents')}",
            f"  Overall: {result.get('overall_status', 'unknown')}",
            f"  MemoryAgent: {result.get('memory_summary', '')}",
            f"  SafetyAgent: {result.get('safety_summary', '')}",
            f"  ReasoningAgent: {result.get('reasoning_summary', '')}",
            f"  LearningAgent: {result.get('learning_summary', '')}",
            f"  Final: {result.get('final_summary', '')}",
        ]
        return "\n".join(lines)

    def _format_agent(self, agent_id: str) -> str:
        agent = self.runtime.agents.get_agent(agent_id)
        if agent is None:
            return f"Agent '{agent_id}' not found in registry."
        return "\n".join(
            [
                f"Agent: {agent['id']}",
                f"  Full form: {agent.get('full_form', 'N/A')}",
                f"  Status: {agent.get('status', 'unknown')}",
                f"  Active: {agent.get('active', False)}",
                f"  Role: {agent.get('role', 'N/A')}",
                f"  Can run: {agent.get('can_run', False)}",
                f"  Can modify files: {agent.get('can_modify_files', False)}",
                f"  Can access API keys: {agent.get('can_access_api_keys', False)}",
                f"  Can move money: {agent.get('can_move_money', False)}",
                f"  Requires Lucy OK: {agent.get('requires_lucy_approval', True)}",
            ]
        )

    def _format_boundary(self, result) -> str:
        lines = [f"Result: {result.status}", f"Reason: {result.reason}"]
        if result.status == "safe":
            lines.append("Action: No system action required.")
        else:
            lines.append("Action: No action executed.")
        return "\n".join(lines)

    def _format_remember(self, result: dict) -> str:
        if result.get("saved"):
            memory = result["memory"]
            return f"Remembered [{memory['id']}]: {memory['fact']}"
        if result.get("duplicate"):
            memory = result["memory"]
            return f"I already had that memory [{memory['id']}]."
        return f"Memory not saved: {result.get('reason', 'unknown reason')}"

    def _format_recall(self, memories: list[dict]) -> str:
        if not memories:
            return "No matching memory found."
        lines = ["Memory recall:"]
        lines.extend(f"  - [{item['id']}] {item['fact']}" for item in memories)
        return "\n".join(lines)

    def _format_forget(self, result: dict) -> str:
        count = result.get("forgotten", 0)
        if count:
            return f"Forgot {count} memory record(s): {', '.join(result.get('ids', []))}"
        return f"Nothing forgotten: {result.get('reason', 'no matching memory')}"

    def _format_memory_audit(self, audit: dict) -> str:
        categories = ", ".join(f"{key}={value}" for key, value in sorted(audit["categories"].items()))
        return "\n".join(
            [
                "Memory audit:",
                f"  Mode: {audit['mode']}",
                f"  Active: {audit['active']}",
                f"  Deleted: {audit['deleted']}",
                f"  Duplicates: {audit['duplicates']}",
                f"  Categories: {categories or 'none'}",
                f"  File: {audit['file']}",
            ]
        )

    def _format_permanent_memory_status(self, audit: dict) -> str:
        return "\n".join(
            [
                "Permanent memory:",
                f"  Active facts: {audit['active']}",
                f"  Deleted facts: {audit['deleted']}",
                f"  Mode: {audit['mode']}",
                f"  File: {audit['file']}",
                "  Save with: remember <fact>",
                "  Recall with: recall [keyword]",
            ]
        )

    def _format_tool_policy(self, result: dict) -> str:
        data = result.get("data", {})
        limits = data.get("limits", {})
        safe_tools = data.get("safe_tools", {})
        lines = [
            "Tool policy:",
            f"  Approved folders: {safe_tools.get('approved_folder_count', 0)}",
            f"  Safe reads: {safe_tools.get('safe_read_enabled', True)}",
            f"  Writes enabled: {safe_tools.get('write_enabled', False)}",
            f"  Network enabled: {safe_tools.get('network_enabled', False)}",
            f"  Execution enabled: {safe_tools.get('execution_enabled', False)}",
            f"  Large read confirmation: {safe_tools.get('confirmation_required_for_large_reads', True)}",
            f"  Max safe read bytes: {limits.get('max_safe_read_bytes')}",
            f"  Max search results: {limits.get('max_safe_search_results')}",
            "  Blocked: write/delete/execute/network/secrets/money/identity-memory actions.",
        ]
        return "\n".join(lines)

    def _format_tool_audit(self, result: dict) -> str:
        if not result.get("ok"):
            return f"Tool audit unavailable: {result.get('reason') or 'unknown'}"
        entries = result.get("entries", [])
        lines = [
            "Tool audit:",
            f"  File: {result.get('file')}",
            f"  Entries shown: {len(entries)}",
        ]
        for item in entries[-20:]:
            lines.append(
                "  - "
                f"{item.get('timestamp')} | {item.get('result')} | {item.get('action_name')} | "
                f"{item.get('policy_category') or 'uncategorized'} | confirmation={item.get('confirmation_id') or 'none'}"
            )
        return "\n".join(lines)

    def _format_pending_confirmations(self, result: dict) -> str:
        confirmations = result.get("confirmations", [])
        if not confirmations:
            return "Pending tool confirmations: none."
        lines = ["Pending tool confirmations:"]
        for item in confirmations:
            lines.append(
                f"  - {item.get('id')} | {item.get('risk_level')} | {item.get('action')} | "
                f"{item.get('reason')} | target={item.get('target_path') or 'none'}"
            )
        return "\n".join(lines)

    def _format_tool_confirmation_result(self, result: dict) -> str:
        if not result.get("ok"):
            return f"Tool confirmation failed: {result.get('reason') or 'unknown'}"
        confirmation = result.get("confirmation", {})
        lines = [
            "Tool confirmation updated:",
            f"  ID: {confirmation.get('id')}",
            f"  Status: {confirmation.get('status')}",
            f"  Action: {confirmation.get('action')}",
        ]
        execution = result.get("execution_result")
        if isinstance(execution, dict):
            lines.append(f"  Applied result: {execution.get('message') or execution.get('reason') or execution.get('result')}")
        return "\n".join(lines)

    def _format_safe_tool_result(self, result: dict) -> str:
        data = result.get("data") if isinstance(result.get("data"), dict) else {}
        if data.get("requires_confirmation"):
            return "\n".join(
                [
                    "Tool action requires manual confirmation:",
                    f"  Reason: {result.get('reason') or 'manual confirmation required'}",
                    f"  Confirmation ID: {data.get('confirmation_id') or 'pending'}",
                    f"  Path: {result.get('path') or 'not provided'}",
                    "  Use: pending confirmations",
                    "  Then: approve tool <id> or reject tool <id>",
                ]
            )

        if not result.get("ok"):
            return "\n".join(
                [
                    f"Safe file tool refused: {result.get('message', 'request refused')}",
                    f"  Reason: {result.get('reason') or 'unknown'}",
                    f"  Path: {result.get('path') or 'not provided'}",
                ]
            )

        action = result.get("action", "")
        data = result.get("data")
        if action == "status":
            return "\n".join(
                [
                    "Safe file tools:",
                    f"  Mode: read-only approved folders",
                    f"  Enabled folders: {data.get('enabled_folders', 0)}",
                    f"  Registry: {data.get('registry_file', '')}",
                    f"  Log: {data.get('log_file', '')}",
                    f"  Audit: {data.get('audit_log_file', '')}",
                    f"  Allowed extensions: {', '.join(data.get('allowed_extensions', []))}",
                    "  No edit, delete, upload, execute, daemon, watcher, or network behavior.",
                ]
            )
        if action == "list_approved_folders":
            folders = data or []
            if not folders:
                return "Approved folders: none. Use: approve folder <path>"
            lines = ["Approved folders:"]
            for item in folders:
                enabled = "enabled" if item.get("enabled") else "disabled"
                lines.append(f"  - {item.get('id')}: {item.get('name')} [{enabled}] {item.get('path')}")
            return "\n".join(lines)
        if action == "add_approved_folder":
            return "\n".join(
                [
                    "Approved folder added:",
                    f"  ID: {data.get('id')}",
                    f"  Name: {data.get('name')}",
                    f"  Path: {data.get('path')}",
                    f"  Access: {data.get('access')}",
                ]
            )
        if action == "remove_approved_folder":
            return f"Approved folder removed: {data.get('removed')}"
        if action == "summarize_tree":
            files = data.get("files", [])
            lines = [
                "Workspace tree:",
                f"  Safe files shown: {len(files)}",
                f"  Skipped unsafe/blocked: {data.get('skipped', 0)}",
            ]
            for item in files[:80]:
                lines.append(f"  - [{item.get('folder_id')}] {item.get('path')} ({item.get('size')} bytes)")
            if len(files) > 80:
                lines.append("  ... more files not shown")
            return "\n".join(lines)
        if action == "read_text_file":
            metadata = data.get("metadata", {})
            lines = [
                "Safe file read:",
                f"  File: {metadata.get('relative_path') or result.get('path')}",
                f"  Characters shown: {data.get('chars', 0)}",
            ]
            if data.get("truncated"):
                lines.append("  Note: output truncated.")
            lines.append("")
            lines.append(data.get("text", ""))
            return "\n".join(lines)
        if action == "search_text":
            matches = data.get("matches", [])
            lines = [
                f"Safe file search: {data.get('query')!r}",
                f"  Matches: {len(matches)}",
                f"  Skipped unsafe/large: {data.get('skipped', 0)}",
            ]
            for item in matches[:50]:
                lines.append(f"  - [{item.get('folder_id')}] {item.get('path')}:{item.get('line')} {item.get('text')}")
            return "\n".join(lines)
        if action == "file_metadata":
            return "\n".join(
                [
                    "Safe file metadata:",
                    f"  Folder: {data.get('folder_id')}",
                    f"  Name: {data.get('name')}",
                    f"  Path: {data.get('relative_path')}",
                    f"  Size: {data.get('size')} bytes",
                    f"  Extension: {data.get('extension')}",
                    f"  Modified: {data.get('modified_at')}",
                ]
            )
        return f"{result.get('message', 'Safe file tool completed.')}"

    def _format_workspace(self, tree: dict) -> str:
        lines = [
            "Workspace:",
            f"  Root: {tree['root']}",
            f"  Files shown: {tree['shown']} / {tree['total']}",
        ]
        for item in tree["files"][:80]:
            lines.append(f"  - {item['path']} ({item['size']} bytes)")
        if tree["shown"] < tree["total"]:
            lines.append("  ... more files not shown")
        return "\n".join(lines)

    def _format_find_files(self, result: dict) -> str:
        if result.get("reason"):
            return f"File search failed: {result['reason']}"
        matches = result.get("matches", [])
        if not matches:
            return "No matching files found."
        lines = [f"File matches for {result['query']!r}:"]
        lines.extend(f"  - {match}" for match in matches)
        return "\n".join(lines)

    def _format_text_search(self, result: dict) -> str:
        if result.get("reason"):
            return f"Text search failed: {result['reason']}"
        matches = result.get("matches", [])
        if not matches:
            return "No matching text found."
        lines = [f"Text matches for {result['query']!r}:"]
        for item in matches:
            lines.append(f"  - {item['path']}:{item['line']} {item['text']}")
        return "\n".join(lines)

    def _format_read_file(self, result: dict) -> str:
        if not result.get("read"):
            return f"File not read: {result.get('reason', 'unknown reason')}"
        lines = [
            f"File: {result['path']}",
            f"Characters shown: {result['chars']}",
        ]
        if result.get("truncated"):
            lines.append("Note: output truncated.")
        lines.append("")
        lines.append(result["text"])
        return "\n".join(lines)

    def _format_system(self, snapshot: dict) -> str:
        return "\n".join(
            [
                "System snapshot:",
                f"  Platform: {snapshot['platform']}",
                f"  Machine: {snapshot['machine']}",
                f"  Python: {snapshot['python_version']}",
                f"  Python executable: {snapshot['python_executable']}",
                f"  Project root: {snapshot['project_root']}",
                f"  CWD: {snapshot['cwd']}",
                f"  Disk total: {snapshot['disk_total_gb']} GB",
                f"  Disk free: {snapshot['disk_free_gb']} GB",
            ]
        )

    def _format_logs(self, logs: list[dict]) -> str:
        if not logs:
            return "No runtime logs found."
        lines = ["Recent runtime logs:"]
        for item in logs:
            if "raw" in item:
                lines.append(f"  - {item['raw']}")
                continue
            lines.append(
                f"  - {item.get('timestamp', '')} "
                f"{item.get('event_type', 'unknown')} "
                f"[{item.get('source', 'unknown')}] {item.get('message', '')}"
            )
        return "\n".join(lines)

    def _format_projects(self, projects: list[dict]) -> str:
        if not projects:
            return "No projects tracked yet."
        lines = ["Projects:"]
        for project in projects:
            marker = "*" if project["active"] else "-"
            lines.append(
                f"  {marker} {project['name']}: {project['status']} "
                f"({project['open_tasks']} open, {project['done_tasks']} done)"
            )
        return "\n".join(lines)

    def _format_set_project(self, result: dict) -> str:
        if not result.get("changed"):
            return f"Active project unchanged: {result.get('reason', 'unknown reason')}"
        return f"Active project set to {result['project']['name']}."

    def _format_add_task(self, result: dict) -> str:
        if not result.get("added"):
            return f"Task not added: {result.get('reason', 'unknown reason')}"
        task = result["task"]
        return f"Added task to {result['project']} [{task['id']}]: {task['text']}"

    def _format_complete_task(self, result: dict) -> str:
        if not result.get("completed"):
            return f"Task not completed: {result.get('reason', 'unknown reason')}"
        task = result["task"]
        return f"Completed task in {result['project']} [{task['id']}]: {task['text']}"

    def _format_tasks(self, result: dict) -> str:
        tasks = result.get("tasks", [])
        if not tasks:
            return f"No matching tasks for {result['project']}."
        lines = [f"Tasks for {result['project']}:"]
        for index, task in enumerate(tasks, start=1):
            lines.append(f"  {index}. [{task['status']}] {task['id']} - {task['text']}")
        return "\n".join(lines)

    def _format_project_summary(self, summary: dict) -> str:
        lines = [
            f"Project: {summary['name']}",
            f"Status: {summary['status']}",
            f"Summary: {summary['summary'] or 'No summary yet.'}",
            f"Next action: {summary['next_action'] or 'Not set.'}",
            f"Open tasks: {len(summary['open_tasks'])}",
            f"Completed tasks: {len(summary['done_tasks'])}",
            f"Checkpoints: {len(summary['checkpoints'])}",
        ]
        for index, task in enumerate(summary["open_tasks"][:5], start=1):
            lines.append(f"  {index}. {task['text']}")
        return "\n".join(lines)

    def _format_daily_brief(self, brief: dict) -> str:
        daily = brief.get("daily_context", {})
        lines = [
            "Daily brief:",
            f"  Active project: {brief['active_project']}",
            f"  Status: {brief['status']}",
            f"  Next action: {brief['next_action'] or 'Not set.'}",
            f"  Today log: {'present' if daily.get('has_today_log') else 'not started'}",
            f"  Energy: {daily.get('energy') if daily.get('energy') is not None else 'not set'}",
            f"  Sleep: {daily.get('sleep_status') or 'not set'}",
            f"  Tomorrow priority: {daily.get('tomorrow_priority') or 'not set'}",
            f"  Projects tracked: {brief['project_count']}",
            f"  Active memories: {brief['memory']['active']}",
            f"  Open reminders: {len(brief['open_reminders'])}",
            f"  Due reminders: {len(brief['due_reminders'])}",
            f"  Pending approvals: {brief['pending_approvals']}",
            "  Top tasks:",
        ]
        if brief["top_tasks"]:
            for index, task in enumerate(brief["top_tasks"], start=1):
                lines.append(f"    {index}. {task['text']}")
        else:
            lines.append("    No open tasks.")
        return "\n".join(lines)

    def _format_daily_checkin(self, result: dict) -> str:
        lines = [
            f"Daily check-in saved for {result['date']}.",
            f"  Fields updated: {', '.join(result.get('fields_updated', [])) or 'baseline entry'}",
            f"  Redacted inputs: {result.get('redacted_count', 0)}",
            f"  File: {result.get('file', '')}",
        ]
        lines.extend(self._daily_entry_lines(result.get("entry", {})))
        return "\n".join(lines)

    def _format_daily_log(self, result: dict, title: str) -> str:
        if not result.get("found"):
            return (
                f"{title}: no entry for {result.get('date', 'unknown date')}.\n"
                "Run: daily checkin energy=6 sleep=ok notes=\"what changed today\""
            )
        lines = [f"{title}: {result['date']}"]
        lines.extend(self._daily_entry_lines(result.get("entry", {})))
        return "\n".join(lines)

    def _format_weekly_review(self, review: dict) -> str:
        lines = [
            f"Weekly review: {review['start_date']} to {review['end_date']}",
            f"  Days logged: {review['days_found']} / {review['days_checked']}",
            f"  Tasks completed: {len(review['tasks_completed'])}",
            f"  Tasks avoided: {len(review['tasks_avoided'])}",
            f"  Promises made: {len(review['promises_made'])}",
            f"  People to message: {len(review['people_to_message'])}",
            f"  Anti-drift: {review['anti_drift_reminder']}",
        ]
        if review["tasks_completed"]:
            lines.append("  Completed:")
            for item in review["tasks_completed"][:6]:
                lines.append(f"    - {item}")
        if review["lessons_learned"]:
            lines.append("  Lessons:")
            for item in review["lessons_learned"][:4]:
                lines.append(f"    - {item}")
        if review["tomorrow_priorities"]:
            lines.append("  Recent priorities:")
            for item in review["tomorrow_priorities"]:
                lines.append(f"    - {item}")
        return "\n".join(lines)

    def _daily_entry_lines(self, entry: dict) -> list[str]:
        def joined(items: list[str]) -> str:
            return ", ".join(items) if items else "none"

        return [
            f"  Energy: {entry.get('energy') if entry.get('energy') is not None else 'not set'}",
            f"  Sleep: {entry.get('sleep_status') or 'not set'}",
            f"  Main project: {entry.get('main_project_today') or 'not set'}",
            f"  Completed: {joined(entry.get('tasks_completed', []))}",
            f"  Avoided: {joined(entry.get('tasks_avoided', []))}",
            f"  Money pressure: {entry.get('money_pressure') or 'not set'}",
            f"  Routine: {entry.get('routine_status') or 'not set'}",
            f"  Health/gym: {entry.get('health_gym_status') or 'not set'}",
            f"  Promises: {joined(entry.get('promises_made', []))}",
            f"  People to message: {joined(entry.get('people_to_message', []))}",
            f"  Important events: {joined(entry.get('important_events', []))}",
            f"  What changed: {entry.get('what_changed_today') or 'not set'}",
            f"  Tomorrow priority: {entry.get('tomorrow_priority') or 'not set'}",
            f"  Lesson: {entry.get('lesson_learned') or 'not set'}",
            f"  Notes: {entry.get('notes') or 'not set'}",
        ]

    def _format_add_reminder(self, result: dict) -> str:
        if not result.get("added"):
            return f"Reminder not added: {result.get('reason', 'unknown reason')}"
        reminder = result["reminder"]
        due = f" due {reminder['due']}" if reminder.get("due") else ""
        return f"Added reminder [{reminder['id']}]: {reminder['text']}{due}"

    def _format_reminders(self, reminders: list[dict]) -> str:
        if not reminders:
            return "No open reminders."
        lines = ["Open reminders:"]
        for index, reminder in enumerate(reminders, start=1):
            due = f" due {reminder['due']}" if reminder.get("due") else ""
            lines.append(f"  {index}. [{reminder['id']}] {reminder['text']}{due}")
        return "\n".join(lines)

    def _format_complete_reminder(self, result: dict) -> str:
        if not result.get("completed"):
            return f"Reminder not completed: {result.get('reason', 'unknown reason')}"
        reminder = result["reminder"]
        return f"Completed reminder [{reminder['id']}]: {reminder['text']}"

    def _format_plan(self, goal: str) -> str:
        if not goal:
            return "Give me a goal to plan."
        project = self.runtime.project_summary()
        return "\n".join(
            [
                f"Plan for: {goal}",
                f"Active project: {project['name']}",
                "1. Clarify the smallest useful outcome.",
                "2. Check Guardian risk before any file, command, account, or automation action.",
                "3. Break the work into one or two local tasks.",
                "4. Execute only safe local steps first.",
                "5. Create a checkpoint with what changed, what passed, and what remains.",
            ]
        )

    def _format_checkpoint(self, checkpoint: dict) -> str:
        return "\n".join(
            [
                f"Checkpoint created: {checkpoint['checkpoint_id']}",
                f"  Timestamp: {checkpoint['timestamp']}",
                f"  Stage: {checkpoint['stage']}",
                f"  Reason: {checkpoint['reason']}",
                f"  Safety: {checkpoint['safety_status']}",
                f"  Next step: {checkpoint['next_step']}",
            ]
        )

    def _format_provider_role_split_status(self, result: dict) -> str:
        workers = result.get('external_worker_names', [])
        workers_str = ", ".join(workers)
        lines = [
            "Provider Role Split status:",
            f"Stage: {result.get('stage', 'unknown')}",
            f"Sovereign Mind: {result.get('sovereign_mind_provider', 'none')} ({result.get('sovereign_mind_endpoint', '')})",
            f"Sovereign Role: {result.get('sovereign_mind_role', '')}",
            f"External Workers Count: {result.get('external_workers_count', 0)}",
            f"External Workers: {workers_str}",
            f"Boundary Enforcement: {result.get('boundary_enforcement', 'active')}",
            f"Identity Leaks Blocked: {str(result.get('identity_leaks_blocked', True)).lower()}",
            f"Memory Leaks Blocked: {str(result.get('memory_leaks_blocked', True)).lower()}",
        ]
        return "\n".join(lines)

    def _format_ollama_status(self, result: dict) -> str:
        adapters = result.get('active_adapters', [])
        adapters_str = ", ".join(adapters) if adapters else "none"
        lines = [
            "Ollama Sovereign Connector status:",
            f"Stage: {result.get('stage', 'unknown')}",
            f"Endpoint: {result.get('endpoint', '')}",
            f"Online: {str(result.get('online', False)).lower()}",
            f"Status: {result.get('status_description', '')}",
            f"Installed Models Count: {result.get('installed_models_count', 0)}",
            f"Active LoRA Adapters Count: {result.get('active_adapters_count', 0)}",
            f"Active LoRA Adapters: {adapters_str}",
            f"Default Sovereign Model: {result.get('default_model', '')}",
            f"Operating Mode: {result.get('fallback_mode', '')}",
        ]
        return "\n".join(lines)

    def _format_training_queue_status(self, result: dict) -> str:
        lines = [
            "Verified LoRA Training Queue status:",
            f"Stage: {result.get('stage', 'unknown')}",
            f"Queue File: {result.get('queue_file', '')}",
            f"Verified Samples Count: {result.get('verified_samples_count', 0)}",
            f"Anti-Hallucination Gate: {result.get('anti_hallucination_gate', 'active')}",
        ]
        return "\n".join(lines)

    def _format_fact_verifier_status(self, result: dict) -> str:
        lines = [
            "ELIE Fact/State Verifier status:",
            f"Stage: {result.get('stage', 'unknown')}",
            f"Verifier Status: {result.get('fact_state_verifier', 'active')}",
            f"Verification Mode: {result.get('verification_mode', '')}",
            f"Anti-Hallucination Gate: {result.get('anti_hallucination_gate', 'enforced')}",
            f"LoRA Queue Protection: {result.get('lora_queue_protection', 'active')}",
        ]
        return "\n".join(lines)

    def _format_fact_verification_result(self, result: dict) -> str:
        lines = [
            f"Fact Verification Result: {result.get('badge', '')}",
            f"Verified: {str(result.get('verified', False)).lower()}",
            f"Hallucination Detected: {str(result.get('hallucination_detected', False)).lower()}",
            f"Summary: {result.get('summary', '')}",
        ]
        if result.get("verified_paths"):
            lines.append(f"Confirmed Files on Disk: {', '.join(result['verified_paths'])}")
        if result.get("missing_paths"):
            lines.append(f"Missing (Hallucinated) Files: {', '.join(result['missing_paths'])}")
        return "\n".join(lines)

    def _format_elie_review_result(self, result: dict) -> str:
        lines = [
            f"ELIE Security Review: {result.get('badge', '')}",
            f"Safe: {str(result.get('safe', False)).lower()}",
            f"Issues Count: {result.get('issues_count', 0)}",
        ]
        for issue in result.get("issues", []):
            lines.append(f"• {issue}")
        return "\n".join(lines)



    # ---------- STAGE 38 FORMATTERS ----------
    def _format_task_daemon_status(self, result: dict) -> str:
        lines = [
            "Task Daemon status:",
            f"Stage: {result.get('stage', 'unknown')}",
            f"Daemon Status: {result.get('task_daemon', 'active')}",
            f"Max Workers: {result.get('max_workers', 0)}",
            f"Total Tasks Tracked: {result.get('total_tasks', 0)}",
            f"Pending: {result.get('pending_count', 0)}",
            f"Running: {result.get('running_count', 0)}",
            f"Completed: {result.get('completed_count', 0)}",
            f"Failed: {result.get('failed_count', 0)}",
            f"Cancelled: {result.get('cancelled_count', 0)}",
        ]
        return "\n".join(lines)

    def _format_background_tasks_list(self, tasks: list[dict]) -> str:
        if not tasks:
            return "No background tasks currently in history."
        lines = ["Background Tasks:"]
        for t in tasks:
            tid = t.get("task_id", "")
            name = t.get("name", "unnamed")
            status = t.get("status", "UNKNOWN")
            progress = f"{t.get('progress_step', 0)}/{t.get('total_steps', 1)}"
            msg = t.get("progress_message", "")
            lines.append(f"• [{status}] {tid} - {name} ({progress}): {msg}")
        return "\n".join(lines)

    def _format_background_task_detail(self, task: dict | None, task_id: str) -> str:
        if not task:
            return f"Background task '{task_id}' not found."
        lines = [
            f"Background Task: {task.get('task_id')}",
            f"Name: {task.get('name')}",
            f"Status: {task.get('status')}",
            f"Progress: {task.get('progress_step', 0)}/{task.get('total_steps', 1)} - {task.get('progress_message', '')}",
            f"Created At: {task.get('created_at')}",
            f"Started At: {task.get('started_at') or 'Not started'}",
            f"Completed At: {task.get('completed_at') or 'In progress'}",
        ]
        if task.get("duration_seconds") is not None:
            lines.append(f"Duration: {task.get('duration_seconds')}s")
        if task.get("error"):
            lines.append(f"Error: {task.get('error')}")
        if task.get("result") is not None:
            lines.append(f"Result: {task.get('result')}")
        return "\n".join(lines)

    def _format_task_cancel_result(self, result: dict) -> str:
        if result.get("cancelled"):
            return f"Task '{result.get('task_id')}' ({result.get('name')}) successfully cancelled. Status: {result.get('status')}."
        return f"Unable to cancel task '{result.get('task_id')}': {result.get('reason')}."


    # ---------- STAGE 39 FORMATTERS ----------
    def _format_connect_swarm_result(self, res: dict) -> str:
        lines = [
            f"Senin AI Swarm Connection: {res.get('status', 'UNKNOWN')}",
            f"Active Live Bots: {res.get('online_count', 0)} / {res.get('total_bots', 3)}",
            f"Sovereign Policy: {res.get('sovereign_policy', '')}",
        ]
        w = res.get("writer", {})
        c = res.get("checker", {})
        d = res.get("director", {})
        lines.append(f"  Writer Bot (Port {w.get('port', 5820)}): {w.get('status', 'OFFLINE')} ({w.get('endpoint', '')})")
        lines.append(f"  Checker Bot (Port {c.get('port', 5821)}): {c.get('status', 'OFFLINE')} ({c.get('endpoint', '')})")
        lines.append(f"  Director Bot (Port {d.get('port', 5822)}): {d.get('status', 'OFFLINE')} ({d.get('endpoint', '')})")
        lines.append(f"Summary: {res.get('message', '')}")
        return "\n".join(lines)

    def _format_checker_connect_result(self, res: dict) -> str:
        lines = [
            f"Checker Bot Connection: {res.get('status', 'UNKNOWN')}",
            f"Online: {res.get('online', False)}",
            f"Endpoint: {res.get('endpoint', 'http://localhost:5821')}",
            f"Message: {res.get('message', '')}",
        ]
        return "\n".join(lines)

    def _format_checker_status_result(self, res: dict) -> str:
        return f"Checker Bot Status: {res.get('status', 'UNKNOWN')} ({res.get('endpoint', 'http://localhost:5821')})"

    def _format_director_connect_result(self, res: dict) -> str:
        lines = [
            f"Director Bot Connection: {res.get('status', 'UNKNOWN')}",
            f"Online: {res.get('online', False)}",
            f"Endpoint: {res.get('endpoint', 'http://localhost:5822')}",
            f"Message: {res.get('message', '')}",
        ]
        return "\n".join(lines)

    def _format_director_status_result(self, res: dict) -> str:
        return f"Director Bot Status: {res.get('status', 'UNKNOWN')} ({res.get('endpoint', 'http://localhost:5822')})"

    def _format_swarm_hierarchy(self) -> str:
        return (
            "SOVEREIGN BOT HIERARCHY (Senin ai/ Swarm Policy):\n"
            "===============================================================\n"
            "1. MASTER / ORCHESTRATOR: Lucy (in LUCY/lucy) is the sovereign brain.\n"
            "2. WORKER TOOLS: Bots in C:\\Users\\admin\\Desktop\\senin\\ai (Writer, Checker, Director, Planner)\n"
            "   act strictly as subordinate, stateless execution tools for this project.\n"
            "3. UNIDIRECTIONAL CONTROL: Lucy uses the bots; the bots NEVER control Lucy.\n"
            "4. PRIVACY BOUNDARY: Lucy never leaks private memory, spine, or keys to workers.\n"
            "5. VERIFICATION GATE: All bot-generated code must pass AST/pytest before acceptance.\n"
            "==============================================================="
        )

    def _format_writer_connect_result(self, res: dict) -> str:
        lines = [
            f"Writer Bot Connection: {res.get('status', 'UNKNOWN')}",
            f"Status: {res.get('status', 'UNKNOWN')}",
            f"Online: {res.get('online', False)}",
            f"Endpoint: {res.get('endpoint', 'http://localhost:5820')}",
            f"Port: {res.get('port', 5820)}",
            f"Model: {res.get('model', 'openai/gpt-oss-120b')}",
            f"Message: {res.get('message', '')}",
        ]
        if res.get("latency_ms") is not None:
            lines.append(f"Latency: {res.get('latency_ms')}ms")
        return "\n".join(lines)

    def _format_writer_status_result(self, res: dict) -> str:
        lines = [
            f"Writer Bot Status: {res.get('status', 'UNKNOWN')}",
            f"Endpoint: {res.get('endpoint', 'http://localhost:5820')}",
            f"Online: {res.get('online', False)}",
        ]
        if res.get("latency_ms") is not None:
            lines.append(f"Latency: {res.get('latency_ms')}ms")
        return "\n".join(lines)

    def _format_swarm_status(self, result: dict) -> str:
        w = result.get("writer", {})
        c = result.get("checker", {})
        d = result.get("director", {})
        p = result.get("planner", {})
        lines = [
            "External Bot Swarm status:",
            f"Stage: {result.get('stage', 'unknown')}",
            f"Model: {result.get('model', 'unknown')}",
            f"Config Source: {result.get('config_source', 'unknown')}",
            f"Active Live Bots: {result.get('online_bots_count', 0)} / {result.get('total_bots_monitored', 0)}",
            f"• Writer Bot (Port {w.get('port', 5820)}): {w.get('status', 'UNKNOWN')} ({w.get('endpoint', '')})",
            f"• Checker Bot (Port {c.get('port', 5821)}): {c.get('status', 'UNKNOWN')} ({c.get('endpoint', '')})",
            f"• Director Bot (Port {d.get('port', 5822)}): {d.get('status', 'UNKNOWN')} ({d.get('endpoint', '')})",
            f"• Planner Bot: {p.get('role', 'Configured')}",
            f"Boundary Safety: {result.get('boundary_safety', 'ENFORCED')}",
        ]
        return "\n".join(lines)

    def _format_swarm_write_result(self, result: dict) -> str:
        if result.get("offline"):
            return f"Swarm Writer Offline: {result.get('message', '')}"
        if not result.get("success", False):
            return f"Swarm Writer Error: {result.get('error', 'Unknown generation error')}"
        lines = [
            "Swarm Writer Response:",
            f"Message: {result.get('message', '')}",
        ]
        files = result.get("files", [])
        if files:
            lines.append(f"Generated Files: {', '.join(files)}")
        return "\n".join(lines)

    def _format_swarm_check_result(self, result: dict) -> str:
        lines = [
            f"Swarm Checker: Status {result.get('status', 'UNKNOWN')}",
            f"Bot: {result.get('bot', 'checker')}",
            f"Message: {result.get('message', '')}",
        ]
        issues = result.get("issues", [])
        if issues:
            lines.append("Issues Detected:")
            for issue in issues:
                lines.append(f"  • {issue}")
        return "\n".join(lines)

    def _format_swarm_director_result(self, result: dict) -> str:
        if result.get("offline"):
            return f"Swarm Director Offline: {result.get('message', '')}"
        return f"Swarm Director Result: {result.get('message', json.dumps(result))}"


    # ---------- STAGE 40 FORMATTERS ----------
    def _format_synthesis_status(self, result: dict) -> str:
        lines = [
            "Code Synthesis Pipeline status:",
            f"Stage: {result.get('stage', 'unknown')}",
            f"Pipeline Status: {result.get('code_synthesis', 'active')}",
            f"Total Syntheses Attempted: {result.get('total_syntheses', 0)}",
            f"Successfully Promoted: {result.get('promoted_count', 0)}",
            f"Verification Failures: {result.get('failed_count', 0)}",
            f"Sandbox Staging Dir: {result.get('sandbox_staging_dir', '')}",
            f"Promoted Tools Dir: {result.get('promoted_dir', '')}",
            f"LoRA Queue Protection: {result.get('lora_queue_protection', 'ACTIVE')}",
        ]
        return "\n".join(lines)

    def _format_synthesis_history(self, history: list[dict]) -> str:
        if not history:
            return "No code synthesis records found in history."
        lines = ["Code Synthesis History:"]
        for h in history:
            status = h.get("status", "UNKNOWN")
            fn = h.get("filename", "unknown.py")
            promoted = "PROMOTED" if h.get("promoted") else "BLOCKED"
            badge = h.get("badge", "")
            lines.append(f"• [{status} | {promoted}] {fn} - {badge}")
        return "\n".join(lines)

    def _format_synthesis_result(self, result: dict) -> str:
        lines = [
            f"Code Synthesis: {result.get('badge', '')}",
            f"Status: {result.get('status', 'UNKNOWN')}",
            f"Source: {result.get('source', '')}",
            f"Promoted to Workspace: {str(result.get('promoted', False)).lower()}",
        ]
        if result.get("final_path"):
            lines.append(f"Target Path: {result.get('final_path')}")
        if result.get("duration_seconds") is not None:
            lines.append(f"Duration: {result.get('duration_seconds')}s")
        if result.get("lora_queue_admitted"):
            lines.append("LoRA Training Queue: Admitted (Compiler Verified)")
        ast_err = result.get("ast", {}).get("error")
        if ast_err:
            lines.append(f"AST Error: {ast_err}")
        compile_err = result.get("compile", {}).get("error")
        if compile_err:
            lines.append(f"Compiler Error: {compile_err}")
        exec_err = result.get("execution", {}).get("error")
        if exec_err:
            lines.append(f"Execution Error: {exec_err}")
        return "\n".join(lines)

    def _format_verify_code_result(self, result: dict) -> str:
        lines = [
            f"Code Verification: {result.get('badge', '')}",
            f"Verified: {str(result.get('verified', False)).lower()}",
            f"Target File: {result.get('file', '')}",
        ]
        ast_res = result.get("ast", {})
        if not ast_res.get("ast_passed"):
            lines.append(f"• AST Failure: {ast_res.get('error')}")
        compile_res = result.get("compile", {})
        if not compile_res.get("compile_passed"):
            lines.append(f"• Compiler Failure: {compile_res.get('error')}")
        exec_res = result.get("execution", {})
        if not exec_res.get("execution_passed"):
            lines.append(f"• Execution Failure: {exec_res.get('error')}")
        return "\n".join(lines)


    # ---------- STAGE 41 FORMATTERS ----------
    def _format_refinement_status(self, result: dict) -> str:
        lines = [
            "Self-Refinement Harness status:",
            f"Stage: {result.get('stage', 'unknown')}",
            f"Harness Status: {result.get('self_refinement', 'active')}",
            f"Total Refinements Attempted: {result.get('total_refinements_attempted', 0)}",
            f"Successfully Resolved: {result.get('resolved_count', 0)}",
            f"Unresolved Failures: {result.get('unresolved_count', 0)}",
            f"Regression Testing: {result.get('regression_testing', 'active')}",
            f"Healer Modes: {', '.join(result.get('healer_modes', []))}",
        ]
        return "\n".join(lines)

    def _format_refinement_history(self, history: list[dict]) -> str:
        if not history:
            return "No refinement records found in history."
        lines = ["Self-Refinement History:"]
        for h in history:
            fn = h.get("filename", "unknown.py")
            resolved = "RESOLVED" if h.get("resolved") else "FAILED"
            attempts = h.get("attempts_count", 0)
            badge = h.get("badge", "")
            lines.append(f"• [{resolved} | Attempts: {attempts}] {fn} - {badge}")
        return "\n".join(lines)

    def _format_regression_result(self, result: dict) -> str:
        lines = [
            "Regression Testing Result:",
            f"Passed: {str(result.get('regression_passed', False)).lower()}",
            f"Summary: {result.get('summary', '')}",
        ]
        if result.get("stderr"):
            lines.append(f"Stderr: {result.get('stderr')}")
        return "\n".join(lines)

    def _format_refinement_result(self, result: dict) -> str:
        lines = [
            f"Self-Refinement: {result.get('badge', '')}",
            f"Resolved: {str(result.get('resolved', False)).lower()}",
            f"Attempts Taken: {result.get('attempts_count', 0)} / {result.get('max_attempts', 3)}",
        ]
        for att in result.get("history_attempts", []):
            num = att.get("attempt", 1)
            src = att.get("repair_source", "unknown")
            outcome = att.get("test_outcome", "UNKNOWN")
            lines.append(f"  [Attempt {num}] Source: {src} -> Test: {outcome}")
        return "\n".join(lines)


    # ---------- STAGE 42 FORMATTERS ----------
    def _format_lora_sleep_cycle_status(self, result: dict) -> str:
        lines = [
            "LoRA Sleep Cycle status:",
            f"Stage: {result.get('stage', 'unknown')}",
            f"Sleep Cycle System: {result.get('lora_sleep_cycle', 'active')}",
            f"Discovered Adapters Count: {result.get('adapters_count', 0)}",
            f"Active Adapter: {result.get('active_adapter') or 'None (Spine Baseline)'}",
            f"Active Adapter Sanity Score: {result.get('active_adapter_score', 'N/A')}%",
            f"Verified Queue Count: {result.get('verified_queue_count', 0)}",
            f"Sanity Gate Threshold: {result.get('sanity_gate_threshold', '90%')}",
            f"Model Collapse Protection: {result.get('model_collapse_protection', 'ACTIVE')}",
        ]
        return "\n".join(lines)

    def _format_sleep_cycle_result(self, result: dict) -> str:
        lines = [
            f"LoRA Sleep Cycle: {result.get('badge', '')}",
            f"Status: {result.get('status', 'UNKNOWN')}",
            f"Adapter Name: {result.get('adapter_name', '')}",
            f"Dataset Exported: {str(result.get('dataset_exported', False)).lower()}",
            f"Modelfile Generated: {str(result.get('modelfile_generated', False)).lower()}",
            f"Adapter Activated: {str(result.get('activated', False)).lower()}",
        ]
        gate = result.get("sanity_gate", {})
        if gate:
            lines.append(f"Sanity Gate Score: {gate.get('score', '')} ({gate.get('score_percentage', 0)}%)")
        return "\n".join(lines)

    def _format_sanity_gate_result(self, result: dict) -> str:
        lines = [
            f"20-Question Sanity Gate: {result.get('badge', '')}",
            f"Passed: {str(result.get('passed', False)).lower()}",
            f"Score: {result.get('score', '')} ({result.get('score_percentage', 0)}%)",
            f"Threshold Required: {result.get('threshold_required', '90.0%')}",
            "Probes Summary:",
        ]
        for p in result.get("probes", []):
            mark = "PASS" if p.get("passed") else "FAIL"
            lines.append(f"  • [{mark}] [{p.get('pillar')}] {p.get('question')}")
        return "\n".join(lines)

    def _format_lora_adapters_list(self, adapters: list[str]) -> str:
        if not adapters:
            return "No LoRA adapters discovered in data/lucy/adapters/."
        lines = ["Discovered LoRA Adapters:"]
        for a in adapters:
            lines.append(f"  • {a}")
        return "\n".join(lines)

    def _format_sleep_cycle_history(self, history: list[dict]) -> str:
        if not history:
            return "No sleep cycle records found in history."
        lines = ["LoRA Sleep Cycle History:"]
        for h in history:
            adp = h.get("adapter_name", "unknown")
            act = "ACTIVATED" if h.get("activated") else "QUARANTINED"
            badge = h.get("badge", "")
            lines.append(f"• [{act}] {adp} - {badge}")
        return "\n".join(lines)

    def _format_conversational_memory_status(self, result: dict) -> str:
        lines = [
            "Conversational Memory & Context Engine status:",
            f"Stage: {result.get('stage', 'unknown')}",
            f"System: {result.get('conversational_memory', 'active')}",
            f"Total Disk Turns: {result.get('total_disk_turns', 0)}",
            f"Active Sliding Context Turns: {result.get('active_sliding_context_turns', 0)} (max {result.get('max_context_turns', 5)})",
            f"Context Cleared: {str(result.get('context_cleared', False)).lower()}",
            f"Permanent Log: {result.get('convo_log_file')}",
            f"Session Recap: {result.get('session_recap', 'None')}",
        ]
        return "\n".join(lines)

    def _format_session_recap(self, result: dict) -> str:
        lines = [
            "Previous Session Recap:",
            f"Stage: {result.get('stage', 'unknown')}",
            f"Total Recorded Turns: {result.get('total_turns', 0)}",
            f"Last Active: {result.get('last_active') or 'None'}",
            f"Summary: {result.get('recap_text', 'No history recorded yet.')}",
        ]
        inputs = result.get("recent_inputs", [])
        if inputs:
            lines.append("Recent Topics:")
            for item in inputs:
                lines.append(f"  • {item}")
        return "\n".join(lines)

    def _format_clear_session_context(self, result: dict) -> str:
        lines = [
            "Conversational Context Buffer Reset:",
            f"Status: {result.get('status', 'cleared')}",
            f"Message: {result.get('message', '')}",
            f"Permanent Log Intact: {result.get('convo_log_file')}",
            f"Retained History Turns: {result.get('retained_history_turns', 0)}",
        ]
        return "\n".join(lines)

    def _format_personal_profile_status(self, result: dict) -> str:
        lines = [
            "Personal Behavioral Profile status:",
            f"Stage: {result.get('stage', 'unknown')}",
            f"Profiler System: {result.get('personal_profiler', 'active')}",
            f"Anti-Drift Rules Count: {result.get('anti_drift_rules_count', 0)}",
            f"Workspace Aliases Count: {result.get('workspace_aliases_count', 0)}",
            f"Learned Corrections Count: {result.get('learned_corrections_count', 0)}",
            f"User Persona: {result.get('user_persona', {})}",
            f"Coding Preferences: {result.get('coding_preferences', {})}",
        ]
        return "\n".join(lines)

    def _format_personal_preferences(self, result: dict) -> str:
        persona = result.get("user_persona", {})
        coding = result.get("coding_preferences", {})
        lines = [
            "User Personal Preferences:",
            f"• Brevity: {persona.get('brevity', 'concise')}",
            f"• Tone: {persona.get('tone', 'direct_technical')}",
            f"• Explanation Depth: {persona.get('explanation_depth', 'minimal')}",
            f"• Prefer Standard Library: {coding.get('prefer_standard_library', True)}",
            f"• Avoid Heavy Dependencies: {coding.get('avoid_heavy_dependencies', True)}",
            f"• Verify with AST/Pytest: {coding.get('verify_with_ast_pytest', True)}",
        ]
        custom = coding.get("custom_rules", [])
        if custom:
            lines.append("Custom Coding Rules:")
            for c in custom:
                lines.append(f"  - {c}")
        return "\n".join(lines)

    def _format_anti_drift_rules(self, result: dict) -> str:
        rules = result.get("anti_drift_rules", [])
        lines = [f"Active Anti-Drift Guardrails ({len(rules)} rules):"]
        for r in rules:
            lines.append(f"  • {r}")
        return "\n".join(lines)

    def _format_add_alias(self, result: dict) -> str:
        if result.get("saved"):
            return f"Workspace alias registered: '{result.get('shortcut')}' -> '{result.get('target')}'."
        return f"Failed to register alias: {result.get('reason', 'unknown')}."

    def _format_add_rule(self, result: dict) -> str:
        if result.get("saved"):
            return f"Anti-drift rule locked in: {result.get('rule')}"
        if result.get("duplicate"):
            return "This anti-drift rule is already active."
        return f"Failed to add rule: {result.get('reason', 'unknown')}."

    def _format_personal_lora_status(self, result: dict) -> str:
        lines = [
            "Personal LoRA Alignment status:",
            f"Stage: {result.get('stage', 'unknown')}",
            f"Alignment System: {result.get('personal_lora_alignment', 'active')}",
            f"Dataset File: {result.get('dataset_file', '')}",
            f"Personal Adapters Count: {result.get('personal_adapters_count', 0)}",
            f"Alignment Pass Threshold: {result.get('alignment_pass_threshold', '90.0%')}",
            f"Personal Modelfile: {result.get('modelfile', '')}",
        ]
        return "\n".join(lines)

    def _format_personal_sleep_cycle_result(self, result: dict) -> str:
        lines = [
            f"Personal LoRA Alignment Cycle: {result.get('badge', '')}",
            f"Status: {result.get('status', 'UNKNOWN')}",
            f"Adapter Name: {result.get('adapter_name', '')}",
            f"Dataset Records: {result.get('dataset_record_count', 0)}",
            f"Modelfile: {result.get('modelfile', '')}",
        ]
        gate = result.get("alignment_gate", {})
        if gate:
            lines.append(f"Alignment Gate Score: {gate.get('score', '')} ({gate.get('score_percentage', 0)}%)")
        return "\n".join(lines)

    def _format_personal_alignment_gate_result(self, result: dict) -> str:
        lines = [
            f"10-Question Personal Alignment Gate: {result.get('badge', '')}",
            f"Passed: {str(result.get('passed', False)).lower()}",
            f"Score: {result.get('score', '')} ({result.get('score_percentage', 0)}%)",
            f"Threshold Required: {result.get('threshold_required', '90.0%')}",
            "Probes Summary:",
        ]
        for p in result.get("probes", []):
            mark = "PASS" if p.get("passed") else "FAIL"
            lines.append(f"  • [{mark}] [{p.get('category')}] {p.get('question')}")
        return "\n".join(lines)

    def _format_personal_adapters_list(self, adapters: list[str]) -> str:
        if not adapters:
            return "No personal LoRA adapters discovered in data/lucy/adapters/."
        lines = ["Discovered Personal LoRA Adapters:"]
        for a in adapters:
            lines.append(f"  • {a}")
        return "\n".join(lines)

    def _format_synthesize_personal_dataset(self, result: dict) -> str:
        lines = [
            "Personal Alignment Dataset Synthesized:",
            f"• Records: {result.get('record_count', 0)}",
            f"• Anti-Drift Directives: {result.get('anti_drift_count', 0)}",
            f"• Workspace Aliases: {result.get('aliases_count', 0)}",
            f"• Output File: {result.get('dataset_file', '')}",
        ]
        return "\n".join(lines)

    def _format_provider_pool_status(self, result: dict) -> str:
        lines = [
            "Multi-Provider Key Rotation Pool status:",
            f"Stage: {result.get('stage', 'unknown')}",
            f"System: {result.get('multi_provider_pool', 'active')}",
            f"Total Keys Loaded: {result.get('total_keys_loaded', 0)}",
            f"Keys File: {result.get('keys_file', '')}",
            f"Cooldown Time: {result.get('cooldown_seconds', 60)}s",
            "Provider Pools Breakdown:",
        ]
        for p, info in result.get("providers_summary", {}).items():
            lines.append(
                f"  • {p.upper()}: {info.get('active_available', 0)}/{info.get('total_keys', 0)} active "
                f"(current: key #{info.get('current_index', 0)} - {info.get('current_active_key', 'None')})"
            )
        return "\n".join(lines)

    def _format_rotate_key(self, result: dict) -> str:
        if result.get("rotated"):
            lines = [
                "Provider Key Rotated:",
                f"• Provider: {result.get('provider')}",
                f"• Index: #{result.get('previous_index')} -> #{result.get('new_index')}",
                f"• Active Key: {result.get('active_masked_key')}",
                f"• Reason: {result.get('reason')}",
            ]
            return "\n".join(lines)
        return f"Failed to rotate key: {result.get('reason', 'unknown')}"

    def _format_reload_keys(self, result: dict) -> str:
        if result.get("loaded"):
            counts = result.get("provider_counts", {})
            lines = [
                f"API Keys Reloaded Successfully ({result.get('total_keys', 0)} total keys):",
                f"Source: {result.get('keys_file')}",
            ]
            for p, c in counts.items():
                if c > 0:
                    lines.append(f"  • {p.upper()}: {c} keys")
            return "\n".join(lines)
        return f"Failed to load keys: {result.get('reason') or result.get('error')}"

    def _format_rate_limit_result(self, result: dict) -> str:
        lines = [
            f"Rate Limit Simulation Result ({result.get('status', '')}):",
            f"• Provider: {result.get('provider', '')}",
            f"• Cooling Down: {result.get('cooling_down_key', '')} ({result.get('cooldown_seconds', 0)}s)",
        ]
        if "new_active_key" in result:
            lines.append(f"• Rotated To Key #{result.get('new_index')}: {result.get('new_active_key')}")
        if "recommended_failover" in result:
            fo = result["recommended_failover"]
            if fo.get("failover_available"):
                lines.append(f"• Cross-Provider Failover Triggered: Switched to {fo.get('provider', '').upper()} ({fo.get('masked_key')})")
            else:
                lines.append("• Notice: All external providers are cooling down.")
        return "\n".join(lines)

    def _format_system_telemetry(self, result: dict) -> str:
        os_info = result.get("os", {})
        ram = result.get("ram", {})
        disk = result.get("disk", {})
        power = result.get("power", {})
        lines = [
            "Windows Hardware & System Telemetry:",
            f"Stage: {result.get('stage', 'unknown')}",
            f"OS: {os_info.get('system')} {os_info.get('release')} (Build {os_info.get('version')})",
            f"CPU: {os_info.get('machine')} with {os_info.get('cpu_cores')} logical cores",
            f"RAM: {ram.get('available_mb', 0)} MB free / {ram.get('total_mb', 0)} MB total ({ram.get('memory_load_percent', 0)}% memory load)",
            f"Disk C: {disk.get('free_gb', 0)} GB free / {disk.get('total_gb', 0)} GB total ({disk.get('percent_free', 0)}% free)",
            f"Power / Battery: {power.get('ac_line_status', 'Unknown')}, Battery: {power.get('battery_percent', 'N/A')}",
        ]
        return "\n".join(lines)

    def _format_inspect_processes(self, procs: list) -> str:
        if not procs:
            return "No matching processes found."
        lines = [f"Process Inspector ({len(procs)} matching processes):"]
        for p in procs:
            lines.append(f"  • [PID {p.get('pid', 'N/A')}] {p.get('name', 'unknown')} (Memory: {p.get('memory', 'N/A')})")
        return "\n".join(lines)

    def _format_search_workspace(self, results: list) -> str:
        if not results:
            return "No matching workspace files found."
        lines = [f"Workspace File Search ({len(results)} matches):"]
        for r in results:
            content_tag = " [content match]" if r.get("matched_content") else ""
            lines.append(f"  • {r.get('name')} ({r.get('size_bytes', 0)} bytes){content_tag} -> {r.get('path')}")
        return "\n".join(lines)

    def _format_probe_ports(self, result: dict) -> str:
        lines = [
            f"Operator Network Socket Probes ({result.get('active_services', 0)}/{result.get('total_probed', 0)} active):",
        ]
        for port, info in result.get("ports", {}).items():
            lines.append(f"  • Port {port} [{info.get('service')}]: {info.get('status')}")
        return "\n".join(lines)

    def _format_clean_sandbox(self, result: dict) -> str:
        lines = [
            "Sandbox Staging Cache Cleanup:",
            f"• Files Cleaned: {result.get('files_found', 0)}",
            f"• Bytes Freed: {result.get('bytes_freed', 0)} bytes",
            f"• Staging Directory: {result.get('staging_dir', '')}",
        ]
        return "\n".join(lines)

    def _format_intent_status(self, result: dict) -> str:
        lines = [
            "Autonomous Intent Dispatcher status:",
            f"Stage: {result.get('stage', 'unknown')}",
            f"Dispatcher System: {result.get('intent_dispatcher', 'active')}",
            f"Total Dispatches Executed: {result.get('dispatch_count', 0)}",
            "Supported Intent Workflows:",
        ]
        for it in result.get("supported_intents", []):
            lines.append(f"  • {it}")
        return "\n".join(lines)

    def _format_intent_classification(self, result: dict) -> str:
        lines = [
            "Natural Language Intent Classification:",
            f"• Query: '{result.get('raw_text', '')}'",
            f"• Classified Intent: {result.get('intent_type', 'UNKNOWN')}",
            f"• Confidence: {round(result.get('confidence', 0.0) * 100, 1)}%",
            f"• Extracted Target: '{result.get('extracted_target', '')}'",
        ]
        return "\n".join(lines)

    def _format_sentinel_status(self, result: dict) -> str:
        lines = [
            "Proactive Workspace Sentinel status:",
            f"Stage: {result.get('stage', 'unknown')}",
            f"Sentinel System: {result.get('workspace_sentinel', 'active')}",
            f"Background Watcher: {'RUNNING' if result.get('is_background_running') else 'STOPPED'}",
            f"Watched Root: {result.get('watch_root', '')}",
            f"Total Scans Executed: {result.get('scan_count', 0)}",
            f"Tracked Files Count: {result.get('tracked_files', 0)}",
            f"Syntax Errors Caught: {result.get('total_syntax_errors_caught', 0)}",
            f"Pending Alerts: {result.get('pending_alerts_count', 0)}",
        ]
        top = result.get("top_active_folders", [])
        if top:
            lines.append("Top Active Workspace Folders:")
            for folder, hits in top:
                lines.append(f"  • {folder} ({hits} touches)")
        return "\n".join(lines)

    def _format_scan_workspace(self, result: dict) -> str:
        lines = [
            f"Workspace Scan #{result.get('scan_index', 0)} Complete:",
            f"• Total Files Tracked: {result.get('total_tracked', 0)}",
            f"• Created: {result.get('created_count', 0)}",
            f"• Modified: {result.get('modified_count', 0)}",
            f"• Deleted: {result.get('deleted_count', 0)}",
            f"• Syntax Alerts Caught: {result.get('syntax_alerts_caught', 0)}",
        ]
        return "\n".join(lines)

    def _format_sentinel_alerts(self, alerts: list) -> str:
        if not alerts:
            return "No pending sentinel alerts. All workspace files are healthy."
        lines = [f"Proactive Sentinel Alerts ({len(alerts)} alerts):"]
        for a in alerts:
            lines.append(f"  • {a}")
        return "\n".join(lines)

    def _format_repl_status(self, result: dict) -> str:
        lines = [
            "Terminal REPL & Command Palette Status:",
            f"• Stage: {result.get('stage', '50')}",
            f"• Status: {result.get('status', 'ready')}",
            f"• Color Enabled: {result.get('color_enabled', False)}",
            f"• History Count: {result.get('history_count', 0)}",
            f"• Macros Registered: {result.get('macros_registered', 0)}",
            f"• Palette Commands: {result.get('palette_commands_count', 0)}",
        ]
        return "\n".join(lines)

    def _format_repl_history(self, history: list) -> str:
        if not history:
            return "Terminal command history is empty."
        lines = [f"Recent Command History ({len(history)} entries):"]
        for i, cmd in enumerate(history, 1):
            lines.append(f"  {i:>2}. {cmd}")
        return "\n".join(lines)

    def _format_diagnostics(self, result: dict) -> str:
        lines = [
            f"Lucy Self-Diagnostics Report (Health: {result.get('overall_health', 'UNKNOWN')}):",
            f"• Elapsed: {result.get('elapsed_ms', 0)} ms",
            f"• Monitored State Files: {result.get('state_audit', {}).get('total_checked', 0)} (All Healthy: {result.get('state_audit', {}).get('all_healthy', False)})",
        ]
        corrupted = result.get("state_audit", {}).get("corrupted", [])
        if corrupted:
            lines.append(f"  - Corrupted: {', '.join(corrupted)}")
        missing = result.get("state_audit", {}).get("missing", [])
        if missing:
            lines.append(f"  - Missing: {', '.join(missing)}")
        lines.append(f"• Log Hygiene: {result.get('log_hygiene', {}).get('logs_scanned', 0)} scanned, {len(result.get('log_hygiene', {}).get('rotated_logs', []))} rotated")
        lines.append("• Subsystem Statuses:")
        for sub, info in result.get("subsystems", {}).items():
            lines.append(f"  - {sub:<18}: {info.get('status', 'UNKNOWN')}")
        return "\n".join(lines)

    def _format_auto_heal(self, result: dict) -> str:
        lines = [
            f"Lucy Auto-Heal Execution (Result: {result.get('current_health', 'UNKNOWN')}):",
        ]
        actions = result.get("actions_taken", [])
        if actions:
            for a in actions:
                lines.append(f"• Action: {a}")
        else:
            lines.append("• All monitored subsystems and state files are in optimal health. No healing required.")
        return "\n".join(lines)

    def _format_create_backups(self, result: dict) -> str:
        lines = [
            f"Lucy State Snapshot Complete ({result.get('total_backed_up', 0)} files backed up to .bak):",
        ]
        for f in result.get("files", []):
            lines.append(f"• {f}.bak")
        return "\n".join(lines)

    def _format_orchestrator_status(self, result: dict) -> str:
        lines = [
            "Master Orchestrator DAG Status:",
            f"• Stage: {result.get('stage', '52')}",
            f"• Status: {result.get('status', 'ready')}",
            f"• Total Goals Executed: {result.get('goals_executed', 0)}",
            f"• Templates Available: {', '.join(result.get('templates_available', []))}",
        ]
        return "\n".join(lines)

    def _format_goal_history(self, history: list) -> str:
        if not history:
            return "No previous goal execution records found."
        lines = [f"Master Orchestrator Goal History ({len(history)} goals):"]
        for g in history:
            lines.append(f"• [{g.get('status', 'UNKNOWN')}] {g.get('title', '')} ({g.get('completed_steps', 0)}/{g.get('total_steps', 0)} steps in {g.get('elapsed_ms', 0)}ms)")
        return "\n".join(lines)

    def _format_goal_result(self, result: dict) -> str:
        lines = [
            f"Master Orchestrator Execution ({'SUCCESS' if result.get('ok') else 'FAILURE'}):",
            f"• Goal ID: {result.get('goal_id', 'unknown')}",
            f"• Status: {result.get('status', 'UNKNOWN')}",
            f"• Total Elapsed: {result.get('elapsed_ms', 0)} ms",
            "",
            result.get("tree", ""),
        ]
        return "\n".join(lines)

    def _format_cron_status(self, result: dict) -> str:
        lines = [
            "Autonomous Cron & Temporal Daemon Status:",
            f"• Stage: {result.get('stage', '53')}",
            f"• Daemon Running: {result.get('daemon_running', False)}",
            f"• Total Jobs: {result.get('total_jobs', 0)} ({result.get('active_jobs', 0)} active, {result.get('paused_jobs', 0)} paused)",
            f"• Total Executions: {result.get('total_executions', 0)}",
        ]
        return "\n".join(lines)

    def _format_schedules(self, jobs: list) -> str:
        if not jobs:
            return "No scheduled operational jobs registered."
        lines = [f"Registered Cron Schedules ({len(jobs)} jobs):"]
        for j in jobs:
            state = "ACTIVE" if j.get("enabled") else "PAUSED"
            lines.append(f"• [{state}] {j.get('job_id')}: '{j.get('name')}' ({j.get('expression')}) -> {j.get('target')} (Next: {j.get('next_run')})")
        return "\n".join(lines)