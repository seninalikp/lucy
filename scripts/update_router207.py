with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

old_g = 'if lowered in {"/governor-status", "governor-status", "/compute-governor-status", "compute-governor-status"}:'
new_g = 'if lowered in {"/compute-governor-status", "compute-governor-status", "/latency-governor-status", "latency-governor-status"}:'
rc = rc.replace(old_g, new_g)

with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
    f.write(rc)

print('Updated router.py cleanly for Stage 207')
