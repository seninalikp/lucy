# scripts/wire_stage195.py
# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.zerocopy_ipc_shm import ZeroCopyIPCShmFabric, STAGE as STAGE_194\n'
imp_repl = 'from backend.lucy_core.zerocopy_ipc_shm import ZeroCopyIPCShmFabric, STAGE as STAGE_194\nfrom backend.lucy_core.distributed_tensor_runtime import DistributedTensorRuntimeFabric, STAGE as STAGE_195\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.zerocopy_shm_fabric = ZeroCopyIPCShmFabric()\n'
init_repl = '        self.zerocopy_shm_fabric = ZeroCopyIPCShmFabric()\n        # Stage 195: Autonomous Neural Weights Sharder & Distributed Tensor Runtime (Era 20)\n        self.tensor_runtime_fabric = DistributedTensorRuntimeFabric()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("zerocopy_shm_fabric", "core"),\n'
svc_repl = '            ("zerocopy_shm_fabric", "core"),\n            ("tensor_runtime_fabric", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 106: Offline Multi-Modal Voice Fabric\n'
tensor_router_code = '''        # Stage 195: Autonomous Neural Weights Sharder & Distributed Tensor Runtime (Era 20)
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

'''
if router_hook in rc and 'tensor_runtime_fabric' not in rc:
    rc = rc.replace(router_hook, tensor_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 195 successfully wired into lucy_runtime.py and router.py!')
