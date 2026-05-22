#!/usr/bin/env python3
import json, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Optional

PROBLEM = """You are given a singly linked list with a cycle. Return the node where the cycle begins.

Definition:
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

Example:
Input: head = [3,2,0,-4], pos = 1  (tail connects to node at index 1)
Output: True (node with val=2)

Implement:
def has_cycle(head):
    # Return the ListNode where the cycle begins, or None if no cycle
"""

@dataclass
class ModelResult:
    model: str
    response: str
    latency_ms: float
    error: Optional[str] = None
    passed: bool = False
    details: str = ""

def call_model(model: str, timeout: int = 60) -> ModelResult:
    url = "http://localhost:8080/anthropic/v1/messages"
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": PROBLEM}],
        "max_tokens": 2048,
    }).encode()
    headers = {
        "Content-Type": "application/json",
        "x-api-key": "sk-bf-49998d75-3b06-4e72-8547-741cb81b497e",
        "anthropic-version": "2023-06-01",
    }
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read())
            latency_ms = (time.time() - start) * 1000
            content = body.get("content", [{}])
            if isinstance(content, list):
                text = "\n".join(b.get("text", "") for b in content if isinstance(b, dict))
            else:
                text = str(content)
            return ModelResult(model=model, response=text, latency_ms=latency_ms)
    except urllib.error.HTTPError as e:
        latency_ms = (time.time() - start) * 1000
        body_text = e.read().decode()[:200]
        return ModelResult(model=model, response="", latency_ms=latency_ms,
                         error=f"HTTP {e.code}: {body_text}")
    except Exception as e:
        latency_ms = (time.time() - start) * 1000
        return ModelResult(model=model, response="", latency_ms=latency_ms, error=str(e))

def verify_code(code: str) -> tuple[bool, str]:
    import re, subprocess, sys
    code_blocks = re.findall(r"```python\s*(.*?)```", code, re.DOTALL)
    if not code_blocks:
        code_blocks = re.findall(r"```\s*(.*?)```", code, re.DOTALL)
    if not code_blocks:
        return False, "No code block"
    for i, block in enumerate(code_blocks):
        test_code = block + "\n\n" + """
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
n1 = ListNode(3); n2 = ListNode(2); n3 = ListNode(0); n4 = ListNode(-4)
n1.next = n2; n2.next = n3; n3.next = n4; n4.next = n2
result = has_cycle(n1)
if result is None:
    print("FAIL_none")
elif result.val == 2:
    print("PASS_val2")
else:
    print(f"FAIL_val={result.val}")
"""
        try:
            proc = subprocess.run([sys.executable, "-c", test_code],
                                  capture_output=True, text=True, timeout=10)
            output = proc.stdout.strip()
            if "PASS_val2" in output:
                return True, f"block {i+1}: ok"
            elif "FAIL" in output:
                return False, f"block {i+1}: {output[:80]}"
            else:
                return False, f"block {i+1}: {output[:80]}"
        except subprocess.TimeoutExpired:
            return False, f"block {i+1}: timeout"
        except Exception as e:
            return False, f"block {i+1}: {e}"
    return False, "all blocks failed"

def main():
    models = [
        "Groq-GPT-OSS-120b", "MiniMax-M2.7", "Mi-Devstral", "Mi-Magistral",
        "Mi-Mistral", "N-DSv4-flash", "N-DSv4-Pro", "N-Kimi-2.6",
        "step-3.5-flash", "N-Q3C-480b-a35b", "N-N3S-120b-a12b",
        "owl-alpha", "ring-2.6-1t", "GLM-5.1", "glm-4.7",
    ]
    print(f"Benchmarking {len(models)} models in parallel...\n")
    results: list[ModelResult] = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(call_model, m): m for m in models}
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda r: (not r.passed, r.latency_ms))
    print(f"{'Model':<25} {'Latency':>10} {'Result':<8} Details")
    print("-" * 90)
    for r in results:
        if r.error:
            print(f"{r.model:<25} {r.latency_ms:>9.0f}ms ERROR   {r.error[:50]}")
            continue
        passed, details = verify_code(r.response)
        r.passed = passed; r.details = details
        status = "PASS" if passed else "FAIL"
        print(f"{r.model:<25} {r.latency_ms:>9.0f}ms {status:<8} {details[:50]}")
    print(f"\n--- Summary ---")
    passed_models = [r.model for r in results if r.passed]
    print(f"Passed: {len(passed_models)}/{len(models)}")
    for m in passed_models:
        r = next(x for x in results if x.model == m)
        print(f"  {m}: {r.latency_ms:.0f}ms")

if __name__ == "__main__":
    main()
