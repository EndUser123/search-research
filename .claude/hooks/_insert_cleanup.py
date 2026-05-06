with open(r'P:\.claude\hooks\Stop.py', 'r', encoding='utf-8') as f:
    content = f.read()

lazy_msg = 'messages.append("LAZY CLOSURE CHECK:\\n- " + "\\n- ".join(sample))'
struct_start = '\n        if os.environ.get("RESPONSE_STRUCTURE_DETECTOR_ENABLED", "true").lower() in (\n            "1",\n            "true",\n            "yes",\n        ):\n            from anti_sycophancy.response_structure_detector import ('

idx = content.find(lazy_msg)
struct_idx = content.find(struct_start, idx)
print(f"lazy_msg at: {idx}")
print(f"struct_start at: {struct_idx}")

if idx >= 0 and struct_idx >= 0:
    lazy_end = idx + len(lazy_msg)
    new_block = (
        '\n        if os.environ.get("DESTRUCTIVE_CLEANUP_DETECTOR_ENABLED", "true").lower() in (\n'
        '            "1", "true", "yes",\n'
        '        ):\n'
        '            cleanup = detect_all_destructive_cleanup(response)\n'
        '            if cleanup:\n'
        '                _append_anti_sycophancy_log(\n'
        '                    data=data,\n'
        '                    detector="destructive_cleanup_detector",\n'
        '                    severity="warn",\n'
        '                    findings=[m.matched for m in cleanup],\n'
        '                )\n'
        '                _samp = "\\n- ".join(\n'
        '                    f"{m.matched}: {m.suggestion}" for m in cleanup\n'
        '                )\n'
        '                messages.append(f"DESTRUCTIVE CLEANUP ADVISORY:\\n- {_samp}")\n'
    )
    new_content = content[:lazy_end] + new_block + content[struct_idx:]
    with open(r'P:\.claude\hooks\Stop.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Done, replacement applied")
else:
    print("ERROR: anchor strings not found")
    print(f"idx={idx}, struct_idx={struct_idx}")
