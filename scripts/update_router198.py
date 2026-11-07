with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

old_mesh = 'if lowered in {"/mesh-status", "mesh-status", "/daemon-mesh-status", "daemon-mesh-status"}:'
new_mesh = 'if lowered in {"/daemon-mesh-status", "daemon-mesh-status", "/sentinel-status", "sentinel-status"}:'
rc = rc.replace(old_mesh, new_mesh)

with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
    f.write(rc)

print('Updated router.py cleanly for Stage 198')
