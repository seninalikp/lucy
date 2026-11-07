import os
import re

# 1. Update backend/lucy_core/tools.py
tools_path = 'backend/lucy_core/tools.py'
with open(tools_path, 'r', encoding='utf-8') as f:
    tools_code = f.read()

create_folder_tools = '''    def create_folder(self, raw_path: str) -> dict:
        """Create a directory safely inside the project workspace."""
        clean_path = str(raw_path or "").strip().strip("\'\\"")
        if not clean_path:
            return {"ok": False, "error": "Folder path cannot be empty."}
        try:
            target_path = self._resolve_inside_project(clean_path)
            if self._is_sensitive_name(target_path):
                return {
                    "ok": False,
                    "error": f"Folder name contains restricted keyword: {clean_path}",
                }
            created = False
            if not target_path.exists():
                target_path.mkdir(parents=True, exist_ok=True)
                created = True
            return {
                "ok": True,
                "created": created,
                "already_existed": not created,
                "path": str(target_path).replace("\\\\", "/"),
                "relative_path": str(target_path.relative_to(self.project_root)).replace("\\\\", "/"),
            }
        except ValueError as ve:
            return {"ok": False, "error": str(ve)}
        except Exception as exc:
            return {"ok": False, "error": f"Could not create folder: {exc}"}
'''

if 'def create_folder' not in tools_code:
    tools_code = tools_code.rstrip() + '\n\n' + create_folder_tools + '\n'
    with open(tools_path, 'w', encoding='utf-8') as f:
        f.write(tools_code)
    print("Added create_folder to tools.py")
else:
    print("create_folder already present in tools.py")

# 2. Update backend/lucy_core/lucy_runtime.py
rt_path = 'backend/lucy_core/lucy_runtime.py'
with open(rt_path, 'r', encoding='utf-8') as f:
    rt_code = f.read()

create_folder_rt = '''    def create_folder(self, raw_path: str) -> dict:
        """Create a directory safely inside the project workspace."""
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
        return res
'''

if 'def create_folder' not in rt_code:
    # insert before def read_project_file or similar
    anchor = '    def read_project_file(self, path: str) -> dict:'
    assert anchor in rt_code, 'anchor in lucy_runtime.py not found'
    rt_code = rt_code.replace(anchor, create_folder_rt + '\n' + anchor, 1)
    with open(rt_path, 'w', encoding='utf-8') as f:
        f.write(rt_code)
    print("Added create_folder to lucy_runtime.py")
else:
    print("create_folder already present in lucy_runtime.py")

# 3. Update backend/lucy_core/router.py
router_path = 'backend/lucy_core/router.py'
with open(router_path, 'r', encoding='utf-8') as f:
    router_code = f.read()

create_folder_router = '''        if lowered.startswith("create folder ") or lowered.startswith("make folder ") or lowered.startswith("mkdir ") or lowered.startswith("/mkdir "):
            if lowered.startswith("create folder "):
                folder_arg = text[14:].strip()
            elif lowered.startswith("make folder "):
                folder_arg = text[12:].strip()
            elif lowered.startswith("mkdir "):
                folder_arg = text[6:].strip()
            elif lowered.startswith("/mkdir "):
                folder_arg = text[7:].strip()
            else:
                folder_arg = ""

            if not folder_arg:
                return RouterResponse("Usage: create folder <path> | make folder <path> | mkdir <path>")

            res = self.runtime.create_folder(folder_arg)
            if res.get("ok"):
                action_word = "Created folder" if res.get("created") else "Folder already exists at"
                msg = f"{action_word}: {res.get('relative_path')} ({res.get('path')})"
                return RouterResponse(msg, data=res)
            return RouterResponse(f"Failed to create folder: {res.get('error', 'Unknown error')}", data=res)
'''

if 'create folder ' not in router_code:
    anchor_router = '        if lowered == "approved folders":'
    assert anchor_router in router_code, 'anchor_router not found'
    router_code = router_code.replace(anchor_router, create_folder_router + '\n' + anchor_router, 1)
    with open(router_path, 'w', encoding='utf-8') as f:
        f.write(router_code)
    print("Added folder creation commands to router.py")
else:
    print("folder creation commands already present in router.py")

# 4. Update backend/lucy_core/natural_action_parser.py
nap_path = 'backend/lucy_core/natural_action_parser.py'
with open(nap_path, 'r', encoding='utf-8') as f:
    nap_code = f.read()

nap_pattern = '''NATURAL_FOLDER_MAKE_PATTERNS = [
    r"(?:please\\s+|can\\s+you\\s+|also\\s+)?(?:make|create)\\s+(?:a\\s+)?(?:folder|directory)\\s+(?:named|called\\s+)?[\'\\"]?([a-zA-Z0-9_\\-\\./\\\\]{1,80})[\'\\"]?",
    r"(?:mkdir)\\s+[\'\\"]?([a-zA-Z0-9_\\-\\./\\\\]{1,80})[\'\\"]?",
]
'''

nap_handling = '''        # 4. Detect natural folder creation
        for pat in NATURAL_FOLDER_MAKE_PATTERNS:
            for match in re.finditer(pat, raw, re.IGNORECASE):
                folder_name = match.group(1).strip().rstrip(".,;\\"\'")
                if folder_name and hasattr(self.runtime, "create_folder"):
                    f_res = self.runtime.create_folder(folder_name)
                    if f_res.get("ok"):
                        executed_actions.append({
                            "type": "folder_created",
                            "id": f_res.get("relative_path", folder_name),
                            "detail": f_res.get("path", folder_name),
                        })
'''

if 'NATURAL_FOLDER_MAKE_PATTERNS' not in nap_code:
    # insert pattern
    pat_anchor = 'NATURAL_TASK_DONE_PATTERNS = ['
    assert pat_anchor in nap_code, 'pat_anchor not found'
    nap_code = nap_code.replace(pat_anchor, nap_pattern + '\n' + pat_anchor, 1)

    # insert handling
    hand_anchor = '        # 1. Detect natural task creation'
    assert hand_anchor in nap_code, 'hand_anchor not found'
    nap_code = nap_code.replace(hand_anchor, nap_handling + '\n' + hand_anchor, 1)

    with open(nap_path, 'w', encoding='utf-8') as f:
        f.write(nap_code)
    print("Added natural folder creation to natural_action_parser.py")
else:
    print("natural folder creation already present in natural_action_parser.py")
