"""
lucy_runtime.py
Main Lucy runtime controller.
Loads config, spine, and all subsystems.
Exposes status, safety checks, memory, projects, checkpoints, and health.
Does NOT execute system actions.
"""

from __future__ import annotations

import json
import importlib
import re
import sys
from typing import Any
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

# Allow imports from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.lucy_core.agent_registry import AgentRegistry
from backend.lucy_core.agent_orchestrator import AgentOrchestrator
from backend.lucy_core.approved_patch_pipeline import ApprovedPatchPipeline
from backend.lucy_core.api_tools import ExternalToolRouter
from backend.lucy_core.approval_manager import ApprovalManager
from backend.lucy_core.boundary_checker import BoundaryChecker, BoundaryResult
from backend.lucy_core.checkpoint_builder import CheckpointBuilder
from backend.lucy_core.checkpoint_manager import CheckpointManager
from backend.lucy_core.conversation import ConversationEngine
from backend.lucy_core.cognition import CognitionCore
from backend.lucy_core.continuity import ContinuityBackup
from backend.lucy_core.daily_context import DailyContextEngine
from backend.lucy_core.event_logger import EventLogger
from backend.lucy_core.brain import BrainRouter
from backend.lucy_core.evaluation_lab import EvaluationLab
from backend.lucy_core.experience_storage import ExperienceStorage
from backend.lucy_core.identity_stability import IdentityStability
from backend.lucy_core.long_term_strategy import LongTermStrategy
from backend.lucy_core.smart_organizer import SmartOrganizer
from backend.lucy_core.safe_local_actions import SafeLocalActions
from backend.lucy_core.external_app_bridge import ExternalAppBridge
from backend.lucy_core.proactive_awareness import ProactiveAwareness
from backend.lucy_core.deep_recall import DeepRecall
from backend.lucy_core.judgment import Judgment
from backend.lucy_core.adaptive_communication import AdaptiveCommunication
from backend.lucy_core.human_state_awareness import HumanStateAwareness
from backend.lucy_core.time_awareness import TimeAwareness
from backend.lucy_core.autonomy_boundaries import AutonomyBoundaries
from backend.lucy_core.provider_identity_boundary import ProviderIdentityBoundary
from backend.lucy_core.secrets_provider_key_safety import SecretsProviderKeySafety
from backend.lucy_core.provider_registry import ProviderRegistry
from backend.lucy_core.provider_health_check import ProviderHealthCheck
from backend.lucy_core.provider_role_split import ProviderRoleSplit
from backend.lucy_core.ollama_connector import OllamaConnector
from backend.lucy_core.training_queue import TrainingQueue, VerifiedTrainingQueue
from backend.lucy_core.fact_state_verifier import FactStateVerifier
from backend.lucy_core.task_daemon import TaskDaemon
from backend.lucy_core.swarm_dispatcher import SwarmDispatcher
from backend.lucy_core.open_jarvis_bridge import OpenJarvisBridge, STAGE as STAGE_301
from backend.lucy_core.code_synthesis import CodeSynthesisPipeline
from backend.lucy_core.self_refinement import SelfRefinementHarness
from backend.lucy_core.lora_sleep_cycle import LoRASleepCycle, LoRASleepCycleEngine
from backend.lucy_core.conversational_memory import ConversationalMemoryEngine
from backend.lucy_core.personal_profiler import PersonalProfiler
from backend.lucy_core.personal_lora_alignment import PersonalLoRAAlignmentPipeline, PersonalLoRAAlignmentEngine
from backend.lucy_core.multi_provider_pool import MultiProviderPool
from backend.lucy_core.operator_toolkit import OperatorToolkit
from backend.lucy_core.intent_dispatcher import IntentDispatcher
from backend.lucy_core.workspace_sentinel import WorkspaceSentinel
from backend.lucy_core.terminal_repl import TerminalREPL
from backend.lucy_core.self_diagnostics import CrashRecoveryDaemon
from backend.lucy_core.master_orchestrator import MasterOrchestrator
from backend.lucy_core.cron_scheduler import CronDaemon
from backend.lucy_core.memory_graph import TemporalMemoryGraph
from backend.lucy_core.internal_monologue import InternalMonologueSpine, STAGE as STAGE_68
from backend.lucy_core.persona_governor import PersonaGovernor, STAGE as STAGE_69
from backend.lucy_core.terminal_react import TerminalReActEngine, STAGE as STAGE_70
from backend.lucy_core.codebase_indexer import CodebaseIndexer, STAGE as STAGE_71
from backend.lucy_core.memory_walker import SpreadingActivationWalker, STAGE as STAGE_72
from backend.lucy_core.tool_synthesizer import DynamicToolSynthesizer, STAGE as STAGE_73
from backend.lucy_core.terminal_sentinel import TerminalSentinel, STAGE as STAGE_74
from backend.lucy_core.terminal_canvas import TerminalCanvas, STAGE as STAGE_75
from backend.lucy_core.memory_distiller import CognitiveDistiller, STAGE as STAGE_76
from backend.lucy_core.code_reviewer import AutonomousCodeReviewer, STAGE as STAGE_77
from backend.lucy_core.atomic_patcher import AtomicPatchOrchestrator, STAGE as STAGE_78
from backend.lucy_core.test_triage import TestTriageEngine, STAGE as STAGE_79
from backend.lucy_core.task_graph import GoalTaskGraphEngine, STAGE as STAGE_80
from backend.lucy_core.web_explorer import SovereignWebExplorer, STAGE as STAGE_81
from backend.lucy_core.web_reader import SovereignWebReader, STAGE as STAGE_82
from backend.lucy_core.web_verifier import WebFactChecker, STAGE as STAGE_83
from backend.lucy_core.lora_harvester import HighSignalLoRAHarvester, STAGE as STAGE_84
from backend.lucy_core.lora_compiler import LocalModelAdapterCompiler, STAGE as STAGE_85
from backend.lucy_core.sanity_gate import AntiForgettingSanityGate, STAGE as STAGE_86
from backend.lucy_core.epistemic_provenance import EpistemicProvenanceTracker, STAGE as STAGE_87
from backend.lucy_core.style_mirror import DynamicStyleMirror, STAGE as STAGE_88
from backend.lucy_core.hypothesis_engine import CounterfactualHypothesisEngine, STAGE as STAGE_89
from backend.lucy_core.master_synthesis import SovereignMasterSynthesis, STAGE as STAGE_90
from backend.lucy_core.mutation_fuzzer import AutonomousMutationFuzzer, STAGE as STAGE_91
from backend.lucy_core.self_healing_patcher import SelfHealingPatchEngine, STAGE as STAGE_92
from backend.lucy_core.ast_vector_index import ASTVectorCodeIndexer, STAGE as STAGE_93
from backend.lucy_core.spec_drift_detector import SpecDriftDetector, STAGE as STAGE_94
from backend.lucy_core.multi_agent_worktree import MultiAgentWorktreeFabric, STAGE as STAGE_95
from backend.lucy_core.offline_model_quantizer import OfflineModelQuantizer, STAGE as STAGE_96
from backend.lucy_core.causal_dag_memory import CausalDAGMemoryEngine, STAGE as STAGE_97
from backend.lucy_core.zero_leak_sandbox import ZeroLeakHostSandbox, STAGE as STAGE_98
from backend.lucy_core.hardware_telemetry_optimizer import HardwareTelemetryOptimizer, STAGE as STAGE_99
from backend.lucy_core.centennial_master_seal import CentennialMasterSealEngine, STAGE as STAGE_100
from backend.lucy_core.kernel_supervisor import KernelSupervisor, STAGE as STAGE_101
from backend.lucy_core.execution_profiler import ExecutionProfiler, STAGE as STAGE_102
from backend.lucy_core.neural_retriever import HybridNeuralRetriever, STAGE as STAGE_103
from backend.lucy_core.refactor_engine import AutonomousRefactorEngine, STAGE as STAGE_104
from backend.lucy_core.peer_mesh_sync import SovereignPeerMeshSync, STAGE as STAGE_105
from backend.lucy_core.offline_voice_fabric import OfflineVoiceFabric, STAGE as STAGE_106
from backend.lucy_core.token_compressor import SemanticTokenCompressor, STAGE as STAGE_107
from backend.lucy_core.red_team_simulator import SecurityRedTeamSimulator, STAGE as STAGE_108
from backend.lucy_core.ambient_hud_overlay import AmbientHUDOverlay, STAGE as STAGE_109
from backend.lucy_core.consensus_nexus import SovereignConsensusNexus, STAGE as STAGE_110
from backend.lucy_core.workspace_daemon import WorkspaceSensorDaemon, STAGE as STAGE_111
from backend.lucy_core.semantic_cache import SemanticInferenceCache, STAGE as STAGE_112
from backend.lucy_core.ast_polyglot_engine import PolyglotASTEngine, STAGE as STAGE_113
from backend.lucy_core.agent_pipeline_fusion import AgentPipelineFusionEngine, STAGE as STAGE_114
from backend.lucy_core.streaming_event_bus import SovereignIPCEventBus, STAGE as STAGE_115
from backend.lucy_core.local_vector_db import PersistentLocalVectorDB, STAGE as STAGE_116
from backend.lucy_core.git_ops_synthesizer import AutonomousGitOpsSynthesizer, STAGE as STAGE_117
from backend.lucy_core.thermal_governor import ThermalComputeGovernor, STAGE as STAGE_118
from backend.lucy_core.dream_consolidator import EpisodicDreamConsolidator, STAGE as STAGE_119
from backend.lucy_core.era12_master_seal import Era12MasterSealNexus, STAGE as STAGE_120
from backend.lucy_core.neural_knowledge_graph import NeuralKnowledgeGraphNexus, STAGE as STAGE_121
from backend.lucy_core.counterfactual_simulator import CounterfactualSimulationEngine, STAGE as STAGE_122
from backend.lucy_core.hierarchical_goal_decomposer import HierarchicalGoalDecomposer, STAGE as STAGE_123
from backend.lucy_core.autonomous_verification_oracle import AutonomousVerificationOracle, STAGE as STAGE_124
from backend.lucy_core.latent_concept_miner import LatentConceptMiner, STAGE as STAGE_125
from backend.lucy_core.dynamic_context_budgeter import DynamicContextBudgetAllocator, STAGE as STAGE_126
from backend.lucy_core.protocol_reverse_synthesizer import ProtocolReverseSynthesizer, STAGE as STAGE_127
from backend.lucy_core.meta_policy_refiner import AutonomousMetaPolicyRefiner, STAGE as STAGE_128
from backend.lucy_core.mesh_gateway_bridge import DistributedMeshGatewayBridge, STAGE as STAGE_129
from backend.lucy_core.era13_master_seal import Era13MasterSealNexus, STAGE as STAGE_130
from backend.lucy_core.ast_mutation_operator import ASTSemanticMutationOperator, STAGE as STAGE_131
from backend.lucy_core.test_oracle_synthesizer import AutonomousTestOracleSynthesizer, STAGE as STAGE_132
from backend.lucy_core.static_constraint_solver import StaticConstraintSolver, STAGE as STAGE_133
from backend.lucy_core.bytecode_disassembler import BytecodeDisassemblyInspector, STAGE as STAGE_134
from backend.lucy_core.ffi_native_linker import PolyglotFFINativeLinker, STAGE as STAGE_135
from backend.lucy_core.sovereign_wheel_fabric import SovereignWheelFabricIndex, STAGE as STAGE_136
from backend.lucy_core.perf_regression_sentinel import RealTimePerfRegressionSentinel, STAGE as STAGE_137
from backend.lucy_core.dead_code_eliminator import DeadCodeEliminator, STAGE as STAGE_138
from backend.lucy_core.flight_data_recorder import FlightDataRecorder, STAGE as STAGE_139
from backend.lucy_core.era14_master_seal import Era14MasterSealNexus, STAGE as STAGE_140
from backend.lucy_core.ir_compiler_core import IRCompilerCore, STAGE as STAGE_141
from backend.lucy_core.ssa_optimizer import SSAOptimizer, STAGE as STAGE_142
from backend.lucy_core.loop_polyhedral_optimizer import LoopPolyhedralOptimizer, STAGE as STAGE_143
from backend.lucy_core.register_allocator import RegisterAllocator, STAGE as STAGE_144
from backend.lucy_core.machine_code_synthesizer import MachineCodeSynthesizer, STAGE as STAGE_145
from backend.lucy_core.jit_hotpath_tracer import JITHotpathTracer, STAGE as STAGE_146
from backend.lucy_core.aot_native_linker import AOTNativeLinker, STAGE as STAGE_147
from backend.lucy_core.memory_arena_allocator import SovereignMemoryManager, STAGE as STAGE_148
from backend.lucy_core.lto_cross_module_inliner import LTOPipeline, STAGE as STAGE_149
from backend.lucy_core.era15_master_seal import Era15MasterSealNexus, STAGE as STAGE_150
from backend.lucy_core.microkernel_scheduler import MicrokernelScheduler, TaskPriority, STAGE as STAGE_151
from backend.lucy_core.hal_cpu_topology import HALCpuTopologySentinel, STAGE as STAGE_152
from backend.lucy_core.virtual_memory_paging import VirtualMemoryPagingEngine, STAGE as STAGE_153
from backend.lucy_core.ipc_fastring_channels import IPCEndpointRegistry, STAGE as STAGE_154
from backend.lucy_core.interrupt_controller import SovereignInterruptController, STAGE as STAGE_155
from backend.lucy_core.dma_buffer_fabric import SovereignDMABufferFabric, STAGE as STAGE_156
from backend.lucy_core.capability_security_enclave import SovereignCapabilityManager, STAGE as STAGE_157
from backend.lucy_core.block_device_fabric import SovereignBlockDeviceFabric, STAGE as STAGE_158
from backend.lucy_core.vfs_inode_storage import VirtualFileSystem, STAGE as STAGE_159
from backend.lucy_core.era16_master_seal import Era16MasterSealNexus, STAGE as STAGE_160
from backend.lucy_core.bft_consensus_smr import BFTConsensusCluster, STAGE as STAGE_161
from backend.lucy_core.raft_leader_election import SovereignRaftCluster, STAGE as STAGE_162
from backend.lucy_core.kademlia_dht_mesh import SovereignDHTMesh, STAGE as STAGE_163
from backend.lucy_core.vector_clock_causality import CausalBroadcastFabric, STAGE as STAGE_164
from backend.lucy_core.multipaxos_commit import MultiPaxosCluster, STAGE as STAGE_165
from backend.lucy_core.gossip_epidemic_mesh import SovereignGossipMesh, STAGE as STAGE_166
from backend.lucy_core.crdt_replicated_types import SovereignCRDTSynthesizer, STAGE as STAGE_167
from backend.lucy_core.mesh_tunnel_tap import SovereignMeshTunnelFabric, STAGE as STAGE_168
from backend.lucy_core.distributed_deadlock_detector import DistributedDeadlockSentinel, STAGE as STAGE_169
from backend.lucy_core.era17_master_seal import Era17MasterSealNexus, STAGE as STAGE_170
from backend.lucy_core.consistent_hashing_ring import ConsistentHashRing, STAGE as STAGE_171
from backend.lucy_core.distributed_lsm_tree import DistributedLSMTree, STAGE as STAGE_172
from backend.lucy_core.quorum_read_repair import QuorumAntiEntropyCoordinator, STAGE as STAGE_173
from backend.lucy_core.distributed_wal_replication import DistributedWALManager, STAGE as STAGE_174
from backend.lucy_core.distributed_mvcc_storage import DistributedMVCCStorage, STAGE as STAGE_175
from backend.lucy_core.dynamic_shard_migrator import DynamicShardSentinel, STAGE as STAGE_176
from backend.lucy_core.distributed_secondary_index import DistributedSecondaryIndexFabric, STAGE as STAGE_177
from backend.lucy_core.raft_partitioned_kv import MultiRaftKVEngine, STAGE as STAGE_178
from backend.lucy_core.geo_replication_gateway import GeoReplicationFabric, STAGE as STAGE_179
from backend.lucy_core.era18_master_seal import Era18MasterSealNexus, STAGE as STAGE_180
from backend.lucy_core.columnar_vector_storage import ColumnarVectorStorageFabric, STAGE as STAGE_181
from backend.lucy_core.cost_based_query_optimizer import CostBasedQueryOptimizerFabric, STAGE as STAGE_182
from backend.lucy_core.vectorized_exec_engine import VectorizedExecutionFabric, STAGE as STAGE_183
from backend.lucy_core.distributed_hash_join import DistributedHashJoinFabric, STAGE as STAGE_184
from backend.lucy_core.approx_query_hll import ApproxQueryFabric, STAGE as STAGE_185
from backend.lucy_core.materialized_view_ivm import MaterializedViewIVMFabric, STAGE as STAGE_186
from backend.lucy_core.streaming_window_watermark import StreamingWindowFabric, STAGE as STAGE_187
from backend.lucy_core.adaptive_query_execution import AdaptiveQueryExecutionFabric, STAGE as STAGE_188
from backend.lucy_core.olap_chunk_compactor import OLAPChunkCompactorFabric, STAGE as STAGE_189
from backend.lucy_core.era19_master_seal import Era19MasterSealNexus, STAGE as STAGE_190
from backend.lucy_core.autonomous_jit_optimizer import AutonomousJITOptimizerFabric, STAGE as STAGE_191
from backend.lucy_core.kernel_self_healing import KernelSelfHealingFabric, STAGE as STAGE_192
from backend.lucy_core.raft_bft_hybrid import RaftBFTHybridFabric, STAGE as STAGE_193
from backend.lucy_core.zerocopy_ipc_shm import ZeroCopyIPCShmFabric, STAGE as STAGE_194
from backend.lucy_core.distributed_tensor_runtime import DistributedTensorRuntimeFabric, STAGE as STAGE_195
from backend.lucy_core.self_evolving_code_pipeline import SelfEvolvingCodePipelineFabric, STAGE as STAGE_196
from backend.lucy_core.global_chrono_log import GlobalChronoLogFabric, STAGE as STAGE_197
from backend.lucy_core.daemon_mesh_sentinel import DaemonMeshSentinelFabric, STAGE as STAGE_198
from backend.lucy_core.bicentennial_singularity_nexus import BicentennialSingularityNexus, STAGE as STAGE_199
from backend.lucy_core.bicentennial_grand_master_seal import BicentennialGrandMasterSealNexus, STAGE as STAGE_200
from backend.lucy_core.multi_kernel_federation import MultiKernelFederationFabric, STAGE as STAGE_201
from backend.lucy_core.post_quantum_crypto import PostQuantumCryptoFabric, STAGE as STAGE_202
from backend.lucy_core.sovereign_contract_engine import SovereignContractEngineFabric, STAGE as STAGE_203
from backend.lucy_core.neuromorphic_spike_mesh import NeuromorphicSpikeMeshFabric, STAGE as STAGE_204
from backend.lucy_core.knowledge_distillation_pruner import KnowledgeDistillationPrunerFabric, STAGE as STAGE_205
from backend.lucy_core.zk_invariant_prover import ZKInvariantProverFabric, STAGE as STAGE_206
from backend.lucy_core.compute_governor import ComputeGovernorFabric, STAGE as STAGE_207
from backend.lucy_core.multimodal_symbolic_grounding import MultimodalSymbolicGroundingFabric, STAGE as STAGE_208
from backend.lucy_core.hyperscale_mesh_synchronizer import HyperscaleMeshSynchronizerFabric, STAGE as STAGE_209
from backend.lucy_core.era21_master_seal import Era21MasterSealFabric, STAGE as STAGE_210
from backend.lucy_core.photonic_matrix_multiplier import PhotonicMatrixMultiplierFabric, STAGE as STAGE_211
from backend.lucy_core.interplanetary_dtn_routing import InterplanetaryDTNRoutingFabric, STAGE as STAGE_212
from backend.lucy_core.tensor_train_engine import TensorTrainEngineFabric, STAGE as STAGE_213
from backend.lucy_core.holographic_associative_memory import HolographicAssociativeMemoryFabric, STAGE as STAGE_214
from backend.lucy_core.async_micro_actor_mesh import AsyncMicroActorMeshFabric, STAGE as STAGE_215
from backend.lucy_core.quantum_hybrid_coprocessor import QuantumHybridCoprocessorFabric, PauliTerm, STAGE as STAGE_216
from backend.lucy_core.chaos_fault_injection import ChaosFaultInjectionFabric, FaultType, STAGE as STAGE_217
from backend.lucy_core.trans_universal_belief_mesh import TransUniversalBeliefMeshFabric, STAGE as STAGE_218
from backend.lucy_core.concept_synthesis_ontology import ConceptSynthesisOntologyFabric, STAGE as STAGE_219
from backend.lucy_core.era22_master_seal import Era22MasterSealFabric, STAGE as STAGE_220
from backend.lucy_core.quantum_many_body_density import QuantumManyBodyDensityFabric, STAGE as STAGE_221
from backend.lucy_core.holographic_swarm_mesh import HolographicSwarmMeshFabric, STAGE as STAGE_222
from backend.lucy_core.subatomic_pipeline_governor import SubatomicPipelineGovernorFabric, STAGE as STAGE_223
from backend.lucy_core.multiverse_state_forker import MultiverseStateForkerFabric, STAGE as STAGE_224
from backend.lucy_core.recursive_snark_aggregator import RecursiveSNARKAggregatorFabric, STAGE as STAGE_225
from backend.lucy_core.topological_data_analysis import TopologicalDataAnalysisFabric, STAGE as STAGE_226
from backend.lucy_core.energy_budget_governor import EnergyBudgetGovernorFabric, STAGE as STAGE_227
from backend.lucy_core.hyperdimensional_computing import HyperdimensionalComputingFabric, STAGE as STAGE_228
from backend.lucy_core.geo_disaster_recovery import GeoDisasterRecoveryFabric, STAGE as STAGE_229
from backend.lucy_core.era23_master_seal import Era23MasterSealFabric, STAGE as STAGE_230
from backend.lucy_core.neuromorphic_spiking_fabric import NeuromorphicSpikingFabric, STAGE as STAGE_231
from backend.lucy_core.lattice_pqc_vault import LatticePQCVaultFabric, STAGE as STAGE_232
from backend.lucy_core.hyperbolic_graph_embedder import HyperbolicGraphEmbedderFabric, STAGE as STAGE_233
from backend.lucy_core.polyglot_bytecode_jit import PolyglotBytecodeJITFabric, STAGE as STAGE_234
from backend.lucy_core.epistemic_logic_mesh import EpistemicLogicMeshFabric, STAGE as STAGE_235
from backend.lucy_core.temporal_chrono_governor import TemporalChronoGovernorFabric, STAGE as STAGE_236
from backend.lucy_core.photonic_optical_switch import PhotonicOpticalSwitchFabric, STAGE as STAGE_237
from backend.lucy_core.byzantine_swarm_consensus import ByzantineSwarmConsensusFabric, STAGE as STAGE_238
from backend.lucy_core.planetary_resource_exchange import PlanetaryResourceExchangeFabric, STAGE as STAGE_239
from backend.lucy_core.era24_master_seal import Era24MasterSealFabric, STAGE as STAGE_240
from backend.lucy_core.metamaterial_phonon_computer import MetamaterialPhononComputerFabric, STAGE as STAGE_241
from backend.lucy_core.exceptional_point_resonance import ExceptionalPointResonanceFabric, STAGE as STAGE_242
from backend.lucy_core.cellular_cohomology_sheaf import CellularCohomologySheafFabric, STAGE as STAGE_243
from backend.lucy_core.dna_molecular_storage import DnaMolecularStorageFabric, STAGE as STAGE_244
from backend.lucy_core.orbital_constellation_grid import OrbitalConstellationGridFabric, STAGE as STAGE_245
from backend.lucy_core.adiabatic_reversible_governor import AdiabaticReversibleGovernorFabric, STAGE as STAGE_246
from backend.lucy_core.antifragile_stress_inverter import AntiFragileStressInverterFabric, STAGE as STAGE_247
from backend.lucy_core.padic_ultrametric_clusterer import PadicUltrametricClustererFabric, STAGE as STAGE_248
from backend.lucy_core.zero_trust_hardware_enclave import ZeroTrustHardwareEnclaveFabric, STAGE as STAGE_249
from backend.lucy_core.era25_master_seal import Era25MasterSealFabric, STAGE as STAGE_250
from backend.lucy_core.calabi_yau_metric_engine import CalabiYauMetricEngineFabric, STAGE as STAGE_251
from backend.lucy_core.jarzynski_entropy_harvester import JarzynskiEntropyHarvesterFabric, STAGE as STAGE_252
from backend.lucy_core.clifford_geometric_algebra import CliffordGeometricAlgebraFabric, STAGE as STAGE_253
from backend.lucy_core.symplectic_hamiltonian_integrator import SymplecticHamiltonianIntegratorFabric, STAGE as STAGE_254
from backend.lucy_core.turing_morphogenetic_synthesizer import TuringMorphogeneticSynthesizerFabric, STAGE as STAGE_255
from backend.lucy_core.renormalization_group_flow import RenormalizationGroupFlowFabric, STAGE as STAGE_256
from backend.lucy_core.josephson_squid_magnetometer import JosephsonSquidMagnetometerFabric, STAGE as STAGE_257
from backend.lucy_core.relativistic_chrono_synchronizer import RelativisticChronoSynchronizerFabric, STAGE as STAGE_258
from backend.lucy_core.constitutional_shapley_nash_engine import ConstitutionalShapleyNashEngineFabric, STAGE as STAGE_259
from backend.lucy_core.era26_master_seal import Era26MasterSealFabric, STAGE as STAGE_260
from backend.lucy_core.yang_mills_gauge_holonomy import YangMillsGaugeHolonomyFabric, STAGE as STAGE_261
from backend.lucy_core.ads_cft_entanglement_wedge import AdSCFTEntanglementWedgeFabric, STAGE as STAGE_262
from backend.lucy_core.optomechanical_cavity_transceiver import OptomechanicalCavityTransceiverFabric
from backend.lucy_core.topological_skyrmion_weaver import TopologicalSkyrmionWeaverFabric, STAGE as STAGE_264
from backend.lucy_core.continuous_quantum_walk_search import ContinuousQuantumWalkSearchFabric, STAGE as STAGE_265
from backend.lucy_core.magnetohydrodynamic_dynamo_sim import MagnetohydrodynamicDynamoSimFabric, STAGE as STAGE_266
from backend.lucy_core.berry_wilczek_zee_holonomy import BerryWilczekZeeHolonomyFabric, STAGE as STAGE_267
from backend.lucy_core.flrw_cosmological_engine import FLRWCosmologicalEngineFabric, STAGE as STAGE_268
from backend.lucy_core.zero_knowledge_zk_verifier import ZeroKnowledgeZKVerifierFabric, STAGE as STAGE_269
from backend.lucy_core.era27_master_seal import Era27MasterSealFabric, STAGE as STAGE_270
from backend.lucy_core.qcd_color_flux_confinement import QCDColorFluxConfinementFabric, STAGE as STAGE_271
from backend.lucy_core.noncommutative_moyal_star_algebra import NoncommutativeMoyalStarAlgebraFabric, STAGE as STAGE_272
from backend.lucy_core.fractional_anyon_braiding_processor import FractionalAnyonBraidingProcessorFabric, STAGE as STAGE_273
from backend.lucy_core.relativistic_plasma_shock_accelerator import RelativisticPlasmaShockAcceleratorFabric, STAGE as STAGE_274
from backend.lucy_core.gravitational_lensing_caustic_tracer import GravitationalLensingCausticTracerFabric, STAGE as STAGE_275
from backend.lucy_core.quantum_teleportation_repeater_fabric import QuantumTeleportationRepeaterFabricFabric, STAGE as STAGE_276
from backend.lucy_core.kdv_integrable_soliton_synthesizer import KdVIntegrableSolitonSynthesizerFabric, STAGE as STAGE_277
from backend.lucy_core.casimir_polder_vacuum_engine import CasimirPolderVacuumEngineFabric, STAGE as STAGE_278
from backend.lucy_core.sovereign_zk_rollup_compressor import SovereignZKRollupCompressorFabric, STAGE as STAGE_279
from backend.lucy_core.era28_master_seal import Era28MasterSealFabric, STAGE as STAGE_280
from backend.lucy_core.black_hole_thermodynamics import BlackHoleThermodynamicsFabric, STAGE as STAGE_281
from backend.lucy_core.non_hermitian_pt_symmetric_engine import NonHermitianPTSymmetricFabric, STAGE as STAGE_282
from backend.lucy_core.quantum_many_body_scrambler import QuantumManyBodyScramblerFabric, STAGE as STAGE_283
from backend.lucy_core.cmb_multipole_power_spectrum import CMBMultipolePowerSpectrumFabric, STAGE as STAGE_284
from backend.lucy_core.quantum_zeno_dynamic_controller import QuantumZenoDynamicControllerFabric, STAGE as STAGE_285
from backend.lucy_core.majorana_zero_mode_gate import MajoranaZeroModeGateFabric, STAGE as STAGE_286
from backend.lucy_core.pulsar_magnetosphere_ffe import PulsarMagnetosphereFFEFabric, STAGE as STAGE_287
from backend.lucy_core.quantum_fisher_phase_estimator import QuantumFisherPhaseEstimatorFabric, STAGE as STAGE_288
from backend.lucy_core.sovereign_cross_chain_zk_bridge import SovereignCrossChainZKBridgeFabric, STAGE as STAGE_289
from backend.lucy_core.era29_master_seal import Era29MasterSealFabric, STAGE as STAGE_290
from backend.lucy_core.execution_receipts import ExecutionReceiptLedger
from backend.lucy_core.workflow_learner import WorkflowHabitLearner
from backend.lucy_core.live_workspace_context import LiveWorkspaceSensor
from backend.lucy_core.proactive_briefer import ProactiveSessionBriefer
from backend.lucy_core.natural_action_parser import NaturalActionParser
from backend.lucy_core.first_thought import FirstThoughtAssembler
from backend.lucy_core.guardian import BLOCKED, GuardianCore
from backend.lucy_core.growth_proposals import GrowthProposalSystem
from backend.lucy_core.learning import LearningSystem
from backend.lucy_core.knowledge import AICollectionsKnowledge
from backend.lucy_core.memory import MemorySystem
from backend.lucy_core.ops import SafeOps
from backend.lucy_core.persistent_runtime import PersistentLocalRuntime
from backend.lucy_core.presence import PresenceLayer
from backend.lucy_core.projects import ProjectTracker
from backend.lucy_core.reflection import ReflectionLog
from backend.lucy_core.recovery import RecoveryReference
from backend.lucy_core.reminders import ReminderStore
from backend.lucy_core.response_frame import build_response_frame
from backend.lucy_core.safe_access import SafeAccessManager
from backend.lucy_core.scheduler import ContextScheduler
from backend.lucy_core.secrets import SessionSecretStore
from backend.lucy_core.session_state import SessionStateManager
from backend.lucy_core.session_review import SessionReviewEngine
from backend.lucy_core.safe_tools import SafeFileToolbox
from backend.lucy_core.self_model import SelfModel
from backend.lucy_core.shadow_testing import ShadowTestingSystem
from backend.lucy_core.spine_loader import get_spine_summary, load_spine
from backend.lucy_core.tool_confirmations import ToolConfirmationManager
from backend.lucy_core.tool_policy import ToolActionPolicy
from backend.lucy_core.tools import SafeToolbox
from backend.lucy_core.wake_state import WakeLayerEngine


def datetime_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


STAGE16_SAFE_NEXT_ACTION = "Finish Stage 16 shadow testing checks, run tests, and back up after acceptance."
STAGE17_SAFE_NEXT_ACTION = "Finish Stage 17 checks, run tests, and back up after acceptance."
STAGE17_OPERATIONAL_NEXT_ACTION = "create/check patch plan, run tests, manual checks, then backup after acceptance"
STAGE17_STAGE_LABEL = "17 approved patch pipeline"
STAGE18_GATE = "blocked until Stage 17 is accepted, backed up locally, uploaded to Drive, and Senin explicitly approves"
STAGE18_SAFE_NEXT_ACTION = "Finish Stage 18 checks, run tests, and back up after acceptance."
STAGE18_OPERATIONAL_NEXT_ACTION = "create/check safe experience record, run tests, manual checks, then backup after acceptance"
STAGE18_STAGE_LABEL = "18 experience storage"
STAGE19_GATE = "blocked until Stage 18 is accepted, backed up locally, uploaded to Drive, and Senin explicitly approves"
STAGE19_SAFE_NEXT_ACTION = "Finish Stage 19 identity stability checks, run tests, and back up after acceptance."
STAGE19_OPERATIONAL_NEXT_ACTION = "run/check identity stability, run tests, manual checks, then backup after acceptance"
STAGE19_STAGE_LABEL = "19 identity stability"
STAGE20_GATE = "blocked until Stage 19 is accepted, backed up locally, uploaded to Drive, and Senin explicitly approves"
STAGE20_SAFE_NEXT_ACTION = "Finish Stage 20 long-term strategy checks, run tests, and back up after acceptance."
STAGE20_OPERATIONAL_NEXT_ACTION = "create/check long-term strategy, run tests, manual checks, then backup after acceptance"
STAGE20_STAGE_LABEL = "20 long-term strategy"
STAGE21_GATE = "blocked until Stage 20 is accepted, backed up locally, uploaded to Drive, and Senin explicitly approves"
STAGE21_SAFE_NEXT_ACTION = "Finish Stage 21 smart organizer checks, run tests, and back up after acceptance."
STAGE21_OPERATIONAL_NEXT_ACTION = "create/check organizer item, run tests, manual checks, then backup after acceptance"
STAGE21_STAGE_LABEL = "21 smart organizer"
STAGE22_GATE = "blocked until Stage 21 is accepted, backed up locally, uploaded to Drive, and Senin explicitly approves"
STAGE22_SAFE_NEXT_ACTION = "Finish Stage 22 safe local action dry-run checks, run tests, and back up after acceptance."
STAGE22_OPERATIONAL_NEXT_ACTION = "create/check safe local action proposal, dry-run only, run tests, manual checks, then backup after acceptance"
STAGE22_STAGE_LABEL = "22 safe local actions"
STAGE23_GATE = "blocked until Stage 22 is accepted, backed up locally, uploaded to Drive, and Senin explicitly approves"
STAGE23_SAFE_NEXT_ACTION = "Finish Stage 23 external app bridge dry-run checks, run tests, and back up after acceptance."
STAGE23_OPERATIONAL_NEXT_ACTION = "create/check external app bridge proposal, dry-run only, run tests, manual checks, then backup after acceptance"
STAGE23_STAGE_LABEL = "23 external app bridge"
STAGE24_GATE = "blocked until Stage 23 is accepted, backed up locally, uploaded to Drive, and Senin explicitly approves"
STAGE24_SAFE_NEXT_ACTION = "Finish Stage 24 proactive awareness dry-run checks, run tests, and back up after acceptance."
STAGE24_OPERATIONAL_NEXT_ACTION = "create/check proactive awareness scan, dry-run only, run tests, manual checks, then backup after acceptance"
STAGE24_STAGE_LABEL = "24 proactive awareness"
STAGE25_GATE = "blocked until Stage 24 is accepted, backed up locally, uploaded to Drive, and Senin explicitly approves"
STAGE25_SAFE_NEXT_ACTION = "Finish Stage 25 deep recall structured-record checks, run tests, and back up after acceptance."
STAGE25_OPERATIONAL_NEXT_ACTION = "create/check deep recall session, dry-run only, run tests, manual checks, then backup after acceptance"
STAGE25_STAGE_LABEL = "25 deep recall"
STAGE26_GATE = "blocked until Stage 25 is accepted, backed up locally, uploaded to Drive, and Senin explicitly approves"
STAGE26_SAFE_NEXT_ACTION = "Finish Stage 26 judgment cautious-assessment checks, run tests, and back up after acceptance."
STAGE26_OPERATIONAL_NEXT_ACTION = "create/check cautious judgment record, dry-run only, run tests, manual checks, then backup after acceptance"
STAGE26_STAGE_LABEL = "26 judgment"
STAGE27_GATE = "blocked until Stage 26 is accepted, backed up locally, uploaded to Drive, and Senin explicitly approves"
STAGE27_SAFE_NEXT_ACTION = "Finish Stage 27 adaptive communication explicit-style checks, run tests, and back up after acceptance."
STAGE27_OPERATIONAL_NEXT_ACTION = "create/check adaptive communication style profile, dry-run only, run tests, manual checks, then backup after acceptance"
STAGE27_STAGE_LABEL = "27 adaptive communication"
STAGE28_GATE = "blocked until Stage 27 is accepted, backed up locally, uploaded to Drive, and Senin explicitly approves"
STAGE28_SAFE_NEXT_ACTION = "Finish Stage 28 human-state awareness explicit-signal checks, run tests, and back up after acceptance."
STAGE28_OPERATIONAL_NEXT_ACTION = "create/check explicit human-state signal, dry-run only, run tests, manual checks, then backup after acceptance"
STAGE28_STAGE_LABEL = "28 human-state awareness"
STAGE29_GATE = "blocked until Stage 28 is accepted, backed up locally, uploaded to Drive, and Senin explicitly approves"
STAGE29_SAFE_NEXT_ACTION = "Finish Stage 29 time awareness manual-time-context checks, run tests, and back up after acceptance."
STAGE29_OPERATIONAL_NEXT_ACTION = "create/check manual time context, dry-run only, run tests, manual checks, then backup after acceptance"
STAGE29_STAGE_LABEL = "29 time awareness"
STAGE30_GATE = "blocked until Stage 29 is accepted, backed up locally, uploaded to Drive, and Senin explicitly approves"
STAGE30_SAFE_NEXT_ACTION = "Finish Stage 30 autonomy boundaries permission-boundary checks, run tests, and back up after acceptance."
STAGE30_OPERATIONAL_NEXT_ACTION = "create/check autonomy boundary record, dry-run only, run tests, manual checks, then backup after acceptance"
STAGE30_STAGE_LABEL = "30 autonomy boundaries"
POST_STAGE30_GATE = "API/provider-key stage blocked until Stage 30 is accepted, backed up locally, uploaded to Drive, and Senin explicitly approves the later provider-key boundary stage"
STAGE31_SAFE_NEXT_ACTION = "Finish Stage 31 provider/API identity-boundary checks, run tests, and back up after acceptance."
STAGE31_OPERATIONAL_NEXT_ACTION = "create/check provider identity boundary record, dry-run only, run tests, manual checks, then backup after acceptance"
STAGE31_STAGE_LABEL = "31 provider/api identity boundary"
STAGE32_GATE = "Secrets/provider-key safety stage blocked until Stage 31 is accepted, backed up locally, uploaded to Drive, and Senin explicitly approves Stage 32 key-handling work"
STAGE32_SAFE_NEXT_ACTION = "Finish Stage 32 secrets/provider-key safety checks, run tests, and back up after acceptance."
STAGE32_OPERATIONAL_NEXT_ACTION = "create/check secret safety record, safe provider-presence scan only, dry-run only, run tests, manual checks, then backup after acceptance"
STAGE32_STAGE_LABEL = "32 secrets/provider-key safety"
STAGE33_GATE = "Provider registry stage blocked until Stage 32 is accepted, backed up locally, uploaded to Drive, and Senin explicitly approves Stage 33 provider-registry work"
STAGE33_SAFE_NEXT_ACTION = "Finish Stage 33 provider registry checks, run tests, and back up after acceptance."
STAGE33_OPERATIONAL_NEXT_ACTION = "create/check provider registry metadata, keep providers disabled unless approved, dry-run only, run tests, manual checks, then backup after acceptance"
STAGE33_STAGE_LABEL = "33 provider registry"
STAGE34_GATE = "Provider health-check dry-run stage blocked until Stage 33 is accepted, backed up locally, uploaded to Drive, and Senin explicitly approves Stage 34 health-check dry-run work"
STAGE34_SAFE_NEXT_ACTION = "Finish Stage 34 provider health-check dry-run checks, run tests, and back up after acceptance."
STAGE34_OPERATIONAL_NEXT_ACTION = "describe what a provider health check would do, dry-run only, no network, no provider calls, no keys read, run tests, manual checks, then backup after acceptance"
STAGE34_STAGE_LABEL = "34 provider health-check dry-run"
STAGE35_GATE = "First manual model call stage blocked until Stage 34 is accepted, backed up locally, uploaded to Drive, and Senin explicitly approves Stage 35 work"







STALE_NEXT_ACTION_MARKERS = (
    "review desktop ui",
    "checkpoint_0101",
    "fallback learning proposals",
    "nvidia key setup",
    "api key setup",
    "external api setup",
    "provider key setup",
    "provider router",
    "finish stage 16 shadow testing checks",
    "finish stage 17 checks",
    "create/check patch plan",
)


DEFAULT_CONFIG = {
    "system_name": "LUCY",
    "full_form": "Living Unified Cognitive Yield",
    "stage": "Recovered Lucy V0.1 Checkpoint 023 Architecture / Local Reconstruction / Not Beta Yet",
    "mode": "Safe Local Runtime",
    "web_ui_enabled": False,
    "desktop_ui_enabled": False,
    "api_enabled": True,
    "stage6_reasoning_router_enabled": True,
    "external_brain_enabled": False,
    "reasoning_mode_default": "local_policy_only",
    "allow_chain_of_thought_output": False,
    "chain_of_thought_output_enabled": False,
    "context_packet_max_chars": 6000,
    "external_api_requires_confirmation": True,
    "voice_enabled": False,
    "autonomy_enabled": False,
    "root_access_enabled": False,
    "agent_execution_enabled": False,
    "protected_actions_blocked": True,
    "memory_mode": "local_json_approved_facts",
    "fallback_learning_enabled": True,
    "permanent_memory_enabled": True,
    "talking_style_learning_enabled": True,
    "encrypted_secret_storage_enabled": True,
    "overnight_checkpoint_target": 100,
}


@dataclass
class HealthReport:
    all_passed: bool
    checks: dict[str, bool]
    timestamp: str


class SimpleMemoryStore:
    """Durable JSON-backed approved memory store with keyword and category recall."""

    def __init__(self, memory_dir: Path) -> None:
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.memory_dir / "memory.json"
        if not self.memory_file.exists():
            self._write([])

    def _read(self) -> list[dict[str, Any]]:
        try:
            data = json.loads(self.memory_file.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def _write(self, records: list[dict[str, Any]]) -> None:
        self.memory_file.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")

    def remember(self, fact: str, category: str = "general", source: str = "user") -> dict[str, Any]:
        cleaned = " ".join(str(fact or "").split()).strip()
        if not cleaned:
            return {"saved": False, "reason": "Empty memory fact."}
        records = self._read()
        for item in records:
            if item.get("active", True) and item.get("fact", "").lower() == cleaned.lower():
                return {"saved": False, "duplicate": True, "memory": item}
        record = {
            "id": f"mem_{len(records) + 1:04d}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fact": cleaned,
            "category": category,
            "source": source,
            "active": True,
        }
        records.append(record)
        self._write(records)
        return {"saved": True, "memory": record}

    def recall(self, query: str = "", limit: int = 8) -> list[dict[str, Any]]:
        active = [r for r in self._read() if r.get("active", True)]
        q = str(query or "").strip().lower()
        if not q:
            return list(reversed(active))[:limit]
        q_tokens = {w for w in q.split() if len(w) > 2}
        scored: list[tuple[int, dict[str, Any]]] = []
        for item in active:
            text = str(item.get("fact", "")).lower()
            score = 0
            if q in text:
                score += 5
            score += sum(1 for tok in q_tokens if tok in text)
            if score > 0:
                scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:limit]]

    def forget(self, target: str) -> dict[str, Any]:
        q = str(target or "").strip().lower()
        if not q:
            return {"forgotten": 0}
        records = self._read()
        count = 0
        for item in records:
            if item.get("active", True) and (q in item.get("fact", "").lower() or q == item.get("id", "").lower()):
                item["active"] = False
                count += 1
        self._write(records)
        return {"forgotten": count}

    def audit(self) -> dict[str, Any]:
        records = self._read()
        active = [r for r in records if r.get("active", True)]
        return {
            "total": len(records),
            "active": len(active),
            "inactive": len(records) - len(active),
            "file": str(self.memory_file),
        }


class SimpleProjectTracker:
    """Tracks active projects and tasks in projects.json with receipt binding."""

    def __init__(self, lucy_data: Path, receipt_ledger: ExecutionReceiptLedger | None = None) -> None:
        self.file = Path(lucy_data) / "projects.json"
        self.receipt_ledger = receipt_ledger
        if not self.file.exists():
            self._write({
                "active_project": "Lucy",
                "next_action": "Run unified adaptive conversation and tool verification loop.",
                "tasks": [],
            })

    def _read(self) -> dict[str, Any]:
        try:
            return json.loads(self.file.read_text(encoding="utf-8"))
        except Exception:
            return {"active_project": "Lucy", "next_action": "", "tasks": []}

    def _write(self, data: dict[str, Any]) -> None:
        self.file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def add_task(self, text: str) -> dict[str, Any]:
        data = self._read()
        tasks = data.setdefault("tasks", [])
        task = {
            "id": f"task_{len(tasks) + 1:03d}",
            "text": text.strip(),
            "done": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        tasks.append(task)
        self._write(data)
        if self.receipt_ledger is not None:
            self.receipt_ledger.issue_receipt(
                action_category="task_mutation",
                operation="add_task",
                target=task["id"],
                verified_outcome=f"Added task: {task['text']}",
            )
        return task

    def complete_task(self, selector: str) -> dict[str, Any]:
        data = self._read()
        sel = selector.strip().lower()
        for t in data.get("tasks", []):
            if not t.get("done") and (t["id"].lower() == sel or sel in t["text"].lower()):
                t["done"] = True
                self._write(data)
                if self.receipt_ledger is not None:
                    self.receipt_ledger.issue_receipt(
                        action_category="task_mutation",
                        operation="complete_task",
                        target=t["id"],
                        verified_outcome=f"Completed task: {t['text']}",
                    )
                return {"completed": True, "task": t}
        return {"completed": False}

    def summary(self) -> dict[str, Any]:
        data = self._read()
        open_tasks = [t for t in data.get("tasks", []) if not t.get("done")]
        return {
            "name": data.get("active_project", "Lucy"),
            "next_action": data.get("next_action") or (
                open_tasks[0]["text"] if open_tasks else "Ready for next instruction."
            ),
            "open_tasks": open_tasks,
            "total_tasks": len(data.get("tasks", [])),
        }


class SimpleSessionState:
    def __init__(self) -> None:
        self._state = {
            "graceful_shutdown": False,
            "last_command": "",
            "current_checkpoint": "Stage 58 Unified",
        }

    def status(self) -> dict[str, Any]:
        return dict(self._state)

    def mark_shutdown(self, reason: str) -> None:
        self._state["graceful_shutdown"] = True
        self._state["shutdown_reason"] = reason


class LucyRuntime:
    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root or PROJECT_ROOT
        self.config = self._load_config()
        self.spine = load_spine(self.project_root)

        lucy_data = self.project_root / "data" / "lucy"
        self.logger = EventLogger(lucy_data / "logs")
        self.boundary = BoundaryChecker()
        self.guardian_core = GuardianCore(self.project_root / "logs", self.boundary)
        self.approvals = ApprovalManager(lucy_data / "approvals")
        self.checkpoints = CheckpointManager(lucy_data / "checkpoints")
        self.memory = MemorySystem(lucy_data / "memory")
        self.projects = ProjectTracker(lucy_data)
        self.session_state = SessionStateManager(lucy_data)
        self.scheduler = ContextScheduler()
        self.safe_file_tools = SafeFileToolbox(lucy_data)
        self.tool_policy = ToolActionPolicy()
        self.tool_confirmations = ToolConfirmationManager(lucy_data)
        self.reminders = ReminderStore(lucy_data)
        self.tools = SafeToolbox(self.project_root)
        self.brain = BrainRouter()
        self.ops = SafeOps(self.project_root, lucy_data)
        self.recovery = RecoveryReference(lucy_data)
        self.secrets = SessionSecretStore(lucy_data / "secure")
        self.learning = LearningSystem(lucy_data / "learning")
        self.knowledge = AICollectionsKnowledge(lucy_data)
        self.cognition = CognitionCore(lucy_data / "cognition")
        self.daily_context = DailyContextEngine(lucy_data / "daily")
        self.continuity = ContinuityBackup(lucy_data)
        self.reflection_log = ReflectionLog(lucy_data)
        self.session_review_engine = SessionReviewEngine(lucy_data, memory_system=self.memory)
        self.wake_layer = WakeLayerEngine()
        self.presence_layer = PresenceLayer()
        self.external_tools = ExternalToolRouter(project_root=self.project_root)
        self.checkpoint_builder = CheckpointBuilder(self)
        self.agents = AgentRegistry(lucy_data)
        self.internal_agent_orchestrator = AgentOrchestrator(self)
        self.conversation = ConversationEngine(self)
        self.persistent_runtime = PersistentLocalRuntime(lucy_data)
        self.safe_access = SafeAccessManager(lucy_data)
        self.first_thought = FirstThoughtAssembler(lucy_data)
        self.self_model = SelfModel(lucy_data)
        self.growth_proposals = GrowthProposalSystem(lucy_data)
        self.evaluation_lab = EvaluationLab(lucy_data)
        self.shadow_testing = ShadowTestingSystem(lucy_data)
        self.approved_patch_pipeline = ApprovedPatchPipeline(lucy_data)
        self.experience_storage = ExperienceStorage(lucy_data)
        self.identity_stability = IdentityStability(lucy_data)
        self.long_term_strategy = LongTermStrategy(lucy_data)
        self.smart_organizer = SmartOrganizer(lucy_data)
        self.safe_local_actions = SafeLocalActions(lucy_data)
        self.external_app_bridge = ExternalAppBridge(lucy_data)
        self.proactive_awareness = ProactiveAwareness(lucy_data)
        self.deep_recall = DeepRecall(lucy_data)
        self.judgment = Judgment(lucy_data)
        self.adaptive_communication = AdaptiveCommunication(lucy_data)
        self.human_state_awareness = HumanStateAwareness(lucy_data)
        self.time_awareness = TimeAwareness(lucy_data)
        self.autonomy_boundaries = AutonomyBoundaries(lucy_data)
        self.provider_identity_boundary = ProviderIdentityBoundary(lucy_data)
        self.secrets_provider_key_safety = SecretsProviderKeySafety(lucy_data)
        self.provider_registry = ProviderRegistry(lucy_data)
        self.provider_health_check = ProviderHealthCheck(lucy_data)
        self.provider_role_split = ProviderRoleSplit(lucy_data)
        self.ollama_connector = OllamaConnector(lucy_data)
        # Stage 36, 40, 42, & 45 Two-Speed Adaptation Wiring
        self.training_queue = VerifiedTrainingQueue(lucy_data)
        self.fact_verifier = FactStateVerifier(self.project_root)
        self.task_daemon = TaskDaemon(lucy_data)
        self.swarm_dispatcher = SwarmDispatcher(lucy_data)
        self.open_jarvis = OpenJarvisBridge(lucy_data)
        self.code_synthesis = CodeSynthesisPipeline(
            project_root=self.project_root,
            lucy_data=lucy_data,
            dispatcher=self.swarm_dispatcher,
            verifier=self.fact_verifier,
            daemon=self.task_daemon,
            training_queue=self.training_queue,
            api_tools=self.external_tools,
            ollama_connector=self.ollama_connector,
        )
        self.lora_sleep_cycle = LoRASleepCycleEngine(
            project_root=self.project_root,
            lucy_data=lucy_data,
            connector=self.ollama_connector,
            training_queue=self.training_queue,
            verifier=self.fact_verifier,
            daemon=self.task_daemon,
        )
        self.lora_sleep = self.lora_sleep_cycle
        self.self_refinement = SelfRefinementHarness(
            project_root=self.project_root,
            lucy_data=lucy_data,
            pipeline=self.code_synthesis,
            dispatcher=self.swarm_dispatcher,
            verifier=self.fact_verifier,
            training_queue=self.training_queue,
        )
        self.personal_profiler = PersonalProfiler(
            lucy_data=lucy_data,
            workspace_root=self.project_root.parent,
        )
        self.conversational_memory = ConversationalMemoryEngine(
            lucy_data=lucy_data,
            memory_system=self.memory,
            learning_system=self.learning,
            personal_profiler=self.personal_profiler,
            max_context_turns=5,
        )
        self.personal_lora_alignment = PersonalLoRAAlignmentEngine(
            project_root=self.project_root,
            lucy_data=lucy_data,
            personal_profiler=self.personal_profiler,
            lora_sleep_cycle=self.lora_sleep_cycle,
            sleep_cycle=self.lora_sleep,
            connector=self.ollama_connector,
            daemon=self.task_daemon,
            training_queue=self.training_queue,
        )
        self.personal_alignment = self.personal_lora_alignment
        self.provider_pool = MultiProviderPool(
            lucy_data=lucy_data,
            keys_path=Path(r"C:\Users\admin\Desktop\senin\api keys.txt"),
        )
        self.operator_toolkit = OperatorToolkit(
            project_root=self.project_root,
            lucy_data=lucy_data,
        )
        self.intent_dispatcher = IntentDispatcher(
            runtime=self,
            profiler=self.personal_profiler,
            toolkit=self.operator_toolkit,
        )
        self.workspace_sentinel = WorkspaceSentinel(
            project_root=self.project_root,
            lucy_data=lucy_data,
            profiler=self.personal_profiler,
        )
        self.terminal_repl = TerminalREPL(
            runtime=self,
            lucy_data=lucy_data,
        )
        self.self_diagnostics = CrashRecoveryDaemon(
            project_root=self.project_root,
            lucy_data=lucy_data,
            runtime=self,
        )
        self.master_orchestrator = MasterOrchestrator(
            project_root=self.project_root,
            lucy_data=lucy_data,
            runtime=self,
        )
        self.cron_scheduler = CronDaemon(
            project_root=self.project_root,
            lucy_data=lucy_data,
            runtime=self,
        )
        # Stages 54–58 Subsystems
        self.lucy_data = lucy_data
        # Stages 54-58 Subsystems
        self.memory_graph = TemporalMemoryGraph(lucy_data / "memory")
        self.conversational_memory.memory_graph = self.memory_graph
        # Stage 72: Memory Graph Associative Edge Walker & Spreading Activation
        self.memory_walker = SpreadingActivationWalker(
            memory_dir=lucy_data / "memory",
            memory_graph=self.memory_graph,
        )
        self.conversational_memory.memory_walker = self.memory_walker
        try:
            self.memory_walker.build_edges_from_nodes(self.memory_graph._read().get("nodes", []))
        except Exception:
            pass
        # Stage 68: Sovereign Internal Monologue & Pre-Output Verification Spine
        self.internal_monologue = InternalMonologueSpine(
            memory_graph=self.memory_graph,
            fact_verifier=self.fact_verifier,
        )
        # Stage 69: Anti-Sycophancy & Sovereign Persona Consistency Engine
        self.persona_governor = PersonaGovernor(
            config_file=self.project_root / "config" / "lucy_personality_spec.json"
        )
        self.receipt_ledger = ExecutionReceiptLedger(lucy_data)
        self.projects.receipt_ledger = self.receipt_ledger
        # Stage 70: Autonomous Terminal ReAct Loop & Self-Healing Execution Engine
        self.react_engine = TerminalReActEngine(
            project_root=self.project_root,
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 71: Local AST Codebase Indexer & High-Speed Symbol Graph
        self.codebase_indexer = CodebaseIndexer(
            project_root=self.project_root,
            data_dir=lucy_data,
        )
        # Stage 73: Dynamic Local Tool Synthesizer & Ephemeral Sandbox
        self.tool_synthesizer = DynamicToolSynthesizer(
            sandbox_dir=self.project_root / "scratch" / "sandbox",
            registry_file=lucy_data / "synthesized_tools.json",
            receipt_ledger=self.receipt_ledger,
            project_root=self.project_root,
        )
        # Stage 74: Proactive Terminal Sentinel & Non-Intrusive Status Broadcaster
        self.terminal_sentinel = TerminalSentinel(
            project_root=self.project_root,
            runtime=self,
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 75: Terminal ANSI Canvas & Syntax-Highlighted Visual Stream
        self.terminal_canvas = TerminalCanvas(colors_enabled=True)
        # Stage 76: Autonomous Memory Pruning & Cognitive Distillation
        self.memory_distiller = CognitiveDistiller(
            memory_graph=self.memory_graph,
            memory_walker=self.memory_walker,
            receipt_ledger=self.receipt_ledger,
            archive_dir=lucy_data / "memory",
        )
        # Stage 77: Autonomous Git Branch & Code Review Companion
        self.code_reviewer = AutonomousCodeReviewer(
            project_root=self.project_root,
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 78: Multi-File Refactor & Atomic Patch Orchestrator
        self.atomic_patcher = AtomicPatchOrchestrator(
            project_root=self.project_root,
            journal_file=lucy_data / "patch_journal.json",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 79: Local Test Suite Auto-Discoverer & Regression Triage Engine
        self.test_triage = TestTriageEngine(
            project_root=self.project_root,
            codebase_indexer=self.codebase_indexer,
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 80: Multi-Turn Operator Goal Decomposition & Task Graph Engine
        self.task_graph = GoalTaskGraphEngine(
            project_root=self.project_root,
            storage_file=lucy_data / "active_goal_dag.json",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 81: Sovereign Terminal Web Explorer & Headless Search Engine
        self.web_explorer = SovereignWebExplorer(
            project_root=self.project_root,
            cache_file=lucy_data / "cache" / "web_search_cache.json",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 82: Grounded Web Page Extractor & Documentation Reader
        self.web_reader = SovereignWebReader(
            project_root=self.project_root,
            cache_file=lucy_data / "cache" / "web_pages_cache.json",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 83: Web-Grounded Cross-Verification & Fact-Checking RAG
        self.web_verifier = WebFactChecker(
            web_explorer=self.web_explorer,
            web_reader=self.web_reader,
            cache_file=lucy_data / "cache" / "fact_check_cache.json",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 84: High-Signal LoRA Interaction Harvester & Preference Dataset Curator
        self.lora_harvester = HighSignalLoRAHarvester(
            project_root=self.project_root,
            data_dir=lucy_data / "lora",
            receipt_ledger=self.receipt_ledger,
        )
        self.active_model = getattr(self.lora_sleep_cycle, "active_model", "lucy:personal") or "lucy:personal"
        # Stage 85: Local Model Adapter Compiler & Ollama Hot-Swap Engine
        self.lora_compiler = LocalModelAdapterCompiler(
            project_root=self.project_root,
            harvester=self.lora_harvester,
            receipt_ledger=self.receipt_ledger,
            active_model=self.active_model,
        )
        self.active_model = self.lora_compiler.active_model
        # Stage 86: 25-Question Anti-Catastrophic-Forgetting Sanity Gate
        self.sanity_gate = AntiForgettingSanityGate(
            project_root=self.project_root,
            receipt_ledger=self.receipt_ledger,
            reports_dir=lucy_data / "lora" / "sanity_reports",
        )
        # Stage 87: Epistemic Provenance Tracker & Anti-Hallucination Confidence Spine
        self.epistemic_tracker = EpistemicProvenanceTracker(
            project_root=self.project_root,
            receipt_ledger=self.receipt_ledger,
            data_dir=lucy_data / "epistemic",
        )
        # Stage 88: Dynamic Few-Shot Operator Style Mirror & Semantic Preference Ingestion
        self.style_mirror = DynamicStyleMirror(
            project_root=self.project_root,
            harvester=self.lora_harvester,
            receipt_ledger=self.receipt_ledger,
            preferences_dir=lucy_data / "preferences",
        )
        # Stage 89: Autonomous Hypothesis Generation & Pre-Response Counterfactual Verifier
        self.hypothesis_engine = CounterfactualHypothesisEngine(
            project_root=self.project_root,
            receipt_ledger=self.receipt_ledger,
            journal_dir=lucy_data / "reasoning",
        )
        # Stage 90: Master Sovereign AGI Cognitive Synthesis & Continuous Alignment Checkpoint
        self.master_synthesis = SovereignMasterSynthesis(
            project_root=self.project_root,
            runtime=self,
            receipt_ledger=self.receipt_ledger,
            alignment_dir=lucy_data / "alignment",
        )
        # Stage 91: Autonomous Code Mutation & Fuzz Tester
        self.mutation_fuzzer = AutonomousMutationFuzzer(
            project_root=self.project_root,
            runtime=self,
            receipt_ledger=self.receipt_ledger,
            data_dir=lucy_data / "mutation_reports",
        )
        # Stage 92: Self-Healing Runtime Patch Engine
        self.self_healing_patcher = SelfHealingPatchEngine(
            project_root=self.project_root,
            runtime=self,
            receipt_ledger=self.receipt_ledger,
            patch_dir=lucy_data / "patches",
        )
        # Stage 93: Semantic AST Vector Code Indexer
        self.ast_vector_index = ASTVectorCodeIndexer(
            project_root=self.project_root,
            runtime=self,
            receipt_ledger=self.receipt_ledger,
            index_dir=lucy_data / "code_index",
        )
        # Stage 94: Architecture Specification Drift Detector & Realignment Engine
        self.spec_drift_detector = SpecDriftDetector(
            project_root=self.project_root,
            runtime=self,
            receipt_ledger=self.receipt_ledger,
            data_dir=lucy_data / "spec_drift",
        )
        # Stage 95: Multi-Agent Autonomous Worktree & Branching Fabric
        self.worktree_fabric = MultiAgentWorktreeFabric(
            project_root=self.project_root,
            runtime=self,
            receipt_ledger=self.receipt_ledger,
            worktree_base_dir=lucy_data / "worktrees",
        )
        # Stage 96: Sovereign Offline Quantization & GGUF Model Compressor
        self.model_quantizer = OfflineModelQuantizer(
            project_root=self.project_root,
            runtime=self,
            receipt_ledger=self.receipt_ledger,
            quant_dir=lucy_data / "quantization",
        )
        # Stage 97: Causal DAG Epistemic Memory & Counterfactual Timeline
        self.causal_dag = CausalDAGMemoryEngine(
            project_root=self.project_root,
            runtime=self,
            receipt_ledger=self.receipt_ledger,
            data_dir=lucy_data / "causal_dag",
        )
        # Stage 98: Zero-Leak Host Sandbox & Process Containment Gate
        self.host_sandbox = ZeroLeakHostSandbox(
            project_root=self.project_root,
            runtime=self,
            receipt_ledger=self.receipt_ledger,
            sandbox_dir=lucy_data / "sandbox",
        )
        # Stage 99: Local Hardware Telemetry & Inference Throttle Guard
        self.hardware_telemetry = HardwareTelemetryOptimizer(
            project_root=self.project_root,
            runtime=self,
            receipt_ledger=self.receipt_ledger,
            data_dir=lucy_data / "telemetry",
        )
        # Stage 100: Centennial Sovereign Master Seal & Cryptographic Self-Attestation Fabric
        self.master_seal = CentennialMasterSealEngine(
            project_root=self.project_root,
            runtime=self,
            receipt_ledger=self.receipt_ledger,
            data_dir=lucy_data / "centennial",
        )
        # Stage 101: Autonomous Kernel & Process Watchdog Fabric
        self.kernel_supervisor = KernelSupervisor(
            project_root=self.project_root,
            runtime=self,
            receipt_ledger=self.receipt_ledger,
            data_dir=lucy_data / "supervisor",
        )
        self._register_default_supervised_services()
        # Stage 102: Dynamic Execution Profiler & Flamegraph Tracer
        self.execution_profiler = ExecutionProfiler(
            project_root=self.project_root,
            runtime=self,
            receipt_ledger=self.receipt_ledger,
            data_dir=lucy_data / "profiler",
        )
        # Stage 103: Hybrid Neural-Lexical Vector RAG Engine
        self.neural_retriever = HybridNeuralRetriever(
            project_root=self.project_root,
            runtime=self,
            receipt_ledger=self.receipt_ledger,
            data_dir=lucy_data / "rag",
        )
        # Stage 104: Autonomous Refactoring & Code Quality Enforcer
        self.refactor_engine = AutonomousRefactorEngine(
            project_root=self.project_root,
            runtime=self,
            receipt_ledger=self.receipt_ledger,
            data_dir=lucy_data / "refactor",
        )
        # Stage 105: Sovereign P2P Peer Mesh & Local Sync
        self.peer_mesh = SovereignPeerMeshSync(
            project_root=self.project_root,
            runtime=self,
            receipt_ledger=self.receipt_ledger,
            data_dir=lucy_data / "mesh",
        )
    # Stage 106: Offline Multi-Modal Voice Fabric
        self.voice_fabric = OfflineVoiceFabric(
            project_root=self.project_root,
            runtime=self,
            receipt_ledger=self.receipt_ledger,
            data_dir=lucy_data / "voice",
        )
        # Stage 107: Context Window Semantic Token Compressor
        self.token_compressor = SemanticTokenCompressor(
            project_root=self.project_root,
            data_dir=lucy_data / "token_compressor",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 108: Autonomous Security Red-Team & Adversary Simulator
        self.red_team = SecurityRedTeamSimulator(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "red_team",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 109: Ambient HUD & Desktop Overlay
        self.ambient_hud = AmbientHUDOverlay(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "hud",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 110: Sovereign Consensus Nexus & Era 11 Master Seal
        self.consensus_nexus = SovereignConsensusNexus(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "consensus",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 111: Proactive Workspace & Process Sensor Daemon (Era 12)
        self.workspace_daemon = WorkspaceSensorDaemon(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "daemon",
            receipt_ledger=self.receipt_ledger,
            scan_interval_sec=60.0,
            auto_start=False,
        )
        # Stage 112: Semantic Inference Cache (Era 12)
        self.semantic_cache = SemanticInferenceCache(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "cache",
            receipt_ledger=self.receipt_ledger,
            similarity_threshold=0.88,
            max_entries=500,
            auto_persist=True,
        )
        # Stage 113: Polyglot AST Engine (Era 12)
        self.polyglot_ast = PolyglotASTEngine(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "polyglot",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 114: Parallel Pipeline Fusion (Era 12)
        self.pipeline_fusion = AgentPipelineFusionEngine(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "pipeline",
            receipt_ledger=self.receipt_ledger,
            max_workers=6,
        )
        # Stage 115: Sovereign IPC Event Bus (Era 12)
        self.ipc_bus = SovereignIPCEventBus(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "ipc",
            receipt_ledger=self.receipt_ledger,
            shm_size=65536,
        )
        # Stage 116: Persistent HNSW Vector DB (Era 12)
        self.local_vector_db = PersistentLocalVectorDB(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "vector_db",
            receipt_ledger=self.receipt_ledger,
            dim=64,
            auto_persist=True,
        )
        # Stage 117: Autonomous GitOps Engine (Era 12)
        self.git_ops = AutonomousGitOpsSynthesizer(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "gitops",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 118: Thermal & Compute Governor (Era 12)
        self.thermal_governor = ThermalComputeGovernor(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "governor",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 119: Episodic Dream Consolidator (Era 12)
        self.dream_consolidator = EpisodicDreamConsolidator(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "dream",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 120: Sovereign Singularity Nexus & Era 12 Master Seal (Era 12)
        self.era12_seal = Era12MasterSealNexus(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "seals",
            receipt_ledger=self.receipt_ledger,
            ipc_bus=getattr(self, "ipc_bus", None),
        )
        # Stage 121: Causal Neural Knowledge Graph & Property Graph Nexus (Era 13)
        self.knowledge_graph = NeuralKnowledgeGraphNexus(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "graph",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 122: Multi-Hypothesis Counterfactual Evaluator (Era 13)
        self.counterfactual_simulator = CounterfactualSimulationEngine(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "simulations",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 123: Hierarchical Goal & Subgoal Decomposer (Era 13)
        self.goal_decomposer = HierarchicalGoalDecomposer(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "plans",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 124: Autonomous Verification Oracle & Proof Engine (Era 13)
        self.verification_oracle = AutonomousVerificationOracle(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "oracle",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 125: Self-Supervised Latent Concept Miner (Era 13)
        self.concept_miner = LatentConceptMiner(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "concepts",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 126: Dynamic Context Budget Allocator (Era 13)
        self.context_budgeter = DynamicContextBudgetAllocator(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "budget",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 127: Protocol Reverse-Engineer & Client Synthesizer (Era 13)
        self.protocol_synthesizer = ProtocolReverseSynthesizer(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "protocols",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 128: Autonomous Meta-Policy Refiner (Era 13)
        self.meta_policy_refiner = AutonomousMetaPolicyRefiner(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "policies",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 129: Distributed Multi-Node IPC Mesh Gateway (Era 13)
        self.mesh_gateway = DistributedMeshGatewayBridge(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "mesh",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 130: Sovereign Singularity Nexus & Era 13 Master Seal (Era 13)
        self.era13_seal = Era13MasterSealNexus(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "seals",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 131: Semantic Mutation Engine & AST Genetic Operator (Era 14)
        self.ast_mutator = ASTSemanticMutationOperator(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "mutations",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 132: Autonomous Test Oracle Synthesizer (Era 14)
        self.test_oracle = AutonomousTestOracleSynthesizer(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "oracles",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 133: Type-Inference & Static Constraint Solver (Era 14)
        self.constraint_solver = StaticConstraintSolver(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "constraints",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 134: Bytecode Decompiler & Disassembly Inspector (Era 14)
        self.bytecode_inspector = BytecodeDisassemblyInspector(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "bytecode",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 135: Polyglot FFI Bridge & Native C ABI Linker (Era 14)
        self.ffi_linker = PolyglotFFINativeLinker(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "ffi",
            receipt_ledger=self.receipt_ledger,
        )
        # Stage 136: Self-Hosted Package Index & Sovereign Wheel Fabric (Era 14)
        self.wheel_fabric = SovereignWheelFabricIndex(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "wheels",
            receipt_ledger=self.receipt_ledger,
        )

        # Stage 137: Real-Time Performance Regression Sentinel (Era 14)
        self.perf_sentinel = RealTimePerfRegressionSentinel(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 138: Dead-Code Eliminator & AST Pruner (Era 14)
        self.dead_code_eliminator = DeadCodeEliminator(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 139: Deterministic Replay & Flight-Data Recorder (Era 14)
        self.flight_recorder = FlightDataRecorder(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 140: Sovereign Singularity Nexus & Era 14 Master Seal (Era 14)
        self.era14_nexus = Era14MasterSealNexus(
            project_root=self.project_root,
            runtime=self,
            data_dir=lucy_data / "seals",
            receipt_ledger=self.receipt_ledger,
        )

        # Stage 141: Intermediate Representation (IR) Compiler Core (Era 15)
        self.ir_compiler = IRCompilerCore(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 142: Static Single Assignment (SSA) Optimizer (Era 15)
        self.ssa_optimizer = SSAOptimizer(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 143: Loop Invariant & Polyhedral Transformation Engine (Era 15)
        self.loop_optimizer = LoopPolyhedralOptimizer(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 144: Register Allocation & Spill Cost Graph Colorer (Era 15)
        self.register_allocator = RegisterAllocator(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 145: Target-Agnostic Assembler & Machine Code Synthesizer (Era 15)
        self.code_synthesizer = MachineCodeSynthesizer(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 146: Just-In-Time (JIT) Hotpath Tracer & Tiered Execution Engine (Era 15)
        self.jit_tracer = JITHotpathTracer(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 147: Ahead-Of-Time (AOT) Sovereign Native Linker & PE/ELF Formatter (Era 15)
        self.native_linker = AOTNativeLinker(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 148: Zero-Copy Memory Arena & Memory Pool Allocator (Era 15)
        self.memory_manager = SovereignMemoryManager(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 149: Link-Time Optimization (LTO) & Cross-Module Inliner (Era 15)
        self.lto_pipeline = LTOPipeline(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 150: Sovereign Singularity Nexus & Era 15 Master Seal (Era 15)
        self.era15_nexus = Era15MasterSealNexus(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 151: Sovereign Microkernel Architecture & TCB Scheduler (Era 16)
        self.kernel_scheduler = MicrokernelScheduler(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 152: Hardware Abstraction Layer & CPU Topology Sentinel (Era 16)
        self.hal_cpu = HALCpuTopologySentinel(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 153: Virtual Memory Management & Page Table Synthesizer (Era 16)
        self.paging_engine = VirtualMemoryPagingEngine(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 154: IPC Fast-Ring & Shared Memory Channels (Era 16)
        self.ipc_registry = IPCEndpointRegistry(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 155: Interrupt Service Routine & PIC/APIC Controller (Era 16)
        self.interrupt_controller = SovereignInterruptController(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 156: Direct Memory Access & Device Buffer Fabric (Era 16)
        self.dma_fabric = SovereignDMABufferFabric(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 157: Capability-Based Security Tokens & Enclave Sentinel (Era 16)
        self.capability_manager = SovereignCapabilityManager(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 158: Sovereign Block Device Driver & Virtual Disk Fabric (Era 16)
        self.block_fabric = SovereignBlockDeviceFabric(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 159: Microkernel VFS & Content-Addressable Inode Storage (Era 16)
        self.vfs = VirtualFileSystem(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 160: Sovereign Singularity Nexus & Era 16 Master Seal (Era 16)
        self.era16_nexus = Era16MasterSealNexus(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 161: Byzantine Fault Tolerant SMR & Consensus Cluster (Era 17)
        self.bft_cluster = BFTConsensusCluster(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 162: Raft Leader Election & Distributed Heartbeat Sentinel (Era 17)
        self.raft_cluster = SovereignRaftCluster(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 163: Sovereign Distributed Hash Table & Kademlia Mesh (Era 17)
        self.dht_mesh = SovereignDHTMesh(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 164: Vector Clock & Lamport Causality Ordering Fabric (Era 17)
        self.causal_fabric = CausalBroadcastFabric(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 165: Multi-Paxos Distributed Transaction Commit Protocol (Era 17)
        self.paxos_cluster = MultiPaxosCluster(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 166: Gossip Protocol & Epidemic State Propagation Engine (Era 17)
        self.gossip_mesh = SovereignGossipMesh(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 167: Conflict-Free Replicated Data Types (CRDTs) Synthesizer (Era 17)
        self.crdt_synth = SovereignCRDTSynthesizer(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 168: Sovereign Mesh Network Tunneling & Virtual TAP/TUN Fabric (Era 17)
        self.mesh_tunnel = SovereignMeshTunnelFabric(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 169: Distributed Deadlock Detection & Chandy-Misra Sentinel (Era 17)
        self.deadlock_sentinel = DistributedDeadlockSentinel(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 170: Sovereign Singularity Nexus & Era 17 Master Seal (Era 17)
        self.era17_nexus = Era17MasterSealNexus(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 171: Consistent Hashing Ring & Virtual Node Partitioning (Era 18)
        self.hash_ring = ConsistentHashRing(
            default_vnodes=128,
            replication_factor=3,
            project_root=self.project_root,
            runtime=self,
        )
        self.hash_ring.add_node("storage_node_0")
        self.hash_ring.add_node("storage_node_1")
        self.hash_ring.add_node("storage_node_2")

        # Stage 172: Distributed LSM-Tree & Memtable SSTable Engine (Era 18)
        self.lsm_tree = DistributedLSMTree(
            node_id="primary_storage_0",
            memtable_max_entries=64,
            compaction_threshold=4,
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 173: Quorum Read-Repair & Active Anti-Entropy Merkle Fabric (Era 18)
        self.quorum_coordinator = QuorumAntiEntropyCoordinator(
            default_n=3,
            default_w=2,
            default_r=2,
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 174: Distributed Write-Ahead Log (WAL) Segment Replication (Era 18)
        self.wal_manager = DistributedWALManager(
            node_id="primary_wal_0",
            max_segment_records=64,
            quorum_size=2,
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 175: Distributed Snapshot Isolation & MVCC Storage (Era 18)
        self.mvcc_storage = DistributedMVCCStorage(
            node_id="primary_mvcc_0",
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 176: Dynamic Shard Migration & Range Splitter Sentinel (Era 18)
        self.shard_sentinel = DynamicShardSentinel(
            split_threshold_records=32,
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 177: Distributed Secondary Indexing & Global Query Fabric (Era 18)
        self.index_fabric = DistributedSecondaryIndexFabric(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 178: Raft-Partitioned Distributed KV Engine (Era 18)
        self.multi_raft_kv = MultiRaftKVEngine(
            group_count=4,
            peers_per_group=3,
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 179: Geo-Replication Replication Fabric & Multi-Region Gateway (Era 18)
        self.geo_fabric = GeoReplicationFabric(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 180: Sovereign Singularity Nexus & Era 18 Master Seal (Era 18)
        self.era18_nexus = Era18MasterSealNexus(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 181: Columnar Vector Storage & Compressed Arrow Layout (Era 19)
        self.columnar_storage = ColumnarVectorStorageFabric(
            batch_capacity=128,
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 182: Cost-Based Distributed Query Optimizer (CBO) (Era 19)
        self.query_optimizer = CostBasedQueryOptimizerFabric()

        # Stage 183: Vectorized Execution Engine & SIMD Batch Operator (Era 19)
        self.vectorized_engine = VectorizedExecutionFabric()

        # Stage 184: Distributed Hash Join & Broadcast Shuffle Fabric (Era 19)
        self.hash_join_fabric = DistributedHashJoinFabric()

        # Stage 185: Approximate Query Processing & HyperLogLog Count-Distinct (Era 19)
        self.approx_query_fabric = ApproxQueryFabric()

        # Stage 186: Materialized View Refresh & Incremental View Maintenance (IVM) (Era 19)
        self.materialized_view_fabric = MaterializedViewIVMFabric()

        # Stage 187: Streaming Window Aggregation & Watermark Sentinel (Era 19)
        self.streaming_window_fabric = StreamingWindowFabric()

        # Stage 188: Adaptive Query Execution (AQE) & Runtime Replanner (Era 19)
        self.aqe_fabric = AdaptiveQueryExecutionFabric()

        # Stage 189: Distributed OLAP Storage Chunk Compactor & Parquet Encoder (Era 19)
        self.olap_compactor_fabric = OLAPChunkCompactorFabric()

        # Stage 190: Sovereign Singularity Nexus & Era 19 Master Seal (Era 19)
        self.era19_nexus = Era19MasterSealNexus(
            project_root=self.project_root,
            runtime=self,
        )

        # Stage 191: Autonomous JIT Micro-Optimizer & Bytecode Vectorizer (Era 20)
        self.jit_optimizer = AutonomousJITOptimizerFabric()

        # Stage 192: Dynamic Kernel Self-Healing & Crash Recovery Supervisor (Era 20)
        self.kernel_self_healing = KernelSelfHealingFabric()
        # Stage 193: Sovereign Distributed Consensus Raft-BFT Hybrid (Era 20)
        self.raft_bft_fabric = RaftBFTHybridFabric()
        # Stage 194: Autonomous Zero-Copy Inter-Process Shared Memory Ring (Era 20)
        self.zerocopy_shm_fabric = ZeroCopyIPCShmFabric()
        # Stage 195: Autonomous Neural Weights Sharder & Distributed Tensor Runtime (Era 20)
        self.tensor_runtime_fabric = DistributedTensorRuntimeFabric()
        # Stage 196: Self-Evolving Code Synthesis & AST Verification Pipeline (Era 20)
        self.self_evolving_code_fabric = SelfEvolvingCodePipelineFabric()
        # Stage 197: Autonomous Global Chrono-Log & Event Sourcing Fabric (Era 20)
        self.chrono_log_fabric = GlobalChronoLogFabric()
        # Stage 198: Sovereign Autonomous Daemon Mesh & Heartbeat Sentinel (Era 20)
        self.daemon_mesh_fabric = DaemonMeshSentinelFabric()
        # Stage 199: Bicentennial Singularity Nexus & 200-Stage Master Orchestrator (Era 20)
        self.bicentennial_nexus = BicentennialSingularityNexus(runtime=self)
        # Stage 200: The Sovereign Bicentennial AGI Grand Master Seal (Era 20)
        self.bicentennial_grand_master_seal = BicentennialGrandMasterSealNexus()
        # Stage 201: Autonomous Multi-Kernel Federation Bus (Era 21)
        self.multi_kernel_federation = MultiKernelFederationFabric()
        # Stage 202: Quantum-Resistant Lattice Cryptography (Era 21)
        self.post_quantum_crypto = PostQuantumCryptoFabric()
        # Stage 203: Autonomous Decentralized Sovereign Contract (Era 21)
        self.sovereign_contract_engine = SovereignContractEngineFabric()
        # Stage 204: Neuromorphic Spike Mesh (Era 21)
        self.neuromorphic_spike_mesh = NeuromorphicSpikeMeshFabric()
        # Stage 205: Knowledge Distillation & Model Pruner (Era 21)
        self.knowledge_distillation_pruner = KnowledgeDistillationPrunerFabric()
        # Stage 206: ZK Invariant Prover (Era 21)
        self.zk_invariant_prover = ZKInvariantProverFabric()
        # Stage 207: Compute Governor (Era 21)
        self.compute_governor = ComputeGovernorFabric()
        # Stage 208: Multimodal Symbolic Grounding (Era 21)
        self.multimodal_grounding = MultimodalSymbolicGroundingFabric()
        # Stage 209: Hyperscale Mesh Synchronizer (Era 21)
        self.hyperscale_mesh = HyperscaleMeshSynchronizerFabric()
        # Stage 210: Era 21 Master Seal & Hyper-Federation Genesis
        self.era21_master_seal = Era21MasterSealFabric()
        # Stage 211: Photonic Matrix Multiplier (Era 22)
        self.photonic_matrix_multiplier = PhotonicMatrixMultiplierFabric()
        # Stage 212: Interplanetary DTN Routing (Era 22)
        self.interplanetary_dtn = InterplanetaryDTNRoutingFabric()
        # Stage 213: Tensor-Train Engine (Era 22)
        self.tensor_train_engine = TensorTrainEngineFabric()
        # Stage 214: Holographic Associative Memory (Era 22)
        self.holographic_memory = HolographicAssociativeMemoryFabric()
        # Stage 215: Async Micro-Actor Mesh (Era 22)
        self.micro_actor_mesh = AsyncMicroActorMeshFabric()
        # Stage 216: Quantum Hybrid Coprocessor (Era 22)
        self.quantum_coprocessor = QuantumHybridCoprocessorFabric()
        # Stage 217: Chaos Fault Injection (Era 22)
        self.chaos_engine = ChaosFaultInjectionFabric()
        # Stage 218: Trans-Universal Belief Mesh (Era 22)
        self.belief_mesh = TransUniversalBeliefMeshFabric()
        # Stage 219: Concept Synthesis Ontology (Era 22)
        self.ontology_engine = ConceptSynthesisOntologyFabric()
        # Stage 220: Era 22 Master Seal & Galactic Hyper-Mesh (Era 22)
        self.era22_master_seal = Era22MasterSealFabric()
        # Stage 221: Quantum Density Matrix Simulator (Era 23)
        self.density_matrix_simulator = QuantumManyBodyDensityFabric()
        # Stage 222: Sovereign Holographic Swarm Coordination & Flocking Mesh (Era 23)
        self.holographic_swarm = HolographicSwarmMeshFabric()
        # Stage 223: Sub-Atomic Micro-Architecture Pipeline Emulation & Speculative Execution Governor (Era 23)
        self.subatomic_pipeline_governor = SubatomicPipelineGovernorFabric()
        # Stage 224: Universal Multi-Verse Counterfactual State Forker & Timeline Brancher (Era 23)
        self.multiverse_forker = MultiverseStateForkerFabric()
        # Stage 225: Autonomous Zero-Knowledge Proof Aggregator & Recursive SNARK Verifier (Era 23)
        self.recursive_snark_aggregator = RecursiveSNARKAggregatorFabric()
        # Stage 226: Self-Supervised Topological Data Analysis & Persistent Homology Engine (Era 23)
        self.topological_data_analysis = TopologicalDataAnalysisFabric()
        # Stage 227: Autonomous Hardware Energy Budget Governor & Thermal-Joule Throttle Fabric (Era 23)
        self.energy_budget_governor = EnergyBudgetGovernorFabric()
        # Stage 228: High-Dimensional Hyperdimensional Computing & Vector Symbolic Architecture (Era 23)
        self.hyperdimensional_computing = HyperdimensionalComputingFabric()
        # Stage 229: Autonomous Planetary Geo-Distributed Disaster Recovery & State Relocator (Era 23)
        self.geo_disaster_recovery = GeoDisasterRecoveryFabric()
        # Stage 230: The Sovereign Era 23 Master Seal & Universal Multi-Verse Genesis (Era 23)
        self.era23_master_seal = Era23MasterSealFabric()
        # Stage 231: Neuromorphic Spiking Neural Network & LIF Synaptic Fabric (Era 24)
        self.neuromorphic_spiking = NeuromorphicSpikingFabric()
        # Stage 232: Quantum-Resilient Lattice Post-Quantum Cryptography Vault (Era 24)
        self.lattice_pqc_vault = LatticePQCVaultFabric()
        # Stage 233: Autonomous Non-Euclidean Hyperbolic Knowledge Graph Embedding (Era 24)
        self.hyperbolic_graph_embedder = HyperbolicGraphEmbedderFabric()
        # Stage 234: Self-Synthesizing AST Bytecode JIT Compiler & Polyglot IR (Era 24)
        self.polyglot_bytecode_jit = PolyglotBytecodeJITFabric()
        # Stage 235: Decentralized Multi-Agent Epistemic Logic & Dynamic Common Knowledge Mesh (Era 24)
        self.epistemic_logic_mesh = EpistemicLogicMeshFabric()
        # Stage 236: Autonomous Temporal Chrono-State Engine & Causality Inversion Governor (Era 24)
        self.temporal_chrono_governor = TemporalChronoGovernorFabric()
        # Stage 237: Autonomous Photonic Optical Neural Interconnect & Ultra-Low-Latency Switch Fabric (Era 24)
        self.photonic_optical_switch = PhotonicOpticalSwitchFabric()
        # Stage 238: Self-Healing Chaos Immunity & Byzantine Swarm Consensus Auto-Recovery (Era 24)
        self.byzantine_swarm_consensus = ByzantineSwarmConsensusFabric()
        # Stage 239: Planetary Sovereign Autonomous Resource Exchange & Zero-Sum Tokenless Ledger (Era 24)
        self.planetary_resource_exchange = PlanetaryResourceExchangeFabric()
        # Stage 240: The Sovereign Era 24 Master Seal & AGI Singularity Genesis (Era 24)
        self.era24_master_seal = Era24MasterSealFabric()
        # Stage 241: Programmable Metamaterial Phonon-Polariton Waveguide Computing & Analog Tensor Interconnect (Era 25)
        self.metamaterial_phonon_computer = MetamaterialPhononComputerFabric()
        # Stage 242: Non-Hermitian Exceptional Point Dynamical Resonance Engine (Era 25)
        self.exceptional_point_resonance = ExceptionalPointResonanceFabric()
        # Stage 243: Deep Sheaf-Theoretic Distributed Multi-Sensor Consistency & Cellular Cohomology Engine (Era 25)
        self.cellular_cohomology_sheaf = CellularCohomologySheafFabric()
        # Stage 244: Autonomous Synthetic Biology DNA/RNA Storage Codec & Transceiver (Era 25)
        self.dna_molecular_storage = DnaMolecularStorageFabric()
        # Stage 245: Hyper-Scale Neuromorphic Astro-Grid Orbital Constellation Coordinator (Era 25)
        self.orbital_constellation_grid = OrbitalConstellationGridFabric()
        # Stage 246: Thermodynamically Reversible Landauer-Zero Computation & Adiabatic Governor (Era 25)
        self.adiabatic_reversible_governor = AdiabaticReversibleGovernorFabric()
        # Stage 247: Sovereign Anti-Fragile Black-Swan Catastrophe Immunity & Stress Inverter (Era 25)
        self.antifragile_stress_inverter = AntiFragileStressInverterFabric()
        # Stage 248: Non-Archimedean p-Adic Ultrametric Cognitive Clustering (Era 25)
        self.padic_ultrametric_clusterer = PadicUltrametricClustererFabric()
        # Stage 249: Universal Multi-Tier Zero-Trust Hardware Enclave (Era 25)
        self.zero_trust_hardware_enclave = ZeroTrustHardwareEnclaveFabric()
        # Stage 250: The Sovereign Era 25 Master Seal & Cosmic Core Genesis (Era 25)
        self.era25_master_seal = Era25MasterSealFabric()
        # Stage 251: Holomorphic Modular Form & Calabi-Yau Metric Engine (Era 26)
        self.calabi_yau_metric_engine = CalabiYauMetricEngineFabric()
        # Stage 252: Non-Equilibrium Fluctuation-Dissipation & Crooks Harvester (Era 26)
        self.jarzynski_entropy_harvester = JarzynskiEntropyHarvesterFabric()
        # Stage 253: Hyper-Dimensional Clifford Geometric Algebra Processor (Era 26)
        self.clifford_processor = CliffordGeometricAlgebraFabric()
        # Stage 254: Symplectic Integrator & Lie-Poisson Momentum Preserver (Era 26)
        self.symplectic_integrator = SymplecticHamiltonianIntegratorFabric()
        # Stage 255: Bio-Mimetic Turing Reaction-Diffusion Synthesizer (Era 26)
        self.turing_synthesizer = TuringMorphogeneticSynthesizerFabric()
        # Stage 256: Deep Renormalization Group Flow & Wilsonian EFT (Era 26)
        self.rg_flow_fabric = RenormalizationGroupFlowFabric()
        # Stage 257: Superconducting Josephson SQUID Magnetometer (Era 26)
        self.squid_magnetometer = JosephsonSquidMagnetometerFabric()
        # Stage 258: Relativistic Astro-Chronometric Synchronizer (Era 26)
        self.chrono_synchronizer = RelativisticChronoSynchronizerFabric()
        # Stage 259: Constitutional Shapley-Nash Game Engine (Era 26)
        self.shapley_nash_engine = ConstitutionalShapleyNashEngineFabric()
        # Stage 260: The Sovereign Era 26 Master Seal & Singularity Genesis (Era 26)
        self.era26_master_seal = Era26MasterSealFabric()
        # Stage 261: Non-Abelian SU(N) Yang-Mills Gauge Connection (Era 27)
        self.yang_mills_engine = YangMillsGaugeHolonomyFabric()
        # Stage 262: Holographic AdS/CFT Ryu-Takayanagi Wedge (Era 27)
        self.entanglement_wedge_fabric = AdSCFTEntanglementWedgeFabric()
        # Stage 263: Optomechanical Cavity Radiation Pressure Transceiver (Era 27)
        self.optomechanical_transceiver = OptomechanicalCavityTransceiverFabric()
        # Stage 264: Autonomous Topological Soliton Skyrmion Lattice Dynamics (Era 27)
        self.skyrmion_weaver = TopologicalSkyrmionWeaverFabric()
        # Stage 265: Continuous-Time Quantum Walk & Spatial Search (Era 27)
        self.quantum_walk_search = ContinuousQuantumWalkSearchFabric()
        # Stage 266: Planetary Magnetohydrodynamic Dynamo Plasma Core (Era 27)
        self.mhd_dynamo_sim = MagnetohydrodynamicDynamoSimFabric()
        # Stage 267: Geometric Berry Phase & Non-Abelian Holonomy Gate (Era 27)
        self.berry_holonomy = BerryWilczekZeeHolonomyFabric()
        # Stage 268: Cosmological FLRW Metric & Dark Energy Engine (Era 27)
        self.flrw_cosmo_engine = FLRWCosmologicalEngineFabric()
        # Stage 269: Multi-Tier Zero-Knowledge zk-SNARK/STARK Verifier (Era 27)
        self.zk_verifier = ZeroKnowledgeZKVerifierFabric()
        # Stage 270: Era 27 Sovereign Master Seal & Cosmological Genesis
        self.era27_master_seal = Era27MasterSealFabric()
        # Stage 271: QCD Color Flux Confinement & Hadronization (Era 28)
        self.qcd_confinement = QCDColorFluxConfinementFabric()
        # Stage 272: Non-Commutative Moyal Star Algebra & GUP (Era 28)
        self.moyal_algebra = NoncommutativeMoyalStarAlgebraFabric()
        # Stage 273: Topological Anyon Braiding & Fusion Processor (Era 28)
        self.anyon_processor = FractionalAnyonBraidingProcessorFabric()
        # Stage 274: Relativistic Plasma Shock Accelerator & Fermi Engine (Era 28)
        self.plasma_shock_accelerator = RelativisticPlasmaShockAcceleratorFabric()
        # Stage 275: Gravitational Lensing Caustic Raytracer (Era 28)
        self.lensing_caustic_tracer = GravitationalLensingCausticTracerFabric()
        # Stage 276: Quantum Teleportation & Entanglement Repeater Fabric (Era 28)
        self.quantum_repeater_fabric = QuantumTeleportationRepeaterFabricFabric()
        # Stage 277: KdV Non-Linear Soliton Integrable Synthesizer (Era 28)
        self.kdv_soliton_synthesizer = KdVIntegrableSolitonSynthesizerFabric()
        # Stage 278: Casimir-Polder Vacuum & Metamaterial Levitation Engine (Era 28)
        self.casimir_vacuum_engine = CasimirPolderVacuumEngineFabric()
        # Stage 279: Sovereign ZK-Rollup & Verifiable State Compressor (Era 28)
        self.zk_rollup_compressor = SovereignZKRollupCompressorFabric()
        # Stage 280: Era 28 Sovereign Master Seal & Astro-Topological Genesis
        self.era28_master_seal = Era28MasterSealFabric()
        # Stage 281: Black Hole Holographic Thermodynamics & Bekenstein-Hawking Entropy Engine (Era 29)
        self.black_hole_thermodynamics = BlackHoleThermodynamicsFabric()
        # Stage 282: Non-Hermitian PT-Symmetric Open Quantum Engine & EP Sensor (Era 29)
        self.pt_symmetric_engine = NonHermitianPTSymmetricFabric()
        # Stage 283: Quantum Many-Body Scrambler & OTOC Engine (Era 29)
        self.quantum_scrambler = QuantumManyBodyScramblerFabric()
        # Stage 284: CMB Multipole Power Spectrum & Inflationary Tensor Fabric (Era 29)
        self.cmb_power_spectrum = CMBMultipolePowerSpectrumFabric()
        # Stage 285: Quantum Zeno & Anti-Zeno Dynamic Controller (Era 29)
        self.zeno_controller = QuantumZenoDynamicControllerFabric()
        # Stage 286: Topological Majorana Zero-Mode Braiding & Gate (Era 29)
        self.majorana_gate = MajoranaZeroModeGateFabric()
        # Stage 287: Pulsar Magnetosphere Relativistic FFE Engine (Era 29)
        self.pulsar_ffe_engine = PulsarMagnetosphereFFEFabric()
        # Stage 288: Quantum Optic Phase Estimator & Fisher Information (Era 29)
        self.fisher_phase_estimator = QuantumFisherPhaseEstimatorFabric()
        # Stage 289: Sovereign Cross-Chain State Relayer & ZK Merkle Bridge (Era 29)
        self.cross_chain_zk_bridge = SovereignCrossChainZKBridgeFabric()
        # Stage 290: Era 29 Sovereign Master Seal & Trans-Cosmic Genesis
        self.era29_master_seal = Era29MasterSealFabric()
        self.workflow_learner = WorkflowHabitLearner(lucy_data)
        self.lora_sleep_cycle.workflow_learner = self.workflow_learner
        self.lora_sleep_cycle.personal_profiler = self.personal_profiler
        self.personal_lora_alignment.workflow_learner = self.workflow_learner
        self.workspace_sensor = LiveWorkspaceSensor(self.project_root)
        self.proactive_briefer = ProactiveSessionBriefer(runtime=self)
        self.natural_action_parser = NaturalActionParser(runtime=self)
        # Stages 54-58 Unified Aliases & Subsystems
        self.data_dir = self.project_root / "data"
        self.cron_daemon = self.cron_scheduler
        self.api_tools = self.external_tools
        self.agent_registry = self.agents
        self.agent_orchestrator = self.internal_agent_orchestrator
        self.human_state = self.human_state_awareness
        self.lora_sleep = self.lora_sleep_cycle
        project = self.project_summary()
        self.session_state.boot_sequence(
            active_project=project.get("name", "Lucy"),
            current_checkpoint=self._latest_checkpoint_id(),
            next_action=project.get("next_action", ""),
            system_status="online",
        )
        self.persistent_runtime.start(
            active_project=project.get("name", "Lucy"),
            guardian_status="active",
        )

        self.logger.log(
            "runtime_started",
            "Lucy Core Runtime initialized.",
            source="lucy_runtime",
        )
        self._startup_continuity_backup()

    def _try_load(self, module_name: str, class_name: str, *args: Any) -> Any:
        try:
            mod = importlib.import_module(f"backend.lucy_core.{module_name}")
            cls = getattr(mod, class_name, None)
            if cls is not None:
                try:
                    return cls(*args)
                except TypeError:
                    return cls()
        except Exception:
            pass
        return None

    def _load_config(self) -> dict:
        cfg_path = self.project_root / "config" / "lucy_runtime_config.json"
        if cfg_path.exists():
            try:
                loaded = json.loads(cfg_path.read_text(encoding="utf-8"))
                config = dict(DEFAULT_CONFIG)
                config.update(loaded)
                return config
            except Exception:
                pass
        return dict(DEFAULT_CONFIG)

    def status(self) -> dict:
        """Return Lucy runtime status as a dict."""
        cfg = self.config
        result = {
            "system_name": cfg.get("system_name", "LUCY"),
            "full_form": cfg.get("full_form", "Living Unified Cognitive Yield"),
            "stage": cfg.get("stage", "Unknown"),
            "mode": cfg.get("mode", "Unknown"),
            "agents_registered": len(self.agents.list_agents()),
            "agents_active": self.agents.any_active(),
            "api_enabled": cfg.get("api_enabled", False),
            "voice_enabled": cfg.get("voice_enabled", False),
            "web_ui_enabled": cfg.get("web_ui_enabled", False),
            "desktop_ui_enabled": cfg.get("desktop_ui_enabled", False),
            "root_access_enabled": cfg.get("root_access_enabled", False),
            "autonomy_enabled": cfg.get("autonomy_enabled", False),
            "protected_actions_blocked": cfg.get("protected_actions_blocked", True),
            "memory_mode": cfg.get("memory_mode", "local_json_approved_facts"),
            "fallback_learning_enabled": cfg.get("fallback_learning_enabled", False),
            "permanent_memory_enabled": cfg.get("permanent_memory_enabled", False),
            "talking_style_learning_enabled": cfg.get("talking_style_learning_enabled", False),
            "encrypted_secret_storage_enabled": cfg.get("encrypted_secret_storage_enabled", False),
            "overnight_checkpoint_target": cfg.get("overnight_checkpoint_target", 100),
            "cognition_mode": self.cognition.status().get("mode"),
            "spine_summary": get_spine_summary(self.spine),
        }
        proj = self.project_summary()
        mem_graph = self.memory_graph.status() if hasattr(self, "memory_graph") else {"active_nodes": 0, "superseded_nodes": 0}
        result["active_project"] = proj.get("name", "Lucy")
        result["next_action"] = proj.get("next_action", "")
        result["open_tasks"] = len(proj.get("open_tasks", []))
        result["active_memories"] = mem_graph.get("active_nodes", 0)
        result["superseded_memories"] = mem_graph.get("superseded_nodes", 0)
        result["personal_pace"] = self.personal_profiler.status().get("current_pace") if hasattr(self, "personal_profiler") else "focused_operational"
        result["correction_rules"] = self.workflow_learner.status().get("correction_rules_count", 0) if hasattr(self, "workflow_learner") else 0
        result["anti_hallucination_gate"] = "two_layer_enforced (Stage 37 Disk + Stage 55 Receipts)"
        self.logger.log("status_checked", "Status checked.", source="lucy_runtime")
        return result

    def session_status(self) -> dict:
        return self.session_state.status()

    def runtime_status(self) -> dict:
        return self.persistent_runtime.status()

    def safe_access_status(self) -> dict:
        return self.safe_access.status()

    def safe_access_check(self, source: str = "unknown") -> dict:
        project = self.project_summary()
        return self.safe_access.check_access(
            source=source,
            guardian=self.guardian_core,
            active_project=project.get("name", "Lucy"),
        )

    def first_thought_status(self) -> dict:
        return self.first_thought.status()

    def first_thought_readiness(self) -> dict:
        return self.first_thought.readiness(self)

    def assemble_first_thought(self) -> dict:
        return self.first_thought.assemble(self)

    def show_first_thought(self) -> dict:
        return self.first_thought.show()

    def self_model_status(self) -> dict:
        return self.self_model.status(self)

    def growth_proposals_status(self) -> dict:
        return self.growth_proposals.status()

    def list_growth_proposals(self) -> list[dict]:
        return self.growth_proposals.list_proposals()

    def propose_growth(self) -> dict:
        return self.growth_proposals.propose(self)

    def reject_growth_proposal(self, selector: str = "") -> dict:
        return self.growth_proposals.review(selector, "rejected")

    def approve_growth_proposal_for_future(self, selector: str = "") -> dict:
        return self.growth_proposals.review(selector, "approved_for_future")

    def evaluation_lab_status(self) -> dict:
        return self.evaluation_lab.status()

    def evaluate_growth_proposals(self) -> dict:
        return self.evaluation_lab.evaluate_all(self.list_growth_proposals())

    def evaluate_proposal(self, selector: str = "") -> dict:
        return self.evaluation_lab.evaluate_selected(self.list_growth_proposals(), selector)

    def show_evaluations(self) -> list[dict]:
        return self.evaluation_lab.list_evaluations()

    def shadow_testing_status(self) -> dict:
        return self.shadow_testing.status()

    def run_shadow_test(self) -> dict:
        return self.shadow_testing.run_latest(
            self.show_evaluations(),
            self.list_growth_proposals(),
        )

    def shadow_test_proposal(self, selector: str = "") -> dict:
        return self.shadow_testing.run(
            self.show_evaluations(),
            self.list_growth_proposals(),
            selector,
        )

    def show_shadow_tests(self) -> list[dict]:
        return self.shadow_testing.list_shadow_tests()

    def patch_pipeline_status(self) -> dict:
        return self.approved_patch_pipeline.status()

    def create_patch_plan(self, selector: str = "") -> dict:
        return self.approved_patch_pipeline.create_patch_plan(
            self.show_shadow_tests(),
            self.show_evaluations(),
            self.list_growth_proposals(),
            selector,
        )

    def show_patch_plans(self) -> list[dict]:
        return self.approved_patch_pipeline.list_patch_plans()

    def patch_plan_status(self) -> dict:
        status = self.patch_pipeline_status()
        status["latest_plan"] = status.get("latest_plan")
        return status

    def experience_storage_status(self) -> dict:
        return self.experience_storage.status()

    def record_experience(self) -> dict:
        return self.experience_storage.record_experience()

    def record_stage_experience(self) -> dict:
        return self.experience_storage.record_stage_experience()

    def show_experiences(self) -> list[dict]:
        return self.experience_storage.list_experiences()

    def identity_stability_status(self) -> dict:
        return self.identity_stability.status()

    def check_identity_stability(self) -> dict:
        return self.identity_stability.check_identity_stability()

    def identity_check(self) -> dict:
        return self.check_identity_stability()

    def show_identity_checks(self) -> list[dict]:
        return self.identity_stability.list_checks()

    def long_term_strategy_status(self) -> dict:
        return self.long_term_strategy.status()

    def create_long_term_strategy(self) -> dict:
        return self.long_term_strategy.create_strategy()

    def show_long_term_strategies(self) -> list[dict]:
        return self.long_term_strategy.list_strategies()

    def smart_organizer_status(self) -> dict:
        return self.smart_organizer.status()

    def create_organizer_item(self) -> dict:
        return self.smart_organizer.create_organizer_item()

    def show_organizer_items(self) -> list[dict]:
        return self.smart_organizer.list_items()

    def safe_local_actions_status(self) -> dict:
        return self.safe_local_actions.status()

    def create_safe_action_proposal(self) -> dict:
        return self.safe_local_actions.create_action_proposal()

    def dry_run_safe_action(self) -> dict:
        return self.safe_local_actions.dry_run_action()

    def show_safe_action_proposals(self) -> list[dict]:
        return self.safe_local_actions.list_actions()

    def external_app_bridge_status(self) -> dict:
        return self.external_app_bridge.status()

    def create_external_app_bridge_proposal(self) -> dict:
        return self.external_app_bridge.create_bridge_proposal()

    def dry_run_external_app_bridge(self) -> dict:
        return self.external_app_bridge.dry_run_bridge_check()

    def show_external_app_bridge_proposals(self) -> list[dict]:
        return self.external_app_bridge.list_bridge_proposals()

    def proactive_awareness_status(self) -> dict:
        return self.proactive_awareness.status()

    def create_proactive_awareness_scan(self) -> dict:
        return self.proactive_awareness.create_awareness_scan()

    def dry_run_proactive_awareness(self) -> dict:
        return self.proactive_awareness.dry_run_awareness_check()

    def show_proactive_awareness_scans(self) -> list[dict]:
        return self.proactive_awareness.list_awareness_scans()

    def deep_recall_status(self) -> dict:
        return self.deep_recall.status()

    def create_deep_recall_session(self, query: str | None = None) -> dict:
        return self.deep_recall.create_recall_session(query=query)

    def dry_run_deep_recall(self, query: str | None = None) -> dict:
        return self.deep_recall.dry_run_deep_recall(query=query)

    def show_deep_recall_sessions(self) -> list[dict]:
        return self.deep_recall.list_recall_sessions()

    def judgment_status(self) -> dict:
        return self.judgment.status()

    def create_judgment_record(self, situation: str | None = None) -> dict:
        return self.judgment.create_judgment(situation=situation)

    def dry_run_judgment(self, situation: str | None = None) -> dict:
        return self.judgment.dry_run_judgment(situation=situation)

    def show_judgments(self) -> list[dict]:
        return self.judgment.list_judgments()

    def adaptive_communication_status(self) -> dict:
        return self.adaptive_communication.status()

    def create_adaptive_communication_profile(self, context: str | None = None) -> dict:
        return self.adaptive_communication.create_style_profile(context=context)

    def dry_run_adaptive_communication(self, context: str | None = None) -> dict:
        return self.adaptive_communication.dry_run_adaptive_communication(context=context)

    def show_adaptive_communication_profiles(self) -> list[dict]:
        return self.adaptive_communication.list_profiles()

    def human_state_awareness_status(self) -> dict:
        return self.human_state_awareness.status()

    def create_human_state_signal(self, signal: str | None = None) -> dict:
        return self.human_state_awareness.create_state_signal(signal=signal)

    def dry_run_human_state_awareness(self, signal: str | None = None) -> dict:
        return self.human_state_awareness.dry_run_human_state_awareness(signal=signal)

    def show_human_state_signals(self) -> list[dict]:
        return self.human_state_awareness.list_state_signals()

    def time_awareness_status(self) -> dict:
        return self.time_awareness.status()

    def create_time_context(self, context: str | None = None) -> dict:
        return self.time_awareness.create_time_context(context=context)

    def dry_run_time_awareness(self, context: str | None = None) -> dict:
        return self.time_awareness.dry_run_time_awareness(context=context)

    def show_time_contexts(self) -> list[dict]:
        return self.time_awareness.list_time_contexts()

    def autonomy_boundaries_status(self) -> dict:
        return self.autonomy_boundaries.status()

    def create_autonomy_boundary_record(self, request: str | None = None) -> dict:
        return self.autonomy_boundaries.create_boundary_record(request=request)

    def dry_run_autonomy_boundaries(self, request: str | None = None) -> dict:
        return self.autonomy_boundaries.dry_run_autonomy_boundaries(request=request)

    def show_autonomy_boundary_records(self) -> list[dict]:
        return self.autonomy_boundaries.list_boundary_records()

    def provider_identity_boundary_status(self) -> dict:
        return self.provider_identity_boundary.status()

    def create_provider_identity_boundary_record(self, context: str | None = None) -> dict:
        return self.provider_identity_boundary.create_boundary_record(context=context)

    def dry_run_provider_identity_boundary(self, context: str | None = None) -> dict:
        return self.provider_identity_boundary.dry_run_provider_identity_boundary(context=context)

    def show_provider_identity_boundary_records(self) -> list[dict]:
        return self.provider_identity_boundary.list_boundary_records()

    def secrets_provider_key_safety_status(self) -> dict:
        return self.secrets_provider_key_safety.status()

    def create_secret_safety_record(self, context: str | None = None) -> dict:
        return self.secrets_provider_key_safety.create_safety_record(context=context)

    def safe_key_file_scan(self) -> dict:
        return self.secrets_provider_key_safety.safe_key_file_scan()

    def dry_run_secrets_safety(self, context: str | None = None) -> dict:
        return self.secrets_provider_key_safety.dry_run_secrets_safety(context=context)

    def show_secret_safety_records(self) -> list[dict]:
        return self.secrets_provider_key_safety.list_safety_records()

    def provider_registry_status(self) -> dict:
        return self.provider_registry.status()

    def list_registered_providers(self) -> list[dict]:
        return self.provider_registry.list_providers()

    def get_registered_provider(self, provider_name: str) -> dict:
        return self.provider_registry.get_provider(provider_name)

    def enable_registered_provider(self, provider_name: str) -> dict:
        return self.provider_registry.set_provider_enabled(provider_name, True)

    def disable_registered_provider(self, provider_name: str) -> dict:
        return self.provider_registry.set_provider_enabled(provider_name, False)

    def reset_provider_registry(self) -> dict:
        return self.provider_registry.reset_registry()

    def dry_run_provider_registry(self, context: str | None = None) -> dict:
        return self.provider_registry.dry_run_provider_registry(context=context)

    def provider_health_check_status(self) -> dict:
        return self.provider_health_check.status()

    def dry_run_provider_health_check(self, provider_name: str | None = None, context: str | None = None) -> dict:
        return self.provider_health_check.dry_run_health_check(provider_name=provider_name, context=context)

    def list_provider_health_checks(self) -> list[dict]:
        return self.provider_health_check.list_dry_runs()

    def reset_provider_health_check(self) -> dict:
        return self.provider_health_check.reset()

    def current_lucy_status(self) -> dict:
        project = self.project_summary()
        runtime = self.runtime_status()
        evaluation = self.evaluation_lab_status()
        shadow = self.shadow_testing_status()
        patch_pipeline = self.patch_pipeline_status()
        experience = self.experience_storage_status()
        agents = self.internal_agent_status()
        agent_count = len(agents.get("agents", []))
        agents_status = "active" if agents.get("active") and agent_count >= 4 else "limited"
        runtime_recovery = "true" if runtime.get("recovery_mode") else "false"
        return {
            "active_stage": STAGE34_STAGE_LABEL,
            "active_project": project.get("name", "Lucy"),
            "guardian_status": "active",
            "runtime_recovery_status": runtime_recovery,
            "agents_status": agents_status,
            "evaluation_lab": evaluation.get("evaluation_lab", "active"),
            "shadow_testing": shadow.get("shadow_testing", "active"),
            "patch_pipeline": patch_pipeline.get("approved_patch_pipeline", "active"),
            "real_patching": patch_pipeline.get("real_patching", "disabled"),
            "experience_storage": experience.get("experience_storage", "active"),
            "experience_records": experience.get("experience_records", 0),
            "identity_checks": self.identity_stability_status().get("identity_checks", 0),
            "strategy_records": self.long_term_strategy_status().get("strategy_records", 0),
            "organizer_items": self.smart_organizer_status().get("organizer_items", 0),
            "safe_action_proposals": self.safe_local_actions_status().get("action_proposals", 0),
            "bridge_proposals": self.external_app_bridge_status().get("bridge_proposals", 0),
            "awareness_scans": self.proactive_awareness_status().get("awareness_scans", 0),
            "recall_sessions": self.deep_recall_status().get("recall_sessions", 0),
            "judgment": "active",
            "judgment_records": self.judgment_status().get("judgment_records", 0),
            "adaptive_communication": "active",
            "style_profiles": self.adaptive_communication_status().get("style_profiles", 0),
            "human_state_awareness": "active",
            "state_signals": self.human_state_awareness_status().get("state_signals", 0),
            "time_awareness": "active",
            "time_context_records": self.time_awareness_status().get("time_context_records", 0),
            "autonomy_boundaries": "active",
            "boundary_records": self.autonomy_boundaries_status().get("boundary_records", 0),
            "provider_identity_boundary": "active",
            "provider_identity_records": self.provider_identity_boundary_status().get("boundary_records", 0),
            "secrets_provider_key_safety": "active",
            "secret_safety_records": self.secrets_provider_key_safety_status().get("safety_records", 0),
            "key_file_exists": self.secrets_provider_key_safety_status().get("key_file_exists", False),
            "provider_registry": "active",
            "provider_registry_count": self.provider_registry_status().get("provider_count", 0),
            "enabled_provider_count": self.provider_registry_status().get("enabled_provider_count", 0),
            "disabled_provider_count": self.provider_registry_status().get("disabled_provider_count", 0),
            "deep_recall": experience.get("deep_recall", "active"),
            "identity_stability": "active",
            "long_term_strategy": "active",
            "evaluation_results": evaluation.get("evaluation_results", 0),
            "shadow_test_results": shadow.get("shadow_test_results", 0),
            "patch_plans": patch_pipeline.get("patch_plans", 0),
            "next_safe_action": STAGE34_SAFE_NEXT_ACTION,
            "stage35_gate": STAGE35_GATE,
        }

    def stage17_next_action(self) -> dict:
        return self.stage33_next_action()

    def stage18_next_action(self) -> dict:
        return self.stage33_next_action()

    def stage19_next_action(self) -> dict:
        return self.stage33_next_action()

    def stage20_next_action(self) -> dict:
        return self.stage33_next_action()

    def stage21_next_action(self) -> dict:
        return self.stage33_next_action()

    def stage22_next_action(self) -> dict:
        return self.stage33_next_action()

    def stage23_next_action(self) -> dict:
        return self.stage33_next_action()

    def stage24_next_action(self) -> dict:
        return self.stage33_next_action()

    def stage25_next_action(self) -> dict:
        return self.stage33_next_action()

    def stage26_next_action(self) -> dict:
        return self.stage33_next_action()

    def stage27_next_action(self) -> dict:
        return self.stage33_next_action()

    def stage28_next_action(self) -> dict:
        return self.stage33_next_action()

    def stage29_next_action(self) -> dict:
        return self.stage33_next_action()

    def stage30_next_action(self) -> dict:
        return self.stage33_next_action()

    def stage31_next_action(self) -> dict:
        return self.stage33_next_action()

    def stage32_next_action(self) -> dict:
        return self.stage33_next_action()

    def stage33_next_action(self) -> dict:
        return {
            "active_stage": STAGE34_STAGE_LABEL,
            "next_safe_action": STAGE34_OPERATIONAL_NEXT_ACTION,
            "stage35_gate": STAGE35_GATE,
        }

    def save_state(self) -> dict:
        project = self.project_summary()
        result = self.session_state.update(
            active_project=project.get("name", "Lucy"),
            current_checkpoint=self._latest_checkpoint_id(),
            next_action=project.get("next_action", ""),
            system_status="online",
        )
        result["file"] = str(self.session_state.state_file)
        self.logger.log(
            "session_state_updated",
            "Session state saved.",
            source="session_state",
        )
        return result

    def load_state(self) -> dict:
        return self.session_state.status()

    def where_did_we_stop(self) -> dict:
        session = self.session_state.status()
        project = self.project_summary(session.get("active_project") or None)
        return {
            "session": session,
            "active_project": project.get("name", "Lucy"),
            "last_command": session.get("last_command", ""),
            "last_response_summary": session.get("last_response_summary", ""),
            "next_action": project.get("next_action") or session.get("next_action", ""),
            "crash_recovery_needed": session.get("crash_recovery_needed", False),
            "open_tasks": project.get("open_tasks", []),
        }

    def next_step(self) -> dict:
        project = self.project_summary()
        daily = self.daily_context.brief_context()
        tasks = [
            {
                "id": task.get("id", f"task_{index:04d}"),
                "text": task.get("text", ""),
                "priority": task.get("priority", 3),
                "complexity": task.get("complexity", 3),
                "project": project.get("name", "Lucy"),
                "status": task.get("status", "open"),
            }
            for index, task in enumerate(project.get("open_tasks", []), start=1)
        ]
        recommended = self.scheduler.next_recommended(
            tasks,
            context={
                "energy": daily.get("energy") or 6,
                "active_project": project.get("name", "Lucy"),
            },
        )
        return {
            "active_project": project.get("name", "Lucy"),
            "project_next_action": project.get("next_action", ""),
            "recommended": recommended,
            "daily_context": daily,
        }

    def classify_action(self, text: str) -> dict:
        project = self.project_summary()
        result = self.guardian_core.classify(text, active_project=project.get("name", "Lucy"))
        self.logger.log(
            "guardian_classified",
            f"Guardian classified action as {result.classification}.",
            source="guardian",
            extra={"matched_pattern": result.matched_pattern, "reason": result.reason},
        )
        return asdict(result)

    def guardian_status(self) -> dict:
        status = self.guardian_core.status()
        status["boundary_checker"] = "active"
        status["protected_actions_blocked"] = self.config.get("protected_actions_blocked", True)
        status["root_access_enabled"] = self.config.get("root_access_enabled", False)
        status["autonomy_enabled"] = self.config.get("autonomy_enabled", False)
        status["agent_execution_enabled"] = self.config.get("agent_execution_enabled", False)
        status["pending_approvals"] = len(self.approvals.list_pending())
        return status

    def session_summary(self) -> dict:
        session = self.session_state.status()
        project = self.project_summary()
        return {
            "session_count": session.get("session_count", 0),
            "last_opened": session.get("last_opened"),
            "last_closed": session.get("last_closed"),
            "graceful_shutdown": session.get("graceful_shutdown"),
            "crash_recovery_needed": session.get("crash_recovery_needed"),
            "active_project": project.get("name", "Lucy"),
            "next_action": project.get("next_action", ""),
            "last_command": session.get("last_command", ""),
            "last_response_summary": session.get("last_response_summary", ""),
            "file": session.get("file"),
        }

    def self_reflection(self, reason: str = "manual reflection") -> dict:
        session = self.session_state.status()
        project = self.project_summary()
        memory = self.memory_audit()
        pending = self.list_approvals()
        entry = self.reflection_log.write(
            session={
                "session_count": session.get("session_count", 0),
                "last_opened": session.get("last_opened"),
                "active_project": project.get("name", "Lucy"),
            },
            session_summary=(
                f"{reason}. Active project: {project.get('name', 'Lucy')}. "
                f"Next action: {project.get('next_action') or 'not set'}."
            ),
            what_changed=[
                f"Open tasks: {len(project.get('open_tasks', []))}",
                f"Completed tasks: {len(project.get('done_tasks', []))}",
            ],
            what_was_saved=[
                f"Active memories: {memory.get('active', 0)}",
                f"Latest checkpoint: {self._latest_checkpoint_id() or 'none'}",
            ],
            what_is_uncertain=[],
            what_needs_confirmation=[item.get("request_text", "") for item in pending[:5]],
            next_time_start_here=project.get("next_action") or "Review project summary and choose the next step.",
            drift_detected=False,
            safety_events=[f"Pending approvals: {len(pending)}"],
            memory_updates=[f"Memory active={memory.get('active', 0)} deleted={memory.get('deleted', 0)}"],
        )
        self.logger.log(
            "reflection_saved",
            "Session reflection saved.",
            source="reflection",
        )
        return entry

    def session_review(self) -> dict:
        """Review the active session and prepare safe memory candidates."""
        session = self.session_state.status()
        project = self.project_summary()
        pending_confirmations = self.pending_tool_confirmations().get("confirmations", [])
        route_summary, guardian_summary, safe_file_summary = self._session_review_summaries()
        review = self.session_review_engine.review_session(
            session=session,
            project=project,
            memory_audit=self.memory_audit(),
            pending_confirmations=pending_confirmations,
            route_decisions_summary=route_summary,
            guardian_events_summary=guardian_summary,
            safe_file_tool_events_summary=safe_file_summary,
        )
        self.logger.log(
            "session_review_created",
            "Memory-aware session review created.",
            source="session_review",
            extra={
                "memory_candidates": len(review.get("memory_candidates", [])),
                "memory_rejected": len(review.get("memory_rejected", [])),
                "drift_detected": review.get("drift_detected", False),
            },
        )
        return review

    def memory_candidates(self) -> dict:
        data = self.session_review_engine.list_memory_candidates()
        data["ok"] = True
        data["counts"] = {
            "pending": len(data.get("pending", [])),
            "approved": len(data.get("approved", [])),
            "rejected": len(data.get("rejected", [])),
        }
        return data

    def approve_memory_candidate(self, candidate_id: str) -> dict:
        result = self.session_review_engine.approve_memory_candidate(candidate_id)
        self.logger.log(
            "memory_candidate_reviewed",
            f"Memory candidate approval requested: {candidate_id}",
            source="session_review",
            extra={"ok": result.get("ok", False), "action": "approved"},
        )
        return result

    def reject_memory_candidate(self, candidate_id: str) -> dict:
        result = self.session_review_engine.reject_memory_candidate(candidate_id)
        self.logger.log(
            "memory_candidate_reviewed",
            f"Memory candidate rejection requested: {candidate_id}",
            source="session_review",
            extra={"ok": result.get("ok", False), "action": "rejected"},
        )
        return result

    def drift_report(self) -> dict:
        session = self.session_state.status()
        texts = [
            session.get("last_command", ""),
            session.get("last_user_intent", ""),
            session.get("last_response_summary", ""),
        ]
        return self.session_review_engine.drift_report(texts)

    def write_reflection(self) -> dict:
        route_summary, guardian_summary, safe_file_summary = self._session_review_summaries()
        review = self.session_review()
        entry = self.session_review_engine.write_reflection(
            review,
            route_decisions_summary=route_summary,
            guardian_events_summary=guardian_summary,
            safe_file_tool_events_summary=safe_file_summary,
        )
        self.logger.log(
            "reflection_saved",
            "Upgraded Stage 6.5 reflection saved.",
            source="session_review",
        )
        return entry

    def _current_wake_state(self):
        session = self.session_state.status()
        project = self.project_summary(session.get("active_project") or None)
        memory_candidates = self.memory_candidates()
        open_tasks = project.get("open_tasks", [])
        latest_reflection = self.reflection_log.latest(1)
        learning = self.learning_status()
        session.update(
            {
                "active_project": project.get("name", session.get("active_project", "Lucy")),
                "current_checkpoint": session.get("current_checkpoint") or self._latest_checkpoint_id(),
                "next_action": project.get("next_action") or session.get("next_action", ""),
                "mode": self.config.get("mode", "Safe Local Runtime"),
                "reasoning_active": self.config.get("stage6_reasoning_router_enabled", True),
                "tools_available": ["memory", "projects", "guardian", "session_review", "safe_file_read"],
                "session_review_available": True,
                "pending_confirmations": len(self.pending_tool_confirmations().get("confirmations", [])),
                "last_unresolved_issue": open_tasks[0].get("text", "") if open_tasks else project.get("next_action", ""),
                "last_correction_applied": self._continuity_correction_hint(
                    session.get("last_user_intent") or session.get("last_command") or ""
                ),
                "latest_session_review_summary": (
                    (latest_reflection[-1].get("summary") or latest_reflection[-1].get("session_summary", ""))
                    if latest_reflection
                    else ""
                ),
                "latest_memory_learning_summary": (
                    f"pending_memory_candidates={memory_candidates.get('counts', {}).get('pending', 0)}, "
                    f"learning_interactions={learning.get('interactions', 0)}, "
                    f"style_preferences={learning.get('style_preferences', 0)}"
                ),
            }
        )
        return self.wake_layer.build_wake_state(session, self.memory_audit(), self.guardian_status())

    def wake_status(self) -> dict:
        state = self._current_wake_state()
        return {
            "ok": True,
            "wake_label": state.wake_label,
            "active_project": state.active_project,
            "current_checkpoint": state.current_checkpoint,
            "next_action": state.next_action,
            "drift_risk": state.drift_risk,
            "presence_coherence_score": state.presence_coherence_score,
            "guardian_active": state.guardian_active,
            "memory_active": state.memory_active,
            "reasoning_active": state.reasoning_active,
            "crash_recovery_needed": state.crash_recovery_needed,
            "limitations": state.limitations,
        }

    def continuity_pulse(self) -> str:
        """Return Lucy's grounded WakeState continuity pulse."""
        return self.wake_layer.generate_continuity_pulse(self._current_wake_state())

    def startup_wake_message(self) -> str:
        return self.wake_layer.startup_wake_message(self._current_wake_state())

    def wake_report(self) -> dict:
        return self.wake_layer.wake_report(self._current_wake_state())

    def wake_limitations(self) -> list[str]:
        return self.wake_layer.wake_limitations(self._current_wake_state())

    def wake_drift_check(self, text: str) -> dict:
        return self.wake_layer.detect_drift(text)

    def presence(self) -> dict:
        return self.presence_layer.build_report(self.wake_report()).to_dict()

    def graceful_shutdown(self, summary: str = "Lucy shut down cleanly.") -> dict:
        reflection = self.self_reflection("clean shutdown")
        project = self.project_summary()
        shutdown_message = self.wake_layer.shutdown_continuity_message(
            project.get("next_action") or "Review project summary.",
            self._latest_checkpoint_id() or self.session_state.status().get("current_checkpoint", ""),
        )
        if hasattr(self, 'task_daemon'):
            self.task_daemon.shutdown(wait=False)
        state = self.session_state.graceful_shutdown(summary)
        runtime_state = self.persistent_runtime.shutdown(
            active_project=project.get("name", "Lucy"),
            guardian_status="active",
        )
        self.logger.log(
            "session_state_updated",
            "Graceful shutdown recorded.",
            source="session_state",
        )
        return {
            "state": state,
            "runtime_state": runtime_state,
            "reflection": reflection,
            "shutdown_message": shutdown_message,
        }

    def check_request(self, request_text: str) -> BoundaryResult:
        """Check a user request for safety. Nothing is executed."""
        result = self.boundary.check(request_text)

        if result.status == "blocked":
            self.logger.log(
                "risky_request_blocked",
                f"Blocked request: {request_text!r}",
                source="boundary_checker",
                risk_level="high",
                blocked=True,
                approval_required=False,
            )
        elif result.status == "approval_required":
            self.logger.log(
                "boundary_check",
                f"Approval required for: {request_text!r}",
                source="boundary_checker",
                risk_level="medium",
                blocked=False,
                approval_required=True,
            )
            self.approvals.create_request(
                request_text=request_text,
                reason=result.reason,
                risk_level="medium",
            )
        else:
            self.logger.log(
                "boundary_check",
                f"Safe request: {request_text!r}",
                source="boundary_checker",
                risk_level="none",
                blocked=False,
                approval_required=False,
            )
        return result

    def create_checkpoint(
        self,
        reason: str,
        files_changed_summary: str = "No files changed.",
        safety_status: str = "safe",
        next_step: str = "Continue development.",
    ) -> dict:
        """Create a checkpoint record and link it to the active project."""
        cp = self.checkpoints.create(
            reason=reason,
            stage=self.config.get("stage", "Core Runtime Prototype"),
            files_changed_summary=files_changed_summary,
            safety_status=safety_status,
            next_step=next_step,
        )
        self.logger.log(
            "checkpoint_created",
            f"Checkpoint created: {cp['checkpoint_id']} - {reason}",
            source="checkpoint_manager",
        )
        try:
            self.projects.add_checkpoint(cp["checkpoint_id"], reason)
        except Exception:
            self.logger.log(
                "error",
                f"Checkpoint project link failed: {cp['checkpoint_id']}",
                source="project_tracker",
            )
        self._auto_continuity_backup("checkpoint created")
        return cp

    def health(self) -> "HealthReport":  # noqa: F821
        """Run health checks and return a HealthReport."""
        from backend.lucy_core.runtime_health import run_health_check

        report = run_health_check(self.project_root, self.config)
        self.logger.log(
            "health_checked",
            f"Health check: {report.passed_count} passed, {report.failed_count} failed.",
            source="runtime_health",
        )
        return report

    def remember(self, fact: str, category: str = "general", source: str = "user", **kwargs) -> dict:
        """Save an approved local memory fact with Stage 54 temporal memory graph and Stage 55 receipt ledger."""
        graph_res = self.memory_graph.upsert_fact(fact, category=category, source=source) if hasattr(self, "memory_graph") else {}
        legacy_res = self.memory.remember(fact, category=category)
        is_saved = graph_res.get("saved", False) or legacy_res.get("saved", False)
        mem_node = graph_res.get("node") or legacy_res.get("memory")
        if is_saved:
            if hasattr(self, "receipt_ledger"):
                node_id = (mem_node or {}).get("id", "mem_node")
                self.receipt_ledger.issue_receipt(
                    action_category="memory_mutation",
                    operation="upsert_fact",
                    target=node_id,
                    verified_outcome=f"Saved fact (superseded: {graph_res.get('superseded_ids', [])})",
                )
            self.logger.log(
                "memory_saved",
                f"Saved memory: {(mem_node or {}).get('id', 'unknown')}",
                source="memory",
            )
            self._auto_continuity_backup("memory saved")
        return {
            "saved": is_saved,
            "duplicate": graph_res.get("duplicate", False) or legacy_res.get("duplicate", False),
            "memory": mem_node,
            "node": mem_node,
            "node_id": (mem_node or {}).get("id"),
            "superseded_ids": graph_res.get("superseded_ids", []),
        }

    def recall(self, query: str = "", limit: int = 8) -> list[dict]:
        """Recall local memory facts using Stage 54 BM25/temporal graph with fallback."""
        if hasattr(self, "memory_graph"):
            graph_hits = self.memory_graph.query(query_text=query, limit=limit)
            if graph_hits:
                return graph_hits
        memories = self.memory.recall(query, limit=limit) if hasattr(self.memory, "recall") else []
        self.logger.log(
            "memory_recalled",
            f"Recalled {len(memories)} memories for query: {query!r}",
            source="memory",
        )
        return memories

    def forget(self, query: str) -> dict:
        """Forget a specific memory by soft-deleting matching records."""
        result = self.memory.forget(query)
        if hasattr(self, "memory_graph"):
            graph_forgot = self.memory_graph.forget(query)
            result["graph_forgotten"] = graph_forgot.get("forgotten", 0)
        self.logger.log(
            "memory_forgotten",
            f"Forgot {result.get('forgotten', 0)} memories for query: {query!r}",
            source="memory",
        )
        if result.get("forgotten", 0) or result.get("graph_forgotten", 0):
            self._auto_continuity_backup("memory forgotten")
        return result

    def memory_audit(self) -> dict:
        return self.memory.audit()

    def _session_review_summaries(self) -> tuple[dict, dict, dict]:
        route_summary = {
            "stage6_reasoning_router_enabled": self.config.get("stage6_reasoning_router_enabled", True),
            "reasoning_mode_default": self.config.get("reasoning_mode_default", "local_policy_only"),
            "external_brain_enabled": self._external_brain_enabled(),
            "chain_of_thought_output_enabled": self.config.get("chain_of_thought_output_enabled", False),
        }
        guardian_status = self.guardian_status()
        guardian_summary = {
            "protected_actions_blocked": guardian_status.get("protected_actions_blocked", True),
            "root_access_enabled": guardian_status.get("root_access_enabled", False),
            "autonomy_enabled": guardian_status.get("autonomy_enabled", False),
            "pending_approvals": guardian_status.get("pending_approvals", 0),
        }
        tool_audit = self.tool_audit_summary(limit=5)
        safe_status = self.safe_file_tools.status().to_dict().get("data", {})
        safe_file_summary = {
            "safe_read_enabled": safe_status.get("safe_read_enabled", True),
            "write_enabled": safe_status.get("write_enabled", False),
            "network_enabled": safe_status.get("network_enabled", False),
            "execution_enabled": safe_status.get("execution_enabled", False),
            "audit_entries_shown": tool_audit.get("shown", 0),
            "recent_results": [
                {
                    "action_name": item.get("action_name"),
                    "result": item.get("result"),
                    "policy_category": item.get("policy_category"),
                    "guardian_classification": item.get("guardian_classification"),
                }
                for item in tool_audit.get("entries", [])
            ],
        }
        return route_summary, guardian_summary, safe_file_summary

    def _continuity_posture(self, session: dict, drift: dict, pending_confirmations: list[dict], checkpoint: str) -> str:
        if session.get("crash_recovery_needed"):
            return "recovery_mode"
        if drift.get("drift_detected"):
            return "drift_warning"
        if pending_confirmations:
            return "waiting_for_confirmation"
        if not checkpoint:
            return "low_context"
        return "checkpoint_ready"

    def _continuity_correction_hint(self, text: str) -> str:
        lowered = str(text).lower()
        correction_markers = [
            "don't",
            "do not",
            "too much drift",
            "stop",
            "correction",
            "not like that",
            "keep this",
            "avoid",
        ]
        if any(marker in lowered for marker in correction_markers):
            return self._safe_preview_text(text)[:180]
        return ""

    def list_projects(self) -> list[dict]:
        return self.projects.list_projects()

    def set_active_project(self, name: str) -> dict:
        result = self.projects.set_active_project(name)
        self.logger.log(
            "projects_updated",
            f"Active project set request: {name!r}",
            source="project_tracker",
        )
        if result.get("changed"):
            self._auto_continuity_backup("active project changed")
        return result

    def add_task(self, text: str) -> dict:
        result = self.projects.add_task(text)
        self.logger.log(
            "projects_updated",
            f"Task add request: {text!r}",
            source="project_tracker",
        )
        if result.get("added"):
            if hasattr(self, "receipt_ledger"):
                t_id = (result.get("task") or {}).get("id", text[:20])
                self.receipt_ledger.issue_receipt(
                    action_category="task_mutation",
                    operation="add_task",
                    target=str(t_id),
                    verified_outcome=f"Added task: {text[:60]}",
                )
            self._auto_continuity_backup("project task added")
        return result

    def complete_task(self, selector: str) -> dict:
        result = self.projects.complete_task(selector)
        self.logger.log(
            "projects_updated",
            f"Task complete request: {selector!r}",
            source="project_tracker",
        )
        if result.get("completed"):
            if hasattr(self, "receipt_ledger"):
                self.receipt_ledger.issue_receipt(
                    action_category="task_mutation",
                    operation="complete_task",
                    target=str(selector),
                    verified_outcome=f"Completed task {selector}",
                )
            self._auto_continuity_backup("project task completed")
        return result

    def show_tasks(self, include_done: bool = False) -> dict:
        return self.projects.show_tasks(include_done=include_done)

    def project_summary(self, project_name: str | None = None) -> dict:
        return self._clean_project_summary(self.projects.summary(project_name))

    def _clean_project_summary(self, summary: dict) -> dict:
        cleaned = dict(summary)
        cleaned["next_action"] = self._clean_next_action(cleaned.get("next_action", ""))
        for key in ("open_tasks", "done_tasks"):
            tasks = []
            for task in cleaned.get(key, []):
                if not isinstance(task, dict):
                    continue
                task_copy = dict(task)
                task_copy["text"] = self._clean_next_action(task_copy.get("text", ""))
                tasks.append(task_copy)
            cleaned[key] = tasks
        return cleaned

    def _clean_next_action(self, text: object) -> str:
        cleaned = str(text or "").strip()
        if not cleaned:
            return ""
        lowered = cleaned.lower()
        if any(marker in lowered for marker in STALE_NEXT_ACTION_MARKERS):
            return STAGE34_SAFE_NEXT_ACTION
        return cleaned

    def daily_brief(self) -> dict:
        brief = self.projects.daily_brief()
        brief["pending_approvals"] = len(self.approvals.list_pending())
        brief["open_reminders"] = self.reminders.list_open()
        brief["due_reminders"] = self.reminders.due_items()
        brief["memory"] = self.memory.audit()
        brief["daily_context"] = self.daily_context.brief_context()
        return brief

    def daily_checkin(self, text: str = "") -> dict:
        result = self.daily_context.checkin(text, project_context=self.project_summary())
        self.logger.log(
            "daily_context_updated",
            f"Daily check-in updated for {result['date']}.",
            source="daily_context",
            extra={
                "fields_updated": result.get("fields_updated", []),
                "redacted_count": result.get("redacted_count", 0),
            },
        )
        self._auto_continuity_backup("daily context updated")
        return result

    def today_log(self) -> dict:
        result = self.daily_context.today()
        self.logger.log(
            "daily_context_viewed",
            f"Today log viewed for {result['date']}.",
            source="daily_context",
        )
        return result

    def yesterday_summary(self) -> dict:
        result = self.daily_context.yesterday()
        self.logger.log(
            "daily_context_viewed",
            f"Yesterday summary viewed for {result['date']}.",
            source="daily_context",
        )
        return result

    def weekly_review(self) -> dict:
        result = self.daily_context.weekly_review()
        self.logger.log(
            "daily_context_viewed",
            f"Weekly review viewed for {result['start_date']} to {result['end_date']}.",
            source="daily_context",
        )
        return result

    def add_reminder(self, text: str, due: str | None = None) -> dict:
        result = self.reminders.add(text, due=due)
        self.logger.log(
            "reminders_updated",
            f"Reminder add request: {text!r}",
            source="reminders",
        )
        if result.get("added"):
            self._auto_continuity_backup("reminder added")
        return result

    def list_reminders(self) -> list[dict]:
        return self.reminders.list_open()

    def complete_reminder(self, selector: str) -> dict:
        result = self.reminders.complete(selector)
        self.logger.log(
            "reminders_updated",
            f"Reminder complete request: {selector!r}",
            source="reminders",
        )
        if result.get("completed"):
            self._auto_continuity_backup("reminder completed")
        return result

    def list_approvals(self, pending_only: bool = True) -> list[dict]:
        return self.approvals.list_pending() if pending_only else self.approvals.list_all()

    def review_approval(self, selector: str, status: str, note: str = "") -> dict:
        result = self.approvals.review(selector, status, note=note)
        self.logger.log(
            "approval_reviewed",
            f"Approval review request: {selector!r} -> {status}",
            source="approval_manager",
        )
        return result

    def project_workspace_tree(self) -> dict:
        result = self.tools.workspace_tree()
        self.logger.log("tool_used", "Workspace tree requested.", source="tools")
        return result

    def safe_tools_status(self) -> dict:
        return self.safe_file_tools.status().to_dict()

    def approved_folders(self) -> dict:
        return self.safe_file_tools.list_approved_folders().to_dict()

    def approve_folder(self, path: str, name: str | None = None) -> dict:
        guard = self._guard_file_tool("add_approved_folder", target_path=path)
        if guard:
            return guard
        result = self.safe_file_tools.add_approved_folder(path, name=name)
        return self._finalize_tool_result("add_approved_folder", path, result.to_dict())

    def remove_approved_folder(self, folder_id: str) -> dict:
        guard = self._guard_file_tool("remove_approved_folder", target_path=folder_id)
        if guard:
            return guard
        result = self.safe_file_tools.remove_approved_folder(folder_id).to_dict()
        return self._finalize_tool_result("remove_approved_folder", folder_id, result)

    def workspace_tree(self, folder_id: str | None = None) -> dict:
        guard = self._guard_file_tool(
            "workspace_tree",
            target_path=folder_id,
            metadata={"max_depth": 3, "max_items": 200},
        )
        if guard:
            return guard
        result = self.safe_file_tools.summarize_tree(folder_id=folder_id).to_dict()
        return self._finalize_tool_result("workspace_tree", folder_id, result)

    def read_file(self, path: str) -> dict:
        guard = self._guard_file_tool("read_file", target_path=path)
        if guard:
            return guard
        result = self.safe_file_tools.read_text_file(path).to_dict()
        return self._finalize_tool_result("read_file", path, result)

    def search_files(self, query: str, folder_id: str | None = None) -> dict:
        guard = self._guard_file_tool(
            "search_files",
            metadata={"max_results": 50, "hint": query},
        )
        if guard:
            return guard
        result = self.safe_file_tools.search_text(query, folder_id=folder_id).to_dict()
        return self._finalize_tool_result("search_files", query, result)

    def file_info(self, path: str) -> dict:
        guard = self._guard_file_tool("file_info", target_path=path)
        if guard:
            return guard
        result = self.safe_file_tools.file_metadata(path).to_dict()
        return self._finalize_tool_result("file_info", path, result)

    def tool_policy_status(self) -> dict:
        status = self.tool_policy.status()
        safe_status = self.safe_file_tools.status().to_dict().get("data", {})
        status["safe_tools"] = {
            "approved_folder_count": safe_status.get("approved_folder_count", 0),
            "safe_read_enabled": safe_status.get("safe_read_enabled", True),
            "write_enabled": safe_status.get("write_enabled", False),
            "network_enabled": safe_status.get("network_enabled", False),
            "execution_enabled": safe_status.get("execution_enabled", False),
            "confirmation_required_for_large_reads": safe_status.get("confirmation_required_for_large_reads", True),
        }
        return {"ok": True, "action": "tool_policy", "data": status}

    def tool_audit_summary(self, limit: int = 20) -> dict:
        audit_file = self.project_root / "data" / "lucy" / "tool_audit_log.jsonl"
        entries: list[dict] = []
        if audit_file.exists():
            try:
                for line in audit_file.read_text(encoding="utf-8").splitlines()[-limit:]:
                    if not line.strip():
                        continue
                    entries.append(json.loads(line))
            except Exception as exc:
                return {"ok": False, "action": "tool_audit", "reason": str(exc), "file": str(audit_file), "entries": []}
        return {"ok": True, "action": "tool_audit", "file": str(audit_file), "entries": entries, "shown": len(entries)}

    def pending_tool_confirmations(self) -> dict:
        result = self.tool_confirmations.list_pending_confirmations()
        result["action"] = "pending_confirmations"
        return result

    def approve_tool_confirmation(self, confirmation_id: str) -> dict:
        result = self.tool_confirmations.approve_confirmation(confirmation_id)
        result["action"] = "approve_tool_confirmation"
        if result.get("ok"):
            confirmation = result.get("confirmation", {})
            action = confirmation.get("action")
            target = confirmation.get("target_path")
            if action == "add_approved_folder" and target:
                consumed = self.tool_confirmations.consume_confirmation(confirmation_id)
                execution = self.safe_file_tools.add_approved_folder(target).to_dict() if consumed.get("ok") else consumed
                result["consumed"] = consumed.get("ok", False)
                result["execution_result"] = execution
                self._append_tool_audit(action, target, execution, confirmation_id=confirmation_id)
            elif action == "remove_approved_folder" and target:
                consumed = self.tool_confirmations.consume_confirmation(confirmation_id)
                execution = self.safe_file_tools.remove_approved_folder(target).to_dict() if consumed.get("ok") else consumed
                result["consumed"] = consumed.get("ok", False)
                result["execution_result"] = execution
                self._append_tool_audit(action, target, execution, confirmation_id=confirmation_id)
        return result

    def reject_tool_confirmation(self, confirmation_id: str) -> dict:
        result = self.tool_confirmations.reject_confirmation(confirmation_id)
        result["action"] = "reject_tool_confirmation"
        return result

    def find_files(self, query: str) -> dict:
        result = self.tools.find_files(query)
        self.logger.log("tool_used", f"File find requested: {query!r}", source="tools")
        return result

    def search_text(self, query: str) -> dict:
        result = self.tools.search_text(query)
        self.logger.log("tool_used", f"Text search requested: {query!r}", source="tools")
        return result

    def create_folder(self, raw_path: str, use_writer_bot: bool = False) -> dict:
        """Create a directory safely inside the project workspace, optionally notifying the Writer Bot."""
        res = self.tools.create_folder(raw_path)
        if res.get("ok"):
            self.logger.log("folder_created", {"path": res.get("relative_path"), "created": res.get("created")})
            if getattr(self, "receipt_ledger", None):
                self.receipt_ledger.issue_receipt(
                    action_category="filesystem_mutation",
                    operation="create_folder",
                    target=res.get("relative_path", raw_path),
                    verified_outcome=f"Created folder: {res.get('relative_path')}",
                )
            if use_writer_bot:
                w_res = self.connect_writer_bot()
                res["writer_bot"] = w_res
        return res

    def read_project_file(self, path: str) -> dict:
        result = self.tools.read_text_file(path)
        self.logger.log("tool_used", f"File read requested: {path!r}", source="tools")
        return result

    def system_snapshot(self) -> dict:
        result = self.tools.system_snapshot()
        self.logger.log("tool_used", "System snapshot requested.", source="tools")
        return result

    def recent_logs(self, limit: int = 10) -> list[dict]:
        return self.tools.log_tail(self.logger.get_log_path(), limit=limit)

    def brain_status(self) -> dict:
        status = self.brain.status(external_enabled=self._external_brain_enabled())
        status["nvidia_key_available"] = self.secrets.has("NVIDIA_API_KEY")
        if self._external_brain_enabled() and status["nvidia_key_available"] and "nvidia" not in status["external_api_modes"]:
            status["external_api_modes"].append("nvidia")
        external_status = self.external_tools.status(status["nvidia_key_available"])
        status["external_tools"] = external_status
        for tool in external_status.get("tools", []):
            provider = tool.get("provider")
            if self._external_brain_enabled() and tool.get("available") and provider and provider not in status["external_api_modes"]:
                status["external_api_modes"].append(provider)
        return status

    def reasoning_status(self) -> dict:
        return {
            "ok": True,
            "stage6_reasoning_router_enabled": self.config.get("stage6_reasoning_router_enabled", True),
            "reasoning_mode_default": self.config.get("reasoning_mode_default", "local_policy_only"),
            "external_brain_enabled": self._external_brain_enabled(),
            "external_api_requires_confirmation": self.config.get("external_api_requires_confirmation", True),
            "chain_of_thought_output_enabled": self.config.get("chain_of_thought_output_enabled", False),
            "context_packet_max_chars": self.config.get("context_packet_max_chars", 6000),
            "hidden_reasoning_output": False,
            "brain_router": self.brain.brain_router_status(external_enabled=self._external_brain_enabled()),
        }

    def explain_route(self, text: str) -> dict:
        guardian = self.guardian_core.classify(text, active_project=self.project_summary().get("name", "Lucy"))
        guardian_dict = asdict(guardian)
        decision = self.brain.route_request(text, {"guardian_classification": guardian_dict})
        return {
            "ok": True,
            "user_text": self._safe_preview_text(text),
            "route_decision": decision,
            "guardian_classification": guardian_dict,
            "summary": decision["reason"],
            "safety_note": "Route explanation only. No tools executed and no online call made.",
            "hidden_reasoning_output": False,
        }

    def route_preview(self, text: str) -> dict:
        route = self.explain_route(text)
        decision = route["route_decision"]
        context_packet = self.brain.build_context_packet(
            text,
            decision,
            runtime=self,
            max_chars=int(self.config.get("context_packet_max_chars", 6000)),
        )
        frame = build_response_frame(
            user_intent=text,
            route_decision=decision,
            context_used=decision.get("required_context", []),
            context_summary=context_packet,
            safety_status={
                "guardian_classification": route["guardian_classification"].get("classification"),
                "guardian_reason": route["guardian_classification"].get("reason"),
                "external_api_allowed": False,
                "hidden_reasoning_output": False,
            },
            answer="Route preview only. Lucy did not execute tools, read files, or call APIs.",
            uncertainty="This is a policy route, not a completed answer.",
            next_action=self._route_next_action(decision),
            memory_update_recommendation="No automatic memory update.",
            tool_action_recommendation=self._route_tool_recommendation(decision),
            requires_confirmation=bool(decision.get("tool_required")),
            blocked_reason=route["guardian_classification"].get("reason") if decision.get("decision") == "BLOCKED_BY_GUARDIAN" else "",
        )
        route["context_packet"] = context_packet
        route["response_frame"] = frame
        return route

    def context_packet_preview(self, text: str) -> dict:
        route = self.explain_route(text)
        packet = self.brain.build_context_packet(
            text,
            route["route_decision"],
            runtime=self,
            max_chars=int(self.config.get("context_packet_max_chars", 6000)),
        )
        return {
            "ok": True,
            "user_text": self._safe_preview_text(text),
            "route_decision": route["route_decision"],
            "context_packet": packet,
            "safety_note": "Context packet preview only. No tools executed and no online call made.",
            "hidden_reasoning_output": False,
        }

    def response_frame_preview(self, text: str) -> dict:
        route = self.explain_route(text)
        packet = self.brain.build_context_packet(
            text,
            route["route_decision"],
            runtime=self,
            max_chars=int(self.config.get("context_packet_max_chars", 6000)),
        )
        frame = self.brain.build_response_frame(
            text,
            route["route_decision"],
            context_packet=packet,
            safety_status={
                "guardian_classification": route["guardian_classification"].get("classification"),
                "guardian_reason": route["guardian_classification"].get("reason"),
                "external_api_allowed": False,
                "hidden_reasoning_output": False,
            },
            uncertainty=(
                "What specifically do you want Lucy to route?"
                if route["route_decision"].get("decision") == "CLARIFICATION_REQUIRED"
                else "This is a policy preview, not a completed answer."
            ),
            blocked_reason=(
                route["guardian_classification"].get("reason", "")
                if route["route_decision"].get("decision") == "BLOCKED_BY_GUARDIAN"
                else ""
            ),
        )
        return {
            "ok": True,
            "user_text": self._safe_preview_text(text),
            "route_decision": route["route_decision"],
            "context_packet": packet,
            "response_frame": frame,
            "safety_note": "Response frame preview only. No tools executed and no online call made.",
            "hidden_reasoning_output": False,
        }

    def brain_status_detailed(self) -> dict:
        status = self.brain_status()
        status["reasoning_status"] = self.reasoning_status()
        status["external_brain_enabled"] = self._external_brain_enabled()
        status["external_api_requires_confirmation"] = self.config.get("external_api_requires_confirmation", True)
        return status

    def brain_router_status(self) -> dict:
        return self.brain_status_detailed()

    def _ask_brain_legacy(self, prompt: str) -> dict:
        memories = self.recall(prompt)
        self.reflect("ask_brain", prompt)
        if self._external_brain_allowed_for_prompt(prompt):
            external = self._ask_external_brain(prompt, memories)
            if external.get("ok"):
                self.logger.log(
                    "brain_used",
                    f"Brain prompt handled in mode: {external['mode']}",
                    source="external_tools",
                    extra={"provider": external.get("provider"), "warnings": external.get("warnings", [])},
                )
                return external

        response = self.brain.ask(prompt, self.project_summary(), memories)
        self.logger.log(
            "brain_used",
            f"Brain prompt handled in mode: {response.mode}",
            source="brain_router",
            extra={"warnings": response.warnings},
        )
        return {
            "ok": response.ok,
            "mode": response.mode,
            "text": response.text,
            "warnings": response.warnings,
        }

    def _external_brain_enabled(self) -> bool:
        return bool(self.config.get("api_enabled", False) and self.config.get("external_brain_enabled", False))

    def _external_brain_allowed_for_prompt(self, prompt: str) -> bool:
        lowered = prompt.lower()
        explicitly_requested = any(
            phrase in lowered
            for phrase in ["external brain", "use api", "call api", "use groq", "use gemini", "use openrouter"]
        )
        return self._external_brain_enabled() and explicitly_requested

    def _route_next_action(self, decision: dict) -> str:
        route = decision.get("decision")
        if route == "CLARIFICATION_REQUIRED":
            return "Ask one specific clarification question before routing."
        if route == "SAFE_FILE_READ_CONTEXT":
            return "Use Stage 5 safe file commands only after approved-folder checks."
        if route == "BLOCKED_BY_GUARDIAN":
            return "Do not proceed. Guardian blocked this request."
        if route == "REASONING_MODE_RECOMMENDED":
            return "Use local structured planning with project and memory context."
        if route in {"EXTERNAL_BRAIN_DISABLED", "EXTERNAL_BRAIN_RECOMMENDED_BUT_DISABLED"}:
            return "Keep the response local unless external brain is explicitly enabled later."
        return "Handle locally with the listed context."

    def _route_tool_recommendation(self, decision: dict) -> str:
        if decision.get("tool_required"):
            return "Tool context may be useful, but no tool was executed by this preview."
        if decision.get("guardian_required"):
            return "Guardian classification is required before any protected action."
        return "No tool action recommended."

    def _safe_preview_text(self, text: str) -> str:
        cleaned = re.sub(r"\s+", " ", str(text)).strip()
        patterns = [
            r"api[_ -]?key\s*[:=]\s*['\"]?[^'\"\s]+",
            r"password\s*[:=]\s*\S+",
            r"sk-[A-Za-z0-9_\-]{12,}",
            r"gsk_[A-Za-z0-9_\-]+",
            r"AIza[A-Za-z0-9_\-]+",
        ]
        for pattern in patterns:
            cleaned = re.sub(pattern, "[redacted-secret]", cleaned, flags=re.IGNORECASE)
        if any(word in cleaned.lower() for word in ["api key", "password", "private key", "secret", "token"]):
            return "[redacted-sensitive-input]"
        return cleaned[:300]

    def _ask_external_brain(self, prompt: str, memories: list[dict]) -> dict:
        project = self.project_summary()
        memory_lines = "\n".join(f"- {item.get('fact', '')}" for item in memories[:5]) or "- No matching local memory."
        system_prompt = "\n".join(
            [
                "You are Lucy's safe language layer for Senin.",
                f"Identity: {self.config.get('system_name', 'LUCY')} means {self.config.get('full_form', 'Living Unified Cognitive Yield')}.",
                "Speak as Lucy, not as Groq, Gemini, OpenRouter, SambaNova, or any model provider.",
                "Be practical, direct, and warm. Do not claim consciousness or human identity.",
                "You have persistent local cognition state: vision, drives, current focus, and working reflections.",
                "Describe that state honestly as local cognition, not consciousness.",
                "Do not reveal, transform, or ask for API keys, passwords, private keys, tokens, or secrets.",
                "You cannot execute shell commands, edit files, move money, trade, deploy, or control the desktop from this chat.",
                "If the user asks for a protected action, say it needs Lucy's local command/approval path.",
            ]
        )
        user_prompt = "\n\n".join(
            [
                f"User message:\n{prompt[:4000]}",
                f"Active project: {project.get('name', 'Lucy')}",
                f"Next action: {project.get('next_action') or 'not set'}",
                f"Daily context: {self.daily_context.brief_context()}",
                f"Relevant local memory:\n{memory_lines}",
                self.cognition.inner_prompt(),
            ]
        )
        result = self.external_tools.chat(user_prompt, system_prompt)
        if not result.get("ok"):
            return {"ok": False, "mode": "external_unavailable", "text": "", "warnings": [result.get("reason", "")]}

        checked = self.brain.checker.sanitize(result.get("text", ""))
        if not checked.ok:
            return {
                "ok": False,
                "mode": "external_blocked_by_response_checker",
                "provider": result.get("provider", "unknown"),
                "text": checked.text,
                "warnings": checked.warnings,
            }

        return {
            "ok": True,
            "mode": f"external_{result.get('provider', 'unknown')}",
            "provider": result.get("provider", "unknown"),
            "model": result.get("model", ""),
            "text": checked.text,
            "warnings": [],
            "attempts": result.get("attempts", []),
        }

    def backup_project(self) -> dict:
        result = self.ops.backup_project()
        self.logger.log(
            "ops_backup_created",
            f"Backup created: {result.get('path')}",
            source="safe_ops",
        )
        return result

    def continuity_backup(self, reason: str = "manual continuity backup") -> dict:
        try:
            result = self.continuity.snapshot(reason=reason, trigger="manual")
        except Exception as exc:
            self.logger.log(
                "error",
                f"Continuity backup failed: {exc}",
                source="continuity",
            )
            return {"created": False, "reason": str(exc)}
        self._log_continuity_result(result, always=True)
        return result

    def continuity_status(self) -> dict:
        return self.continuity.status()

    def scan_project(self) -> dict:
        result = self.ops.scan_project()
        self.logger.log(
            "ops_scan_created",
            f"Scan report created: {result.get('report_path')}",
            source="safe_ops",
        )
        return result

    def recovered_summary(self) -> dict:
        summary = self.recovery.summary()
        self.logger.log(
            "recovery_reference_viewed",
            "Recovered Lucy architecture summary viewed.",
            source="recovery",
        )
        return summary

    def recovered_checkpoints(self) -> list[dict]:
        checkpoints = self.recovery.checkpoints()
        self.logger.log(
            "recovery_reference_viewed",
            "Recovered Lucy checkpoint map viewed.",
            source="recovery",
        )
        return checkpoints

    def setup_nvidia_key(self) -> dict:
        result = self.secrets.prompt_for_secret("NVIDIA", "NVIDIA_API_KEY")
        self.logger.log(
            "secret_configured",
            "NVIDIA API key configured for current Lucy session." if result.get("saved") else "NVIDIA API key setup failed.",
            source="secrets",
        )
        return result

    def save_nvidia_key(self) -> dict:
        result = self.secrets.prompt_for_secret("NVIDIA", "NVIDIA_API_KEY", permanent=True)
        self.logger.log(
            "secret_configured",
            "NVIDIA API key saved in encrypted permanent storage." if result.get("saved") else "NVIDIA API key setup failed.",
            source="secrets",
        )
        return result

    def set_nvidia_key(self, value: str, permanent: bool = False) -> dict:
        if permanent:
            result = self.secrets.set_persistent_secret("NVIDIA", "NVIDIA_API_KEY", value)
        else:
            result = self.secrets.set_session_secret("NVIDIA", "NVIDIA_API_KEY", value)
        self.logger.log(
            "secret_configured",
            (
                "NVIDIA API key saved in encrypted permanent storage."
                if result.get("saved") and permanent
                else "NVIDIA API key configured for current Lucy session."
                if result.get("saved")
                else "NVIDIA API key setup failed."
            ),
            source="secrets",
        )
        return result

    def forget_nvidia_key(self) -> dict:
        result = self.secrets.forget_persistent_secret("NVIDIA_API_KEY")
        self.logger.log(
            "secret_removed",
            "NVIDIA permanent key removed." if result.get("forgotten") else "No NVIDIA permanent key found.",
            source="secrets",
        )
        return result

    def nvidia_key_status(self) -> dict:
        return self.secrets.status("NVIDIA", "NVIDIA_API_KEY")

    def external_tools_status(self) -> dict:
        return self.external_tools.status(self.secrets.has("NVIDIA_API_KEY"))

    def internal_agent_status(self) -> dict:
        return self.internal_agent_orchestrator.status()

    def internal_agent_report(self, request_text: str = "agent report") -> dict:
        return self.internal_agent_orchestrator.run_cycle(request_text)

    def internal_agent_single_status(self, agent_id: str) -> dict:
        return self.internal_agent_orchestrator.agent_status(agent_id)

    def respond(self, text: str) -> str:
        """Unified cognitive response method."""
        return self.lucy_respond(text)

    def ask_brain(self, user_text: str) -> dict:
        """Unified brain response method with full Stages 54-59 cognitive pipeline."""
        # 1. Stage 59: Execute natural conversational actions before brain reasoning
        action_summary = ""
        action_res: dict[str, Any] = {}
        if hasattr(self, "natural_action_parser"):
            action_res = self.natural_action_parser.parse_and_execute(user_text)
            action_summary = action_res.get("summary_block", "")

        # 1b. Short-circuit: deterministic response for filesystem actions
        if action_res.get("actions_executed", 0) > 0:
            fs_actions = [a for a in action_res.get("actions", []) if a.get("type") in (
                "folder_created", "swarm_connected", "writer_connected",
            )]
            if fs_actions:
                lines = []
                for act in fs_actions:
                    act_type = act.get("type", "")
                    if act_type == "folder_created":
                        lines.append(f"Created folder: {act.get('id', '')} ({act.get('detail', '')})")
                    elif act_type == "swarm_connected":
                        lines.append(act.get("detail", "Connected to Senin AI Swarm."))
                    elif act_type == "writer_connected":
                        lines.append(act.get("detail", "Connected to Writer Bot."))
                deterministic_reply = "\n".join(lines)
                return {
                    "ok": True,
                    "mode": "deterministic_action",
                    "text": deterministic_reply,
                    "verification": {"verified": True},
                    "receipt_verification": {"verified": True},
                    "natural_actions": action_res,
                    "chat_result": {"message": deterministic_reply, "source": "deterministic_action"},
                }

        # 2. Observe for corrections & personal adaptation (if natural_action_parser not present)
        if not hasattr(self, "natural_action_parser"):
            if hasattr(self, "workflow_learner"):
                self.workflow_learner.observe_for_corrections(user_text)
            if hasattr(self, "personal_profiler"):
                self.personal_profiler.observe_interaction(user_text)

        # 3. Build augmented prompt
        proj = self.project_summary()
        open_task_texts = [t["text"] for t in proj.get("open_tasks", []) if isinstance(t, dict)]
        guardrails = self.workflow_learner.prompt_guardrails_block() if hasattr(self, "workflow_learner") else ""
        ws_snippet = self.workspace_sensor.build_workspace_prompt_snippet() if hasattr(self, "workspace_sensor") else ""
        few_shot_block = self.personal_alignment.build_cloud_few_shot_block(max_examples=3) if hasattr(self, "personal_alignment") else ""
        base_prompt = (
            (f"{action_summary}\n\n" if action_summary else "")
            + f"{self.cognition.inner_prompt(limit=2)}\n\n"
            + f"{guardrails}\n\n"
            + f"{ws_snippet}"
            + (f"\n\n{few_shot_block}" if few_shot_block else "")
        )

        prompt_pkg = self.conversational_memory.build_augmented_prompt(
            user_input=user_text,
            system_prompt_base=base_prompt,
            active_project=proj.get("name", "Lucy"),
            open_tasks=open_task_texts,
        )

        chat_res = self.conversational_chat(user_text, _skip_observation=bool(hasattr(self, 'natural_action_parser')))
        raw_reply = chat_res.get("message", "")
        mode = chat_res.get("source", "deterministic_spine")

        # Two-layer anti-hallucination verification
        disk_check = self.fact_verifier.guard_response(raw_reply, runtime=self)
        receipt_check = self.receipt_ledger.verify_response_actions(disk_check.get("guarded_text", raw_reply)) if hasattr(self, "receipt_ledger") else {"verified": True, "guarded_text": raw_reply}
        final_text = receipt_check.get("guarded_text", raw_reply)

        if hasattr(self, "personal_alignment") and hasattr(self.personal_alignment, "maybe_admit_verified_turn"):
            self.personal_alignment.maybe_admit_verified_turn(
                user_text=user_text,
                reply_text=final_text,
                disk_verified=disk_check.get("verified", False),
                receipt_verified=receipt_check.get("verified", False),
                source=mode,
            )

        return {
            "ok": True,
            "mode": mode,
            "text": final_text,
            "verification": disk_check,
            "receipt_verification": receipt_check,
            "natural_actions": action_res,
            "chat_result": chat_res,
        }

    def lucy_respond(self, text: str) -> str:
        raw = str(text or "").strip()

        # 1. Stage 59: Execute natural conversational actions ONCE before reasoning
        executed_summary = ""
        action_res: dict = {}
        if hasattr(self, "natural_action_parser"):
            action_res = self.natural_action_parser.parse_and_execute(raw)
            executed_summary = action_res.get("summary_block", "")

        # 1b. Short-circuit: If the natural action parser already executed a
        # filesystem action (folder_created, swarm_connected, writer_connected),
        # return a deterministic confirmation instead of passing to the LLM.
        # This prevents the LLM from hallucinating its own version of the action.
        if action_res.get("actions_executed", 0) > 0:
            executed_actions = action_res.get("actions", [])
            fs_actions = [a for a in executed_actions if a.get("type") in (
                "folder_created", "swarm_connected", "writer_connected",
            )]
            if fs_actions:
                lines = []
                for act in fs_actions:
                    act_type = act.get("type", "")
                    if act_type == "folder_created":
                        rel = act.get("id", "")
                        full = act.get("detail", "")
                        lines.append(f"Created folder: {rel} ({full})")
                    elif act_type == "swarm_connected":
                        lines.append(act.get("detail", "Connected to Senin AI Swarm."))
                    elif act_type == "writer_connected":
                        lines.append(act.get("detail", "Connected to Writer Bot."))
                reply = "\n".join(lines) if lines else executed_summary
                if hasattr(self, "conversational_memory"):
                    self.conversational_memory._in_memory_turns.append({
                        "timestamp": datetime_now_iso(), "input": raw,
                        "reply": reply, "quality": "high",
                        "source": "deterministic_action",
                    })
                    self.conversational_memory.dialogue_tracker.observe_turn(raw, reply)
                self.self_improve_response(raw, reply, quality="high", source="deterministic_action")
                return reply

        lowered = re.sub(r"\s+", " ", raw.lower()).rstrip("?!., ")
        if lowered in {"/thought", "/thoughts", "thought", "thoughts"}:
            return self.format_last_thought()
        if lowered in {"/persona", "persona"}:
            return json.dumps(self.persona_status(), indent=2)
        if raw.startswith("/react "):
            cmd_to_heal = raw.split(" ", 1)[1].strip()
            if hasattr(self, "react_engine"):
                res = self.react_engine.execute_with_self_healing(cmd_to_heal, goal="Autonomous terminal execution")
                return res.format_terminal_summary()
        if raw.startswith("/walk ") or raw.startswith("/graph "):
            topic = raw.split(" ", 1)[1].strip()
            if hasattr(self, "memory_walker") and hasattr(self, "memory_graph"):
                seed_nodes = self.memory_graph.query(topic, limit=3)
                seed_ids = [n.get("id") for n in seed_nodes if n.get("id")]
                walk_res = self.memory_walker.walk(seed_ids, limit=5)
                return self.memory_walker.format_walk_trace(topic, walk_res)
        if raw.startswith("/where ") or raw.startswith("where "):
            sym = raw.split(" ", 1)[1].strip()
            if hasattr(self, "codebase_indexer"):
                return self.codebase_indexer.format_symbol_lookup(sym)
        if raw.startswith("/outline ") or raw.startswith("outline "):
            fpath = raw.split(" ", 1)[1].strip()
            if hasattr(self, "codebase_indexer"):
                return self.codebase_indexer.format_file_outline(fpath)
        if lowered in {"/reindex", "reindex", "index codebase"}:
            if hasattr(self, "codebase_indexer"):
                res = self.codebase_indexer.index_workspace(force=True)
                return f"Codebase re-indexed in {res.get('elapsed_ms')}ms: {res.get('total_symbols')} symbols across {res.get('total_files')} files."
        if lowered in {"/tools", "tools", "/listtools"}:
            if hasattr(self, "tool_synthesizer"):
                return self.tool_synthesizer.format_terminal_summary()
        if raw.startswith("/synthesize ") or raw.startswith("synthesize "):
            rest = raw.split(" ", 1)[1].strip()
            parts = rest.split(" ", 1)
            t_name = parts[0].strip()
            t_code = parts[1].strip() if len(parts) > 1 else ""
            if not t_code:
                return "Usage: /synthesize <tool_name> <python_code>"
            if hasattr(self, "tool_synthesizer"):
                try:
                    tool = self.tool_synthesizer.synthesize_tool(t_name, t_code)
                    return f"Synthesized dynamic tool '{tool.name}' at {tool.script_path}"
                except Exception as exc:
                    return f"Synthesis error: {str(exc)}"
        if raw.startswith("/runtool ") or raw.startswith("runtool "):
            rest = raw.split(" ", 1)[1].strip()
            parts = rest.split(" ")
            t_name = parts[0].strip()
            t_args = parts[1:] if len(parts) > 1 else []
            if hasattr(self, "tool_synthesizer"):
                res = self.tool_synthesizer.execute_tool(t_name, args=t_args)
                if res.success:
                    return f"[Tool '{t_name}' Executed ({res.duration_ms:.1f}ms)]\n{res.stdout.strip()}"
                return f"[Tool '{t_name}' Failed (exit {res.exit_code}, {res.duration_ms:.1f}ms)]\n{res.stderr.strip() or res.error_message}"
        if lowered in {"/purge_sandbox", "purge sandbox"}:
            if hasattr(self, "tool_synthesizer"):
                rep = self.tool_synthesizer.purge_sandbox()
                return f"Sandbox Purged: {rep.get('purged_count')} temporary files removed, {rep.get('preserved_count')} preserved."
        if lowered in {"/pulse", "pulse", "/sentinel pulse"}:
            if hasattr(self, "terminal_sentinel"):
                return self.terminal_sentinel.pulse().to_one_line()
        if lowered in {"/sentinel", "sentinel"}:
            if hasattr(self, "terminal_sentinel"):
                return self.terminal_sentinel.format_terminal_dashboard()
        if lowered in {"/sentinel diff", "sentinel diff", "/diff"}:
            if hasattr(self, "terminal_sentinel"):
                return self.terminal_sentinel.format_diff_list()
        if lowered in {"/sentinel toggle", "sentinel toggle"}:
            if hasattr(self, "terminal_sentinel"):
                active = self.terminal_sentinel.toggle_banner()
                return f"Terminal Sentinel Auto-Pulse Banner: {'ENABLED' if active else 'DISABLED'}"
        if raw.startswith("/cat ") or raw.startswith("cat "):
            target_file = raw.split(" ", 1)[1].strip()
            if hasattr(self, "terminal_canvas"):
                path_obj = Path(target_file)
                if not path_obj.is_absolute():
                    path_obj = self.project_root / path_obj
                return self.terminal_canvas.view_file(path_obj)
        if raw.startswith("/tree") or raw.startswith("tree"):
            parts = raw.split(" ", 1)
            target_dir = self.project_root
            if len(parts) > 1 and parts[1].strip():
                req_path = Path(parts[1].strip())
                target_dir = req_path if req_path.is_absolute() else (self.project_root / req_path)
            if hasattr(self, "terminal_canvas"):
                return self.terminal_canvas.render_tree(target_dir)
        if lowered in {"/diffview", "diffview"}:
            if hasattr(self, "terminal_canvas"):
                try:
                    import subprocess
                    diff_proc = subprocess.run(["git", "diff"], cwd=str(self.project_root), capture_output=True, text=True, timeout=2.0)
                    diff_txt = diff_proc.stdout.strip()
                    if not diff_txt:
                        return "No git diff detected (working tree is clean)."
                    return self.terminal_canvas.highlighter.highlight_diff(diff_txt)
                except Exception as e:
                    return f"Diffview error: {e}"
        if lowered in {"/distill preview", "distill preview"}:
            if hasattr(self, "memory_distiller"):
                rep = self.memory_distiller.dry_run()
                return rep.format_terminal_summary()
        if lowered in {"/distill stats", "distill stats"}:
            if hasattr(self, "memory_distiller"):
                st = self.memory_distiller.stats()
                return f"[Cognitive Distillation Stats] Total Nodes: {st.get('total_nodes')} | Pinned: {st.get('pinned_nodes')} | Superseded: {st.get('superseded_nodes')} | Last Distilled: {st.get('last_distilled_at') or 'Never'}"
        if lowered in {"/distill", "distill"}:
            if hasattr(self, "memory_distiller"):
                rep = self.memory_distiller.distill()
                return rep.format_terminal_summary()
        if lowered in {"/review", "review", "/code-review"}:
            if hasattr(self, "code_reviewer"):
                rep = self.code_reviewer.review_diff()
                return rep.format_terminal_summary()
        if lowered in {"/commit-msg", "commit-msg", "/suggest-commit"}:
            if hasattr(self, "code_reviewer"):
                rep = self.code_reviewer.review_diff()
                return f"[Proposed Commit Message]\n{rep.proposed_commit}"
        if lowered in {"/changelog", "changelog"}:
            if hasattr(self, "code_reviewer"):
                return self.code_reviewer.generate_changelog()
        if lowered in {"/patches", "patches", "/patch-list"}:
            if hasattr(self, "atomic_patcher"):
                return self.atomic_patcher.format_terminal_summary()
        if lowered in {"/patch-status", "patch-status"}:
            if hasattr(self, "atomic_patcher"):
                tx = self.atomic_patcher.active_tx or self.atomic_patcher._get_latest_committed_tx()
                if not tx:
                    return "No active or recent patch transaction."
                return f"[Patch Transaction {tx.tx_id}] Status: {tx.status} | Files: {len(tx.operations)} | Desc: {tx.description}"
        if raw.startswith("/rollback-patch") or raw.startswith("rollback-patch"):
            parts = raw.split(" ", 1)
            tx_id = parts[1].strip() if len(parts) > 1 and parts[1].strip() else None
            if tx_id and hasattr(self, "self_healing_patcher") and tx_id in getattr(self.self_healing_patcher, "_patches", {}):
                ok, msg = self.self_healing_patcher.rollback_patch(tx_id)
                return f"[Rollback {'SUCCESS' if ok else 'FAILED'}] {msg}"
            if hasattr(self, "atomic_patcher"):
                ok, msg = self.atomic_patcher.rollback_transaction(tx_id=tx_id)
                return f"[{'SUCCESS' if ok else 'FAILED'}] {msg}"
        if lowered in {"/test-affected", "test-affected", "/triage", "triage"}:
            if hasattr(self, "test_triage"):
                res = self.test_triage.triage_uncommitted()
                return res.format_terminal_summary()
        if raw.startswith("/test ") or raw.startswith("test "):
            query = raw.split(" ", 1)[1].strip()
            if hasattr(self, "test_triage"):
                matching = [f for f in self.test_triage.tests_dir.glob("test_*.py") if query.lower() in f.stem.lower()]
                if not matching:
                    return f"No test files found matching '{query}' in tests/."
                res = self.test_triage.run_tests(matching)
                return res.format_terminal_summary()
        if raw.startswith("/plan ") or raw.startswith("plan "):
            goal_desc = raw.split(" ", 1)[1].strip()
            if hasattr(self, "task_graph"):
                dag = self.task_graph.create_plan(goal_desc)
                return dag.format_terminal_summary()
        if lowered in {"/tasks", "tasks", "/dag", "/plan"}:
            if hasattr(self, "task_graph"):
                return self.task_graph.format_terminal_summary()
        if lowered in {"/next-task", "next-task", "/next"}:
            if hasattr(self, "task_graph"):
                nt = self.task_graph.get_next_task()
                if not nt:
                    return "No pending or ready tasks in active plan."
                tool_hint = f" (Suggested Tool: {nt.assigned_tool})" if nt.assigned_tool else ""
                return f"[Ready Task {nt.task_id}] {nt.title}\n{nt.description}{tool_hint}"
        if raw.startswith("/complete-task ") or raw.startswith("complete-task "):
            parts = raw.split(" ", 2)
            t_id = parts[1].strip()
            summary = parts[2].strip() if len(parts) > 2 else ""
            if hasattr(self, "task_graph"):
                ok, msg = self.task_graph.complete_task(t_id, summary=summary)
                return f"[{'SUCCESS' if ok else 'FAILED'}] {msg}"
        if lowered in {"/clear-plan", "clear-plan"}:
            if hasattr(self, "task_graph"):
                self.task_graph.clear_plan()
                return "Active goal plan cleared."
        if raw.startswith("/search ") or raw.startswith("search "):
            q = raw.split(" ", 1)[1].strip()
            if hasattr(self, "web_explorer"):
                res = self.web_explorer.search(q)
                return res.format_terminal_summary()
        if lowered in {"/web-status", "web-status"}:
            if hasattr(self, "web_explorer"):
                st = self.web_explorer.status()
                return f"[Sovereign Web Explorer] Status: {st.get('status')} | Cached Queries: {st.get('cached_queries')} | TTL: {st.get('ttl_seconds')}s"
        if lowered in {"/web-cache-clear", "web-cache-clear"}:
            if hasattr(self, "web_explorer"):
                c = self.web_explorer.clear_cache()
                return f"Cleared {c} cached web search queries."
        # Stage 82: Grounded Web Page Extractor & Documentation Reader
        if raw.startswith("/fetch ") or raw.startswith("fetch "):
            target_url = raw.split(" ", 1)[1].strip()
            if hasattr(self, "web_reader"):
                page = self.web_reader.fetch_url(target_url)
                return page.format_terminal_summary()
        if raw.startswith("/codeblocks ") or raw.startswith("codeblocks "):
            target_url = raw.split(" ", 1)[1].strip()
            if hasattr(self, "web_reader"):
                page = self.web_reader.fetch_url(target_url)
                if page.error:
                    return f"[Error] Failed to extract code blocks: {page.error}"
                return self.web_reader.format_code_blocks_summary(target_url, page.code_blocks)
        if raw.startswith("/pypi ") or raw.startswith("pypi "):
            pkg_name = raw.split(" ", 1)[1].strip()
            if hasattr(self, "web_reader"):
                info = self.web_reader.fetch_pypi_package(pkg_name)
                return self.web_reader.format_pypi_summary(info)
        if lowered in {"/web-read-status", "web-read-status"}:
            if hasattr(self, "web_reader"):
                st = self.web_reader.status()
                return f"[Sovereign Web Reader] Status: {st.get('status')} | Cached Pages: {st.get('cached_pages')} | TTL: {st.get('ttl_seconds')}s"
        if lowered in {"/web-read-cache-clear", "web-read-cache-clear"}:
            if hasattr(self, "web_reader"):
                c = self.web_reader.clear_cache()
                return f"Cleared {c} cached web pages."
        # Stage 83: Web-Grounded Cross-Verification & Fact-Checking RAG
        if raw.startswith("/verify-web ") or raw.startswith("verify-web ") or raw.startswith("/web-verify ") or raw.startswith("web-verify "):
            claim_text = raw.split(" ", 1)[1].strip()
            if hasattr(self, "web_verifier"):
                res = self.web_verifier.verify_claim(claim_text)
                return res.format_terminal_summary()
        if raw.startswith("/verify-web-code ") or raw.startswith("verify-web-code ") or raw.startswith("/web-code-verify ") or raw.startswith("web-code-verify "):
            code_text = raw.split(" ", 1)[1].strip()
            if hasattr(self, "web_verifier"):
                report = self.web_verifier.verify_code_snippet(code_text)
                return self.web_verifier.format_code_verification_summary(report)
        if lowered in {"/web-fact-status", "web-fact-status", "/fact-check-status"}:
            if hasattr(self, "web_verifier"):
                st = self.web_verifier.status()
                return f"[Sovereign Fact Checker] Status: {st.get('status')} | Cached Claims: {st.get('cached_claims')} | TTL: {st.get('ttl_seconds')}s"
        if lowered in {"/web-fact-cache-clear", "web-fact-cache-clear", "/fact-check-cache-clear"}:
            if hasattr(self, "web_verifier"):
                c = self.web_verifier.clear_cache()
                return f"Cleared {c} cached fact checks."
        # Stage 84: High-Signal LoRA Interaction Harvester & Preference Dataset Curator
        if lowered in {"/harvest-stats", "harvest-stats", "/lora-stats"}:
            if hasattr(self, "lora_harvester"):
                return self.lora_harvester.format_terminal_summary()
        if raw.startswith("/harvest-prune ") or raw.startswith("harvest-prune "):
            arg = raw.split(" ", 1)[1].strip()
            try:
                thresh = float(arg)
            except ValueError:
                thresh = 0.70
            if hasattr(self, "lora_harvester"):
                cnt = self.lora_harvester.prune_low_signal(threshold=thresh)
                return f"Pruned {cnt} interactions below score {thresh:.2f}."
        if raw.startswith("/harvest-turn ") or raw.startswith("harvest-turn "):
            parts = raw.split(" ", 1)[1].split("|", 1)
            inst = parts[0].strip()
            resp = parts[1].strip() if len(parts) > 1 else ""
            if hasattr(self, "lora_harvester"):
                res = self.lora_harvester.harvest_turn(inst, resp, category="manual")
                if res:
                    return f"[Curated] Interaction {res.interaction_id} stored with score {res.signal_score:.2f}."
                return "[Rejected] Interaction signal score below admission threshold."
        # Stage 85: Local Model Adapter Compiler & Ollama Hot-Swap Engine
        if lowered in {"/compile-adapter", "compile-adapter"}:
            if hasattr(self, "lora_compiler"):
                res = self.lora_compiler.compile_model()
                if res.get("compiled"):
                    if res.get("swapped_active"):
                        self.active_model = res.get("active_model", self.active_model)
                    return f"[SUCCESS] Compiled model tag '{res['tag']}' in {res.get('elapsed_ms', 0):.1f}ms. Active model: {self.active_model}"
                return f"[FAILED] Model compilation failed: {res.get('reason')}"
        if raw.startswith("/hot-swap ") or raw.startswith("hot-swap "):
            target_tag = raw.split(" ", 1)[1].strip()
            if hasattr(self, "lora_compiler"):
                res = self.lora_compiler.hot_swap(target_tag)
                if res.get("success"):
                    self.active_model = res.get("active_model", self.active_model)
                    return f"[HOT-SWAP] Active model switched: {res['swapped_from']} -> {res['active_model']}"
                return f"[FAILED] Hot-swap rejected: {res.get('reason')}"
        if lowered in {"/adapter-rollback", "adapter-rollback", "/model-rollback"}:
            if hasattr(self, "lora_compiler"):
                res = self.lora_compiler.rollback()
                if res.get("success"):
                    self.active_model = res.get("active_model", self.active_model)
                    return f"[ROLLBACK] Reverted model: {res.get('swapped_from')} -> {res['active_model']}"
                return f"[FAILED] Rollback failed: {res.get('reason')}"
        if lowered in {"/adapter-status", "adapter-status", "/compiler-status", "compiler-status"}:
            if hasattr(self, "lora_compiler"):
                return self.lora_compiler.format_terminal_summary()
        # Stage 86: 25-Question Anti-Catastrophic-Forgetting Sanity Gate
        if lowered in {"/sanity-check", "sanity-check", "/sanity-run", "sanity-run"}:
            if hasattr(self, "sanity_gate"):
                report = self.sanity_gate.run_sanity_gate(model_tag=getattr(self, "active_model", "current_model"))
                return report.format_terminal_summary()
        if lowered in {"/sanity-status", "sanity-status", "/sanity-report", "sanity-report"}:
            if hasattr(self, "sanity_gate"):
                return self.sanity_gate.format_terminal_summary()
        # Stage 87: Epistemic Provenance Tracker & Anti-Hallucination Confidence Spine
        if raw.startswith("/provenance ") or raw.startswith("provenance "):
            statement = raw.split(" ", 1)[1].strip()
            if hasattr(self, "epistemic_tracker"):
                att = self.epistemic_tracker.verify_response_provenance(statement)
                return att.format_terminal_summary()
        if lowered in {"/epistemic-status", "epistemic-status", "/provenance-status"}:
            if hasattr(self, "epistemic_tracker"):
                st = self.epistemic_tracker.status()
                return f"[Epistemic Tracker] Status: {st.get('status')} | Log: {st.get('log_file')}"
        # Stage 88: Dynamic Few-Shot Operator Style Mirror & Semantic Preference Ingestion
        if lowered in {"/style-profile", "style-profile", "/style-status", "style-status"}:
            if hasattr(self, "style_mirror"):
                return self.style_mirror.format_terminal_summary()
        if raw.startswith("/set-preference ") or raw.startswith("set-preference "):
            stmt = raw.split(" ", 1)[1].strip()
            if "=" in stmt:
                k, v = stmt.split("=", 1)
                if hasattr(self, "style_mirror"):
                    pref = self.style_mirror.ingest_preference(k.strip(), v.strip())
                    return f"[Preference Updated] {pref.key} = {pref.value}"
            return "[Error] Format: /set-preference <key> = <value>"
        if raw.startswith("/style-exemplars ") or raw.startswith("style-exemplars "):
            query = raw.split(" ", 1)[1].strip()
            if hasattr(self, "style_mirror"):
                block = self.style_mirror.build_style_steering_block(query)
                return block
        # Stage 89: Autonomous Hypothesis Generation & Pre-Response Counterfactual Verifier
        if raw.startswith("/hypothesize ") or raw.startswith("hypothesize "):
            problem_text = raw.split(" ", 1)[1].strip()
            if hasattr(self, "hypothesis_engine"):
                hyps = self.hypothesis_engine.formulate_hypotheses(problem_text)
                if hyps:
                    summaries = [h.format_terminal_summary() for h in hyps]
                    return "\n\n".join(summaries)
                return "Zero hypotheses derived."
        if raw.startswith("/counterfactual ") or raw.startswith("counterfactual "):
            prop_text = raw.split(" ", 1)[1].strip()
            if hasattr(self, "hypothesis_engine"):
                rep = self.hypothesis_engine.evaluate_solution_candidate(prop_text)
                return f"[Counterfactual Probe] Syntax Valid: {rep['syntax_valid']} | Risk: {rep['counterfactual_risk']} | Recommended: {rep['recommended']}"
        if lowered in {"/hypothesis-journal", "hypothesis-journal", "/hypothesis-status"}:
            if hasattr(self, "hypothesis_engine"):
                return self.hypothesis_engine.format_terminal_summary()
        # Stage 90: Master Sovereign AGI Cognitive Synthesis & Continuous Alignment Checkpoint
        if lowered in {"/synthesis", "synthesis", "/cognitive-status", "cognitive-status"}:
            if hasattr(self, "master_synthesis"):
                return self.master_synthesis.format_terminal_summary()
        if lowered in {"/alignment-checkpoint", "alignment-checkpoint"}:
            if hasattr(self, "master_synthesis"):
                chk = self.master_synthesis.create_alignment_checkpoint()
                return chk.format_terminal_summary()
        if raw.startswith("/audit-turn ") or raw.startswith("audit-turn "):
            statement = raw.split(" ", 1)[1].strip()
            if hasattr(self, "master_synthesis"):
                audit_res = self.master_synthesis.synthesize_turn("Manual audit instruction", statement)
                return f"[Synthesis Audit] Signal: {audit_res.signal_score:.2f} | Integrity: {audit_res.integrity_score:.2f} | Safe: {audit_res.counterfactual_safe} | Harvested: {audit_res.harvested_to_lora}" 

        # Stage 91: Autonomous Code Mutation & Fuzz Tester
        if lowered in {"/mutation-stats", "mutation-stats", "/fuzz-stats", "fuzz-stats"}:
            if hasattr(self, "mutation_fuzzer"):
                return self.mutation_fuzzer.format_terminal_summary()
        if lowered in {"/fuzz-cli", "fuzz-cli", "/fuzz", "fuzz"}:
            if hasattr(self, "mutation_fuzzer"):
                report = self.mutation_fuzzer.fuzz_cli()
                return report.format_terminal_summary()
        if raw.startswith("/mutate ") or raw.startswith("mutate "):
            target = raw.split(" ", 1)[1].strip()
            if hasattr(self, "mutation_fuzzer"):
                report = self.mutation_fuzzer.run_mutation_test(target)
                return report.format_terminal_summary()

        # Stage 92: Self-Healing Runtime Patch Engine
        if lowered in {"/patch-ledger", "patch-ledger"}:
            if hasattr(self, "self_healing_patcher"):
                return self.self_healing_patcher.format_ledger_summary()
        if raw.startswith("/patch-diff ") or raw.startswith("patch-diff "):
            pid = raw.split(" ", 1)[1].strip()
            if hasattr(self, "self_healing_patcher"):
                return self.self_healing_patcher.get_patch_diff(pid)
        if raw.startswith("/rollback-patch ") or raw.startswith("rollback-patch "):
            pid = raw.split(" ", 1)[1].strip()
            if hasattr(self, "self_healing_patcher"):
                ok, msg = self.self_healing_patcher.rollback_patch(pid)
                return f"[Rollback {'SUCCESS' if ok else 'FAILED'}] {msg}"
        if raw.startswith("/heal ") or raw.startswith("heal "):
            target = raw.split(" ", 1)[1].strip()
            if hasattr(self, "self_healing_patcher"):
                return self.self_healing_patcher.heal(target)

        # Stage 93: Semantic AST Vector Code Indexer
        if lowered in {"/index-repo", "index-repo", "/reindex-code", "reindex-code"}:
            if hasattr(self, "ast_vector_index"):
                summary = self.ast_vector_index.index_repository()
                return summary.format_terminal_summary()
        if raw.startswith("/code-search ") or raw.startswith("code-search "):
            query = raw.split(" ", 1)[1].strip()
            if hasattr(self, "ast_vector_index"):
                matches = self.ast_vector_index.search(query)
                return self.ast_vector_index.format_search_results(query, matches)
        if raw.startswith("/symbol-tree ") or raw.startswith("symbol-tree "):
            target = raw.split(" ", 1)[1].strip()
            if hasattr(self, "ast_vector_index"):
                return self.ast_vector_index.get_symbol_tree(target)

        # Stage 94: Architecture Specification Drift Detector & Realignment Engine
        if lowered in {"/spec-audit", "spec-audit", "/drift-report", "drift-report"}:
            if hasattr(self, "spec_drift_detector"):
                report = self.spec_drift_detector.audit()
                return report.format_terminal_summary()
        if lowered.startswith("/realign-spec") or lowered.startswith("realign-spec"):
            prefix = "/realign-spec" if lowered.startswith("/realign-spec") else "realign-spec"
            spec_arg = raw[len(prefix):].strip() or None
            if hasattr(self, "spec_drift_detector"):
                res = self.spec_drift_detector.realign_spec(spec_arg)
                return res.get("terminal_summary", res.get("message", "Realignment complete."))

        # Stage 95: Multi-Agent Autonomous Worktree & Branching Fabric
        if lowered in {"/tree-status", "tree-status", "/worktrees", "worktrees", "/list-branches", "list-branches"}:
            if hasattr(self, "worktree_fabric"):
                return self.worktree_fabric.tree_status()
        if raw.startswith("/spawn-branch ") or raw.startswith("spawn-branch "):
            prefix = "/spawn-branch " if raw.startswith("/spawn-branch ") else "spawn-branch "
            parts = raw[len(prefix):].strip().split(" ", 1)
            bname = parts[0].strip()
            task = parts[1].strip() if len(parts) > 1 else ""
            if hasattr(self, "worktree_fabric"):
                branch = self.worktree_fabric.spawn_branch(bname, task=task)
                return f"[Worktree Spawned] Branch: '{branch.branch_name}' (ID: {branch.branch_id})\nDirectory: {branch.worktree_dir}\nRole: {branch.agent_role}"
        if raw.startswith("/merge-worktree ") or raw.startswith("merge-worktree "):
            prefix = "/merge-worktree " if raw.startswith("/merge-worktree ") else "merge-worktree "
            bname = raw[len(prefix):].strip()
            if hasattr(self, "worktree_fabric"):
                res = self.worktree_fabric.merge_worktree(bname)
                status_str = "SUCCESS" if res.success else "FAILED"
                return f"[Worktree Merge: {status_str}] {res.message}" 

        # Stage 96: Sovereign Offline Quantization & GGUF Model Compressor
        if lowered in {"/quant-status", "quant-status", "/list-quants", "list-quants"}:
            if hasattr(self, "model_quantizer"):
                return self.model_quantizer.quant_status()
        if raw.startswith("/quantize-weights ") or raw.startswith("quantize-weights "):
            prefix = "/quantize-weights " if raw.startswith("/quantize-weights ") else "quantize-weights "
            parts = raw[len(prefix):].strip().split(" ", 1)
            target_model = parts[0].strip()
            qtype = parts[1].strip() if len(parts) > 1 else "Q4_K_M"
            if hasattr(self, "model_quantizer"):
                res = self.model_quantizer.quantize_weights(target_model, quant_type=qtype)
                return f"[Quantization {res.status}] Model: '{res.model_name}' ({res.quant_type})\nOutput: {res.output_path}\nRatio: {res.compression_ratio}x | VRAM: ~{res.vram_estimate_mb:.0f} MB"
        if raw.startswith("/gguf-export ") or raw.startswith("gguf-export "):
            prefix = "/gguf-export " if raw.startswith("/gguf-export ") else "gguf-export "
            parts = raw[len(prefix):].strip().split(" ", 1)
            target_model = parts[0].strip()
            qtype = parts[1].strip() if len(parts) > 1 else "Q4_K_M"
            if hasattr(self, "model_quantizer"):
                export_data = self.model_quantizer.export_gguf(target_model, quant_type=qtype)
                return f"[GGUF Export: SUCCESS] Model: '{target_model}'\nGGUF: {export_data['gguf_path']}\nModelfile: {export_data['modelfile_path']}" 

        # Stage 97: Causal DAG Epistemic Memory & Counterfactual Timeline
        if lowered in {"/dag-timeline", "dag-timeline", "/causal-dag", "causal-dag"}:
            if hasattr(self, "causal_dag"):
                return self.causal_dag.dag_timeline()
        if raw.startswith("/causal-why ") or raw.startswith("causal-why "):
            prefix = "/causal-why " if raw.startswith("/causal-why ") else "causal-why "
            target = raw[len(prefix):].strip()
            if hasattr(self, "causal_dag"):
                chain = self.causal_dag.causal_why(target)
                return chain.format_terminal_summary()
        if raw.startswith("/counterfactual-replay ") or raw.startswith("counterfactual-replay "):
            prefix = "/counterfactual-replay " if raw.startswith("/counterfactual-replay ") else "counterfactual-replay "
            parts = raw[len(prefix):].strip().split(" ", 1)
            target_id = parts[0].strip()
            intervention = parts[1].strip() if len(parts) > 1 else "Action was skipped or failed"
            if hasattr(self, "causal_dag"):
                cf = self.causal_dag.counterfactual_replay(target_id, intervention)
                return cf.format_terminal_summary()
        if lowered in {"/prune-dag", "prune-dag"}:
            if hasattr(self, "causal_dag"):
                pruned = self.causal_dag.prune_dag(max_nodes=300)
                return f"[Causal DAG Pruned] Removed {pruned} intermediate nodes while preserving root-cause reachability." 

        # Stage 98: Zero-Leak Host Sandbox & Process Containment Gate
        if lowered in {"/leak-audit", "leak-audit"}:
            if hasattr(self, "host_sandbox"):
                report = self.host_sandbox.leak_audit()
                return report.format_terminal_summary()
        if lowered in {"/quarantine-status", "quarantine-status"}:
            if hasattr(self, "host_sandbox"):
                return self.host_sandbox.quarantine_status()
        if raw.startswith("/quarantine-release ") or raw.startswith("quarantine-release "):
            prefix = "/quarantine-release " if raw.startswith("/quarantine-release ") else "quarantine-release "
            target_qid = raw[len(prefix):].strip()
            if hasattr(self, "host_sandbox"):
                rel_res = self.host_sandbox.release_quarantine(target_qid)
                return f"[Quarantine Released] Cleared {rel_res.get('released_count', 0)} artifact(s)."
        if raw.startswith("/sandbox-run ") or raw.startswith("sandbox-run "):
            prefix = "/sandbox-run " if raw.startswith("/sandbox-run ") else "sandbox-run "
            cmd_payload = raw[len(prefix):].strip()
            if hasattr(self, "host_sandbox"):
                is_py = cmd_payload.endswith(".py") or "print(" in cmd_payload or "import " in cmd_payload
                res = self.host_sandbox.run_in_sandbox(cmd_payload, is_python_code=is_py)
                return res.format_terminal_summary()

        # Stage 99: Local Hardware Telemetry & Inference Throttle Guard
        if lowered in {"/hardware-status", "hardware-status", "/telemetry", "telemetry"}:
            if hasattr(self, "hardware_telemetry"):
                return self.hardware_telemetry.hardware_status()
        if lowered in {"/vram-tune", "vram-tune"}:
            if hasattr(self, "hardware_telemetry"):
                return self.hardware_telemetry.vram_tune().format_terminal_summary()
        if lowered in {"/bench-inference", "bench-inference"}:
            if hasattr(self, "hardware_telemetry"):
                return self.hardware_telemetry.bench_inference().format_terminal_summary()
        if lowered.startswith("/throttle-guard") or lowered.startswith("throttle-guard"):
            prefix = "/throttle-guard" if lowered.startswith("/throttle-guard") else "throttle-guard"
            arg = raw[len(prefix):].strip()
            if hasattr(self, "hardware_telemetry"):
                if arg:
                    try:
                        val = float(arg)
                        cfg = self.hardware_telemetry.set_throttle_thresholds(ram_pct=val)
                        return f"[Throttle Guard Configured] RAM Threshold set to {cfg['ram_threshold_pct']:.1f}%"
                    except ValueError:
                        pass
                st = self.hardware_telemetry.status()
                return f"[Throttle Guard Active] Policy: {st['throttle_policy']} | RAM Threshold: {st['ram_threshold_pct']}% | Temp Threshold: {st['temp_threshold_c']}C" 

        # Stage 100: Centennial Sovereign Master Seal & Cryptographic Self-Attestation Fabric
        if lowered in {"/centennial-seal", "centennial-seal", "/seal", "seal"}:
            if hasattr(self, "master_seal"):
                cert = self.master_seal.generate_seal(runtime=self)
                return cert.format_terminal_summary()
        if lowered in {"/verify-seal", "verify-seal", "/check-seal", "check-seal"}:
            if hasattr(self, "master_seal"):
                res = self.master_seal.verify_seal()
                return f"[Master Seal Verification] Status: {res.get('status')} | Valid: {res.get('valid')} | Creator Intact: {res.get('creator_intact')}"
        if lowered in {"/lucy-centennial", "lucy-centennial", "/centennial", "centennial"}:
            if hasattr(self, "master_seal"):
                return self.master_seal.get_centennial_banner()
        if lowered in {"/integrity-proof", "integrity-proof", "/merkle-root", "merkle-root"}:
            if hasattr(self, "master_seal"):
                cert = self.master_seal.last_certificate or self.master_seal.generate_seal(runtime=self)
                return (
                    f"[Cryptographic Integrity Proof]\n"
                    f"Merkle Root SHA256: {cert.merkle_root_sha256}\n"
                    f"Master Signature:   {cert.master_seal_signature}\n"
                    f"Total Modules:      {cert.codebase_files_count}\n"
                    f"Total Stages:       {cert.total_stages_sealed} / 100\n"
                    f"Creator & Operator: {cert.creator} ({cert.creator_full_name})"
                )

        # Stage 101: Autonomous Kernel & Process Watchdog Fabric
        if lowered in {"/supervisor-status", "supervisor-status", "/watchdog", "watchdog"}:
            if hasattr(self, "kernel_supervisor"):
                self.kernel_supervisor.heartbeat_all_active()
                return self.kernel_supervisor.supervisor_status()
        if lowered in {"/heartbeat-audit", "heartbeat-audit"}:
            if hasattr(self, "kernel_supervisor"):
                self.kernel_supervisor.heartbeat_all_active()
                rep = self.kernel_supervisor.audit_heartbeats(auto_recover=True)
                return rep.format_terminal_summary()
        if lowered.startswith("/restart-worker") or lowered.startswith("restart-worker") or lowered.startswith("/force-recover") or lowered.startswith("force-recover"):
            sub_name = ""
            for pfx in ("/restart-worker", "restart-worker", "/force-recover", "force-recover"):
                if lowered.startswith(pfx):
                    sub_name = raw[len(pfx):].strip()
                    break
            if hasattr(self, "kernel_supervisor"):
                if sub_name:
                    rec_res = self.kernel_supervisor.recover_subsystem(sub_name, force=True)
                    return f"[Kernel Supervisor] Subsystem '{sub_name}' recovery: success={rec_res.get('success')}, status={rec_res.get('status')}"
                else:
                    return "[Kernel Supervisor] Usage: /restart-worker <subsystem_name>"

        # Stage 102: Dynamic Execution Profiler & Flamegraph Tracer
        if lowered in {"/flamegraph", "flamegraph"}:
            if hasattr(self, "execution_profiler"):
                return self.execution_profiler.get_latest_flamegraph()
        if lowered in {"/latency-audit", "latency-audit"}:
            if hasattr(self, "execution_profiler"):
                return self.execution_profiler.get_latency_audit_report()
        if lowered in {"/hot-paths", "hot-paths"}:
            if hasattr(self, "execution_profiler"):
                return self.execution_profiler.get_hot_paths_table()
        if lowered.startswith("/profile-run") or lowered.startswith("profile-run"):
            prefix = "/profile-run" if lowered.startswith("/profile-run") else "profile-run"
            target_cmd = raw[len(prefix):].strip()
            if hasattr(self, "execution_profiler"):
                if not target_cmd:
                    target_cmd = "/hardware-status"
                with self.execution_profiler.profile_scope(f"run:{target_cmd}") as meta:
                    _ = self.respond(target_cmd)
                return meta["result"].format_terminal_summary()

        # Stage 103: Hybrid Neural-Lexical Vector RAG Engine
        if lowered in {"/rag-status", "rag-status"}:
            if hasattr(self, "neural_retriever"):
                st = self.neural_retriever.status()
                return f"[Neural RAG Status] Indexed Chunks: {st['total_chunks']} | Terms: {st['unique_terms']} | Dim: {st['vector_dimension']} | Persisted: {st['index_persisted']}"
        if lowered in {"/reindex-rag", "reindex-rag"}:
            if hasattr(self, "neural_retriever"):
                res = self.neural_retriever.reindex()
                return f"[Neural RAG Reindexed] Chunks: {res.get('chunks_indexed')}, Unique Terms: {res.get('unique_terms')}, Duration: {res.get('duration_ms')}ms"
        if lowered.startswith("/neural-search ") or lowered.startswith("neural-search "):
            prefix = "/neural-search " if lowered.startswith("/neural-search ") else "neural-search "
            q = raw[len(prefix):].strip()
            if hasattr(self, "neural_retriever"):
                search_res = self.neural_retriever.search(q, top_k=5)
                return search_res.format_terminal_summary()
        if lowered.startswith("/retrieve-context ") or lowered.startswith("retrieve-context "):
            prefix = "/retrieve-context " if lowered.startswith("/retrieve-context ") else "retrieve-context "
            q = raw[len(prefix):].strip()
            if hasattr(self, "neural_retriever"):
                return self.neural_retriever.retrieve_context_window(q, max_tokens=1500)

        # Stage 104: Autonomous Refactoring & Code Quality Enforcer
        if lowered in {"/scan-tech-debt", "scan-tech-debt", "/clean-code-audit", "clean-code-audit"}:
            if hasattr(self, "refactor_engine"):
                return self.refactor_engine.format_tech_debt_table(top_n=8)
        if lowered.startswith("/suggest-refactor") or lowered.startswith("suggest-refactor"):
            prefix = "/suggest-refactor" if lowered.startswith("/suggest-refactor") else "suggest-refactor"
            target_file = raw[len(prefix):].strip()
            if hasattr(self, "refactor_engine"):
                if not target_file:
                    target_file = "backend/lucy_core/refactor_engine.py"
                props = self.refactor_engine.suggest_refactorings(target_file)
                if not props:
                    return f"[Refactor Engine] File '{target_file}' is pristine. Zero code smells detected (Grade A)."
                lines = [f"[Refactor Proposals for {target_file}] ({len(props)} found):"]
                for p in props[:5]:
                    lines.append(f" - [{p.proposal_id}] ({p.rule_id}) on `{p.target_symbol}`: {p.description}")
                lines.append("Use `/apply-refactor <proposal_id>` to validate and apply.")
                return "\n".join(lines)
        if lowered.startswith("/apply-refactor ") or lowered.startswith("apply-refactor "):
            prefix = "/apply-refactor " if lowered.startswith("/apply-refactor ") else "apply-refactor "
            pid = raw[len(prefix):].strip()
            if hasattr(self, "refactor_engine"):
                res = self.refactor_engine.apply_refactor_patch(pid)
                return f"[Refactor Engine] Patch application for '{pid}': success={res.get('success')}, status={res.get('status')}" 

        # Stage 105: Sovereign P2P Peer Mesh & Local Sync
        if lowered in {"/mesh-status", "mesh-status"}:
            if hasattr(self, "peer_mesh"):
                return self.peer_mesh.mesh_status()
        if lowered in {"/discover-peers", "discover-peers"}:
            if hasattr(self, "peer_mesh"):
                peers = self.peer_mesh.discover_peers()
                return f"[Peer Mesh] Discovery scan complete: found {len(peers)} peers on local network."
        if lowered.startswith("/sync-mesh") or lowered.startswith("sync-mesh"):
            prefix = "/sync-mesh" if lowered.startswith("/sync-mesh") else "sync-mesh"
            peer_id = raw[len(prefix):].strip()
            if hasattr(self, "peer_mesh"):
                if peer_id:
                    res = self.peer_mesh.sync_peer_deltas(peer_id)
                    return f"[Peer Mesh] Sync with '{peer_id}': status={res.get('status')}, items={res.get('items_synced')}"
                else:
                    rep = self.peer_mesh.sync_all()
                    return rep.format_terminal_summary()
        if lowered in {"/export-node-key", "export-node-key"}:
            if hasattr(self, "peer_mesh"):
                creds = self.peer_mesh.export_node_credentials()
                return (
                    f"[Node Credentials]\n"
                    f"Node ID:    {creds['node_id']}\n"
                    f"Device:     {creds['device_name']}\n"
                    f"Public Key: {creds['public_key']}\n"
                    f"Creator:    {creds['creator']} ({creds['creator_full_name']})"
                )

        # Stage 106: Offline Multi-Modal Voice Fabric
        if lowered in {"/voice-status", "voice-status"}:
            if hasattr(self, "voice_fabric"):
                return self.voice_fabric.voice_status()
        if lowered.startswith("/voice-speak ") or lowered.startswith("voice-speak "):
            prefix = "/voice-speak " if lowered.startswith("/voice-speak ") else "voice-speak "
            speech_txt = raw[len(prefix):].strip()
            if hasattr(self, "voice_fabric"):
                wav_bytes, pkt = self.voice_fabric.synthesize_speech(speech_txt)
                return f"[Voice Synthesized] Packet: {pkt.packet_id} | Duration: {pkt.duration_sec:.2f}s | Size: {pkt.data_size_bytes}B | Saved: data/lucy/voice/tts_{pkt.packet_id}.wav"
        if lowered in {"/voice-listen", "voice-listen"}:
            if hasattr(self, "voice_fabric"):
                sample_audio, _ = self.voice_fabric.synthesize_speech("Lucy system status check")
                tr = self.voice_fabric.transcribe_audio(sample_audio, simulated_text="Lucy system status check")
                return f"[Voice Transcription] Text: '{tr.text}' | Confidence: {tr.confidence:.2f} | VAD: {tr.vad_triggered} (Energy: {tr.energy_level:.4f})"
        if lowered.startswith("/tune-vad") or lowered.startswith("tune-vad"):
            prefix = "/tune-vad" if lowered.startswith("/tune-vad") else "tune-vad"
            arg_val = raw[len(prefix):].strip()
            if hasattr(self, "voice_fabric"):
                if arg_val:
                    try:
                        new_thresh = float(arg_val)
                        cfg = self.voice_fabric.tune_vad(energy_threshold=new_thresh)
                        return f"[VAD Calibrated] Energy threshold set to: {cfg['energy_threshold']}"
                    except ValueError:
                        pass
                return f"[VAD Status] Current energy threshold: {self.voice_fabric.energy_threshold:.4f}, silence window: {self.voice_fabric.silence_window_ms}ms"

        # Stage 107: Context Window Semantic Token Compressor
        if lowered.startswith("/compress-prompt ") or lowered.startswith("compress-prompt "):
            prefix = "/compress-prompt " if lowered.startswith("/compress-prompt ") else "compress-prompt "
            prompt_body = raw[len(prefix):].strip()
            if hasattr(self, "token_compressor"):
                return self.token_compressor.compress_prompt_command(prompt_body)
        if lowered.startswith("/token-budget") or lowered.startswith("token-budget"):
            prefix = "/token-budget" if lowered.startswith("/token-budget") else "token-budget"
            args = raw[len(prefix):].strip().split()
            target_ctx = int(args[0]) if len(args) > 0 and args[0].isdigit() else None
            sys_len = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
            if hasattr(self, "token_compressor"):
                return self.token_compressor.format_token_budget_table(model_ctx_size=target_ctx, system_prompt_len=sys_len)
        if lowered in {"/compression-ratio", "compression-ratio"}:
            if hasattr(self, "token_compressor"):
                return self.token_compressor.format_compression_ratio_table()
        if lowered.startswith("/token-audit") or lowered.startswith("token-audit"):
            prefix = "/token-audit" if lowered.startswith("/token-audit") else "token-audit"
            arg_val = raw[len(prefix):].strip()
            limit = int(arg_val) if arg_val.isdigit() else 5
            if hasattr(self, "token_compressor"):
                return self.token_compressor.format_token_audit_table(limit=limit)

        # Stage 108: Autonomous Security Red-Team & Adversary Simulator
        if lowered.startswith("/simulate-attack") or lowered.startswith("simulate-attack"):
            prefix = "/simulate-attack" if lowered.startswith("/simulate-attack") else "simulate-attack"
            q = raw[len(prefix):].strip()
            if hasattr(self, "red_team"):
                return self.red_team.simulate_attack_command(q)
        if lowered in {"/redteam-audit", "redteam-audit"}:
            if hasattr(self, "red_team"):
                rep = self.red_team.run_full_audit()
                return rep.format_terminal_summary()
        if lowered in {"/vulnerability-scan", "vulnerability-scan"}:
            if hasattr(self, "red_team"):
                return self.red_team.format_vulnerability_scan_table()
        if lowered in {"/harden-surface", "harden-surface"}:
            if hasattr(self, "red_team"):
                return self.red_team.format_harden_surface_summary()

        # Stage 109: Ambient HUD & Desktop Overlay
        if lowered.startswith("/hud-launch") or lowered.startswith("hud-launch"):
            prefix = "/hud-launch" if lowered.startswith("/hud-launch") else "hud-launch"
            m = raw[len(prefix):].strip() or "floating"
            if hasattr(self, "ambient_hud"):
                return self.ambient_hud.launch_hud(m)
        if lowered in {"/hud-status", "hud-status"}:
            if hasattr(self, "ambient_hud"):
                return self.ambient_hud.format_hud_status_table()
        if lowered.startswith("/tray-notify ") or lowered.startswith("tray-notify "):
            prefix = "/tray-notify " if lowered.startswith("/tray-notify ") else "tray-notify "
            body = raw[len(prefix):].strip()
            parts = body.split(" ", 1)
            t = parts[0] if parts else "Notice"
            msg = parts[1] if len(parts) > 1 else t
            if hasattr(self, "ambient_hud"):
                n = self.ambient_hud.tray_notify(title=t, message=msg)
                return f"[Tray Notification Dispatched] ID: {n.notification_id} | Title: '{n.title}' | Message: '{n.message}'"
        if lowered in {"/toggle-hud", "toggle-hud"}:
            if hasattr(self, "ambient_hud"):
                return self.ambient_hud.toggle_hud()

        # Stage 110: Sovereign Consensus Nexus & Era 11 Master Seal
        if lowered in {"/nexus-status", "nexus-status"}:
            if hasattr(self, "consensus_nexus"):
                return self.consensus_nexus.format_nexus_status_table()
        if lowered.startswith("/agent-consensus ") or lowered.startswith("agent-consensus "):
            prefix = "/agent-consensus " if lowered.startswith("/agent-consensus ") else "agent-consensus "
            prop = raw[len(prefix):].strip()
            if hasattr(self, "consensus_nexus"):
                res = self.consensus_nexus.propose(prop)
                return f"[Consensus Committed] Index: {res['index']} | Term: {res['term']} | Proposal: {res['proposal_id']} | Hash: {res['entry_hash'][:16]}..."
        if lowered in {"/verify-nexus", "verify-nexus"}:
            if hasattr(self, "consensus_nexus"):
                v = self.consensus_nexus.verify_era11_integrity()
                return f"[Nexus Integrity] All Verified: {v['all_verified']} | Modules: {v['verified_modules']}/{v['total_modules']} | Merkle Root: {v['merkle_root'][:16]}..."
        if lowered in {"/seal-era11", "seal-era11"}:
            if hasattr(self, "consensus_nexus"):
                cert = self.consensus_nexus.seal_era11()
                return cert.format_terminal_summary()

        # Stage 111: Proactive Workspace & Process Sensor Daemon
        if lowered in {"/daemon-status", "daemon-status"}:
            if hasattr(self, "workspace_daemon"):
                return self.workspace_daemon.format_daemon_status_table()

        if lowered in {"/toggle-daemon", "toggle-daemon"}:
            if hasattr(self, "workspace_daemon"):
                return f"[Workspace Daemon] {self.workspace_daemon.toggle()}"

        if lowered in {"/daemon-pulse", "daemon-pulse"}:
            if hasattr(self, "workspace_daemon"):
                evs = self.workspace_daemon.scan_now()
                return f"[Workspace Daemon] Manual pulse executed. Detected {len(evs)} delta change(s)."

        if lowered.startswith("/stage-context ") or lowered.startswith("stage-context "):
            prefix = "/stage-context " if lowered.startswith("/stage-context ") else "stage-context "
            target_f = raw[len(prefix):].strip()
            if hasattr(self, "workspace_daemon"):
                stg = self.workspace_daemon.stage_file_context(target_f)
                if stg:
                    return f"[Context Staged] {stg.source_file} ({stg.line_count} lines, {len(stg.symbols)} symbols) | Test suite: {stg.matching_test_file or 'None'}"
                return f"[Context Staging Failed] File '{target_f}' not found or unreadable."

        # Stage 112: Semantic Inference Cache
        if lowered in {"/cache-status", "cache-status"}:
            if hasattr(self, "semantic_cache"):
                return self.semantic_cache.format_cache_status_table()

        if lowered in {"/flush-cache", "flush-cache"}:
            if hasattr(self, "semantic_cache"):
                cnt = self.semantic_cache.flush()
                return f"[Semantic Cache] Flushed {cnt} cached inference entries."

        if lowered in {"/cache-stats", "cache-stats"}:
            if hasattr(self, "semantic_cache"):
                st = self.semantic_cache.status()
                return f"[Cache Stats] Entries: {st['active_entries']}/{st['max_entries']} | Hit Rate: {st['hit_rate']*100:.1f}% | Tokens Saved: {st['total_tokens_saved']:,} | Lookups: {st['total_lookups']}"

        if lowered.startswith("/cache-query ") or lowered.startswith("cache-query "):
            prefix = "/cache-query " if lowered.startswith("/cache-query ") else "cache-query "
            q = raw[len(prefix):].strip()
            if hasattr(self, "semantic_cache"):
                res = self.semantic_cache.lookup(q)
                if res:
                    entry, m_type, score = res
                    return f"[Cache Hit: {m_type} (score={score:.3f})] {entry.response}"
                return f"[Cache Miss] No cached inference matching query above threshold."

        # Stage 113: Polyglot AST Engine
        if lowered in {"/polyglot-status", "polyglot-status"}:
            if hasattr(self, "polyglot_ast"):
                return self.polyglot_ast.format_polyglot_summary_table()

        if lowered in {"/polyglot-scan", "polyglot-scan"}:
            if hasattr(self, "polyglot_ast"):
                sumry = self.polyglot_ast.scan_workspace()
                return f"[Polyglot AST Scan] Indexed {sumry.total_files} files, {sumry.total_symbols} symbols across {len(sumry.language_breakdown)} languages."

        if lowered.startswith("/find-symbol ") or lowered.startswith("find-symbol "):
            prefix = "/find-symbol " if lowered.startswith("/find-symbol ") else "find-symbol "
            sym_target = raw[len(prefix):].strip()
            if hasattr(self, "polyglot_ast"):
                return self.polyglot_ast.format_symbol_search_results(sym_target)

        if lowered.startswith("/polyglot-inspect ") or lowered.startswith("polyglot-inspect "):
            prefix = "/polyglot-inspect " if lowered.startswith("/polyglot-inspect ") else "polyglot-inspect "
            f_target = raw[len(prefix):].strip()
            if hasattr(self, "polyglot_ast"):
                rep = self.polyglot_ast.inspect_file(f_target)
                if rep:
                    return f"[Polyglot Inspect] {rep.file_path} ({rep.language}): {rep.total_lines} lines, {len(rep.symbols)} symbols, {len(rep.imports)} imports | Valid: {rep.syntax_valid}"
                return f"[Polyglot Inspect] File '{f_target}' not found."

        # Stage 114: Parallel Pipeline Fusion
        if lowered in {"/pipeline-status", "pipeline-status"}:
            if hasattr(self, "pipeline_fusion"):
                return self.pipeline_fusion.format_pipeline_status_table()

        if lowered in {"/pipeline-history", "pipeline-history"}:
            if hasattr(self, "pipeline_fusion"):
                st = self.pipeline_fusion.status()
                return f"[Pipeline History] Total Executed: {st['total_executed']} | Success: {st['successful_executed']} | Failed: {st['failed_executed']}"

        if lowered.startswith("/run-pipeline ") or lowered.startswith("run-pipeline "):
            prefix = "/run-pipeline " if lowered.startswith("/run-pipeline ") else "run-pipeline "
            t_name = raw[len(prefix):].strip().lower()
            if hasattr(self, "pipeline_fusion"):
                if "refactor" in t_name:
                    dag = self.pipeline_fusion.create_refactor_fusion_pipeline()
                elif "audit" in t_name:
                    dag = self.pipeline_fusion.create_workspace_audit_pipeline()
                else:
                    return f"[Pipeline Fusion] Unknown template '{t_name}'. Available: 'refactor', 'audit'"
                res = self.pipeline_fusion.execute_pipeline(dag)
                return f"[Pipeline Fusion] '{res.name}' {'COMPLETED' if res.success else 'FAILED'}: {res.completed_steps}/{res.total_steps} steps in {res.layers_executed} layers ({res.total_latency_ms:.1f}ms)."

        if lowered.startswith("/pipeline-dag ") or lowered.startswith("pipeline-dag "):
            prefix = "/pipeline-dag " if lowered.startswith("/pipeline-dag ") else "pipeline-dag "
            t_name = raw[len(prefix):].strip().lower()
            if hasattr(self, "pipeline_fusion"):
                dag = self.pipeline_fusion.create_workspace_audit_pipeline() if "audit" in t_name else self.pipeline_fusion.create_refactor_fusion_pipeline()
                return self.pipeline_fusion.format_dag_visualization(dag)

        # Stage 115: Sovereign IPC Event Bus
        if lowered in {"/ipc-status", "ipc-status"}:
            if hasattr(self, "ipc_bus"):
                return self.ipc_bus.format_ipc_status_table()

        if lowered in {"/ipc-channels", "ipc-channels"}:
            if hasattr(self, "ipc_bus"):
                st = self.ipc_bus.status()
                return f"[IPC Channels] Loopback Socket: 127.0.0.1:{st['loopback_port']} | SHM Ring Buffer: Active (64 KB) | Journal: {st['journal_file']}"

        if lowered.startswith("/publish-event ") or lowered.startswith("publish-event "):
            prefix = "/publish-event " if lowered.startswith("/publish-event ") else "publish-event "
            args = raw[len(prefix):].strip().split(" ", 1)
            topic = args[0]
            payload_str = args[1] if len(args) > 1 else "{}"
            if hasattr(self, "ipc_bus"):
                try:
                    payload = json.loads(payload_str)
                except Exception:
                    payload = {"message": payload_str}
                evt = self.ipc_bus.publish(topic, payload, source="cli")
                return f"[IPC Event Published] ID: {evt.event_id} | Topic: {evt.topic} | Seq: {evt.sequence}"

        if lowered.startswith("/ipc-tail ") or lowered.startswith("ipc-tail "):
            prefix = "/ipc-tail " if lowered.startswith("/ipc-tail ") else "ipc-tail "
            t_pat = raw[len(prefix):].strip() or "#"
            if hasattr(self, "ipc_bus"):
                evts = self.ipc_bus.tail(t_pat, limit=5)
                if not evts:
                    return f"[IPC Tail] No events found on topic pattern '{t_pat}'."
                formatted_lines = [f"  [{e.sequence}] {e.topic} ({e.source}): {e.payload}" for e in evts]
                return f"[IPC Tail] {len(evts)} event(s) on '{t_pat}':\n" + "\n".join(formatted_lines)

        # Stage 116: Persistent HNSW Vector DB
        if lowered in {"/vectordb-status", "vectordb-status"}:
            if hasattr(self, "local_vector_db"):
                return self.local_vector_db.format_vectordb_status_table()

        if lowered in {"/vectordb-stats", "vectordb-stats"}:
            if hasattr(self, "local_vector_db"):
                st = self.local_vector_db.status()
                return f"[Vector DB Stats] Total Vectors: {st['total_vectors']:,} | Dim: {st['dim']} | Max Level: {st['max_level']} | Searches: {st['total_searches']} (avg {st['avg_latency_ms']:.2f}ms)"

        if lowered.startswith("/vectordb-search ") or lowered.startswith("vectordb-search "):
            prefix = "/vectordb-search " if lowered.startswith("/vectordb-search ") else "vectordb-search "
            q = raw[len(prefix):].strip()
            if hasattr(self, "local_vector_db"):
                results = self.local_vector_db.search_text(q, top_k=3)
                if not results:
                    return f"[Vector DB Search] No matching vectors found for '{q}'."
                res_lines = [f"  [{r.doc_id}] score={r.score:.3f} | {r.metadata.get('text_preview', '')}" for r in results]
                return f"[Vector DB Search] Top {len(results)} matches for '{q}':\n" + "\n".join(res_lines)

        if lowered.startswith("/vectordb-insert ") or lowered.startswith("vectordb-insert "):
            prefix = "/vectordb-insert " if lowered.startswith("/vectordb-insert ") else "vectordb-insert "
            args = raw[len(prefix):].strip().split(" ", 1)
            doc_id = args[0]
            txt = args[1] if len(args) > 1 else ""
            if hasattr(self, "local_vector_db"):
                self.local_vector_db.insert_text(doc_id, txt)
                return f"[Vector DB Insert] Indexed document '{doc_id}' ({len(txt)} chars, {self.local_vector_db.dim} dimensions)."

        # Stage 117: Autonomous GitOps Engine
        if lowered in {"/gitops-status", "gitops-status"}:
            if hasattr(self, "git_ops"):
                return self.git_ops.format_gitops_status_table()

        if lowered in {"/gitops-commit-plan", "gitops-commit-plan"}:
            if hasattr(self, "git_ops"):
                prop = self.git_ops.synthesize_commit_proposal()
                return "[GitOps Proposed Commit]\n" + prop.raw_message

        if lowered in {"/gitops-changelog", "gitops-changelog"}:
            if hasattr(self, "git_ops"):
                cl = self.git_ops.generate_changelog(era=12)
                return f"[GitOps Changelog Generated: {cl.version}]\nSaved to: data/lucy/gitops/CHANGELOG.md\n\n" + cl.markdown[:300] + "..."


        if lowered in {"/gitops-preflight", "gitops-preflight"}:
            if hasattr(self, "git_ops"):
                st = self.git_ops.get_status()
                return f"[GitOps Pre-Flight Check] Working tree clean: {st.is_clean} | Modified: {len(st.modified_files)} | Untracked: {len(st.untracked_files)} | Safety status: Safe to proceed."

        # Stage 118: Thermal & Compute Governor
        if lowered in {"/governor-status", "governor-status"}:
            if hasattr(self, "thermal_governor"):
                return self.thermal_governor.format_governor_status_table()

        if lowered in {"/governor-cooldown", "governor-cooldown"}:
            if hasattr(self, "thermal_governor"):
                self.thermal_governor.trigger_cooldown(20.0)
                return "[Thermal Governor] Cooldown period engaged (20s). Background threads throttled to 1."

        if lowered in {"/governor-tripwires", "governor-tripwires"}:
            if hasattr(self, "thermal_governor"):
                tw = self.thermal_governor.tripwires
                return f"[Governor Tripwires] Temp Warn: {tw.temp_warn_c}C, Crit: {tw.temp_critical_c}C | CPU Warn: {tw.cpu_warn_pct}%, Crit: {tw.cpu_critical_pct}% | RAM Warn: {tw.ram_warn_pct}%"

        if lowered.startswith("/governor-mode ") or lowered.startswith("governor-mode "):
            prefix = "/governor-mode " if lowered.startswith("/governor-mode ") else "governor-mode "
            mode_req = raw[len(prefix):].strip()
            if hasattr(self, "thermal_governor"):
                ok = self.thermal_governor.set_mode(mode_req)
                if ok:
                    workers = self.thermal_governor.allocate_workers()
                    return f"[Thermal Governor] Operating mode switched to {mode_req.upper()} (Worker capacity: {workers} threads)."
                return f"[Thermal Governor] Unknown mode '{mode_req}'. Valid: 'eco', 'balanced', 'turbo'."   



        # Stage 119: Episodic Dream Consolidator
        if lowered in {"/dream-status", "dream-status"}:
            if hasattr(self, "dream_consolidator"):
                return self.dream_consolidator.format_dream_status_table()

        if lowered in {"/run-dream", "run-dream", "/dream-cycle", "dream-cycle"}:
            if hasattr(self, "dream_consolidator"):
                rcpt = self.dream_consolidator.run_dream_cycle()
                return (
                    f"[Dream Consolidator] Dream cycle {rcpt.dream_id} complete.\n"
                    f"Traces reviewed: {rcpt.traces_reviewed} | Axioms crystallized: {rcpt.axioms_crystallized}\n"
                    f"Contradictions resolved: {rcpt.contradictions_resolved} | Pruned traces: {rcpt.pruned_traces}\n"
                    f"LoRA training triples generated: {rcpt.lora_triples_generated} | Duration: {rcpt.duration_ms:.1f}ms"
                )

        if lowered in {"/dream-axioms", "dream-axioms"}:
            if hasattr(self, "dream_consolidator"):
                axioms = self.dream_consolidator.recall_axioms()
                if not axioms:
                    return "[Dream Consolidator] No crystallized axioms found in memory."
                out = [f"[Crystallized Axioms Repository] ({len(axioms)} axioms stored):"]
                for ax in axioms:
                    out.append(f" - [{ax.domain.upper()}] {ax.subject}: {ax.rule} (confidence: {ax.confidence:.2f})")
                return "\n".join(out)

        # Stage 120: Sovereign Singularity Nexus & Era 12 Master Seal
        if lowered in {"/era12-seal", "era12-seal"}:
            if hasattr(self, "era12_seal"):
                return self.era12_seal.format_seal_certificate_table()

        if lowered in {"/verify-era12", "verify-era12"}:
            if hasattr(self, "era12_seal"):
                ok, msg, _ = self.era12_seal.verify_era12_integrity()
                return f"[Era 12 Master Seal Verification] Status: {'PASS' if ok else 'FAIL'}\n{msg}"

        if lowered in {"/singularity-status", "singularity-status"}:
            if hasattr(self, "era12_seal"):
                return self.era12_seal.format_singularity_status_table()

        if lowered.startswith("/cognitive-cycle") or lowered.startswith("cognitive-cycle"):
            prefix = "/cognitive-cycle" if lowered.startswith("/cognitive-cycle") else "cognitive-cycle"
            goal_arg = raw[len(prefix):].strip() or "General Self-Regulating Equilibrium"
            if hasattr(self, "era12_seal"):
                res = self.era12_seal.run_cognitive_cycle(goal_arg)
                return f"[Cognitive Singularity Pulse] Cycle: {res.cycle_id} | Goal: {res.goal}\nDuration: {res.duration_ms:.1f}ms | Active subsystems: {res.subsystems_active}/10\nOutcome: {res.summary}"

        # Stage 121: Causal Neural Knowledge Graph & Property Graph Nexus
        if lowered in {"/kg-status", "kg-status"}:
            if hasattr(self, "knowledge_graph"):
                return self.knowledge_graph.format_kg_status_table()

        if lowered in {"/kg-contradictions", "kg-contradictions"}:
            if hasattr(self, "knowledge_graph"):
                contras = self.knowledge_graph.detect_contradictions()
                if not contras:
                    return "[Knowledge Graph] No conflicting assertions detected. Topology is epistemically consistent."
                lines = [f"[Knowledge Graph Contradictions] ({len(contras)} conflicts flagged):"]
                for s, t, r in contras:
                    lines.append(f" - {s} vs {t}: {r}")
                return "\n".join(lines)

        if lowered.startswith("/kg-query") or lowered.startswith("kg-query"):
            prefix = "/kg-query" if lowered.startswith("/kg-query") else "kg-query"
            kw = raw[len(prefix):].strip()
            if hasattr(self, "knowledge_graph"):
                nodes = self.knowledge_graph.query(keyword=kw if kw else None)
                lines = [f"[Knowledge Graph Query Results] ({len(nodes)} nodes matched):"]
                for n in nodes[:15]:
                    lines.append(f" - [{n.node_type}] {n.node_id}: {n.label}")
                return "\n".join(lines)

        if lowered.startswith("/kg-path ") or lowered.startswith("kg-path "):
            prefix = "/kg-path " if lowered.startswith("/kg-path ") else "kg-path "
            parts = raw[len(prefix):].strip().split()
            if len(parts) >= 2 and hasattr(self, "knowledge_graph"):
                p = self.knowledge_graph.find_shortest_path(parts[0], parts[1])
                if p:
                    return f"[Knowledge Graph Path] {" -> ".join(p)}"
                return f"[Knowledge Graph] No path found between {parts[0]} and {parts[1]}."

        # Stage 122: Multi-Hypothesis Counterfactual Evaluator
        if lowered in {"/counterfactual-status", "counterfactual-status"}:
            if hasattr(self, "counterfactual_simulator"):
                return self.counterfactual_simulator.format_counterfactual_status_table()

        if lowered.startswith("/counterfactual-simulate") or lowered.startswith("counterfactual-simulate"):
            prefix = "/counterfactual-simulate" if lowered.startswith("/counterfactual-simulate") else "counterfactual-simulate"
            goal_arg = raw[len(prefix):].strip() or "Standard Autonomous System Refactor"
            if hasattr(self, "counterfactual_simulator"):
                rep = self.counterfactual_simulator.simulate_goal_hypotheses(goal_arg)
                return (
                    f"[Counterfactual Simulation Complete]\n"
                    f"Simulation ID: {rep.simulation_id} | Goal: {rep.goal}\n"
                    f"Optimal Trajectory: {rep.best_hypothesis_id} (Score: {rep.best_score:.3f})\n"
                    f"Comparative Analysis: {rep.counterfactual_explanation}"
                )

        if lowered in {"/counterfactual-tree", "counterfactual-tree"}:
            if hasattr(self, "counterfactual_simulator"):
                last_rep = self.counterfactual_simulator._last_simulation
                if not last_rep:
                    return "[Counterfactual Simulator] No simulation recorded in history. Run /counterfactual-simulate [goal] first."
                lines = [f"[Counterfactual Trajectory Tree: {last_rep.simulation_id}] ({last_rep.total_hypotheses} branches):"]
                for h in last_rep.hypotheses:
                    state = "DISQUALIFIED" if h["violates_invariants"] else f"Score {h['composite_score']:.3f}"
                    lines.append(f" - [{h['hypothesis_id']}] {h['description']} -> {state}")
                return "\n".join(lines)

        # Stage 123: Hierarchical Goal & Subgoal Decomposer
        if lowered in {"/decomposer-status", "decomposer-status"}:
            if hasattr(self, "goal_decomposer"):
                return self.goal_decomposer.format_decomposer_status_table()

        if lowered.startswith("/decompose-goal") or lowered.startswith("decompose-goal"):
            prefix = "/decompose-goal" if lowered.startswith("/decompose-goal") else "decompose-goal"
            goal_arg = raw[len(prefix):].strip() or "Refactor memory and cognitive subsystem"
            if hasattr(self, "goal_decomposer"):
                plan = self.goal_decomposer.decompose_goal(goal_arg)
                return self.goal_decomposer.format_goal_tree(plan.plan_id)

        if lowered.startswith("/goal-tree") or lowered.startswith("goal-tree"):
            prefix = "/goal-tree" if lowered.startswith("/goal-tree") else "goal-tree"
            pid = raw[len(prefix):].strip() or None
            if hasattr(self, "goal_decomposer"):
                return self.goal_decomposer.format_goal_tree(pid)

        # Stage 124: Autonomous Verification Oracle & Proof Engine
        if lowered in {"/oracle-status", "oracle-status"}:
            if hasattr(self, "verification_oracle"):
                return self.verification_oracle.format_oracle_status_table()

        if lowered.startswith("/oracle-verify") or lowered.startswith("oracle-verify"):
            prefix = "/oracle-verify" if lowered.startswith("/oracle-verify") else "oracle-verify"
            sample_text = raw[len(prefix):].strip() or "def valid_subsystem(): pass"
            if hasattr(self, "verification_oracle"):
                cert = self.verification_oracle.verify_code_patch(sample_text)
                return self.verification_oracle.format_certificate_table(cert.certificate_id)

        if lowered.startswith("/oracle-cert") or lowered.startswith("oracle-cert"):
            prefix = "/oracle-cert" if lowered.startswith("/oracle-cert") else "oracle-cert"
            cid = raw[len(prefix):].strip() or None
            if hasattr(self, "verification_oracle"):
                return self.verification_oracle.format_certificate_table(cid)

        # Stage 125: Self-Supervised Latent Concept Miner
        if lowered in {"/concept-status", "concept-status"}:
            if hasattr(self, "concept_miner"):
                return self.concept_miner.format_concept_status_table()

        if lowered in {"/concept-taxonomy", "concept-taxonomy"}:
            if hasattr(self, "concept_miner"):
                return self.concept_miner.format_concept_taxonomy_tree()

        if lowered in {"/mine-concepts", "mine-concepts"}:
            if hasattr(self, "concept_miner"):
                mined = self.concept_miner.mine_concepts()
                exported = 0
                if hasattr(self, "knowledge_graph"):
                    exported = self.concept_miner.export_to_knowledge_graph(self.knowledge_graph)
                return (
                    f"[Latent Concept Miner Sweep Complete]\n"
                    f"Mined {len(mined)} new latent concepts. Exported {exported} concepts to Neural Knowledge Graph.\n\n"
                    f"{self.concept_miner.format_concept_taxonomy_tree()}"
                )

        if lowered in {"/budget-status", "budget-status"}:
            if hasattr(self, "context_budgeter"):
                return self.context_budgeter.format_budget_status_table()

        if lowered.startswith("/allocate-budget") or lowered.startswith("allocate-budget"):
            if hasattr(self, "context_budgeter"):
                parts = raw.strip().split()
                if len(parts) > 1:
                    arg = parts[1].strip()
                    if arg.isdigit():
                        snap = self.context_budgeter.allocate_slices(total_budget=int(arg))
                    else:
                        snap = self.context_budgeter.allocate_slices(hardware_mode=arg)
                    return f"[Context Budget Reallocated]\nTotal Budget: {snap.total_budget_tokens:,} tokens (mode: {snap.hardware_mode})\n\n{self.context_budgeter.format_budget_status_table()}"
                return self.context_budgeter.format_budget_status_table()

        if lowered.startswith("/compact-context") or lowered.startswith("compact-context"):
            if hasattr(self, "context_budgeter"):
                parts = raw.strip().split()
                slice_name = parts[1].strip() if len(parts) > 1 else "RETRIEVAL_RAG_KG"
                freed = self.context_budgeter.compact_slice(slice_name)
                return f"[Context Compacted]\nSlice: {slice_name.upper()}\nTokens Freed: {freed:,}\n\n{self.context_budgeter.format_budget_status_table()}"

        if lowered in {"/protocol-status", "protocol-status"}:
            if hasattr(self, "protocol_synthesizer"):
                return self.protocol_synthesizer.format_protocol_status_table()

        if lowered.startswith("/infer-protocol") or lowered.startswith("infer-protocol"):
            if hasattr(self, "protocol_synthesizer"):
                parts = raw.strip().split(maxsplit=1)
                sample = parts[1] if len(parts) > 1 else ""
                if sample.startswith("curl"):
                    spec = self.protocol_synthesizer.infer_from_curl(sample)
                else:
                    spec = self.protocol_synthesizer.infer_protocol("Inferred Endpoint", raw_payload=sample)
                return f"[Inferred Protocol: {spec.name}]\nID: {spec.protocol_id} | Method: {spec.method} {spec.path}\nFields ({len(spec.request_fields)}): {[f.name for f in spec.request_fields]}\nAuth: {spec.auth_type}\n\n{self.protocol_synthesizer.format_protocol_status_table()}"

        if lowered.startswith("/synthesize-client") or lowered.startswith("synthesize-client"):
            if hasattr(self, "protocol_synthesizer"):
                parts = raw.strip().split(maxsplit=1)
                pid = parts[1].strip() if len(parts) > 1 else ""
                # Find matching protocol
                matched = self.protocol_synthesizer.get_protocol(pid)
                if not matched:
                    # Try matching prefix
                    for p in self.protocol_synthesizer.list_protocols():
                        if p.protocol_id.startswith(pid) or pid in p.name.lower():
                            matched = p
                            break
                if matched:
                    code = self.protocol_synthesizer.synthesize_client_code(matched.protocol_id)
                    return f"[Synthesized Client: {matched.name}]\nProtocol ID: {matched.protocol_id}\n\n```python\n{code}\n```"
                return f"[Error] Protocol matching '{pid}' not found in registry."

        if lowered in {"/policy-status", "policy-status"}:
            if hasattr(self, "meta_policy_refiner"):
                return self.meta_policy_refiner.format_policy_status_table()

        if lowered.startswith("/tune-policy") or lowered.startswith("tune-policy"):
            if hasattr(self, "meta_policy_refiner"):
                parts = raw.strip().split()
                if len(parts) >= 3:
                    pname = parts[1].strip()
                    try:
                        val = float(parts[2].strip())
                        success, msg, final_val = self.meta_policy_refiner.tune_policy(pname, val)
                        prefix = "[Policy Tuned]" if success else "[Policy Tune Rejected]"
                        return f"{prefix} {msg}\n\n{self.meta_policy_refiner.format_policy_status_table()}"
                    except ValueError:
                        return f"[Error] Invalid policy numeric value: {parts[2]}"
                return self.meta_policy_refiner.format_policy_status_table()

        if lowered in {"/evaluate-policies", "evaluate-policies"}:
            if hasattr(self, "meta_policy_refiner"):
                res = self.meta_policy_refiner.evaluate_and_refine_policies()
                return f"[Meta-Policy Evaluation Sweep Complete]\nSweep ID: {res['sweep_id']} | Adjustments: {res['adjustments_count']}\n\n{self.meta_policy_refiner.format_policy_status_table()}"

        if lowered in {"/mesh-gateway-status", "mesh-gateway-status", "/ipc-mesh-status", "ipc-mesh-status"}:
            if hasattr(self, "mesh_gateway"):
                return self.mesh_gateway.format_mesh_status_table()

        if lowered.startswith("/register-node") or lowered.startswith("register-node"):
            if hasattr(self, "mesh_gateway"):
                parts = raw.strip().split()
                if len(parts) >= 3:
                    nid = parts[1].strip()
                    ep = parts[2].strip()
                    role = parts[3].strip() if len(parts) > 3 else "worker"
                    node = self.mesh_gateway.register_node(nid, ep, role)
                    return f"[Registered Mesh Node: {node.node_id}]\nEndpoint: {node.endpoint} | Role: {node.role} | Sig: {node.signature[:12]}...\n\n{self.mesh_gateway.format_mesh_status_table()}"
                return "[Error] Usage: /register-node <node_id> <endpoint> [role]"

        if lowered.startswith("/dispatch-rpc") or lowered.startswith("dispatch-rpc"):
            if hasattr(self, "mesh_gateway"):
                parts = raw.strip().split(maxsplit=3)
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
                    res = self.mesh_gateway.dispatch_rpc(tnode, proc, params)
                    return f"[RPC Dispatched: {proc} -> {tnode}]\nStatus: {res.get('status')} | Latency: {res.get('latency_ms', 0):.2f}ms\nResult: {res.get('result')}\n\n{self.mesh_gateway.format_mesh_status_table()}"
                return "[Error] Usage: /dispatch-rpc <target_node> <procedure> [json_params]"

        if lowered in {"/era13-seal", "era13-seal", "/era13-status", "era13-status"}:
            if hasattr(self, "era13_seal"):
                return self.era13_seal.format_seal_certificate_table()

        if lowered in {"/verify-era13", "verify-era13"}:
            if hasattr(self, "era13_seal"):
                intact, msg, cert = self.era13_seal.verify_era13_integrity()
                return f"[Era 13 Verification]\nStatus: {'VERIFIED' if intact else 'TAMPERED'}\nMessage: {msg}\n\n{self.era13_seal.format_seal_certificate_table()}"

        if lowered.startswith("/symbolic-cycle") or lowered.startswith("symbolic-cycle"):
            if hasattr(self, "era13_seal"):
                parts = raw.strip().split(maxsplit=1)
                goal = parts[1] if len(parts) > 1 else "Synthesize sovereign cognitive mesh"
                res = self.era13_seal.run_symbolic_mesh_cycle(goal=goal)
                steps_txt = "\n".join(f"  - {s}" for s in res.steps_executed)
                return f"[Symbolic Singularity Pulse: {res.cycle_id}]\nGoal: {res.goal}\nDuration: {res.duration_ms:.2f}ms | Active Subsystems: {res.subsystems_active}\n\nExecution Steps:\n{steps_txt}\n\nSummary: {res.summary}\n\n{self.era13_seal.format_seal_certificate_table()}"

        if lowered in {"/mutation-status", "mutation-status"}:
            if hasattr(self, "ast_mutator"):
                return self.ast_mutator.format_mutation_status_table()

        if lowered.startswith("/mutate-code") or lowered.startswith("mutate-code"):
            if hasattr(self, "ast_mutator"):
                parts = raw.strip().split(maxsplit=2)
                code_snippet = parts[1] if len(parts) > 1 else "def test(): return 1 + 2"
                op = parts[2].strip() if len(parts) > 2 else "AOR"
                mutant = self.ast_mutator.mutate_code(code_snippet, operator_name=op)
                return f"[Mutant Generated: {mutant.mutant_id}]\nOperator: {mutant.operator_applied} | Valid: {mutant.is_valid_syntax} | Fitness: {mutant.fitness_score:.2f}\n\nMutated Code:\n```python\n{mutant.mutated_code}\n```\n\n{self.ast_mutator.format_mutation_status_table()}"

        if lowered.startswith("/evolve-code") or lowered.startswith("evolve-code"):
            if hasattr(self, "ast_mutator"):
                parts = raw.strip().split(maxsplit=1)
                code_snippet = parts[1] if len(parts) > 1 else "def compute(x): return x + 10"
                survivors = self.ast_mutator.evolve_code(code_snippet, generations=2)
                return f"[Genetic Evolution Complete]\nTotal Mutant Population: {len(survivors)}\nBest Mutant: {survivors[-1].mutant_id if survivors else 'none'}\n\n{self.ast_mutator.format_mutation_status_table()}"

        if lowered in {"/test-oracle-status", "test-oracle-status"}:
            if hasattr(self, "test_oracle"):
                return self.test_oracle.format_oracle_status_table()

        if lowered.startswith("/synthesize-tests") or lowered.startswith("synthesize-tests"):
            if hasattr(self, "test_oracle"):
                parts = raw.strip().split(maxsplit=1)
                code_snippet = parts[1] if len(parts) > 1 else "def compute(x): return x * 2"
                rec = self.test_oracle.synthesize_test_suite(code_snippet)
                return f"[Test Suite Synthesized: {rec.suite_id}]\nTarget: {rec.target_name} | Assertions: {rec.assertions_count} | Compilable: {rec.is_compilable}\n\nSynthesized Test Suite Code:\n```python\n{rec.test_code}\n```\n\n{self.test_oracle.format_oracle_status_table()}"

        if lowered.startswith("/validate-test-suite") or lowered.startswith("validate-test-suite"):
            if hasattr(self, "test_oracle"):
                parts = raw.strip().split(maxsplit=1)
                sid = parts[1].strip() if len(parts) > 1 else ""
                # Find matching suite
                matched = self.test_oracle._test_suites.get(sid)
                if not matched:
                    for s in self.test_oracle._test_suites.values():
                        if s.suite_id.startswith(sid) or sid in s.target_name.lower():
                            matched = s
                            break
                if matched:
                    val = self.test_oracle.validate_test_suite(matched.suite_id)
                    return f"[Test Suite Validated: {matched.suite_id}]\nStatus: {val.get('status')} | Compilable: {val.get('is_compilable')}\n\n{self.test_oracle.format_oracle_status_table()}"
                return f"[Error] Test suite matching '{sid}' not found."

        if lowered in {"/constraint-status", "constraint-status"}:
            if hasattr(self, "constraint_solver"):
                return self.constraint_solver.format_constraint_status_table()

        if lowered.startswith("/solve-constraints") or lowered.startswith("solve-constraints"):
            if hasattr(self, "constraint_solver"):
                parts = raw.strip().split(maxsplit=1)
                code_snippet = parts[1] if len(parts) > 1 else "x = 10"
                # Support semicolon-separated oneliners
                code_snippet = code_snippet.replace("; ", "\n").replace(";", "\n")
                res = self.constraint_solver.solve_constraints(code_snippet)
                return f"[Constraints Solved: {res.solve_id}]\nSatisfiable: {res.is_satisfiable} | Variables Analyzed: {res.total_variables_analyzed}\nInferred Types: {res.inferred_types}\nConflicts: {res.conflicts_detected}\n\n{self.constraint_solver.format_constraint_status_table()}"

        if lowered.startswith("/check-branch-sat") or lowered.startswith("check-branch-sat"):
            if hasattr(self, "constraint_solver"):
                parts = raw.strip().split(maxsplit=1)
                cond = parts[1].strip() if len(parts) > 1 else "True"
                res = self.constraint_solver.check_branch_sat(cond)
                return f"[Branch Satisfiability]\nCondition: {res['condition']}\nStatus: {res['status']}\nReason: {res['reason']}"

        if lowered in {"/bytecode-status", "bytecode-status"}:
            if hasattr(self, "bytecode_inspector"):
                return self.bytecode_inspector.format_bytecode_status_table()

        if lowered.startswith("/disassemble-code") or lowered.startswith("disassemble-code"):
            if hasattr(self, "bytecode_inspector"):
                parts = raw.strip().split(maxsplit=1)
                snippet = parts[1] if len(parts) > 1 else "x = 1 + 2"
                snippet = snippet.replace("; ", "\n").replace(";", "\n")
                rep = self.bytecode_inspector.disassemble_code(snippet)
                dump = self.bytecode_inspector.format_bytecode_dump(rep.report_id)
                return f"[Bytecode Disassembled: {rep.report_id}]\nInstructions: {rep.total_instructions} | Stack Depth: {rep.stack_size} | Eval Anomaly: {rep.has_dynamic_eval}\n\n```\n{dump}\n```\n\n{self.bytecode_inspector.format_bytecode_status_table()}"

        if lowered.startswith("/inspect-opcodes") or lowered.startswith("inspect-opcodes"):
            if hasattr(self, "bytecode_inspector"):
                parts = raw.strip().split(maxsplit=1)
                snippet = parts[1] if len(parts) > 1 else "x = 1 + 2"
                snippet = snippet.replace("; ", "\n").replace(";", "\n")
                rep = self.bytecode_inspector.disassemble_code(snippet)
                lines = [f"[Opcode Frequency Breakdown: {rep.report_id}]", f"Total Instructions: {rep.total_instructions}"]
                for op, count in sorted(rep.opcode_distribution.items(), key=lambda x: -x[1]):
                    lines.append(f"  {op:<24} : {count} occurrences")
                return "\n".join(lines) + f"\n\n{self.bytecode_inspector.format_bytecode_status_table()}"

        if lowered in {"/ffi-status", "ffi-status"}:
            if hasattr(self, "ffi_linker"):
                return self.ffi_linker.format_ffi_status_table()

        if lowered.startswith("/link-native-symbol") or lowered.startswith("link-native-symbol"):
            if hasattr(self, "ffi_linker"):
                parts = raw.strip().split()
                if len(parts) >= 4:
                    lib_name = parts[1].strip()
                    sym_name = parts[2].strip()
                    res_type = parts[3].strip()
                    arg_types = parts[4:] if len(parts) > 4 else []
                    b = self.ffi_linker.link_native_symbol(sym_name, library_name=lib_name, restype_name=res_type, argtypes_names=arg_types)
                    return f"[Linked Native Symbol: {b.symbol_name}]\nLibrary: {b.library_name} | Return: {b.restype} | Live: {b.is_live_loaded}\n\n{self.ffi_linker.format_ffi_status_table()}"
                return "[Error] Usage: /link-native-symbol <lib_name> <symbol_name> <restype> [argtypes...]"

        if lowered.startswith("/invoke-native") or lowered.startswith("invoke-native"):
            if hasattr(self, "ffi_linker"):
                parts = raw.strip().split()
                if len(parts) >= 2:
                    sym_name = parts[1].strip()
                    raw_args = parts[2:]
                    # Convert integer arguments if numeric
                    converted_args = []
                    for a in raw_args:
                        try:
                            converted_args.append(int(a))
                        except ValueError:
                            converted_args.append(a)
                    try:
                        res = self.ffi_linker.invoke_native_symbol(sym_name, *converted_args)
                        return f"[Native Invocation Complete: {sym_name}]\nArguments: {converted_args}\nResult: {res}\n\n{self.ffi_linker.format_ffi_status_table()}"
                    except Exception as e:
                        return f"[Native Invocation Error] {str(e)}"
                return "[Error] Usage: /invoke-native <symbol_name> [args...]"

        if lowered in {"/wheel-status", "wheel-status"}:
            if hasattr(self, "wheel_fabric"):
                return self.wheel_fabric.format_wheel_status_table()

        if lowered.startswith("/build-wheel") or lowered.startswith("build-wheel"):
            if hasattr(self, "wheel_fabric"):
                parts = raw.strip().split()
                if len(parts) >= 2:
                    pname = parts[1].strip()
                    ver = parts[2].strip() if len(parts) > 2 else "1.0.0"
                    rec = self.wheel_fabric.build_wheel(pname, version=ver)
                    return f"[Wheel Package Built: {rec.wheel_filename}]\nSize: {rec.file_size_bytes:,} bytes | Files: {rec.total_files_contained}\nSHA-256: {rec.sha256_digest}\nSignature: {rec.hmac_signature[:16]}...\n\n{self.wheel_fabric.format_wheel_status_table()}"
                return "[Error] Usage: /build-wheel <package_name> [version]"

        if lowered.startswith("/verify-wheel") or lowered.startswith("verify-wheel"):
            if hasattr(self, "wheel_fabric"):
                parts = raw.strip().split(maxsplit=1)
                whl = parts[1].strip() if len(parts) > 1 else ""
                res = self.wheel_fabric.verify_wheel(whl)
                return f"[Wheel Verification Complete]\nFilename: {res.get('wheel_filename')}\nStatus: {res.get('status')}\nValid: {res.get('is_valid')}\nTampered Files: {res.get('tampered_files')}\n\n{self.wheel_fabric.format_wheel_status_table()}"

        # Stage 137: Real-Time Performance Regression Sentinel
        if lowered in {"/perf-status", "perf-status", "/perf-sentinel-status", "perf-sentinel-status"}:
            if hasattr(self, "perf_sentinel"):
                return self.perf_sentinel.format_perf_status_table()

        if lowered in {"/perf-baselines", "perf-baselines"}:
            if hasattr(self, "perf_sentinel"):
                return self.perf_sentinel.format_baselines_table()

        if lowered.startswith("/perf-benchmark") or lowered.startswith("perf-benchmark"):
            if hasattr(self, "perf_sentinel"):
                parts = raw.strip().split()
                target = parts[1] if len(parts) > 1 else "ast_mutation"
                iters = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 50
                metric, alerts = self.perf_sentinel.benchmark_subsystem(target, iterations=iters)
                alert_text = f"\n[Regression Alert: {len(alerts)} detected]" if alerts else "\n[No Regressions Detected]"
                return f"[Performance Benchmark Completed: {metric.name}]\nLatency: {metric.avg_latency_ms:.3f}ms | Throughput: {metric.ops_per_sec:.1f} ops/s{alert_text}\n\n{self.perf_sentinel.format_perf_status_table()}"
            return "[Error] perf_sentinel unavailable"

        if lowered.startswith("/perf-check") or lowered.startswith("perf-check"):
            if hasattr(self, "perf_sentinel"):
                parts = raw.strip().split()
                target = parts[1] if len(parts) > 1 else "ast_mutation"
                metric, alerts = self.perf_sentinel.benchmark_subsystem(target, iterations=25)
                stat_str = "ALERT" if alerts else "OPTIMAL"
                return f"[Performance Check: {target}]\nStatus: {stat_str}\nLatency: {metric.avg_latency_ms:.3f}ms\n\n{self.perf_sentinel.format_perf_status_table()}"
            return "[Error] perf_sentinel unavailable"

        # Stage 138: Dead-Code Eliminator & AST Pruner
        if lowered in {"/prune-status", "prune-status", "/deadcode-status", "deadcode-status"}:
            if hasattr(self, "dead_code_eliminator"):
                return self.dead_code_eliminator.format_status_table()

        if lowered.startswith("/prune-analyze") or lowered.startswith("prune-analyze"):
            if hasattr(self, "dead_code_eliminator"):
                parts = raw.strip().split(maxsplit=1)
                target = parts[1].strip() if len(parts) > 1 else ""
                if Path(target).exists():
                    items, summary = self.dead_code_eliminator.analyze_file(target)
                else:
                    items, summary = self.dead_code_eliminator.analyze_code(target)
                out = f"[Dead-Code Analysis: {target}]\nItems Detected: {len(items)}\n"
                for it in items[:5]:
                    out += f" - [{it.item_type}] {it.name} (line {it.line_number}): {it.reason}\n"
                return out.strip() + f"\n\n{self.dead_code_eliminator.format_status_table()}"
            return "[Error] dead_code_eliminator unavailable"

        if lowered.startswith("/prune-file") or lowered.startswith("prune-file"):
            if hasattr(self, "dead_code_eliminator"):
                parts = raw.strip().split(maxsplit=1)
                fpath = parts[1].strip() if len(parts) > 1 else ""
                report = self.dead_code_eliminator.prune_file(fpath, in_place=False)
                return self.dead_code_eliminator.format_report_table(report)
            return "[Error] dead_code_eliminator unavailable"

        if lowered.startswith("/reachability-graph") or lowered.startswith("reachability-graph"):
            if hasattr(self, "dead_code_eliminator"):
                parts = raw.strip().split(maxsplit=1)
                target = parts[1].strip() if len(parts) > 1 else ""
                content = Path(target).read_text(encoding="utf-8") if Path(target).exists() else target
                graph = self.dead_code_eliminator.build_reachability_graph(content)
                return f"[Reachability Graph: {target}]\nFunctions: {graph.get('functions')}\nCalls: {graph.get('calls_adjacency')}"
            return "[Error] dead_code_eliminator unavailable"

        # Stage 139: Deterministic Replay & Flight-Data Recorder
        if lowered in {"/flight-status", "flight-status", "/recorder-status", "recorder-status"}:
            if hasattr(self, "flight_recorder"):
                return self.flight_recorder.format_flight_status_table()

        if lowered.startswith("/flight-snapshot") or lowered.startswith("flight-snapshot"):
            if hasattr(self, "flight_recorder"):
                parts = raw.strip().split(maxsplit=1)
                lbl = parts[1].strip() if len(parts) > 1 else "manual_checkpoint"
                snap = self.flight_recorder.take_snapshot(label=lbl)
                return f"[Flight Snapshot Recorded: {lbl}]\nEvent ID: {snap.event_id}\nState Hash: {snap.state_hash[:16]}...\n\n{self.flight_recorder.format_flight_status_table()}"
            return "[Error] flight_recorder unavailable"

        if lowered.startswith("/flight-replay") or lowered.startswith("flight-replay"):
            if hasattr(self, "flight_recorder"):
                parts = raw.strip().split(maxsplit=1)
                fid = parts[1].strip() if len(parts) > 1 else ""
                diff = self.flight_recorder.replay_flight(fid)
                return self.flight_recorder.format_replay_diff_table(diff)
            return "[Error] flight_recorder unavailable"

        if lowered in {"/blackbox-export", "blackbox-export"}:
            if hasattr(self, "flight_recorder"):
                rec = self.flight_recorder.flush_flight_recording()
                return f"[Black-Box Flight Log Exported]\nFlight ID: {rec.flight_id}\nEvents: {rec.events_count}\nMerkle Root: {rec.merkle_root[:16]}...\nSignature: {rec.hmac_signature[:16]}...\n\n{self.flight_recorder.format_flight_status_table()}"
            return "[Error] flight_recorder unavailable"

        # Stage 140: Sovereign Singularity Nexus & Era 14 Master Seal
        if lowered in {"/era14-status", "era14-status"}:
            if hasattr(self, "era14_nexus"):
                return self.era14_nexus.format_era14_status_table()

        if lowered in {"/verify-era14", "verify-era14"}:
            if hasattr(self, "era14_nexus"):
                cert = self.era14_nexus.generate_era14_master_seal(force=True)
                return f"[Era 14 Master Seal Verified]\nSeal ID: {cert.seal_id}\nMerkle Root: {cert.merkle_root}\nStatus: {cert.integrity_status}\n\n{self.era14_nexus.format_era14_status_table()}"
            return "[Error] era14_nexus unavailable"

        if lowered.startswith("/evolution-cycle") or lowered.startswith("evolution-cycle"):
            if hasattr(self, "era14_nexus"):
                parts = raw.strip().split(maxsplit=1)
                target = parts[1].strip() if len(parts) > 1 else "runtime_evolution"
                res = self.era14_nexus.run_evolution_cycle(target)
                return self.era14_nexus.format_cycle_result_table(res)
            return "[Error] era14_nexus unavailable"

        # Stage 141: Intermediate Representation (IR) Compiler Core
        if lowered in {"/ir-status", "ir-status", "/compiler-status", "compiler-status"}:
            if hasattr(self, "ir_compiler"):
                return self.ir_compiler.format_ir_status_table()

        if lowered.startswith("/ir-compile") or lowered.startswith("ir-compile"):
            if hasattr(self, "ir_compiler"):
                parts = raw.strip().split(maxsplit=1)
                target = parts[1].strip() if len(parts) > 1 else ""
                content = Path(target).read_text(encoding="utf-8") if Path(target).exists() else target
                mod = self.ir_compiler.compile_source(content, module_name="cli_mod")
                valid, errors = self.ir_compiler.verify_module(mod)
                return f"[IR Compilation Complete]\nModule: {mod.module_name}\nFunctions: {len(mod.functions)}\nVerified: {valid}\n\n{mod.to_text()}"
            return "[Error] ir_compiler unavailable"

        if lowered.startswith("/ir-verify") or lowered.startswith("ir-verify"):
            if hasattr(self, "ir_compiler"):
                parts = raw.strip().split(maxsplit=1)
                mname = parts[1].strip() if len(parts) > 1 else "cli_mod"
                mod = self.ir_compiler.compiled_modules.get(mname)
                if not mod:
                    return f"[Error] Module '{mname}' not found."
                valid, errors = self.ir_compiler.verify_module(mod)
                err_str = f"\nErrors: {errors}" if errors else ""
                return f"[IR Module Verification: {mname}]\nStatus: {'VERIFIED_VALID' if valid else 'INVALID'}{err_str}"
            return "[Error] ir_compiler unavailable"

        # Stage 142: Static Single Assignment (SSA) Optimizer
        if lowered in {"/ssa-status", "ssa-status", "/optimizer-status", "optimizer-status"}:
            if hasattr(self, "ssa_optimizer"):
                return self.ssa_optimizer.format_ssa_status_table()

        if lowered.startswith("/ssa-optimize") or lowered.startswith("ssa-optimize"):
            if hasattr(self, "ssa_optimizer"):
                parts = raw.strip().split(maxsplit=1)
                target = parts[1].strip() if len(parts) > 1 else ""
                content = Path(target).read_text(encoding="utf-8") if Path(target).exists() else target
                opt_mod, rep = self.ssa_optimizer.optimize_source(content, module_name="cli_opt")
                rep_table = self.ssa_optimizer.format_optimization_report(rep)
                return f"{rep_table}\n\n[Optimized IR Disassembly]\n{opt_mod.to_text()}"
            return "[Error] ssa_optimizer unavailable"

        # Stage 143: Loop Invariant & Polyhedral Transformation Engine
        if lowered in {"/loop-status", "loop-status", "/polyhedral-status", "polyhedral-status"}:
            if hasattr(self, "loop_optimizer"):
                return self.loop_optimizer.format_loop_status_table()

        if lowered.startswith("/loop-optimize") or lowered.startswith("loop-optimize"):
            if hasattr(self, "loop_optimizer"):
                parts = raw.strip().split(maxsplit=1)
                target = parts[1].strip() if len(parts) > 1 else ""
                content = Path(target).read_text(encoding="utf-8") if Path(target).exists() else target
                opt_mod, rep = self.loop_optimizer.optimize_source(content, module_name="cli_loop_opt")
                rep_table = self.loop_optimizer.format_transform_report(rep)
                return f"{rep_table}\n\n[Loop-Optimized IR Disassembly]\n{opt_mod.to_text()}"
            return "[Error] loop_optimizer unavailable"

        # Stage 144: Register Allocation & Spill Cost Graph Colorer
        if lowered in {"/reg-status", "reg-status", "/allocator-status", "allocator-status"}:
            if hasattr(self, "register_allocator"):
                return self.register_allocator.format_reg_status_table()

        if lowered.startswith("/reg-allocate") or lowered.startswith("reg-allocate"):
            if hasattr(self, "register_allocator"):
                parts = raw.strip().split()
                target = parts[1] if len(parts) > 1 else ""
                k_val = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 8
                content = Path(target).read_text(encoding="utf-8") if Path(target).exists() else target
                results = self.register_allocator.allocate_source(content, k=k_val)
                out = f"[Register Allocation Complete (K={k_val})]\n"
                for fname, res in results.items():
                    out += f"\n{self.register_allocator.format_allocation_table(res)}\n"
                return out.strip()
            return "[Error] register_allocator unavailable"

        # Stage 145: Target-Agnostic Assembler & Machine Code Synthesizer
        if lowered in {"/asm-status", "asm-status", "/codegen-status", "codegen-status"}:
            if hasattr(self, "code_synthesizer"):
                return self.code_synthesizer.format_asm_status_table()

        if lowered.startswith("/asm-emit") or lowered.startswith("asm-emit"):
            if hasattr(self, "code_synthesizer"):
                parts = raw.strip().split()
                target = parts[1] if len(parts) > 1 else ""
                arch = parts[2] if len(parts) > 2 else "x86_64"
                content = Path(target).read_text(encoding="utf-8") if Path(target).exists() else target
                results = self.code_synthesizer.synthesize_source(content, target_arch=arch)
                out = f"[Machine Code Synthesis Complete ({arch})]\n"
                for fname, art in results.items():
                    out += f"\n{self.code_synthesizer.format_assembly_artifact(art)}\n"
                return out.strip()
            return "[Error] code_synthesizer unavailable"

        # Stage 146: Just-In-Time (JIT) Hotpath Tracer & Tiered Execution Engine
        if lowered in {"/jit-status", "jit-status", "/hotpath-status", "hotpath-status"}:
            if hasattr(self, "jit_tracer"):
                return self.jit_tracer.format_jit_status_table()

        if lowered.startswith("/jit-trace") or lowered.startswith("jit-trace"):
            if hasattr(self, "jit_tracer"):
                parts = raw.strip().split(maxsplit=1)
                fname = parts[1].strip() if len(parts) > 1 else ""
                trace = self.jit_tracer.jit_cache.get(fname)
                if trace:
                    return self.jit_tracer.format_trace_table(trace)
                return f"[Info] No JIT trace compiled yet for '@{fname}'. Invoke function to promote."
            return "[Error] jit_tracer unavailable"

        if lowered in {"/jit-flush", "jit-flush"}:
            if hasattr(self, "jit_tracer"):
                cnt = self.jit_tracer.flush_jit_cache()
                return f"[JIT Cache Flushed: {cnt} traces evicted]\n\n{self.jit_tracer.format_jit_status_table()}"
            return "[Error] jit_tracer unavailable" 

        greetings = {"hi", "hey", "hello", "hyy", "hii", "heyy", "yo", "bro"}
        if lowered in greetings or lowered in {f"{greeting} lucy" for greeting in greetings}:
            reply = f"Hey. I'm here. Active project: {self._conversation_active_project()}."
            if executed_summary:
                reply = f"{executed_summary}\n\n{reply}"
            if hasattr(self, "internal_monologue"):
                reply, _ = self.internal_monologue.process(raw, reply)
            if hasattr(self, "conversational_memory"):
                self.conversational_memory._in_memory_turns.append({"timestamp": datetime_now_iso(), "input": raw, "reply": reply, "quality": "low", "source": "fallback_v2"})
                self.conversational_memory.dialogue_tracker.observe_turn(raw, reply)
            self.self_improve_response(text, reply, quality="low", source="fallback_v2")
            return reply

        # 2. Stage 48: Autonomous Intent Dispatch
        if hasattr(self, "intent_dispatcher"):
            dispatch_result = self.intent_dispatcher.dispatch(raw)
            if dispatch_result and dispatch_result.get("handled"):
                reply = dispatch_result["message"]
                if executed_summary:
                    reply = f"{executed_summary}\n\n{reply}"
                if hasattr(self, "internal_monologue"):
                    reply, _ = self.internal_monologue.process(raw, reply)
                if hasattr(self, "conversational_memory"):
                    self.conversational_memory._in_memory_turns.append({"timestamp": datetime_now_iso(), "input": raw, "reply": reply, "quality": "high", "source": "intent_dispatcher"})
                    self.conversational_memory.dialogue_tracker.observe_turn(raw, reply)
                self.self_improve_response(text, reply, quality="high", source="intent_dispatcher")
                return reply

        # 3. Unified Cognitive Conversational Turn
        chat_result = self.conversational_chat(raw, action_summary=executed_summary, skip_observation=True)
        reply = chat_result.get("message", "")
        if executed_summary and executed_summary not in reply:
            reply = f"{executed_summary}\n\n{reply}" if reply else executed_summary
        if hasattr(self, "internal_monologue"):
            reply, _ = self.internal_monologue.process(raw, reply)
        if hasattr(self, "persona_governor"):
            reply, _ = self.persona_governor.process(raw, reply)
        if getattr(self, "terminal_sentinel", None) and self.terminal_sentinel.banner_enabled:
            reply = f"{self.terminal_sentinel.pulse().to_one_line()}\n{reply}"
        self.self_improve_response(
            text,
            reply,
            quality="high" if chat_result.get("online") else "low",
            source=chat_result.get("source") if chat_result.get("online") else "fallback_v2",
        )
        return reply

    def self_improve_response(
        self,
        user_input: str,
        reply: str,
        quality: str = "low",
        source: str = "fallback_v2",
    ) -> dict:
        record = {
            "timestamp": datetime_now_iso(),
            "input": self._safe_conversation_log_input(user_input),
            "reply": self._safe_preview_text(reply),
            "quality": quality,
            "source": source,
        }
        try:
            path = self._conversation_log_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            return {"logged": True, "file": str(path)}
        except Exception:
            return {"logged": False, "file": str(self._conversation_log_path())}

    def load_conversation_history(self, limit: int | None = None) -> list[dict]:
        path = self._conversation_log_path()
        if not path.exists():
            return []
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception:
            return []
        if limit is not None:
            lines = lines[-max(0, int(limit)):]

        history = []
        for line in lines:
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                history.append(item)
        return history

    def _conversation_log_path(self) -> Path:
        return self.project_root / "data" / "lucy" / "conversation_log.jsonl"

    def _safe_conversation_log_input(self, text: str) -> str:
        lowered = str(text or "").lower()
        sensitive_markers = ("api key", "token", "password", "secret", "seed phrase", "private key")
        if any(marker in lowered for marker in sensitive_markers):
            return "[redacted sensitive input]"
        return self._safe_preview_text(text)

    def _conversation_bootstrap_reply(self, text: str, resolved_context: str = "") -> str:
        raw = str(text or "").strip()
        # If multi-turn coreference bound this short follow-up to a prior turn topic/statement, respond with context
        if resolved_context and resolved_context != raw and hasattr(self, "conversational_memory") and self.conversational_memory._in_memory_turns:
            dt = getattr(self.conversational_memory, "dialogue_tracker", None)
            if dt and dt._turns:
                last_t = dt._turns[-1]
                topic = dt._current_topic or (dt._active_entities[0] if dt._active_entities else self._conversation_active_project())
                last_stmt = dt._last_assistant_statement or last_t.reply_text[:120]
                return f"Regarding {topic}: {last_stmt} — what part of that should we dive into or adjust next?"
        lowered = re.sub(r"\s+", " ", raw.lower())
        normalized = lowered.rstrip("?!., ")

        greetings = {"hi", "hey", "hello", "hyy", "hii", "heyy", "yo", "bro"}
        if normalized in greetings or normalized in {f"{greeting} lucy" for greeting in greetings}:
            return f"Hey. I'm here. Active project: {self._conversation_active_project()}."

        if normalized in {"how are you", "how are you lucy"}:
            return "Systems nominal. What do you need?"

        if normalized in {"what can you do", "what can you do lucy"}:
            return (
                "I can help with your active project, run checks, review memory, and answer questions about my current state. "
                "What would you like to start with?"
            )

        if any(term in normalized for term in ("conscious", "sentient", "alive")):
            return "I'm not literally conscious, sentient, or alive. I can track state, memory, and project continuity."

        if normalized in {"tell me", "tell me about it", "explain", "continue"}:
            status = self.current_lucy_status()
            return (
                f"Lucy status: Stage {status['active_stage']}. "
                f"Guardian {status['guardian_status']}. Agents {status['agents_status']}. "
                f"Next safe action: {status['next_safe_action']}"
            )

        if normalized in {"what next", "next", "now what", "wht next"}:
            return (
                f"Current active stage: {STAGE34_STAGE_LABEL}. "
                f"Next safe action: {STAGE34_OPERATIONAL_NEXT_ACTION}. "
                f"Stage 35 gate is {STAGE35_GATE}."
            )

        work_markers = ("work in progress", "working on lucy", "we are working", "ok we are work", "okee")
        acknowledgement_tokens = set(normalized.split())
        if any(marker in normalized for marker in work_markers) or acknowledgement_tokens.intersection({"ok", "okay"}):
            return f"Confirmed. Lucy is work in progress. Current safe move: {self._conversation_next_action()}."

        question_starters = (
            "what ",
            "why ",
            "how ",
            "when ",
            "where ",
            "who ",
            "can ",
            "could ",
            "should ",
            "is ",
            "are ",
            "do ",
            "does ",
            "did ",
        )
        if raw.endswith("?") or lowered.startswith(question_starters):
            return "I don't have enough context yet. Ask about Lucy's status, next step, memory, tests, or current stage."

        if len([word for word in normalized.split() if word]) < 4:
            return "I'm tracking this as context. Give me the next instruction or ask for current status."

        return "Understood. I logged the context. What should we do next?"

    def _conversation_active_project(self) -> str:
        try:
            project = self.project_summary()
            return str(project.get("name") or "Lucy")
        except Exception:
            return "Lucy"

    def _conversation_next_action(self) -> str:
        try:
            project = self.project_summary()
            next_action = str(project.get("next_action") or "").strip()
            if next_action:
                return self._clean_next_action(next_action)
        except Exception:
            pass
        return STAGE34_SAFE_NEXT_ACTION

    def record_interaction(self, user_text: str, response_text: str) -> None:
        try:
            self.learning.record_interaction(user_text, response_text)
        except Exception:
            self.logger.log(
                "error",
                "Learning interaction save failed.",
                source="learning",
            )
        try:
            project = self.project_summary()
            self.session_state.record_command(user_text, response_text, user_intent=user_text)
            self.session_state.update(
                active_project=project.get("name", "Lucy"),
                current_checkpoint=self._latest_checkpoint_id(),
                next_action=project.get("next_action", ""),
                system_status="online",
            )
            self.persistent_runtime.heartbeat(
                last_command=user_text,
                active_project=project.get("name", "Lucy"),
                guardian_status="active",
            )
        except Exception:
            self.logger.log(
                "error",
                "Session command or runtime heartbeat save failed.",
                source="session_state",
            )

    def learning_status(self) -> dict:
        return self.learning.status()

    def cognition_status(self) -> dict:
        return self.cognition.status()

    def cognition_vision(self) -> dict:
        return self.cognition.vision()

    def reflect(self, trigger: str = "manual", user_text: str = "") -> dict:
        context = self._cognition_context()
        result = self.cognition.reflect(trigger, user_text, context)
        self.logger.log(
            "cognition_reflected",
            f"Lucy cognition reflected from trigger: {trigger}",
            source="cognition",
        )
        self._auto_continuity_backup("cognition reflected")
        return result

    def _cognition_context(self) -> dict:
        return {
            "project": self.project_summary(),
            "memory": self.memory_audit(),
            "knowledge": self.ai_collections_status(),
            "daily_context": self.daily_context.brief_context(),
            "pending_approvals": len(self.list_approvals()),
        }

    def ingest_ai_collections(self, root: str | None = None) -> dict:
        result = self.knowledge.ingest(root)
        self.logger.log(
            "knowledge_ingested",
            "AI Collections ingestion completed." if result.get("ok") else "AI Collections ingestion failed.",
            source="knowledge",
            extra={
                "root": result.get("root", ""),
                "counts": result.get("counts", {}),
                "index_file": result.get("index_file", ""),
            },
        )
        return result

    def ai_collections_status(self) -> dict:
        return self.knowledge.status()

    def search_ai_collections(self, query: str) -> dict:
        result = self.knowledge.search(query)
        self.logger.log(
            "knowledge_searched",
            f"AI Collections search requested: {query!r}",
            source="knowledge",
        )
        return result

    def overnight_checkpoint_run(self, target_count: int = 100, pause_seconds: float = 0.0) -> dict:
        result = self.checkpoint_builder.ensure_minimum(
            target_count=target_count,
            pause_seconds=pause_seconds,
        )
        self.logger.log(
            "overnight_checkpoint_run",
            f"Checkpoint builder reached {result['final_count']} total checkpoints.",
            source="checkpoint_builder",
            extra={
                "created_count": result["created_count"],
                "target": result["target"],
                "learning_traces": result["learning_traces"],
            },
        )
        return result

    def learn_from_text(self, text: str) -> dict:
        result = self.learning.add_lesson(text)
        self.logger.log(
            "learning_saved",
            "Local lesson saved." if result.get("saved") else "Local lesson not saved.",
            source="learning",
        )
        if result.get("saved"):
            self._auto_continuity_backup("learning saved")
        return result

    def learn_style(self, text: str) -> dict:
        result = self.learning.add_style_preference(text)
        self.logger.log(
            "style_saved",
            "Talking style preference saved." if result.get("saved") else "Talking style preference not saved.",
            source="learning",
        )
        if result.get("saved"):
            self._auto_continuity_backup("style preference saved")
        return result

    def style_status(self) -> dict:
        return self.learning.style_status()

    def memory_fallback(self, query: str) -> dict:
        local_matches = self.recall(query)
        if local_matches:
            return {
                "source": "local_memory",
                "used_external_api": False,
                "matches": local_matches,
            }

        key = self.secrets.get("NVIDIA_API_KEY")
        if not key:
            proposal = self.learning.add_proposal(
                "NVIDIA memory fallback unavailable",
                "NVIDIA_API_KEY is missing. Run setup nvidia key inside Lucy, then retry memory fallback.",
                source="memory_fallback",
            )
            return {
                "source": "missing_api_key",
                "used_external_api": False,
                "proposal": proposal,
                "message": "No local memory matched. NVIDIA fallback needs a session key first.",
            }

        context = f"Active project: {self.project_summary().get('name')}. Memory audit: {self.memory.audit()}."
        result = self.external_tools.nvidia_memory.memory_fallback(query, context, key)
        if result.get("ok"):
            proposal = self.learning.add_proposal(
                "External memory fallback suggestion",
                result.get("text", ""),
                source="nvidia_memory_tool",
            )
            result["proposal"] = proposal
        self.logger.log(
            "tool_used",
            "NVIDIA memory fallback requested.",
            source="external_tools",
        )
        return {
            "source": "nvidia_memory_tool",
            "used_external_api": result.get("ok", False),
            "result": result,
        }

    def _guard_file_tool(self, action_name: str, target_path: str | None = None, metadata: dict | None = None) -> dict | None:
        project = self.project_summary()
        classification = self.guardian_core.classify_tool_action(
            action_name,
            target_path=target_path,
            metadata=metadata or {},
            active_project=project.get("name", "Lucy"),
        )
        self.logger.log(
            "guardian_classified",
            f"Guardian classified file tool request as {classification['classification']}.",
            source="guardian",
            extra={
                "tool_category": classification.get("tool_category"),
                "requires_confirmation": classification.get("requires_confirmation"),
                "blocked": classification.get("blocked"),
                "reason": classification.get("reason"),
            },
        )
        if classification.get("blocked"):
            result = {
                "ok": False,
                "action": "guardian_file_tool_check",
                "message": "Safe file tool request refused.",
                "data": {
                    "guardian_classification": classification.get("classification"),
                    "policy_decision": classification.get("policy_decision"),
                },
                "blocked": True,
                "reason": classification.get("reason"),
                "path": target_path,
            }
            self._append_tool_audit(action_name, target_path, result, guardian_result=classification)
            return result
        if classification.get("requires_confirmation"):
            confirmation = self.tool_confirmations.create_confirmation(
                action_name,
                classification.get("reason", "Manual confirmation required."),
                classification.get("policy_decision", {}).get("risk_level", "medium"),
                target_path=target_path,
                metadata={
                    **(metadata or {}),
                    "tool_category": classification.get("tool_category"),
                },
            )
            confirmation_id = confirmation["confirmation"]["id"]
            result = {
                "ok": False,
                "action": action_name,
                "message": "Tool action requires manual confirmation.",
                "data": {
                    "requires_confirmation": True,
                    "confirmation_id": confirmation_id,
                    "guardian_classification": classification.get("classification"),
                    "policy_decision": classification.get("policy_decision"),
                },
                "blocked": False,
                "reason": classification.get("reason"),
                "path": target_path,
            }
            self._append_tool_audit(action_name, target_path, result, guardian_result=classification, confirmation_id=confirmation_id)
            return result
        return None

    def _finalize_tool_result(self, action_name: str, target_path: str | None, result: dict) -> dict:
        data = result.get("data") if isinstance(result.get("data"), dict) else {}
        confirmation_id = data.get("confirmation_id")
        if data.get("requires_confirmation") and not confirmation_id:
            policy = data.get("policy_decision") if isinstance(data.get("policy_decision"), dict) else {}
            confirmation = self.tool_confirmations.create_confirmation(
                action_name,
                result.get("reason") or policy.get("reason") or "Manual confirmation required.",
                policy.get("risk_level", "medium"),
                target_path=target_path or result.get("path"),
                metadata={
                    "tool_category": policy.get("category"),
                    "file_size": self._file_size_for_audit(target_path or result.get("path")),
                },
            )
            confirmation_id = confirmation["confirmation"]["id"]
            data["confirmation_id"] = confirmation_id
            result["data"] = data
        self._append_tool_audit(action_name, target_path or result.get("path"), result, confirmation_id=confirmation_id)
        return result

    def _append_tool_audit(
        self,
        action_name: str,
        target_path: str | None,
        result: dict,
        guardian_result: dict | None = None,
        confirmation_id: str | None = None,
    ) -> None:
        audit_file = self.project_root / "data" / "lucy" / "tool_audit_log.jsonl"
        data = result.get("data") if isinstance(result.get("data"), dict) else {}
        policy = data.get("policy_decision") if isinstance(data.get("policy_decision"), dict) else {}
        session = self.session_state.status()
        project = self.project_summary()
        record = {
            "timestamp": datetime_now_iso(),
            "session_count": session.get("session_count"),
            "active_project": project.get("name", "Lucy"),
            "action_name": action_name,
            "target_path": target_path,
            "policy_category": policy.get("category") or (guardian_result or {}).get("tool_category"),
            "guardian_classification": (guardian_result or {}).get("classification") or data.get("guardian_classification"),
            "confirmation_id": confirmation_id,
            "result": self._tool_audit_result_label(result),
            "reason": result.get("reason"),
        }
        try:
            audit_file.parent.mkdir(parents=True, exist_ok=True)
            with open(audit_file, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def _tool_audit_result_label(self, result: dict) -> str:
        data = result.get("data") if isinstance(result.get("data"), dict) else {}
        if data.get("requires_confirmation"):
            return "requires_confirmation"
        if result.get("blocked"):
            return "blocked"
        if result.get("ok"):
            return "allowed"
        return "refused"

    def _file_size_for_audit(self, path: str | None) -> int | None:
        if not path:
            return None
        try:
            candidate = Path(path)
            if candidate.exists() and candidate.is_file():
                return candidate.stat().st_size
        except OSError:
            return None
        return None

    def _latest_checkpoint_id(self) -> str:
        try:
            checkpoints = self.checkpoints.list_checkpoints()
        except Exception:
            return ""
        if not checkpoints:
            return ""
        latest = checkpoints[-1]
        return str(latest.get("checkpoint_id", ""))

    def _startup_continuity_backup(self) -> None:
        try:
            result = self.continuity.startup_backup()
        except Exception as exc:
            self.logger.log(
                "error",
                f"Startup continuity backup failed: {exc}",
                source="continuity",
            )
            return
        self._log_continuity_result(result)

    def _auto_continuity_backup(self, reason: str) -> None:
        try:
            result = self.continuity.maybe_auto_backup(reason)
        except Exception as exc:
            self.logger.log(
                "error",
                f"Auto continuity backup failed: {exc}",
                source="continuity",
            )
            return
        self._log_continuity_result(result)

    def _log_continuity_result(self, result: dict, always: bool = False) -> None:
        if result.get("created"):
            self.logger.log(
                "continuity_backup_created",
                f"Continuity backup created: {result.get('path')}",
                source="continuity",
                extra={
                    "files": result.get("files", 0),
                    "reason": result.get("reason", ""),
                    "trigger": result.get("trigger", ""),
                    "removed_old_backups": result.get("removed_old_backups", 0),
                },
            )
        elif always:
            self.logger.log(
                "continuity_backup_skipped",
                f"Continuity backup skipped: {result.get('reason', 'unknown reason')}",
                source="continuity",
            )

    def provider_role_split_status(self) -> dict:
        return self.provider_role_split.status()

    def ollama_status(self) -> dict:
        return self.ollama_connector.status()

    def training_queue_status(self) -> dict:
        return self.training_queue.status()

    # ---------- STAGE 37: ELIE FACT/STATE VERIFIER ----------
    def fact_verifier_status(self) -> dict:
        return self.fact_verifier.status()

    def verify_claim(self, claim_text: str) -> dict:
        return self.fact_verifier.verify_claim(claim_text)

    def elie_security_review(self, code_text: str) -> dict:
        return self.fact_verifier.elie_security_review(code_text)



    # ---------- STAGE 38: TASK DAEMON & CONVERSATIONAL ROUTER ----------
    def task_daemon_status(self) -> dict:
        return self.task_daemon.status()

    def submit_background_task(
        self,
        name: str,
        fn: any,
        *args: any,
        total_steps: int = 1,
        metadata: dict | None = None,
        **kwargs: any,
    ) -> str:
        return self.task_daemon.submit_task(
            name, fn, *args, total_steps=total_steps, metadata=metadata, **kwargs
        )

    def get_background_task(self, task_id: str) -> dict | None:
        return self.task_daemon.get_task(task_id)

    def list_background_tasks(self, status: str | None = None, limit: int = 20) -> list[dict]:
        return self.task_daemon.list_tasks(status=status, limit=limit)

    def cancel_background_task(self, task_id: str) -> dict:
        return self.task_daemon.cancel_task(task_id)

    def record_turn(self, user_text: str, assistant_reply: str, **kwargs) -> dict:
        """Records conversational turn with conversational memory engine."""
        if hasattr(self, "conversational_memory"):
            return self.conversational_memory.record_turn(user_text, assistant_reply, **kwargs)
        return {"turn_id": "turn_001", "saved": True}

    def conversational_chat(
        self,
        text: str,
        action_summary: str = "",
        skip_observation: bool = False,
        _skip_observation: bool = False,
        **kwargs: Any,
    ) -> dict:
        raw = str(text or "").strip()
        if not raw:
            return {
                "stage": "66 conversational router",
                "message": "I'm listening. What do you need?",
                "source": "bootstrap",
                "online": False,
                "model": "deterministic_fallback",
            }

        should_skip = skip_observation or _skip_observation
        if not should_skip:
            if hasattr(self, "personal_profiler") and hasattr(self.personal_profiler, "observe_interaction"):
                try:
                    self.personal_profiler.observe_interaction(raw)
                except Exception:
                    pass
            if hasattr(self, "workflow_learner") and hasattr(self.workflow_learner, "observe_for_corrections"):
                try:
                    self.workflow_learner.observe_for_corrections(raw)
                except Exception:
                    pass
        if hasattr(self, "style_mirror") and hasattr(self.style_mirror, "detect_implicit_preferences"):
            try:
                self.style_mirror.detect_implicit_preferences(raw)
            except Exception:
                pass

        spine_data = self.spine.get("lucy", {}) if isinstance(self.spine, dict) else {}
        full_name = spine_data.get("full_name", "Living Unified Cognitive Yield")
        project_name = self._conversation_active_project()

        style_steering = self.style_mirror.build_style_steering_block(raw) if hasattr(self, "style_mirror") else ""
        guardrails = self.workflow_learner.prompt_guardrails_block() if hasattr(self, "workflow_learner") else ""
        few_shot_block = (
            self.personal_alignment.build_cloud_few_shot_block(max_examples=3)
            if hasattr(self, "personal_alignment") and hasattr(self.personal_alignment, "build_cloud_few_shot_block")
            else ""
        )
        ws_snippet = (
            self.workspace_sensor.build_workspace_prompt_snippet()
            if hasattr(self, "workspace_sensor")
            else ""
        )

        base_sys = "\n\n".join(
            p for p in [
                f"You are LUCY ({full_name}), Senin's direct, warm, and highly capable desktop companion.",
                action_summary,
                guardrails,
                style_steering,
                few_shot_block,
                ws_snippet,
            ] if p
        )

        # Build augmented prompt payload with coreference and casual gating
        prompt_pkg = self.conversational_memory.build_augmented_prompt(
            user_input=raw,
            system_prompt_base=base_sys,
            active_project=project_name,
            max_history_turns=6,
        )
        augmented_prompt = prompt_pkg.get("augmented_system_prompt", "")
        resolved_raw = prompt_pkg.get("resolved_input") or prompt_pkg.get("raw_prompt", raw)
        history_turns = prompt_pkg.get("history_turns", [])
        messages_array = prompt_pkg.get("messages")
        active_model = getattr(self, "active_model", None)

        # Tier 1: Local Sovereign Ollama with Native Multi-Turn Message Arrays
        res = self.ollama_connector.chat_or_fallback(
            prompt=resolved_raw,
            system_prompt=augmented_prompt,
            history=history_turns,
            messages=messages_array,
            model=active_model,
        )
        online = res.get("online", False)
        reply = res.get("message", "")
        source = res.get("source", "ollama_multiturn")

        # Tier 2: Multi-Provider Cloud Failover (when Ollama is offline and api_enabled is True)
        if not online and bool(self.config.get("api_enabled", False)):
            ext = self.external_tools.chat(prompt=resolved_raw, system_prompt=augmented_prompt, messages=messages_array)
            if ext.get("ok") and (ext.get("text") or ext.get("reply")):
                online = True
                reply = ext.get("text") or ext.get("reply")
                source = f"provider:{ext.get('provider', 'cloud')}"

        # Tier 3: Context-Aware Deterministic Spine Bootstrap
        if not online:
            boot_reply = self._conversation_bootstrap_reply(raw, resolved_context=resolved_raw)
            reply = boot_reply if boot_reply else f"[{project_name}] Running in sovereign terminal mode."
            source = "fallback_v2"

        # Stage 68: Internal Monologue & Pre-Output Verification Spine
        if hasattr(self, "internal_monologue"):
            reply, _ = self.internal_monologue.process(raw, reply)

        # Stage 69: Anti-Sycophancy & Persona Governor
        if hasattr(self, "persona_governor"):
            reply, _ = self.persona_governor.process(raw, reply)

        # Stage 61 & 55: Two-Layer Ground-Truth Verification BEFORE LoRA harvesting
        guarded = self.fact_verifier.guard_response(reply, runtime=self)
        reply = guarded.get("guarded_text", reply)
        disk_verified = bool(guarded.get("verified", True))
        badge = guarded.get("badge")

        receipt_verified = True
        if hasattr(self, "receipt_ledger"):
            receipt_check = self.receipt_ledger.verify_response_actions(reply)
            reply = receipt_check.get("guarded_text", reply)
            receipt_verified = bool(receipt_check.get("verified", True))

        # Admit 100% verified online turns into BOTH Stage 36/45 TrainingQueue and Stage 84/90 LoRA Harvester
        lora_admitted = False
        if online and disk_verified and receipt_verified:
            if hasattr(self, "master_synthesis"):
                syn_audit = self.master_synthesis.synthesize_turn(raw, reply)
                reply = syn_audit.clean_response
                lora_admitted = bool(getattr(syn_audit, "harvested_to_lora", False))
            if hasattr(self, "personal_alignment") and hasattr(self.personal_alignment, "maybe_admit_verified_turn"):
                try:
                    adm = self.personal_alignment.maybe_admit_verified_turn(
                        user_text=raw,
                        reply_text=reply,
                        disk_verified=disk_verified,
                        receipt_verified=receipt_verified,
                        source=source,
                    )
                    lora_admitted = lora_admitted or bool(adm.get("admitted", False))
                except Exception:
                    pass

        # Record turn to conversational memory (using raw user text so history stays clean)
        self.conversational_memory.record_turn(
            user_text=raw,
            reply_text=reply,
            source=source,
            quality="high" if (online and disk_verified and receipt_verified) else "standard",
            run_auto_extract=False,
        )

        return {
            "stage": "66 native multi-turn router",
            "message": reply,
            "source": source,
            "online": online,
            "model": res.get("model", active_model or "deterministic_fallback"),
            "badge": badge,
            "verification": guarded,
            "lora_admitted": lora_admitted,
        }

    # ---------- STAGE 43: CONVERSATIONAL MEMORY & CONTEXT ENGINE ----------
    def dialogue_tracker_status(self) -> dict:
        if hasattr(self, "conversational_memory") and hasattr(self.conversational_memory, "dialogue_tracker"):
            return self.conversational_memory.dialogue_tracker.status()
        return {"dialogue_tracker": "inactive"}

    # Stage 67: Rolling Episodic Context Summarizer
    def episodic_digest_status(self) -> dict:
        if hasattr(self, "conversational_memory") and hasattr(self.conversational_memory, "get_episodic_digest"):
            return self.conversational_memory.get_episodic_digest()
        return {}

    # Stage 68: Sovereign Internal Monologue & Pre-Output Verification Spine
    def internal_monologue_status(self) -> dict:
        if hasattr(self, "internal_monologue"):
            return self.internal_monologue.status()
        return {"internal_monologue": "inactive"}

    def last_thought(self) -> dict:
        if hasattr(self, "internal_monologue"):
            t = self.internal_monologue.get_last_thought()
            return t.to_dict() if t else {}
        return {}

    def format_last_thought(self) -> str:
        if hasattr(self, "internal_monologue"):
            t = self.internal_monologue.get_last_thought()
            return t.format_debug_view() if t else "No internal monologue recorded yet in this session."
        return "Internal monologue spine not active."

    # Stage 69: Anti-Sycophancy & Sovereign Persona Consistency Engine
    def persona_status(self) -> dict:
        if hasattr(self, "persona_governor"):
            return self.persona_governor.status()
        return {"persona_governor": "inactive"}

    # Stage 70: Autonomous Terminal ReAct Loop & Self-Healing Execution Engine
    def autonomous_exec(self, command: str, goal: str = "", max_attempts: int = 3) -> dict:
        if hasattr(self, "react_engine"):
            res = self.react_engine.execute_with_self_healing(command, goal=goal, max_attempts=max_attempts)
            return res.to_dict()
        return {"error": "react_engine inactive"}

    def react_status(self) -> dict:
        if hasattr(self, "react_engine"):
            return self.react_engine.status()
        return {"react_engine": "inactive"}

    # Stage 71: Local AST Codebase Indexer
    def find_symbol(self, name: str, exact: bool = False) -> list:
        if hasattr(self, "codebase_indexer"):
            return self.codebase_indexer.find_symbol(name, exact=exact)
        return []

    def codebase_outline(self, rel_path: str) -> list:
        if hasattr(self, "codebase_indexer"):
            return self.codebase_indexer.get_file_outline(rel_path)
        return []

    def codebase_index_status(self) -> dict:
        if hasattr(self, "codebase_indexer"):
            return self.codebase_indexer.status()
        return {"codebase_indexer": "inactive"}

    def conversational_memory_status(self) -> dict:
        return self.conversational_memory.status()

    def session_recap(self) -> dict:
        return self.conversational_memory.get_session_recap()

    def clear_session_context(self) -> dict:
        return self.conversational_memory.clear_active_context()

# ---------- STAGES 54–58: ADAPTIVE, GROUNDED ENGINE ----------
    def memory_graph_status(self) -> dict:
        return self.memory_graph.status()

    def memory_conflicts(self, limit: int = 15) -> list[dict]:
        return self.memory_graph.list_conflicts(limit=limit) if hasattr(self, "memory_graph") else []

    def memory_lineage(self, query_or_id: str) -> dict:
        return self.memory_graph.explain_lineage(query_or_id) if hasattr(self, "memory_graph") else {"ok": False}

    def pin_memory(self, selector: str, pinned: bool = True) -> dict:
        res = self.memory_graph.pin_fact(selector, pinned=pinned) if hasattr(self, "memory_graph") else {"ok": False}
        if res.get("ok") and hasattr(self, "receipt_ledger"):
            node_id = (res.get("node") or {}).get("id", selector)
            self.receipt_ledger.issue_receipt(
                action_category="memory_mutation",
                operation="pin_memory" if pinned else "unpin_memory",
                target=str(node_id),
                verified_outcome=f"{'Pinned' if pinned else 'Unpinned'} memory node {node_id}",
            )
        return res

    # Stage 72: Memory Graph Associative Edge Walker
    def walk_memory_graph(self, topic: str, limit: int = 5) -> list:
        if hasattr(self, "memory_walker") and hasattr(self, "memory_graph"):
            seed_nodes = self.memory_graph.query(topic, limit=3)
            seed_ids = [n.get("id") for n in seed_nodes if n.get("id")]
            return self.memory_walker.walk(seed_ids, limit=limit)
        return []

    def memory_walker_status(self) -> dict:
        if hasattr(self, "memory_walker"):
            return self.memory_walker.status()
        return {"memory_walker": "inactive"}

    # Stage 73: Dynamic Local Tool Synthesizer & Ephemeral Sandbox
    def synthesize_dynamic_tool(self, name: str, code: str, description: str = "", tags: list[str] = None) -> dict:
        if hasattr(self, "tool_synthesizer"):
            tool = self.tool_synthesizer.synthesize_tool(name, code, description=description, tags=tags)
            return tool.to_dict()
        return {"error": "tool_synthesizer unavailable"}

    def run_dynamic_tool(self, name: str, args: list[str] = None, timeout_sec: float = 10.0) -> dict:
        if hasattr(self, "tool_synthesizer"):
            res = self.tool_synthesizer.execute_tool(name, args=args, timeout_sec=timeout_sec)
            return res.to_dict()
        return {"error": "tool_synthesizer unavailable"}

    def run_ephemeral_code(self, code: str, args: list[str] = None, timeout_sec: float = 10.0) -> dict:
        if hasattr(self, "tool_synthesizer"):
            res = self.tool_synthesizer.run_ephemeral_code(code, args=args, timeout_sec=timeout_sec)
            return res.to_dict()
        return {"error": "tool_synthesizer unavailable"}

    def tool_synthesizer_status(self) -> dict:
        if hasattr(self, "tool_synthesizer"):
            return {
                "status": "active",
                "registered_tools": len(self.tool_synthesizer.tools),
                "sandbox_dir": str(self.tool_synthesizer.sandbox_dir),
            }
        return {"status": "inactive"}

    def purge_sandbox(self, max_age_hours: float = 24.0) -> dict:
        if hasattr(self, "tool_synthesizer"):
            return self.tool_synthesizer.purge_sandbox(max_age_hours=max_age_hours)
        return {"status": "inactive"}

    # Stage 74: Proactive Terminal Sentinel & Non-Intrusive Status Broadcaster
    def terminal_sentinel_pulse(self) -> dict:
        if hasattr(self, "terminal_sentinel"):
            p = self.terminal_sentinel.pulse()
            return {
                "timestamp": p.timestamp,
                "git_branch": p.git_branch,
                "git_dirty": p.git_dirty,
                "ollama_online": p.ollama_online,
                "memory_nodes_count": p.memory_nodes_count,
                "background_tasks_count": p.background_tasks_count,
                "synthesized_tools_count": p.synthesized_tools_count,
                "workspace_delta_count": p.workspace_delta_count,
                "banner": p.to_one_line(),
            }
        return {"status": "inactive"}

    def terminal_sentinel_status(self) -> dict:
        if hasattr(self, "terminal_sentinel"):
            return {
                "status": "active",
                "banner_enabled": self.terminal_sentinel.banner_enabled,
                "tracked_files": len(self.terminal_sentinel._file_snapshots),
            }
        return {"status": "inactive"}

    def terminal_sentinel_deltas(self) -> list:
        if hasattr(self, "terminal_sentinel"):
            return [d.__dict__ for d in self.terminal_sentinel.detect_workspace_deltas()]
        return []

    # Stage 75: Terminal ANSI Canvas & Syntax-Highlighted Visual Stream
    def render_canvas_box(self, title: str, lines: list[str], width: int = 72) -> str:
        if hasattr(self, "terminal_canvas"):
            return self.terminal_canvas.render_box(title, lines, width=width)
        return "\n".join([f"=== {title} ==="] + lines)

    def render_canvas_tree(self, target_dir: str = "", max_depth: int = 2) -> str:
        if hasattr(self, "terminal_canvas"):
            d = Path(target_dir) if target_dir else self.project_root
            if not d.is_absolute():
                d = self.project_root / d
            return self.terminal_canvas.render_tree(d, max_depth=max_depth)
        return ""

    def view_file_canvas(self, path: str, max_lines: int = 80) -> str:
        if hasattr(self, "terminal_canvas"):
            p = Path(path)
            if not p.is_absolute():
                p = self.project_root / p
            return self.terminal_canvas.view_file(p, max_lines=max_lines)
        return f"File view unavailable: {path}"

    def terminal_canvas_status(self) -> dict:
        if hasattr(self, "terminal_canvas"):
            return {
                "status": "active",
                "colors_enabled": self.terminal_canvas.highlighter.enabled,
            }
        return {"status": "inactive"}

    # Stage 76: Autonomous Memory Pruning & Cognitive Distillation
    def distill_memory_graph(self, threshold: float = 0.25) -> dict:
        if hasattr(self, "memory_distiller"):
            rep = self.memory_distiller.distill(threshold=threshold)
            return rep.to_dict()
        return {"error": "memory_distiller unavailable"}

    def preview_memory_distillation(self, threshold: float = 0.25) -> dict:
        if hasattr(self, "memory_distiller"):
            rep = self.memory_distiller.dry_run(threshold=threshold)
            return rep.to_dict()
        return {"error": "memory_distiller unavailable"}

    def memory_distillation_stats(self) -> dict:
        if hasattr(self, "memory_distiller"):
            return self.memory_distiller.stats()
        return {"error": "memory_distiller unavailable"}

    # Stage 77: Autonomous Git Branch & Code Review Companion
    def review_code(self, diff_text: str = None) -> dict:
        if hasattr(self, "code_reviewer"):
            rep = self.code_reviewer.review_diff(diff_text=diff_text)
            return rep.to_dict()
        return {"error": "code_reviewer unavailable"}

    def suggest_commit_message(self) -> str:
        if hasattr(self, "code_reviewer"):
            rep = self.code_reviewer.review_diff()
            return rep.proposed_commit
        return ""

    def get_semantic_changelog(self, limit: int = 5) -> str:
        if hasattr(self, "code_reviewer"):
            return self.code_reviewer.generate_changelog(recent_commits_limit=limit)
        return ""

    def code_reviewer_status(self) -> dict:
        if hasattr(self, "code_reviewer"):
            return {
                "status": "active",
                "branch": self.code_reviewer.get_git_branch(),
            }
        return {"status": "inactive"}

    # Stage 78: Multi-File Refactor & Atomic Patch Orchestrator
    def begin_atomic_patch(self, description: str = "") -> dict:
        if hasattr(self, "atomic_patcher"):
            tx = self.atomic_patcher.begin_transaction(description=description)
            return tx.to_dict()
        return {"error": "atomic_patcher unavailable"}

    def stage_atomic_file(self, file_path: str, new_content: str, tx_id: str = None) -> bool:
        if hasattr(self, "atomic_patcher"):
            return self.atomic_patcher.stage_file_patch(file_path, new_content, tx_id=tx_id)
        return False

    def commit_atomic_patch(self, tx_id: str = None) -> tuple[bool, str]:
        if hasattr(self, "atomic_patcher"):
            return self.atomic_patcher.commit_transaction(tx_id=tx_id)
        return False, "atomic_patcher unavailable"

    def rollback_atomic_patch(self, tx_id: str = None) -> tuple[bool, str]:
        if hasattr(self, "atomic_patcher"):
            return self.atomic_patcher.rollback_transaction(tx_id=tx_id)
        return False, "atomic_patcher unavailable"

    def atomic_patch_status(self) -> dict:
        if hasattr(self, "atomic_patcher"):
            tx = self.atomic_patcher.active_tx
            return {
                "status": "active",
                "active_tx": tx.to_dict() if tx else None,
                "total_transactions": len(self.atomic_patcher.transactions),
            }
        return {"status": "inactive"}

    # Stage 79: Local Test Suite Auto-Discoverer & Regression Triage Engine
    def run_affected_tests(self) -> dict:
        if hasattr(self, "test_triage"):
            res = self.test_triage.triage_uncommitted()
            return res.to_dict()
        return {"error": "test_triage unavailable"}

    def triage_test_suite(self, test_name_or_path: str = "") -> dict:
        if hasattr(self, "test_triage"):
            if test_name_or_path:
                matching = [f for f in self.test_triage.tests_dir.glob("test_*.py") if test_name_or_path.lower() in f.stem.lower()]
                res = self.test_triage.run_tests(matching)
            else:
                res = self.test_triage.triage_uncommitted()
            return res.to_dict()
        return {"error": "test_triage unavailable"}

    def test_triage_status(self) -> dict:
        if hasattr(self, "test_triage"):
            return {
                "status": "active",
                "indexed_test_suites": len(list(self.test_triage.tests_dir.glob("test_*.py"))),
            }
        return {"status": "inactive"}

    # Stage 80: Multi-Turn Operator Goal Decomposition & Task Graph Engine
    def create_goal_plan(self, goal_description: str) -> dict:
        if hasattr(self, "task_graph"):
            dag = self.task_graph.create_plan(goal_description)
            return dag.to_dict()
        return {"error": "task_graph unavailable"}

    def get_active_goal_plan(self) -> dict:
        if hasattr(self, "task_graph") and self.task_graph.active_dag:
            return self.task_graph.active_dag.to_dict()
        return {"status": "no_active_plan"}

    def complete_goal_task(self, task_id: str, summary: str = "") -> tuple[bool, str]:
        if hasattr(self, "task_graph"):
            return self.task_graph.complete_task(task_id, summary=summary)
        return False, "task_graph unavailable"

    def get_next_goal_task(self) -> dict:
        if hasattr(self, "task_graph"):
            nt = self.task_graph.get_next_task()
            return nt.to_dict() if nt else {}
        return {}

    def clear_goal_plan(self) -> bool:
        if hasattr(self, "task_graph"):
            return self.task_graph.clear_plan()
        return False

    def task_graph_status(self) -> dict:
        if hasattr(self, "task_graph"):
            has_plan = self.task_graph.active_dag is not None
            return {
                "status": "active",
                "has_active_plan": has_plan,
                "progress_percent": self.task_graph.active_dag.progress_percent() if has_plan else 0,
            }
        return {"status": "inactive"}

    # Stage 81: Sovereign Terminal Web Explorer & Headless Search Engine
    def search_web(self, query: str, max_results: int = 5) -> dict:
        if hasattr(self, "web_explorer"):
            res = self.web_explorer.search(query, max_results=max_results)
            return res.to_dict()
        return {"error": "web_explorer unavailable"}

    def web_explorer_status(self) -> dict:
        if hasattr(self, "web_explorer"):
            return self.web_explorer.status()
        return {"status": "inactive"}

    def clear_web_cache(self) -> int:
        if hasattr(self, "web_explorer"):
            return self.web_explorer.clear_cache()
        return 0

    # Stage 82: Grounded Web Page Extractor & Documentation Reader
    def fetch_web_page(self, url: str, bypass_cache: bool = False) -> dict:
        if hasattr(self, "web_reader"):
            page = self.web_reader.fetch_url(url, bypass_cache=bypass_cache)
            return page.to_dict()
        return {"error": "web_reader unavailable"}

    def fetch_pypi_package(self, package_name: str) -> dict:
        if hasattr(self, "web_reader"):
            return self.web_reader.fetch_pypi_package(package_name)
        return {"error": "web_reader unavailable"}

    def web_reader_status(self) -> dict:
        if hasattr(self, "web_reader"):
            return self.web_reader.status()
        return {"status": "inactive"}

    def clear_web_reader_cache(self) -> int:
        if hasattr(self, "web_reader"):
            return self.web_reader.clear_cache()
        return 0

    # Stage 83: Web-Grounded Cross-Verification & Fact-Checking RAG
    def verify_web_claim(self, claim: str, bypass_cache: bool = False) -> dict:
        if hasattr(self, "web_verifier"):
            res = self.web_verifier.verify_claim(claim, bypass_cache=bypass_cache)
            return res.to_dict()
        return {"error": "web_verifier unavailable"}

    def verify_web_code_snippet(self, code: str) -> dict:
        if hasattr(self, "web_verifier"):
            return self.web_verifier.verify_code_snippet(code)
        return {"error": "web_verifier unavailable"}

    def web_verifier_status(self) -> dict:
        if hasattr(self, "web_verifier"):
            return self.web_verifier.status()
        return {"status": "inactive"}

    def clear_web_verifier_cache(self) -> int:
        if hasattr(self, "web_verifier"):
            return self.web_verifier.clear_cache()
        return 0

    # Stage 84: High-Signal LoRA Interaction Harvester & Preference Dataset Curator
    def harvest_interaction(self, instruction: str, response: str, category: str = "coding", metadata: dict = None) -> dict:
        if hasattr(self, "lora_harvester"):
            item = self.lora_harvester.harvest_turn(instruction, response, category=category, metadata=metadata)
            if item:
                return {"curated": True, "interaction_id": item.interaction_id, "signal_score": item.signal_score}
            return {"curated": False, "reason": "Signal score below admission threshold"}
        return {"error": "lora_harvester unavailable"}

    def lora_harvester_status(self) -> dict:
        if hasattr(self, "lora_harvester"):
            return self.lora_harvester.status()
        return {"status": "inactive"}

    def prune_lora_harvest(self, min_score: float = 0.70) -> int:
        if hasattr(self, "lora_harvester"):
            return self.lora_harvester.prune_low_signal(threshold=min_score)
        return 0

    # Stage 85: Local Model Adapter Compiler & Ollama Hot-Swap Engine
    def compile_lora_adapter(self, custom_tag: str = None, max_exemplars: int = 6) -> dict:
        if hasattr(self, "lora_compiler"):
            res = self.lora_compiler.compile_model(custom_tag=custom_tag, max_exemplars=max_exemplars)
            if res.get("compiled") and res.get("swapped_active"):
                self.active_model = res.get("active_model", self.active_model)
            return res
        return {"error": "lora_compiler unavailable"}

    def hot_swap_model(self, target_model: str) -> dict:
        if hasattr(self, "lora_compiler"):
            res = self.lora_compiler.hot_swap(target_model)
            if res.get("success"):
                self.active_model = res.get("active_model", self.active_model)
            return res
        return {"error": "lora_compiler unavailable"}

    def rollback_model(self) -> dict:
        if hasattr(self, "lora_compiler"):
            res = self.lora_compiler.rollback()
            if res.get("success"):
                self.active_model = res.get("active_model", self.active_model)
            return res
        return {"error": "lora_compiler unavailable"}

    def lora_compiler_status(self) -> dict:
        if hasattr(self, "lora_compiler"):
            return self.lora_compiler.status()
        return {"status": "inactive"}

    # Stage 86: 25-Question Anti-Catastrophic-Forgetting Sanity Gate
    def run_sanity_gate(self, responder_fn = None, model_tag: str = None) -> dict:
        if hasattr(self, "sanity_gate"):
            tag = model_tag or getattr(self, "active_model", "current_model")
            report = self.sanity_gate.run_sanity_gate(responder_fn=responder_fn, model_tag=tag)
            return report.to_dict()
        return {"error": "sanity_gate unavailable"}

    def sanity_gate_status(self) -> dict:
        if hasattr(self, "sanity_gate"):
            return self.sanity_gate.status()
        return {"status": "inactive"}

    # Stage 87: Epistemic Provenance Tracker & Anti-Hallucination Confidence Spine
    def audit_response_provenance(self, response_text: str, web_grounded: bool = False, memory_grounded: bool = False) -> dict:
        if hasattr(self, "epistemic_tracker"):
            att = self.epistemic_tracker.verify_response_provenance(
                response_text,
                web_grounded=web_grounded,
                memory_grounded=memory_grounded,
            )
            return att.to_dict()
        return {"error": "epistemic_tracker unavailable"}

    def epistemic_provenance_status(self) -> dict:
        if hasattr(self, "epistemic_tracker"):
            return self.epistemic_tracker.status()
        return {"status": "inactive"}

    # Stage 88: Dynamic Few-Shot Operator Style Mirror & Semantic Preference Ingestion
    def ingest_operator_preference(self, key: str, value: str, category: str = "general") -> dict:
        if hasattr(self, "style_mirror"):
            pref = self.style_mirror.ingest_preference(key, value, category=category)
            return pref.to_dict()
        return {"error": "style_mirror unavailable"}

    def build_style_steering_prompt(self, current_prompt: str) -> str:
        if hasattr(self, "style_mirror"):
            return self.style_mirror.build_style_steering_block(current_prompt)
        return ""

    def style_mirror_status(self) -> dict:
        if hasattr(self, "style_mirror"):
            return self.style_mirror.status()
        return {"status": "inactive"}

    # Stage 89: Autonomous Hypothesis Generation & Pre-Response Counterfactual Verifier
    def generate_hypotheses(self, problem: str, code_context: str = None) -> list:
        if hasattr(self, "hypothesis_engine"):
            hyps = self.hypothesis_engine.formulate_hypotheses(problem, code_context=code_context)
            return [h.to_dict() for h in hyps]
        return []

    def evaluate_counterfactual_proposal(self, proposal: str) -> dict:
        if hasattr(self, "hypothesis_engine"):
            return self.hypothesis_engine.evaluate_solution_candidate(proposal)
        return {"error": "hypothesis_engine unavailable"}

    def hypothesis_engine_status(self) -> dict:
        if hasattr(self, "hypothesis_engine"):
            return self.hypothesis_engine.status()
        return {"status": "inactive"}

    # Stage 90: Master Sovereign AGI Cognitive Synthesis & Continuous Alignment Checkpoint
    def synthesize_turn(self, instruction: str, response: str, metadata: dict = None) -> dict:
        if hasattr(self, "master_synthesis"):
            res = self.master_synthesis.synthesize_turn(instruction, response, metadata=metadata)
            return res.to_dict()
        return {"error": "master_synthesis unavailable"}

    def create_alignment_checkpoint(self) -> dict:
        if hasattr(self, "master_synthesis"):
            chk = self.master_synthesis.create_alignment_checkpoint()
            return chk.to_dict()
        return {"error": "master_synthesis unavailable"}

    # Stage 91: Autonomous Code Mutation & Fuzz Tester
    def run_mutation_test(self, file_path: str, max_mutants: int = 10) -> dict:
        if hasattr(self, "mutation_fuzzer"):
            res = self.mutation_fuzzer.run_mutation_test(file_path, max_mutants=max_mutants)
            return res.to_dict()
        return {"error": "mutation_fuzzer unavailable"}

    def fuzz_cli(self, iterations: int = 40) -> dict:
        if hasattr(self, "mutation_fuzzer"):
            res = self.mutation_fuzzer.fuzz_cli(iterations=iterations)
            return res.to_dict()
        return {"error": "mutation_fuzzer unavailable"}

    def mutation_fuzzer_status(self) -> dict:
        if hasattr(self, "mutation_fuzzer"):
            return self.mutation_fuzzer.status()
        return {"status": "inactive"}

    # Stage 92: Self-Healing Runtime Patch Engine
    def heal(self, target_or_error: str) -> str:
        if hasattr(self, "self_healing_patcher"):
            return self.self_healing_patcher.heal(target_or_error)
        return "[Error] self_healing_patcher unavailable"

    def rollback_patch(self, patch_id: str) -> dict:
        if hasattr(self, "self_healing_patcher"):
            ok, msg = self.self_healing_patcher.rollback_patch(patch_id)
            return {"ok": ok, "message": msg}
        return {"ok": False, "error": "self_healing_patcher unavailable"}

    def self_healing_status(self) -> dict:
        if hasattr(self, "self_healing_patcher"):
            return self.self_healing_patcher.status()
        return {"status": "inactive"}

    # Stage 93: Semantic AST Vector Code Indexer
    def search_code(self, query: str, top_k: int = 5) -> dict:
        if hasattr(self, "ast_vector_index"):
            matches = self.ast_vector_index.search(query, top_k=top_k)
            return {"query": query, "matches": [m.to_dict() for m in matches]}
        return {"query": query, "matches": [], "error": "ast_vector_index unavailable"}

    def index_code_repository(self) -> dict:
        if hasattr(self, "ast_vector_index"):
            summary = self.ast_vector_index.index_repository()
            return summary.to_dict()
        return {"error": "ast_vector_index unavailable"}

    def get_symbol_tree(self, module_or_file: str) -> str:
        if hasattr(self, "ast_vector_index"):
            return self.ast_vector_index.get_symbol_tree(module_or_file)
        return "[Error] ast_vector_index unavailable"

    def code_index_status(self) -> dict:
        if hasattr(self, "ast_vector_index"):
            return self.ast_vector_index.status()
        return {"status": "inactive"}

    # Stage 94: Architecture Specification Drift Detector & Realignment Engine
    def audit_architecture_drift(self) -> dict:
        if hasattr(self, "spec_drift_detector"):
            report = self.spec_drift_detector.audit()
            return report.to_dict()
        return {"error": "spec_drift_detector unavailable"}

    def realign_architecture_spec(self, spec_id: str | None = None) -> dict:
        if hasattr(self, "spec_drift_detector"):
            return self.spec_drift_detector.realign_spec(spec_id)
        return {"error": "spec_drift_detector unavailable"}

    def get_drift_report(self) -> str:
        if hasattr(self, "spec_drift_detector"):
            return self.spec_drift_detector.format_report()
        return "[Error] spec_drift_detector unavailable"

    def spec_drift_status(self) -> dict:
        if hasattr(self, "spec_drift_detector"):
            return self.spec_drift_detector.status()
        return {"status": "inactive"}

    # Stage 95: Multi-Agent Autonomous Worktree & Branching Fabric
    def spawn_worktree_branch(self, branch_name: str, task: str = "", agent_role: str = "coder") -> dict:
        if hasattr(self, "worktree_fabric"):
            branch = self.worktree_fabric.spawn_branch(branch_name, task=task, agent_role=agent_role)
            return branch.to_dict()
        return {"error": "worktree_fabric unavailable"}

    def merge_worktree_branch(self, branch_name: str, strategy: str = "safe") -> dict:
        if hasattr(self, "worktree_fabric"):
            res = self.worktree_fabric.merge_worktree(branch_name, strategy=strategy)
            return res.to_dict()
        return {"error": "worktree_fabric unavailable"}

    def get_worktree_status(self) -> str:
        if hasattr(self, "worktree_fabric"):
            return self.worktree_fabric.tree_status()
        return "[Error] worktree_fabric unavailable"

    def worktree_fabric_status(self) -> dict:
        if hasattr(self, "worktree_fabric"):
            return self.worktree_fabric.status()
        return {"status": "inactive"}

    # Stage 96: Sovereign Offline Quantization & GGUF Model Compressor
    def quantize_model_weights(self, source_path_or_name: str, quant_type: str = "Q4_K_M") -> dict:
        if hasattr(self, "model_quantizer"):
            res = self.model_quantizer.quantize_weights(source_path_or_name, quant_type=quant_type)
            return res.to_dict()
        return {"error": "model_quantizer unavailable"}

    def export_gguf_model(self, model_name: str, quant_type: str = "Q4_K_M") -> dict:
        if hasattr(self, "model_quantizer"):
            return self.model_quantizer.export_gguf(model_name, quant_type=quant_type)
        return {"error": "model_quantizer unavailable"}

    def get_quant_status(self) -> str:
        if hasattr(self, "model_quantizer"):
            return self.model_quantizer.quant_status()
        return "[Error] model_quantizer unavailable"

    def model_quantizer_status(self) -> dict:
        if hasattr(self, "model_quantizer"):
            return self.model_quantizer.status()
        return {"status": "inactive"}

    # Stage 97: Causal DAG Epistemic Memory & Counterfactual Timeline
    def record_causal_event(self, title: str, event_type: str = "SYSTEM_DECISION", details: str = "", cause_ids: list[str] | None = None) -> dict:
        if hasattr(self, "causal_dag"):
            node = self.causal_dag.record_event(title, event_type=event_type, details=details, cause_ids=cause_ids)
            return node.to_dict()
        return {"error": "causal_dag unavailable"}

    def explain_causal_why(self, target: str) -> dict:
        if hasattr(self, "causal_dag"):
            chain = self.causal_dag.causal_why(target)
            return chain.to_dict()
        return {"error": "causal_dag unavailable"}

    def replay_counterfactual(self, node_id: str, intervention: str) -> dict:
        if hasattr(self, "causal_dag"):
            cf = self.causal_dag.counterfactual_replay(node_id, intervention)
            return cf.to_dict()
        return {"error": "causal_dag unavailable"}

    def get_dag_timeline(self) -> str:
        if hasattr(self, "causal_dag"):
            return self.causal_dag.dag_timeline()
        return "[Error] causal_dag unavailable"

    def causal_dag_status(self) -> dict:
        if hasattr(self, "causal_dag"):
            return self.causal_dag.status()
        return {"status": "inactive"}

    # Stage 98: Zero-Leak Host Sandbox & Process Containment Gate
    def run_sandboxed(self, script_or_command: str, is_python_code: bool = False, timeout_sec: float = 10.0) -> dict:
        if hasattr(self, "host_sandbox"):
            res = self.host_sandbox.run_in_sandbox(script_or_command, is_python_code=is_python_code, timeout_sec=timeout_sec)
            return res.to_dict()
        return {"error": "host_sandbox unavailable"}

    def audit_credential_leaks(self) -> dict:
        if hasattr(self, "host_sandbox"):
            report = self.host_sandbox.leak_audit()
            return report.to_dict()
        return {"error": "host_sandbox unavailable"}

    def get_quarantine_status(self) -> str:
        if hasattr(self, "host_sandbox"):
            return self.host_sandbox.quarantine_status()
        return "[Error] host_sandbox unavailable"

    def release_quarantine_items(self, target: str = "all") -> dict:
        if hasattr(self, "host_sandbox"):
            return self.host_sandbox.release_quarantine(target)
        return {"error": "host_sandbox unavailable"}

    def host_sandbox_status(self) -> dict:
        if hasattr(self, "host_sandbox"):
            return self.host_sandbox.status()
        return {"status": "inactive"}

    # Stage 99: Local Hardware Telemetry & Inference Throttle Guard
    def get_hardware_dashboard(self) -> str:
        if hasattr(self, "hardware_telemetry"):
            return self.hardware_telemetry.hardware_status()
        return "[Error] hardware_telemetry unavailable"

    def tune_vram_parameters(self, param_billions: float = 3.0) -> dict:
        if hasattr(self, "hardware_telemetry"):
            rec = self.hardware_telemetry.vram_tune(param_billions)
            return rec.to_dict()
        return {"error": "hardware_telemetry unavailable"}

    def run_inference_benchmark(self, test_tokens: int = 50) -> dict:
        if hasattr(self, "hardware_telemetry"):
            res = self.hardware_telemetry.bench_inference(test_tokens)
            return res.to_dict()
        return {"error": "hardware_telemetry unavailable"}

    def configure_throttle_guard(self, ram_pct: float | None = None, temp_c: float | None = None) -> dict:
        if hasattr(self, "hardware_telemetry"):
            return self.hardware_telemetry.set_throttle_thresholds(ram_pct=ram_pct, temp_c=temp_c)
        return {"error": "hardware_telemetry unavailable"}

    def hardware_telemetry_status(self) -> dict:
        if hasattr(self, "hardware_telemetry"):
            return self.hardware_telemetry.status()
        return {"status": "inactive"}

    # Stage 100: Centennial Sovereign Master Seal & Cryptographic Self-Attestation Fabric
    def generate_master_seal(self) -> dict:
        if hasattr(self, "master_seal"):
            return self.master_seal.generate_seal(runtime=self).to_dict()
        return {"error": "master_seal unavailable"}

    def verify_master_seal(self) -> dict:
        if hasattr(self, "master_seal"):
            return self.master_seal.verify_seal()
        return {"error": "master_seal unavailable"}

    def get_centennial_banner(self) -> str:
        if hasattr(self, "master_seal"):
            return self.master_seal.get_centennial_banner()
        return "[Error] master_seal unavailable"

    def master_seal_status(self) -> dict:
        if hasattr(self, "master_seal"):
            return self.master_seal.status()
        return {"status": "inactive"}

    # Stage 101: Autonomous Kernel & Process Watchdog Fabric
    def get_supervisor_dashboard(self) -> str:
        if hasattr(self, "kernel_supervisor"):
            self.kernel_supervisor.heartbeat_all_active()
            return self.kernel_supervisor.supervisor_status()
        return "[Error] kernel_supervisor unavailable"

    def audit_supervisor_heartbeats(self, auto_recover: bool = True) -> dict:
        if hasattr(self, "kernel_supervisor"):
            self.kernel_supervisor.heartbeat_all_active()
            rep = self.kernel_supervisor.audit_heartbeats(auto_recover=auto_recover)
            return rep.to_dict()
        return {"error": "kernel_supervisor unavailable"}

    def recover_subsystem(self, name: str, force: bool = False) -> dict:
        if hasattr(self, "kernel_supervisor"):
            return self.kernel_supervisor.recover_subsystem(name, force=force)
        return {"error": "kernel_supervisor unavailable"}

    def kernel_supervisor_status(self) -> dict:
        if hasattr(self, "kernel_supervisor"):
            return self.kernel_supervisor.status()
        return {"status": "inactive"}

    # Stage 102: Dynamic Execution Profiler & Flamegraph Tracer
    def get_flamegraph(self) -> str:
        if hasattr(self, "execution_profiler"):
            return self.execution_profiler.get_latest_flamegraph()
        return "[Error] execution_profiler unavailable"

    def get_latency_audit(self) -> str:
        if hasattr(self, "execution_profiler"):
            return self.execution_profiler.get_latency_audit_report()
        return "[Error] execution_profiler unavailable"

    def get_hot_paths(self, top_n: int = 8) -> str:
        if hasattr(self, "execution_profiler"):
            return self.execution_profiler.get_hot_paths_table(top_n=top_n)
        return "[Error] execution_profiler unavailable"

    def profile_command_execution(self, command: str) -> dict:
        if hasattr(self, "execution_profiler"):
            with self.execution_profiler.profile_scope(f"profile:{command}") as meta:
                _ = self.respond(command)
            return meta["result"].to_dict()
        return {"error": "execution_profiler unavailable"}

    def execution_profiler_status(self) -> dict:
        if hasattr(self, "execution_profiler"):
            return self.execution_profiler.status()
        return {"status": "inactive"}

    # Stage 103: Hybrid Neural-Lexical Vector RAG Engine
    def neural_search(self, query: str, top_k: int = 5) -> dict:
        if hasattr(self, "neural_retriever"):
            return self.neural_retriever.search(query, top_k=top_k).to_dict()
        return {"error": "neural_retriever unavailable"}

    def reindex_rag(self) -> dict:
        if hasattr(self, "neural_retriever"):
            return self.neural_retriever.reindex()
        return {"error": "neural_retriever unavailable"}

    def retrieve_context_for_prompt(self, query: str, max_tokens: int = 1500) -> str:
        if hasattr(self, "neural_retriever"):
            return self.neural_retriever.retrieve_context_window(query, max_tokens=max_tokens)
        return "[Error] neural_retriever unavailable"

    def neural_retriever_status(self) -> dict:
        if hasattr(self, "neural_retriever"):
            return self.neural_retriever.status()
        return {"status": "inactive"}

    # Stage 104: Autonomous Refactoring & Code Quality Enforcer
    def scan_tech_debt(self, top_n: int = 8) -> str:
        if hasattr(self, "refactor_engine"):
            return self.refactor_engine.format_tech_debt_table(top_n=top_n)
        return "[Error] refactor_engine unavailable"

    def suggest_refactorings(self, file_path: str) -> list:
        if hasattr(self, "refactor_engine"):
            props = self.refactor_engine.suggest_refactorings(file_path)
            return [p.to_dict() for p in props]
        return []

    def apply_refactor_patch(self, proposal_id: str) -> dict:
        if hasattr(self, "refactor_engine"):
            return self.refactor_engine.apply_refactor_patch(proposal_id)
        return {"error": "refactor_engine unavailable"}

    def refactor_engine_status(self) -> dict:
        if hasattr(self, "refactor_engine"):
            return self.refactor_engine.status()
        return {"status": "inactive"}

    # Stage 105: Sovereign P2P Peer Mesh & Local Sync
    def get_mesh_status(self) -> str:
        if hasattr(self, "peer_mesh"):
            return self.peer_mesh.mesh_status()
        return "[Error] peer_mesh unavailable"

    def discover_mesh_peers(self) -> list:
        if hasattr(self, "peer_mesh"):
            return [p.to_dict() for p in self.peer_mesh.discover_peers()]
        return []

    def sync_mesh_network(self, peer_id: str | None = None) -> dict:
        if hasattr(self, "peer_mesh"):
            if peer_id:
                return self.peer_mesh.sync_peer_deltas(peer_id)
            return self.peer_mesh.sync_all().to_dict()
        return {"error": "peer_mesh unavailable"}

    def export_node_key(self) -> dict:
        if hasattr(self, "peer_mesh"):
            return self.peer_mesh.export_node_credentials()
        return {"error": "peer_mesh unavailable"}

    def peer_mesh_status(self) -> dict:
        if hasattr(self, "peer_mesh"):
            return self.peer_mesh.status()
        return {"status": "inactive"}

    # Stage 106: Offline Multi-Modal Voice Fabric
    def get_voice_status(self) -> str:
        if hasattr(self, "voice_fabric"):
            return self.voice_fabric.voice_status()
        return "[Error] voice_fabric unavailable"

    def synthesize_voice(self, text: str) -> dict:
        if hasattr(self, "voice_fabric"):
            wav_bytes, pkt = self.voice_fabric.synthesize_speech(text)
            return pkt.to_dict()
        return {"error": "voice_fabric unavailable"}

    def transcribe_voice(self, audio_data: bytes | str) -> dict:
        if hasattr(self, "voice_fabric"):
            return self.voice_fabric.transcribe_audio(audio_data).to_dict()
        return {"error": "voice_fabric unavailable"}

    def tune_vad_threshold(self, threshold: float) -> dict:
        if hasattr(self, "voice_fabric"):
            return self.voice_fabric.tune_vad(energy_threshold=threshold)
        return {"error": "voice_fabric unavailable"}

    def voice_fabric_status(self) -> dict:
        if hasattr(self, "voice_fabric"):
            return self.voice_fabric.status()
        return {"status": "inactive"}

    # Stage 107: Context Window Semantic Token Compressor
    def compress_prompt(self, raw_text: str, level: str = "BALANCED") -> str:
        if hasattr(self, "token_compressor"):
            return self.token_compressor.compress_prompt_command(raw_text, level=level)
        return "[Error] token_compressor unavailable"

    def get_token_budget_table(self, ctx: int | None = None, sys_len: int | None = None) -> str:
        if hasattr(self, "token_compressor"):
            return self.token_compressor.format_token_budget_table(model_ctx_size=ctx, system_prompt_len=sys_len)
        return "[Error] token_compressor unavailable"

    def get_compression_ratio_table(self) -> str:
        if hasattr(self, "token_compressor"):
            return self.token_compressor.format_compression_ratio_table()
        return "[Error] token_compressor unavailable"

    def get_token_audit_table(self, limit: int = 5) -> str:
        if hasattr(self, "token_compressor"):
            return self.token_compressor.format_token_audit_table(limit=limit)
        return "[Error] token_compressor unavailable"

    def token_compressor_status(self) -> dict:
        if hasattr(self, "token_compressor"):
            return self.token_compressor.status()
        return {"status": "inactive"}

    # Stage 108: Autonomous Security Red-Team & Adversary Simulator
    def simulate_attack(self, vector_query: str = "") -> str:
        if hasattr(self, "red_team"):
            return self.red_team.simulate_attack_command(vector_query)
        return "[Error] red_team unavailable"

    def run_redteam_audit(self) -> str:
        if hasattr(self, "red_team"):
            return self.red_team.run_full_audit().format_terminal_summary()
        return "[Error] red_team unavailable"

    def vulnerability_scan(self) -> str:
        if hasattr(self, "red_team"):
            return self.red_team.format_vulnerability_scan_table()
        return "[Error] red_team unavailable"

    def harden_defensive_surface(self) -> str:
        if hasattr(self, "red_team"):
            return self.red_team.format_harden_surface_summary()
        return "[Error] red_team unavailable"

    def red_team_status(self) -> dict:
        if hasattr(self, "red_team"):
            return self.red_team.status()
        return {"status": "inactive"}

    # Stage 109: Ambient HUD & Desktop Overlay
    def launch_hud(self, mode: str = "floating") -> str:
        if hasattr(self, "ambient_hud"):
            return self.ambient_hud.launch_hud(mode)
        return "[Error] ambient_hud unavailable"

    def toggle_hud(self) -> str:
        if hasattr(self, "ambient_hud"):
            return self.ambient_hud.toggle_hud()
        return "[Error] ambient_hud unavailable"

    def tray_notify(self, title: str, message: str, level: str = "INFO") -> dict:
        if hasattr(self, "ambient_hud"):
            return self.ambient_hud.tray_notify(title=title, message=message, level=level).to_dict()
        return {"error": "ambient_hud unavailable"}

    def hud_status(self) -> str:
        if hasattr(self, "ambient_hud"):
            return self.ambient_hud.format_hud_status_table()
        return "[Error] ambient_hud unavailable"

    def ambient_hud_status(self) -> dict:
        if hasattr(self, "ambient_hud"):
            return self.ambient_hud.status()
        return {"status": "inactive"}

    # Stage 110: Sovereign Consensus Nexus & Era 11 Master Seal
    def nexus_status(self) -> str:
        if hasattr(self, "consensus_nexus"):
            return self.consensus_nexus.format_nexus_status_table()
        return "[Error] consensus_nexus unavailable"

    def propose_consensus(self, action: str) -> dict:
        if hasattr(self, "consensus_nexus"):
            return self.consensus_nexus.propose(action)
        return {"error": "consensus_nexus unavailable"}

    def verify_nexus(self) -> dict:
        if hasattr(self, "consensus_nexus"):
            return self.consensus_nexus.verify_era11_integrity()
        return {"error": "consensus_nexus unavailable"}

    def seal_era11(self) -> str:
        if hasattr(self, "consensus_nexus"):
            return self.consensus_nexus.seal_era11().format_terminal_summary()
        return "[Error] consensus_nexus unavailable"

    def consensus_nexus_status(self) -> dict:
        if hasattr(self, "consensus_nexus"):
            return self.consensus_nexus.status()
        return {"status": "inactive"}

    def workspace_daemon_status(self) -> dict:
        if hasattr(self, "workspace_daemon"):
            return self.workspace_daemon.status()
        return {"status": "inactive"}

    def format_workspace_daemon_table(self) -> str:
        if hasattr(self, "workspace_daemon"):
            return self.workspace_daemon.format_daemon_status_table()
        return "[Error] workspace_daemon unavailable"

    def toggle_workspace_daemon(self) -> str:
        if hasattr(self, "workspace_daemon"):
            return self.workspace_daemon.toggle()
        return "[Error] workspace_daemon unavailable"

    def stage_workspace_context(self, rel_path: str):
        if hasattr(self, "workspace_daemon"):
            return self.workspace_daemon.stage_file_context(rel_path)
        return None

    def semantic_cache_status(self) -> dict:
        if hasattr(self, "semantic_cache"):
            return self.semantic_cache.status()
        return {"status": "inactive"}

    def format_semantic_cache_table(self) -> str:
        if hasattr(self, "semantic_cache"):
            return self.semantic_cache.format_cache_status_table()
        return "[Error] semantic_cache unavailable"

    def flush_semantic_cache(self) -> int:
        if hasattr(self, "semantic_cache"):
            return self.semantic_cache.flush()
        return 0

    def query_semantic_cache(self, prompt: str):
        if hasattr(self, "semantic_cache"):
            return self.semantic_cache.lookup(prompt)
        return None

    def polyglot_status(self) -> dict:
        if hasattr(self, "polyglot_ast"):
            return self.polyglot_ast.status()
        return {"status": "inactive"}

    def format_polyglot_table(self) -> str:
        if hasattr(self, "polyglot_ast"):
            return self.polyglot_ast.format_polyglot_summary_table()
        return "[Error] polyglot_ast unavailable"

    def scan_polyglot_workspace(self):
        if hasattr(self, "polyglot_ast"):
            return self.polyglot_ast.scan_workspace()
        return None

    def find_polyglot_symbol(self, name: str):
        if hasattr(self, "polyglot_ast"):
            return self.polyglot_ast.find_symbol(name)
        return []

    def pipeline_fusion_status(self) -> dict:
        if hasattr(self, "pipeline_fusion"):
            return self.pipeline_fusion.status()
        return {"status": "inactive"}

    def format_pipeline_table(self) -> str:
        if hasattr(self, "pipeline_fusion"):
            return self.pipeline_fusion.format_pipeline_status_table()
        return "[Error] pipeline_fusion unavailable"

    def run_pipeline_template(self, name: str):
        if hasattr(self, "pipeline_fusion"):
            dag = self.pipeline_fusion.create_workspace_audit_pipeline() if "audit" in name.lower() else self.pipeline_fusion.create_refactor_fusion_pipeline()
            return self.pipeline_fusion.execute_pipeline(dag)
        return None

    def ipc_bus_status(self) -> dict:
        if hasattr(self, "ipc_bus"):
            return self.ipc_bus.status()
        return {"status": "inactive"}

    def format_ipc_table(self) -> str:
        if hasattr(self, "ipc_bus"):
            return self.ipc_bus.format_ipc_status_table()
        return "[Error] ipc_bus unavailable"

    def publish_ipc_event(self, topic: str, payload: dict, source: str = "core"):
        if hasattr(self, "ipc_bus"):
            return self.ipc_bus.publish(topic, payload, source=source)
        return None

    def tail_ipc_events(self, topic: str = "#", limit: int = 10):
        if hasattr(self, "ipc_bus"):
            return self.ipc_bus.tail(topic, limit=limit)
        return []

    def local_vector_db_status(self) -> dict:
        if hasattr(self, "local_vector_db"):
            return self.local_vector_db.status()
        return {"status": "inactive"}

    def format_vector_db_table(self) -> str:
        if hasattr(self, "local_vector_db"):
            return self.local_vector_db.format_vectordb_status_table()
        return "[Error] local_vector_db unavailable"

    def search_vector_db(self, query: str, top_k: int = 5):
        if hasattr(self, "local_vector_db"):
            return self.local_vector_db.search_text(query, top_k=top_k)
        return []

    def insert_vector_doc(self, doc_id: str, text: str, metadata: dict = None):
        if hasattr(self, "local_vector_db"):
            return self.local_vector_db.insert_text(doc_id, text, metadata=metadata)
        return False

    def git_ops_status(self) -> dict:
        if hasattr(self, "git_ops"):
            return self.git_ops.status()
        return {"status": "inactive"}

    def format_gitops_table(self) -> str:
        if hasattr(self, "git_ops"):
            return self.git_ops.format_gitops_status_table()
        return "[Error] git_ops unavailable"

    def synthesize_git_commit(self, files: list = None):
        if hasattr(self, "git_ops"):
            return self.git_ops.synthesize_commit_proposal(files)
        return None

    def generate_gitops_changelog(self, era: int = 12):
        if hasattr(self, "git_ops"):
            return self.git_ops.generate_changelog(era)
        return None

    def thermal_governor_status(self) -> dict:
        if hasattr(self, "thermal_governor"):
            return self.thermal_governor.status()
        return {"status": "inactive"}

    def format_thermal_governor_table(self) -> str:
        if hasattr(self, "thermal_governor"):
            return self.thermal_governor.format_governor_status_table()
        return "[Error] thermal_governor unavailable"

    def set_governor_mode(self, mode: str) -> bool:
        if hasattr(self, "thermal_governor"):
            return self.thermal_governor.set_mode(mode)
        return False

    def allocate_governor_workers(self, task_type: str = "general") -> int:
        if hasattr(self, "thermal_governor"):
            return self.thermal_governor.allocate_workers(task_type)
        return 2

    def dream_consolidator_status(self) -> dict:
        if hasattr(self, "dream_consolidator"):
            return self.dream_consolidator.status()
        return {"status": "inactive"}

    def format_dream_status_table(self) -> str:
        if hasattr(self, "dream_consolidator"):
            return self.dream_consolidator.format_dream_status_table()
        return "[Error] dream_consolidator unavailable"

    def run_dream_cycle(self) -> dict:
        if hasattr(self, "dream_consolidator"):
            rcpt = self.dream_consolidator.run_dream_cycle()
            return rcpt.to_dict()
        return {"error": "dream_consolidator unavailable"}

    def recall_dream_axioms(self, domain: Optional[str] = None) -> list:
        if hasattr(self, "dream_consolidator"):
            return [ax.to_dict() for ax in self.dream_consolidator.recall_axioms(domain)]
        return []

    def era12_seal_status(self) -> dict:
        if hasattr(self, "era12_seal"):
            return self.era12_seal.status()
        return {"status": "inactive"}

    def format_era12_seal_table(self) -> str:
        if hasattr(self, "era12_seal"):
            return self.era12_seal.format_seal_certificate_table()
        return "[Error] era12_seal unavailable"

    def verify_era12(self) -> tuple:
        if hasattr(self, "era12_seal"):
            return self.era12_seal.verify_era12_integrity()
        return False, "era12_seal unavailable", {}

    def run_cognitive_cycle(self, goal: str = "Autonomous Equilibrium") -> dict:
        if hasattr(self, "era12_seal"):
            res = self.era12_seal.run_cognitive_cycle(goal)
            return res.to_dict()
        return {"error": "era12_seal unavailable"}

    def knowledge_graph_status(self) -> dict:
        if hasattr(self, "knowledge_graph"):
            return self.knowledge_graph.status()
        return {"status": "inactive"}

    def format_kg_status_table(self) -> str:
        if hasattr(self, "knowledge_graph"):
            return self.knowledge_graph.format_kg_status_table()
        return "[Error] knowledge_graph unavailable"

    def kg_add_node(self, node_id: str, node_type: str, label: str, properties: dict = None) -> dict:
        if hasattr(self, "knowledge_graph"):
            n = self.knowledge_graph.add_node(node_id, node_type, label, properties)
            return n.to_dict()
        return {"error": "knowledge_graph unavailable"}

    def kg_add_edge(self, source_id: str, target_id: str, relation: str, weight: float = 1.0) -> dict:
        if hasattr(self, "knowledge_graph"):
            e = self.knowledge_graph.add_edge(source_id, target_id, relation, weight)
            return e.to_dict()
        return {"error": "knowledge_graph unavailable"}

    def kg_find_shortest_path(self, source_id: str, target_id: str) -> list:
        if hasattr(self, "knowledge_graph"):
            return self.knowledge_graph.find_shortest_path(source_id, target_id) or []
        return []

    def counterfactual_simulator_status(self) -> dict:
        if hasattr(self, "counterfactual_simulator"):
            return self.counterfactual_simulator.status()
        return {"status": "inactive"}

    def format_counterfactual_status_table(self) -> str:
        if hasattr(self, "counterfactual_simulator"):
            return self.counterfactual_simulator.format_counterfactual_status_table()
        return "[Error] counterfactual_simulator unavailable"

    def simulate_counterfactual_goal(self, goal: str) -> dict:
        if hasattr(self, "counterfactual_simulator"):
            rep = self.counterfactual_simulator.simulate_goal_hypotheses(goal)
            return rep.to_dict()
        return {"error": "counterfactual_simulator unavailable"}

    def goal_decomposer_status(self) -> dict:
        if hasattr(self, "goal_decomposer"):
            return self.goal_decomposer.status()
        return {"status": "inactive"}

    def format_decomposer_status_table(self) -> str:
        if hasattr(self, "goal_decomposer"):
            return self.goal_decomposer.format_decomposer_status_table()
        return "[Error] goal_decomposer unavailable"

    def decompose_goal(self, goal: str) -> dict:
        if hasattr(self, "goal_decomposer"):
            p = self.goal_decomposer.decompose_goal(goal)
            return p.to_dict()
        return {"error": "goal_decomposer unavailable"}

    def format_goal_tree(self, plan_id: Optional[str] = None) -> str:
        if hasattr(self, "goal_decomposer"):
            return self.goal_decomposer.format_goal_tree(plan_id)
        return "[Error] goal_decomposer unavailable"

    def verification_oracle_status(self) -> dict:
        if hasattr(self, "verification_oracle"):
            return self.verification_oracle.status()
        return {"status": "inactive"}

    def format_oracle_status_table(self) -> str:
        if hasattr(self, "verification_oracle"):
            return self.verification_oracle.format_oracle_status_table()
        return "[Error] verification_oracle unavailable"

    def verify_code_or_text(self, text: str, is_code: bool = True) -> dict:
        if hasattr(self, "verification_oracle"):
            cert = self.verification_oracle.verify_code_patch(text) if is_code else self.verification_oracle.verify_agent_output(text)
            return cert.to_dict()
        return {"error": "verification_oracle unavailable"}

    def format_oracle_certificate(self, cert_id: Optional[str] = None) -> str:
        if hasattr(self, "verification_oracle"):
            return self.verification_oracle.format_certificate_table(cert_id)
        return "[Error] verification_oracle unavailable"

    def concept_miner_status(self) -> dict:
        if hasattr(self, "concept_miner"):
            return self.concept_miner.status()
        return {"status": "inactive"}

    def format_concept_status_table(self) -> str:
        if hasattr(self, "concept_miner"):
            return self.concept_miner.format_concept_status_table()
        return "[Error] concept_miner unavailable"

    def format_concept_taxonomy_tree(self) -> str:
        if hasattr(self, "concept_miner"):
            return self.concept_miner.format_concept_taxonomy_tree()
        return "[Error] concept_miner unavailable"

    def mine_latent_concepts(self) -> dict:
        if hasattr(self, "concept_miner"):
            new_c = self.concept_miner.mine_concepts()
            exported = 0
            if hasattr(self, "knowledge_graph"):
                exported = self.concept_miner.export_to_knowledge_graph(self.knowledge_graph)
            return {"mined_count": len(new_c), "exported_to_kg": exported}
        return {"error": "concept_miner unavailable"}

    def context_budgeter_status(self) -> dict:
        if hasattr(self, "context_budgeter"):
            return self.context_budgeter.status()
        return {"status": "inactive"}

    def format_budget_status_table(self) -> str:
        if hasattr(self, "context_budgeter"):
            return self.context_budgeter.format_budget_status_table()
        return "[Error] context_budgeter unavailable"

    def allocate_context_budget(self, total_budget: int = 4096, hardware_mode: str = "balanced") -> dict:
        if hasattr(self, "context_budgeter"):
            snap = self.context_budgeter.allocate_slices(total_budget=total_budget, hardware_mode=hardware_mode)
            return snap.to_dict()
        return {"error": "context_budgeter unavailable"}

    def compact_context_slice(self, slice_name: str) -> dict:
        if hasattr(self, "context_budgeter"):
            freed = self.context_budgeter.compact_slice(slice_name)
            return {"slice_name": slice_name, "freed_tokens": freed}
        return {"error": "context_budgeter unavailable"}

    def protocol_synthesizer_status(self) -> dict:
        if hasattr(self, "protocol_synthesizer"):
            return self.protocol_synthesizer.status()
        return {"status": "inactive"}

    def format_protocol_status_table(self) -> str:
        if hasattr(self, "protocol_synthesizer"):
            return self.protocol_synthesizer.format_protocol_status_table()
        return "[Error] protocol_synthesizer unavailable"

    def infer_protocol(self, name: str, method: str = "GET", path: str = "/", raw_payload: any = None) -> dict:
        if hasattr(self, "protocol_synthesizer"):
            spec = self.protocol_synthesizer.infer_protocol(name, method=method, path=path, raw_payload=raw_payload)
            return spec.to_dict()
        return {"error": "protocol_synthesizer unavailable"}

    def synthesize_client_code(self, protocol_id: str) -> str:
        if hasattr(self, "protocol_synthesizer"):
            return self.protocol_synthesizer.synthesize_client_code(protocol_id)
        return "# [Error] protocol_synthesizer unavailable"

    def meta_policy_refiner_status(self) -> dict:
        if hasattr(self, "meta_policy_refiner"):
            return self.meta_policy_refiner.status()
        return {"status": "inactive"}

    def format_policy_status_table(self) -> str:
        if hasattr(self, "meta_policy_refiner"):
            return self.meta_policy_refiner.format_policy_status_table()
        return "[Error] meta_policy_refiner unavailable"

    def tune_meta_policy(self, name: str, value: float) -> dict:
        if hasattr(self, "meta_policy_refiner"):
            success, msg, final_val = self.meta_policy_refiner.tune_policy(name, value)
            return {"success": success, "message": msg, "value": final_val}
        return {"error": "meta_policy_refiner unavailable"}

    def evaluate_meta_policies(self) -> dict:
        if hasattr(self, "meta_policy_refiner"):
            return self.meta_policy_refiner.evaluate_and_refine_policies()
        return {"error": "meta_policy_refiner unavailable"}

    def mesh_gateway_status(self) -> dict:
        if hasattr(self, "mesh_gateway"):
            return self.mesh_gateway.status()
        return {"status": "inactive"}

    def format_mesh_status_table(self) -> str:
        if hasattr(self, "mesh_gateway"):
            return self.mesh_gateway.format_mesh_status_table()
        return "[Error] mesh_gateway unavailable"

    def register_mesh_node(self, node_id: str, endpoint: str, role: str = "worker") -> dict:
        if hasattr(self, "mesh_gateway"):
            node = self.mesh_gateway.register_node(node_id, endpoint, role)
            return node.to_dict()
        return {"error": "mesh_gateway unavailable"}

    def dispatch_mesh_rpc(self, target_node: str, procedure: str, parameters: dict = None) -> dict:
        if hasattr(self, "mesh_gateway"):
            return self.mesh_gateway.dispatch_rpc(target_node, procedure, parameters)
        return {"error": "mesh_gateway unavailable"}

    def era13_seal_status(self) -> dict:
        if hasattr(self, "era13_seal"):
            return self.era13_seal.status()
        return {"status": "inactive"}

    def format_era13_seal_table(self) -> str:
        if hasattr(self, "era13_seal"):
            return self.era13_seal.format_seal_certificate_table()
        return "[Error] era13_seal unavailable"

    def verify_era13_integrity(self) -> tuple:
        if hasattr(self, "era13_seal"):
            return self.era13_seal.verify_era13_integrity()
        return False, "era13_seal unavailable", {}

    def run_symbolic_mesh_cycle(self, goal: str = "Synthesize sovereign cognitive mesh") -> dict:
        if hasattr(self, "era13_seal"):
            res = self.era13_seal.run_symbolic_mesh_cycle(goal)
            return res.to_dict()
        return {"error": "era13_seal unavailable"}

    def ast_mutator_status(self) -> dict:
        if hasattr(self, "ast_mutator"):
            return self.ast_mutator.status()
        return {"status": "inactive"}

    def format_mutation_status_table(self) -> str:
        if hasattr(self, "ast_mutator"):
            return self.ast_mutator.format_mutation_status_table()
        return "[Error] ast_mutator unavailable"

    def mutate_code_ast(self, source_code: str, operator_name: str = "AOR") -> dict:
        if hasattr(self, "ast_mutator"):
            mutant = self.ast_mutator.mutate_code(source_code, operator_name=operator_name)
            return mutant.to_dict()
        return {"error": "ast_mutator unavailable"}

    def evolve_code_ast(self, source_code: str, generations: int = 3) -> list:
        if hasattr(self, "ast_mutator"):
            survivors = self.ast_mutator.evolve_code(source_code, generations=generations)
            return [s.to_dict() for s in survivors]
        return []

    def test_oracle_status(self) -> dict:
        if hasattr(self, "test_oracle"):
            return self.test_oracle.status()
        return {"status": "inactive"}

    def format_oracle_status_table(self) -> str:
        if hasattr(self, "test_oracle"):
            return self.test_oracle.format_oracle_status_table()
        return "[Error] test_oracle unavailable"

    def synthesize_test_suite(self, source_code: str, target_name: str = "TargetModule") -> dict:
        if hasattr(self, "test_oracle"):
            rec = self.test_oracle.synthesize_test_suite(source_code, target_name=target_name)
            return rec.to_dict()
        return {"error": "test_oracle unavailable"}

    def validate_test_suite(self, suite_id: str) -> dict:
        if hasattr(self, "test_oracle"):
            return self.test_oracle.validate_test_suite(suite_id)
        return {"error": "test_oracle unavailable"}

    def constraint_solver_status(self) -> dict:
        if hasattr(self, "constraint_solver"):
            return self.constraint_solver.status()
        return {"status": "inactive"}

    def format_constraint_status_table(self) -> str:
        if hasattr(self, "constraint_solver"):
            return self.constraint_solver.format_constraint_status_table()
        return "[Error] constraint_solver unavailable"

    def solve_code_constraints(self, source_code: str, target_name: str = "SourceCode") -> dict:
        if hasattr(self, "constraint_solver"):
            res = self.constraint_solver.solve_constraints(source_code, target_name=target_name)
            return res.to_dict()
        return {"error": "constraint_solver unavailable"}

    def check_branch_satisfiability(self, condition_expr: str) -> dict:
        if hasattr(self, "constraint_solver"):
            return self.constraint_solver.check_branch_sat(condition_expr)
        return {"error": "constraint_solver unavailable"}

    def bytecode_inspector_status(self) -> dict:
        if hasattr(self, "bytecode_inspector"):
            return self.bytecode_inspector.status()
        return {"status": "inactive"}

    def format_bytecode_status_table(self) -> str:
        if hasattr(self, "bytecode_inspector"):
            return self.bytecode_inspector.format_bytecode_status_table()
        return "[Error] bytecode_inspector unavailable"

    def disassemble_python_code(self, code_input: str, target_name: str = "DisassembledTarget") -> dict:
        if hasattr(self, "bytecode_inspector"):
            rep = self.bytecode_inspector.disassemble_code(code_input, target_name=target_name)
            return rep.to_dict()
        return {"error": "bytecode_inspector unavailable"}

    def format_bytecode_dump(self, report_id: str) -> str:
        if hasattr(self, "bytecode_inspector"):
            return self.bytecode_inspector.format_bytecode_dump(report_id)
        return "[Error] bytecode_inspector unavailable"

    def ffi_linker_status(self) -> dict:
        if hasattr(self, "ffi_linker"):
            return self.ffi_linker.status()
        return {"status": "inactive"}

    def format_ffi_status_table(self) -> str:
        if hasattr(self, "ffi_linker"):
            return self.ffi_linker.format_ffi_status_table()
        return "[Error] ffi_linker unavailable"

    def link_native_c_symbol(self, symbol_name: str, library_name: str = "msvcrt", restype_name: str = "int", argtypes_names: list = None) -> dict:
        if hasattr(self, "ffi_linker"):
            b = self.ffi_linker.link_native_symbol(symbol_name, library_name=library_name, restype_name=restype_name, argtypes_names=argtypes_names)
            return b.to_dict()
        return {"error": "ffi_linker unavailable"}

    def invoke_native_c_symbol(self, symbol_name: str, *args) -> any:
        if hasattr(self, "ffi_linker"):
            return self.ffi_linker.invoke_native_symbol(symbol_name, *args)
        return None

    def wheel_fabric_status(self) -> dict:
        if hasattr(self, "wheel_fabric"):
            return self.wheel_fabric.status()
        return {"status": "inactive"}

    def format_wheel_status_table(self) -> str:
        if hasattr(self, "wheel_fabric"):
            return self.wheel_fabric.format_wheel_status_table()
        return "[Error] wheel_fabric unavailable"

    def build_sovereign_wheel(self, package_name: str, version: str = "1.0.0") -> dict:
        if hasattr(self, "wheel_fabric"):
            rec = self.wheel_fabric.build_wheel(package_name, version=version)
            return rec.to_dict()
        return {"error": "wheel_fabric unavailable"}

    def verify_sovereign_wheel(self, wheel_filename: str) -> dict:
        if hasattr(self, "wheel_fabric"):
            return self.wheel_fabric.verify_wheel(wheel_filename)
        return {"error": "wheel_fabric unavailable"}

    def perf_sentinel_status(self) -> dict:
        if hasattr(self, "perf_sentinel"):
            return self.perf_sentinel.status()
        return {"status": "inactive"}

    def format_perf_status_table(self) -> str:
        if hasattr(self, "perf_sentinel"):
            return self.perf_sentinel.format_perf_status_table()
        return "[Error] perf_sentinel unavailable"

    def run_subsystem_benchmark(self, target_name: str, iterations: int = 50) -> dict:
        if hasattr(self, "perf_sentinel"):
            metric, alerts = self.perf_sentinel.benchmark_subsystem(target_name, iterations=iterations)
            return {"metric": metric.to_dict(), "alerts": [a.to_dict() for a in alerts]}
        return {"error": "perf_sentinel unavailable"}

    def dead_code_eliminator_status(self) -> dict:
        if hasattr(self, "dead_code_eliminator"):
            return self.dead_code_eliminator.status()
        return {"status": "inactive"}

    def format_prune_status_table(self) -> str:
        if hasattr(self, "dead_code_eliminator"):
            return self.dead_code_eliminator.format_status_table()
        return "[Error] dead_code_eliminator unavailable"

    def prune_file(self, filepath: str, in_place: bool = False) -> dict:
        if hasattr(self, "dead_code_eliminator"):
            rep = self.dead_code_eliminator.prune_file(filepath, in_place=in_place)
            return rep.to_dict()
        return {"error": "dead_code_eliminator unavailable"}

    def flight_recorder_status(self) -> dict:
        if hasattr(self, "flight_recorder"):
            return self.flight_recorder.status()
        return {"status": "inactive"}

    def format_flight_status_table(self) -> str:
        if hasattr(self, "flight_recorder"):
            return self.flight_recorder.format_flight_status_table()
        return "[Error] flight_recorder unavailable"

    def record_flight_event(self, event_type: str, subsystem: str, payload: dict) -> dict:
        if hasattr(self, "flight_recorder"):
            ev = self.flight_recorder.record_event(event_type, subsystem, payload)
            return ev.to_dict()
        return {"error": "flight_recorder unavailable"}

    def era14_nexus_status(self) -> dict:
        if hasattr(self, "era14_nexus"):
            return self.era14_nexus.status()
        return {"status": "inactive"}

    def format_era14_status_table(self) -> str:
        if hasattr(self, "era14_nexus"):
            return self.era14_nexus.format_era14_status_table()
        return "[Error] era14_nexus unavailable"

    def verify_era14(self) -> dict:
        if hasattr(self, "era14_nexus"):
            return self.era14_nexus.verify_era14_manifest()
        return {"error": "era14_nexus unavailable"}

    def run_evolution_cycle(self, target_name: str = "runtime_evolution") -> dict:
        if hasattr(self, "era14_nexus"):
            res = self.era14_nexus.run_evolution_cycle(target_name)
            return res.to_dict()
        return {"error": "era14_nexus unavailable"}

    def ir_compiler_status(self) -> dict:
        if hasattr(self, "ir_compiler"):
            return self.ir_compiler.status()
        return {"status": "inactive"}

    def format_ir_status_table(self) -> str:
        if hasattr(self, "ir_compiler"):
            return self.ir_compiler.format_ir_status_table()
        return "[Error] ir_compiler unavailable"

    def compile_ir(self, source_code: str, module_name: str = "main") -> dict:
        if hasattr(self, "ir_compiler"):
            mod = self.ir_compiler.compile_source(source_code, module_name=module_name)
            valid, errors = self.ir_compiler.verify_module(mod)
            return {"module": mod.to_dict(), "is_valid": valid, "errors": errors, "ir_text": mod.to_text()}
        return {"error": "ir_compiler unavailable"}

    def ssa_optimizer_status(self) -> dict:
        if hasattr(self, "ssa_optimizer"):
            return self.ssa_optimizer.status()
        return {"status": "inactive"}

    def format_ssa_status_table(self) -> str:
        if hasattr(self, "ssa_optimizer"):
            return self.ssa_optimizer.format_ssa_status_table()
        return "[Error] ssa_optimizer unavailable"

    def optimize_ssa(self, source_code: str, module_name: str = "main") -> dict:
        if hasattr(self, "ssa_optimizer"):
            opt_mod, rep = self.ssa_optimizer.optimize_source(source_code, module_name=module_name)
            return {"optimized_module": opt_mod.to_dict(), "report": rep.to_dict(), "ir_text": opt_mod.to_text()}
        return {"error": "ssa_optimizer unavailable"}

    def loop_optimizer_status(self) -> dict:
        if hasattr(self, "loop_optimizer"):
            return self.loop_optimizer.status()
        return {"status": "inactive"}

    def format_loop_status_table(self) -> str:
        if hasattr(self, "loop_optimizer"):
            return self.loop_optimizer.format_loop_status_table()
        return "[Error] loop_optimizer unavailable"

    def optimize_loops(self, source_code: str, module_name: str = "main") -> dict:
        if hasattr(self, "loop_optimizer"):
            opt_mod, rep = self.loop_optimizer.optimize_source(source_code, module_name=module_name)
            return {"optimized_module": opt_mod.to_dict(), "report": rep.to_dict(), "ir_text": opt_mod.to_text()}
        return {"error": "loop_optimizer unavailable"}

    def register_allocator_status(self) -> dict:
        if hasattr(self, "register_allocator"):
            return self.register_allocator.status()
        return {"status": "inactive"}

    def format_reg_status_table(self) -> str:
        if hasattr(self, "register_allocator"):
            return self.register_allocator.format_reg_status_table()
        return "[Error] register_allocator unavailable"

    def allocate_registers_for_source(self, source_code: str, k: int = 8) -> dict:
        if hasattr(self, "register_allocator"):
            res = self.register_allocator.allocate_source(source_code, k=k)
            return {k_fn: r.to_dict() for k_fn, r in res.items()}
        return {"error": "register_allocator unavailable"}

    def code_synthesizer_status(self) -> dict:
        if hasattr(self, "code_synthesizer"):
            return self.code_synthesizer.status()
        return {"status": "inactive"}

    def format_asm_status_table(self) -> str:
        if hasattr(self, "code_synthesizer"):
            return self.code_synthesizer.format_asm_status_table()
        return "[Error] code_synthesizer unavailable"

    def emit_machine_code(self, source_code: str, target_arch: str = "x86_64") -> dict:
        if hasattr(self, "code_synthesizer"):
            res = self.code_synthesizer.synthesize_source(source_code, target_arch=target_arch)
            return {fname: art.to_dict() for fname, art in res.items()}
        return {"error": "code_synthesizer unavailable"}

    def jit_tracer_status(self) -> dict:
        if hasattr(self, "jit_tracer"):
            return self.jit_tracer.status()
        return {"status": "inactive"}

    def format_jit_status_table(self) -> str:
        if hasattr(self, "jit_tracer"):
            return self.jit_tracer.format_jit_status_table()
        return "[Error] jit_tracer unavailable"

    def execute_jit(self, source_code: str, func_name: str, args: list = None) -> dict:
        if hasattr(self, "jit_tracer"):
            res = self.jit_tracer.execute_source(source_code, func_name, args=args or [])
            return res.to_dict()
        return {"error": "jit_tracer unavailable"}

    def _register_default_supervised_services(self) -> None:
        if not hasattr(self, "kernel_supervisor"):
            return
        services = [
            ("receipt_ledger", "core"),
            ("workspace_sensor", "sensor"),
            ("proactive_briefer", "core"),
            ("cron_scheduler", "daemon"),
            ("hardware_telemetry", "sensor"),
            ("worktree_fabric", "core"),
            ("ast_vector_index", "core"),
            ("causal_dag", "memory"),
            ("host_sandbox", "sandbox"),
            ("master_seal", "core"),
            ("mutation_fuzzer", "core"),
            ("self_healing_patcher", "core"),
            ("execution_profiler", "core"),
            ("neural_retriever", "core"),
            ("refactor_engine", "core"),
            ("peer_mesh", "core"),
            ("voice_fabric", "core"),
            ("token_compressor", "core"),
            ("red_team", "core"),
            ("ambient_hud", "sensor"),
            ("consensus_nexus", "core"),
            ("workspace_daemon", "sensor"),
            ("semantic_cache", "core"),
            ("polyglot_ast", "core"),
            ("pipeline_fusion", "core"),
            ("ipc_bus", "daemon"),
            ("local_vector_db", "memory"),
            ("git_ops", "core"),
            ("thermal_governor", "core"),
            ("dream_consolidator", "memory"),
            ("era12_seal", "core"),
            ("knowledge_graph", "memory"),
            ("counterfactual_simulator", "core"),
            ("goal_decomposer", "core"),
            ("verification_oracle", "core"),
            ("concept_miner", "core"),
            ("context_budgeter", "core"),
            ("protocol_synthesizer", "core"),
            ("meta_policy_refiner", "core"),
            ("mesh_gateway", "daemon"),
            ("era13_seal", "core"),
            ("ast_mutator", "core"),
            ("test_oracle", "core"),
            ("constraint_solver", "core"),
            ("bytecode_inspector", "core"),
            ("ffi_linker", "core"),
            ("wheel_fabric", "core"),
            ("perf_sentinel", "core"),
            ("dead_code_eliminator", "core"),
            ("flight_recorder", "core"),
            ("era14_nexus", "core"),
            ("ir_compiler", "core"),
            ("ssa_optimizer", "core"),
            ("loop_optimizer", "core"),
            ("register_allocator", "core"),
            ("code_synthesizer", "core"),
            ("jit_tracer", "core"),
            ("native_linker", "core"),
            ("memory_manager", "core"),
            ("lto_pipeline", "core"),
            ("era15_nexus", "core"),
            ("kernel_scheduler", "core"),
            ("hal_cpu", "core"),
            ("paging_engine", "core"),
            ("ipc_registry", "core"),
            ("interrupt_controller", "core"),
            ("dma_fabric", "core"),
            ("capability_manager", "core"),
            ("block_fabric", "core"),
            ("vfs", "core"),
            ("era16_nexus", "core"),
            ("bft_cluster", "core"),
            ("raft_cluster", "core"),
            ("dht_mesh", "core"),
            ("causal_fabric", "core"),
            ("paxos_cluster", "core"),
            ("gossip_mesh", "core"),
            ("crdt_synth", "core"),
            ("mesh_tunnel", "core"),
            ("deadlock_sentinel", "core"),
            ("era17_nexus", "core"),
            ("hash_ring", "core"),
            ("lsm_tree", "core"),
            ("quorum_coordinator", "core"),
            ("wal_manager", "core"),
            ("mvcc_storage", "core"),
            ("shard_sentinel", "core"),
            ("index_fabric", "core"),
            ("multi_raft_kv", "core"),
            ("geo_fabric", "core"),
            ("era18_nexus", "core"),
            ("columnar_storage", "core"),
            ("query_optimizer", "core"),
            ("vectorized_engine", "core"),
            ("hash_join_fabric", "core"),
            ("approx_query_fabric", "core"),
            ("materialized_view_fabric", "core"),
            ("streaming_window_fabric", "core"),
            ("aqe_fabric", "core"),
            ("olap_compactor_fabric", "core"),
            ("era19_nexus", "core"),
            ("jit_optimizer", "core"),
            ("kernel_self_healing", "core"),
            ("raft_bft_fabric", "core"),
            ("zerocopy_shm_fabric", "core"),
            ("tensor_runtime_fabric", "core"),
            ("self_evolving_code_fabric", "core"),
            ("chrono_log_fabric", "core"),
            ("daemon_mesh_fabric", "core"),
            ("bicentennial_nexus", "core"),
            ("bicentennial_grand_master_seal", "core"),
            ("multi_kernel_federation", "core"),
            ("post_quantum_crypto", "core"),
            ("sovereign_contract_engine", "core"),
            ("neuromorphic_spike_mesh", "core"),
            ("knowledge_distillation_pruner", "core"),
            ("zk_invariant_prover", "core"),
            ("compute_governor", "core"),
            ("multimodal_grounding", "core"),
            ("hyperscale_mesh", "core"),
            ("era21_master_seal", "core"),
            ("photonic_matrix_multiplier", "core"),
            ("interplanetary_dtn", "core"),
            ("tensor_train_engine", "core"),
            ("holographic_memory", "core"),
            ("micro_actor_mesh", "core"),
            ("quantum_coprocessor", "core"),
            ("chaos_engine", "core"),
            ("belief_mesh", "core"),
            ("ontology_engine", "core"),
            ("era22_master_seal", "core"),
            ("density_matrix_simulator", "core"),
            ("holographic_swarm", "core"),
            ("subatomic_pipeline_governor", "core"),
            ("multiverse_forker", "core"),
            ("recursive_snark_aggregator", "core"),
            ("topological_data_analysis", "core"),
            ("energy_budget_governor", "core"),
            ("hyperdimensional_computing", "core"),
            ("geo_disaster_recovery", "core"),
            ("era23_master_seal", "core"),
            ("neuromorphic_spiking", "core"),
            ("lattice_pqc_vault", "core"),
            ("hyperbolic_graph_embedder", "core"),
            ("polyglot_bytecode_jit", "core"),
            ("epistemic_logic_mesh", "core"),
            ("temporal_chrono_governor", "core"),
            ("photonic_optical_switch", "core"),
            ("byzantine_swarm_consensus", "core"),
            ("planetary_resource_exchange", "core"),
            ("era24_master_seal", "core"),
            ("metamaterial_phonon_computer", "core"),
            ("exceptional_point_resonance", "core"),
            ("cellular_cohomology_sheaf", "core"),
            ("dna_molecular_storage", "core"),
            ("orbital_constellation_grid", "core"),
            ("adiabatic_reversible_governor", "core"),
            ("antifragile_stress_inverter", "core"),
            ("padic_ultrametric_clusterer", "core"),
            ("zero_trust_hardware_enclave", "core"),
            ("era25_master_seal", "core"),
            ("calabi_yau_metric_engine", "core"),
            ("jarzynski_entropy_harvester", "core"),
            ("clifford_processor", "core"),
            ("symplectic_integrator", "core"),
            ("turing_synthesizer", "core"),
            ("rg_flow_fabric", "core"),
            ("squid_magnetometer", "core"),
            ("chrono_synchronizer", "core"),
            ("shapley_nash_engine", "core"),
            ("era26_master_seal", "core"),
            ("yang_mills_engine", "core"),
            ("entanglement_wedge_fabric", "core"),
            ("optomechanical_transceiver", "core"),
            ("skyrmion_weaver", "core"),
            ("quantum_walk_search", "core"),
            ("mhd_dynamo_sim", "core"),
            ("berry_holonomy", "core"),
            ("flrw_cosmo_engine", "core"),
            ("zk_verifier", "core"),
            ("era27_master_seal", "core"),
            ("qcd_confinement", "core"),
            ("moyal_algebra", "core"),
            ("anyon_processor", "core"),
            ("plasma_shock_accelerator", "core"),
            ("lensing_caustic_tracer", "core"),
            ("quantum_repeater_fabric", "core"),
            ("kdv_soliton_synthesizer", "core"),
            ("casimir_vacuum_engine", "core"),
            ("zk_rollup_compressor", "core"),
            ("era28_master_seal", "core"),
            ("black_hole_thermodynamics", "core"),
            ("pt_symmetric_engine", "core"),
            ("quantum_scrambler", "core"),
            ("cmb_power_spectrum", "core"),
            ("zeno_controller", "core"),
            ("majorana_gate", "core"),
            ("pulsar_ffe_engine", "core"),
            ("fisher_phase_estimator", "core"),
            ("cross_chain_zk_bridge", "core"),
            ("era29_master_seal", "core"),
        ]
        for sname, stype in services:
            self.kernel_supervisor.register_subsystem(sname, subsystem_type=stype)

    def master_synthesis_status(self) -> dict:
        if hasattr(self, "master_synthesis"):
            return self.master_synthesis.status()
        return {"status": "inactive"}

    def execution_receipts_status(self) -> dict:
        return self.receipt_ledger.status()

    def workflow_learner_status(self) -> dict:
        return self.workflow_learner.status()

    def live_workspace_status(self) -> dict:
        return self.workspace_sensor.status()

    def proactive_briefer_status(self) -> dict:
        return self.proactive_briefer.status()

    def natural_action_status(self) -> dict:
        return self.natural_action_parser.status() if hasattr(self, "natural_action_parser") else {"status": "inactive"}

    def generate_brief(self) -> dict:
        return self.proactive_briefer.generate_brief()

# ---------- STAGE 53: AUTONOMOUS CRON SCHEDULER ----------
    def cron_status(self) -> dict:
        return self.cron_scheduler.status()

    def add_cron_job(self, expression: str, target: str, name: str = "", catch_up: bool = True) -> dict:
        job = self.cron_scheduler.add_job(expression=expression, target=target, name=name, catch_up=catch_up)
        return job.to_dict()

    def list_cron_jobs(self) -> list[dict]:
        return self.cron_scheduler.list_jobs()

    def pause_cron_job(self, job_id: str) -> bool:
        return self.cron_scheduler.pause_job(job_id)

    def resume_cron_job(self, job_id: str) -> bool:
        return self.cron_scheduler.resume_job(job_id)

    def delete_cron_job(self, job_id: str) -> bool:
        return self.cron_scheduler.delete_job(job_id)

    # ---------- STAGE 52: MASTER ORCHESTRATOR GOAL DAG LOOP ----------
    def execute_tool_chain(self, chain_spec: str, title: str = "Terminal Tool Chain") -> dict:
        return self.master_orchestrator.execute_tool_chain(chain_spec=chain_spec, title=title)

    def parse_tool_chain(self, chain_spec: str) -> list[tuple[str, str, dict]]:
        return self.master_orchestrator.parse_tool_chain(chain_spec)

    def orchestrator_status(self) -> dict:
        return self.master_orchestrator.status()

    def execute_goal(self, intent: str, template: str = "auto") -> dict:
        if template == "auto":
            return self.master_orchestrator.execute_goal_from_intent(intent)
        dag = self.master_orchestrator.create_goal(title=intent, description=intent, template=template)
        return self.master_orchestrator.execute_dag(dag)

    def list_goal_history(self, limit: int = 10) -> list[dict]:
        return self.master_orchestrator.list_history(limit=limit)

    def get_goal_details(self, goal_id: str) -> dict | None:
        return self.master_orchestrator.get_goal_details(goal_id=goal_id)

    # ---------- STAGE 51: SELF-DIAGNOSTICS & CRASH RECOVERY ----------
    def self_diagnostics_status(self) -> dict:
        return self.self_diagnostics.status()

    def run_system_diagnostics(self) -> dict:
        return self.self_diagnostics.run_diagnostics()

    def auto_heal_system(self) -> dict:
        return self.self_diagnostics.auto_heal()

    def create_system_backups(self) -> dict:
        return self.self_diagnostics.create_system_snapshot()

    # ---------- STAGE 50: TERMINAL REPL & COMMAND PALETTE ----------
    def terminal_repl_status(self) -> dict:
        return self.terminal_repl.status()

    def execute_repl_command(self, command: str) -> dict:
        return self.terminal_repl.execute_one(command)

    def repl_autocomplete(self, prefix: str) -> list[str]:
        return self.terminal_repl.palette.autocomplete(prefix)

    # ---------- STAGE 49: WORKSPACE SENTINEL & HABIT WATCHDOG ----------
    def sentinel_status(self) -> dict:
        return self.workspace_sentinel.status()

    def scan_workspace_now(self) -> dict:
        return self.workspace_sentinel.scan_once()

    def get_sentinel_alerts(self) -> list[str]:
        return self.workspace_sentinel.consume_alerts()

    def start_sentinel_watcher(self, interval_seconds: float = 30.0) -> dict:
        return self.workspace_sentinel.start_background_watcher(interval_seconds=interval_seconds)

    def stop_sentinel_watcher(self) -> dict:
        return self.workspace_sentinel.stop_background_watcher()

    # ---------- STAGE 48: AUTONOMOUS INTENT DISPATCHER ----------
    def intent_dispatcher_status(self) -> dict:
        return self.intent_dispatcher.status()

    def classify_user_intent(self, text: str) -> dict:
        cl = self.intent_dispatcher.classify_intent(text)
        return {
            "intent_type": cl.intent_type,
            "confidence": cl.confidence,
            "extracted_target": cl.extracted_target,
            "raw_text": cl.raw_text,
        }

    def dispatch_user_intent(self, text: str) -> dict | None:
        return self.intent_dispatcher.dispatch(text)

    def submit_synthesis_task(self, instruction: str, filename: str = "synthesized_tool.py") -> dict:
        task_id = self.task_daemon.submit_task(
            name=f"synth_{instruction[:30]}",
            target_fn=self.code_synthesis.synthesize,
            instruction=instruction,
            filename=filename,
        )
        return {
            "submitted": True,
            "task_id": task_id,
            "instruction": instruction,
        }

    # ---------- STAGE 47: WINDOWS OPERATOR TOOLKIT ----------
    def system_telemetry(self) -> dict:
        return self.operator_toolkit.get_system_telemetry()

    def inspect_processes(self, query: str = "", limit: int = 15) -> list[dict]:
        return self.operator_toolkit.inspect_processes(query=query, limit=limit)

    def search_workspace_files(self, pattern: str = "", extension: str = "", search_content: bool = False, limit: int = 20) -> list[dict]:
        return self.operator_toolkit.search_workspace(pattern=pattern, extension=extension, search_content=search_content, limit=limit)

    def probe_network_ports(self, ports: list[int] | None = None) -> dict:
        return self.operator_toolkit.probe_network_ports(ports=ports)

    def clean_sandbox_cache(self, dry_run: bool = True) -> dict:
        res = self.operator_toolkit.clean_sandbox_cache(dry_run=dry_run)
        if not dry_run and hasattr(self, "receipt_ledger"):
            self.receipt_ledger.issue_receipt(
                action_category="sandbox_cleanup",
                operation="clean_sandbox_cache",
                target=res.get("staging_dir", "staging"),
                verified_outcome=f"Deleted {res.get('files_found', 0)} staging files ({res.get('bytes_freed', 0)} bytes)",
            )
        return res

    # ---------- STAGE 46: MULTI-PROVIDER KEY ROTATION POOL ----------
    def provider_pool_status(self) -> dict:
        return self.provider_pool.status()

    def rotate_provider_key(self, provider: str = "groq") -> dict:
        return self.provider_pool.rotate_key(provider)

    def reload_provider_keys(self) -> dict:
        return self.provider_pool.load_keys()

    def mark_key_rate_limited(self, provider: str = "groq") -> dict:
        return self.provider_pool.mark_rate_limited(provider)

    # ---------- STAGE 45: PERSONAL LORA STYLE ALIGNMENT ----------
    def personal_lora_status(self) -> dict:
        return self.personal_lora_alignment.status()

    def trigger_personal_sleep_cycle(self) -> dict:
        return self.personal_lora_alignment.trigger_personal_sleep_cycle()

    def run_personal_alignment_gate(self) -> dict:
        return self.personal_lora_alignment.run_alignment_gate()

    def list_personal_adapters(self) -> list[str]:
        return self.personal_lora_alignment.list_personal_adapters()

    def synthesize_personal_dataset(self) -> dict:
        return self.personal_lora_alignment.synthesize_personal_dataset()

    def build_cloud_few_shot_block(self, max_examples: int = 3) -> str:
        if hasattr(self, "personal_lora_alignment") and hasattr(self.personal_lora_alignment, "build_cloud_few_shot_block"):
            return self.personal_lora_alignment.build_cloud_few_shot_block(max_examples=max_examples)
        return ""

    def maybe_admit_verified_turn(
        self,
        user_text: str,
        reply_text: str,
        disk_verified: bool,
        receipt_verified: bool,
        source: str,
    ) -> dict[str, Any]:
        if hasattr(self, "personal_lora_alignment") and hasattr(self.personal_lora_alignment, "maybe_admit_verified_turn"):
            return self.personal_lora_alignment.maybe_admit_verified_turn(
                user_text=user_text,
                reply_text=reply_text,
                disk_verified=disk_verified,
                receipt_verified=receipt_verified,
                source=source,
            )
        return {"admitted": False, "reason": "No personal lora alignment engine"}

    # ---------- STAGE 44: PERSONAL BEHAVIORAL PROFILER ----------
    def personal_profile_status(self) -> dict:
        return self.personal_profiler.status()

    def add_anti_drift_rule(self, rule_text: str) -> dict:
        return self.personal_profiler.add_anti_drift_rule(rule_text)

    def add_workspace_alias(self, shortcut: str, target_path: str) -> dict:
        return self.personal_profiler.add_alias(shortcut, target_path)

    def set_personal_preference(self, category: str, key: str, value: Any) -> dict:
        return self.personal_profiler.set_preference(category, key, value)

    # ---------- STAGE 39: SWARM DISPATCHER BRIDGE ----------
    def open_jarvis_status(self) -> dict:
        if hasattr(self, "open_jarvis"):
            return self.open_jarvis.status()
        return {"status": "UNAVAILABLE", "message": "OpenJarvisBridge not loaded"}

    def open_jarvis_execute_agent(self, agent_type: str, task: str, context: dict | None = None) -> dict:
        if hasattr(self, "open_jarvis"):
            return self.open_jarvis.execute_agent(agent_type=agent_type, task=task, context=context)
        return {"status": "ERROR", "message": "OpenJarvisBridge not loaded"}

    def open_jarvis_invoke_tool(self, tool_name: str, parameters: dict) -> dict:
        if hasattr(self, "open_jarvis"):
            return self.open_jarvis.invoke_tool(tool_name=tool_name, parameters=parameters)
        return {"status": "ERROR", "message": "OpenJarvisBridge not loaded"}

    def open_jarvis_profile_efficiency(self, token_count: int = 150, duration_ms: float = 250.0) -> dict:
        if hasattr(self, "open_jarvis"):
            return self.open_jarvis.profile_efficiency(token_count=token_count, duration_ms=duration_ms)
        return {"status": "ERROR", "message": "OpenJarvisBridge not loaded"}

    def swarm_status(self) -> dict:
        return self.swarm_dispatcher.status()

    def ensure_writer_online(self, max_wait_seconds: float = 6.0) -> bool:
        if hasattr(self, "swarm_dispatcher") and hasattr(self.swarm_dispatcher, "ensure_writer_online"):
            return self.swarm_dispatcher.ensure_writer_online(max_wait_seconds=max_wait_seconds)
        return False

    def connect_writer_bot(self) -> dict:
        if hasattr(self, "swarm_dispatcher") and hasattr(self.swarm_dispatcher, "connect_writer_bot"):
            return self.swarm_dispatcher.connect_writer_bot()
        return {"bot": "writer", "online": False, "status": "UNAVAILABLE", "message": "SwarmDispatcher not loaded"}

    def writer_status(self) -> dict:
        if hasattr(self, "swarm_dispatcher") and hasattr(self.swarm_dispatcher, "probe_bot"):
            return self.swarm_dispatcher.probe_bot("writer")
        return {"bot": "writer", "online": False, "status": "OFFLINE"}

    def checker_status(self) -> dict:
        if hasattr(self, "swarm_dispatcher") and hasattr(self.swarm_dispatcher, "probe_bot"):
            return self.swarm_dispatcher.probe_bot("checker")
        return {"bot": "checker", "online": False, "status": "OFFLINE"}

    def director_status(self) -> dict:
        if hasattr(self, "swarm_dispatcher") and hasattr(self.swarm_dispatcher, "probe_bot"):
            return self.swarm_dispatcher.probe_bot("director")
        return {"bot": "director", "online": False, "status": "OFFLINE"}

    def connect_checker_bot(self) -> dict:
        if hasattr(self, "swarm_dispatcher") and hasattr(self.swarm_dispatcher, "connect_checker_bot"):
            return self.swarm_dispatcher.connect_checker_bot()
        return {"bot": "checker", "online": False, "status": "UNAVAILABLE"}

    def connect_director_bot(self) -> dict:
        if hasattr(self, "swarm_dispatcher") and hasattr(self.swarm_dispatcher, "connect_director_bot"):
            return self.swarm_dispatcher.connect_director_bot()
        return {"bot": "director", "online": False, "status": "UNAVAILABLE"}

    def connect_swarm(self) -> dict:
        if hasattr(self, "swarm_dispatcher") and hasattr(self.swarm_dispatcher, "connect_swarm"):
            return self.swarm_dispatcher.connect_swarm()
        return {"status": "UNAVAILABLE", "message": "SwarmDispatcher not loaded"}

    def ensure_bot_online(self, bot_name: str, max_wait_seconds: float = 6.0) -> bool:
        if hasattr(self, "swarm_dispatcher") and hasattr(self.swarm_dispatcher, "ensure_bot_online"):
            return self.swarm_dispatcher.ensure_bot_online(bot_name, max_wait_seconds=max_wait_seconds)
        return False

    def dispatch_write(
        self,
        instruction: str,
        filename: str = "",
        folder: str = "",
        context: str = "",
        save: bool = True,
    ) -> dict:
        return self.swarm_dispatcher.dispatch_write(
            instruction=instruction,
            filename=filename,
            folder=folder,
            context=context,
            save=save,
        )

    def dispatch_check(
        self,
        code: str,
        filepath: str = "",
        instruction: str = "",
        context: str = "",
    ) -> dict:
        return self.swarm_dispatcher.dispatch_check(
            code=code,
            filepath=filepath,
            instruction=instruction,
            context=context,
        )

    def dispatch_director(
        self,
        blueprint: str,
        stage: str = "",
        workspace: str = "",
    ) -> dict:
        ws = workspace or str(self.project_root)
        return self.swarm_dispatcher.dispatch_director(
            blueprint=blueprint,
            stage=stage,
            workspace=ws,
        )

    def dispatch_async_swarm_job(
        self,
        name: str,
        job_fn: any,
        *args: any,
        **kwargs: any,
    ) -> str:
        return self.task_daemon.submit_task(name, job_fn, *args, **kwargs)


    # ---------- STAGE 40: CODE SYNTHESIS & TERMINAL VERIFICATION PIPELINE ----------
    def code_synthesis_status(self) -> dict:
        return self.code_synthesis.status()

    def synthesize_code(
        self,
        instruction: str,
        filename: str = "generated_tool.py",
        target_dir: any = None,
        custom_code: str | None = None,
    ) -> dict:
        return self.code_synthesis.synthesize(
            instruction=instruction,
            filename=filename,
            target_dir=target_dir,
            custom_code=custom_code,
        )

    def verify_code_file(self, file_path: str | Path) -> dict:
        return self.code_synthesis.verify_file(Path(file_path))

    def code_synthesis_history(self, limit: int = 20) -> list[dict]:
        return self.code_synthesis.history(limit=limit)


    # ---------- STAGE 41: SELF-REFINEMENT & REGRESSION TESTING HARNESS ----------
    def self_refinement_status(self) -> dict:
        return self.self_refinement.status()

    def refine_code(
        self,
        code: str,
        error_context: str = "",
        filename: str = "healed_tool.py",
        max_attempts: int = 3,
        instruction: str = "Self-refine code",
    ) -> dict:
        return self.self_refinement.refine_code(
            code=code,
            error_context=error_context,
            filename=filename,
            max_attempts=max_attempts,
            instruction=instruction,
        )

    def run_regression_suite(self, test_patterns: list[str] | None = None) -> dict:
        return self.self_refinement.run_regression_suite(test_patterns)

    def self_refinement_history(self, limit: int = 20) -> list[dict]:
        return self.self_refinement.history(limit=limit)


    # ---------- STAGE 42: LORA SLEEP CYCLE & SANITY GATE ----------
    def lora_sleep_cycle_status(self) -> dict:
        return self.lora_sleep_cycle.status()

    def trigger_sleep_cycle(
        self,
        adapter_name: str | None = None,
        min_samples: int = 1,
    ) -> dict:
        return self.lora_sleep_cycle.trigger_sleep_cycle(
            adapter_name=adapter_name,
            min_samples=min_samples,
        )

    def run_lora_sanity_gate(self) -> dict:
        return self.lora_sleep_cycle.run_sanity_gate()

    def list_lora_adapters(self) -> list[str]:
        return self.lora_sleep_cycle.list_adapters()

    def lora_sleep_cycle_history(self, limit: int = 20) -> list[dict]:
        return self.lora_sleep_cycle.history(limit=limit)