"""
router.py
Command router for Lucy's terminal interface.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from backend.lucy_core.command_normalizer import normalize_command


@dataclass
class RouterResponse:
    message: str
    should_exit: bool = False


class CommandRouter:
    def __init__(self, runtime) -> None:
        self.runtime = runtime

    def handle(self, raw_text: str) -> RouterResponse:
        response = self._handle(raw_text)
        if not response.should_exit:
            self.runtime.record_interaction(raw_text, response.message)
        return response

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

        if lowered in {"create deep recall session", "create recall session", "deep recall", "recall"}:
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
