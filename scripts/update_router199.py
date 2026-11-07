with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

old_s = 'if lowered in {"/singularity-status", "singularity-status", "/nexus-status", "nexus-status"}:'
new_s = 'if lowered in {"/bicentennial-nexus-status", "bicentennial-nexus-status", "/stage199-status", "stage199-status"}:'
rc = rc.replace(old_s, new_s)

with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
    f.write(rc)

print('Updated router.py cleanly for Stage 199')
