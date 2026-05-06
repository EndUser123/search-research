#!/usr/bin/env python3
with open(r'P:\.claude\hooks\Stop.py', 'r', encoding='utf-8') as f:
    content = f.read()

lazy_line = 'messages.append("LAZY CLOSURE CHECK'
resp_marker = '\n        if os.environ.get("RESPONSE_STRUCTURE_DETECTOR_ENABLED", "true").lower() in (\n            "1",'

la_start = content.find(lazy_line)
resp_idx = content.find(resp_marker, la_start)
print("LAZY:", la_start, "RESP:", resp_idx)

new_block = '\n\n        if os.environ.get("DESTRUCTIVE_CLEANUP_DETECTOR_ENABLED", "true").lower() in (\n            "1", "true", "yes",\n        ):\n            cleanup = detect_all_destructive_cleanup(response)\n            if cleanup:\n                _append_anti_sycophancy_log(\n                    data=data,\n                    detector="destructive_cleanup_detector",\n                    severity="warn",\n                    findings=[m.matched for m in cleanup],\n                )\n                samp = "\\n- ".join(\n                    f"{m.matched}: {m.suggestion}" for m in cleanup\n                )\n                messages.append("DESTRUCTIVE CLEANUP ADVISORY:\\n- " + samp)

new_content = content[:resp_idx] + new_block + content[resp_idx:]

with open(r'P:\.claude\hooks\Stop.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
print("Done, written", len(new_content), "chars")
