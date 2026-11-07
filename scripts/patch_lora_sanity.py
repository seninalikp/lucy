path = 'backend/lucy_core/lora_sleep_cycle.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

old_block = """        if not ans_fn:
            # Check if live connector is available
            has_model = False
            if self.connector and hasattr(self.connector, "is_online") and self.connector.is_online():
                try:
                    mods = self.connector.list_models()
                    has_model = any(DEFAULT_BASE_MODEL in m.get("name", "") for m in mods)
                except Exception:
                    has_model = False
            if has_model:
                def _conn_responder(q: str) -> str:
                    try:
                        res = self.connector.generate(prompt=q, model=DEFAULT_BASE_MODEL)
                        return res.get("response", "")
                    except Exception:
                        return _default_responder(q)
                active_fn = _conn_responder
            else:
                active_fn = _default_responder
        else:
            active_fn = ans_fn"""

new_block = """        if not ans_fn:
            # Check if live connector is available
            has_model = False
            target_model = DEFAULT_BASE_MODEL
            if self.connector and hasattr(self.connector, "is_online") and self.connector.is_online():
                try:
                    mods = self.connector.list_models()
                    if any(HOT_SWAP_TARGET_MODEL in m.get("name", "") for m in mods):
                        target_model = HOT_SWAP_TARGET_MODEL
                        has_model = True
                    elif any(DEFAULT_BASE_MODEL in m.get("name", "") for m in mods):
                        target_model = DEFAULT_BASE_MODEL
                        has_model = True
                except Exception:
                    has_model = False

            sys_ctx = _default_responder("")
            if has_model:
                def _conn_responder(q: str) -> str:
                    try:
                        res = self.connector.generate(prompt=q, system_prompt=sys_ctx, model=target_model)
                        ans = res.get("response", "")
                        return ans if ans else _default_responder(q)
                    except Exception:
                        return _default_responder(q)
                active_fn = _conn_responder
            else:
                active_fn = _default_responder
        else:
            active_fn = ans_fn"""

if old_block not in c:
    old_block_crlf = old_block.replace('\n', '\r\n')
    assert old_block_crlf in c, 'old_block not found in lora_sleep_cycle.py'
    c = c.replace(old_block_crlf, new_block.replace('\n', '\r\n'), 1)
else:
    c = c.replace(old_block, new_block, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

print('Updated lora_sleep_cycle.py run_sanity_gate successfully')
