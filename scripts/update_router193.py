with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

old_check = 'if lowered in {"/bft-status", "bft-status", "/raft-bft-status", "raft-bft-status"}:'
new_check = 'if lowered in {"/raft-bft-status", "raft-bft-status", "/hybrid-bft-status", "hybrid-bft-status"}:'
rc = rc.replace(old_check, new_check)

old_prop = 'if lowered.startswith("/bft-propose ") or lowered.startswith("bft-propose "):'
new_prop = 'if lowered.startswith("/raft-bft-propose ") or lowered.startswith("raft-bft-propose "):'
rc = rc.replace(old_prop, new_prop)

old_pref = 'prefix = "/bft-propose " if lowered.startswith("/bft-propose ") else "bft-propose "'
new_pref = 'prefix = "/raft-bft-propose " if lowered.startswith("/raft-bft-propose ") else "raft-bft-propose "'
rc = rc.replace(old_pref, new_pref)

with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
    f.write(rc)

print('Updated router.py cleanly')
